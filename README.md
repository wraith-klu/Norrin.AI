# ⚡ Norrin AI — Sports Performance Prediction Engine

A real-time, multi-sport performance prediction and analytics platform powered by ensemble machine learning, live weather intelligence, and LLM reasoning (Google Gemini 3.6 Flash & OpenRouter fallback).

---

## 🌟 Key Features

- **🏏 Multi-Sport Prediction Models**: Supports **Cricket**, **Football**, and **NBA** with custom statistical and contextual feature engineering (rolling averages, EWMA, rest days, injury risk, home/away advantage).
- **🤖 Real-time Cricket Intelligence**:
  - Live AI predictions using **Google Gemini 3.6 Flash** with automatic fallback to **OpenRouter** models.
  - Squad scraping and matchup analysis directly from Cricbuzz squad URLs.
  - Head-to-head match simulation and player comparison.
- **⛅ Environmental & Pitch Intelligence**:
  - Real-time weather integration via WeatherAPI.com (temperature, humidity, dew factor, wind speed, pitch conditions).
  - Venue directory lookup (`seed_venues.csv`) with automatic boundary dimension parsing.
- **🎨 Modern React + Three.js Frontend**:
  - Cyberpunk-grade interactive UI with Framer Motion animations and 3D background effects via React Three Fiber.
  - Real-time model selection, confidence intervals, risk factor analysis, and breakdown charts.
- **🚀 Zero-Database Architecture**:
  - Stateless architecture using fast, memory-mapped CSV datasets and scikit-learn model bundles.
  - Zero SQLite overhead — production-ready for horizontal scaling on modern serverless/cloud platforms.

---

## 🏗️ Project Architecture

```
Black Bolt AI/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application endpoints & CORS
│   │   ├── config.py                   # Global configuration & feature schema
│   │   ├── models.py                   # Ensemble, Quantile & ML training logic
│   │   ├── components/                 # Feature engineering pipeline
│   │   ├── security/                   # Request validation & output filtering
│   │   ├── services/
│   │   │   ├── prediction_service.py   # Core ML inference engine
│   │   │   ├── realtime_cricket.py     # Gemini & OpenRouter AI prediction engine
│   │   │   ├── weather_service.py      # WeatherAPI & venue conditions loader
│   │   │   └── data_collection.py      # Data cleaning & synthetic data generator
│   │   └── tests/                      # 42 unit and integration tests (100% pass)
│   ├── data/
│   │   ├── seed_venues.csv             # Cricket venues and pitch characteristics
│   │   └── sample_player_stats.csv     # Player match dataset
│   ├── requirements.txt                # Python dependencies
│   ├── pyproject.toml                  # Backend package config
│   └── .env.example                    # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── App.jsx                     # Main application view & dashboard
│   │   ├── PlayerCompare.jsx           # Head-to-head comparison module
│   │   ├── index.css                   # Cyberpunk dark mode design system
│   │   └── main.jsx                    # React entrypoint
│   ├── vercel.json                     # Vercel SPA routing configuration
│   └── package.json                    # Frontend dependencies (React 19, Vite, Three.js)
├── render.yaml                         # Render Infrastructure as Code Blueprint
└── README.md
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+ and `npm`

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (optional but recommended)
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies and local package
pip install -r requirements.txt
pip install -e .

# Configure environment variables
copy .env.example .env
```

Open `.env` in `backend/` and set your API keys:
```env
# Google Gemini (Primary AI Engine)
GEMINI_MODEL=gemini-3.6-flash
GEMINI_API_KEY=your_gemini_api_key_here

# OpenRouter (Secondary AI Fallback)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# WeatherAPI (Optional - falls back to synthetic conditions)
WEATHER_API_KEY=your_weatherapi_key_here
```

Start the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at: `http://localhost:8000`  
Interactive Swagger docs: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install node dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend application will be live at: `http://localhost:5173`

---

## 🧪 Running Tests

The test suite covers full-pipeline training, feature extraction, real-time cricket inference, weather service, and API contracts.

```bash
cd backend
python -m pytest app/tests
```
*(Baseline: 42 passed)*

---

## 🌐 Deployment Guide

### Deploy Backend to Render

1. Log in to [Render](https://render.com) and click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name**: `black-bolt-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && pip install -e .`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Add Environment Variables:
   - `PYTHON_VERSION`: `3.10.11`
   - `GEMINI_MODEL`: `gemini-3.6-flash`
   - `GEMINI_API_KEY`: *(your key)*
   - `OPENROUTER_API_KEY`: *(your key)*
   - `WEATHER_API_KEY`: *(your key)*
5. Click **Deploy**. Note down your service URL (e.g., `https://black-bolt-backend.onrender.com`).

*(Alternatively, use the included [render.yaml](render.yaml) blueprint directly on Render).*

---

### Deploy Frontend to Vercel

1. Log in to [Vercel](https://vercel.com) and click **Add New...** > **Project**.
2. Select your repository.
3. In Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. In **Environment Variables**, add:
   - `VITE_API_URL`: `https://black-bolt-backend.onrender.com` *(your Render backend URL without trailing slash)*
5. Click **Deploy**.

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status check |
| `POST` | `/v1/predict` | Single match prediction for Cricket, Football, or NBA |
| `POST` | `/v1/predict-batch` | Batch predictions across multiple athletes |
| `POST` | `/v1/models/train` | Triggers retraining of all sport ensemble models |
| `POST` | `/v1/cricket/predict-manual` | Real-time AI cricket prediction (Gemini / OpenRouter) |
| `POST` | `/v1/cricket/predict-squad` | Real-time squad matchup prediction |
| `POST` | `/v1/cricket/compare-players` | Head-to-head two player comparison |
| `GET` | `/v1/cricket/squad` | Scrapes squad player list from Cricbuzz match URL |

---

## 🔒 Security & Best Practices

- **Zero Database Exposure**: No SQL injection surface area.
- **Strict Pydantic Input Guards**: Validates date ranges, numeric ranges, and sport schemas before inference.
- **Environment Separation**: No hardcoded API keys; all secrets reside in `.env` (ignored by Git).
- **Graceful Multi-Tier Fallbacks**: Automatically falls back across LLM providers and fallback weather states.

---

## 📄 License

This project is licensed under the MIT License.
