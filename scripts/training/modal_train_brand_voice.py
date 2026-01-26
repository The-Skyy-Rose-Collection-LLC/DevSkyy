"""
SkyyRose Brand Voice LLM Training on Modal.

Run with: modal run scripts/training/modal_train_brand_voice.py
"""
import modal

# Define the Modal app
app = modal.App("skyyrose-brand-voice-training")

# Create image with all dependencies
training_image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "torch",
    "transformers",
    "datasets",
    "peft",
    "trl",
    "accelerate",
    "bitsandbytes",
    "huggingface_hub",
)

@app.function(
    image=training_image,
    gpu="A10G",  # A10G GPU with 24GB VRAM
    timeout=7200,  # 2 hours
    secrets=[modal.Secret.from_name("huggingface-secret")],  # HF_TOKEN from Modal secrets
)
def train_brand_voice():
    """Train SkyyRose brand voice model."""
    import os
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTTrainer, SFTConfig
    from huggingface_hub import login

    # Configuration
    MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
    DATASET_NAME = "damBruh/skyyrose-brand-voice-training"
    OUTPUT_DIR = "/tmp/skyyrose-brand-voice-llm"
    HF_USERNAME = "damBruh"

    # Login to HuggingFace
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        login(token=hf_token)
        print("Logged in to HuggingFace")
    else:
        raise ValueError("HF_TOKEN not found in secrets")

    print(f"Loading dataset: {DATASET_NAME}")
    dataset = load_dataset(DATASET_NAME, split="train", token=hf_token)
    print(f"Dataset loaded: {len(dataset)} examples")

    # Quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
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

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True, token=hf_token)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # LoRA configuration
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
        output_dir=OUTPUT_DIR,
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
        hub_model_id=f"{HF_USERNAME}/skyyrose-brand-voice-llm",
        hub_token=hf_token,
        seed=42,
    )

    print("Initializing SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
    )

    print("Starting training...")
    trainer.train()

    print("Saving and pushing to Hub...")
    trainer.save_model()
    trainer.push_to_hub()

    return f"Training complete! Model at: huggingface.co/{HF_USERNAME}/skyyrose-brand-voice-llm"


@app.local_entrypoint()
def main():
    """Run the training job."""
    print("Starting SkyyRose brand voice training on Modal...")
    result = train_brand_voice.remote()
    print(result)


if __name__ == "__main__":
    main()
