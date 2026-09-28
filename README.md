# 🔥 ThermoTrace — Thermal Anomaly Classification System

> 🛰️ **From Thermal Signals to Actionable Intelligence**

[![SIH](https://img.shields.io/badge/Smart%20India%20Hackathon-SIH%202026-orange?style=for-the-badge)](#)
[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)](#)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](#)
[![Leaflet](https://img.shields.io/badge/Leaflet-Maps-199900?logo=leaflet)](#)

## 🏆 SIH Details

* **Problem Statement:** Thermal Anomaly Classification System
* **PS ID:** SIH PS162
* **Ministry/Organization:** National Technical Research Organisation (NTRO)

## 🌍 About

**ThermoTrace** is a thermal intelligence platform that detects, classifies, and prioritizes thermal anomalies using satellite detection data, historical activity, source information, and anomaly analysis.

It provides an interactive **geospatial dashboard** to explore thermal sources, anomaly status, classification, priority, and historical FRP activity.

## 🚨 Problem

* Large volumes of thermal detections are difficult to analyze.
* Genuine anomalies can be difficult to distinguish from recurring sources.
* Raw satellite data lacks contextual information.
* Manual analysis makes prioritization difficult.

## ✨ Key Features

* 🗺️ Interactive thermal anomaly map
* 🔥 Source classification
* 📊 Anomaly & priority assessment
* ⏱️ Historical FRP analysis
* 🔎 Multi-dimensional filtering
* 🧠 Evidence-based data fusion
* ⚡ FastAPI REST APIs

## 🛠️ Tech Stack

**Frontend:** React, Vite, Tailwind CSS, Leaflet
**Backend:** Python, FastAPI, Uvicorn, Pydantic
**Data:** Pandas, Parquet
**Geospatial:** Leaflet, React Leaflet
**Analysis:** Anomaly scoring, source classification & data fusion

## 🏗️ Architecture

```text
Thermal Data
     ↓
Data Cleaning
     ↓
Source Registry
     ↓
Anomaly Analysis
     ↓
Classification
     ↓
Evidence Fusion
     ↓
FastAPI
     ↓
React + Leaflet Dashboard
```

## 🚀 Run Locally

### Backend

```bash
cd thermal_api
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd thermal_frontend
npm install
npm run dev
```

## 📈 Future Scope

* 🛰️ Live satellite data integration
* 🤖 Advanced ML models
* 🚨 Real-time alerts
* ☁️ Cloud deployment
* 🗺️ Advanced GIS layers
* 📊 Model monitoring

## 👥 Team

| Name         | Role      |
| ------------ | --------- |
| `[Member 1]` | Team Lead |
| `[Member 2]` | ML / Data |
| `[Member 3]` | Backend   |
| `[Member 4]` | Frontend  |

---

### 🛰️ ThermoTrace

**Detect • Classify • Prioritize • Visualize**

Made with ❤️ for **Smart India Hackathon**
