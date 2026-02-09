/**
 * Scene Manager Utility
 * Handles initialization, lifecycle, and interaction management for Three.js scenes
 */

export class SceneManager {
    constructor() {
        this.activeScene = null;
        this.scenes = new Map();
        this.isInitialized = false;
    }

    /**
     * Register a scene
     */
    registerScene(name, SceneClass, container) {
        if (this.scenes.has(name)) {
            console.warn(`Scene "${name}" is already registered. Disposing previous instance.`);
            this.disposeScene(name);
        }

        this.scenes.set(name, { SceneClass, container, instance: null });
    }

    /**
     * Initialize a scene
     */
    initScene(name) {
        const sceneData = this.scenes.get(name);
        if (!sceneData) {
            console.error(`Scene "${name}" not found. Did you register it first?`);
            return null;
        }

        // Dispose active scene if different
        if (this.activeScene && this.activeScene !== name) {
            this.disposeScene(this.activeScene);
        }

        // Create new instance if not exists
        if (!sceneData.instance) {
            sceneData.instance = new sceneData.SceneClass(sceneData.container);
        }

        this.activeScene = name;
        this.isInitialized = true;

        return sceneData.instance;
    }

    /**
     * Get active scene instance
     */
    getActiveScene() {
        if (!this.activeScene) return null;
        return this.scenes.get(this.activeScene)?.instance;
    }

    /**
     * Dispose a scene
     */
    disposeScene(name) {
        const sceneData = this.scenes.get(name);
        if (!sceneData || !sceneData.instance) return;

        // Call dispose if available
        if (typeof sceneData.instance.dispose === 'function') {
            sceneData.instance.dispose();
        }

        // Clear instance
        sceneData.instance = null;

        if (this.activeScene === name) {
            this.activeScene = null;
            this.isInitialized = false;
        }
    }

    /**
     * Dispose all scenes
     */
    disposeAll() {
        this.scenes.forEach((_, name) => {
            this.disposeScene(name);
        });
        this.scenes.clear();
    }

    /**
     * Switch to a different scene
     */
    switchScene(name) {
        if (!this.scenes.has(name)) {
            console.error(`Cannot switch to scene "${name}": not registered`);
            return null;
        }

        return this.initScene(name);
    }
}

// Singleton instance
export const sceneManager = new SceneManager();

export default sceneManager;
