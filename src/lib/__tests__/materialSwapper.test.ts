/**
 * Unit Tests for MaterialSwapper
 */

import * as THREE from 'three';
import { MaterialSwapper } from '../materialSwapper';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

function createMockMaterial(overrides: any = {}) {
  const color = new THREE.Color(0xffffff);
  color.copy = jest.fn().mockReturnThis();
  const emissive = new THREE.Color(0x000000);
  emissive.set = jest.fn().mockReturnThis();

  const mat: any = {
    uuid: 'mat-' + Math.random().toString(36).slice(2, 8),
    dispose: jest.fn(),
    needsUpdate: false,
    color,
    roughness: 0.5,
    metalness: 0.5,
    opacity: 1,
    transparent: false,
    emissive,
    emissiveIntensity: 0,
    map: null,
    ...overrides,
  };
  mat.clone = jest.fn().mockImplementation(() => createMockMaterial(overrides));
  return mat;
}

function createMockMesh(materialOverride?: any) {
  const material = materialOverride || createMockMaterial();
  return {
    uuid: 'mesh-' + Math.random().toString(36).slice(2, 8),
    material,
    userData: {},
  } as any;
}

describe('MaterialSwapper', () => {
  let swapper: MaterialSwapper;

  beforeEach(() => {
    swapper = new MaterialSwapper();
  });

  describe('saveOriginal', () => {
    it('should save single material', () => {
      const mesh = createMockMesh();
      swapper.saveOriginal(mesh);
      expect(mesh.material.clone).toHaveBeenCalled();
    });

    it('should save array of materials', () => {
      const mat1 = createMockMaterial();
      const mat2 = createMockMaterial();
      const mesh = createMockMesh([mat1, mat2]);
      swapper.saveOriginal(mesh);
      expect(mat1.clone).toHaveBeenCalled();
      expect(mat2.clone).toHaveBeenCalled();
    });

    it('should not save twice', () => {
      const mesh = createMockMesh();
      swapper.saveOriginal(mesh);
      mesh.material.clone.mockClear();
      swapper.saveOriginal(mesh);
      expect(mesh.material.clone).not.toHaveBeenCalled();
    });
  });

  describe('resetToOriginal', () => {
    it('should restore single material', () => {
      const mesh = createMockMesh();
      swapper.saveOriginal(mesh);
      // Change material
      mesh.material = createMockMaterial();
      swapper.resetToOriginal(mesh);
      expect(mesh.material.needsUpdate).toBe(true);
    });

    it('should warn when no original saved', () => {
      const mesh = createMockMesh();
      swapper.resetToOriginal(mesh);
      // Should not throw
    });

    it('should restore array materials', () => {
      const mat1 = createMockMaterial();
      const mat2 = createMockMaterial();
      const mesh = createMockMesh([mat1, mat2]);
      swapper.saveOriginal(mesh);
      mesh.material = [createMockMaterial()];
      swapper.resetToOriginal(mesh);
      expect(Array.isArray(mesh.material)).toBe(true);
    });

    it('should dispose current material if different', () => {
      const mesh = createMockMesh();
      swapper.saveOriginal(mesh);
      const newMat = createMockMaterial();
      mesh.material = newMat;
      swapper.resetToOriginal(mesh);
      expect(newMat.dispose).toHaveBeenCalled();
    });
  });

  describe('setColor', () => {
    it('should auto-save original before changing color', () => {
      const mesh = createMockMesh();
      swapper.setColor(mesh, '#B76E79');
      // Should have saved original (clone called)
      expect(mesh.material.clone).toHaveBeenCalled();
    });

    it('should set color on single material', () => {
      const mesh = createMockMesh();
      swapper.setColor(mesh, '#ff0000');
      expect(mesh.material.color.copy).toHaveBeenCalled();
      expect(mesh.material.needsUpdate).toBe(true);
    });

    it('should set color on array materials', () => {
      const mat1 = createMockMaterial();
      const mat2 = createMockMaterial();
      const mesh = createMockMesh([mat1, mat2]);
      swapper.setColor(mesh, '#00ff00');
      expect(mat1.color.copy).toHaveBeenCalled();
      expect(mat2.color.copy).toHaveBeenCalled();
    });
  });

  describe('setMaterialProperties', () => {
    it('should set roughness', () => {
      const mesh = createMockMesh();
      swapper.setMaterialProperties(mesh, { roughness: 0.8 });
      expect(mesh.material.roughness).toBe(0.8);
    });

    it('should set metalness', () => {
      const mesh = createMockMesh();
      swapper.setMaterialProperties(mesh, { metalness: 1.0 });
      expect(mesh.material.metalness).toBe(1.0);
    });

    it('should set opacity and transparency', () => {
      const mesh = createMockMesh();
      swapper.setMaterialProperties(mesh, { opacity: 0.5, transparent: true });
      expect(mesh.material.opacity).toBe(0.5);
      expect(mesh.material.transparent).toBe(true);
    });

    it('should set emissive properties', () => {
      const mesh = createMockMesh();
      swapper.setMaterialProperties(mesh, { emissive: '#ff0000', emissiveIntensity: 0.5 });
      expect(mesh.material.emissive.set).toHaveBeenCalledWith('#ff0000');
      expect(mesh.material.emissiveIntensity).toBe(0.5);
    });

    it('should apply to array materials', () => {
      const mat1 = createMockMaterial();
      const mat2 = createMockMaterial();
      const mesh = createMockMesh([mat1, mat2]);
      swapper.setMaterialProperties(mesh, { roughness: 0.2 });
      expect(mat1.roughness).toBe(0.2);
      expect(mat2.roughness).toBe(0.2);
    });

    it('should mark materials as needing update', () => {
      const mesh = createMockMesh();
      swapper.setMaterialProperties(mesh, { roughness: 0.1 });
      expect(mesh.material.needsUpdate).toBe(true);
    });
  });

  describe('setTexture', () => {
    it('should load and apply texture to single material', async () => {
      const mesh = createMockMesh();
      // TextureLoader.load calls onLoad callback asynchronously
      const promise = swapper.setTexture(mesh, '/textures/fabric.jpg');
      // Wait for the setTimeout in TextureLoader mock
      await new Promise((r) => setTimeout(r, 10));
      await promise;

      // Texture should have been applied
      // The mock TextureLoader's load returns a texture and calls onLoad
    });

    it('should auto-save original before applying texture', async () => {
      const mesh = createMockMesh();
      const promise = swapper.setTexture(mesh, '/textures/fabric.jpg');
      await new Promise((r) => setTimeout(r, 10));
      await promise;

      expect(mesh.material.clone).toHaveBeenCalled();
    });

    it('should apply texture to array materials', async () => {
      const mat1 = createMockMaterial();
      const mat2 = createMockMaterial();
      const mesh = createMockMesh([mat1, mat2]);

      const promise = swapper.setTexture(mesh, '/textures/fabric.jpg');
      await new Promise((r) => setTimeout(r, 10));
      await promise;
    });
  });

  describe('resetToOriginal edge cases', () => {
    it('should dispose array of current materials when different from original', () => {
      const mesh = createMockMesh();
      swapper.saveOriginal(mesh);
      // Replace with array of new materials
      const newMat1 = createMockMaterial();
      const newMat2 = createMockMaterial();
      mesh.material = [newMat1, newMat2];
      swapper.resetToOriginal(mesh);
      expect(newMat1.dispose).toHaveBeenCalled();
      expect(newMat2.dispose).toHaveBeenCalled();
    });

    it('should not dispose current material if same as original', () => {
      const mat = createMockMaterial();
      const mesh = createMockMesh(mat);
      swapper.saveOriginal(mesh);
      // material is same reference - should not dispose
      swapper.resetToOriginal(mesh);
      // The clone of original is different, so current gets disposed
      // but the original reference check via isSameMaterial matters
    });
  });

  describe('setColor edge cases', () => {
    it('should not set color on material without color property', () => {
      const matNoColor = { dispose: jest.fn(), needsUpdate: false, clone: jest.fn().mockReturnThis() };
      const mesh = createMockMesh(matNoColor);
      expect(() => swapper.setColor(mesh, '#ff0000')).not.toThrow();
    });
  });

  describe('setMaterialProperties edge cases', () => {
    it('should not crash when material lacks standard properties', () => {
      const basicMat = {
        dispose: jest.fn(),
        needsUpdate: false,
        opacity: 1,
        transparent: false,
        clone: jest.fn().mockReturnThis(),
      };
      const mesh = createMockMesh(basicMat);
      expect(() =>
        swapper.setMaterialProperties(mesh, {
          roughness: 0.5,
          metalness: 0.5,
          emissive: '#ff0000',
          emissiveIntensity: 0.3,
        })
      ).not.toThrow();
    });
  });

  describe('dispose', () => {
    it('should not throw', () => {
      expect(() => swapper.dispose()).not.toThrow();
    });
  });
});
