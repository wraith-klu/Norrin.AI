import React, { Suspense, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, Line } from '@react-three/drei';
import * as THREE from 'three';

function AnimatedBallPath({ isPlaying, deliveryType = 'outswing-pace' }) {
  const ballRef = useRef();
  const progressRef = useRef(0);

  const isSpin = deliveryType.includes('spin');
  const bounceZ = isSpin ? 1.0 : -0.5;
  const lateralMovement = isSpin ? 0.85 : -0.45;

  const points = [
    new THREE.Vector3(0, 2.4, -9),
    new THREE.Vector3(0.1, 1.2, -4.5),
    new THREE.Vector3(0.2, 0.08, bounceZ),
    new THREE.Vector3(0.2 + lateralMovement * 0.5, 0.5, bounceZ + 2),
    new THREE.Vector3(0.2 + lateralMovement, 0.9, 4.5),
  ];

  const curve = new THREE.CatmullRomCurve3(points);
  const curvePoints = curve.getPoints(50);

  useFrame((_, delta) => {
    if (isPlaying && ballRef.current) {
      progressRef.current = (progressRef.current + delta * 0.45) % 1;
      const point = curve.getPoint(progressRef.current);
      ballRef.current.position.set(point.x, point.y, point.z);
    }
  });

  return (
    <group>
      {/* 3D Ball Trajectory Line */}
      <Line
        points={curvePoints.map(p => [p.x, p.y, p.z])}
        color="#f59e0b"
        lineWidth={4}
      />

      {/* Animated Cricket Ball */}
      <mesh ref={ballRef} position={[0, 2.4, -9]}>
        <sphereGeometry args={[0.22, 32, 32]} />
        <meshStandardMaterial color="#dc2626" roughness={0.3} metalness={0.2} />
      </mesh>

      {/* Pitch Bounce Ring + TV Label */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0.2, 0.02, bounceZ]}>
        <ringGeometry args={[0.35, 0.55, 32]} />
        <meshBasicMaterial color="#ef4444" side={THREE.DoubleSide} transparent opacity={0.8} />
      </mesh>
      <Html position={[0.2, 0.7, bounceZ]} center distanceFactor={15}>
        <div style={{ background: 'rgba(239,68,68,0.95)', color: '#fff', padding: '3px 8px', borderRadius: 6, fontSize: '0.72rem', fontWeight: 800, whiteSpace: 'nowrap' }}>
          🎯 PITCH SPOT (5.6m GOOD LENGTH)
        </div>
      </Html>
    </group>
  );
}

export function DeliveryTrajectory3D({ batsmanPrediction }) {
  const [isPlaying, setIsPlaying] = useState(true);
  const [deliveryType, setDeliveryType] = useState('outswing-pace');

  const dismissal = batsmanPrediction?.possible_mode_of_dismissal || 'LBW to in-dipper';
  const threatBowler = batsmanPrediction?.who_can_get_him_out || 'Pace / Seam bowler';

  return (
    <div className="neo-raised panel-card" style={{ padding: 0, overflow: 'hidden', position: 'relative', borderRadius: 16 }}>
      {/* TV Graphic Banner */}
      <div
        style={{
          position: 'absolute',
          top: 16,
          left: 16,
          zIndex: 10,
          background: 'linear-gradient(90deg, #1e1b4b 0%, #0f172a 100%)',
          borderLeft: '4px solid #f59e0b',
          padding: '8px 16px',
          borderRadius: '0 10px 10px 0',
          boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
        }}
      >
        <div style={{ color: '#fbbf24', fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          HAWK-EYE 3D BALL TRACKING TELECAST
        </div>
        <div style={{ color: '#ffffff', fontSize: '0.9rem', fontWeight: 700 }}>
          🎥 Delivery Flight &amp; Seam Replay
        </div>
      </div>

      {/* Right Telecast Controls */}
      <div style={{ position: 'absolute', top: 16, right: 16, zIndex: 10, display: 'flex', gap: 8 }}>
        <button
          className="btn btn-slate btn-sm"
          onClick={() => setDeliveryType(t => (t === 'outswing-pace' ? 'off-spin-break' : 'outswing-pace'))}
          style={{ fontSize: '0.75rem', padding: '6px 12px', background: 'rgba(15, 23, 42, 0.9)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)' }}
        >
          🔄 {deliveryType === 'outswing-pace' ? 'Pace Seam' : 'Spin Break'}
        </button>
        <button
          className="btn btn-purple btn-sm"
          onClick={() => setIsPlaying(!isPlaying)}
          style={{ fontSize: '0.75rem', padding: '6px 12px' }}
        >
          {isPlaying ? '⏸ Pause Replay' : '▶ Play Replay'}
        </button>
      </div>

      <div style={{ width: '100%', height: 420, background: 'radial-gradient(circle at 50% 50%, #0b0f19 0%, #02040a 100%)' }}>
        <Canvas camera={{ position: [8, 6, 4], fov: 45 }}>
          <ambientLight intensity={0.8} />
          <directionalLight position={[10, 15, 10]} intensity={1.3} />

          {/* 3D Pitch Strip */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]}>
            <planeGeometry args={[2.4, 15]} />
            <meshStandardMaterial color="#854d0e" roughness={0.8} />
          </mesh>

          {/* Stumps & Creases */}
          {[-6.5, 4.5].map((zPos, sIdx) => (
            <group key={sIdx} position={[0, 0, zPos]}>
              <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
                <planeGeometry args={[2.6, 0.1]} />
                <meshBasicMaterial color="#ffffff" />
              </mesh>
              {[-0.2, 0, 0.2].map((x, i) => (
                <mesh key={i} position={[x, 0.4, 0]}>
                  <cylinderGeometry args={[0.03, 0.03, 0.8, 16]} />
                  <meshStandardMaterial color="#fef08a" />
                </mesh>
              ))}
            </group>
          ))}

          {/* Pitch Ends Labels */}
          <Html position={[0, 0.2, -7.2]} center distanceFactor={15}>
            <div style={{ background: 'rgba(255,255,255,0.95)', color: '#0f172a', padding: '3px 8px', borderRadius: 4, fontSize: '0.72rem', fontWeight: 800, whiteSpace: 'nowrap' }}>
              BOWLER'S END (CITY END)
            </div>
          </Html>
          <Html position={[0, 0.2, 5.2]} center distanceFactor={15}>
            <div style={{ background: 'rgba(255,255,255,0.95)', color: '#0f172a', padding: '3px 8px', borderRadius: 4, fontSize: '0.72rem', fontWeight: 800, whiteSpace: 'nowrap' }}>
              STRIKER'S END (PAVILION END)
            </div>
          </Html>

          <Suspense fallback={null}>
            <AnimatedBallPath isPlaying={isPlaying} deliveryType={deliveryType} />
          </Suspense>

          <OrbitControls enablePan={true} enableZoom={true} />
        </Canvas>
      </div>

      {/* Bottom TV Telecast Stat Card */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 10, padding: '12px 18px', background: '#0b0f19', borderTop: '1px solid rgba(255,255,255,0.1)', fontSize: '0.78rem' }}>
        <div>
          <span style={{ color: '#94a3b8' }}>Release Speed:</span>
          <div style={{ color: '#38bdf8', fontWeight: 800 }}>142.5 km/h</div>
        </div>
        <div>
          <span style={{ color: '#94a3b8' }}>Seam Movement:</span>
          <div style={{ color: '#f59e0b', fontWeight: 800 }}>1.8° {deliveryType === 'outswing-pace' ? 'Outswing' : 'Off-Break'}</div>
        </div>
        <div>
          <span style={{ color: '#94a3b8' }}>Threat Bowler:</span>
          <div style={{ color: '#ffffff', fontWeight: 800 }}>{threatBowler}</div>
        </div>
        <div>
          <span style={{ color: '#94a3b8' }}>Dismissal Threat:</span>
          <div style={{ color: '#ef4444', fontWeight: 800 }}>{dismissal}</div>
        </div>
      </div>
    </div>
  );
}

export default DeliveryTrajectory3D;
