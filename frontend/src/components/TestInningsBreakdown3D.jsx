import React, { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html, Line } from '@react-three/drei';
import * as THREE from 'three';

/* ── Error Boundary ─────────────────────────────── */
class ErrorBoundary3D extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) return (
      <div className="neo-raised panel-card" style={{ padding: 24, textAlign: 'center', color: 'var(--text-gray)' }}>
        ⏳ 3D Test Innings Simulation unavailable.
      </div>
    );
    return this.props.children;
  }
}

/* ── 3D Pitch Wear Scene ───────────────────────── */
function PitchWearScene({ activeDay }) {
  // Day 1-2: Fresh green/tan (#cca462), Day 3: Flat (#d4a373), Day 4-5: Cracked dry (#8c6a38)
  const pitchColor = activeDay === 'day1' ? '#cca462' : activeDay === 'day3' ? '#d4a373' : '#8c6a38';

  return (
    <group>
      {/* Main Pitch Surface */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[2.8, 8.5]} />
        <meshStandardMaterial color={pitchColor} roughness={activeDay === 'day5' ? 0.95 : 0.7} />
      </mesh>

      {/* Outfield Grass Surroundings */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]}>
        <ringGeometry args={[4.5, 9, 32]} />
        <meshStandardMaterial color="#15803d" roughness={0.8} />
      </mesh>

      {/* Creases */}
      {[-3.5, 3.5].map((z, i) => (
        <Line
          key={`crease-${i}`}
          points={[[-1.2, 0.01, z], [1.2, 0.01, z]]}
          color="#ffffff"
          lineWidth={2.5}
        />
      ))}

      {/* Stumps */}
      {[-3.5, 3.5].map((z, i) => (
        <group key={`stumps-${i}`} position={[0, 0, z]}>
          {[-0.15, 0, 0.15].map((x, j) => (
            <mesh key={`stump-${j}`} position={[x, 0.4, 0]}>
              <cylinderGeometry args={[0.02, 0.02, 0.75, 8]} />
              <meshStandardMaterial color="#fef08a" />
            </mesh>
          ))}
        </group>
      ))}

      {/* Day 4-5 Wear Cracks & Rough Footmarks */}
      {(activeDay === 'day3' || activeDay === 'day5') && (
        <group position={[0, 0.02, 0]}>
          {/* Bowlers' Footmark Roughs */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-0.6, 0, 1.8]}>
            <circleGeometry args={[0.45, 16]} />
            <meshBasicMaterial color="#544026" transparent opacity={activeDay === 'day5' ? 0.8 : 0.4} />
          </mesh>
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0.6, 0, -1.8]}>
            <circleGeometry args={[0.45, 16]} />
            <meshBasicMaterial color="#544026" transparent opacity={activeDay === 'day5' ? 0.8 : 0.4} />
          </mesh>
        </group>
      )}

      {/* Day 5 Cracks Overlay */}
      {activeDay === 'day5' && (
        <group position={[0, 0.02, 0]}>
          <Line points={[[-0.2, 0.02, -1], [0.1, 0.02, 1], [-0.1, 0.02, 2.5]]} color="#362411" lineWidth={3} />
          <Line points={[[0.4, 0.02, -2], [0.2, 0.02, 0], [0.5, 0.02, 2]]} color="#362411" lineWidth={3} />
          <Line points={[[-0.5, 0.02, 0.5], [-0.3, 0.02, 1.5]]} color="#362411" lineWidth={2} />
        </group>
      )}

      {/* 3D Label */}
      <Html position={[0, 1.5, 0]} center>
        <div style={{
          background: 'rgba(15, 23, 42, 0.88)', color: '#fff',
          padding: '6px 14px', borderRadius: 20, fontSize: '0.75rem', fontWeight: 800,
          border: '1px solid rgba(255, 255, 255, 0.2)', backdropFilter: 'blur(6px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)', whiteSpace: 'nowrap',
        }}>
          {activeDay === 'day1' && '🟩 Day 1-2: Fresh Seam & True Bounce'}
          {activeDay === 'day3' && '🟨 Day 3: True Batting Track'}
          {activeDay === 'day5' && '🟥 Day 4-5: Cracked Pitch · Variable Bounce & Turn'}
        </div>
      </Html>
    </group>
  );
}

export function TestInningsBreakdown3D({ testBreakdown, playerName }) {
  const [activeDay, setActiveDay] = useState('day1');

  const breakdown = testBreakdown || {
    first_innings: {
      predicted_performance: '55 to 85 runs',
      pitch_condition: 'Fresh Day 1-2 surface with good carry and seam movement.',
      weather_impact: 'Cool morning moisture favoring fast bowlers.',
      tactical_plan: 'Leave outside off-stump early; play under the eyes.',
    },
    second_innings: {
      predicted_performance: '35 to 60 runs',
      pitch_condition: 'Deteriorated Day 4-5 pitch with cracks, footmarks, and low bounce.',
      weather_impact: 'Dry, warm afternoon aiding reverse swing and sharp spin.',
      tactical_plan: 'Attack spin early; sweep and drive before low bounce takes over.',
    },
    pitch_deterioration_summary: 'Pitch transitions from seam-friendly on Days 1-2 to a dry, cracked turner by Days 4-5.',
    day_by_day_breakdown: [
      { days: 'Day 1-2', pitch_state: 'Hard & Seaming', key_factor: 'Seam & Bounce' },
      { days: 'Day 3', pitch_state: 'Settled & Flat', key_factor: 'True Pace & High Scoring' },
      { days: 'Day 4-5', pitch_state: 'Cracked & Dusty', key_factor: 'Variable Bounce & Sharp Spin' },
    ],
  };

  const inn1 = breakdown.first_innings || {};
  const inn2 = breakdown.second_innings || {};
  const dayList = breakdown.day_by_day_breakdown || [];

  return (
    <ErrorBoundary3D>
      <div style={{ marginBottom: 20 }}>
        {/* Header Banner */}
        <div style={{
          background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
          color: '#fff', padding: '14px 20px', borderRadius: '18px 18px 0 0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        }}>
          <div>
            <div style={{ fontSize: '1rem', fontWeight: 800 }}>⏳ Test Match Innings-by-Innings Analysis</div>
            <div style={{ fontSize: '0.78rem', color: '#c7d2fe', marginTop: 2 }}>
              Multi-Day Performance & Pitch Deterioration Forecast for <strong>{playerName || 'Player'}</strong>
            </div>
          </div>
          <div style={{
            background: 'rgba(255,255,255,0.15)', padding: '4px 12px', borderRadius: 20,
            fontSize: '0.75rem', fontWeight: 700, border: '1px solid rgba(255,255,255,0.2)',
          }}>
            5-DAY FORMAT
          </div>
        </div>

        {/* 3D Pitch Wear Canvas */}
        <div className="neo-raised" style={{
          borderRadius: 0, padding: 0, overflow: 'hidden', background: '#0f172a',
          borderLeft: '1px solid var(--neo-dark-shadow)', borderRight: '1px solid var(--neo-dark-shadow)',
        }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '8px 16px', background: 'rgba(15, 23, 42, 0.95)', borderBottom: '1px solid #1e293b',
          }}>
            <span style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              3D Pitch Wear & Weather Simulation
            </span>
            <div style={{ display: 'flex', gap: 6 }}>
              {[
                { id: 'day1', label: 'Day 1-2' },
                { id: 'day3', label: 'Day 3' },
                { id: 'day5', label: 'Day 4-5' },
              ].map(d => (
                <button
                  key={d.id}
                  onClick={() => setActiveDay(d.id)}
                  style={{
                    padding: '4px 10px', borderRadius: 8, border: 'none',
                    fontSize: '0.72rem', fontWeight: 700, cursor: 'pointer',
                    background: activeDay === d.id ? '#6366f1' : 'rgba(255,255,255,0.1)',
                    color: activeDay === d.id ? '#fff' : '#94a3b8',
                    transition: 'all 0.2s ease',
                  }}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ height: 260, background: 'linear-gradient(180deg, #0b0f19 0%, #1e293b 100%)' }}>
            <Canvas camera={{ position: [0, 5, 5], fov: 40 }}>
              <ambientLight intensity={0.7} />
              <directionalLight position={[5, 10, 5]} intensity={0.9} />
              <Suspense fallback={null}>
                <PitchWearScene activeDay={activeDay} />
              </Suspense>
              <OrbitControls enableZoom={false} enablePan={false} minPolarAngle={0.4} maxPolarAngle={1.2} />
            </Canvas>
          </div>
        </div>

        {/* 1st Innings vs 2nd Innings Side-by-Side Cards */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, padding: 16,
          background: 'var(--neo-bg)', borderRadius: '0 0 18px 18px',
          boxShadow: 'inset 2px 2px 5px var(--neo-inset-dark)',
        }}>
          {/* 1st Innings Card */}
          <div className="neo-raised panel-card" style={{ borderTop: '4px solid #3b82f6', margin: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#1d4ed8' }}>🏏 1st Innings Forecast</div>
              <span className="pill pill-blue" style={{ fontSize: '0.7rem' }}>Fresh Pitch</span>
            </div>

            <div className="result-box amber mb-3" style={{ padding: '10px 12px' }}>
              <div className="result-label">Predicted Range</div>
              <div className="result-value sm" style={{ color: '#d97706' }}>{inn1.predicted_performance || 'N/A'}</div>
            </div>

            <div style={{ fontSize: '0.78rem', display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div>
                <strong style={{ color: 'var(--text-dark)' }}>🌱 Pitch Behavior:</strong>
                <div style={{ color: 'var(--text-gray)', marginTop: 2 }}>{inn1.pitch_condition || 'N/A'}</div>
              </div>
              <div>
                <strong style={{ color: 'var(--text-dark)' }}>🌦️ Weather Impact:</strong>
                <div style={{ color: 'var(--text-gray)', marginTop: 2 }}>{inn1.weather_impact || 'N/A'}</div>
              </div>
              <div>
                <strong style={{ color: 'var(--text-dark)' }}>🎯 Tactical Approach:</strong>
                <div style={{ color: 'var(--text-gray)', marginTop: 2 }}>{inn1.tactical_plan || 'N/A'}</div>
              </div>
            </div>
          </div>

          {/* 2nd Innings Card */}
          <div className="neo-raised panel-card" style={{ borderTop: '4px solid #ef4444', margin: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#b91c1c' }}>🔥 2nd / 4th Innings Forecast</div>
              <span className="pill pill-red" style={{ fontSize: '0.7rem' }}>Deteriorated</span>
            </div>

            <div className="result-box red mb-3" style={{ padding: '10px 12px' }}>
              <div className="result-label">Predicted Range</div>
              <div className="result-value sm" style={{ color: '#dc2626' }}>{inn2.predicted_performance || 'N/A'}</div>
            </div>

            <div style={{ fontSize: '0.78rem', display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div>
                <strong style={{ color: 'var(--text-dark)' }}>🏜️ Pitch Deterioration:</strong>
                <div style={{ color: 'var(--text-gray)', marginTop: 2 }}>{inn2.pitch_condition || 'N/A'}</div>
              </div>
              <div>
                <strong style={{ color: 'var(--text-dark)' }}>☀️ Weather & Spin Impact:</strong>
                <div style={{ color: 'var(--text-gray)', marginTop: 2 }}>{inn2.weather_impact || 'N/A'}</div>
              </div>
              <div>
                <strong style={{ color: 'var(--text-dark)' }}>🛡️ Pressure & Chase Strategy:</strong>
                <div style={{ color: 'var(--text-gray)', marginTop: 2 }}>{inn2.tactical_plan || 'N/A'}</div>
              </div>
            </div>
          </div>
        </div>

        {/* 5-Day Pitch Wear Timeline */}
        {dayList.length > 0 && (
          <div className="neo-raised panel-card mt-3" style={{ padding: 14 }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-dark)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              🗓️ 5-Day Pitch Progression Timeline
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
              {dayList.map((item, idx) => (
                <div key={idx} style={{
                  background: 'rgba(255,255,255,0.6)', padding: '8px 12px', borderRadius: 10,
                  borderLeft: `4px solid ${idx === 0 ? '#3b82f6' : idx === 1 ? '#f59e0b' : '#ef4444'}`,
                  fontSize: '0.76rem',
                }}>
                  <div style={{ fontWeight: 800, color: 'var(--text-dark)' }}>{item.days}: {item.pitch_state}</div>
                  <div style={{ color: 'var(--text-gray)', fontSize: '0.7rem', marginTop: 2 }}>Key Factor: {item.key_factor}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary3D>
  );
}
