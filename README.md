# AEGIS — Autonomous Cyber-Defense Platform

> **AI-Powered Threat Detection, Prediction & Autonomous Response**

[![Live Dashboard](https://img.shields.io/badge/Dashboard-Live-brightgreen)](https://aegis-ph9ui09ar-astrophage2.vercel.app/)
[![Backend](https://img.shields.io/badge/API-Online-blue)](https://aegis-api-hqnx.onrender.com/api/health)
[![License](https://img.shields.io/badge/License-Proprietary-red)]()
[![Stage](https://img.shields.io/badge/Current%20Stage-1-cyan)]()
[![Built With](https://img.shields.io/badge/Built%20With-FastAPI%20%7C%20React%20%7C%20ML-purple)]()

---

## What is AEGIS?

AEGIS is a full-stack, AI-powered cybersecurity platform that monitors network traffic in real time, predicts cyberattacks before they escalate, and autonomously recommends and executes defense actions — all through a live dashboard.

It processes raw network data through a **7-phase AI pipeline** — from packet ingestion to live defense execution — validated across **15 real-world network datasets** with live ML inference and a complete audit trail for every action taken.

---

## The Problem AEGIS Solves

Traditional security tools are **reactive** — they alert you after a breach has already happened. By then, data is stolen and damage is done.

AEGIS is **predictive and autonomous**:
- Detects attacks **before** they escalate
- Scores risk **every minute** using a deterministic ensemble
- Maps attacks to **MITRE ATT&CK** techniques automatically
- Simulates defense outcomes **before** committing to action
- Executes defense commands **autonomously** when authorized

---

## Live Demo

| Resource | URL |
|---|---|
| Frontend (Vercel) | https://aegis-ph9ui09ar-astrophage2.vercel.app/ |
| Backend API (Render) | https://aegis-api-hqnx.onrender.com |
| API Health Check | https://aegis-api-hqnx.onrender.com/api/health |

> **Note:** Backend is hosted on Render free tier — first request may take 15–30 seconds to wake the instance.

---

## The 7-Phase Pipeline

Every piece of data in AEGIS flows through a strict 7-phase pipeline. Each phase builds on the last — raw traffic becomes a risk score, which becomes an episode, which becomes a defense action.

| Phase | Name | What It Does |
|---|---|---|
| P1 | Continuous Ingestion | Reads raw network traffic minute by minute, filling gaps where no data was captured |
| P2 | Escalation Forecast | Predicts the probability that an attack will worsen using a GRU neural network |
| P3 | Deterministic Risk Scoring | Combines forecast, activity, speed, and persistence into a 0–100 risk score |
| P4 | Investigation & MITRE ATT&CK | Groups attack windows into episodes and maps them to real-world attack techniques |
| P5 | Historical Memory | Compares the current attack to past episodes using FAISS vector similarity |
| P6A | Counterfactual Simulation | Simulates what would happen if each defense action was applied |
| P6B | Active Defense Execution | Dispatches firewall, VLAN, and traffic control commands when authorized |
| P7 | Live Lab Verification | Captures post-defense telemetry to confirm the attack was contained |

---

## Dashboard

| Section | Description |
|---|---|
| Command Center | Main overview — KPI cards, risk timeline, active threat summary |
| Network Activity | Raw traffic flows per minute — benign vs malicious connections |
| Attack Forecast | Escalation probability chart across time windows |
| Risk Monitor | Current threat level: LOW / MEDIUM / HIGH / CRITICAL |
| Attack Events | Forensic dossiers for each detected attack episode |
| Attack Techniques | MITRE ATT&CK matrix — maps attacks to real-world techniques |
| What-If Scenarios | Simulates each defense action before execution |
| Response Actions | Dispatches isolation, throttling, and packet drop commands |
| Historical Memory | Compares current attack to similar past episodes |
| Live Feed | Real-time network tick stream updated every 5 seconds |
| Data Pipeline | Source code contracts for each of the 7 phases |
| Model Registry | Status of all active ML models powering the platform |

---

## ML Models

| Model | Role | Performance |
|---|---|---|
| GRU v3 (Calibrated) | Primary Escalation Forecaster | AUROC 0.91 (LODO mean) |
| Random Forest (Tuned) | Escalation Classifier & Fallback | F1 Score 0.87 |
| Delta Forecaster (LSTM) | Attack-Rate Change Predictor | MAE 0.031 (normalised delta) |
| Risk Ensemble Engine | Deterministic Risk Scorer | 0–100 risk index, < 0.1ms |
| FAISS Episode Memory | Historical Similarity Retrieval | Top-3 recall 0.89 |

> All models trained on CIC-IDS2018 corpus with leave-one-dataset-out (LODO) cross-validation.

---

## Datasets

| Dataset | Description |
|---|---|
| CIC-IDS2017 | Canadian Institute for Cybersecurity IDS 2017 |
| CIC-IDS2018 | CIC IDS 2018 — 9 day-splits (Feb 14 – Mar 02) |
| CIC-IoT-DIAD-2024 | IoT device intrusion and anomaly detection dataset |
| CIC-BCCC-TabularIoT-2024 | Tabular IoT network traffic dataset |
| CIC-APT-IIoT-2024 | Advanced Persistent Threat on IIoT networks |

---

## Tech Stack

### Frontend
- **React + TypeScript** — component-based UI
- **Tailwind CSS** — utility-first styling
- **Zustand** — global state management
- **Recharts** — network timeline and forecast charts
- **Vercel** — deployment and CDN

### Backend
- **FastAPI (Python)** — REST API, 13 endpoints
- **pandas + numpy** — data processing
- **scikit-learn + joblib** — model inference
- **Render** — cloud deployment

### Machine Learning
- **scikit-learn** — Random Forest classifier
- **PyTorch** — GRU and LSTM models
- **FAISS** — vector similarity index for episode memory

---

## Project Structure

```
AEGIS/
├── api.py                          # FastAPI backend — all endpoints
├── src/
│   ├── inference.py                # RF model inference
│   ├── live_replay.py              # CSV-based live tick engine
│   └── pcap_replay.py              # PCAP feature replay engine
├── models/
│   ├── aegis_escalation_rf.joblib  # Trained Random Forest model
│   └── feature_schema.json         # Feature schema for inference
├── data/
│   ├── processed/                  # Temporal continuous CSVs (Phase 1)
│   ├── final_forecasts/            # Forecast CSVs (Phase 2)
│   └── pcap_features/              # PCAP feature CSVs for live feed
├── outputs/
│   ├── incident_records/           # Per-dataset incident JSON files
│   ├── phase4_investigations/      # Episode dossiers (Phase 4)
│   ├── phase5_memory/              # Historical memory store (Phase 5)
│   ├── phase6_simulations/         # Counterfactual simulation results
│   ├── phase6b_executions/         # Defense execution records
│   └── phase7_executions/          # Live lab verification records
└── frontend/
    └── src/
        ├── api/client.ts           # Central API fetch wrapper
        ├── components/             # All React components
        ├── context/useAegisStore.ts # Zustand global store
        ├── hooks/useLiveTick.ts    # Live polling hook (5s interval)
        └── types/aegis.ts          # TypeScript type definitions
```

---

## API Endpoints

All endpoints require `X-API-Key` header except `/api/health`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check — no auth required |
| GET | `/api/datasets` | List all available datasets with phase flags |
| GET | `/api/network-state` | Temporal network state CSV (Phase 1) |
| GET | `/api/forecasts` | Escalation forecast CSV (Phase 2) |
| GET | `/api/incidents` | Incident records JSON (Phase 3) |
| GET | `/api/episodes` | Investigation episodes JSON (Phase 4) |
| GET | `/api/memory` | Historical memory store (Phase 5) |
| GET | `/api/simulations` | Counterfactual simulation results (Phase 6A) |
| GET | `/api/executions` | Defense execution records (Phase 6B) |
| GET | `/api/live/tick` | Live CSV replay tick |
| GET | `/api/live/status` | Live replay status |
| POST | `/api/live/reset` | Reset live replay cursor |
| GET | `/api/pcap/tick` | PCAP feature replay tick |

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### Backend

```bash
cd AEGIS-local
pip install -r requirements.txt
python api.py
# Backend runs at http://localhost:8000
```

### Frontend

```bash
cd AEGIS-local/frontend
npm install
npm run dev
# UI runs at http://localhost:5175
```

### Environment Variables

Create `frontend/.env.local`:
```
VITE_API_URL=http://localhost:8000
VITE_API_KEY=dev-insecure-key
```

---

## Results

| Metric | Value |
|---|---|
| Escalation Forecast AUROC | 0.91 (LODO cross-validation) |
| Binary Classification F1 | 0.87 |
| Inference Latency | < 5ms end-to-end |
| Temporal Resolution | 1-minute windows |
| Datasets Validated | 15 |
| Historical Memory Records | 258+ |
| Defense Actions Audited | Full immutable log |
| MITRE ATT&CK Coverage | Auto-mapped per episode |

---

## Current Stage

**Autonomous Cyber-Defense Pipeline**

A fully working end-to-end platform covering all 7 phases of the pipeline, 15 real-world datasets, live ML inference, a complete dashboard, and a full audit trail for every defense action taken.

---

## License

Copyright (c) 2024 Gitanshu Tule and Vishuddhi Waykos. All rights reserved.

This software and its source code are the exclusive property of Gitanshu Tule and Vishuddhi Waykos. Unauthorized use, copying, modification, or distribution of this software, via any medium, is strictly prohibited. See the `LICENSE` file for full terms.

---

## Acknowledgements

- Datasets provided by the **Canadian Institute for Cybersecurity (CIC)** at the University of New Brunswick
- MITRE ATT&CK framework by **The MITRE Corporation**
- Built with FastAPI, React, scikit-learn, and FAISS

---

<div align="center">
  <b>AEGIS — Autonomous Cyber-Defense Platform</b><br/>
  Built by Gitanshu Tule & Vishuddhi Waykos
</div>
