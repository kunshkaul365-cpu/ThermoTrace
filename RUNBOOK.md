# RUNBOOK.md — SIH PS162: Thermal Anomaly Classification System

## Team Roles & Ownership

### M1 — Data & Temporal Engine
- Raw thermal/satellite data ingestion
- Cleaning, deduplication, geolocation snapping
- Temporal engine (persistence, recurrence, time-series windows)
- Owns: **Handoff A**, **Handoff B**

### M2 — Context, ML & Validation
- Contextual enrichment (land use, industrial zones, known source metadata)
- ML model: anomaly scoring & source classification
- Model validation, precision/recall tracking, false-positive audits
- Owns: **Handoff C**, **Handoff D**

### M3 — Product & Integration
- API design & delivery (`ThermalSourceAssessment`)
- End-to-end pipeline integration across A → E
- Frontend/consumer-facing output, docs, deployment
- Owns: **Handoff E**

---

## Handoff Checklist

### Handoff A — `detections_clean`
- [ ] Raw hotspot data ingested (source, timestamp, lat/lon, confidence)
- [ ] Duplicate detections merged
- [ ] Invalid/low-confidence rows filtered
- [ ] Schema validated against agreed contract
- [ ] Output file/table published to shared storage

### Handoff B — `source_registry`
- [ ] Known source metadata compiled (industrial, volcanic, agricultural, etc.)
- [ ] Registry schema finalized (id, type, coordinates, tags)
- [ ] Registry deduplicated & geo-indexed
- [ ] Handoff to M2 for contextual join
- [ ] Version tagged

### Handoff C — `anomaly_scores`
- [ ] Detections joined with source registry context
- [ ] Anomaly scoring model run on `detections_clean`
- [ ] Score range & thresholds documented
- [ ] Output includes confidence + explainability fields
- [ ] Validated against sample ground truth

### Handoff D — `classified_sources`
- [ ] Anomaly scores mapped to source classes
- [ ] Classification labels finalized (e.g., industrial/fire/gas-flare/unknown)
- [ ] Validation metrics logged (precision, recall, F1)
- [ ] Edge cases / low-confidence flagged
- [ ] Output schema locked for API consumption

### Handoff E — `ThermalSourceAssessment` API
- [ ] API contract defined (request/response schema)
- [ ] `classified_sources` wired into API layer
- [ ] Error handling & fallback states implemented
- [ ] Endpoint tested (unit + integration)
- [ ] Deployed & documented for external consumption
