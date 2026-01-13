"""
WordPress 3D Viewer Plugin Generator
=====================================

Generate WordPress plugin files for the SkyyRose 3D product viewer.

Features:
- Three.js 3D model viewer
- GLB/GLTF model loading
- OrbitControls for interaction
- AR Quick Look integration (iOS)
- WebXR support (Android)
- Shortcode for easy embedding
- WooCommerce product integration

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# Plugin Configuration
# =============================================================================


@dataclass
class ViewerConfig:
    """Configuration for the 3D viewer."""

    # Viewer settings
    auto_rotate: bool = True
    auto_rotate_speed: float = 2.0
    enable_zoom: bool = True
    enable_pan: bool = False
    min_distance: float = 1.0
    max_distance: float = 10.0
    camera_fov: float = 45.0

    # Lighting
    ambient_intensity: float = 0.5
    directional_intensity: float = 1.0
    shadow_enabled: bool = True

    # AR settings
    ar_button_text: str = "View in AR"
    ar_enabled: bool = True

    # UI settings
    loading_text: str = "Loading 3D Model..."
    error_text: str = "Failed to load 3D model"
    show_controls: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "autoRotate": self.auto_rotate,
            "autoRotateSpeed": self.auto_rotate_speed,
            "enableZoom": self.enable_zoom,
            "enablePan": self.enable_pan,
            "minDistance": self.min_distance,
            "maxDistance": self.max_distance,
            "cameraFov": self.camera_fov,
            "ambientIntensity": self.ambient_intensity,
            "directionalIntensity": self.directional_intensity,
            "shadowEnabled": self.shadow_enabled,
            "arButtonText": self.ar_button_text,
            "arEnabled": self.ar_enabled,
            "loadingText": self.loading_text,
            "errorText": self.error_text,
            "showControls": self.show_controls,
        }


# =============================================================================
# JavaScript Generator
# =============================================================================


def generate_viewer_javascript(config: ViewerConfig) -> str:
    """Generate the 3D viewer JavaScript code."""
    config_json = json.dumps(config.to_dict(), indent=2)

    return f"""/**
 * SkyyRose 3D Product Viewer
 * ==========================
 * Interactive 3D model viewer using Three.js
 *
 * @version 1.0.0
 * @author DevSkyy Platform Team
 */

(function() {{
    'use strict';

    // Default configuration
    const DEFAULT_CONFIG = {config_json};

    // Three.js dependencies loaded check
    let THREE_LOADED = false;
    let GLTF_LOADER_LOADED = false;
    let ORBIT_CONTROLS_LOADED = false;

    /**
     * SkyyRose3DViewer class
     */
    class SkyyRose3DViewer {{
        constructor(container, modelUrl, options = {{}}) {{
            this.container = container;
            this.modelUrl = modelUrl;
            this.config = {{ ...DEFAULT_CONFIG, ...options }};

            this.scene = null;
            this.camera = null;
            this.renderer = null;
            this.controls = null;
            this.model = null;
            this.mixer = null;
            this.clock = new THREE.Clock();

            this.init();
        }}

        init() {{
            // Create scene
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0xf5f5f5);

            // Create camera
            const width = this.container.clientWidth || 400;
            const height = this.container.clientHeight || 400;
            this.camera = new THREE.PerspectiveCamera(
                this.config.cameraFov,
                width / height,
                0.1,
                1000
            );
            this.camera.position.set(0, 1, 3);

            // Create renderer
            this.renderer = new THREE.WebGLRenderer({{
                antialias: true,
                alpha: true
            }});
            this.renderer.setSize(width, height);
            this.renderer.setPixelRatio(window.devicePixelRatio);
            this.renderer.outputEncoding = THREE.sRGBEncoding;
            this.renderer.toneMapping = THREE.ACESFilmicToneMapping;

            if (this.config.shadowEnabled) {{
                this.renderer.shadowMap.enabled = true;
                this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            }}

            this.container.appendChild(this.renderer.domElement);

            // Add lighting
            this.addLighting();

            // Add controls
            if (typeof THREE.OrbitControls !== 'undefined') {{
                this.controls = new THREE.OrbitControls(
                    this.camera,
                    this.renderer.domElement
                );
                this.controls.enableDamping = true;
                this.controls.dampingFactor = 0.05;
                this.controls.autoRotate = this.config.autoRotate;
                this.controls.autoRotateSpeed = this.config.autoRotateSpeed;
                this.controls.enableZoom = this.config.enableZoom;
                this.controls.enablePan = this.config.enablePan;
                this.controls.minDistance = this.config.minDistance;
                this.controls.maxDistance = this.config.maxDistance;
            }}

            // Load model
            this.loadModel();

            // Handle resize
            window.addEventListener('resize', () => this.onResize());

            // Start animation loop
            this.animate();
        }}

        addLighting() {{
            // Ambient light
            const ambient = new THREE.AmbientLight(
                0xffffff,
                this.config.ambientIntensity
            );
            this.scene.add(ambient);

            // Directional light (key light)
            const directional = new THREE.DirectionalLight(
                0xffffff,
                this.config.directionalIntensity
            );
            directional.position.set(5, 5, 5);

            if (this.config.shadowEnabled) {{
                directional.castShadow = true;
                directional.shadow.mapSize.width = 1024;
                directional.shadow.mapSize.height = 1024;
            }}

            this.scene.add(directional);

            // Fill light
            const fill = new THREE.DirectionalLight(0xffffff, 0.3);
            fill.position.set(-5, 3, -5);
            this.scene.add(fill);

            // Rim light
            const rim = new THREE.DirectionalLight(0xffffff, 0.2);
            rim.position.set(0, 5, -5);
            this.scene.add(rim);
        }}

        loadModel() {{
            // Show loading indicator
            this.showLoading();

            const loader = new THREE.GLTFLoader();

            loader.load(
                this.modelUrl,
                (gltf) => {{
                    this.model = gltf.scene;

                    // Center and scale model
                    const box = new THREE.Box3().setFromObject(this.model);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());

                    const maxDim = Math.max(size.x, size.y, size.z);
                    const scale = 2 / maxDim;
                    this.model.scale.multiplyScalar(scale);

                    this.model.position.sub(center.multiplyScalar(scale));

                    // Enable shadows
                    if (this.config.shadowEnabled) {{
                        this.model.traverse((child) => {{
                            if (child.isMesh) {{
                                child.castShadow = true;
                                child.receiveShadow = true;
                            }}
                        }});
                    }}

                    this.scene.add(this.model);

                    // Handle animations
                    if (gltf.animations.length > 0) {{
                        this.mixer = new THREE.AnimationMixer(this.model);
                        gltf.animations.forEach((clip) => {{
                            this.mixer.clipAction(clip).play();
                        }});
                    }}

                    this.hideLoading();
                }},
                (progress) => {{
                    // Update loading progress
                    if (progress.total > 0) {{
                        const percent = (progress.loaded / progress.total * 100).toFixed(0);
                        this.updateLoadingProgress(percent);
                    }}
                }},
                (error) => {{
                    console.error('Failed to load 3D model:', error);
                    this.showError();
                }}
            );
        }}

        showLoading() {{
            const loading = document.createElement('div');
            loading.className = 'skyyrose-3d-loading';
            loading.innerHTML = `
                <div class="skyyrose-3d-loading-content">
                    <div class="skyyrose-3d-spinner"></div>
                    <p>${{this.config.loadingText}}</p>
                    <div class="skyyrose-3d-progress">
                        <div class="skyyrose-3d-progress-bar" style="width: 0%"></div>
                    </div>
                </div>
            `;
            this.container.appendChild(loading);
        }}

        updateLoadingProgress(percent) {{
            const progressBar = this.container.querySelector('.skyyrose-3d-progress-bar');
            if (progressBar) {{
                progressBar.style.width = percent + '%';
            }}
        }}

        hideLoading() {{
            const loading = this.container.querySelector('.skyyrose-3d-loading');
            if (loading) {{
                loading.remove();
            }}
        }}

        showError() {{
            this.hideLoading();
            const error = document.createElement('div');
            error.className = 'skyyrose-3d-error';
            error.innerHTML = `
                <p>${{this.config.errorText}}</p>
            `;
            this.container.appendChild(error);
        }}

        onResize() {{
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;

            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        }}

        animate() {{
            requestAnimationFrame(() => this.animate());

            const delta = this.clock.getDelta();

            if (this.mixer) {{
                this.mixer.update(delta);
            }}

            if (this.controls) {{
                this.controls.update();
            }}

            this.renderer.render(this.scene, this.camera);
        }}

        dispose() {{
            if (this.controls) {{
                this.controls.dispose();
            }}
            if (this.renderer) {{
                this.renderer.dispose();
            }}
            if (this.model) {{
                this.scene.remove(this.model);
            }}
        }}
    }}

    // Initialize viewers on DOM ready
    function initViewers() {{
        document.querySelectorAll('.skyyrose-3d-viewer').forEach((container) => {{
            const modelUrl = container.dataset.modelUrl;
            const config = container.dataset.config
                ? JSON.parse(container.dataset.config)
                : {{}};

            if (modelUrl) {{
                new SkyyRose3DViewer(container, modelUrl, config);
            }}
        }});
    }}

    // Wait for Three.js to load
    function waitForThreeJS() {{
        return new Promise((resolve, reject) => {{
            let attempts = 0;
            const maxAttempts = 50;

            const check = () => {{
                if (typeof THREE !== 'undefined' &&
                    typeof THREE.GLTFLoader !== 'undefined') {{
                    resolve();
                }} else if (attempts >= maxAttempts) {{
                    reject(new Error('Three.js failed to load'));
                }} else {{
                    attempts++;
                    setTimeout(check, 100);
                }}
            }};

            check();
        }});
    }}

    // Export for external use
    window.SkyyRose3DViewer = SkyyRose3DViewer;

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', () => {{
            waitForThreeJS().then(initViewers).catch(console.error);
        }});
    }} else {{
        waitForThreeJS().then(initViewers).catch(console.error);
    }}
}})();
"""


def generate_viewer_css() -> str:
    """Generate CSS styles for the 3D viewer."""
    return """/**
 * SkyyRose 3D Product Viewer Styles
 * ==================================
 */

.skyyrose-3d-viewer {
    position: relative;
    width: 100%;
    height: 400px;
    background: #f5f5f5;
    border-radius: 8px;
    overflow: hidden;
}

.skyyrose-3d-viewer canvas {
    display: block;
}

.skyyrose-3d-loading {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.9);
    z-index: 10;
}

.skyyrose-3d-loading-content {
    text-align: center;
}

.skyyrose-3d-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e0e0e0;
    border-top-color: #B76E79;
    border-radius: 50%;
    animation: skyyrose-spin 1s linear infinite;
    margin: 0 auto 16px;
}

@keyframes skyyrose-spin {
    to {
        transform: rotate(360deg);
    }
}

.skyyrose-3d-loading p {
    margin: 0;
    color: #666;
    font-size: 14px;
}

.skyyrose-3d-progress {
    width: 200px;
    height: 4px;
    background: #e0e0e0;
    border-radius: 2px;
    margin: 12px auto 0;
    overflow: hidden;
}

.skyyrose-3d-progress-bar {
    height: 100%;
    background: #B76E79;
    border-radius: 2px;
    transition: width 0.3s ease;
}

.skyyrose-3d-error {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.9);
    z-index: 10;
}

.skyyrose-3d-error p {
    margin: 0;
    color: #c0392b;
    font-size: 14px;
}

/* AR Button */
.skyyrose-3d-ar-button {
    position: absolute;
    bottom: 16px;
    right: 16px;
    padding: 12px 24px;
    background: #B76E79;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: background 0.2s ease;
    z-index: 5;
}

.skyyrose-3d-ar-button:hover {
    background: #a05d68;
}

.skyyrose-3d-ar-button svg {
    width: 20px;
    height: 20px;
}

/* Controls */
.skyyrose-3d-controls {
    position: absolute;
    bottom: 16px;
    left: 16px;
    display: flex;
    gap: 8px;
    z-index: 5;
}

.skyyrose-3d-control-btn {
    width: 36px;
    height: 36px;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.2s ease;
}

.skyyrose-3d-control-btn:hover {
    background: #f5f5f5;
}

.skyyrose-3d-control-btn svg {
    width: 18px;
    height: 18px;
    color: #666;
}

/* Fullscreen mode */
.skyyrose-3d-viewer.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    border-radius: 0;
    z-index: 9999;
}
"""


def generate_shortcode_html(
    model_url: str,
    width: str = "100%",
    height: str = "400px",
    config: ViewerConfig | None = None,
) -> str:
    """Generate HTML for embedding the 3D viewer."""
    config = config or ViewerConfig()
    config_json = json.dumps(config.to_dict())

    return f"""<div
    class="skyyrose-3d-viewer"
    style="width: {width}; height: {height};"
    data-model-url="{model_url}"
    data-config='{config_json}'
></div>"""


# =============================================================================
# Plugin Generator
# =============================================================================


class WordPressPluginGenerator:
    """Generate WordPress plugin files for the 3D viewer."""

    def __init__(
        self,
        output_dir: Path,
        plugin_name: str = "skyyrose-3d-viewer",
        version: str = "1.0.0",
    ) -> None:
        """
        Initialize plugin generator.

        Args:
            output_dir: Directory to output plugin files
            plugin_name: Plugin directory/slug name
            version: Plugin version
        """
        self.output_dir = Path(output_dir)
        self.plugin_name = plugin_name
        self.version = version
        self.config = ViewerConfig()

    def generate(self) -> Path:
        """
        Generate all plugin files.

        Returns:
            Path to the generated plugin directory
        """
        plugin_dir = self.output_dir / self.plugin_name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Generate JavaScript
        js_path = plugin_dir / "assets" / "js"
        js_path.mkdir(parents=True, exist_ok=True)
        (js_path / "3d-viewer.js").write_text(generate_viewer_javascript(self.config))

        # Generate CSS
        css_path = plugin_dir / "assets" / "css"
        css_path.mkdir(parents=True, exist_ok=True)
        (css_path / "3d-viewer.css").write_text(generate_viewer_css())

        # Generate config.json
        config_path = plugin_dir / "config.json"
        config_path.write_text(json.dumps(self.config.to_dict(), indent=2))

        logger.info(
            "WordPress 3D viewer plugin generated",
            plugin_dir=str(plugin_dir),
            version=self.version,
        )

        return plugin_dir


# Aliases for backwards compatibility and test expectations
PluginGenerator = WordPressPluginGenerator
ThreeDViewerPlugin = WordPressPluginGenerator


__all__ = [
    "ViewerConfig",
    "WordPressPluginGenerator",
    "PluginGenerator",  # Alias
    "ThreeDViewerPlugin",  # Alias
    "generate_viewer_javascript",
    "generate_viewer_css",
    "generate_shortcode_html",
]
