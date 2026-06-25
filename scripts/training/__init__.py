"""
ResNet Training Pipeline for SkyyRose Product Recognition

Pre-configured training infrastructure for fine-tuning ResNet on labeled
product catalog. Use after labeling product groups.

Workflow:
1. Label products: prepare_dataset.py
2. Train model: train_resnet.py
3. Assess performance: assess_model.py

Note: visual_product_recognition.py now embeds via the unified CLIP encoder in
``skyyrose.core.embeddings`` (the old ``scripts/image_embeddings/`` OOP package,
including its never-trained ResNet embedder, was removed in the Phase 2
embeddings reframe). A fine-tuned ResNet would need a fresh integration point.
"""
