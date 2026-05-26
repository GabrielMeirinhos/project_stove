import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { MeshDistortMaterial, Sphere, Cylinder, Float } from '@react-three/drei';
import * as THREE from 'three';

interface PlantProps {
  day: number;
  health: number;
}

export const ProceduralPlant: React.FC<PlantProps> = ({ day, health }) => {
  const groupRef = useRef<THREE.Group>(null);
  
  // Growth scale based on day
  const scale = 0.5 + (day - 1) * 0.4;
  const healthColor = health > 80 ? '#22c55e' : health > 50 ? '#facc15' : '#ef4444';

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
    }
  });

  return (
    <group ref={groupRef} scale={[scale, scale, scale]} position={[0, -1, 0]}>
      {/* Stem */}
      <Cylinder args={[0.05, 0.08, 2, 8]} position={[0, 1, 0]}>
        <meshStandardMaterial color="#3f6212" />
      </Cylinder>

      {/* Leaves - Day 1 */}
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
        <mesh position={[0.2, 0.8, 0]} rotation={[0, 0, -Math.PI / 4]}>
          <sphereGeometry args={[0.3, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
          <MeshDistortMaterial color={healthColor} speed={2} distort={0.3} />
        </mesh>
      </Float>

      {/* More leaves for later days */}
      {day >= 2 && (
        <Float speed={1.5} rotationIntensity={0.8} floatIntensity={0.4}>
          <mesh position={[-0.3, 1.4, 0.1]} rotation={[0, 0, Math.PI / 3]}>
            <sphereGeometry args={[0.4, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
            <MeshDistortMaterial color={healthColor} speed={1.5} distort={0.4} />
          </mesh>
        </Float>
      )}

      {day >= 3 && (
        <>
          <Float speed={1} rotationIntensity={1} floatIntensity={0.6}>
            <mesh position={[0.4, 1.8, -0.2]} rotation={[0, 0, -Math.PI / 2.5]}>
              <sphereGeometry args={[0.5, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
              <MeshDistortMaterial color={healthColor} speed={1} distort={0.5} />
            </mesh>
          </Float>
          {/* Flower for day 3 */}
          <mesh position={[0, 2.1, 0]}>
            <sphereGeometry args={[0.15, 16, 16]} />
            <meshStandardMaterial color="#facc15" emissive="#facc15" emissiveIntensity={0.5} />
          </mesh>
        </>
      )}

      {/* Soil/Pot */}
      <mesh position={[0, -0.1, 0]}>
        <cylinderGeometry args={[0.6, 0.4, 0.4, 32]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
    </group>
  );
};
