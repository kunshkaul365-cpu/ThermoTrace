import pandas as pd
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    df_registry = pd.read_parquet(
        BASE_DIR / "historical_source_registry_v2.parquet"
    )
    df_anomaly = pd.read_parquet(
        BASE_DIR / "m1_anomaly_sources_india.parquet"
    )
    df_classified = pd.read_parquet(
        BASE_DIR / "classified_sources.parquet"
    )

    df_registry["source_id"] = (
        df_registry["source_id"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    df_anomaly["source_id"] = (
        df_anomaly["source_id"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    df_classified["source_id"] = (
        df_classified["source_id"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    if "anomaly_status" in df_anomaly.columns:
        df_anomaly["anomaly_status"] = (
            df_anomaly["anomaly_status"]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

    if "class_label" in df_classified.columns:
        df_classified["class_label"] = (
            df_classified["class_label"]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

except Exception as e:
    print(f"Error loading Parquet files: {e}")
    df_registry = pd.DataFrame()
    df_anomaly = pd.DataFrame()
    df_classified = pd.DataFrame()

try:
    df_detections = pd.read_parquet(
        BASE_DIR / "historical_detections_with_sources_v2.parquet"
    )

    df_detections["source_id"] = (
        df_detections["source_id"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    FRP_DATA_AVAILABLE = True

except Exception as e:
    df_detections = pd.DataFrame()
    FRP_DATA_AVAILABLE = False
    print(f"historical_detections_with_sources_v2.parquet not found: {e}")


def calculate_priority(c_label, anom_status, f_dist):
    is_industrial = c_label in (
        "persistent_industrial",
        "anomalous_industrial",
    )

    if c_label == "anomalous_industrial":
        return (
            "P1 - Critical",
            "Classifier flagged this industrial source itself as anomalous.",
        )

    if is_industrial and anom_status == "high_anomaly":
        return (
            "P1 - Critical",
            "Industrial source showing a strong anomalous thermal signature.",
        )

    if anom_status == "high_anomaly":
        return (
            "P2 - High",
            "Strong anomaly detected relative to this source's own baseline.",
        )

    if is_industrial and pd.notnull(f_dist) and f_dist < 500:
        return (
            "P2 - High",
            "Activity detected very close (<500m) to a known industrial facility.",
        )

    if anom_status == "elevated":
        return (
            "P3 - Medium",
            "Activity elevated above baseline - borderline anomaly.",
        )

    if anom_status == "new_activity":
        return (
            "P3 - Medium",
            "Newly active source with limited history.",
        )

    if c_label == "agri_burn":
        return (
            "P4 - Low",
            "Standard agricultural burning detected.",
        )

    return (
        "P4 - Low",
        "Routine activity matching historical baseline.",
    )


def get_fused_assessment(source_id: str):
    try:
        source_id_str = str(source_id)

        source_b = df_registry[
            df_registry["source_id"] == source_id_str
        ]

        if source_b.empty:
            return {
                "error": f"Source {source_id} not found in registry."
            }

        source_c = df_anomaly[
            df_anomaly["source_id"] == source_id_str
        ]

        anom_status = (
            source_c["anomaly_status"].values[0]
            if not source_c.empty and "anomaly_status" in source_c.columns
            else "not_assessed"
        )

        anom_conf = (
            source_c["anomaly_score"].values[0]
            if not source_c.empty and "anomaly_score" in source_c.columns
            else 0.0
        )

        source_d = df_classified[
            df_classified["source_id"] == source_id_str
        ]

        c_label = (
            source_d["class_label"].values[0]
            if not source_d.empty and "class_label" in source_d.columns
            else "unknown"
        )

        c_conf = (
            source_d["confidence"].values[0]
            if not source_d.empty and "confidence" in source_d.columns
            else 0.0
        )

        f_dist = (
            source_d["facility_distance_m"].values[0]
            if not source_d.empty and "facility_distance_m" in source_d.columns
            else None
        )

        tier, rationale = calculate_priority(
            c_label,
            anom_status,
            f_dist,
        )

        assessment = {
            "source_id": source_id,
            "location": {
                "lat": float(source_b["centroid_lat"].values[0]),
                "lng": float(source_b["centroid_lon"].values[0]),
            },
            "history": {
                "detection_count": int(source_b["detection_count"].values[0]),
                "history_days": int(source_b["history_days"].values[0]),
                "baseline_days": int(source_b["history_days"].values[0]),
            },
            "classification": c_label,
            "classification_confidence": (
                float(c_conf) if pd.notnull(c_conf) else 0.0
            ),
            "anomaly_status": anom_status,
            "anomaly_confidence": (
                float(anom_conf) if pd.notnull(anom_conf) else 0.0
            ),
            "facility_distance_m": (
                float(f_dist) if pd.notnull(f_dist) else None
            ),
            "priority_tier": tier,
            "priority_rationale": rationale,
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

        temp_df = pd.DataFrame([assessment])
        json_str = temp_df.to_json(orient="records")

        return json.loads(json_str)[0]

    except Exception as e:
        print(f"Fusion Error for {source_id}: {e}")
        return {"error": str(e)}


def get_frp_history(source_id: str, days: int = 30):
    if not FRP_DATA_AVAILABLE or df_detections.empty:
        return {
            "available": False,
            "reason": "FRP history unavailable.",
            "days": [],
        }

    try:
        sid = str(source_id).strip()

        rows = df_detections[
            df_detections["source_id"] == sid
        ]

        if rows.empty or "frp_mw" not in rows.columns:
            return {
                "available": True,
                "days": [],
            }

        ts_col = (
            "acq_datetime_utc"
            if "acq_datetime_utc" in rows.columns
            else "acq_datetime_ist"
        )

        if ts_col not in rows.columns:
            return {
                "available": False,
                "reason": "No timestamp column found.",
                "days": [],
            }

        ts = pd.to_datetime(
            rows[ts_col],
            errors="coerce",
            utc=True,
        )

        daily = (
            rows.assign(_date=ts.dt.date)
            .dropna(subset=["_date"])
        )

        daily_grouped = (
            daily.groupby("_date")["frp_mw"]
            .agg(["sum", "mean", "count"])
            .sort_index()
        )

        if daily_grouped.empty:
            return {
                "available": True,
                "days": [],
            }

        end_date = daily_grouped.index.max()
        start_date = end_date - pd.Timedelta(days=days - 1)

        full_range = pd.date_range(
            start=start_date,
            end=end_date,
            freq="D",
        ).date

        daily_grouped = daily_grouped.reindex(
            full_range,
            fill_value=0.0,
        )

        baseline = None

        reg_row = df_registry[
            df_registry["source_id"] == sid
        ]

        if not reg_row.empty:
            for col in (
                "rolling_frp_mean",
                "history_frp_mean",
            ):
                if (
                    col in reg_row.columns
                    and pd.notnull(reg_row[col].values[0])
                ):
                    baseline = round(
                        float(reg_row[col].values[0]),
                        2,
                    )
                    break

        day_list = [
            {
                "date": str(d),
                "frp_mw_total": round(float(row["sum"]), 2),
                "frp_mw_avg": (
                    round(float(row["mean"]), 2)
                    if row["count"] > 0
                    else None
                ),
                "detections": int(row["count"]),
            }
            for d, row in daily_grouped.iterrows()
        ]

        peak = (
            max(
                day_list,
                key=lambda d: d["frp_mw_total"],
            )
            if day_list
            else None
        )

        return {
            "available": True,
            "baseline_frp_mw_per_detection": baseline,
            "peak_day": peak,
            "days": day_list,
        }

    except Exception as e:
        print(f"FRP history error for {source_id}: {e}")
        return {
            "available": False,
            "reason": str(e),
            "days": [],
        }


def get_top_assessments(limit=30):
    try:
        top_sources = (
            df_registry
            .nlargest(limit, "detection_count")["source_id"]
            .tolist()
        )

        assessments = []

        for sid in top_sources:
            result = get_fused_assessment(str(sid))

            if "error" not in result:
                assessments.append(result)

        return assessments

    except Exception as e:
        return [
            {
                "source_id": "Error",
                "error": str(e),
            }
        ]


def _enrich_active_for_selection():
    df = df_registry[
        df_registry["detection_count"] > 2
    ][
        ["source_id", "detection_count"]
    ].copy()

    df = df.merge(
        df_classified[
            [
                "source_id",
                "class_label",
                "facility_distance_m",
            ]
        ],
        on="source_id",
        how="left",
    )

    df = df.merge(
        df_anomaly[
            [
                "source_id",
                "anomaly_status",
            ]
        ],
        on="source_id",
        how="left",
    )

    df["class_label"] = df["class_label"].fillna("unknown")
    df["anomaly_status"] = df["anomaly_status"].fillna("not_assessed")

    df["priority_tier"] = df.apply(
        lambda r: calculate_priority(
            r["class_label"],
            r["anomaly_status"],
            r["facility_distance_m"],
        )[0],
        axis=1,
    )

    return df


def get_diverse_assessments(limit=200, per_bucket=8):
    try:
        enriched = _enrich_active_for_selection()

        picked_ids = []
        seen = set()

        for _, group in enriched.groupby(
            [
                "priority_tier",
                "class_label",
                "anomaly_status",
            ]
        ):
            for sid in group.nlargest(
                per_bucket,
                "detection_count",
            )["source_id"]:
                if sid not in seen:
                    seen.add(sid)
                    picked_ids.append(sid)

        if len(picked_ids) < limit:
            remaining = (
                enriched[
                    ~enriched["source_id"].isin(seen)
                ]
                .nlargest(
                    limit - len(picked_ids),
                    "detection_count",
                )
            )

            picked_ids.extend(
                remaining["source_id"].tolist()
            )

        assessments = []

        for sid in picked_ids[:limit]:
            result = get_fused_assessment(str(sid))

            if "error" not in result:
                assessments.append(result)

        assessments.sort(
            key=lambda a: a["history"]["detection_count"],
            reverse=True,
        )

        return assessments

    except Exception as e:
        print(f"Diverse Assessments Error: {e}")
        return [
            {
                "source_id": "Error",
                "error": str(e),
            }
        ]


def get_stats():
    try:
        active = df_registry[
            df_registry["detection_count"] > 2
        ]

        active_sources = int(len(active))
        total_active_detections = int(
            active["detection_count"].sum()
        )

        visible_on_map = min(
            active_sources,
            7000,
        )

        flagged_for_review = 0

        if "anomaly_status" in df_anomaly.columns:
            flagged_for_review = int(
                (
                    df_anomaly["anomaly_status"] == "elevated"
                ).sum()
            )

        return {
            "total_active_detections": total_active_detections,
            "active_sources": active_sources,
            "visible_on_map": visible_on_map,
            "flagged_for_review": flagged_for_review,
        }

    except Exception as e:
        print(f"Stats Error: {e}")
        return {"error": str(e)}


def get_all_map_sources():
    try:
        df = df_registry[
            df_registry["detection_count"] > 2
        ].copy()

        mask = (
            (df["centroid_lat"] >= 8.0)
            & (df["centroid_lat"] <= 37.5)
            & (df["centroid_lon"] >= 68.0)
            & (df["centroid_lon"] <= 97.5)
        )

        mask = mask & ~(
            (df["centroid_lat"] < 11.0)
            & (df["centroid_lon"] > 78.5)
        )

        mask = mask & ~(
            (df["centroid_lat"] < 25.0)
            & (df["centroid_lon"] < 71.0)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 25.0)
            & (df["centroid_lat"] < 28.0)
            & (df["centroid_lon"] < 73.0)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 28.0)
            & (df["centroid_lat"] < 32.0)
            & (df["centroid_lon"] < 74.0)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 32.0)
            & (df["centroid_lon"] < 75.0)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 28.5)
            & (df["centroid_lat"] < 30.5)
            & (df["centroid_lon"] >= 80.0)
            & (df["centroid_lon"] < 84.0)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 27.5)
            & (df["centroid_lat"] < 28.5)
            & (df["centroid_lon"] >= 82.0)
            & (df["centroid_lon"] < 88.0)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 26.8)
            & (df["centroid_lat"] < 27.5)
            & (df["centroid_lon"] >= 86.0)
            & (df["centroid_lon"] < 88.0)
        )

        mask = mask & ~(
            (df["centroid_lat"] > 31.0)
            & (df["centroid_lon"] > 79.5)
        )

        mask = mask & ~(
            (df["centroid_lat"] > 28.0)
            & (df["centroid_lon"] >= 82.0)
            & (df["centroid_lon"] < 91.5)
        )

        mask = mask & ~(
            (df["centroid_lat"] > 29.5)
            & (df["centroid_lon"] >= 91.5)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 21.5)
            & (df["centroid_lat"] < 23.5)
            & (df["centroid_lon"] >= 89.0)
            & (df["centroid_lon"] < 91.0)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 23.5)
            & (df["centroid_lat"] < 25.0)
            & (df["centroid_lon"] >= 89.0)
            & (df["centroid_lon"] < 90.5)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 25.0)
            & (df["centroid_lat"] < 26.2)
            & (df["centroid_lon"] >= 88.5)
            & (df["centroid_lon"] < 89.8)
        )

        mask = mask & ~(
            (df["centroid_lat"] < 21.0)
            & (df["centroid_lon"] > 93.5)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 21.0)
            & (df["centroid_lat"] < 24.0)
            & (df["centroid_lon"] > 94.8)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 24.0)
            & (df["centroid_lat"] < 26.5)
            & (df["centroid_lon"] > 95.5)
        )

        mask = mask & ~(
            (df["centroid_lat"] >= 26.5)
            & (df["centroid_lat"] < 28.0)
            & (df["centroid_lon"] > 97.5)
        )

        df = df[mask]

        if "anomaly_status" in df_anomaly.columns:
            df = df.merge(
                df_anomaly[
                    [
                        "source_id",
                        "anomaly_status",
                    ]
                ],
                on="source_id",
                how="left",
            )
        else:
            df["anomaly_status"] = "not_assessed"

        c_cols = ["source_id"]

        if "class_label" in df_classified.columns:
            c_cols.append("class_label")

        if "facility_distance_m" in df_classified.columns:
            c_cols.append("facility_distance_m")

        if len(c_cols) > 1:
            df = df.merge(
                df_classified[c_cols],
                on="source_id",
                how="left",
            )

        def get_tier(row):
            tier, _ = calculate_priority(
                row.get("class_label", "unknown"),
                row.get("anomaly_status", "not_assessed"),
                row.get("facility_distance_m", None),
            )
            return tier

        df["priority_tier"] = df.apply(
            get_tier,
            axis=1,
        )

        df_rare = df[
            df["priority_tier"].isin(
                [
                    "P1 - Critical",
                    "P3 - Medium",
                ]
            )
        ]

        df_common = df[
            df["priority_tier"].isin(
                [
                    "P2 - High",
                    "P4 - Low",
                ]
            )
        ]

        remaining_slots = 7000 - len(df_rare)

        if remaining_slots > 0:
            df_common_top = df_common.nlargest(
                remaining_slots,
                "detection_count",
            )

            df_final = pd.concat(
                [
                    df_rare,
                    df_common_top,
                ]
            )
        else:
            df_final = df_rare.head(7000)

        df_final = (
            df_final
            .sample(frac=1)
            .reset_index(drop=True)
        )

        map_data = df_final[
            [
                "source_id",
                "centroid_lat",
                "centroid_lon",
                "detection_count",
                "priority_tier",
                "class_label",
                "anomaly_status",
            ]
        ]

        map_data = map_data.rename(
            columns={
                "centroid_lat": "lat",
                "centroid_lon": "lng",
                "class_label": "classification",
            }
        )

        map_data["classification"] = (
            map_data["classification"]
            .fillna("unknown")
        )

        map_data["anomaly_status"] = (
            map_data["anomaly_status"]
            .fillna("not_assessed")
        )

        return json.loads(
            map_data.to_json(
                orient="records"
            )
        )

    except Exception as e:
        print(f"Map Data Error: {e}")
        return []
