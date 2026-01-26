# /// script
# dependencies = ["trl>=0.12.0", "peft>=0.7.0", "trackio", "datasets", "transformers", "accelerate", "bitsandbytes"]
# ///

from datasets import load_dataset
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig
import trackio
import os

# Get HF token from environment
hf_token = os.environ.get("HF_TOKEN")

print("Loading SkyyRose brand voice dataset...")
dataset = load_dataset("damBruh/skyyrose-brand-voice-training", split="train", token=hf_token)
print(f"Dataset loaded: {len(dataset)} examples")

# LoRA configuration for efficient fine-tuning
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)

# Training configuration
training_args = SFTConfig(
    output_dir="skyyrose-brand-voice-llm",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_ratio=0.1,
    weight_decay=0.01,
    max_grad_norm=1.0,
    logging_steps=1,
    save_strategy="epoch",
    save_total_limit=2,
    gradient_checkpointing=True,
    push_to_hub=True,
    hub_model_id="damBruh/skyyrose-brand-voice-llm",
    hub_token=hf_token,
    report_to="trackio",
    run_name="skyyrose-brand-voice-qwen2.5",
    seed=42,
)

print("Initializing SFTTrainer with Qwen/Qwen2.5-1.5B-Instruct...")
trainer = SFTTrainer(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    train_dataset=dataset,
    peft_config=peft_config,
    args=training_args,
)

print("Starting training...")
trainer.train()

print("Saving and pushing to Hub...")
trainer.save_model()
trainer.push_to_hub()

print("SUCCESS: Model available at huggingface.co/damBruh/skyyrose-brand-voice-llm")
