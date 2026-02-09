#!/usr/bin/env python3
"""
Generate on-brand placeholder 3D models for SkyyRose theme
Creates GLB files with SkyyRose aesthetic: roses, luxury, dark elegance
"""

import struct
import base64
import json
import os
import numpy as np
from pygltflib import GLTF2, Scene, Node, Mesh, Primitive, Buffer, BufferView, Accessor
from pygltflib import Material, PbrMetallicRoughness, ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER
from pygltflib.utils import gltf2glb

def create_rose_geometry(scale=1.0, color=(1.0, 0.078, 0.576)):  # SkyyRose pink
    """Create a stylized rose using spheres arranged in petal pattern"""
    vertices = []
    indices = []
    colors = []
    normals = []

    # Center of rose
    center_segments = 8
    for i in range(center_segments):
        angle = (i / center_segments) * 2 * np.pi
        x = np.cos(angle) * 0.3 * scale
        y = np.sin(angle) * 0.3 * scale
        z = 0.2 * scale
        vertices.extend([x, y, z])
        colors.extend(color)
        normals.extend([0, 0, 1])

    # Outer petals (layered)
    for layer in range(3):
        petal_count = 5 + layer * 2
        radius = (0.6 + layer * 0.3) * scale
        height = (0.4 - layer * 0.1) * scale

        for i in range(petal_count):
            angle = (i / petal_count) * 2 * np.pi
            x = np.cos(angle) * radius
            y = np.sin(angle) * radius
            z = height
            vertices.extend([x, y, z])

            # Gradient color (darker on outer petals)
            r, g, b = color
            darkness = 0.7 + (layer * 0.1)
            colors.extend([r * darkness, g * darkness, b * darkness])

            nx = np.cos(angle)
            ny = np.sin(angle)
            normals.extend([nx, ny, 0.2])

    # Create triangles (simplified)
    vertex_count = len(vertices) // 3
    for i in range(vertex_count - 2):
        indices.extend([0, i + 1, i + 2])

    return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint16), \
           np.array(colors, dtype=np.float32), np.array(normals, dtype=np.float32)

def create_heart_geometry(scale=1.0, color=(0.545, 0.0, 0.0)):  # Dark red for Love Hurts
    """Create a heart shape with thorns for Love Hurts collection"""
    vertices = []
    indices = []
    colors = []
    normals = []

    # Heart curve (parametric)
    segments = 32
    for i in range(segments):
        t = (i / segments) * 2 * np.pi
        # Heart curve equations
        x = (16 * np.sin(t)**3) * 0.05 * scale
        y = (13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t)) * 0.05 * scale
        z = 0
        vertices.extend([x, y, z])
        colors.extend(color)
        normals.extend([0, 0, 1])

    # Add thorns (spikes at key points)
    thorn_positions = [np.pi/4, np.pi*3/4, np.pi*5/4, np.pi*7/4]
    for pos in thorn_positions:
        base_x = np.cos(pos) * 0.6 * scale
        base_y = np.sin(pos) * 0.6 * scale
        tip_x = np.cos(pos) * 0.9 * scale
        tip_y = np.sin(pos) * 0.9 * scale

        vertices.extend([base_x, base_y, 0])
        vertices.extend([tip_x, tip_y, 0.3 * scale])

        # Darker color for thorns
        colors.extend([0.2, 0.0, 0.0])
        colors.extend([0.1, 0.0, 0.0])

        normals.extend([tip_x - base_x, tip_y - base_y, 0.3])
        normals.extend([tip_x - base_x, tip_y - base_y, 0.3])

    # Simple triangulation
    vertex_count = len(vertices) // 3
    for i in range(segments - 1):
        indices.extend([0, i, i + 1])

    return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint16), \
           np.array(colors, dtype=np.float32), np.array(normals, dtype=np.float32)

def create_black_rose_geometry(scale=1.0, color=(0.1, 0.1, 0.1)):  # Almost black
    """Create a gothic black rose with metallic sheen"""
    # Similar to rose but with layered petals and darker aesthetic
    vertices, indices, colors, normals = create_rose_geometry(scale, color)

    # Add gothic elements - crystalline structure
    crystal_points = 6
    for i in range(crystal_points):
        angle = (i / crystal_points) * 2 * np.pi
        x = np.cos(angle) * 1.2 * scale
        y = np.sin(angle) * 1.2 * scale
        z = -0.3 * scale  # Below the rose

        vertices = np.append(vertices, [x, y, z])
        colors = np.append(colors, [0.05, 0.05, 0.05])  # Very dark
        normals = np.append(normals, [np.cos(angle), np.sin(angle), -0.5])

    return vertices, indices, colors, normals

def create_luxury_box_geometry(scale=1.0, color=(0.831, 0.686, 0.216)):  # Gold for luxury
    """Create a luxury gift box for pre-order items"""
    vertices = []
    indices = []
    colors = []
    normals = []

    # Box vertices (cube)
    box_size = scale
    box_vertices = [
        # Front face
        [-box_size, -box_size, box_size],
        [box_size, -box_size, box_size],
        [box_size, box_size, box_size],
        [-box_size, box_size, box_size],
        # Back face
        [-box_size, -box_size, -box_size],
        [box_size, -box_size, -box_size],
        [box_size, box_size, -box_size],
        [-box_size, box_size, -box_size],
    ]

    for v in box_vertices:
        vertices.extend(v)
        colors.extend(color)  # Gold color
        normals.extend([0, 0, 1])

    # Box faces (triangles)
    faces = [
        [0, 1, 2], [0, 2, 3],  # Front
        [4, 6, 5], [4, 7, 6],  # Back
        [0, 4, 5], [0, 5, 1],  # Bottom
        [2, 6, 7], [2, 7, 3],  # Top
        [0, 3, 7], [0, 7, 4],  # Left
        [1, 5, 6], [1, 6, 2],  # Right
    ]

    for face in faces:
        indices.extend(face)

    # Add ribbon (cross on top)
    ribbon_color = (1.0, 0.078, 0.576)  # SkyyRose pink ribbon
    ribbon_width = 0.15 * scale
    ribbon_height = box_size + 0.1 * scale

    ribbon_vertices = [
        # Vertical ribbon
        [-ribbon_width, -box_size, ribbon_height],
        [ribbon_width, -box_size, ribbon_height],
        [ribbon_width, box_size, ribbon_height],
        [-ribbon_width, box_size, ribbon_height],
    ]

    for v in ribbon_vertices:
        vertices.extend(v)
        colors.extend(ribbon_color)
        normals.extend([0, 0, 1])

    return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint16), \
           np.array(colors, dtype=np.float32), np.array(normals, dtype=np.float32)

def create_glb(vertices, indices, colors, normals, filename, material_name="Material"):
    """Create a GLB file from geometry data"""

    # Prepare binary data
    vertices_binary = vertices.tobytes()
    indices_binary = indices.tobytes()
    colors_binary = colors.tobytes()
    normals_binary = normals.tobytes()

    # Combine all binary data
    buffer_data = vertices_binary + indices_binary + colors_binary + normals_binary

    # Calculate offsets
    vertices_offset = 0
    indices_offset = len(vertices_binary)
    colors_offset = indices_offset + len(indices_binary)
    normals_offset = colors_offset + len(colors_binary)

    # Create GLTF structure
    gltf = GLTF2()

    # Buffer
    gltf.buffers = [Buffer(byteLength=len(buffer_data))]

    # Buffer Views
    gltf.bufferViews = [
        BufferView(buffer=0, byteOffset=vertices_offset, byteLength=len(vertices_binary), target=ARRAY_BUFFER),
        BufferView(buffer=0, byteOffset=indices_offset, byteLength=len(indices_binary), target=ELEMENT_ARRAY_BUFFER),
        BufferView(buffer=0, byteOffset=colors_offset, byteLength=len(colors_binary), target=ARRAY_BUFFER),
        BufferView(buffer=0, byteOffset=normals_offset, byteLength=len(normals_binary), target=ARRAY_BUFFER),
    ]

    # Accessors
    gltf.accessors = [
        Accessor(bufferView=0, componentType=5126, count=len(vertices)//3, type="VEC3",
                min=vertices.reshape(-1, 3).min(axis=0).tolist(),
                max=vertices.reshape(-1, 3).max(axis=0).tolist()),
        Accessor(bufferView=1, componentType=5123, count=len(indices), type="SCALAR"),
        Accessor(bufferView=2, componentType=5126, count=len(colors)//3, type="VEC3"),
        Accessor(bufferView=3, componentType=5126, count=len(normals)//3, type="VEC3"),
    ]

    # Material
    gltf.materials = [Material(
        name=material_name,
        pbrMetallicRoughness=PbrMetallicRoughness(
            metallicFactor=0.5,
            roughnessFactor=0.3
        )
    )]

    # Mesh
    gltf.meshes = [Mesh(
        primitives=[Primitive(
            attributes={"POSITION": 0, "COLOR_0": 2, "NORMAL": 3},
            indices=1,
            material=0
        )]
    )]

    # Node and Scene
    gltf.nodes = [Node(mesh=0)]
    gltf.scenes = [Scene(nodes=[0])]
    gltf.scene = 0

    # Set binary blob
    gltf.set_binary_blob(buffer_data)

    # Save as GLB
    output_path = f"assets/models/{filename}"
    gltf.save(output_path)

    return os.path.getsize(output_path)

def main():
    """Generate all placeholder models"""

    print("Generating on-brand SkyyRose placeholder models...\n")

    os.makedirs("assets/models", exist_ok=True)

    models = [
        {
            "name": "Signature Rose",
            "filename": "placeholder-signature.glb",
            "generator": create_rose_geometry,
            "material": "SkyyRose Pink"
        },
        {
            "name": "Love Hurts Heart",
            "filename": "placeholder-lovehurts.glb",
            "generator": create_heart_geometry,
            "material": "Dark Romance"
        },
        {
            "name": "Black Rose Gothic",
            "filename": "placeholder-blackrose.glb",
            "generator": create_black_rose_geometry,
            "material": "Gothic Black"
        },
        {
            "name": "Luxury Pre-order Box",
            "filename": "placeholder-preorder.glb",
            "generator": create_luxury_box_geometry,
            "material": "Luxury Gold"
        }
    ]

    total_size = 0
    for model in models:
        vertices, indices, colors, normals = model["generator"]()
        size = create_glb(vertices, indices, colors, normals, model["filename"], model["material"])
        total_size += size
        print(f"✓ Created {model['name']}: {model['filename']} ({size/1024:.1f}KB)")

    print(f"\n✓ Generated {len(models)} on-brand models")
    print(f"  Total size: {total_size/1024:.1f}KB")
    print(f"  Location: assets/models/")
    print(f"\n  Brand aesthetic: SkyyRose luxury with dark elegance")

if __name__ == "__main__":
    main()
