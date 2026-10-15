import React, { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

function PhaseBar3D({ position, height, color, isHovered, onHover, onUnhover }) {
  return (
    <group position={position}>
      {/* 3D Volumetric Bar */}
      <mesh
        position={[0, height / 2, 0]}
        onPointerOver={onHover}
        onPointerOut={onUnhover}
      >
        <boxGeometry args={[1.8, height, 1.8]} />
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

export function ImpactMatrix3D({ batsmanPrediction, bowlerPrediction }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);
  const pImpact = batsmanPrediction?.phase_impact || bowlerPrediction?.phase_impact || {};

  const pp = Number(pImpact.powerplay_pct) || 75;
  const mid = Number(pImpact.middle_pct) || 82;
  const death = Number(pImpact.death_pct) || 90;

  const phases = [
    { title: 'Powerplay Phase', overs: 'Overs 1 – 6', pos: [-3.8, 0, 0], height: (pp / 100) * 4.5, color: '#3b82f6', score: pp, desc: 'Early boundary threat & fast scoring rate' },
    { title: 'Middle Overs Phase', overs: 'Overs 7 – 15', pos: [0, 0, 0], height: (mid / 100) * 4.5, color: '#10b981', score: mid, desc: 'Spin adaptation & innings consolidation' },
    { title: 'Death Overs Phase', overs: 'Overs 16 – 20', pos: [3.8, 0, 0], height: (death / 100) * 4.5, color: '#ef4444', score: death, desc: 'Clutch boundary hitting & Yorker execution' },
  ];

  return (
    <div className="neo-raised panel-card" style={{ padding: 0, overflow: 'hidden', borderRadius: 16 }}>
      {/* TV Graphic Banner */}
      <div
        style={{
          background: 'linear-gradient(90deg, #1e1b4b 0%, #0f172a 100%)',
          borderLeft: '4px solid #8b5cf6',
          padding: '10px 18px',
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ color: '#a78bfa', fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            STAR SPORTS BROADCAST ANALYTICS
          </div>
          <div style={{ color: '#ffffff', fontSize: '0.95rem', fontWeight: 700 }}>
            ⚡ 3D Match Phase Impact Matrix (Overs 1 – 20)
          </div>
        </div>
        <div style={{ background: 'rgba(0,0,0,0.4)', padding: '4px 10px', borderRadius: 6, color: '#ddd6fe', fontSize: '0.75rem', fontWeight: 700 }}>
          TV GRAPHICS MODE
        </div>
      </div>

      {/* 2-Column Split Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', background: '#0b0f19' }}>
        {/* Left Column: Clean 3D Volumetric Scene */}
        <div style={{ height: 380, position: 'relative', borderRight: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 10, color: '#94a3b8', fontSize: '0.72rem', fontWeight: 600 }}>
            🎮 Drag to rotate 3D bars
          </div>

          <Canvas camera={{ position: [0, 6, 11], fov: 45 }}>
            <ambientLight intensity={0.8} />
            <directionalLight position={[10, 15, 10]} intensity={1.3} />

            {/* 3D Grid Floor */}
            <gridHelper args={[20, 20, '#475569', '#1e293b']} position={[0, -0.05, 0]} />

            <Suspense fallback={null}>
              {phases.map((p, idx) => (
                <PhaseBar3D
                  key={idx}
                  position={p.pos}
                  height={p.height}
                  color={p.color}
                  isHovered={hoveredIdx === idx}
                  onHover={() => setHoveredIdx(idx)}
                  onUnhover={() => setHoveredIdx(null)}
                />
              ))}
            </Suspense>

            <OrbitControls enablePan={true} enableZoom={true} maxPolarAngle={Math.PI / 2 - 0.05} />
          </Canvas>
        </div>

        {/* Right Column: TV Telecast Impact Table */}
        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 14 }}>
          <div style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            MATCH PHASE IMPACT RATINGS
          </div>

          {phases.map((p, idx) => {
            const isHovered = hoveredIdx === idx;
            return (
              <div
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                style={{
                  background: isHovered ? 'rgba(30, 41, 59, 0.9)' : 'rgba(15, 23, 42, 0.6)',
                  border: `1.5px solid ${isHovered ? p.color : 'rgba(255,255,255,0.08)'}`,
                  borderLeft: `4px solid ${p.color}`,
                  borderRadius: 10,
                  padding: '10px 14px',
                  transition: 'all 0.2s ease',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <div>
                    <span style={{ color: '#ffffff', fontSize: '0.88rem', fontWeight: 800 }}>{p.title}</span>
                    <span style={{ color: '#94a3b8', fontSize: '0.72rem', marginLeft: 8 }}>({p.overs})</span>
                  </div>
                  <span style={{ color: p.color, fontSize: '0.95rem', fontWeight: 900 }}>{p.score}%</span>
                </div>

                {/* Progress bar */}
                <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.1)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: `${p.score}%`, height: '100%', background: p.color, transition: 'width 0.5s ease' }} />
                </div>
                <div style={{ color: '#94a3b8', fontSize: '0.72rem', marginTop: 4 }}>{p.desc}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default ImpactMatrix3D;
