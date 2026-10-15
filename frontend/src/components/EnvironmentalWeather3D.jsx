import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

function WindVectors3D({ windKmh = 14 }) {
  const arrows = [
    { pos: [-4, 2, -3], rot: [0, 0, -Math.PI / 6] },
    { pos: [-1, 3.2, 0], rot: [0, 0, -Math.PI / 6] },
    { pos: [3, 2.5, 2], rot: [0, 0, -Math.PI / 6] },
    { pos: [-2, 1.8, 3], rot: [0, 0, -Math.PI / 6] },
    { pos: [4, 3.5, -2], rot: [0, 0, -Math.PI / 6] },
  ];

  return (
    <group>
      {arrows.map((a, idx) => (
        <group key={idx} position={a.pos} rotation={a.rot}>
          <mesh position={[0, 0, 0]} rotation={[0, 0, -Math.PI / 2]}>
            <cylinderGeometry args={[0.04, 0.04, 2, 12]} />
            <meshStandardMaterial color="#38bdf8" emissive="#0284c7" emissiveIntensity={0.6} />
          </mesh>
          <mesh position={[1, 0, 0]} rotation={[0, 0, -Math.PI / 2]}>
            <coneGeometry args={[0.2, 0.5, 16]} />
            <meshStandardMaterial color="#38bdf8" emissive="#0284c7" />
          </mesh>
        </group>
      ))}
    </group>
  );
}

function TemperaturePillar3D({ temp = 28 }) {
  const height = (temp / 40) * 4;
  return (
    <group position={[-5.5, 0, 0]}>
      {/* Outer Glass Tube */}
      <mesh position={[0, 2, 0]}>
        <cylinderGeometry args={[0.3, 0.3, 4.2, 24]} />
        <meshStandardMaterial color="#ffffff" transparent opacity={0.25} roughness={0.1} />
      </mesh>

      {/* Mercury Pillar */}
      <mesh position={[0, height / 2, 0]}>
        <cylinderGeometry args={[0.2, 0.2, height, 24]} />
        <meshStandardMaterial color="#f43f5e" emissive="#e11d48" emissiveIntensity={0.8} />
      </mesh>
    </group>
  );
}

export function EnvironmentalWeather3D({ environmentalConditions = {} }) {
  const dayTemp = environmentalConditions.day_temp_c ?? 28;
  const nightTemp = environmentalConditions.night_temp_c ?? 22;
  const humidity = environmentalConditions.humidity_pct ?? 78;
  const windKmh = environmentalConditions.wind_speed_kmh ?? 14;
  const dewFactor = environmentalConditions.dew_factor ?? 0.65;
  const isDayNight = environmentalConditions.is_day_night ?? true;

  return (
    <div className="neo-raised panel-card" style={{ padding: 0, overflow: 'hidden', borderRadius: 16 }}>
      {/* TV Graphic Banner */}
      <div
        style={{
          background: 'linear-gradient(90deg, #0c4a6e 0%, #0f172a 100%)',
          borderLeft: '4px solid #38bdf8',
          padding: '10px 18px',
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ color: '#7dd3fc', fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            ATMOSPHERIC &amp; GROUND TELECAST GRAPHICS
          </div>
          <div style={{ color: '#ffffff', fontSize: '0.95rem', fontWeight: 700 }}>
            🌦️ Weather, Wind Vectors &amp; Dew Matrix
          </div>
        </div>
        <div style={{ background: 'rgba(0,0,0,0.4)', padding: '4px 10px', borderRadius: 6, color: '#bae6fd', fontSize: '0.75rem', fontWeight: 700 }}>
          TV GRAPHICS MODE
        </div>
      </div>

      {/* 2-Column Split Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', background: '#0b0f19' }}>
        {/* Left Column: 3D Weather Scene */}
        <div style={{ height: 380, position: 'relative', borderRight: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 10, color: '#94a3b8', fontSize: '0.72rem', fontWeight: 600 }}>
            🎮 Drag to rotate 3D view
          </div>

          <Canvas camera={{ position: [0, 7, 12], fov: 45 }}>
            <ambientLight intensity={0.8} />
            <directionalLight position={[10, 15, 10]} intensity={1.2} />

            {/* Grass Ground */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]}>
              <planeGeometry args={[16, 12]} />
              <meshStandardMaterial color="#14532d" roughness={0.5} />
            </mesh>

            <Suspense fallback={null}>
              <TemperaturePillar3D temp={dayTemp} />
              <WindVectors3D windKmh={windKmh} />

              {/* Dew Layer Ring */}
              <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.03, 0]}>
                <ringGeometry args={[1, 5.5, 64]} />
                <meshStandardMaterial
                  color="#06b6d4"
                  emissive="#0891b2"
                  emissiveIntensity={dewFactor}
                  transparent
                  opacity={0.4 + dewFactor * 0.4}
                />
              </mesh>
            </Suspense>

            <OrbitControls enablePan={true} enableZoom={true} maxPolarAngle={Math.PI / 2 - 0.05} />
          </Canvas>
        </div>

        {/* Right Column: TV Telecast Weather Stat Table */}
        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 12 }}>
          <div style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            ENVIRONMENTAL TELEMETRY DATA
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.6)', borderLeft: '4px solid #f43f5e', borderRadius: 8, padding: '10px 14px' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700 }}>AIR TEMPERATURE</div>
            <div style={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 800 }}>{dayTemp}°C (Day) / {nightTemp}°C (Night)</div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.6)', borderLeft: '4px solid #38bdf8', borderRadius: 8, padding: '10px 14px' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700 }}>WIND VELOCITY &amp; DIRECTION</div>
            <div style={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 800 }}>{windKmh} km/h (SW to NE Cross-Wind)</div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.6)', borderLeft: '4px solid #06b6d4', borderRadius: 8, padding: '10px 14px' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700 }}>OUTFIELD DEW FACTOR</div>
            <div style={{ color: '#06b6d4', fontSize: '1.1rem', fontWeight: 800 }}>{(dewFactor * 100).toFixed(0)}% Moisture Level</div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.6)', borderLeft: '4px solid #f59e0b', borderRadius: 8, padding: '10px 14px' }}>
            <div style={{ color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700 }}>MATCH SCHEDULE &amp; HUMIDITY</div>
            <div style={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 800 }}>{isDayNight ? 'Day / Night Match' : 'Day Only'} · {humidity}% Humidity</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EnvironmentalWeather3D;
