import React, { useState } from 'react';

const RAW_API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const API_BASE = RAW_API_BASE.replace(/\/+$/, '');

export function PlayerCompare({ popularPlayers = [], popularTeams = [], popularVenues = [], models = [] }) {
  const [playerA, setPlayerA] = useState('Virat Kohli');
  const [playerB, setPlayerB] = useState('Babar Azam');
  const [opp, setOpp] = useState('Australia');
  const [venue, setVenue] = useState('Melbourne Cricket Ground (MCG)');
  const [format, setFormat] = useState('ODI');
  const [model, setModel] = useState(models[0]?.id || 'gemini-3.6-flash');

  const [loading, setLoading] = useState(false);
  const [resA, setResA] = useState(null);
  const [resB, setResB] = useState(null);
  const [err, setErr] = useState('');

  const runComparison = async () => {
    setLoading(true);
    setErr('');
    setResA(null);
    setResB(null);

    const payloadA = { player_name: playerA, opposition: opp, venue, match_format: format, model };
    const payloadB = { player_name: playerB, opposition: opp, venue, match_format: format, model };

    try {
      const [rA, rB] = await Promise.all([
        fetch(`${API_BASE}/v1/cricket/predict-manual`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payloadA),
        }),
        fetch(`${API_BASE}/v1/cricket/predict-manual`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payloadB),
        }),
      ]);

      if (!rA.ok || !rB.ok) {
        throw new Error('Comparison prediction failed for one or both players.');
      }

      const dataA = await rA.json();
      const dataB = await rB.json();

      setResA(dataA);
      setResB(dataB);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="gap-col">
      {/* Input panel */}
      <div className="neo-raised panel-card">
        <div className="panel-title">⚔️ Head-to-Head Player Comparison</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          {/* Player A */}
          <div className="field-group">
            <span className="field-label">Player 1</span>
            <div className="neo-inset">
              <input
                className="neo-input"
                value={playerA}
                onChange={e => setPlayerA(e.target.value)}
                placeholder="e.g. Virat Kohli"
                list="popular-players-list"
              />
            </div>
          </div>

          {/* Player B */}
          <div className="field-group">
            <span className="field-label">Player 2</span>
            <div className="neo-inset">
              <input
                className="neo-input"
                value={playerB}
                onChange={e => setPlayerB(e.target.value)}
                placeholder="e.g. Babar Azam"
                list="popular-players-list"
              />
            </div>
          </div>
        </div>

        {/* Shared Match Conditions */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div className="field-group">
            <span className="field-label">Opposition</span>
            <div className="neo-inset">
              <input className="neo-input" value={opp} onChange={e => setOpp(e.target.value)} list="popular-teams-list" />
            </div>
          </div>

          <div className="field-group">
            <span className="field-label">Venue</span>
            <div className="neo-inset">
              <input className="neo-input" value={venue} onChange={e => setVenue(e.target.value)} list="popular-venues-list" />
            </div>
          </div>

          <div className="field-group">
            <span className="field-label">Format</span>
            <div className="neo-inset">
              <select className="neo-input" value={format} onChange={e => setFormat(e.target.value)}>
                <option value="T20">T20</option>
                <option value="ODI">ODI</option>
                <option value="Test">Test</option>
              </select>
            </div>
          </div>
        </div>

        <button className="btn btn-purple" onClick={runComparison} disabled={loading} style={{ width: '100%' }}>
          {loading ? '⏳ Analysing Both Players...' : '⚔️ Compare Players Head-to-Head'}
        </button>

        {err && <div className="info-strip red mt-3">⚠️ {err}</div>}
      </div>

      {/* Comparison Results */}
      {resA && resB && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Card Player A */}
          <div className="neo-raised panel-card">
            <div className="section-head" style={{ color: 'var(--color-purple)' }}>👤 {resA.player_name || playerA}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-gray)', marginBottom: 12 }}>"{resA.visual_tagline || 'N/A'}"</div>
            
            <div className="result-grid mb-3">
              <div className="result-box amber">
                <div className="result-label">Predicted Runs</div>
                <div className="result-value sm">{resA.batsman_prediction?.predicted_runs_range || 'N/A'}</div>
              </div>
              <div className="result-box red">
                <div className="result-label">Dismissal Threat</div>
                <div className="result-value sm">{resA.batsman_prediction?.possible_mode_of_dismissal || 'N/A'}</div>
              </div>
            </div>

            <div style={{ fontSize: '0.78rem', marginBottom: 8 }}>
              <strong>Key Strengths:</strong>
              <div className="pill-row mt-1">
                {(resA.batsman_prediction?.bowling_strength || []).map((s, i) => (
                  <span key={i} className="pill pill-green">{s}</span>
                ))}
              </div>
            </div>

            <div style={{ fontSize: '0.78rem' }}>
              <strong>Weaknesses:</strong>
              <div className="pill-row mt-1">
                {(resA.batsman_prediction?.bowling_weakness || []).map((w, i) => (
                  <span key={i} className="pill pill-red">{w}</span>
                ))}
              </div>
            </div>

            {(resA.batsman_prediction?.venue_performance_history || []).length > 0 && (
              <div style={{ marginTop: 12 }}>
                <strong style={{ fontSize: '0.78rem' }}>🏟️ Venue Record:</strong>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 6 }}>
                  {resA.batsman_prediction.venue_performance_history.slice(0, 5).map((e, i) => (
                    <div key={i} style={{ fontSize: '0.76rem', padding: '4px 8px', borderRadius: 6, background: 'rgba(124,58,237,0.06)', fontWeight: 600 }}>
                      {i + 1}. {e}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Card Player B */}
          <div className="neo-raised panel-card">
            <div className="section-head" style={{ color: 'var(--color-teal)' }}>👤 {resB.player_name || playerB}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-gray)', marginBottom: 12 }}>"{resB.visual_tagline || 'N/A'}"</div>

            <div className="result-grid mb-3">
              <div className="result-box amber">
                <div className="result-label">Predicted Runs</div>
                <div className="result-value sm">{resB.batsman_prediction?.predicted_runs_range || 'N/A'}</div>
              </div>
              <div className="result-box red">
                <div className="result-label">Dismissal Threat</div>
                <div className="result-value sm">{resB.batsman_prediction?.possible_mode_of_dismissal || 'N/A'}</div>
              </div>
            </div>

            <div style={{ fontSize: '0.78rem', marginBottom: 8 }}>
              <strong>Key Strengths:</strong>
              <div className="pill-row mt-1">
                {(resB.batsman_prediction?.bowling_strength || []).map((s, i) => (
                  <span key={i} className="pill pill-green">{s}</span>
                ))}
              </div>
            </div>

            <div style={{ fontSize: '0.78rem' }}>
              <strong>Weaknesses:</strong>
              <div className="pill-row mt-1">
                {(resB.batsman_prediction?.bowling_weakness || []).map((w, i) => (
                  <span key={i} className="pill pill-red">{w}</span>
                ))}
              </div>
            </div>

            {(resB.batsman_prediction?.venue_performance_history || []).length > 0 && (
              <div style={{ marginTop: 12 }}>
                <strong style={{ fontSize: '0.78rem' }}>🏟️ Venue Record:</strong>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 6 }}>
                  {resB.batsman_prediction.venue_performance_history.slice(0, 5).map((e, i) => (
                    <div key={i} style={{ fontSize: '0.76rem', padding: '4px 8px', borderRadius: 6, background: 'rgba(13,148,136,0.06)', fontWeight: 600 }}>
                      {i + 1}. {e}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default PlayerCompare;
