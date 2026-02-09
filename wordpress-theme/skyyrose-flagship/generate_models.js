#!/usr/bin/env node
/**
 * Generate placeholder 3D models for SkyyRose theme
 * Creates simple geometric .glb files for product visualization
 */

import * as THREE from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import fs from 'fs';
import path from 'path';

const exporter = new GLTFExporter();
const modelsDir = './assets/models';

// Ensure models directory exists
if (!fs.existsSync(modelsDir)) {
  fs.mkdirSync(modelsDir, { recursive: true });
}

/**
 * Create a rose-like signature piece (torus + sphere)
 */
function createSignatureModel() {
  const group = new THREE.Group();

  // Rose petals (torus)
  const torusGeometry = new THREE.TorusGeometry(1, 0.4, 16, 32);
  const torusMaterial = new THREE.MeshStandardMaterial({
    color: 0xff1493, // Deep pink
    metalness: 0.3,
    roughness: 0.4
  });
  const torus = new THREE.Mesh(torusGeometry, torusMaterial);
  group.add(torus);

  // Center sphere (rose center)
  const sphereGeometry = new THREE.SphereGeometry(0.5, 32, 32);
  const sphereMaterial = new THREE.MeshStandardMaterial({
    color: 0xffc0cb, // Light pink
    metalness: 0.2,
    roughness: 0.5
  });
  const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
  group.add(sphere);

  // Add point light
  const light = new THREE.PointLight(0xffffff, 1, 100);
  light.position.set(5, 5, 5);
  group.add(light);

  return group;
}

/**
 * Create a heart shape for Love Hurts collection
 */
function createLoveHurtsModel() {
  const group = new THREE.Group();

  // Create heart using two spheres and a rotated box
  const heartMaterial = new THREE.MeshStandardMaterial({
    color: 0x8b0000, // Dark red
    metalness: 0.7,
    roughness: 0.2
  });

  // Left sphere
  const leftSphere = new THREE.Mesh(
    new THREE.SphereGeometry(0.5, 32, 32),
    heartMaterial
  );
  leftSphere.position.set(-0.5, 0.5, 0);
  group.add(leftSphere);

  // Right sphere
  const rightSphere = new THREE.Mesh(
    new THREE.SphereGeometry(0.5, 32, 32),
    heartMaterial
  );
  rightSphere.position.set(0.5, 0.5, 0);
  group.add(rightSphere);

  // Bottom diamond (rotated cube)
  const diamond = new THREE.Mesh(
    new THREE.BoxGeometry(1.4, 1.4, 0.5),
    heartMaterial
  );
  diamond.rotation.z = Math.PI / 4;
  diamond.position.set(0, -0.3, 0);
  group.add(diamond);

  // Add ambient light
  const light = new THREE.AmbientLight(0xffffff, 0.5);
  group.add(light);

  return group;
}

/**
 * Create a black rose (similar to signature but darker)
 */
function createBlackRoseModel() {
  const group = new THREE.Group();

  // Dark petals (multiple toruses)
  const blackMaterial = new THREE.MeshStandardMaterial({
    color: 0x1a1a1a, // Almost black
    metalness: 0.8,
    roughness: 0.1
  });

  for (let i = 0; i < 3; i++) {
    const torus = new THREE.Mesh(
      new THREE.TorusGeometry(1 - i * 0.2, 0.3, 16, 32),
      blackMaterial
    );
    torus.rotation.x = Math.PI / 2 * i / 3;
    group.add(torus);
  }

  // Center spike (cone)
  const cone = new THREE.Mesh(
    new THREE.ConeGeometry(0.3, 1, 8),
    blackMaterial
  );
  cone.rotation.x = Math.PI;
  group.add(cone);

  // Add directional light
  const light = new THREE.DirectionalLight(0xffffff, 1);
  light.position.set(0, 10, 5);
  group.add(light);

  return group;
}

/**
 * Create a gift box for pre-order items
 */
function createPreorderModel() {
  const group = new THREE.Group();

  // Box
  const boxGeometry = new THREE.BoxGeometry(1.5, 1.5, 1.5);
  const boxMaterial = new THREE.MeshStandardMaterial({
    color: 0x4169e1, // Royal blue
    metalness: 0.1,
    roughness: 0.6
  });
  const box = new THREE.Mesh(boxGeometry, boxMaterial);
  group.add(box);

  // Ribbon (flat box on top)
  const ribbonMaterial = new THREE.MeshStandardMaterial({
    color: 0xffd700, // Gold
    metalness: 0.9,
    roughness: 0.1
  });
  const ribbon1 = new THREE.Mesh(
    new THREE.BoxGeometry(1.6, 0.2, 0.3),
    ribbonMaterial
  );
  ribbon1.position.y = 0.85;
  group.add(ribbon1);

  const ribbon2 = new THREE.Mesh(
    new THREE.BoxGeometry(0.3, 0.2, 1.6),
    ribbonMaterial
  );
  ribbon2.position.y = 0.85;
  group.add(ribbon2);

  // Bow (sphere on top)
  const bow = new THREE.Mesh(
    new THREE.SphereGeometry(0.3, 16, 16),
    ribbonMaterial
  );
  bow.position.y = 1.1;
  group.add(bow);

  return group;
}

/**
 * Export model to GLB file
 */
function exportModel(scene, filename) {
  return new Promise((resolve, reject) => {
    exporter.parse(
      scene,
      (gltf) => {
        const outputPath = path.join(modelsDir, filename);
        fs.writeFileSync(outputPath, Buffer.from(gltf));
        const stats = fs.statSync(outputPath);
        console.log(`✓ Created ${filename} (${(stats.size / 1024).toFixed(1)}KB)`);
        resolve();
      },
      (error) => {
        console.error(`✗ Failed to create ${filename}:`, error);
        reject(error);
      },
      { binary: true }
    );
  });
}

/**
 * Main generation function
 */
async function generateModels() {
  console.log('Generating placeholder 3D models...\n');

  try {
    // Create scenes for each model
    const models = [
      { scene: createSignatureModel(), filename: 'placeholder-signature.glb' },
      { scene: createLoveHurtsModel(), filename: 'placeholder-lovehurts.glb' },
      { scene: createBlackRoseModel(), filename: 'placeholder-blackrose.glb' },
      { scene: createPreorderModel(), filename: 'placeholder-preorder.glb' }
    ];

    // Export all models
    for (const model of models) {
      await exportModel(model.scene, model.filename);
    }

    // Summary
    const files = fs.readdirSync(modelsDir);
    const totalSize = files.reduce((sum, file) => {
      const stats = fs.statSync(path.join(modelsDir, file));
      return sum + stats.size;
    }, 0);

    console.log(`\n✓ Generated ${files.length} models`);
    console.log(`  Total size: ${(totalSize / 1024).toFixed(1)}KB`);
    console.log(`  Location: ${modelsDir}`);

  } catch (error) {
    console.error('Error generating models:', error);
    process.exit(1);
  }
}

// Run generation
generateModels();
