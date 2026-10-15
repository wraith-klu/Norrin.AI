import React, { useState } from 'react';
import './index.css';
import './App.css';
import { CricketGround3D } from './components/CricketGround3D';
import { WagonWheel3D } from './components/WagonWheel3D';
import { DeliveryHeatmap3D } from './components/DeliveryHeatmap3D';
import { VulnerabilityGlobe3D } from './components/VulnerabilityGlobe3D';
import { PlayerCompare } from './components/PlayerCompare';
import { DeliveryTrajectory3D } from './components/DeliveryTrajectory3D';
import { EnvironmentalWeather3D } from './components/EnvironmentalWeather3D';
import { ImpactMatrix3D } from './components/ImpactMatrix3D';
import { BowlingPitchMap3D } from './components/BowlingPitchMap3D';
import { BowlerSpeedGauge3D } from './components/BowlerSpeedGauge3D';
import { TestInningsBreakdown3D } from './components/TestInningsBreakdown3D';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/* ── Error Boundary: prevents white screen on render crash ─── */
class ResultErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error('ResultErrorBoundary caught:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="neo-raised panel-card" style={{ padding: 24, textAlign: 'center' }}>
          <div style={{ fontSize: '1.4rem', marginBottom: 8 }}>⚠️ Rendering Error</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-gray)', marginBottom: 12 }}>
            Something went wrong while displaying the prediction results.
          </div>
          <div style={{ fontSize: '0.75rem', color: '#ef4444', fontFamily: 'monospace', background: '#fef2f2', padding: 12, borderRadius: 8, textAlign: 'left', wordBreak: 'break-all' }}>
            {this.state.error?.message || 'Unknown error'}
          </div>
          <button
            className="btn btn-purple"
            style={{ marginTop: 16 }}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            🔄 Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const POPULAR_PLAYERS = [
  'Virat Kohli',
  'Rohit Sharma',
  'Babar Azam',
  'Shubman Gill',
  'Travis Head',
  'Suryakumar Yadav',
  'Jos Buttler',
  'Steve Smith',
  'Kane Williamson',
  'Joe Root',
  'Glenn Maxwell',
  'Heinrich Klaasen',
  'Yashasvi Jaiswal',
  'Rishabh Pant',
  'Hardik Pandya',
  'Ravindra Jadeja',
  'Jasprit Bumrah',
  'Mitchell Starc',
  'Rashid Khan',
  'Shaheen Afridi'
];

const POPULAR_TEAMS = [
  'India',
  'Australia',
  'England',
  'Pakistan',
  'South Africa',
  'New Zealand',
  'West Indies',
  'Sri Lanka',
  'Bangladesh',
  'Afghanistan',
  'Ireland',
  'Zimbabwe'
];

const POPULAR_VENUES = [
  "Wankhede Stadium, Mumbai",
  "Eden Gardens, Kolkata",
  "Melbourne Cricket Ground (MCG)",
  "Lord's Cricket Ground, London",
  "Narendra Modi Stadium, Ahmedabad",
  "M. Chinnaswamy Stadium, Bengaluru",
  "MA Chidambaram Stadium, Chennai",
  "Adelaide Oval, Adelaide",
  "Sydney Cricket Ground (SCG)",
  "HPCA Stadium, Dharamshala",
  "Rajiv Gandhi Stadium, Hyderabad",
  "Trent Bridge, Nottingham",
  "Arun Jaitley Stadium, Delhi",
  "Kingsmead, Durban",
  "Sheikh Zayed Stadium, Abu Dhabi",
  "Sabina Park, Kingston",
  "Eden Park, Auckland",
  "County Ground, Bristol"
];

const OFFLINE_VENUE_IDS = [
  'wankhede',
  'eden_gardens',
  'mcg',
  'lords',
  'narendra_modi',
  'chinnaswamy',
  'chepauk',
  'adelaide_oval',
  'scg',
  'dharamshala',
  'hyderabad',
  'trent_bridge',
  'arun_jaitley',
  'kingsmead',
  'abu_dhabi',
  'sabina_park',
  'eden_park',
  'bristol'
];


const MODELS = [
  { id: 'gemini-3.6-flash', label: '⭐ Google Gemini 3.6 Flash (Primary)' },
  { id: 'poolside/laguna-s-2.1:free', label: '✅ Poolside Laguna S-2.1 (Free)' },
  { id: 'poolside/laguna-xs-2.1:free', label: '✅ Poolside Laguna XS-2.1 (Free)' },
  { id: 'nvidia/nemotron-3-ultra-550b-a55b:free', label: '✅ NVIDIA Nemotron 3 Ultra (Free)' },
  { id: 'inclusionai/ling-3.0-flash:free', label: '✅ InclusionAI Ling 3.0 Flash (Free)' },
  { id: 'google/gemma-4-31b-it:free', label: '✅ Google Gemma 4 31B (Free)' },
  { id: 'cohere/north-mini-code:free', label: '✅ Cohere North Mini-Code (Free)' },
  { id: 'google/gemini-2.5-flash', label: '⚡ Gemini 2.5 Flash' },
  { id: 'google/gemini-2.5-pro', label: '⚡ Gemini 2.5 Pro' },
  { id: 'openai/gpt-4o-mini', label: '⚡ GPT-4o Mini' },
  { id: 'openai/gpt-4o', label: '⚡ GPT-4o' },
];

/* ─── Small SVG Icons ─────────────────────────────────────── */
const UserIcon = () => (
  <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="4" /><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
  </svg>
);
const TrendIcon = () => (
  <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" /><polyline points="17 6 23 6 23 12" />
  </svg>
);
const SpinnerIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="16" height="16" className="spin">
    <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
    <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
  </svg>
);
const ChevronRight = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

/* ─── Radar SVG ────────────────────────────────────────────── */
function RadarChart({ data }) {
  if (!data || data.length === 0) return null;
  const n = data.length;
  const cx = 170, cy = 170, r = 120;

  /* point positions */
  const pts = data.map((d, i) => {
    const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
    const rv = (d.score / 5) * r;
    const lDist = r + 32;
    return {
      x: cx + rv * Math.cos(angle),
      y: cy + rv * Math.sin(angle),
      lx: cx + lDist * Math.cos(angle),
      ly: cy + lDist * Math.sin(angle),
      ax: cx + (r + 2) * Math.cos(angle),
      ay: cy + (r + 2) * Math.sin(angle),
      score: d.score,
      label: d.type,
      angle,
    };
  });

  const polygon = pts.map(p => `${p.x},${p.y}`).join(' ');
  const dotColor = (s) => s === 5 ? '#10b981' : s === 1 ? '#ef4444' : '#7c3aed';

  const splitLabel = (lbl) => {
    const words = lbl.split(' ');
    if (words.length <= 2) return [lbl, ''];
    const mid = Math.ceil(words.length / 2);
    return [words.slice(0, mid).join(' '), words.slice(mid).join(' ')];
  };

  const ringLevels = [1, 2, 3, 4, 5];

  return (
    <svg width="100%" viewBox="0 0 340 340" style={{ maxWidth: 340 }}>

      {/* Grid rings */}
      {ringLevels.map(lvl => (
        <circle key={lvl} cx={cx} cy={cy} r={(lvl / 5) * r}
          fill="none"
          stroke={lvl === 5 ? '#cbd5e1' : '#e2e8f0'}
          strokeWidth={lvl === 5 ? 1.5 : 0.8}
          strokeDasharray={lvl < 5 ? '3 3' : undefined}
        />
      ))}

      {/* Ring level numbers */}
      {ringLevels.map(lvl => (
        <text key={lvl} x={cx + (lvl / 5) * r + 4} y={cy + 4}
          fontSize="8" fontWeight="700" fill="#94a3b8" textAnchor="start">{lvl}</text>
      ))}

      {/* Axis spokes */}
      {pts.map((p, i) => (
        <line key={i} x1={cx} y1={cy} x2={p.ax} y2={p.ay} stroke="#e2e8f0" strokeWidth="1" />
      ))}

      {/* Filled polygon */}
      <polygon points={polygon} fill="rgba(124,58,237,0.13)" stroke="#7c3aed"
        strokeWidth="2.5" strokeLinejoin="round" />

      {/* Vertex score circles */}
      {pts.map((p, i) => (
        <g key={i}>
          <circle cx={p.x} cy={p.y} r="11" fill={dotColor(p.score)} opacity="0.15" />
          <circle cx={p.x} cy={p.y} r="7" fill={dotColor(p.score)} />
          <text x={p.x} y={p.y + 1} textAnchor="middle" dominantBaseline="middle"
            fontSize="7" fontWeight="900" fill="white">{p.score}</text>
        </g>
      ))}

      {/* Full two-line labels */}
      {pts.map((p, i) => {
        const [line1, line2] = splitLabel(p.label);
        const isTop = p.angle < -Math.PI * 0.1 && p.angle > -Math.PI * 0.9;
        const isBottom = p.angle > Math.PI * 0.1;
        const dy0 = isTop ? -10 : isBottom ? 6 : 0;
        return (
          <text key={i} x={p.lx} y={p.ly + dy0}
            textAnchor="middle" dominantBaseline="middle"
            fontSize="9.5" fontWeight="700" fill="#334155">
            <tspan x={p.lx} dy="0">{line1}</tspan>
            {line2 && <tspan x={p.lx} dy="13">{line2}</tspan>}
          </text>
        );
      })}
    </svg>
  );
}

/* ─── Radar Legend (HTML, below chart) ─────────────────────── */
const RADAR_LEGEND = [
  { color: '#10b981', label: 'Strong (5)', sub: 'handles this well' },
  { color: '#7c3aed', label: 'Neutral (3)', sub: 'average matchup' },
  { color: '#ef4444', label: 'Weakness (1)', sub: 'vulnerable here' },
];
function RadarLegend() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap', marginTop: 10 }}>
      {RADAR_LEGEND.map((l, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <span style={{
            width: 11, height: 11, borderRadius: '50%',
            background: l.color, flexShrink: 0,
            boxShadow: `0 0 0 3px ${l.color}30`,
          }} />
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#334155' }}>{l.label}</span>
          <span style={{ fontSize: '0.72rem', fontWeight: 500, color: '#94a3b8' }}>— {l.sub}</span>
        </div>
      ))}
    </div>
  );
}


/* ─── Analysing / Loading Panel ────────────────────────────── */
const CRICKET_FACTS = [
  { emoji: '🏏', text: "Sachin Tendulkar scored 100 international centuries — a record that may never be broken." },
  { emoji: '🌀', text: "A cricket ball swings due to asymmetric airflow — the seam angle changes everything." },
  { emoji: '📊', text: "Our AI analyses 10,000+ player data points, combined with live pitch & weather data." },
  { emoji: '🏟️', text: "The MCG holds 100,024 spectators — the largest cricket ground in the world." },
  { emoji: '⚡', text: "A fast bowler's delivery can exceed 160 km/h — that's 44 metres per second." },
  { emoji: '🌦️', text: "Dew factor after 7 PM can reduce swing by up to 40% — a game-changer in night matches." },
  { emoji: '🧠', text: "Ensemble ML models combine Random Forest, XGBoost and Neural Networks for peak accuracy." },
  { emoji: '📐', text: "Smaller boundaries increase six probability by 28% compared to standard grounds." },
  { emoji: '🌏', text: "Over 2.5 billion people watch cricket worldwide — the 2nd most watched sport on Earth." },
];

function AnalysingPanel({ logs }) {
  const [factIdx, setFactIdx] = React.useState(0);
  const [visible, setVisible] = React.useState(true);
  const [counter, setCounter] = React.useState(0);

  React.useEffect(() => {
    const iv = setInterval(() => {
      setVisible(false);
      setTimeout(() => { setFactIdx(i => (i + 1) % CRICKET_FACTS.length); setVisible(true); }, 400);
    }, 3600);
    return () => clearInterval(iv);
  }, []);

  React.useEffect(() => {
    const iv = setInterval(() => setCounter(c => c + 1), 60);
    return () => clearInterval(iv);
  }, []);

  const fact = CRICKET_FACTS[factIdx];
  const latestLog = logs[logs.length - 1] || 'Initialising AI engine…';

  const stats = [
    { label: 'Data Points', val: (1480 + counter * 4).toLocaleString(), color: '#a78bfa' },
    { label: 'Tokens Used', val: (counter * 23).toLocaleString(), color: '#34d399' },
    { label: 'Models Active', val: '3', color: '#fb923c' },
  ];

  const stages = [
    { label: 'Web Scraping', pct: 78 },
    { label: 'Matchup Analysis', pct: 55 },
    { label: 'Pitch & Weather', pct: 88 },
    { label: 'LLM Reasoning', pct: (counter % 40) + 10 },
  ];

  return (
    <div className="ap-card">

      {/* ── Header ── */}
      <div className="ap-header">
        <div className="ap-header-left">
          <div className="ap-header-badge">LIVE</div>
          <span className="ap-header-title">AI Engine Running</span>
        </div>
        <div className="ap-dots">
          {[0, 1, 2].map(i => <span key={i} className="ap-dot" style={{ animationDelay: `${i * 0.18}s` }} />)}
        </div>
      </div>

      {/* ── Glowing Cricket Ball ── */}
      <div className="ap-ball-wrap">
        <div className="ap-glow-ring r1" /><div className="ap-glow-ring r2" /><div className="ap-glow-ring r3" />
        <div className="ap-ball-inner">
          <svg viewBox="0 0 80 80" width="80" height="80">
            <defs>
              <radialGradient id="ballGrad" cx="35%" cy="35%">
                <stop offset="0%" stopColor="#f87171" />
                <stop offset="60%" stopColor="#dc2626" />
                <stop offset="100%" stopColor="#7f1d1d" />
              </radialGradient>
            </defs>
            <circle cx="40" cy="40" r="36" fill="url(#ballGrad)" />
            <path d="M 16 30 Q 40 18 64 30" fill="none" stroke="white" strokeWidth="2.5" strokeOpacity="0.6" />
            <path d="M 16 50 Q 40 62 64 50" fill="none" stroke="white" strokeWidth="2.5" strokeOpacity="0.6" />
            <path d="M 40 4 Q 52 40 40 76" fill="none" stroke="white" strokeWidth="2.5" strokeOpacity="0.5" />
          </svg>
        </div>
      </div>

      {/* ── Live Stats ── */}
      <div className="ap-stats-row">
        {stats.map((s, i) => (
          <div key={i} className="ap-stat">
            <div className="ap-stat-val" style={{ color: s.color }}>{s.val}</div>
            <div className="ap-stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Stage bars ── */}
      <div className="ap-stages">
        {stages.map((s, i) => (
          <div key={i} className="ap-stage-row">
            <span className="ap-stage-label">{s.label}</span>
            <div className="ap-stage-track">
              <div className="ap-stage-fill" style={{ width: `${s.pct}%`, animationDelay: `${i * 0.3}s` }} />
            </div>
            <span className="ap-stage-pct">{s.pct}%</span>
          </div>
        ))}
      </div>

      {/* ── Fact card ── */}
      <div className={`ap-fact ${visible ? 'ap-fact-in' : 'ap-fact-out'}`}>
        <div className="ap-fact-emoji">{fact.emoji}</div>
        <div>
          <div className="ap-fact-head">💡 Did you know?</div>
          <div className="ap-fact-body">{fact.text}</div>
        </div>
      </div>

      {/* ── Current step ── */}
      <div className="ap-status-bar">
        <span className="ap-status-dot" />
        <span className="ap-status-text">{latestLog}</span>
      </div>

    </div>
  );
}


/* ─── Pitch type display labels ───────────────────────────── */
const PITCH_LABELS = {
  dry_turner: 'Dry Turner',
  green_top: 'Green Top',
  flat: 'Flat',
  dusty: 'Dusty',
  bouncy: 'Bouncy',
  slow_low: 'Slow & Low',
  good_batting: 'Good Batting',
  sporting: 'Sporting',
};

/* ─── Dew factor → label ───────────────────────────────────── */
function dewLabel(val) {
  if (val == null) return 'Unknown';
  if (val >= 0.7) return 'High';
  if (val >= 0.4) return 'Medium';
  return 'Low';
}

/* ─── ConditionsPanel ──────────────────────────────────────── */
function ConditionsPanel({ factors, narrative }) {
  if (!factors) return null;

  // Render nothing if ALL numeric fields are null
  const numericFields = [
    factors.pitch_batting_friendliness,
    factors.straight_boundary_m,
    factors.square_boundary_m,
    factors.venue_avg_score,
    factors.day_temp_c,
    factors.night_temp_c,
    factors.humidity_pct,
    factors.wind_speed_kmh,
    factors.dew_factor,
  ];
  if (numericFields.every(v => v == null)) return null;

  const pitchDisplay = factors.pitch_type
    ? (PITCH_LABELS[factors.pitch_type] || factors.pitch_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()))
    : null;

  const tempDisplay = (factors.day_temp_c != null && factors.night_temp_c != null)
    ? `${factors.day_temp_c}°C / ${factors.night_temp_c}°C`
    : factors.day_temp_c != null
      ? `${factors.day_temp_c}°C`
      : null;

  const groundDisplay = (factors.straight_boundary_m != null && factors.square_boundary_m != null)
    ? `Straight ${factors.straight_boundary_m}m · Square ${factors.square_boundary_m}m`
    : null;

  const dewPct = factors.dew_factor != null ? Math.round(factors.dew_factor * 100) : null;

  const isEstimated = factors.weather_source === 'synthetic';

  return (
    <div className="neo-raised panel-card" style={{ marginBottom: 0 }}>
      <div className="section-head">
        🌦️ Match Conditions
        {isEstimated && (
          <span className="conditions-estimated-badge">estimated conditions</span>
        )}
      </div>
      <div className="result-grid conditions-grid">
        {factors.venue_name && (
          <div className="result-box conditions-box">
            <div className="result-label">Venue</div>
            <div className="result-value sm">{factors.venue_name}</div>
          </div>
        )}
        {pitchDisplay && (
          <div className="result-box conditions-box amber">
            <div className="result-label">Pitch Type</div>
            <div className="result-value sm">{pitchDisplay}</div>
          </div>
        )}
        {tempDisplay && (
          <div className="result-box conditions-box">
            <div className="result-label">Day / Night Temp</div>
            <div className="result-value sm">{tempDisplay}</div>
          </div>
        )}
        {factors.humidity_pct != null && (
          <div className="result-box conditions-box">
            <div className="result-label">Humidity</div>
            <div className="result-value sm">{factors.humidity_pct}%</div>
          </div>
        )}
        {factors.wind_speed_kmh != null && (
          <div className="result-box conditions-box">
            <div className="result-label">Wind Speed</div>
            <div className="result-value sm">{factors.wind_speed_kmh} km/h</div>
          </div>
        )}
        {dewPct != null && (
          <div className="result-box conditions-box">
            <div className="result-label">Dew Factor</div>
            <div className="result-value sm" style={{ marginTop: 8 }}>
              <div className="dew-bar-track">
                <div
                  className={`dew-bar-fill ${dewPct >= 70 ? 'dew-high' : dewPct >= 40 ? 'dew-medium' : 'dew-low'}`}
                  style={{ width: `${dewPct}%` }}
                />
              </div>
              <span className="dew-label-text">{dewLabel(factors.dew_factor)}</span>
            </div>
          </div>
        )}
        {groundDisplay && (
          <div className="result-box conditions-box">
            <div className="result-label">Ground Dimensions</div>
            <div className="result-value sm">{groundDisplay}</div>
          </div>
        )}
        {factors.venue_avg_score != null && (
          <div className="result-box conditions-box green">
            <div className="result-label">Venue Avg Score</div>
            <div className="result-value sm">{factors.venue_avg_score}</div>
          </div>
        )}
      </div>

      {narrative && (narrative.pitch_reading || narrative.weather_dew_note || narrative.ground_dimension_note) && (
        <div className="conditions-narrative">
          {narrative.pitch_reading && (
            <div className="conditions-narrative-item">
              <span className="conditions-narrative-label">🏏 Pitch Reading</span>
              <span className="conditions-narrative-text">{narrative.pitch_reading}</span>
            </div>
          )}
          {narrative.weather_dew_note && (
            <div className="conditions-narrative-item">
              <span className="conditions-narrative-label">🌧️ Weather & Dew</span>
              <span className="conditions-narrative-text">{narrative.weather_dew_note}</span>
            </div>
          )}
          {narrative.ground_dimension_note && (
            <div className="conditions-narrative-item">
              <span className="conditions-narrative-label">📐 Ground Dimensions</span>
              <span className="conditions-narrative-text">{narrative.ground_dimension_note}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Rate-Limit Error Helpers ────────────────────────────── */

/**
 * Parse a backend error response and extract rate-limit specific info.
 * Returns { isRateLimit, errorType, message, suggestions } or null.
 */
async function parseRateLimitError(response) {
  try {
    const data = await response.json();
    const detail = data?.detail;
    // Structured rate-limit error from our backend
    if (detail && typeof detail === 'object' && detail.error_type) {
      return {
        isRateLimit: true,
        errorType: detail.error_type,
        message: detail.message || 'API limit reached.',
        suggestions: detail.suggestions || [],
      };
    }
    // Simple string detail — check for rate-limit keywords
    const msg = typeof detail === 'string' ? detail : JSON.stringify(detail || data);
    const lower = msg.toLowerCase();
    const isRate = lower.includes('rate limit') || lower.includes('429')
      || lower.includes('quota') || lower.includes('too many')
      || lower.includes('credits') || lower.includes('exhausted')
      || lower.includes('payment') || lower.includes('billing');
    if (isRate || response.status === 429 || response.status === 402) {
      return {
        isRateLimit: true,
        errorType: response.status === 402 ? 'quota_exceeded' : 'rate_limit',
        message: msg,
        suggestions: [
          'Switch to a different model (especially a free one marked with ✅)',
          'Wait and try again later — free-tier limits reset every 24 hours',
          'Replace your API key with a new one from https://openrouter.ai/keys',
          'Upgrade to a paid API key for unlimited usage',
        ],
      };
    }
    return { isRateLimit: false, message: msg };
  } catch {
    return { isRateLimit: false, message: response.statusText || 'Request failed' };
  }
}

/* ─── Rate-Limit Error Panel Component ────────────────────── */
function RateLimitErrorPanel({ errorType, message, suggestions, onDismiss }) {
  const configs = {
    rate_limit: {
      icon: '🚫',
      title: 'Rate Limit Reached',
      color: '#f97316',
      bg: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)',
      border: '#fed7aa',
      iconBg: '#fff7ed',
    },
    quota_exceeded: {
      icon: '💳',
      title: 'API Credits Exhausted',
      color: '#ef4444',
      bg: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
      border: '#fecaca',
      iconBg: '#fef2f2',
    },
    payment_required: {
      icon: '💰',
      title: 'Payment Required',
      color: '#ef4444',
      bg: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
      border: '#fecaca',
      iconBg: '#fef2f2',
    },
    auth_error: {
      icon: '🔑',
      title: 'API Key Error',
      color: '#dc2626',
      bg: 'linear-gradient(135deg, #fef2f2 0%, #fce7f3 100%)',
      border: '#fda4af',
      iconBg: '#fff1f2',
    },
  };
  const cfg = configs[errorType] || configs.rate_limit;

  return (
    <div style={{
      background: cfg.bg,
      border: `2px solid ${cfg.border}`,
      borderRadius: 16,
      padding: '24px 28px',
      marginTop: 12,
      position: 'relative',
      boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
      animation: 'fadeInUp 0.4s ease-out',
    }}>
      {/* Dismiss button */}
      {onDismiss && (
        <button onClick={onDismiss} style={{
          position: 'absolute', top: 12, right: 16,
          background: 'none', border: 'none', cursor: 'pointer',
          fontSize: '1.2rem', color: '#94a3b8', lineHeight: 1,
        }} title="Dismiss">✕</button>
      )}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
        <span style={{
          fontSize: '2rem',
          background: cfg.iconBg,
          borderRadius: 12,
          width: 52, height: 52,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: `0 2px 8px ${cfg.color}20`,
        }}>{cfg.icon}</span>
        <div>
          <div style={{ fontWeight: 800, fontSize: '1.15rem', color: cfg.color, letterSpacing: '-0.02em' }}>
            {cfg.title}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, marginTop: 2 }}>
            Your request was blocked by the AI provider
          </div>
        </div>
      </div>

      {/* Message */}
      <div style={{
        background: 'rgba(255,255,255,0.7)',
        borderRadius: 10,
        padding: '14px 18px',
        fontSize: '0.85rem',
        color: '#334155',
        lineHeight: 1.65,
        fontWeight: 500,
        whiteSpace: 'pre-line',
        marginBottom: suggestions?.length ? 16 : 0,
        borderLeft: `4px solid ${cfg.color}`,
      }}>
        {message}
      </div>

      {/* Suggestions */}
      {suggestions?.length > 0 && (
        <div>
          <div style={{
            fontWeight: 700, fontSize: '0.82rem', color: '#475569',
            marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span style={{ fontSize: '1rem' }}>💡</span> What you can do:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {suggestions.map((s, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                background: 'rgba(255,255,255,0.6)',
                borderRadius: 10,
                padding: '10px 14px',
                fontSize: '0.82rem',
                color: '#334155',
                fontWeight: 500,
                lineHeight: 1.5,
              }}>
                <span style={{
                  background: cfg.color,
                  color: 'white',
                  borderRadius: 6,
                  width: 22, height: 22,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.7rem', fontWeight: 800,
                  flexShrink: 0, marginTop: 1,
                }}>{i + 1}</span>
                <span>{s}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick action links */}
      <div style={{
        display: 'flex', gap: 10, marginTop: 18, flexWrap: 'wrap',
      }}>
        <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 16px',
            background: cfg.color,
            color: 'white',
            borderRadius: 8,
            fontSize: '0.78rem',
            fontWeight: 700,
            textDecoration: 'none',
            boxShadow: `0 2px 8px ${cfg.color}30`,
            transition: 'transform 0.15s, box-shadow 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-1px)'; }}
          onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
        >
          🔑 Get New API Key
        </a>
        <a href="https://openrouter.ai/credits" target="_blank" rel="noopener noreferrer"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 16px',
            background: 'white',
            color: cfg.color,
            border: `1.5px solid ${cfg.color}`,
            borderRadius: 8,
            fontSize: '0.78rem',
            fontWeight: 700,
            textDecoration: 'none',
            transition: 'transform 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-1px)'; }}
          onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
        >
          💳 Add Credits
        </a>
      </div>
    </div>
  );
}


/* ─── Main App ─────────────────────────────────────────────── */
export default function App() {
  const [tab, setTab] = useState('squad');

  /* Squad state */
  const [squadUrl, setSquadUrl] = useState('https://www.cricbuzz.com/cricket-match-squads/129563/eng-vs-nz-2nd-test-new-zealand-tour-of-england-2026');
  const [squadData, setSquadData] = useState(null);
  const [loadingRoster, setLoadingRoster] = useState(false);
  const [rosterErr, setRosterErr] = useState('');
  const [playerMap, setPlayerMap] = useState({});
  const [playerLabels, setPlayerLabels] = useState([]);
  const [selPlayer, setSelPlayer] = useState('');
  const [squadFormat, setSquadFormat] = useState('T20');
  const [squadModel, setSquadModel] = useState(MODELS[0].id);
  const [sqMatchDate, setSqMatchDate] = useState(new Date().toISOString().split('T')[0]);
  const [sqIsDayNight, setSqIsDayNight] = useState(false);

  /* Manual state */
  const [mPlayer, setMPlayer] = useState('Virat Kohli');
  const [mOpp, setMOpp] = useState('Pakistan');
  const [mVenue, setMVenue] = useState('Melbourne Cricket Ground');
  const [mFormat, setMFormat] = useState('T20');
  const [mModel, setMModel] = useState(MODELS[0].id);
  const [mMatchDate, setMMatchDate] = useState(new Date().toISOString().split('T')[0]);
  const [mIsDayNight, setMIsDayNight] = useState(false);

  /* Offline state */
  const [oSport, setOSport] = useState('cricket');
  const [oId, setOId] = useState(1);
  const [oDate, setODate] = useState(new Date().toISOString().split('T')[0]);
  const [oOpp, setOOpp] = useState('Team 3');
  const [oHA, setOHA] = useState('home');
  const [oStr, setOStr] = useState(0.7);
  const [oInjury, setOInjury] = useState(0.05);
  const [oRest, setORest] = useState(4);
  const [oVenueId, setOVenueId] = useState('');
  const [oIsDayNight, setOIsDayNight] = useState(false);
  const [offResult, setOffResult] = useState(null);
  const [offLoading, setOffLoading] = useState(false);
  const [offErr, setOffErr] = useState('');
  const [trainStatus, setTrainStatus] = useState(null);
  const [trainLoading, setTrainLoading] = useState(false);

  /* Prediction shared state */
  const [predicting, setPredicting] = useState(false);
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState(null);
  const [predErr, setPredErr] = useState('');
  const [predErrInfo, setPredErrInfo] = useState(null); // { isRateLimit, errorType, message, suggestions }
  const [visMode, setVisMode] = useState('3d-stadium');

  /* ── Load Roster ──────────────────────────────────── */
  const loadRoster = async () => {
    setLoadingRoster(true); setRosterErr(''); setSquadData(null);
    try {
      const res = await fetch(`${API_BASE}/v1/cricket/squad?url=${encodeURIComponent(squadUrl)}`);
      if (!res.ok) throw new Error((await res.json()).detail || 'Load failed');
      const data = await res.json();
      setSquadData(data);
      const labels = [], map = {};
      (data.squad1 || []).forEach(p => {
        const l = `${p.name} (${data.team1} · ${p.role})`;
        labels.push(l);
        map[l] = { name: p.name, role: p.role, url: p.href, opp_team: data.team2, opp_squad: data.squad2 || [] };
      });
      (data.squad2 || []).forEach(p => {
        const l = `${p.name} (${data.team2} · ${p.role})`;
        labels.push(l);
        map[l] = { name: p.name, role: p.role, url: p.href, opp_team: data.team1, opp_squad: data.squad1 || [] };
      });
      setPlayerLabels(labels); setPlayerMap(map);
      if (labels[0]) setSelPlayer(labels[0]);
      const s = (data.series || '').toLowerCase();
      setSquadFormat(s.includes('test') ? 'Test' : s.includes('odi') ? 'ODI' : 'T20');
    } catch (e) { setRosterErr(e.message); }
    finally { setLoadingRoster(false); }
  };

  /* ── Add log ──────────────────────────────────────── */
  const addLogs = (steps) => setLogs(prev => [...prev, ...steps]);

  /* ── Squad predict ────────────────────────────────── */
  const runSquad = async () => {
    const pl = playerMap[selPlayer]; if (!pl) return;
    setPredicting(true); setPredErr(''); setResult(null);
    setLogs(['Initialising engine…', 'Scraping Cricbuzz player profile…']);
    const steps = ['Parsing opposition squad…', 'Fetching venue & pitch report…', 'Calling LLM reasoning layer…'];
    let si = 0;
    const iv = setInterval(() => { if (si < steps.length) { addLogs([steps[si++]]); } else clearInterval(iv); }, 1600);
    try {
      const res = await fetch(`${API_BASE}/v1/cricket/predict-squad`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_name: pl.name, player_role: pl.role, player_profile_url: pl.url,
          opposition_team: pl.opp_team, opponent_squad: pl.opp_squad,
          match_format: squadFormat, venue: squadData?.venue || '', model_name: squadModel,
          match_date: sqMatchDate || undefined, is_day_night: sqIsDayNight,
        }),
      });
      clearInterval(iv);
      if (!res.ok) {
        const parsed = await parseRateLimitError(res);
        if (parsed?.isRateLimit) {
          setPredErrInfo(parsed);
          setPredErr(parsed.message);
        } else {
          setPredErr(parsed?.message || 'Prediction failed');
        }
        return;
      }
      const d = await res.json();
      setResult(d); 
      setLogs(d.steps?.length ? d.steps : [...logs, '✓ Done!']);
      if (d.error) {
        // Check if the error in the response body is a rate-limit error
        const lower = (d.error || '').toLowerCase();
        const isRate = d.error_type || lower.includes('rate limit') || lower.includes('429')
          || lower.includes('quota') || lower.includes('credits');
        if (isRate) {
          setPredErrInfo({
            isRateLimit: true,
            errorType: d.error_type || 'rate_limit',
            message: d.error,
            suggestions: [
              'Switch to a different model (especially a free one marked with ✅)',
              'Wait and try again later — free-tier limits reset every 24 hours',
              'Replace your API key with a new one from https://openrouter.ai/keys',
              'Upgrade to a paid API key for unlimited usage',
            ],
          });
        }
        setPredErr(d.error);
      }
    } catch (e) { clearInterval(iv); setPredErr(e.message); }
    finally { setPredicting(false); }
  };

  /* ── Clear result when player changes ─────────────── */
  React.useEffect(() => {
    setResult(null);
    setPredErr('');
    setPredErrInfo(null);
  }, [selPlayer]);

  /* ── Manual predict ───────────────────────────────── */
  const runManual = async () => {
    setPredicting(true); setPredErr(''); setResult(null);
    setLogs([`Searching web for ${mPlayer}…`, 'Initialising…']);
    const steps = [`Analysing matchups vs ${mOpp} bowlers…`, `Scraping conditions at ${mVenue}…`, 'LLM deep reasoning…'];
    let si = 0;
    const iv = setInterval(() => { if (si < steps.length) { addLogs([steps[si++]]); } else clearInterval(iv); }, 1600);
    try {
      const res = await fetch(`${API_BASE}/v1/cricket/predict-manual`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_name: mPlayer, opposition: mOpp, venue: mVenue, match_format: mFormat, model_name: mModel,
          match_date: mMatchDate || undefined, is_day_night: mIsDayNight,
        }),
      });
      clearInterval(iv);
      if (!res.ok) {
        const parsed = await parseRateLimitError(res);
        if (parsed?.isRateLimit) {
          setPredErrInfo(parsed);
          setPredErr(parsed.message);
        } else {
          setPredErr(parsed?.message || 'Prediction failed');
        }
        return;
      }
      const d = await res.json();
      setResult(d); 
      if (mFormat === 'Test' || d.test_match_innings_breakdown) {
        setVisMode('3d-test-breakdown');
      } else {
        setVisMode('3d-stadium');
      }
      setLogs(d.steps?.length ? d.steps : [...logs, '✓ Done!']);
      if (d.error) {
        // Check if the error in the response body is a rate-limit error
        const lower = (d.error || '').toLowerCase();
        const isRate = d.error_type || lower.includes('rate limit') || lower.includes('429')
          || lower.includes('quota') || lower.includes('credits');
        if (isRate) {
          setPredErrInfo({
            isRateLimit: true,
            errorType: d.error_type || 'rate_limit',
            message: d.error,
            suggestions: [
              'Switch to a different model (especially a free one marked with ✅)',
              'Wait and try again later — free-tier limits reset every 24 hours',
              'Replace your API key with a new one from https://openrouter.ai/keys',
              'Upgrade to a paid API key for unlimited usage',
            ],
          });
        }
        setPredErr(d.error);
      }
    } catch (e) { clearInterval(iv); setPredErr(e.message); }
    finally { setPredicting(false); }
  };

  /* ── Offline predict ──────────────────────────────── */
  const runOffline = async () => {
    setOffLoading(true); setOffErr(''); setOffResult(null);
    try {
      const res = await fetch(`${API_BASE}/v1/predict`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: +oId, sport: oSport, match_date: oDate, opposition: oOpp,
          home_away: oHA, opposition_strength: +oStr, injury_risk: +oInjury, days_rest: +oRest,
          venue_id: oVenueId || undefined, is_day_night: oIsDayNight,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      setOffResult(await res.json());
    } catch (e) { setOffErr(e.message); }
    finally { setOffLoading(false); }
  };

  /* ── Train models ─────────────────────────────────── */
  const trainModels = async () => {
    setTrainLoading(true); setTrainStatus(null);
    try {
      const res = await fetch(`${API_BASE}/v1/models/train`, { method: 'POST' });
      setTrainStatus(await res.json());
    } catch (e) { alert('Train error: ' + e.message); }
    finally { setTrainLoading(false); }
  };

  /* ── Vulnerability data ───────────────────────────── */
  const radarData = () => {
    const bat = result?.batsman_prediction; if (!bat) return [];
    const types = ['Off-spin', 'Leg-spin', 'Left-arm spinner', 'Left-arm pacer', 'Right-arm pacer', 'Medium pace', 'Fast pace'];
    const str = (bat.bowling_strength || []).map(x => x.toLowerCase());
    const wk = (bat.bowling_weakness || []).map(x => x.toLowerCase());
    return types.map(t => {
      const tl = t.toLowerCase();
      if (wk.some(w => w.includes(tl) || tl.includes(w))) return { type: t, score: 1 };
      if (str.some(s => s.includes(tl) || tl.includes(s))) return { type: t, score: 5 };
      return { type: t, score: 3 };
    });
  };

  const lengthData = () => {
    const bat = result?.batsman_prediction; if (!bat) return [];
    const lengths = ['Good length', 'Hard length', 'Short (Bouncer)', 'Full (Yorker)', 'Half volley', 'Googly', 'Slower ball'];
    const str = (bat.length_strength || []).map(x => x.toLowerCase());
    const wk = (bat.length_weakness || []).map(x => x.toLowerCase());
    return lengths.map(l => {
      const ll = l.toLowerCase();
      if (wk.some(w => w.includes(ll) || ll.includes(w))) return { l, score: -1 };
      if (str.some(s => s.includes(ll) || ll.includes(s))) return { l, score: 1 };
      return { l, score: 0 };
    });
  };

  const isBat = ['batsman', 'all-rounder'].includes(result?.role?.toLowerCase());
  const isBowl = ['bowler', 'all-rounder'].includes(result?.role?.toLowerCase());
  const bio = result?.scraped_context?.profile_data || {};

  /* ── Field wrapper helper ─────────────────────────── */
  const Field = ({ label, children }) => (
    <div className="field-group">
      <span className="field-label">{label}</span>
      {children}
    </div>
  );

  /* ─── RENDER ──────────────────────────────────────── */
  return (
    <div className="app-shell">

      {/* ── TOP STATS GRID ──────────────────────────── */}
      <div className="top-grid mb-4">

        {/* Profile Card */}
        <div className="neo-raised profile-card">
          <div className="avatar-ring"><UserIcon /></div>
          <div>
            <div className="profile-name">Hi, Wraith</div>
            <div className="profile-sub">7 devices active</div>
          </div>
        </div>

        {/* Brand Card */}
        <div className="neo-raised brand-card">
          <div className="brand-title">🏏 Norrin<span className="brand-accent">.AI</span></div>
          <div className="brand-desc">
            Real-time analysis &amp; AI-powered predictions for cricket — combining live web intelligence with LLM reasoning.
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
            <span className="badge-green status-badge">⚡ Live Web Scraping</span>
            <span className="badge-purple status-badge">🧠 LLM Reasoning</span>
            <span className="badge-red status-badge">📊 Ensemble ML</span>
          </div>
        </div>

        {/* AI Power Analytics List Panel */}
        <div className="neo-raised status-card">
          <div style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-gray)', marginBottom: 6 }}>AI Power Analytics</div>
          {['Live Web Data', 'OpenRouter LLM', '10+ Models', '∞ Players'].map((item, i) => (
            <div key={i} className="neo-flat" style={{ padding: '10px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderRadius: 12, marginBottom: 4 }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark)' }}>{item}</span>
              <span style={{ color: 'var(--text-gray)', display: 'flex', alignItems: 'center' }}><ChevronRight /></span>
            </div>
          ))}
        </div>
      </div>

      {/* ── TABS ────────────────────────────────────── */}
      <div className="tab-switcher mb-4">
        {[
          { id: 'squad', label: '📡 Live Squad Matchup' },
          { id: 'manual', label: '✍️ Manual Entry' },
          { id: 'compare', label: '⚔️ Compare Players' },
          { id: 'offline', label: '🔮 Offline ML' },
        ].map(t => (
          <button key={t.id} className={`tab-btn ${tab === t.id ? 'active' : ''}`}
            onClick={() => { setTab(t.id); setResult(null); setPredErr(''); setPredErrInfo(null); setLogs([]); }}
            title={t.label}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── MAIN 2-COLUMN GRID ──────────────────────── */}
      <div className="main-grid">

        {/* LEFT PANEL */}
        <div className="gap-col">
          <div className="neo-raised panel-card">
            <div className="panel-title">⚙ Control Inputs</div>

            {/* TAB: SQUAD */}
            {tab === 'squad' && (
              <div className="gap-col">
                <Field label="Cricbuzz Squad URL">
                  <div style={{ display: 'flex', gap: 8 }}>
                    <div className="neo-inset" style={{ flex: 1 }}>
                      <input
                        title="Cricbuzz Squad URL"
                        className="neo-input"
                        value={squadUrl}
                        onChange={e => setSquadUrl(e.target.value)}
                        placeholder="https://www.cricbuzz.com/cricket-match-squads/…"
                      />
                      {squadUrl && (
                        <button
                          type="button"
                          className="clear-btn"
                          onClick={() => setSquadUrl('')}
                          title="Clear Squad URL"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                    <button className="btn btn-slate btn-sm" onClick={loadRoster} disabled={loadingRoster} title="Load roster">
                      {loadingRoster ? <SpinnerIcon /> : 'Load'}
                    </button>
                  </div>
                  {rosterErr && <p style={{ color: '#ef4444', fontSize: '0.75rem', marginTop: 6, fontWeight: 600 }}>{rosterErr}</p>}
                </Field>

                {squadData && (
                  <>
                    <div className="info-strip">🏆 {squadData.series} · {squadData.team1} vs {squadData.team2}</div>

                    <Field label="Select Player">
                      <div className="neo-inset">
                        <select className="neo-select" title="Select Player" value={selPlayer} onChange={e => setSelPlayer(e.target.value)}>
                          {playerLabels.map((l, i) => <option key={i} value={l}>{l}</option>)}
                        </select>
                      </div>
                    </Field>

                    <div className="row-2">
                      <Field label="Match Format">
                        <div className="neo-inset">
                          <select className="neo-select" title="Match Format" value={squadFormat} onChange={e => setSquadFormat(e.target.value)}>
                            {['T20', 'ODI', 'Test', 'IPL'].map(f => <option key={f} value={f}>{f}</option>)}
                          </select>
                        </div>
                      </Field>
                      <Field label="Venue">
                        <div className="neo-inset" style={{ opacity: 0.65 }}>
                          <input className="neo-input" title="Venue" value={squadData.venue || ''} readOnly placeholder="Venue" />
                        </div>
                      </Field>
                    </div>

                    <div className="row-2">
                      <Field label="Match Date">
                        <div className="neo-inset">
                          <input className="neo-input" type="date" title="Match Date" value={sqMatchDate} onChange={e => setSqMatchDate(e.target.value)} />
                        </div>
                      </Field>
                      <Field label="Day/Night Match">
                        <div className="neo-inset" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <input
                            type="checkbox"
                            id="sq-day-night"
                            title="Day/Night Match"
                            checked={sqIsDayNight}
                            onChange={e => setSqIsDayNight(e.target.checked)}
                            style={{ accentColor: 'var(--color-purple)', width: 18, height: 18, cursor: 'pointer' }}
                          />
                          <label htmlFor="sq-day-night" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-dark)', cursor: 'pointer' }}>
                            {sqIsDayNight ? 'Day/Night' : 'Day only'}
                          </label>
                        </div>
                      </Field>
                    </div>

                    <Field label="LLM Model">
                      <div className="neo-inset">
                        <select className="neo-select" title="LLM Model" value={squadModel} onChange={e => setSquadModel(e.target.value)}>
                          {MODELS.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
                        </select>
                      </div>
                    </Field>

                    <button className="btn btn-purple" onClick={runSquad} disabled={predicting || !selPlayer} title="Analyse &amp; Predict">
                      {predicting ? <SpinnerIcon /> : '🔮'} Analyse &amp; Predict
                    </button>
                  </>
                )}

                {!squadData && !loadingRoster && (
                  <p style={{ color: 'var(--text-gray)', fontSize: '0.82rem', textAlign: 'center', padding: '16px 0', fontWeight: 500 }}>
                    Paste a Cricbuzz squad URL above and click <strong>Load</strong>.
                  </p>
                )}
              </div>
            )}

            {/* TAB: MANUAL */}
            {tab === 'manual' && (
              <div className="gap-col">
                <Field label="Player Name">
                  <div className="neo-inset">
                    <input
                      className="neo-input"
                      title="Player Name"
                      value={mPlayer}
                      onChange={e => setMPlayer(e.target.value)}
                      placeholder="e.g. Virat Kohli"
                      list="popular-players-list"
                    />
                    {mPlayer && (
                      <button
                        type="button"
                        className="clear-btn"
                        onClick={() => setMPlayer('')}
                        title="Clear Player Name"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </Field>

                <div className="row-2">
                  <Field label="Opposition">
                    <div className="neo-inset">
                      <input
                        className="neo-input"
                        title="Opposition"
                        value={mOpp}
                        onChange={e => setMOpp(e.target.value)}
                        placeholder="e.g. Pakistan"
                        list="popular-teams-list"
                      />
                      {mOpp && (
                        <button
                          type="button"
                          className="clear-btn"
                          onClick={() => setMOpp('')}
                          title="Clear Opposition"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </Field>
                  <Field label="Venue">
                    <div className="neo-inset">
                      <input
                        className="neo-input"
                        title="Venue"
                        value={mVenue}
                        onChange={e => setMVenue(e.target.value)}
                        placeholder="e.g. MCG"
                        list="popular-venues-list"
                      />
                      {mVenue && (
                        <button
                          type="button"
                          className="clear-btn"
                          onClick={() => setMVenue('')}
                          title="Clear Venue"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </Field>
                </div>

                <div className="row-2">
                  <Field label="Match Format">
                    <div className="neo-inset">
                      <select className="neo-select" title="Match Format" value={mFormat} onChange={e => setMFormat(e.target.value)}>
                        {['T20', 'ODI', 'Test', 'IPL'].map(f => <option key={f} value={f}>{f}</option>)}
                      </select>
                    </div>
                  </Field>
                  <Field label="LLM Model">
                    <div className="neo-inset">
                      <select className="neo-select" title="LLM Model" value={mModel} onChange={e => setMModel(e.target.value)}>
                        {MODELS.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
                      </select>
                    </div>
                  </Field>
                </div>

                <div className="row-2">
                  <Field label="Match Date">
                    <div className="neo-inset">
                      <input className="neo-input" type="date" title="Match Date" value={mMatchDate} onChange={e => setMMatchDate(e.target.value)} />
                    </div>
                  </Field>
                  <Field label="Day/Night Match">
                    <div className="neo-inset" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <input
                        type="checkbox"
                        id="m-day-night"
                        title="Day/Night Match"
                        checked={mIsDayNight}
                        onChange={e => setMIsDayNight(e.target.checked)}
                        style={{ accentColor: 'var(--color-purple)', width: 18, height: 18, cursor: 'pointer' }}
                      />
                      <label htmlFor="m-day-night" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-dark)', cursor: 'pointer' }}>
                        {mIsDayNight ? 'Day/Night' : 'Day only'}
                      </label>
                    </div>
                  </Field>
                </div>

                <button className="btn btn-purple" onClick={runManual} disabled={predicting || !mPlayer} title="Analyse &amp; Predict">
                  {predicting ? <SpinnerIcon /> : '🔮'} Analyse &amp; Predict
                </button>
              </div>
            )}

            {/* TAB: OFFLINE */}
            {tab === 'offline' && (
              <div className="gap-col">
                <div className="row-2">
                  <Field label="Sport">
                    <div className="neo-inset">
                      <select className="neo-select" title="Sport" value={oSport} onChange={e => setOSport(e.target.value)}>
                        <option value="cricket">Cricket</option>
                        <option value="football">Football</option>
                        <option value="nba">NBA</option>
                      </select>
                    </div>
                  </Field>
                  <Field label="Player ID">
                    <div className="neo-inset">
                      <input className="neo-input" title="Player ID" type="number" value={oId} onChange={e => setOId(+e.target.value)} placeholder="e.g. 1" />
                    </div>
                  </Field>
                </div>

                <div className="row-2">
                  <Field label="Opposition">
                    <div className="neo-inset">
                      <input
                        className="neo-input"
                        title="Opposition"
                        value={oOpp}
                        onChange={e => setOOpp(e.target.value)}
                        placeholder="Team 3"
                        list="popular-teams-list"
                      />
                      {oOpp && (
                        <button
                          type="button"
                          className="clear-btn"
                          onClick={() => setOOpp('')}
                          title="Clear Opposition"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </Field>
                  <Field label="Home / Away">
                    <div className="neo-inset">
                      <select className="neo-select" title="Home / Away" value={oHA} onChange={e => setOHA(e.target.value)}>
                        <option value="home">Home</option>
                        <option value="away">Away</option>
                      </select>
                    </div>
                  </Field>
                </div>

                <Field label={`Opponent Strength: ${oStr}`}>
                  <input type="range" min="0" max="1" step="0.1" title="Opponent Strength"
                    style={{ width: '100%', accentColor: 'var(--color-purple)' }}
                    value={oStr} onChange={e => setOStr(+e.target.value)} />
                </Field>

                <div className="row-2">
                  <Field label="Injury Risk">
                    <div className="neo-inset">
                      <input className="neo-input" type="number" step="0.01" title="Injury Risk" value={oInjury} onChange={e => setOInjury(+e.target.value)} placeholder="0.05" />
                    </div>
                  </Field>
                  <Field label="Days Rest">
                    <div className="neo-inset">
                      <input className="neo-input" type="number" title="Days Rest" value={oRest} onChange={e => setORest(+e.target.value)} placeholder="4" />
                    </div>
                  </Field>
                </div>

                <Field label="Venue ID (optional)">
                  <div className="neo-inset">
                    <input
                      className="neo-input"
                      title="Venue ID"
                      value={oVenueId}
                      onChange={e => setOVenueId(e.target.value)}
                      placeholder="e.g. wankhede"
                      list="offline-venue-ids-list"
                    />
                    {oVenueId && (
                      <button
                        type="button"
                        className="clear-btn"
                        onClick={() => setOVenueId('')}
                        title="Clear Venue ID"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </Field>

                <Field label="Day/Night Match">
                  <div className="neo-inset" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <input
                      type="checkbox"
                      id="o-day-night"
                      title="Day/Night Match"
                      checked={oIsDayNight}
                      onChange={e => setOIsDayNight(e.target.checked)}
                      style={{ accentColor: 'var(--color-purple)', width: 18, height: 18, cursor: 'pointer' }}
                    />
                    <label htmlFor="o-day-night" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-dark)', cursor: 'pointer' }}>
                      {oIsDayNight ? 'Day/Night' : 'Day only'}
                    </label>
                  </div>
                </Field>

                <button className="btn btn-purple" onClick={runOffline} disabled={offLoading} title="Predict">
                  {offLoading ? <SpinnerIcon /> : '🔮'} Predict with ML Models
                </button>

                <hr className="divider" />

                <button className="btn btn-slate" onClick={trainModels} disabled={trainLoading} title="Re-train">
                  {trainLoading ? <SpinnerIcon /> : '⚙️'} Re-train ML Models
                </button>

                {trainStatus && (
                  <div className="info-strip mt-3" style={{ fontSize: '0.75rem', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                    {JSON.stringify(trainStatus, null, 2)}
                  </div>
                )}
                {offErr && <div className="info-strip red mt-3">⚠️ {offErr}</div>}
              </div>
            )}
          </div>

          {/* LIVE LOGS */}
          {(predicting || logs.length > 0) && (
            <div className="neo-raised panel-card">
              <div className="panel-title">⚡ Live Analysis Progress</div>
              <div className="log-list">
                {logs.map((l, i) => (
                  <div key={i} className="log-item">
                    <span className={`log-dot ${i === logs.length - 1 && predicting ? 'active' : 'done'}`} />
                    {l}
                  </div>
                ))}
              </div>
            </div>
          )}

          {predErrInfo?.isRateLimit ? (
            <RateLimitErrorPanel
              errorType={predErrInfo.errorType}
              message={predErrInfo.message}
              suggestions={predErrInfo.suggestions}
              onDismiss={() => {
                setPredErr('');
                setPredErrInfo(null);
              }}
            />
          ) : predErr ? (
            <div className="neo-raised info-strip red" style={{ margin: 0 }}>
              ⚠️ {predErr}
            </div>
          ) : null}
        </div>

        {/* RIGHT PANEL */}
        <div className="gap-col">

          {/* OFFLINE RESULTS */}
          {tab === 'offline' && offResult && (
            <div className="neo-raised panel-card">
              <div className="panel-title">🔮 ML Ensemble Results</div>
              <div className="result-grid">
                <div className="result-box green">
                  <div className="result-label">Predicted Performance</div>
                  <div className="result-value">{offResult.predicted_performance?.toFixed(2) ?? 'N/A'}</div>
                </div>
                <div className="result-box">
                  <div className="result-label">Confidence</div>
                  <div className="result-value" style={{ fontSize: '1rem', paddingTop: 6 }}>{offResult.confidence_level ?? 'N/A'}</div>
                </div>
                <div className="result-box amber">
                  <div className="result-label">Sport</div>
                  <div className="result-value" style={{ fontSize: '1rem', paddingTop: 6, textTransform: 'uppercase' }}>{offResult.sport ?? oSport}</div>
                </div>
                <div className="result-box red">
                  <div className="result-label">Risk Level</div>
                  <div className="result-value" style={{ fontSize: '1rem', paddingTop: 6 }}>
                    {offResult.risk_level ?? 'N/A'}
                  </div>
                </div>
              </div>

              {Array.isArray(offResult.confidence_interval) && offResult.confidence_interval.length === 2 && (
                <div className="result-grid" style={{ gridTemplateColumns: '1fr', marginBottom: 20 }}>
                  <div className="result-box" style={{ borderTopColor: 'var(--color-teal)' }}>
                    <div className="result-label">Confidence Interval</div>
                    <div className="result-value" style={{ fontSize: '1.25rem', paddingTop: 4 }}>
                      {offResult.confidence_interval[0].toFixed(1)} – {offResult.confidence_interval[1].toFixed(1)}
                    </div>
                  </div>
                </div>
              )}

              <ConditionsPanel factors={offResult.contextual_factors} />
            </div>
          )}

          {/* LIVE PREDICTION RESULTS */}
          {tab !== 'offline' && tab !== 'compare' && result && (
            <ResultErrorBoundary>
            <>
              {result.visual_tagline && <div className="tagline-banner">"{result.visual_tagline}"</div>}

              {/* Bio Details */}
              {bio?.name && (
                <div className="neo-raised bio-strip">
                  {bio.image_url && (
                    <img
                      className="bio-avatar"
                      src={bio.image_url}
                      alt={bio.name}
                      onError={e => { e.currentTarget.style.display = 'none'; }}
                    />
                  )}
                  <div>
                    <div className="bio-name">{bio.name}</div>
                    <div className="bio-meta">{bio.country} · {bio.role} · {bio.bat_style} · {bio.bowl_style}</div>
                    {bio.dob && <div className="bio-meta">DOB: {bio.dob} · {bio.height}</div>}
                  </div>
                </div>
              )}

              {/* 3D VISUAL MODES SUB-NAV */}
              <div className="tab-switcher mb-3" style={{ background: 'var(--bg-card)', padding: 6, borderRadius: 14 }}>
                {[
                  { id: '3d-stadium', label: '🏟️ 3D Stadium Field' },
                  { id: '3d-test-breakdown', label: '⏳ 3D Test Innings' },
                  { id: '3d-bowling-map', label: '🎯 3D Bowler Pitch Map' },
                  { id: '3d-bowling-speed', label: '⚡ 3D Speed & Arsenal' },
                  { id: '3d-delivery', label: '🎥 3D Ball Replay' },
                  { id: '3d-wagon', label: '🎯 3D Shot Wheel' },
                  { id: '3d-pitch', label: '📊 3D Length Map' },
                  { id: '3d-weather', label: '🌦️ 3D Weather & Dew' },
                  { id: '3d-impact', label: '⚡ 3D Match Impact' },
                  { id: '3d-globe', label: '🌐 3D Vulnerability Globe' },
                  { id: 'stats', label: '📋 Detailed Stats' },
                ].map(v => (
                  <button
                    key={v.id}
                    className={`tab-btn ${visMode === v.id ? 'active' : ''}`}
                    onClick={() => setVisMode(v.id)}
                    style={{ fontSize: '0.78rem', padding: '6px 12px' }}
                  >
                    {v.label}
                  </button>
                ))}
              </div>

              {/* 3D Visual Views */}
              {visMode === '3d-stadium' && (
                <CricketGround3D
                  batsmanPrediction={result.batsman_prediction}
                  groundDimensions={result.environmental_conditions}
                />
              )}

              {visMode === '3d-test-breakdown' && (
                <TestInningsBreakdown3D
                  testBreakdown={result.test_match_innings_breakdown}
                  playerName={result.player_name || mPlayer}
                />
              )}

              {visMode === '3d-bowling-map' && (
                <BowlingPitchMap3D bowlerPrediction={result.bowler_prediction} />
              )}

              {visMode === '3d-bowling-speed' && (
                <BowlerSpeedGauge3D bowlerPrediction={result.bowler_prediction} />
              )}

              {visMode === '3d-delivery' && (
                <DeliveryTrajectory3D batsmanPrediction={result.batsman_prediction} />
              )}

              {visMode === '3d-wagon' && (
                <WagonWheel3D batsmanPrediction={result.batsman_prediction} />
              )}

              {visMode === '3d-pitch' && (
                <DeliveryHeatmap3D batsmanPrediction={result.batsman_prediction} />
              )}

              {visMode === '3d-weather' && (
                <EnvironmentalWeather3D environmentalConditions={result.environmental_conditions} />
              )}

              {visMode === '3d-impact' && (
                <ImpactMatrix3D
                  batsmanPrediction={result.batsman_prediction}
                  bowlerPrediction={result.bowler_prediction}
                />
              )}

              {visMode === '3d-globe' && (
                <VulnerabilityGlobe3D batsmanPrediction={result.batsman_prediction} />
              )}

              <ConditionsPanel factors={result.contextual_factors} narrative={result.conditions_impact} />

              {/* Metrics side-by-side */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

                {/* Batsman prediction */}
                {isBat && result.batsman_prediction && (
                  <div className="neo-raised panel-card">
                    <div className="section-head">🏏 Batsman Metrics</div>
                    <div className="result-grid" style={{ marginBottom: 12 }}>
                      <div className="result-box amber">
                        <div className="result-label">Runs Range</div>
                        <div className="result-value sm">{result.batsman_prediction.predicted_runs_range ?? 'N/A'}</div>
                      </div>
                      <div className="result-box red">
                        <div className="result-label">Dismissal Mode</div>
                        <div className="result-value sm">{result.batsman_prediction.possible_mode_of_dismissal ?? 'N/A'}</div>
                      </div>
                    </div>

                    <div className="info-strip red mb-3" style={{ fontSize: '0.78rem' }}>
                      <strong>Bowler Threat:</strong> {result.batsman_prediction.who_can_get_him_out ?? 'N/A'}
                    </div>

                    <div style={{ fontSize: '0.78rem', color: 'var(--text-dark)', marginBottom: 6 }}>
                      <strong>Strengths vs:</strong>
                      <div className="pill-row">
                        {(result.batsman_prediction.bowling_strength || []).map((x, i) => (
                          <span key={i} className="pill pill-green">{x}</span>
                        ))}
                      </div>
                    </div>

                    <div style={{ fontSize: '0.78rem', color: 'var(--text-dark)' }}>
                      <strong>Weaknesses vs:</strong>
                      <div className="pill-row">
                        {(result.batsman_prediction.bowling_weakness || []).map((x, i) => (
                          <span key={i} className="pill pill-red">{x}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Bowler prediction */}
                {isBowl && result.bowler_prediction && (
                  <div className="neo-raised panel-card">
                    <div className="section-head">🎯 Bowler Metrics</div>
                    <div className="result-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 12 }}>
                      <div className="result-box green" style={{ padding: '14px 12px' }}>
                        <div className="result-label">Wickets</div>
                        <div className="result-value">{result.bowler_prediction.predicted_wickets ?? 'N/A'}</div>
                      </div>
                      <div className="result-box amber" style={{ padding: '14px 12px' }}>
                        <div className="result-label">Economy</div>
                        <div className="result-value">{result.bowler_prediction.predicted_economy ?? 'N/A'}</div>
                      </div>
                      <div className="result-box" style={{ padding: '14px 12px' }}>
                        <div className="result-label">SR</div>
                        <div className="result-value">{result.bowler_prediction.success_rate ?? 'N/A'}</div>
                      </div>
                    </div>

                    <div className="info-strip mb-2" style={{ fontSize: '0.78rem' }}>
                      <strong>Match Role:</strong> {result.bowler_prediction.role_in_match ?? 'N/A'}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-dark)' }}>
                      <strong>Expected deliveries:</strong> {result.bowler_prediction.kind_of_ball_will_bowl ?? 'N/A'}
                    </div>
                  </div>
                )}
              </div>

              {/* Venue Performance History */}
              {(() => {
                const raw = result.batsman_prediction?.venue_performance_history
                  || result.bowler_prediction?.venue_performance_history;
                const venueHist = Array.isArray(raw) ? raw : (typeof raw === 'string' && raw.trim() ? [raw] : []);
                return venueHist.length > 0 ? (
                  <div className="neo-raised panel-card">
                    <div className="section-head">🏟️ Last Performances at {mVenue || 'Venue'}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {venueHist.slice(0, 5).map((entry, i) => (
                        <div key={i} style={{
                          display: 'flex', alignItems: 'center', gap: 10,
                          padding: '8px 12px', borderRadius: 10,
                          background: i % 2 === 0
                            ? 'linear-gradient(135deg, rgba(37,99,235,0.08), rgba(37,99,235,0.02))'
                            : 'linear-gradient(135deg, rgba(124,58,237,0.08), rgba(124,58,237,0.02))',
                          fontSize: '0.82rem', color: 'var(--text-dark)',
                        }}>
                          <span style={{
                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                            width: 24, height: 24, borderRadius: '50%',
                            background: 'var(--color-purple)', color: '#fff',
                            fontSize: '0.7rem', fontWeight: 800, flexShrink: 0,
                          }}>{i + 1}</span>
                          <span style={{ fontWeight: 600 }}>{entry}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null;
              })()}

              {/* Career Summary Stats */}
              {(bio.batting_summary?.rows || bio.recent_batting?.rows) && (
                <div className="neo-raised panel-card">
                  <div className="section-head">📋 Cricbuzz Career Stats</div>
                  {bio.batting_summary?.rows && (
                    <>
                      <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-gray)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>Batting Summary</div>
                      <div className="neo-table-wrap mb-4">
                        <table className="neo-table">
                          <thead>
                            <tr>{bio.batting_summary.headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
                          </thead>
                          <tbody>
                            {bio.batting_summary.rows.map((row, i) => (
                              <tr key={i}>{row.map((v, j) => <td key={j}>{v}</td>)}</tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}

                  {bio.recent_batting?.rows && (
                    <>
                      <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-gray)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>Recent Batting (Last 5)</div>
                      <div className="neo-table-wrap">
                        <table className="neo-table">
                          <thead>
                            <tr>{bio.recent_batting.headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
                          </thead>
                          <tbody>
                            {bio.recent_batting.rows.map((row, i) => (
                              <tr key={i}>{row.map((v, j) => <td key={j}>{v}</td>)}</tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Graphical radar / mapping */}
              {isBat && result.batsman_prediction && (
                <>
                  {/* Radar chart — full width so labels never clip */}
                  <div className="neo-raised panel-card chart-wrap">
                    <div className="section-head">📊 Bowling Vulnerability</div>
                    <RadarChart data={radarData()} />
                    <RadarLegend />
                  </div>

                  {/* Delivery length bar map */}
                  <div className="neo-raised panel-card">
                    <div className="section-head">📊 Delivery Length Map</div>
                    <div style={{ marginBottom: 8, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                      {[
                        { color: '#10b981', label: 'Strength — plays well' },
                        { color: '#ef4444', label: 'Weakness — vulnerable' },
                        { color: '#94a3b8', label: 'Neutral' },
                      ].map((l, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.72rem', fontWeight: 600, color: '#475569' }}>
                          <span style={{ width: 10, height: 10, borderRadius: '50%', background: l.color, flexShrink: 0 }} />
                          {l.label}
                        </div>
                      ))}
                    </div>
                    {lengthData().map((item, i) => (
                      <div key={i} className="bar-row">
                        <span className="bar-label">{item.l}</span>
                        <div className="bar-track">
                          {item.score === 1 && <div className="bar-fill-green">STRENGTH</div>}
                          {item.score === -1 && <div className="bar-fill-red">WEAKNESS</div>}
                          {item.score === 0 && <span className="bar-neutral">NEUTRAL</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}


              {/* Deep AI reasoning layer */}
              {result.reasoning_markdown && (
                <div className="neo-raised panel-card">
                  <div className="section-head">🧠 AI Reasoning &amp; Matchup Analysis</div>
                  <div className="reasoning-block">{result.reasoning_markdown}</div>
                </div>
              )}

              {/* Data web references */}
              {(() => {
                const ctx = result.scraped_context || {};
                // Collect all real (non-error) web search sources
                const webSources = ['recent_form', 'head_to_head', 'pitch_report', 'opposition_bowlers']
                  .flatMap(key => (ctx[key] || []))
                  .filter(item =>
                    item &&
                    item.url &&
                    item.url.trim() !== '' &&
                    item.title &&
                    item.title !== 'Search error'
                  );

                // Prepend the Cricbuzz profile as a verified source
                const profileUrl = ctx.profile_data?.profile_url;
                const profileName = ctx.profile_data?.name;
                const profileSources = profileUrl
                  ? [{ title: `Cricbuzz Profile — ${profileName || 'Player'}`, url: profileUrl, snippet: 'Career stats, batting/bowling style, recent form (Cricbuzz direct)' }]
                  : [];

                const allSources = [...profileSources, ...webSources];
                if (allSources.length === 0) return null;

                return (
                  <div className="neo-raised panel-card">
                    <div className="section-head">🔗 Data Sources Used</div>
                    {webSources.length === 0 && (
                      <div style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: 600, marginBottom: 8 }}>
                        ⚠️ Web search unavailable — prediction based on Cricbuzz career data only.
                      </div>
                    )}
                    <ul className="source-list">
                      {allSources.map((item, i) => (
                        <li key={i}>
                          <a className="source-link" href={item.url} target="_blank" rel="noreferrer">{item.title}</a>
                          {item.snippet && <span style={{ color: 'var(--text-gray)', fontSize: '0.72rem' }}> — {item.snippet.slice(0, 140)}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })()}

            </>
            </ResultErrorBoundary>
          )}

          {/* PLAYER COMPARE TAB */}
          {tab === 'compare' && (
            <PlayerCompare
              popularPlayers={POPULAR_PLAYERS}
              popularTeams={POPULAR_TEAMS}
              popularVenues={POPULAR_VENUES}
              models={MODELS}
            />
          )}

          {/* EMPTY STATE */}
          {!result && !(tab === 'offline' && offResult) && tab !== 'compare' && !predicting && (
            <div className="neo-raised panel-card empty-state">
              <TrendIcon />
              <div className="empty-title">No Prediction Run Yet</div>
              <div className="empty-sub">
                Configure match data in the left panel and click <strong>Analyse &amp; Predict</strong> to begin.
              </div>
            </div>
          )}

          {/* LOADING / ANALYSING STATE */}
          {predicting && (
            <AnalysingPanel logs={logs} />
          )}

        </div>

      </div>

      {/* HTML5 Datalists for user-friendly autocomplete suggestions */}
      <datalist id="popular-players-list">
        {POPULAR_PLAYERS.map(p => <option key={p} value={p} />)}
      </datalist>
      <datalist id="popular-teams-list">
        {POPULAR_TEAMS.map(t => <option key={t} value={t} />)}
      </datalist>
      <datalist id="popular-venues-list">
        {POPULAR_VENUES.map(v => <option key={v} value={v} />)}
      </datalist>
      <datalist id="offline-venue-ids-list">
        {OFFLINE_VENUE_IDS.map(vid => <option key={vid} value={vid} />)}
      </datalist>

    </div>
  );
}

