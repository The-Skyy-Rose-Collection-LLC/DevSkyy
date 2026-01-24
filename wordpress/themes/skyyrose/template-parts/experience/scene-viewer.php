<?php
/**
 * Template Part: Scene Viewer with Enhanced Hotspots
 *
 * Immersive 3D scene viewer with interactive hotspots, open source
 * environment assets, and atmospheric effects.
 *
 * @package SkyyRose
 * @version 2.0.0
 *
 * Expected variables:
 * @var string $collection_slug - Collection identifier (black-rose, love-hurts, signature)
 * @var array  $collection      - Collection data from skyyrose_get_collection()
 * @var string $scene_model     - GLB model URL for the scene (optional)
 * @var array  $hotspots        - Hotspot configuration array
 */

defined('ABSPATH') || exit;

// Defaults
$collection_slug = $collection_slug ?? 'signature';
$collection = $collection ?? skyyrose_get_collection($collection_slug);
$scene_model = $scene_model ?? '';
$hotspots = $hotspots ?? [];

// Load hotspots from JSON if available
$hotspots_json_path = SKYYROSE_DIR . '/hotspots/' . $collection_slug . '_hotspots.json';
if (empty($hotspots) && file_exists($hotspots_json_path)) {
    $hotspots_data = json_decode(file_get_contents($hotspots_json_path), true);
    $hotspots = $hotspots_data['hotspots'] ?? [];
}

// Fallback to WordPress hotspots directory
if (empty($hotspots)) {
    $wp_hotspots_path = WP_CONTENT_DIR . '/themes/skyyrose/../../hotspots/' . str_replace('-', '_', $collection_slug) . '_hotspots.json';
    if (file_exists($wp_hotspots_path)) {
        $hotspots_data = json_decode(file_get_contents($wp_hotspots_path), true);
        $hotspots = $hotspots_data['hotspots'] ?? [];
    }
}

// Environment settings per collection
$environment_settings = [
    'black-rose' => [
        'hdri' => 'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_09_1k.hdr',
        'exposure' => '0.8',
        'shadow' => '1.2',
        'ambient_color' => '#0A0A0A',
    ],
    'love-hurts' => [
        'hdri' => 'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/lebombo_1k.hdr',
        'exposure' => '1.0',
        'shadow' => '1.0',
        'ambient_color' => '#1a0a10',
    ],
    'signature' => [
        'hdri' => 'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/golden_bay_1k.hdr',
        'exposure' => '1.2',
        'shadow' => '0.8',
        'ambient_color' => '#0A0805',
    ],
];

$env = $environment_settings[$collection_slug] ?? $environment_settings['signature'];
?>

<section class="experience-scene" id="scene-<?php echo esc_attr($collection_slug); ?>">
    <!-- Scene Particles (atmospheric effect) -->
    <div class="scene-particles" aria-hidden="true"></div>

    <!-- 3D Scene Viewer -->
    <div class="scene-viewer">
        <?php if ($scene_model) : ?>
            <model-viewer
                src="<?php echo esc_url($scene_model); ?>"
                ios-src="<?php echo esc_url(str_replace('.glb', '.usdz', $scene_model)); ?>"
                ar
                ar-modes="webxr scene-viewer quick-look"
                ar-scale="auto"
                ar-placement="floor"
                camera-controls
                auto-rotate
                rotation-per-second="5deg"
                environment-image="<?php echo esc_url($env['hdri']); ?>"
                exposure="<?php echo esc_attr($env['exposure']); ?>"
                shadow-intensity="<?php echo esc_attr($env['shadow']); ?>"
                shadow-softness="0.5"
                interaction-prompt="auto"
                class="scene-viewer__model"
                style="--poster-color: <?php echo esc_attr($env['ambient_color']); ?>;">

                <!-- AR Button -->
                <button slot="ar-button" class="ar-button ar-button--scene">
                    <span class="ar-button__icon" aria-hidden="true">&#x1F4F1;</span>
                    <span>Enter AR Experience</span>
                </button>

                <!-- Loading State -->
                <div class="model-viewer__loading" slot="poster">
                    <div class="loading-spinner loading-spinner--<?php echo esc_attr($collection_slug); ?>"></div>
                    <p>Loading <?php echo esc_html($collection['name']); ?> Experience...</p>
                </div>

                <!-- Hotspot Slots (for model-viewer integration) -->
                <?php foreach ($hotspots as $index => $hotspot) :
                    if (!isset($hotspot['position'])) continue;
                    $pos = $hotspot['position'];
                    $normal = $hotspot['normal'] ?? ['x' => 0, 'y' => 1, 'z' => 0];
                ?>
                    <div
                        class="hotspot-anchor"
                        slot="hotspot-<?php echo esc_attr($index); ?>"
                        data-position="<?php echo esc_attr($pos['x'] . ' ' . $pos['y'] . ' ' . $pos['z']); ?>"
                        data-normal="<?php echo esc_attr($normal['x'] . ' ' . $normal['y'] . ' ' . $normal['z']); ?>"
                        data-visibility-attribute="visible">
                    </div>
                <?php endforeach; ?>
            </model-viewer>
        <?php else : ?>
            <!-- Fallback: 2D Environment Preview -->
            <div class="scene-viewer__fallback" style="background-color: <?php echo esc_attr($env['ambient_color']); ?>;">
                <div class="scene-viewer__fallback-content">
                    <div class="badge-3d-coming badge-3d-coming--<?php echo esc_attr($collection_slug); ?>">
                        <span class="badge-icon">&#x1F3AD;</span>
                        <span>3D Scene</span>
                        <span>Coming Soon</span>
                    </div>
                    <p class="scene-viewer__fallback-text">
                        The immersive <?php echo esc_html($collection['name']); ?> 3D environment is being crafted.
                    </p>
                </div>
            </div>
        <?php endif; ?>

        <!-- Hotspots Container (rendered by JS) -->
        <div class="hotspots-container" aria-label="Interactive product hotspots"></div>
    </div>

    <!-- Scene Info Bar -->
    <div class="scene-info-bar">
        <div class="scene-info-bar__env">
            <span class="scene-info-bar__env-icon"></span>
            <span><?php echo esc_html($collection['name']); ?> Collection</span>
        </div>
        <div class="scene-info-bar__attribution">
            Environment by <a href="https://polyhaven.com" target="_blank" rel="noopener">Poly Haven</a> (CC0)
        </div>
    </div>

    <!-- Audio Toggle (optional ambient sound) -->
    <button class="audio-toggle is-muted" aria-label="Toggle ambient audio" data-collection="<?php echo esc_attr($collection_slug); ?>">
        <span class="audio-toggle__icon">&#x1F50A;</span>
        <span class="audio-toggle__label">Sound</span>
    </button>

    <!-- Easter Egg Progress (shown after first discovery) -->
    <div class="easter-egg-progress" aria-live="polite">
        <span class="easter-egg-progress__icon">&#x1F5DD;</span>
        <span class="easter-egg-progress__text">
            Secrets: <span class="easter-egg-progress__count">0/0</span>
        </span>
    </div>
</section>

<!-- Initialize Scene -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Wait for enhanced hotspots script to load
    if (typeof window.SkyyRoseHotspots !== 'undefined') {
        window.SkyyRoseHotspots.init('<?php echo esc_js($collection_slug); ?>', {
            hotspots: <?php echo wp_json_encode($hotspots); ?>
        });
        window.SkyyRoseSceneEnvironment.init('<?php echo esc_js($collection_slug); ?>');
    }

    // Audio toggle handler
    const audioToggle = document.querySelector('.audio-toggle');
    if (audioToggle) {
        let audioEnabled = false;
        audioToggle.addEventListener('click', function() {
            audioEnabled = !audioEnabled;
            this.classList.toggle('is-muted', !audioEnabled);

            if (typeof window.SkyyRoseHotspots !== 'undefined') {
                const sounds = window.SKYYROSE_SCENE_ASSETS?.ambience?.['<?php echo esc_js($collection_slug); ?>']?.sounds || [];
                sounds.forEach(function(sound) {
                    window.SkyyRoseHotspots.toggleAmbientSound(sound.name, audioEnabled);
                });
            }
        });
    }

    // Update easter egg progress display
    document.addEventListener('skyyrose:easter-egg-discovered', function() {
        const progressEl = document.querySelector('.easter-egg-progress');
        const countEl = progressEl?.querySelector('.easter-egg-progress__count');

        if (progressEl && countEl && typeof window.SkyyRoseHotspots !== 'undefined') {
            const progress = window.SkyyRoseHotspots.getProgress();
            if (progress.total > 0) {
                progressEl.classList.add('is-visible');
                countEl.textContent = progress.discovered + '/' + progress.total;
            }
        }
    });
});
</script>
