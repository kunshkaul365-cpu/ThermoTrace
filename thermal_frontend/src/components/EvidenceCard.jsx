import { useEffect, useState } from "react";

const TIER_STYLES = {
  P1: "border-red-500/30 bg-red-500/10 text-red-300",
  P2: "border-orange-500/30 bg-orange-500/10 text-orange-300",
  P3: "border-yellow-500/30 bg-yellow-500/10 text-yellow-300",
  P4: "border-green-500/30 bg-green-500/10 text-green-300",
};

function tierCode(tier) {
  const match = typeof tier === "string" && tier.match(/P[1-4]/);
  return match ? match[0] : null;
}

function FrpHistory({ sourceId }) {
  const [state, setState] = useState({ loading: true, data: null });
  const [hovered, setHovered] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setState({ loading: true, data: null });
    setHovered(null);

    fetch(`http://localhost:8000/api/assessments/${sourceId}/frp-history`)
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) setState({ loading: false, data });
      })
      .catch((err) => {
        console.error("Failed to load FRP history:", err);
        if (!cancelled) setState({ loading: false, data: { available: false, days: [] } });
      });

    return () => {
      cancelled = true;
    };
  }, [sourceId]);

  if (state.loading) {
    return <p className="text-xs text-zinc-500">Loading FRP history…</p>;
  }

  if (!state.data?.available) {
    return (
      <p className="text-xs text-zinc-500">
        FRP history unavailable for this source - no detection records found.
      </p>
    );
  }

  const days = state.data.days ?? [];
  if (days.length === 0) {
    return <p className="text-xs text-zinc-500">No detections recorded for this source yet.</p>;
  }

  const baseline = state.data.baseline_frp_mw_per_detection;
  const peak = state.data.peak_day ?? days.reduce((b, d) => (d.frp_mw_total > b.frp_mw_total ? d : b), days[0]);
  const max = Math.max(...days.map((d) => d.frp_mw_total), 1);
  const scale = (v) => (v <= 0 ? 0 : Math.sqrt(v) / Math.sqrt(max));
  const shown = hovered ?? peak;

  return (
    <div>
      <div className="flex h-20 items-end gap-[3px]">
        {days.map((d) => {
          const isPeak = d.date === peak.date && d.frp_mw_total > 0;
          const isHovered = hovered?.date === d.date;
          return (
            <div
              key={d.date}
              onMouseEnter={() => setHovered(d)}
              onMouseLeave={() => setHovered(null)}
              className={`flex-1 cursor-default rounded-t-sm transition-all duration-150 ${
                isHovered
                  ? "bg-gradient-to-t from-white to-teal-200"
                  : isPeak
                  ? "bg-gradient-to-t from-teal-400 to-emerald-300"
                  : "bg-gradient-to-t from-teal-600/70 to-teal-400/70 hover:brightness-125"
              }`}
              style={{ height: `${Math.max(scale(d.frp_mw_total) * 100, d.frp_mw_total > 0 ? 4 : 1.5)}%` }}
            />
          );
        })}
      </div>

      <div className="mt-1.5 flex items-center justify-between text-[11px] text-zinc-500">
        <span>{days[0].date}</span>
        <span>{days[days.length - 1].date}</span>
      </div>

      {}
      <div className="mt-2 rounded-md bg-black/30 px-2.5 py-2 text-[11px]">
        <div className="flex items-center justify-between text-zinc-300">
          <span className="text-zinc-500">{shown === peak ? "Peak day" : "Hovered"} · {shown.date}</span>
          <span className="font-medium text-teal-300 tabular-nums">{shown.frp_mw_total} MW total</span>
        </div>
        <div className="mt-1 flex items-center justify-between text-zinc-500">
          <span>
            {shown.detections} detection{shown.detections === 1 ? "" : "s"} · avg{" "}
            {shown.frp_mw_avg ?? 0} MW/detection
          </span>
          {typeof baseline === "number" && (
            <span>
              baseline <span className="text-zinc-400">{baseline} MW/detection</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

const EvidenceCard = ({ source, onClose }) => {
  if (!source) return null;

  const tierStyle = TIER_STYLES[tierCode(source.priority_tier)] ?? TIER_STYLES.P4;

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="font-mono text-sm text-white">{source.source_id}</h2>
        <button
          onClick={onClose}
          className="rounded-md border border-zinc-700 px-2.5 py-1 text-xs text-zinc-300 hover:border-teal-500/40 hover:text-teal-300"
        >
          Close
        </button>
      </div>

      <div className={`rounded-lg border px-3 py-2 ${tierStyle}`}>
        <p className="text-sm font-medium">{source.priority_tier ?? "—"}</p>
        <p className="mt-0.5 text-xs text-zinc-400">{source.priority_rationale}</p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2">
          <p className="text-[11px] text-zinc-500">Classification</p>
          <p className="mt-0.5 text-sm text-zinc-100">
            {source.classification ? String(source.classification).replaceAll("_", " ") : "unknown"}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2">
          <p className="text-[11px] text-zinc-500">Confidence</p>
          <p className="mt-0.5 text-sm text-zinc-100">
            {typeof source.classification_confidence === "number"
              ? (source.classification_confidence * 100).toFixed(1) + "%"
              : "N/A"}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2">
          <p className="text-[11px] text-zinc-500">Anomaly status</p>
          <p className="mt-0.5 text-sm text-zinc-100">
            {source.anomaly_status
              ? String(source.anomaly_status).replaceAll("_", " ")
              : "not assessed"}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2">
          <p className="text-[11px] text-zinc-500">Baseline</p>
          <p className="mt-0.5 text-sm text-zinc-100">{source.history?.baseline_days ?? 0} days</p>
        </div>
        <div className="col-span-2 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2">
          <p className="text-[11px] text-zinc-500">Detections</p>
          <p className="mt-0.5 text-sm text-zinc-100 tabular-nums">
            {(source.history?.detection_count ?? 0).toLocaleString("en-IN")}
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
        <p className="mb-2 text-[11px] text-zinc-500">FRP history (last 30 days)</p>
        <FrpHistory sourceId={source.source_id} />
      </div>
    </div>
  );
};

export default EvidenceCard;
