import React, { useRef, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { 
  OrbitControls, 
  MeshDistortMaterial, 
  Float, 
  ContactShadows, 
  Environment,
  Cylinder,
  Sphere
} from '@react-three/drei';
import * as THREE from 'three';

const Plant: React.FC<{ day: number }> = ({ day }) => {
  const groupRef = useRef<THREE.Group>(null);
  
  // Growth scale based on day (1 to 20)
  const scale = 0.6 + (day / 20) * 1.4;

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
    }
  });

  return (
    <group ref={groupRef} scale={[scale, scale, scale]} position={[0, -1.5, 0]}>
      {/* Stem */}
      <Cylinder args={[0.05, 0.08, 2, 8]} position={[0, 1, 0]}>
        <meshStandardMaterial color="#3f6212" />
      </Cylinder>

      {/* Leaves */}
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
        <mesh position={[0.2, 0.8, 0]} rotation={[0, 0, -Math.PI / 4]}>
          <sphereGeometry args={[0.3, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
          <MeshDistortMaterial color="#22c55e" speed={2} distort={0.3} />
        </mesh>
      </Float>
      
      <Float speed={1.5} rotationIntensity={0.8} floatIntensity={0.4}>
        <mesh position={[-0.3, 1.4, 0.1]} rotation={[0, 0, Math.PI / 3]}>
          <sphereGeometry args={[0.4, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
          <MeshDistortMaterial color="#16a34a" speed={1.5} distort={0.4} />
        </mesh>
      </Float>

      {day > 10 && (
        <Float speed={1} rotationIntensity={1} floatIntensity={0.6}>
          <mesh position={[0.4, 1.8, -0.2]} rotation={[0, 0, -Math.PI / 2.5]}>
            <sphereGeometry args={[0.5, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
            <MeshDistortMaterial color="#15803d" speed={1} distort={0.5} />
          </mesh>
        </Float>
      )}

      {/* Soil/Pot */}
      <mesh position={[0, -0.1, 0]}>
        <cylinderGeometry args={[0.6, 0.4, 0.4, 32]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
    </group>
  );
};

export const PlantView: React.FC<{ day: number }> = ({ day }) => {
  return (
    <div className="relative w-full h-full min-h-[400px] flex items-center justify-center">
      <div className="w-full h-full z-10">
        <Canvas camera={{ position: [0, 2, 8], fov: 45 }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1} />
          <spotLight position={[-10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
          
          <Suspense fallback={null}>
            <Plant day={day} />
            <ContactShadows 
              position={[0, -1.6, 0]} 
              opacity={0.4} 
              scale={10} 
              blur={2.5} 
              far={4} 
            />
            <Environment preset="city" />
          </Suspense>
          
          <OrbitControls 
            makeDefault
            enableZoom={true} 
            enablePan={false} 
            minDistance={3}
            maxDistance={15}
            minPolarAngle={0} 
            maxPolarAngle={Math.PI / 1.8} 
          />
        </Canvas>
      </div>
    </div>
  );
};
