'use client';

import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Text3D, Center, Float, Environment } from '@react-three/drei';
import type { Mesh, Group } from 'three';

interface LogoMeshProps {
  text: string;
  color: string;
  speed?: number;
}

function LogoMesh({ text, color, speed = 0.3 }: LogoMeshProps) {
  const groupRef = useRef<Group>(null);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * speed;
    }
  });

  return (
    <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
      <group ref={groupRef}>
        <Center>
          <Text3D
            font="/fonts/helvetiker_bold.typeface.json"
            size={0.5}
            height={0.15}
            curveSegments={12}
            bevelEnabled
            bevelThickness={0.02}
            bevelSize={0.01}
            bevelSegments={5}
          >
            {text}
            <meshStandardMaterial
              color={color}
              metalness={0.8}
              roughness={0.2}
              envMapIntensity={1.5}
            />
          </Text3D>
        </Center>
      </group>
    </Float>
  );
}

interface RotatingCollectionLogoProps {
  text: string;
  color: string;
  className?: string;
}

export default function RotatingCollectionLogo({
  text,
  color,
  className = '',
}: RotatingCollectionLogoProps) {
  return (
    <div className={`w-full h-[200px] ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 3], fov: 50 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <pointLight position={[-5, -5, -5]} intensity={0.5} color={color} />
        <LogoMesh text={text} color={color} />
        <Environment preset="studio" />
      </Canvas>
    </div>
  );
}
