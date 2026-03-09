"""
ResNet Image Embedder (Fine-tuned on SkyyRose Catalog)

Pre-configured for future use when product images are labeled.
"""

import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as transforms

from .base_embedder import BaseEmbedder


class ResNetEmbedder(BaseEmbedder):
    """ResNet-based image embedder fine-tuned on SkyyRose products."""

    def __init__(self, model_path=None, device=None, use_pretrained=True):
        if device is None:
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "mps" if torch.backends.mps.is_available() else "cpu"
            )

        self.model_path = model_path
        self.use_pretrained = use_pretrained
        self.transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

        super().__init__(str(model_path) if model_path else "resnet50-pretrained", device)
        self.load_model()

    def load_model(self):
        """Load ResNet model (pretrained or fine-tuned)."""
        if self.model_path and self.model_path.exists():
            print(f"Loading fine-tuned ResNet from: {self.model_path}")
            self.model = self._load_finetuned_model()
        elif self.use_pretrained:
            print("Loading pretrained ResNet-50 (ImageNet weights)...")
            self.model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
            print(
                "⚠️  Note: Using pretrained model. For best results, fine-tune on SkyyRose catalog."
            )
        else:
            raise ValueError("No model_path provided and use_pretrained=False")

        # Remove classification head (use as feature extractor)
        self.model = torch.nn.Sequential(*list(self.model.children())[:-1])
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode

    def _load_finetuned_model(self):
        """Load fine-tuned model from checkpoint."""
        print("⚠️  Fine-tuned model loading not yet implemented. Using pretrained model.")
        return models.resnet50(weights=models.ResNet50_Weights.DEFAULT)

    def encode_image(self, image_path):
        """Generate ResNet embedding for a single image."""
        image = self.load_image(image_path)
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            embedding = self.model(image_tensor)

        embedding = embedding.squeeze().cpu().numpy()
        return embedding / np.linalg.norm(embedding)

    def encode_batch(self, image_paths, batch_size=32):
        """Generate ResNet embeddings for multiple images."""
        all_embeddings = []

        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i : i + batch_size]
            images = [self.load_image(path) for path in batch_paths]
            image_tensors = torch.stack([self.transform(img) for img in images]).to(self.device)

            with torch.no_grad():
                embeddings = self.model(image_tensors)

            embeddings = embeddings.squeeze().cpu().numpy()
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings)

    def get_embedding_dim(self):
        """Return ResNet-50 embedding dimensionality."""
        return 2048
