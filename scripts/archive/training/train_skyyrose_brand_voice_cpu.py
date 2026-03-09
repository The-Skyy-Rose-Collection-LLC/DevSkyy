"""
Train SkyyRose brand voice LLM using LoRA on CPU (more stable).

Model: Qwen/Qwen2.5-0.5B-Instruct
Method: LoRA (r=16, alpha=32)
Device: CPU (Apple Silicon optimized)
"""

import json

import torch
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

from datasets import Dataset

# Configuration
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
OUTPUT_DIR = "skyyrose-brand-voice-lora"
DATASET_PATH = "datasets/skyyrose_brand_voice/train_merged.jsonl"

# LoRA config
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

# Training config
BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 4
MAX_SEQ_LENGTH = 256  # Reduced for faster training
NUM_EPOCHS = 5  # More epochs to compensate for small dataset
LEARNING_RATE = 3e-4


def load_dataset_from_jsonl(file_path: str) -> Dataset:
    """Load dataset from JSONL file."""
    print(f"Loading dataset from {file_path}...")

    examples = []
    with open(file_path) as f:
        for line in f:
            data = json.loads(line)
            messages = data["messages"]

            # Format as chat template
            text = ""
            for msg in messages:
                role = msg["role"]
                content = msg["content"]

                if role == "system":
                    text += f"<|im_start|>system\n{content}<|im_end|>\n"
                elif role == "user":
                    text += f"<|im_start|>user\n{content}<|im_end|>\n"
                elif role == "assistant":
                    text += f"<|im_start|>assistant\n{content}<|im_end|>\n"

            examples.append({"text": text})

    print(f"Loaded {len(examples)} examples")
    return Dataset.from_list(examples)


def main():
    print("=" * 70)
    print("  SKYYROSE BRAND VOICE LLM TRAINING (CPU)")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Dataset: {DATASET_PATH}")
    print("=" * 70)
    print()

    # Force CPU
    device = torch.device("cpu")
    print(f"Using device: {device}")
    print()

    # Load tokenizer
    print("[1/6] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    print("✓ Tokenizer loaded")

    # Load model on CPU
    print("\n[2/6] Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model = model.to(device)
    print(f"✓ Model loaded ({sum(p.numel() for p in model.parameters()) / 1e6:.1f}M parameters)")

    # Configure LoRA
    print("\n[3/6] Configuring LoRA...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    print("✓ LoRA configured")

    # Load dataset
    print("\n[4/6] Loading dataset...")
    dataset = load_dataset_from_jsonl(DATASET_PATH)

    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding="max_length",
        )

    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,
    )
    print(f"✓ Dataset tokenized ({len(tokenized_dataset)} examples)")

    # Training arguments
    print("\n[5/6] Configuring training...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        learning_rate=LEARNING_RATE,
        logging_steps=5,
        save_steps=25,
        save_total_limit=2,
        warmup_steps=10,
        lr_scheduler_type="cosine",
        gradient_checkpointing=False,
        fp16=False,
        bf16=False,
        use_cpu=True,  # Force CPU training
        dataloader_pin_memory=False,
        optim="adamw_torch",
        report_to="none",
        disable_tqdm=False,
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )

    print("✓ Training configured")
    print(f"  - Batch size: {BATCH_SIZE}")
    print(f"  - Gradient accumulation: {GRADIENT_ACCUMULATION_STEPS}")
    print(f"  - Effective batch size: {BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS}")
    print(f"  - Epochs: {NUM_EPOCHS}")
    print(f"  - Learning rate: {LEARNING_RATE}")
    print(f"  - Max sequence length: {MAX_SEQ_LENGTH}")
    print(
        f"  - Total steps: {len(tokenized_dataset) * NUM_EPOCHS // (BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS)}"
    )

    # Train
    print("\n[6/6] Training...")
    print("This will take several minutes on CPU...\n")
    try:
        trainer.train()
        print("\n✓ Training complete!")

        # Save
        print("\nSaving model...")
        model.save_pretrained(OUTPUT_DIR)
        tokenizer.save_pretrained(OUTPUT_DIR)
        print(f"✓ Model saved to {OUTPUT_DIR}")

        print("\n" + "=" * 70)
        print("  TRAINING COMPLETE")
        print("=" * 70)
        print(f"\nModel saved to: {OUTPUT_DIR}")
        print("\nTest the model:")
        print("```python")
        print("from transformers import AutoTokenizer, AutoModelForCausalLM")
        print("from peft import PeftModel")
        print()
        print(f"base_model = AutoModelForCausalLM.from_pretrained('{MODEL_NAME}')")
        print(f"model = PeftModel.from_pretrained(base_model, '{OUTPUT_DIR}')")
        print(f"tokenizer = AutoTokenizer.from_pretrained('{MODEL_NAME}')")
        print()
        print("prompt = 'Write a product description for a rose gold hoodie.'")
        print("inputs = tokenizer(prompt, return_tensors='pt')")
        print("outputs = model.generate(**inputs, max_length=200)")
        print("print(tokenizer.decode(outputs[0]))")
        print("```")

    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
