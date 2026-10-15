import React, { Suspense, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, Line } from '@react-three/drei';
import * as THREE from 'three';

/* ── Error Boundary ─────────────────────────────── */
class ErrorBoundary3D extends React.Component {
  constructor(p) { super(p); this.state = { err: false }; }
  static getDerivedStateFromError() { return { err: true }; }
  render() {
    if (this.state.err) return (
      <div className="neo-raised panel-card" style={{ padding: 24, textAlign: 'center', color: 'var(--text-gray)' }}>
        🎯 3D Bowling Pitch Map unavailable.
      </div>
    );
    return this.props.children;
  }
}

/* ── Zone colour map ────────────────────────────── */
const ZONE_COLORS = {
  good_length: '#22c55e',
  short:       '#ef4444',
  yorker:      '#3b82f6',
  full:        '#f59e0b',
  half_volley: '#a855f7',
};

const ZONE_LABELS = {
  good_length: 'Good Length',
  short:       'Short / Bouncer',
  yorker:      'Yorker',
  full:        'Full',
  half_volley: 'Half Volley',
};

/* ── Pitch Zone Positions (Z-axis = pitch length, X = line) ── */
const ZONE_POSITIONS = {
  yorker:      { zMin: -0.3, zMax: 0.6 },
  full:        { zMin: 0.6,  zMax: 1.8 },
  half_volley: { zMin: 1.8,  zMax: 2.6 },
  good_length: { zMin: 2.6,  zMax: 4.4 },
  short:       { zMin: 4.4,  zMax: 6.2 },
};

/* ── Generate random dots within a zone ──────────── */
function generateDots(zone, count) {
  const pos = ZONE_POSITIONS[zone] || { zMin: 2, zMax: 4 };
  const dots = [];
  for (let i = 0; i < count; i++) {
    const x = (Math.random() - 0.5) * 1.4;  // stump-to-stump spread
    const z = pos.zMin + Math.random() * (pos.zMax - pos.zMin);
    dots.push([x, 0.04, z]);
  }
  return dots;
}

/* ── Animated rotating ball ──────────────────────── */
function SpinningBall({ position }) {
  const ref = useRef();
  useFrame((_, dt) => {
    if (ref.current) {
      ref.current.rotation.x += dt * 4;
      ref.current.rotation.z += dt * 2;
    }
  });
  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[0.18, 32, 32]} />
      <meshStandardMaterial color="#dc2626" roughness={0.3} metalness={0.2} />
    </mesh>
  );
}

/* ── 3D Pitch scene ──────────────────────────────── */
function PitchScene({ pitchZones }) {
  return (
    <group>
      {/* Pitch surface */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 3]}>
        <planeGeometry args={[2.6, 7.5]} />
        <meshStandardMaterial color="#c4a35a" roughness={0.9} />
      </mesh>

      {/* Crease lines */}
      {[0, 6.5].map((z, i) => (
        <Line key={`crease-${i}`}
          points={[[-1.1, 0.02, z], [1.1, 0.02, z]]}
          color="#fff" lineWidth={2}
        />
      ))}

      {/* Stumps at batsman's end */}
      {[-0.12, 0, 0.12].map((x, i) => (
        <mesh key={`stump-${i}`} position={[x, 0.35, -0.1]}>
          <cylinderGeometry args={[0.02, 0.02, 0.7, 8]} />
          <meshStandardMaterial color="#f5f0e0" />
        </mesh>
      ))}

      {/* Stumps at bowler's end */}
      {[-0.12, 0, 0.12].map((x, i) => (
        <mesh key={`stump-b-${i}`} position={[x, 0.35, 6.6]}>
          <cylinderGeometry args={[0.02, 0.02, 0.7, 8]} />
          <meshStandardMaterial color="#f5f0e0" />
        </mesh>
      ))}

      {/* Zone strips (translucent) */}
      {pitchZones.map((pz, i) => {
        const zone = pz.zone;
        const pos = ZONE_POSITIONS[zone];
        if (!pos) return null;
        const height = pos.zMax - pos.zMin;
        const centerZ = pos.zMin + height / 2;
        return (
          <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, centerZ]}>
            <planeGeometry args={[2.4, height]} />
            <meshBasicMaterial
              color={ZONE_COLORS[zone] || '#888'}
              transparent opacity={0.12}
              side={THREE.DoubleSide}
            />
          </mesh>
        );
      })}

      {/* Delivery dots (beehive clusters) */}
      {pitchZones.map((pz, i) => {
        const dotCount = Math.max(3, Math.round((pz.percentage || 20) / 5));
        const dots = generateDots(pz.zone, dotCount);
        const color = ZONE_COLORS[pz.zone] || '#888';
        return dots.map((d, j) => (
          <mesh key={`dot-${i}-${j}`} position={d}>
            <sphereGeometry args={[0.06, 16, 16]} />
            <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.6} />
          </mesh>
        ));
      })}

      {/* Ball at bowler's end */}
      <SpinningBall position={[0, 1.8, 7.5]} />
    </group>
  );
}

/* ── Main exported component ─────────────────────── */
export function BowlingPitchMap3D({ bowlerPrediction }) {
  const bp = bowlerPrediction || {};
  const pitchZones = Array.isArray(bp.pitch_zones) && bp.pitch_zones.length > 0
    ? bp.pitch_zones
    : [
        { zone: 'good_length', percentage: 40, wicket_pct: 50 },
        { zone: 'short', percentage: 25, wicket_pct: 20 },
        { zone: 'yorker', percentage: 15, wicket_pct: 20 },
        { zone: 'full', percentage: 15, wicket_pct: 8 },
        { zone: 'half_volley', percentage: 5, wicket_pct: 2 },
      ];

  return (
    <ErrorBoundary3D>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: 16, marginBottom: 16 }}>
        {/* 3D Pitch Canvas */}
        <div className="neo-raised panel-card" style={{ padding: 0, overflow: 'hidden', borderRadius: 16 }}>
          <div style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            padding: '6px 16px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              🎯 Hawk-Eye Bowling Pitch Map
            </span>
            <span style={{ color: '#f59e0b', fontSize: '0.72rem', fontWeight: 700 }}>PREDICTED</span>
          </div>
          <div style={{ height: 380, background: '#0f172a' }}>
            <Canvas camera={{ position: [0, 8, -3], fov: 38 }}>
              <ambientLight intensity={0.6} />
              <directionalLight position={[5, 10, -5]} intensity={0.8} />
              <pointLight position={[0, 5, 3]} intensity={0.4} color="#fbbf24" />
              <Suspense fallback={null}>
                <PitchScene pitchZones={pitchZones} />
              </Suspense>
              <OrbitControls
                enableZoom={true} enablePan={false}
                minPolarAngle={0.3} maxPolarAngle={1.3}
                target={[0, 0, 3]}
              />
            </Canvas>
          </div>
        </div>

        {/* TV Broadcast Stats Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {/* Zone breakdown */}
          <div className="neo-raised panel-card" style={{ padding: 14 }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-gray)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
              Pitch Zone Breakdown
            </div>
            {pitchZones.map((pz, i) => {
              const color = ZONE_COLORS[pz.zone] || '#888';
              const label = ZONE_LABELS[pz.zone] || pz.zone;
              return (
                <div key={i} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 3 }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-dark)' }}>
                      <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: color, marginRight: 6 }} />
                      {label}
                    </span>
                    <span style={{ fontSize: '0.72rem', fontWeight: 800, color }}>{pz.percentage}%</span>
                  </div>
                  <div style={{ height: 5, borderRadius: 3, background: '#e2e8f0' }}>
                    <div style={{
                      height: '100%', borderRadius: 3,
                      background: `linear-gradient(90deg, ${color}, ${color}aa)`,
                      width: `${Math.min(pz.percentage || 0, 100)}%`,
                      transition: 'width 0.5s ease',
                    }} />
                  </div>
                  {pz.wicket_pct != null && (
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-gray)', marginTop: 2 }}>
                      {pz.wicket_pct}% of wickets from this zone
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Key stats */}
          <div className="neo-raised panel-card" style={{ padding: 14 }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-gray)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
              Predicted Figures
            </div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
              <div style={{ flex: 1, background: 'rgba(34,197,94,0.08)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-gray)', fontWeight: 700 }}>WICKETS</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#22c55e' }}>{bp.predicted_wickets || 'N/A'}</div>
              </div>
              <div style={{ flex: 1, background: 'rgba(245,158,11,0.08)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-gray)', fontWeight: 700 }}>ECONOMY</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#f59e0b' }}>{bp.predicted_economy || 'N/A'}</div>
              </div>
            </div>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-dark)', fontWeight: 600 }}>
              {bp.role_in_match || ''}
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary3D>
  );
}
