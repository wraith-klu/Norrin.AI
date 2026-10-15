import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import * as THREE from 'three';

function ShotArc({ start, end, color, label }) {
  const points = [];
  const midX = (start[0] + end[0]) / 2;
  const midZ = (start[2] + end[2]) / 2;
  const peakY = 4.5;

  for (let t = 0; t <= 1; t += 0.05) {
    const x = start[0] + (end[0] - start[0]) * t;
    const z = start[2] + (end[2] - start[2]) * t;
    const y = 4 * peakY * t * (1 - t);
    points.push(new THREE.Vector3(x, y, z));
  }

  const curve = new THREE.CatmullRomCurve3(points);

  return (
    <group>
      {/* 3D Arc Tube */}
      <mesh>
        <tubeGeometry args={[curve, 32, 0.12, 8, false]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.6} />
      </mesh>

      {/* Landing Spot Marker */}
      <mesh position={end}>
        <cylinderGeometry args={[0.3, 0.3, 0.05, 16]} />
        <meshBasicMaterial color={color} />
      </mesh>

      {/* Shot Type Tag */}
      <Text position={[end[0], 0.6, end[2]]} fontSize={0.4} color="#ffffff" anchorX="center" anchorY="middle">
        {label}
      </Text>
    </group>
  );
}

export function WagonWheel3D({ batsmanPrediction }) {
  const customShots = batsmanPrediction?.shot_distribution;

  // Sector landing vector dictionary
  const sectorMap = {
    'cover': [7, 0, -5],
    'off side': [8, 0, -3],
    'mid-wicket': [-8, 0, -3],
    'on side': [-7, 0, -4],
    'straight': [0, 0, -11],
    'third man': [6, 0, 7],
    'fine leg': [-6, 0, 8],
    'point': [9, 0, 1],
  };

  let shots = [];
  if (Array.isArray(customShots) && customShots.length > 0) {
    shots = customShots.map(s => {
      const secKey = (s.sector || 'straight').toLowerCase();
      let endVec = [0, 0, -9];
      Object.keys(sectorMap).forEach(k => {
        if (secKey.includes(k)) endVec = sectorMap[k];
      });
      const color = s.efficiency === 'weakness' ? '#ef4444' : s.efficiency === 'strength' ? '#10b981' : '#3b82f6';
      return { label: s.shot_name, end: endVec, color };
    });
  } else {
    // Derive dynamically from strengths & weaknesses
    const strengths = batsmanPrediction?.bowling_strength || [];
    const weaknesses = batsmanPrediction?.bowling_weakness || [];

    shots = [
      { label: `Cover Drive (${strengths[0] || 'Off Pace'}) 🏏`, end: [7, 0, -5], color: '#10b981' },
      { label: `Straight Loft 🚀`, end: [0, 0, -11], color: '#3b82f6' },
      { label: `Pull / Hook (${strengths[1] || 'Short'}) 💥`, end: [-8, 0, -3], color: '#10b981' },
      { label: `Square Cut ⚡`, end: [9, 0, 1], color: '#06b6d4' },
      { label: `Edge Danger (${weaknesses[0] || 'Outswing'}) ⚠️`, end: [6, 0, 7], color: '#ef4444' },
    ];
  }

  return (
    <div className="neo-raised panel-card" style={{ padding: 0, overflow: 'hidden', position: 'relative', borderRadius: 16 }}>
      <div
        style={{
          position: 'absolute',
          top: 16,
          left: 16,
          zIndex: 10,
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(8px)',
          padding: '8px 14px',
          borderRadius: 10,
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#fff',
          fontSize: '0.82rem',
          fontWeight: 600,
          pointerEvents: 'none',
        }}
      >
        🎯 3D Player Shot Distribution Wagon Wheel
      </div>

      <div style={{ width: '100%', height: 380, background: 'radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%)' }}>
        <Canvas camera={{ position: [0, 16, 18], fov: 45 }}>
          <ambientLight intensity={0.8} />
          <directionalLight position={[10, 20, 10]} intensity={1} />

          {/* Outfield disc */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]}>
            <circleGeometry args={[12, 64]} />
            <meshStandardMaterial color="#14532d" roughness={0.8} />
          </mesh>

          {/* 3D Pitch */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
            <planeGeometry args={[1.5, 5]} />
            <meshStandardMaterial color="#ca8a04" />
          </mesh>

          <Suspense fallback={null}>
            {shots.map((s, idx) => (
              <ShotArc key={idx} start={[0, 0.2, 1.8]} end={s.end} color={s.color} label={s.label} />
            ))}
          </Suspense>

          <OrbitControls enablePan={true} enableZoom={true} maxPolarAngle={Math.PI / 2 - 0.05} />
        </Canvas>
      </div>

      <div style={{ display: 'flex', gap: 16, padding: '12px 18px', background: 'var(--bg-card)', fontSize: '0.75rem', fontWeight: 600 }}>
        <span style={{ color: '#10b981' }}>🟢 Scoring Shot Sector</span>
        <span style={{ color: '#3b82f6' }}>🔵 Power Hit Sector</span>
        <span style={{ color: '#ef4444' }}>🔴 Edge &amp; Dismissal Danger Sector</span>
      </div>
    </div>
  );
}

export default WagonWheel3D;
