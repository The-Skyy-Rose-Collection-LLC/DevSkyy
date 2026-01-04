"""Headless 3D Model Renderer.

Renders GLB/GLTF 3D models to 2D images for visual comparison.
Supports multiple camera angles and lighting presets.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Set headless rendering before importing pyrender
os.environ["PYOPENGL_PLATFORM"] = "osmesa"  # or "egl" on Linux with GPU

# Optional imports with availability flags
try:
    import trimesh

    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    logger.warning("trimesh not available. 3D model loading disabled.")

try:
    import pyrender

    PYRENDER_AVAILABLE = True
except ImportError:
    PYRENDER_AVAILABLE = False
    logger.warning("pyrender not available. 3D rendering disabled.")


class LightingPreset(str, Enum):
    """Lighting configurations for rendering."""

    STUDIO = "studio"
    AMBIENT = "ambient"
    PRODUCT = "product"
    DRAMATIC = "dramatic"


class CameraAngle(str, Enum):
    """Standard camera angles for product photography."""

    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    THREE_QUARTER = "three_quarter"
    TOP = "top"
    BOTTOM = "bottom"


# Camera position configurations (azimuth, elevation in degrees)
CAMERA_POSITIONS: dict[CameraAngle, tuple[float, float]] = {
    CameraAngle.FRONT: (0.0, 0.0),
    CameraAngle.BACK: (180.0, 0.0),
    CameraAngle.LEFT: (90.0, 0.0),
    CameraAngle.RIGHT: (-90.0, 0.0),
    CameraAngle.THREE_QUARTER: (45.0, 20.0),
    CameraAngle.TOP: (0.0, 80.0),
    CameraAngle.BOTTOM: (0.0, -80.0),
}


@dataclass
class RenderConfig:
    """Configuration for 3D rendering."""

    resolution: tuple[int, int] = (1024, 1024)
    background_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    lighting: LightingPreset = LightingPreset.PRODUCT
    angles: list[CameraAngle] = field(
        default_factory=lambda: [CameraAngle.FRONT, CameraAngle.THREE_QUARTER]
    )
    camera_distance_factor: float = 2.5  # Multiplier of model bounding sphere


@dataclass
class RenderResult:
    """Result of 3D model rendering."""

    success: bool
    images: dict[str, Path]  # angle -> image path
    model_info: dict[str, Any]
    errors: list[str] = field(default_factory=list)


class HeadlessRenderer:
    """Renders 3D models (GLB/GLTF) to 2D images without a display.

    Uses trimesh for model loading and pyrender for rendering.
    Works in headless environments (servers, CI/CD).
    """

    def __init__(self, config: RenderConfig | None = None) -> None:
        """Initialize renderer.

        Args:
            config: Rendering configuration
        """
        self.config = config or RenderConfig()
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """Check required dependencies are available."""
        if not TRIMESH_AVAILABLE:
            logger.error("trimesh required but not installed")
        if not PYRENDER_AVAILABLE:
            logger.error("pyrender required but not installed")

    def _load_model(self, model_path: Path) -> Any:
        """Load 3D model from file.

        Args:
            model_path: Path to GLB/GLTF file

        Returns:
            trimesh.Scene or trimesh.Trimesh object
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not available")

        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        # Load with trimesh
        mesh = trimesh.load(str(model_path), force="scene")
        logger.info(f"Loaded model: {model_path.name}, type: {type(mesh).__name__}")
        return mesh

    def _get_camera_pose(
        self,
        angle: CameraAngle,
        center: np.ndarray,
        distance: float,
    ) -> np.ndarray:
        """Calculate camera pose matrix for given angle.

        Args:
            angle: Camera angle preset
            center: Model center point
            distance: Camera distance from center

        Returns:
            4x4 camera pose matrix
        """
        azimuth_deg, elevation_deg = CAMERA_POSITIONS[angle]
        azimuth = np.radians(azimuth_deg)
        elevation = np.radians(elevation_deg)

        # Calculate camera position
        x = distance * np.cos(elevation) * np.sin(azimuth)
        y = distance * np.sin(elevation)
        z = distance * np.cos(elevation) * np.cos(azimuth)

        camera_pos = center + np.array([x, y, z])

        # Look-at matrix
        forward = center - camera_pos
        forward = forward / np.linalg.norm(forward)

        up = np.array([0.0, 1.0, 0.0])
        right = np.cross(forward, up)
        if np.linalg.norm(right) < 1e-6:
            up = np.array([0.0, 0.0, 1.0])
            right = np.cross(forward, up)
        right = right / np.linalg.norm(right)
        up = np.cross(right, forward)

        # Build rotation matrix
        pose = np.eye(4)
        pose[:3, 0] = right
        pose[:3, 1] = up
        pose[:3, 2] = -forward
        pose[:3, 3] = camera_pos

        return pose

    def _setup_lighting(self, scene: Any, preset: LightingPreset) -> None:
        """Add lights to scene based on preset.

        Args:
            scene: pyrender Scene
            preset: Lighting configuration
        """
        if not PYRENDER_AVAILABLE:
            return

        if preset == LightingPreset.STUDIO:
            # Three-point lighting
            scene.add(
                pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0),
                pose=self._get_camera_pose(CameraAngle.THREE_QUARTER, np.zeros(3), 5.0),
            )
            scene.add(
                pyrender.DirectionalLight(color=[0.8, 0.8, 1.0], intensity=1.5),
                pose=self._get_camera_pose(CameraAngle.LEFT, np.zeros(3), 5.0),
            )
            scene.add(
                pyrender.DirectionalLight(color=[1.0, 0.9, 0.8], intensity=1.0),
                pose=self._get_camera_pose(CameraAngle.BACK, np.zeros(3), 5.0),
            )

        elif preset == LightingPreset.AMBIENT:
            # Soft ambient lighting
            scene.ambient_light = [0.5, 0.5, 0.5]
            scene.add(
                pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0),
                pose=self._get_camera_pose(CameraAngle.TOP, np.zeros(3), 5.0),
            )

        elif preset == LightingPreset.PRODUCT:
            # E-commerce style lighting
            scene.ambient_light = [0.3, 0.3, 0.3]
            scene.add(
                pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=4.0),
                pose=self._get_camera_pose(CameraAngle.FRONT, np.zeros(3), 5.0),
            )
            scene.add(
                pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0),
                pose=self._get_camera_pose(CameraAngle.THREE_QUARTER, np.zeros(3), 5.0),
            )
            scene.add(
                pyrender.SpotLight(
                    color=[1.0, 1.0, 1.0], intensity=2.0, innerConeAngle=0.5, outerConeAngle=1.0
                ),
                pose=self._get_camera_pose(CameraAngle.TOP, np.zeros(3), 3.0),
            )

        elif preset == LightingPreset.DRAMATIC:
            # High contrast lighting
            scene.ambient_light = [0.1, 0.1, 0.1]
            scene.add(
                pyrender.DirectionalLight(color=[1.0, 0.95, 0.9], intensity=5.0),
                pose=self._get_camera_pose(CameraAngle.THREE_QUARTER, np.zeros(3), 5.0),
            )

    def render_model(
        self,
        model_path: Path | str,
        output_dir: Path | str,
        angles: list[CameraAngle] | None = None,
    ) -> RenderResult:
        """Render 3D model to 2D images from multiple angles.

        Args:
            model_path: Path to GLB/GLTF file
            output_dir: Directory to save rendered images
            angles: Camera angles to render (uses config default if None)

        Returns:
            RenderResult with paths to rendered images
        """
        if not TRIMESH_AVAILABLE or not PYRENDER_AVAILABLE:
            return RenderResult(
                success=False,
                images={},
                model_info={},
                errors=["trimesh and pyrender required for rendering"],
            )

        model_path = Path(model_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        angles = angles or self.config.angles
        errors: list[str] = []
        images: dict[str, Path] = {}

        try:
            # Load model
            mesh = self._load_model(model_path)

            # Get model bounds
            if isinstance(mesh, trimesh.Scene):
                bounds = mesh.bounds
                extents = mesh.extents
            else:
                bounds = mesh.bounds
                extents = mesh.extents

            center = (bounds[0] + bounds[1]) / 2
            max_extent = max(extents)
            distance = max_extent * self.config.camera_distance_factor

            model_info = {
                "bounds": bounds.tolist(),
                "extents": extents.tolist(),
                "center": center.tolist(),
                "name": model_path.stem,
            }

            # Convert to pyrender scene
            scene = pyrender.Scene(
                bg_color=self.config.background_color,
                ambient_light=[0.2, 0.2, 0.2],
            )

            # Add mesh to scene
            if isinstance(mesh, trimesh.Scene):
                for node_name, _node in mesh.graph.nodes_geometry:
                    transform, geometry_name = mesh.graph[node_name]
                    geometry = mesh.geometry[geometry_name]
                    if hasattr(geometry, "visual") and geometry.visual is not None:
                        material = pyrender.MetallicRoughnessMaterial(
                            baseColorFactor=[0.8, 0.8, 0.8, 1.0],
                            metallicFactor=0.2,
                            roughnessFactor=0.5,
                        )
                        py_mesh = pyrender.Mesh.from_trimesh(geometry, material=material)
                    else:
                        py_mesh = pyrender.Mesh.from_trimesh(geometry)
                    scene.add(py_mesh, pose=transform)
            else:
                py_mesh = pyrender.Mesh.from_trimesh(mesh)
                scene.add(py_mesh)

            # Setup lighting
            self._setup_lighting(scene, self.config.lighting)

            # Setup camera
            camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)

            # Create renderer
            renderer = pyrender.OffscreenRenderer(
                viewport_width=self.config.resolution[0],
                viewport_height=self.config.resolution[1],
            )

            # Render each angle
            for angle in angles:
                try:
                    pose = self._get_camera_pose(angle, center, distance)

                    # Add camera (remove previous if exists)
                    camera_node = scene.add(camera, pose=pose)

                    # Render
                    color, depth = renderer.render(scene)

                    # Save image
                    output_path = output_dir / f"{model_path.stem}_{angle.value}.png"
                    Image.fromarray(color).save(output_path)
                    images[angle.value] = output_path

                    # Remove camera for next angle
                    scene.remove_node(camera_node)

                    logger.info(f"Rendered {angle.value}: {output_path}")

                except Exception as e:
                    errors.append(f"Failed to render {angle.value}: {e}")
                    logger.error(f"Render error for {angle.value}: {e}")

            renderer.delete()

            return RenderResult(
                success=len(images) > 0,
                images=images,
                model_info=model_info,
                errors=errors,
            )

        except Exception as e:
            logger.exception(f"Rendering failed: {e}")
            return RenderResult(
                success=False,
                images={},
                model_info={},
                errors=[str(e)],
            )

    def render_silhouette(
        self,
        model_path: Path | str,
        output_path: Path | str,
        angle: CameraAngle = CameraAngle.FRONT,
    ) -> Path | None:
        """Render model silhouette (black shape on white background).

        Useful for shape comparison.

        Args:
            model_path: Path to GLB/GLTF file
            output_path: Path to save silhouette image
            angle: Camera angle

        Returns:
            Path to silhouette image or None on failure
        """
        if not TRIMESH_AVAILABLE or not PYRENDER_AVAILABLE:
            return None

        model_path = Path(model_path)
        output_path = Path(output_path)

        try:
            mesh = self._load_model(model_path)

            # Create scene with white background
            scene = pyrender.Scene(
                bg_color=(1.0, 1.0, 1.0, 1.0),
                ambient_light=[0.0, 0.0, 0.0],
            )

            # Add mesh with solid black material
            black_material = pyrender.MetallicRoughnessMaterial(
                baseColorFactor=[0.0, 0.0, 0.0, 1.0],
                metallicFactor=0.0,
                roughnessFactor=1.0,
            )

            if isinstance(mesh, trimesh.Scene):
                for node_name, _node in mesh.graph.nodes_geometry:
                    transform, geometry_name = mesh.graph[node_name]
                    geometry = mesh.geometry[geometry_name]
                    py_mesh = pyrender.Mesh.from_trimesh(geometry, material=black_material)
                    scene.add(py_mesh, pose=transform)
            else:
                py_mesh = pyrender.Mesh.from_trimesh(mesh, material=black_material)
                scene.add(py_mesh)

            # Add strong front light
            scene.add(
                pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=5.0),
                pose=np.eye(4),
            )

            # Setup camera
            bounds = mesh.bounds if hasattr(mesh, "bounds") else mesh.bounding_box.bounds
            center = (bounds[0] + bounds[1]) / 2
            extents = bounds[1] - bounds[0]
            distance = max(extents) * self.config.camera_distance_factor

            camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
            pose = self._get_camera_pose(angle, center, distance)
            scene.add(camera, pose=pose)

            # Render
            renderer = pyrender.OffscreenRenderer(
                viewport_width=self.config.resolution[0],
                viewport_height=self.config.resolution[1],
            )
            color, _ = renderer.render(scene)
            renderer.delete()

            # Save silhouette
            output_path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(color).save(output_path)

            return output_path

        except Exception as e:
            logger.exception(f"Silhouette rendering failed: {e}")
            return None

    async def render_model_async(
        self,
        model_path: Path | str,
        output_dir: Path | str,
        angles: list[CameraAngle] | None = None,
    ) -> RenderResult:
        """Async wrapper for render_model()."""
        import asyncio

        return await asyncio.get_event_loop().run_in_executor(
            None, self.render_model, model_path, output_dir, angles
        )


# Convenience function
def render_glb_to_images(
    model_path: Path | str,
    output_dir: Path | str,
    angles: list[str] | None = None,
) -> RenderResult:
    """Render GLB model to images from multiple angles.

    Args:
        model_path: Path to GLB file
        output_dir: Directory for output images
        angles: List of angle names ("front", "three_quarter", etc.)

    Returns:
        RenderResult with image paths

    Example:
        >>> result = render_glb_to_images("model.glb", "./renders")
        >>> if result.success:
        ...     for angle, path in result.images.items():
        ...         print(f"{angle}: {path}")
    """
    renderer = HeadlessRenderer()

    if angles:
        camera_angles = [CameraAngle(a) for a in angles]
    else:
        camera_angles = None

    return renderer.render_model(model_path, output_dir, camera_angles)


__all__ = [
    "HeadlessRenderer",
    "RenderConfig",
    "RenderResult",
    "LightingPreset",
    "CameraAngle",
    "render_glb_to_images",
]
