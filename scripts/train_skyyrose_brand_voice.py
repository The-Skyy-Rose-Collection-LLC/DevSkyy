"""
Train SkyyRose brand voice LLM using LoRA on Apple Silicon.

Model: Qwen/Qwen2.5-0.5B-Instruct (fits in 8GB)
Method: LoRA (r=16, alpha=32)
Optimizations: Gradient checkpointing, small batch size
"""

import json
import os
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)

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
MAX_SEQ_LENGTH = 512
NUM_EPOCHS = 3
LEARNING_RATE = 2e-4


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
    print("  SKYYROSE BRAND VOICE LLM TRAINING")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Dataset: {DATASET_PATH}")
    print("=" * 70)
    print()

    # Load tokenizer
    print("[1/6] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    print("✓ Tokenizer loaded")

    # Load model
    print("\n[2/6] Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,  # Use float32 for Apple Silicon
        device_map="auto",
        use_cache=False,  # Disable KV cache for training
    )
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

    # Enable gradients for LoRA parameters
    for name, param in model.named_parameters():
        if "lora" in name:
            param.requires_grad = True

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"✓ LoRA configured ({trainable_params / 1e6:.1f}M trainable parameters)")

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
        logging_steps=1,
        save_steps=10,
        save_total_limit=2,
        warmup_steps=10,
        lr_scheduler_type="cosine",
        gradient_checkpointing=False,  # Disabled due to compatibility issues
        fp16=False,  # Apple Silicon doesn't support FP16 training
        bf16=False,
        optim="adamw_torch",
        report_to="none",
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

    # Train
    print("\n[6/6] Training...")
    try:
        trainer.train()
        print("\n✓ Training complete!")

        # Save
        print("\nSaving model...")
        model.save_pretrained(OUTPUT_DIR)
        tokenizer.save_pretrained(OUTPUT_DIR)
        print(f"✓ Model saved to {OUTPUT_DIR}")

    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("  TRAINING COMPLETE")
    print("=" * 70)
    print(f"\nModel saved to: {OUTPUT_DIR}")
    print("\nTest the model:")
    print(f"  python -c \"from transformers import pipeline; p = pipeline('text-generation', '{OUTPUT_DIR}'); print(p('Write a product description for'))\"")


if __name__ == "__main__":
    main()
