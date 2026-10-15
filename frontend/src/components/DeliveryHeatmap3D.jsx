import React, { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';

function LengthZoneBlock({ position, size, color, isHovered, onHover, onUnhover }) {
  return (
    <group position={position}>
      {/* 3D Elevated Pitch Block */}
      <mesh
        position={[0, size[1] / 2, 0]}
        onPointerOver={onHover}
        onPointerOut={onUnhover}
      >
        <boxGeometry args={size} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isHovered ? 0.9 : 0.5}
          roughness={0.2}
          metalness={0.3}
        />
      </mesh>
    </group>
  );
}

export function DeliveryHeatmap3D({ batsmanPrediction }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  const strengths = (batsmanPrediction?.length_strength || ['Good length', 'Full (Yorker)']).map(x => x.toLowerCase());
  const weaknesses = (batsmanPrediction?.length_weakness || ['Short (Bouncer)', 'Hard length']).map(x => x.toLowerCase());

  const lengthZones = [
    { label: 'Full / Yorker', z: 2.4, key: 'yorker', dist: '0 – 2m from stumps' },
    { label: 'Drive Length', z: 1.2, key: 'full', dist: '2 – 4m from stumps' },
    { label: 'Good Length', z: 0.0, key: 'good', dist: '4 – 6m from stumps' },
    { label: 'Hard Length', z: -1.2, key: 'hard', dist: '6 – 8m from stumps' },
    { label: 'Short / Bouncer', z: -2.4, key: 'short', dist: '8m+ from stumps' },
  ];

  return (
    <div className="neo-raised panel-card" style={{ padding: 0, overflow: 'hidden', borderRadius: 16 }}>
      {/* TV Graphic Banner */}
      <div
        style={{
          background: 'linear-gradient(90deg, #7c2d12 0%, #0f172a 100%)',
          borderLeft: '4px solid #ea580c',
          padding: '10px 18px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ color: '#fdba74', fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            HAWK-EYE BROADCAST TELECAST
          </div>
          <div style={{ color: '#ffffff', fontSize: '0.95rem', fontWeight: 700 }}>
            📊 3D Delivery Pitch Map &amp; Length Vulnerability
          </div>
        </div>
        <div style={{ background: 'rgba(0,0,0,0.4)', padding: '4px 10px', borderRadius: 6, color: '#fed7aa', fontSize: '0.75rem', fontWeight: 700 }}>
          TV GRAPHICS MODE
        </div>
      </div>

      {/* 2-Column Split Layout: Left 3D View, Right TV Broadcast Stat Card */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', background: '#0b0f19' }}>
        {/* Left Column: 3D Pitch Scene */}
        <div style={{ height: 380, position: 'relative', borderRight: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 10, color: '#94a3b8', fontSize: '0.72rem', fontWeight: 600 }}>
            🎮 Drag to rotate pitch
          </div>

          <Canvas camera={{ position: [5, 6, 7], fov: 45 }}>
            <ambientLight intensity={0.8} />
            <directionalLight position={[5, 12, 5]} intensity={1.2} />

            {/* 3D Pitch Strip */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]}>
              <planeGeometry args={[2.2, 7.8]} />
              <meshStandardMaterial color="#854d0e" roughness={0.9} />
            </mesh>

            {/* Creases */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 3.4]}>
              <planeGeometry args={[2.4, 0.08]} />
              <meshBasicMaterial color="#ffffff" />
            </mesh>
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -3.4]}>
              <planeGeometry args={[2.4, 0.08]} />
              <meshBasicMaterial color="#ffffff" />
            </mesh>

            {/* Stumps (North & South) */}
            {[-3.4, 3.4].map((zPos, sIdx) => (
              <group key={sIdx} position={[0, 0, zPos]}>
                {[-0.2, 0, 0.2].map((x, i) => (
                  <mesh key={i} position={[x, 0.35, 0]}>
                    <cylinderGeometry args={[0.02, 0.02, 0.7, 12]} />
                    <meshStandardMaterial color="#fff3b0" />
                  </mesh>
                ))}
              </group>
            ))}

            {/* Pitch End 3D Text Labels */}
            <Text position={[0, 0.1, 4.1]} rotation={[-Math.PI / 2, 0, 0]} fontSize={0.35} color="#ffffff" anchorX="center">
              STRIKER'S END
            </Text>
            <Text position={[0, 0.1, -4.1]} rotation={[-Math.PI / 2, 0, 0]} fontSize={0.35} color="#ffffff" anchorX="center">
              BOWLER'S END
            </Text>

            <Suspense fallback={null}>
              {lengthZones.map((zone, idx) => {
                const isWeak = weaknesses.some(w => w.includes(zone.key));
                const isStrong = strengths.some(s => s.includes(zone.key));
                const color = isWeak ? '#ef4444' : isStrong ? '#10b981' : '#3b82f6';
                const height = isWeak ? 1.1 : isStrong ? 0.8 : 0.45;

                return (
                  <LengthZoneBlock
                    key={idx}
                    position={[0, 0, zone.z]}
                    size={[1.8, height, 0.7]}
                    color={color}
                    isHovered={hoveredIdx === idx}
                    onHover={() => setHoveredIdx(idx)}
                    onUnhover={() => setHoveredIdx(null)}
                  />
                );
              })}
            </Suspense>

            <OrbitControls enablePan={true} enableZoom={true} maxPolarAngle={Math.PI / 2 - 0.05} />
          </Canvas>
        </div>

        {/* Right Column: Crystal Clear TV Broadcast Telecast Table */}
        <div style={{ padding: 18, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 10 }}>
          <div style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
            PITCH LENGTH PROFILE &amp; DISMISSAL RISK
          </div>

          {lengthZones.map((zone, idx) => {
            const isWeak = weaknesses.some(w => w.includes(zone.key));
            const isStrong = strengths.some(s => s.includes(zone.key));
            const color = isWeak ? '#ef4444' : isStrong ? '#10b981' : '#3b82f6';
            const statusText = isWeak ? '⚠️ HIGH VULNERABILITY' : isStrong ? '💪 DOMINANT STRENGTH' : 'NEUTRAL CONTROL';
            const isHovered = hoveredIdx === idx;

            return (
              <div
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                style={{
                  background: isHovered ? 'rgba(30, 41, 59, 0.9)' : 'rgba(15, 23, 42, 0.6)',
                  border: `1.5px solid ${isHovered ? color : 'rgba(255,255,255,0.08)'}`,
                  borderLeft: `4px solid ${color}`,
                  borderRadius: 8,
                  padding: '8px 12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'all 0.2s ease',
                  cursor: 'pointer',
                }}
              >
                <div>
                  <div style={{ color: '#ffffff', fontSize: '0.85rem', fontWeight: 700 }}>
                    {zone.label}
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>
                    {zone.dist}
                  </div>
                </div>

                <div
                  style={{
                    background: `${color}20`,
                    border: `1px solid ${color}`,
                    color: color,
                    padding: '4px 8px',
                    borderRadius: 6,
                    fontSize: '0.72rem',
                    fontWeight: 800,
                  }}
                >
                  {statusText}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default DeliveryHeatmap3D;
