from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from config import settings
from schemas import (
    AnomalyScore,
    AnomalyType,
    AssessmentStatus,
    ClassifiedSource,
    ClassLabel,
    CoverageStatus,
    PriorityTier,
    ThermalSourceAssessment,
)

_FACILITY_NAMES = [
    "Jamnagar Refinery Complex",
    "Bokaro Steel Plant",
    "Vizag Steel Plant",
    "Paradip Industrial Cluster",
    "Barmer Oil Field",
    None,  
]

_LAND_COVER_CLASSES = ["cropland", "built_up", "barren", "forest", "grassland", "wetland"]

_FEATURE_POOL = [
    "frp_p95", "brightness_temp_std", "detection_frequency", "nighttime_persistence",
    "seasonal_deviation", "cluster_compactness", "sensor_agreement", "vnf_bt_delta",
    "distance_to_known_facility", "diurnal_pattern_score",
]


def _random_class_probs(rng: random.Random, winner: ClassLabel) -> dict:
    labels = list(ClassLabel)
    raw = {lbl.value: rng.random() for lbl in labels}
    raw[winner.value] += 1.5
    total = sum(raw.values())
    return {k: round(v / total, 4) for k, v in raw.items()}


def _priority_rationale(tier: PriorityTier, anomaly_type: AnomalyType, class_label: ClassLabel) -> str:
    return (
        f"{tier.value} priority: {anomaly_type.value.replace('_', ' ')} thermal anomaly "
        f"on a source classified as {class_label.value.replace('_', ' ')}."
    )


def make_assessment(rng: random.Random, index: int, as_of: datetime) -> ThermalSourceAssessment:
    source_id = f"SRC-{index:05d}"
    class_label = rng.choice(list(ClassLabel))
    anomaly_type = rng.choice(list(AnomalyType))
    priority_tier = rng.choices(
        list(PriorityTier), weights=[1, 2, 3, 2], k=1  # P1 rarest, P2/P3 common
    )[0]
    assessment_status = rng.choices(
        list(AssessmentStatus), weights=[7, 2, 1], k=1
    )[0]

    facility_name = rng.choice(_FACILITY_NAMES) if class_label in (
        ClassLabel.INDUSTRIAL, ClassLabel.GAS_FLARE
    ) else None

    classification = ClassifiedSource(
        source_id=source_id,
        class_label=class_label,
        class_probs=_random_class_probs(rng, class_label),
        top_features=rng.sample(_FEATURE_POOL, k=rng.randint(2, 4)),
        facility_name=facility_name,
        facility_distance_m=round(rng.uniform(10, 5000), 1) if facility_name else None,
        land_cover_class=rng.choice(_LAND_COVER_CLASSES),
        vnf_bt_match=rng.choice([True, False, None]),
        confidence=round(rng.uniform(0.4, 0.99), 3),
        assessment_status=assessment_status,
    )

    anomaly = AnomalyScore(
        source_id=source_id,
        as_of_date=as_of.date(),
        anomaly_type=anomaly_type,
        statistic=round(rng.uniform(-3, 6), 2),
        confidence=round(rng.uniform(0.3, 0.99), 3),
        coverage_status=rng.choices(list(CoverageStatus), weights=[6, 3, 1], k=1)[0],
        baseline_days=rng.choice([7, 14, 30, 60, 90]),
    )

    return ThermalSourceAssessment(
        source_id=source_id,
        classification=classification,
        anomaly=anomaly,
        evidence_complete=assessment_status == AssessmentStatus.COMPLETE,
        priority_tier=priority_tier,
        priority_rationale=_priority_rationale(priority_tier, anomaly_type, class_label),
        last_updated=as_of - timedelta(minutes=rng.randint(0, 6 * 60)),
    )


def generate(count: int, seed: int) -> List[ThermalSourceAssessment]:
    rng = random.Random(seed)
    as_of = datetime.now(timezone.utc)
    return [make_assessment(rng, i + 1, as_of) for i in range(count)]


def write_fixture(count: int, seed: int, out_path: Path) -> Path:
    rows = generate(count, seed)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [row.model_dump(mode="json") for row in rows]
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=30, help="Number of rows to generate (20-50 recommended)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed, for reproducible fixtures")
    parser.add_argument("--out", type=str, default=settings.sample_data_path, help="Output JSON path")
    args = parser.parse_args()

    if not (20 <= args.count <= 50):
        parser.error("--count should be between 20 and 50 to match the fixture spec")

    out_path = write_fixture(args.count, args.seed, Path(args.out))
    print(f"Wrote {args.count} mock ThermalSourceAssessment rows to {out_path}")


if __name__ == "__main__":
    main()
