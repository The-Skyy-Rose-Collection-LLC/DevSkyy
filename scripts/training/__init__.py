"""
ResNet Training Pipeline for SkyyRose Product Recognition

Pre-configured training infrastructure for fine-tuning ResNet on labeled
product catalog. Use after labeling product groups.

Workflow:
1. Label products: prepare_dataset.py
2. Train model: train_resnet.py
3. Assess performance: assess_model.py
4. Switch to ResNet: ../image_embeddings/config.py
"""
