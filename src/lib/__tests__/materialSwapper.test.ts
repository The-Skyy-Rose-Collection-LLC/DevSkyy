/**
 * Unit Tests for MaterialSwapper
 */

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
  return {
    uuid: 'mat-' + Math.random().toString(36).slice(2, 8),
    clone: jest.fn().mockImplementation(function (this: any) {
      return { ...this, clone: jest.fn(), dispose: jest.fn(), needsUpdate: false };
    }),
    dispose: jest.fn(),
    needsUpdate: false,
    color: { copy: jest.fn(), set: jest.fn() },
    roughness: 0.5,
    metalness: 0.5,
    opacity: 1,
    transparent: false,
    emissive: { set: jest.fn() },
    emissiveIntensity: 0,
    map: null,
    ...overrides,
  };
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

  describe('dispose', () => {
    it('should not throw', () => {
      expect(() => swapper.dispose()).not.toThrow();
    });
  });
});
