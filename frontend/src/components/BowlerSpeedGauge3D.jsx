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
        🎯 3D Bowling Speed Gauge unavailable.
      </div>
    );
    return this.props.children;
  }
}

/* ── Delivery type colours ──────────────────────── */
const TYPE_COLORS = {
  'Outswing':     '#3b82f6',
  'Inswing':      '#06b6d4',
  'Bouncer':      '#ef4444',
  'Yorker':       '#f59e0b',
  'Slower Ball':  '#a855f7',
  'Off-cutter':   '#10b981',
  'Leg-cutter':   '#84cc16',
  'Off-break':    '#ec4899',
  'Leg-break':    '#f97316',
  'Googly':       '#e11d48',
  'Doosra':       '#8b5cf6',
  'Arm Ball':     '#14b8a6',
  'Straight':     '#6366f1',
  'Seam':         '#0ea5e9',
  'Reverse Swing':'#dc2626',
};

function getColor(type) {
  const key = Object.keys(TYPE_COLORS).find(k => type?.toLowerCase().includes(k.toLowerCase()));
  return key ? TYPE_COLORS[key] : '#64748b';
}

/* ── Speedometer arc in 3D ──────────────────────── */
function SpeedArc({ speed = 140, maxSpeed = 160 }) {
  const fraction = Math.min(speed / maxSpeed, 1);
  const arcAngle = Math.PI * fraction;
  const segments = 64;
  const radius = 3;
  const points = [];

  for (let i = 0; i <= segments; i++) {
    const angle = Math.PI - (Math.PI * (i / segments));
    points.push(new THREE.Vector3(
      Math.cos(angle) * radius,
      Math.sin(angle) * radius,
      0
    ));
  }

  const needleAngle = Math.PI - arcAngle;
  const needleEnd = new THREE.Vector3(
    Math.cos(needleAngle) * (radius - 0.4),
    Math.sin(needleAngle) * (radius - 0.4),
    0
  );

  // Color based on speed
  const speedColor = speed >= 145 ? '#ef4444' : speed >= 135 ? '#f59e0b' : speed >= 120 ? '#3b82f6' : '#22c55e';

  return (
    <group position={[0, -1, 0]}>
      {/* Background arc */}
      <Line points={points.map(p => [p.x, p.y, p.z])} color="#334155" lineWidth={6} />

      {/* Active arc */}
      {(() => {
        const activePoints = [];
        const activeSegments = Math.floor(segments * fraction);
        for (let i = 0; i <= activeSegments; i++) {
          const angle = Math.PI - (Math.PI * (i / segments));
          activePoints.push([
            Math.cos(angle) * radius,
            Math.sin(angle) * radius,
            0,
          ]);
        }
        return activePoints.length >= 2 ? (
          <Line points={activePoints} color={speedColor} lineWidth={8} />
        ) : null;
      })()}

      {/* Needle */}
      <Line
        points={[[0, 0, 0], [needleEnd.x, needleEnd.y, needleEnd.z]]}
        color="#fff"
        lineWidth={3}
      />

      {/* Center hub */}
      <mesh position={[0, 0, 0.1]}>
        <circleGeometry args={[0.25, 32]} />
        <meshBasicMaterial color="#f8fafc" />
      </mesh>

      {/* Speed label */}
      <Html position={[0, 1.2, 0]} center>
        <div style={{
          color: speedColor, fontSize: '2rem', fontWeight: 900, fontFamily: "'Inter', sans-serif",
          textShadow: `0 0 20px ${speedColor}60`,
        }}>
          {speed} <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#94a3b8' }}>km/h</span>
        </div>
      </Html>

      {/* Min / Max labels */}
      <Html position={[-3.2, -0.2, 0]} center>
        <span style={{ color: '#64748b', fontSize: '0.65rem', fontWeight: 700 }}>90</span>
      </Html>
      <Html position={[3.2, -0.2, 0]} center>
        <span style={{ color: '#64748b', fontSize: '0.65rem', fontWeight: 700 }}>160</span>
      </Html>
    </group>
  );
}

/* ── Animated pulsing ring ────────────────────────── */
function PulsingRing() {
  const ref = useRef();
  useFrame((state) => {
    if (ref.current) {
      const s = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.08;
      ref.current.scale.set(s, s, 1);
    }
  });
  return (
    <mesh ref={ref} position={[0, -1, -0.1]}>
      <ringGeometry args={[3.1, 3.3, 64]} />
      <meshBasicMaterial color="#475569" transparent opacity={0.3} />
    </mesh>
  );
}

/* ── Main component ──────────────────────────────── */
export function BowlerSpeedGauge3D({ bowlerPrediction }) {
  const bp = bowlerPrediction || {};
  const deliveryTypes = Array.isArray(bp.delivery_types) && bp.delivery_types.length > 0
    ? bp.delivery_types
    : [
        { type: 'Seam', percentage: 40, avg_speed_kph: 138 },
        { type: 'Bouncer', percentage: 20, avg_speed_kph: 145 },
        { type: 'Yorker', percentage: 15, avg_speed_kph: 140 },
        { type: 'Slower Ball', percentage: 15, avg_speed_kph: 115 },
        { type: 'Off-cutter', percentage: 10, avg_speed_kph: 128 },
      ];

  const phaseBowling = bp.phase_bowling || {};

  // Calculate max speed for gauge
  const allSpeeds = deliveryTypes.map(d => d.avg_speed_kph || 130);
  const maxSpeed = Math.max(...allSpeeds);
  const avgSpeed = Math.round(allSpeeds.reduce((a, b) => a + b, 0) / allSpeeds.length);

  return (
    <ErrorBoundary3D>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 16, marginBottom: 16 }}>
        {/* 3D Speed Gauge */}
        <div className="neo-raised panel-card" style={{ padding: 0, overflow: 'hidden', borderRadius: 16 }}>
          <div style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            padding: '6px 16px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              🔫 Bowling Speed Analysis
            </span>
            <span style={{ color: '#ef4444', fontSize: '0.72rem', fontWeight: 700 }}>LIVE DATA</span>
          </div>
          <div style={{ height: 320, background: 'linear-gradient(180deg, #0f172a, #1e293b)' }}>
            <Canvas camera={{ position: [0, 0.5, 7], fov: 40 }}>
              <ambientLight intensity={0.5} />
              <Suspense fallback={null}>
                <SpeedArc speed={maxSpeed} maxSpeed={160} />
                <PulsingRing />
              </Suspense>
            </Canvas>
          </div>
        </div>

        {/* TV Broadcast Side Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {/* Delivery Type Mix */}
          <div className="neo-raised panel-card" style={{ padding: 14 }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-gray)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
              Delivery Arsenal
            </div>
            {deliveryTypes.sort((a, b) => (b.percentage || 0) - (a.percentage || 0)).map((dt, i) => {
              const color = getColor(dt.type);
              return (
                <div key={i} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-dark)' }}>
                      <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: 2, background: color, marginRight: 6 }} />
                      {dt.type}
                    </span>
                    <span style={{ fontSize: '0.7rem', fontWeight: 800, color }}>
                      {dt.avg_speed_kph || '?'} km/h
                    </span>
                  </div>
                  <div style={{ height: 5, borderRadius: 3, background: '#e2e8f0' }}>
                    <div style={{
                      height: '100%', borderRadius: 3,
                      background: `linear-gradient(90deg, ${color}, ${color}88)`,
                      width: `${Math.min(dt.percentage || 0, 100)}%`,
                      transition: 'width 0.5s ease',
                    }} />
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-gray)', marginTop: 1 }}>
                    {dt.percentage}% of deliveries
                  </div>
                </div>
              );
            })}
          </div>

          {/* Phase Economy */}
          {(phaseBowling.powerplay_economy || phaseBowling.middle_economy || phaseBowling.death_economy) && (
            <div className="neo-raised panel-card" style={{ padding: 14 }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-gray)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
                Phase Economy
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {[
                  { label: 'PP', key: 'powerplay_economy', color: '#3b82f6' },
                  { label: 'MID', key: 'middle_economy', color: '#22c55e' },
                  { label: 'DEATH', key: 'death_economy', color: '#ef4444' },
                ].map((phase, i) => {
                  const val = phaseBowling[phase.key];
                  if (val == null) return null;
                  return (
                    <div key={i} style={{
                      flex: 1, background: `${phase.color}10`, borderRadius: 8,
                      padding: '8px 6px', textAlign: 'center',
                      border: `1px solid ${phase.color}30`,
                    }}>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-gray)', fontWeight: 700, marginBottom: 2 }}>{phase.label}</div>
                      <div style={{ fontSize: '1rem', fontWeight: 900, color: phase.color }}>{val}</div>
                      <div style={{ fontSize: '0.55rem', color: 'var(--text-gray)' }}>rpo</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Batters targeted */}
          {bp.success_rate_vs_batters && (
            <div className="neo-raised panel-card" style={{ padding: 14 }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-gray)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
                Matchup Targets
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dark)', lineHeight: 1.5 }}>
                {bp.success_rate_vs_batters}
              </div>
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary3D>
  );
}
