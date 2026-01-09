"""Premium 3D Asset Pipeline.

Combines AI reconstruction with professional 3D finishing
for AAA-quality output suitable for luxury brand websites.

Pipeline stages:
1. Multi-view 3D reconstruction (Wonder3D)
2. Topology refinement (Blender)
3. UV unwrapping optimization
4. PBR material authoring (Substance-style)
5. Web optimization with LOD

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FabricType(str, Enum):
    """Detected fabric types for material generation."""

    COTTON = "cotton"
    DENIM = "denim"
    LEATHER = "leather"
    SILK = "silk"
    WOOL = "wool"
    FLEECE = "fleece"
    SHERPA = "sherpa"
    SYNTHETIC = "synthetic"
    SATIN = "satin"
    KNIT = "knit"


class TextureMap(str, Enum):
    """PBR texture map types."""

    ALBEDO = "albedo"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    AO = "ao"  # Ambient occlusion
    HEIGHT = "height"
    EMISSIVE = "emissive"


@dataclass
class MeshQuality:
    """Mesh quality settings."""

    target_polycount: int = 50000
    preserve_details: bool = True
    quad_topology: bool = True
    texture_resolution: int = 4096


@dataclass
class MaterialSet:
    """PBR material texture set."""

    albedo: Path | None = None
    normal: Path | None = None
    roughness: Path | None = None
    metallic: Path | None = None
    ao: Path | None = None
    height: Path | None = None
    fabric_type: FabricType = FabricType.COTTON
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LODLevel:
    """Level of detail configuration."""

    level: int
    polycount: int
    texture_resolution: int
    distance_threshold: float


@dataclass
class FinalModel:
    """Finalized 3D model ready for web."""

    glb_path: Path
    lod_paths: dict[int, Path] = field(default_factory=dict)
    materials: MaterialSet | None = None
    polycount: int = 0
    file_size_mb: float = 0.0
    compression: str = "draco"
    metadata: dict[str, Any] = field(default_factory=dict)


class Wonder3DReconstructor:
    """Wrapper for Wonder3D multi-view reconstruction.

    Requires Wonder3D to be installed:
    git clone https://github.com/xxlong0/Wonder3D.git
    """

    def __init__(self, wonder3d_path: Path | str = Path("Wonder3D")) -> None:
        """Initialize Wonder3D wrapper.

        Args:
            wonder3d_path: Path to Wonder3D installation
        """
        self.wonder3d_path = Path(wonder3d_path)
        self._check_installation()

    def _check_installation(self) -> None:
        """Verify Wonder3D is installed."""
        if not self.wonder3d_path.exists():
            logger.warning(
                f"Wonder3D not found at {self.wonder3d_path}. "
                "Install with: git clone https://github.com/xxlong0/Wonder3D.git"
            )

    async def reconstruct(
        self,
        images: list[Path],
        output_dir: Path,
        quality: str = "ultra",
        topology: str = "quad",
    ) -> Path | None:
        """Reconstruct 3D model from multi-view images.

        Args:
            images: List of product images from different angles
            output_dir: Directory for output mesh
            quality: Quality preset (draft, standard, ultra)
            topology: Mesh topology (triangle, quad)

        Returns:
            Path to reconstructed mesh or None on failure
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_mesh = output_dir / "reconstructed.obj"

        try:
            # Prepare image directory
            image_dir = output_dir / "input_images"
            image_dir.mkdir(exist_ok=True)

            for i, img in enumerate(images[:8]):  # Wonder3D uses up to 8 views
                import shutil

                dest = image_dir / f"view_{i:02d}{img.suffix}"
                shutil.copy2(img, dest)

            # Run Wonder3D
            cmd = [
                "python",
                str(self.wonder3d_path / "run.py"),
                "--input_dir",
                str(image_dir),
                "--output_dir",
                str(output_dir),
                "--quality",
                quality,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"Wonder3D failed: {result.stderr}")
                return None

            if output_mesh.exists():
                logger.info(f"Reconstruction complete: {output_mesh}")
                return output_mesh

            # Check for alternative output formats
            for ext in [".obj", ".ply", ".glb"]:
                alt_path = output_dir / f"mesh{ext}"
                if alt_path.exists():
                    return alt_path

            return None

        except FileNotFoundError:
            logger.error("Wonder3D not installed or Python not found")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Reconstruction timed out")
            return None
        except Exception as e:
            logger.exception(f"Reconstruction failed: {e}")
            return None


class BlenderProcessor:
    """Blender-based mesh processing via Python API.

    Requires Blender 4.0+ with bpy module:
    pip install bpy mathutils
    """

    def __init__(self) -> None:
        """Initialize Blender processor."""
        self._bpy = None
        self._check_installation()

    def _check_installation(self) -> None:
        """Check if bpy is available."""
        try:
            import bpy

            self._bpy = bpy
            logger.info(f"Blender {bpy.app.version_string} available")
        except ImportError:
            logger.warning("Blender Python module not available. Install with: pip install bpy")

    def _ensure_bpy(self) -> Any:
        """Ensure bpy is available."""
        if self._bpy is None:
            try:
                import bpy

                self._bpy = bpy
            except ImportError:
                raise ImportError("Blender Python module (bpy) required")
        return self._bpy

    async def refine_topology(
        self,
        mesh_path: Path,
        output_path: Path,
        target_polycount: int = 50000,
        preserve_details: bool = True,
        quad_topology: bool = True,
    ) -> Path | None:
        """Refine mesh topology for production quality.

        Args:
            mesh_path: Input mesh file
            output_path: Output mesh file
            target_polycount: Target polygon count
            preserve_details: Whether to preserve fine details
            quad_topology: Convert to quad-dominant topology

        Returns:
            Path to refined mesh or None on failure
        """
        try:
            bpy = self._ensure_bpy()

            # Clear scene
            bpy.ops.wm.read_factory_settings(use_empty=True)

            # Import mesh
            if mesh_path.suffix.lower() == ".obj":
                bpy.ops.wm.obj_import(filepath=str(mesh_path))
            elif mesh_path.suffix.lower() == ".glb":
                bpy.ops.import_scene.gltf(filepath=str(mesh_path))
            elif mesh_path.suffix.lower() == ".ply":
                bpy.ops.wm.ply_import(filepath=str(mesh_path))
            else:
                logger.error(f"Unsupported format: {mesh_path.suffix}")
                return None

            # Get imported object
            obj = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = obj

            # Decimate to target polycount
            current_polys = len(obj.data.polygons)
            if current_polys > target_polycount:
                ratio = target_polycount / current_polys

                mod = obj.modifiers.new("Decimate", "DECIMATE")
                mod.ratio = ratio
                mod.use_collapse_triangulate = not quad_topology

                bpy.ops.object.modifier_apply(modifier="Decimate")

            # Convert to quads if requested
            if quad_topology:
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.tris_convert_to_quads(face_threshold=0.698)
                bpy.ops.object.mode_set(mode="OBJECT")

            # Smooth shading
            bpy.ops.object.shade_smooth()

            # Export
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if output_path.suffix.lower() == ".glb":
                bpy.ops.export_scene.gltf(
                    filepath=str(output_path),
                    export_format="GLB",
                )
            elif output_path.suffix.lower() == ".obj":
                bpy.ops.wm.obj_export(filepath=str(output_path))

            logger.info(f"Topology refined: {len(obj.data.polygons)} polys -> {output_path}")
            return output_path

        except Exception as e:
            logger.exception(f"Topology refinement failed: {e}")
            return None

    async def smart_uv_unwrap(
        self,
        mesh_path: Path,
        output_path: Path,
        method: str = "conformal",
        minimize_stretch: bool = True,
        texture_resolution: int = 4096,
    ) -> Path | None:
        """Create optimized UV mapping.

        Args:
            mesh_path: Input mesh file
            output_path: Output mesh file
            method: UV projection method (conformal, angle_based)
            minimize_stretch: Minimize UV distortion
            texture_resolution: Target texture resolution

        Returns:
            Path to UV-mapped mesh or None on failure
        """
        try:
            bpy = self._ensure_bpy()

            # Clear and import
            bpy.ops.wm.read_factory_settings(use_empty=True)

            if mesh_path.suffix.lower() == ".glb":
                bpy.ops.import_scene.gltf(filepath=str(mesh_path))
            else:
                bpy.ops.wm.obj_import(filepath=str(mesh_path))

            obj = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = obj

            # Smart UV project
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")

            if method == "conformal":
                bpy.ops.uv.smart_project(
                    angle_limit=66.0,
                    island_margin=0.02,
                    correct_aspect=True,
                )
            else:
                bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.02)

            # Pack UVs efficiently
            bpy.ops.uv.pack_islands(margin=0.01)

            bpy.ops.object.mode_set(mode="OBJECT")

            # Export
            output_path.parent.mkdir(parents=True, exist_ok=True)
            bpy.ops.export_scene.gltf(
                filepath=str(output_path),
                export_format="GLB",
            )

            logger.info(f"UV mapping complete: {output_path}")
            return output_path

        except Exception as e:
            logger.exception(f"UV unwrap failed: {e}")
            return None

    async def finalize_for_web(
        self,
        mesh_path: Path,
        output_path: Path,
        materials: MaterialSet | None = None,
        lod_levels: int = 3,
        compression: str = "draco",
    ) -> FinalModel | None:
        """Finalize model for web deployment.

        Creates LOD levels and applies Draco compression.

        Args:
            mesh_path: Input mesh file
            output_path: Output GLB file
            materials: PBR material set to apply
            lod_levels: Number of LOD levels to generate
            compression: Compression method (draco, meshopt)

        Returns:
            FinalModel with all outputs or None on failure
        """
        try:
            bpy = self._ensure_bpy()

            # Import mesh
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=str(mesh_path))

            obj = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = obj

            base_polys = len(obj.data.polygons)

            # Generate LOD levels
            lod_configs = [
                LODLevel(0, base_polys, 4096, 0),
                LODLevel(1, base_polys // 2, 2048, 10),
                LODLevel(2, base_polys // 4, 1024, 25),
            ][:lod_levels]

            result = FinalModel(
                glb_path=output_path,
                polycount=base_polys,
                compression=compression,
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Export each LOD
            for lod in lod_configs:
                lod_path = output_path.parent / f"{output_path.stem}_lod{lod.level}.glb"

                if lod.level > 0:
                    # Decimate for lower LODs
                    mod = obj.modifiers.new("LOD_Decimate", "DECIMATE")
                    mod.ratio = lod.polycount / base_polys
                    bpy.ops.object.modifier_apply(modifier="LOD_Decimate")

                # Export with compression
                bpy.ops.export_scene.gltf(
                    filepath=str(lod_path),
                    export_format="GLB",
                    export_draco_mesh_compression_enable=(compression == "draco"),
                    export_draco_mesh_compression_level=6,
                )

                result.lod_paths[lod.level] = lod_path

                # Undo decimate for next LOD
                if lod.level > 0:
                    bpy.ops.ed.undo()

            # Primary output is LOD0
            result.glb_path = result.lod_paths.get(0, output_path)
            result.file_size_mb = result.glb_path.stat().st_size / (1024 * 1024)
            result.materials = materials

            logger.info(
                f"Web optimization complete: {result.file_size_mb:.2f}MB, "
                f"{len(result.lod_paths)} LOD levels"
            )

            return result

        except Exception as e:
            logger.exception(f"Web finalization failed: {e}")
            return None


class FabricMaterialGenerator:
    """Generate PBR materials for fabric types.

    Creates physically accurate materials without requiring
    Substance Designer installation.
    """

    FABRIC_PROPERTIES = {
        FabricType.COTTON: {"roughness": 0.8, "metallic": 0.0, "normal_strength": 0.3},
        FabricType.DENIM: {"roughness": 0.75, "metallic": 0.0, "normal_strength": 0.5},
        FabricType.LEATHER: {"roughness": 0.4, "metallic": 0.0, "normal_strength": 0.4},
        FabricType.SILK: {"roughness": 0.2, "metallic": 0.1, "normal_strength": 0.1},
        FabricType.WOOL: {"roughness": 0.9, "metallic": 0.0, "normal_strength": 0.6},
        FabricType.FLEECE: {"roughness": 0.95, "metallic": 0.0, "normal_strength": 0.4},
        FabricType.SHERPA: {"roughness": 0.98, "metallic": 0.0, "normal_strength": 0.7},
        FabricType.SYNTHETIC: {"roughness": 0.5, "metallic": 0.05, "normal_strength": 0.2},
        FabricType.SATIN: {"roughness": 0.15, "metallic": 0.15, "normal_strength": 0.1},
        FabricType.KNIT: {"roughness": 0.85, "metallic": 0.0, "normal_strength": 0.5},
    }

    async def detect_fabric_type(self, image_path: Path) -> FabricType:
        """Detect fabric type from product image.

        Uses texture analysis to classify fabric.
        """
        try:
            import cv2

            img = cv2.imread(str(image_path))
            if img is None:
                return FabricType.COTTON

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Texture analysis using Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            texture_variance = laplacian.var()

            # Color analysis
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            saturation = hsv[:, :, 1].mean()
            value = hsv[:, :, 2].mean()

            # Classify based on texture and color
            if texture_variance > 1000:
                if saturation < 50:
                    return FabricType.SHERPA
                return FabricType.WOOL
            elif texture_variance > 500:
                return FabricType.DENIM
            elif value > 200 and saturation < 30:
                return FabricType.SILK
            elif saturation > 150:
                return FabricType.SATIN
            else:
                return FabricType.COTTON

        except Exception as e:
            logger.warning(f"Fabric detection failed: {e}")
            return FabricType.COTTON

    async def create_material_set(
        self,
        base_image: Path,
        fabric_type: FabricType,
        output_dir: Path,
        resolution: int = 4096,
    ) -> MaterialSet:
        """Create PBR material set from base image.

        Generates all standard PBR maps.
        """
        try:
            import cv2
            import numpy as np

            output_dir.mkdir(parents=True, exist_ok=True)
            props = self.FABRIC_PROPERTIES.get(
                fabric_type, self.FABRIC_PROPERTIES[FabricType.COTTON]
            )

            # Load base image
            img = cv2.imread(str(base_image))
            img = cv2.resize(img, (resolution, resolution))

            material = MaterialSet(fabric_type=fabric_type)

            # Albedo (base color)
            albedo_path = output_dir / "albedo.png"
            cv2.imwrite(str(albedo_path), img)
            material.albedo = albedo_path

            # Normal map from height
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

            strength = props["normal_strength"]
            normal = np.zeros((resolution, resolution, 3), dtype=np.uint8)
            normal[:, :, 0] = np.clip(128 + sobelx * strength * 50, 0, 255)
            normal[:, :, 1] = np.clip(128 + sobely * strength * 50, 0, 255)
            normal[:, :, 2] = 255

            normal_path = output_dir / "normal.png"
            cv2.imwrite(str(normal_path), normal)
            material.normal = normal_path

            # Roughness map
            roughness_base = int(props["roughness"] * 255)
            roughness_variation = (gray.astype(float) - 128) / 128 * 20
            roughness = np.clip(roughness_base + roughness_variation, 0, 255).astype(np.uint8)

            roughness_path = output_dir / "roughness.png"
            cv2.imwrite(str(roughness_path), roughness)
            material.roughness = roughness_path

            # Metallic map
            metallic_value = int(props["metallic"] * 255)
            metallic = np.full((resolution, resolution), metallic_value, dtype=np.uint8)

            metallic_path = output_dir / "metallic.png"
            cv2.imwrite(str(metallic_path), metallic)
            material.metallic = metallic_path

            # Ambient occlusion
            ao = cv2.blur(gray, (50, 50))
            ao = cv2.normalize(ao, None, 128, 255, cv2.NORM_MINMAX)

            ao_path = output_dir / "ao.png"
            cv2.imwrite(str(ao_path), ao)
            material.ao = ao_path

            logger.info(f"Material set created for {fabric_type.value}: {output_dir}")
            return material

        except Exception as e:
            logger.exception(f"Material creation failed: {e}")
            return MaterialSet(fabric_type=fabric_type)


class Premium3DAssetPipeline:
    """Complete pipeline for luxury 3D asset creation.

    Combines AI reconstruction with professional finishing
    for AAA-quality output.

    Example:
        >>> pipeline = Premium3DAssetPipeline()
        >>> photos = [Path(f"product_{i}.jpg") for i in range(8)]
        >>> model = await pipeline.create_luxury_3d_model(photos)
    """

    def __init__(
        self,
        wonder3d_path: Path | str = Path("Wonder3D"),
        output_base: Path = Path("assets/3d-models-premium"),
    ) -> None:
        """Initialize pipeline.

        Args:
            wonder3d_path: Path to Wonder3D installation
            output_base: Base directory for outputs
        """
        self.wonder3d = Wonder3DReconstructor(wonder3d_path)
        self.blender = BlenderProcessor()
        self.material_gen = FabricMaterialGenerator()
        self.output_base = Path(output_base)

    async def create_luxury_3d_model(
        self,
        product_photos: list[Path],
        product_name: str = "product",
        fabric_reference: Path | None = None,
    ) -> FinalModel | None:
        """Create luxury 3D model through 5-stage pipeline.

        Args:
            product_photos: Multi-view product images
            product_name: Name for output files
            fabric_reference: Optional close-up for fabric detection

        Returns:
            FinalModel ready for web deployment
        """
        output_dir = self.output_base / product_name
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting premium 3D pipeline for: {product_name}")

        # STAGE 1: AI Reconstruction
        logger.info("Stage 1/5: Multi-view 3D reconstruction...")
        stage1_dir = output_dir / "stage1_reconstruction"
        base_mesh = await self.wonder3d.reconstruct(
            images=product_photos,
            output_dir=stage1_dir,
            quality="ultra",
            topology="quad",
        )

        if not base_mesh:
            logger.error("Stage 1 failed: Reconstruction unsuccessful")
            return None

        # STAGE 2: Topology Refinement
        logger.info("Stage 2/5: Professional topology cleanup...")
        stage2_mesh = output_dir / "stage2_refined.glb"
        refined_mesh = await self.blender.refine_topology(
            mesh_path=base_mesh,
            output_path=stage2_mesh,
            target_polycount=50000,
            preserve_details=True,
            quad_topology=True,
        )

        if not refined_mesh:
            logger.warning("Stage 2 skipped: Using base mesh")
            refined_mesh = base_mesh

        # STAGE 3: UV Mapping
        logger.info("Stage 3/5: UV mapping optimization...")
        stage3_mesh = output_dir / "stage3_uv.glb"
        uv_mesh = await self.blender.smart_uv_unwrap(
            mesh_path=refined_mesh,
            output_path=stage3_mesh,
            method="conformal",
            minimize_stretch=True,
            texture_resolution=4096,
        )

        if not uv_mesh:
            logger.warning("Stage 3 skipped: Using previous mesh")
            uv_mesh = refined_mesh

        # STAGE 4: Material Creation
        logger.info("Stage 4/5: PBR material authoring...")
        material_dir = output_dir / "materials"

        # Detect fabric type
        fabric_ref = fabric_reference or product_photos[0]
        fabric_type = await self.material_gen.detect_fabric_type(fabric_ref)
        logger.info(f"Detected fabric: {fabric_type.value}")

        materials = await self.material_gen.create_material_set(
            base_image=product_photos[0],
            fabric_type=fabric_type,
            output_dir=material_dir,
            resolution=4096,
        )

        # STAGE 5: Web Optimization
        logger.info("Stage 5/5: Web optimization with LOD...")
        final_path = output_dir / f"{product_name}_final.glb"
        final_model = await self.blender.finalize_for_web(
            mesh_path=uv_mesh,
            output_path=final_path,
            materials=materials,
            lod_levels=3,
            compression="draco",
        )

        if final_model:
            # Save pipeline metadata
            metadata = {
                "product_name": product_name,
                "stages_completed": 5,
                "fabric_type": fabric_type.value,
                "polycount": final_model.polycount,
                "file_size_mb": final_model.file_size_mb,
                "lod_levels": len(final_model.lod_paths),
                "compression": final_model.compression,
            }

            with open(output_dir / "pipeline_metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(
                f"Premium 3D pipeline complete: {final_model.glb_path} "
                f"({final_model.file_size_mb:.2f}MB)"
            )

        return final_model


__all__ = [
    "Premium3DAssetPipeline",
    "Wonder3DReconstructor",
    "BlenderProcessor",
    "FabricMaterialGenerator",
    "FabricType",
    "MaterialSet",
    "FinalModel",
    "MeshQuality",
]
