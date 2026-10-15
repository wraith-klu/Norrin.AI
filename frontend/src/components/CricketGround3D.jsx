import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html, Float } from '@react-three/drei';
import * as THREE from 'three';

class ErrorBoundary3D extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error) {
    console.warn('3D Canvas fallback triggered:', error);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="neo-raised panel-card" style={{ padding: 24, textAlign: 'center', color: 'var(--text-gray)' }}>
          <div>🏟️ 3D WebGL Canvas unavailable on this browser/device.</div>
          <div style={{ fontSize: '0.8rem', marginTop: 4 }}>Showing 2D ground representation.</div>
        </div>
      );
    }
    return this.props.children;
  }
}

function GroundMesh({ straightBoundary = 80, squareBoundary = 75 }) {
  const rX = (squareBoundary / 80) * 12;
  const rZ = (straightBoundary / 80) * 15;
  const scaleX = rZ > 0 ? rX / rZ : 1;

  return (
    <group>
      {/* Outer Outfield Grass Oval */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]} scale={[scaleX, 1, 1]}>
        <circleGeometry args={[rZ, 64]} />
        <meshStandardMaterial color="#14532d" roughness={0.7} metalness={0.1} />
      </mesh>

      {/* Inner Ring (30-Yard Circle) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.04, 0]} scale={[scaleX, 1, 1]}>
        <ringGeometry args={[rZ * 0.48, rZ * 0.50, 64]} />
        <meshBasicMaterial color="#40916c" side={THREE.DoubleSide} transparent opacity={0.6} />
      </mesh>

      {/* Boundary Rope / Ring */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} scale={[scaleX, 1, 1]}>
        <ringGeometry args={[rZ * 0.98, rZ * 1.01, 64]} />
        <meshStandardMaterial color="#ffb703" emissive="#fb8500" emissiveIntensity={0.5} />
      </mesh>

      {/* Pitch Strip */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[1.6, 5.2]} />
        <meshStandardMaterial color="#d4a373" roughness={0.9} />
      </mesh>

      {/* Crease Lines */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, 1.9]}>
        <planeGeometry args={[1.8, 0.08]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, -1.9]}>
        <planeGeometry args={[1.8, 0.08]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>

      {/* Stumps (North & South Ends) */}
      {[-1.9, 1.9].map((zPos, sIdx) => (
        <group key={sIdx} position={[0, 0, zPos]}>
          {[-0.2, 0, 0.2].map((xOffset, idx) => (
            <mesh key={idx} position={[xOffset, 0.35, 0]}>
              <cylinderGeometry args={[0.02, 0.02, 0.7, 12]} />
              <meshStandardMaterial color="#fff3b0" roughness={0.3} />
            </mesh>
          ))}
          {/* Bails */}
          <mesh position={[0, 0.71, 0]}>
            <boxGeometry args={[0.45, 0.02, 0.03]} />
            <meshStandardMaterial color="#ffb703" />
          </mesh>
        </group>
      ))}

      {/* Non-overlapping TV Sector Labels */}
      <Html position={[0, 0.2, -rZ - 0.8]} center distanceFactor={15}>
        <div style={{ background: 'rgba(15,23,42,0.9)', border: '1px solid #a855f7', color: '#e9d5ff', padding: '3px 8px', borderRadius: 6, fontSize: '0.72rem', fontWeight: 800, whiteSpace: 'nowrap' }}>
          NORTH STAND (LONG OFF / ON)
        </div>
      </Html>
      <Html position={[0, 0.2, rZ + 0.8]} center distanceFactor={15}>
        <div style={{ background: 'rgba(15,23,42,0.9)', border: '1px solid #a855f7', color: '#e9d5ff', padding: '3px 8px', borderRadius: 6, fontSize: '0.72rem', fontWeight: 800, whiteSpace: 'nowrap' }}>
          SOUTH STAND (THIRD MAN / FINE LEG)
        </div>
      </Html>
      <Html position={[rX + 0.8, 0.2, 0]} center distanceFactor={15}>
        <div style={{ background: 'rgba(15,23,42,0.9)', border: '1px solid #a855f7', color: '#e9d5ff', padding: '3px 8px', borderRadius: 6, fontSize: '0.72rem', fontWeight: 800, whiteSpace: 'nowrap' }}>
          EAST STAND (POINT / COVER)
        </div>
      </Html>
      <Html position={[-rX - 0.8, 0.2, 0]} center distanceFactor={15}>
        <div style={{ background: 'rgba(15,23,42,0.9)', border: '1px solid #a855f7', color: '#e9d5ff', padding: '3px 8px', borderRadius: 6, fontSize: '0.72rem', fontWeight: 800, whiteSpace: 'nowrap' }}>
          WEST STAND (MID WICKET / SQUARE LEG)
        </div>
      </Html>
    </group>
  );
}

function ThreatZones3D({ strengths = [], weaknesses = [] }) {
  const zoneCoords = {
    'off-spin': { pos: [4, 0.3, -2], label: 'Off-Spin Zone', color: '#ef4444' },
    'leg-spin': { pos: [-4, 0.3, -2], label: 'Leg-Spin Zone', color: '#10b981' },
    'left-arm pacer': { pos: [3, 0.3, 4], label: 'Left Arm Angle', color: '#f59e0b' },
    'right-arm pacer': { pos: [-3, 0.3, 4], label: 'Right Arm Pace', color: '#3b82f6' },
    'short (bouncer)': { pos: [0, 0.3, -3.5], label: 'Bouncer Zone', color: '#dc2626' },
    'full (yorker)': { pos: [0, 0.3, 1.2], label: 'Yorker Spot', color: '#8b5cf6' },
  };

  const activeWeak = weaknesses.map(w => w.toLowerCase());
  const activeStr = strengths.map(s => s.toLowerCase());

  return (
    <group>
      {Object.entries(zoneCoords).map(([key, info], i) => {
        const isWeak = activeWeak.some(w => w.includes(key) || key.includes(w));
        const isStrong = activeStr.some(s => s.includes(key) || key.includes(s));
        const color = isWeak ? '#ef4444' : isStrong ? '#10b981' : info.color;
        const scale = isWeak ? 1.3 : isStrong ? 1.1 : 0.9;

        return (
          <Float key={i} speed={2} rotationIntensity={0.2} floatIntensity={0.5}>
            <group position={info.pos}>
              {/* Pulsing Zone Sphere */}
              <mesh scale={[scale, scale, scale]}>
                <sphereGeometry args={[0.5, 32, 32]} />
                <meshStandardMaterial
                  color={color}
                  emissive={color}
                  emissiveIntensity={0.7}
                  roughness={0.2}
                  transparent
                  opacity={0.85}
                />
              </mesh>

              {/* TV Sector Badge Overlay */}
              <Html position={[0, 0.8, 0]} center distanceFactor={15}>
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.95)',
                    border: `1.5px solid ${color}`,
                    color: '#ffffff',
                    padding: '3px 8px',
                    borderRadius: 6,
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    whiteSpace: 'nowrap',
                    boxShadow: `0 0 10px ${color}80`,
                    pointerEvents: 'none',
                  }}
                >
                  {info.label.toUpperCase()} {isWeak ? '⚠️ WEAK' : isStrong ? '💪 STRENGTH' : ''}
                </div>
              </Html>
            </group>
          </Float>
        );
      })}
    </group>
  );
}

export function CricketGround3D({ batsmanPrediction, groundDimensions = {} }) {
  const strengths = batsmanPrediction?.bowling_strength || [];
  const weaknesses = batsmanPrediction?.bowling_weakness || [];
  const straightBoundary = groundDimensions.straight_boundary_m || 83;
  const squareBoundary = groundDimensions.square_boundary_m || 80;

  return (
    <ErrorBoundary3D>
      <div className="neo-raised panel-card" style={{ padding: 0, overflow: 'hidden', position: 'relative', borderRadius: 16 }}>
        {/* TV Broadcast Banner */}
        <div
          style={{
            position: 'absolute',
            top: 16,
            left: 16,
            zIndex: 10,
            background: 'linear-gradient(90deg, #14532d 0%, #0f172a 100%)',
            borderLeft: '4px solid #10b981',
            padding: '8px 16px',
            borderRadius: '0 10px 10px 0',
            boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
          }}
        >
          <div style={{ color: '#6ee7b7', fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            3D STADIUM TELECAST GRAPHICS
          </div>
          <div style={{ color: '#ffffff', fontSize: '0.9rem', fontWeight: 700 }}>
            🏟️ Field Sector &amp; Threat Radar
          </div>
        </div>

        <div style={{ width: '100%', height: 440, background: 'radial-gradient(circle at 50% 50%, #0b0f19 0%, #02040a 100%)' }}>
          <Canvas camera={{ position: [0, 18, 22], fov: 45 }}>
            <ambientLight intensity={0.8} />
            <directionalLight position={[10, 25, 15]} intensity={1.3} castShadow />
            <pointLight position={[-10, 15, -10]} intensity={0.5} color="#a855f7" />

            <Suspense fallback={null}>
              <GroundMesh straightBoundary={straightBoundary} squareBoundary={squareBoundary} />
              <ThreatZones3D strengths={strengths} weaknesses={weaknesses} />
            </Suspense>

            <OrbitControls
              enablePan={true}
              enableZoom={true}
              minDistance={10}
              maxDistance={40}
              maxPolarAngle={Math.PI / 2 - 0.05}
            />
          </Canvas>
        </div>

        {/* Legend strip */}
        <div style={{ display: 'flex', gap: 20, padding: '12px 18px', background: '#0b0f19', borderTop: '1px solid rgba(255,255,255,0.1)', fontSize: '0.78rem', fontWeight: 700 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#ef4444' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444', display: 'inline-block' }} />
            Vulnerability Zone (Weakness)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#10b981' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
            Dominance Zone (Strength)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#fb8500' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#fb8500', display: 'inline-block' }} />
            Perimeter ({straightBoundary}m × {squareBoundary}m)
          </div>
        </div>
      </div>
    </ErrorBoundary3D>
  );
}

export default CricketGround3D;
