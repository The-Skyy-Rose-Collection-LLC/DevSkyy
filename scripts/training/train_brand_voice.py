#!/usr/bin/env python3
"""SkyyRose Brand Voice LLM Training with TRL.

Fine-tunes Qwen2.5-1.5B-Instruct on SkyyRose brand voice dataset.
"""

import os

from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

from datasets import load_dataset

# Configuration
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
DATASET_NAME = "damBruh/skyyrose-brand-voice-training"
OUTPUT_DIR = "./skyyrose-brand-voice-llm"
HF_USERNAME = "damBruh"


def main():
    """Run training."""
    # Get HF token
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not set")

    print(f"Loading dataset: {DATASET_NAME}")
    dataset = load_dataset(DATASET_NAME, split="train", token=hf_token)
    print(f"Dataset size: {len(dataset)} examples")

    # Quantization config for efficient training
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype="float16",
        bnb_4bit_use_double_quant=True,
    )

    print(f"Loading model: {MODEL_NAME}")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        token=hf_token,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        token=hf_token,
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # LoRA configuration
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        bias="none",
        task_type="CAUSAL_LM",
    )

    # Training configuration
    training_args = SFTConfig(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_ratio=0.1,
        weight_decay=0.01,
        max_grad_norm=1.0,
        logging_steps=1,
        save_steps=50,
        save_total_limit=2,
        max_seq_length=1024,
        gradient_checkpointing=True,
        report_to="none",
        push_to_hub=True,
        hub_model_id=f"{HF_USERNAME}/skyyrose-brand-voice-llm",
        hub_token=hf_token,
        seed=42,
    )

    print("Starting training...")
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
    )

    trainer.train()

    print("Saving model...")
    trainer.save_model()

    print("Pushing to Hub...")
    trainer.push_to_hub()

    print(
        f"Training complete! Model available at: huggingface.co/{HF_USERNAME}/skyyrose-brand-voice-llm"
    )


if __name__ == "__main__":
    main()
