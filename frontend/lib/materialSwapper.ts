/**
 * Material Swapper
 * Utility for dynamically changing materials and textures on Three.js meshes
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import * as THREE from 'three';
import { Logger } from '../utils/Logger';

/**
 * Material Swapper for dynamic color and texture changes
 */
export class MaterialSwapper {
  private logger: Logger;
  private originalMaterials: WeakMap<THREE.Mesh, THREE.Material | THREE.Material[]> = new WeakMap();
  private textureLoader: THREE.TextureLoader;

  constructor() {
    this.logger = new Logger('MaterialSwapper');
    this.textureLoader = new THREE.TextureLoader();
  }

  /**
   * Save the original material of a mesh for later restoration
   *
   * @param mesh - The mesh to save material from
   */
  public saveOriginal(mesh: THREE.Mesh): void {
    if (this.originalMaterials.has(mesh)) {
      return; // Already saved
    }

    // Clone the material(s) to preserve original state
    if (Array.isArray(mesh.material)) {
      const clonedMaterials = mesh.material.map((mat) => mat.clone());
      this.originalMaterials.set(mesh, clonedMaterials);
    } else {
      const clonedMaterial = mesh.material.clone();
      this.originalMaterials.set(mesh, clonedMaterial);
    }

    this.logger.debug(`Saved original material for mesh`, { meshId: mesh.uuid });
  }

  /**
   * Reset mesh to its original material
   *
   * @param mesh - The mesh to reset
   */
  public resetToOriginal(mesh: THREE.Mesh): void {
    const originalMaterial = this.originalMaterials.get(mesh);

    if (!originalMaterial) {
      this.logger.warn('No original material found for mesh', { meshId: mesh.uuid });
      return;
    }

    // Dispose current material(s) if different from original
    if (Array.isArray(mesh.material)) {
      mesh.material.forEach((mat) => {
        if (!this.isSameMaterial(mat, originalMaterial)) {
          mat.dispose();
        }
      });
    } else if (mesh.material) {
      if (!this.isSameMaterial(mesh.material, originalMaterial)) {
        mesh.material.dispose();
      }
    }

    // Clone the original material to avoid modifying the saved copy
    if (Array.isArray(originalMaterial)) {
      mesh.material = originalMaterial.map((mat) => mat.clone());
    } else {
      mesh.material = originalMaterial.clone();
    }

    // Mark material(s) as needing update
    if (Array.isArray(mesh.material)) {
      mesh.material.forEach((mat) => { mat.needsUpdate = true; });
    } else {
      mesh.material.needsUpdate = true;
    }
    this.logger.debug('Reset mesh to original material', { meshId: mesh.uuid });
  }

  /**
   * Change the color of a mesh's material
   *
   * @param mesh - The mesh to modify
   * @param hex - Hex color string (e.g., '#B76E79')
   */
  public setColor(mesh: THREE.Mesh, hex: string): void {
    // Save original if not already saved
    if (!this.originalMaterials.has(mesh)) {
      this.saveOriginal(mesh);
    }

    const color = new THREE.Color(hex);

    if (Array.isArray(mesh.material)) {
      mesh.material.forEach((mat) => {
        if ('color' in mat && mat.color instanceof THREE.Color) {
          mat.color.copy(color);
          mat.needsUpdate = true;
        }
      });
    } else if ('color' in mesh.material && (mesh.material as THREE.MeshStandardMaterial).color instanceof THREE.Color) {
      (mesh.material as THREE.MeshStandardMaterial).color.copy(color);
      mesh.material.needsUpdate = true;
    }

    this.logger.debug('Set mesh color', { meshId: mesh.uuid, color: hex });
  }

  /**
   * Apply a texture to a mesh's material
   *
   * @param mesh - The mesh to modify
   * @param textureUrl - URL of the texture image
   * @returns Promise that resolves when texture is loaded
   */
  public async setTexture(mesh: THREE.Mesh, textureUrl: string): Promise<void> {
    // Save original if not already saved
    if (!this.originalMaterials.has(mesh)) {
      this.saveOriginal(mesh);
    }

    return new Promise((resolve, reject) => {
      this.textureLoader.load(
        textureUrl,
        (texture) => {
          // Configure texture
          texture.colorSpace = THREE.SRGBColorSpace;
          texture.wrapS = THREE.RepeatWrapping;
          texture.wrapT = THREE.RepeatWrapping;

          // Apply texture to material(s)
          if (Array.isArray(mesh.material)) {
            mesh.material.forEach((mat) => {
              const stdMat = mat as THREE.MeshStandardMaterial;
              if ('map' in stdMat) {
                // Dispose old texture if exists
                if (stdMat.map && typeof stdMat.map.dispose === 'function') {
                  stdMat.map.dispose();
                }
                stdMat.map = texture;
                stdMat.needsUpdate = true;
              }
            });
          } else {
            const stdMat = mesh.material as THREE.MeshStandardMaterial;
            if ('map' in stdMat) {
              // Dispose old texture if exists
              if (stdMat.map && typeof stdMat.map.dispose === 'function') {
                stdMat.map.dispose();
              }
              stdMat.map = texture;
              stdMat.needsUpdate = true;
            }
          }

          this.logger.debug('Set mesh texture', { meshId: mesh.uuid, textureUrl });
          resolve();
        },
        undefined,
        (error) => {
          this.logger.error('Failed to load texture', error, { textureUrl });
          reject(error);
        }
      );
    });
  }

  /**
   * Change material properties (roughness, metalness, etc.)
   *
   * @param mesh - The mesh to modify
   * @param properties - Object containing material properties to update
   */
  public setMaterialProperties(
    mesh: THREE.Mesh,
    properties: {
      roughness?: number;
      metalness?: number;
      opacity?: number;
      transparent?: boolean;
      emissive?: string;
      emissiveIntensity?: number;
    }
  ): void {
    // Save original if not already saved
    if (!this.originalMaterials.has(mesh)) {
      this.saveOriginal(mesh);
    }

    const applyProperties = (material: THREE.Material): void => {
      if (properties.roughness !== undefined && 'roughness' in material) {
        (material as THREE.MeshStandardMaterial).roughness = properties.roughness;
      }
      if (properties.metalness !== undefined && 'metalness' in material) {
        (material as THREE.MeshStandardMaterial).metalness = properties.metalness;
      }
      if (properties.opacity !== undefined) {
        material.opacity = properties.opacity;
      }
      if (properties.transparent !== undefined) {
        material.transparent = properties.transparent;
      }
      if (properties.emissive !== undefined && 'emissive' in material) {
        (material as THREE.MeshStandardMaterial).emissive.set(properties.emissive);
      }
      if (properties.emissiveIntensity !== undefined && 'emissiveIntensity' in material) {
        (material as THREE.MeshStandardMaterial).emissiveIntensity = properties.emissiveIntensity;
      }
      material.needsUpdate = true;
    };

    if (Array.isArray(mesh.material)) {
      mesh.material.forEach(applyProperties);
    } else {
      applyProperties(mesh.material);
    }

    this.logger.debug('Set material properties', { meshId: mesh.uuid, properties });
  }

  /**
   * Check if two materials are the same instance
   */
  private isSameMaterial(
    mat1: THREE.Material,
    mat2: THREE.Material | THREE.Material[]
  ): boolean {
    if (Array.isArray(mat2)) {
      return mat2.includes(mat1);
    }
    return mat1 === mat2;
  }

  /**
   * Dispose of all stored original materials
   */
  public dispose(): void {
    // WeakMap automatically handles garbage collection
    this.logger.info('Material swapper disposed');
  }
}

// Export singleton instance for convenience
export const materialSwapper = new MaterialSwapper();
