"""
CLIP Image Embedder

Uses OpenAI's CLIP for zero-shot visual similarity matching.
"""

import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor

from .base_embedder import BaseEmbedder


class CLIPEmbedder(BaseEmbedder):
    """CLIP-based image embedder for product similarity matching."""

    def __init__(self, model_name="openai/clip-vit-base-patch32", device=None):
        if device is None:
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "mps" if torch.backends.mps.is_available() else "cpu"
            )

        super().__init__(model_name, device)
        self.load_model()

    def load_model(self):
        """Load CLIP model and processor from HuggingFace."""
        print(f"Loading CLIP model: {self.model_name} on {self.device}...")
        self.processor = CLIPProcessor.from_pretrained(self.model_name)
        self.model = CLIPModel.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode
        print("✓ CLIP model loaded successfully")

    def encode_image(self, image_path):
        """Generate CLIP embedding for a single image."""
        image = self.load_image(image_path)
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)

        embedding = image_features.cpu().numpy()[0]
        return embedding / np.linalg.norm(embedding)

    def encode_batch(self, image_paths, batch_size=32):
        """Generate CLIP embeddings for multiple images."""
        all_embeddings = []

        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i : i + batch_size]
            images = [self.load_image(path) for path in batch_paths]
            inputs = self.processor(images=images, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)

            embeddings = image_features.cpu().numpy()
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings)

    def get_embedding_dim(self):
        """Return CLIP embedding dimensionality."""
        return 768 if "large" in self.model_name else 512

    def compute_similarity(self, embedding1, embedding2):
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2))

    def find_similar_images(self, query_embedding, database_embeddings, top_k=5, threshold=0.7):
        """Find most similar images in database."""
        similarities = np.dot(database_embeddings, query_embedding)
        valid_indices = np.where(similarities >= threshold)[0]
        valid_scores = similarities[valid_indices]
        sorted_indices = np.argsort(valid_scores)[::-1]

        return [(int(valid_indices[i]), float(valid_scores[i])) for i in sorted_indices[:top_k]]
