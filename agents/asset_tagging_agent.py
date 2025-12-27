import os
import yaml
from typing import List, Dict


class AssetTaggingAgent:
    def __init__(self, config_path: str = "config/asset_tagging.yaml"):
        """
        Initialize the asset tagging agent by loading taxonomy and vision service configuration.
        :param config_path: Path to the YAML configuration file containing taxonomy and service details.
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.taxonomy: Dict[str, List[str]] = self.config.get('taxonomy', {})
        self.vision_service: Dict[str, str] = self.config.get('vision_service', {})
        tagging_cfg = self.config.get('tagging', {})
        self.threshold: float = tagging_cfg.get('threshold', 0.5)
        self.assign_multiple: bool = tagging_cfg.get('assign_multiple', True)

    def _get_api_key(self) -> str:
        """
        Retrieve the API key for the vision service from the environment variable specified in the config.
        :return: API key string
        """
        env_var = self.vision_service.get('api_key_env')
        if not env_var:
            raise ValueError("No api_key_env specified in vision_service config")
        api_key = os.getenv(env_var)
        if not api_key:
            raise EnvironmentError(f"Environment variable {env_var} is not set")
        return api_key

    def _call_vision_service(self, image_path: str) -> Dict[str, float]:
        """
        Placeholder method for calling the configured vision service to detect tags for an image.
        Implement this method to call the external vision API and return a mapping of tag to confidence score.
        :param image_path: Path to the image file to be processed
        :return: Dictionary mapping tag names to confidence scores
        """
        # TODO: integrate with actual vision API using the API key and endpoint from self.vision_service
        raise NotImplementedError("Vision service integration not implemented yet")

    def tag_image(self, image_path: str) -> List[str]:
        """
        Assign tags to an image based on the vision service outputs and the taxonomy defined in the config.
        :param image_path: Path to the image file to be tagged
        :return: List of tags assigned to the image
        """
        tag_scores = self._call_vision_service(image_path)
        assigned_tags: List[str] = []
        for category, tags in self.taxonomy.items():
            if self.assign_multiple:
                # Assign all tags in this category that exceed the confidence threshold
                for tag in tags:
                    if tag_scores.get(tag, 0.0) >= self.threshold:
                        assigned_tags.append(tag)
            else:
                # Assign only the single highest-scoring tag in this category
                best_tag = None
                best_score = 0.0
                for tag in tags:
                    score = tag_scores.get(tag, 0.0)
                    if score > best_score:
                        best_score = score
                        best_tag = tag
                if best_tag is not None:
                    assigned_tags.append(best_tag)
        return assigned_tags
