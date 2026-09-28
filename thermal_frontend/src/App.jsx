import { useState } from "react";
import "leaflet/dist/leaflet.css";
import EvidenceCard from "./components/EvidenceCard";
import ThermalMap from "./components/ThermalMap";

const TIER_OPTIONS = [
  { value: "P1", label: "P1 · Critical" },
  { value: "P2", label: "P2 · High" },
  { value: "P3", label: "P3 · Medium" },
  { value: "P4", label: "P4 · Low" },
];

const FIRE_TYPE_OPTIONS = [
  { value: "persistent_industrial", label: "Persistent industrial" },
  { value: "anomalous_industrial", label: "Anomalous industrial" },
  { value: "agri_burn", label: "Agricultural burning" },
];

const ANOMALY_OPTIONS = [
  { value: "high_anomaly", label: "High anomaly" },
  { value: "elevated", label: "Elevated" },
  { value: "new_activity", label: "New activity" },
  { value: "not_assessed", label: "Not yet assessed" },
];

function FilterGroup({ title, options, selected, onToggle }) {
  return (
    <div>
      <p className="text-[11px] font-medium tracking-wide text-zinc-500">{title}</p>
      <div className="mt-1.5 flex flex-wrap gap-1.5">
        {options.map((opt) => {
          const isActive = selected.has(opt.value);
          return (
            <button
              key={opt.value}
              onClick={() => onToggle(opt.value)}
              className={`rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors ${
                isActive
                  ? "border-teal-500/40 bg-teal-500/10 text-teal-300"
                  : "border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function FilterPanel({ filters, setFilters }) {
  const anyActive =
    filters.tiers.size > 0 || filters.fireTypes.size > 0 || filters.anomalyStatuses.size > 0;

  function toggle(group, value) {
    setFilters((prev) => {
      const next = new Set(prev[group]);
      next.has(value) ? next.delete(value) : next.add(value);
      return { ...prev, [group]: next };
    });
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-zinc-200">Filters</p>
        {anyActive && (
          <button
            onClick={() => setFilters({ tiers: new Set(), fireTypes: new Set(), anomalyStatuses: new Set() })}
            className="text-[11px] text-teal-400 hover:text-teal-300"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="mt-3 flex flex-col gap-3">
        <FilterGroup
          title="Priority tier"
          options={TIER_OPTIONS}
          selected={filters.tiers}
          onToggle={(v) => toggle("tiers", v)}
        />
        <FilterGroup
          title="Fire type"
          options={FIRE_TYPE_OPTIONS}
          selected={filters.fireTypes}
          onToggle={(v) => toggle("fireTypes", v)}
        />
        <FilterGroup
          title="Anomaly status"
          options={ANOMALY_OPTIONS}
          selected={filters.anomalyStatuses}
          onToggle={(v) => toggle("anomalyStatuses", v)}
        />
      </div>
    </div>
  );
}

export default function App() {
  const [selectedItem, setSelectedItem] = useState(null);
  const [mapCount, setMapCount] = useState(null);
  const [filters, setFilters] = useState({
    tiers: new Set(),
    fireTypes: new Set(),
    anomalyStatuses: new Set(),
  });

  return (
    <div className="flex h-screen w-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex shrink-0 items-center border-b border-zinc-800 bg-zinc-950 px-6 py-4">
        <h1 className="font-display text-xl font-semibold tracking-tight text-white">
          Thermo<span className="text-teal-400">Trace</span>
        </h1>
      </header>

      <main className="flex min-h-0 flex-1 flex-col-reverse md:flex-row">
        {}
        <div className="flex w-full shrink-0 flex-col gap-4 overflow-y-auto border-t border-zinc-800 bg-zinc-950 p-4 md:w-[380px] md:border-t-0 md:border-r">
          <FilterPanel filters={filters} setFilters={setFilters} />

          <div className="min-h-0 flex-1">
            {selectedItem ? (
              <EvidenceCard source={selectedItem} onClose={() => setSelectedItem(null)} />
            ) : (
              <p className="px-1 pt-2 text-sm text-zinc-600">
                Click a point on the map to see its details.
              </p>
            )}
          </div>
        </div>

        {}
        <div className="flex min-h-[320px] flex-1 flex-col">
          <div className="flex shrink-0 items-center gap-2 border-b border-zinc-800 bg-zinc-950 px-4 py-2.5">
            <span
              className={`h-2 w-2 shrink-0 rounded-full bg-teal-400 ${
                mapCount !== null ? "animate-pulse" : "opacity-30"
              }`}
            />
            <span className="text-sm text-zinc-300">
              {mapCount !== null ? (
                <>
                  <span className="font-semibold text-white tabular-nums">
                    {mapCount.toLocaleString("en-IN")}
                  </span>{" "}
                  points on map
                </>
              ) : (
                "Loading points…"
              )}
            </span>
          </div>
          <div className="relative min-h-0 flex-1">
            <ThermalMap
              filters={filters}
              onCountChange={setMapCount}
              onSourceClick={async (sourceData) => {
                try {
                  const response = await fetch(
                    `http://localhost:8000/api/assessments/${sourceData.source_id}`
                  );
                  if (!response.ok) {
                    const body = await response.json().catch(() => ({}));
                    console.error("Backend error:", body.detail ?? response.status);
                    setSelectedItem(sourceData);
                    return;
                  }
                  setSelectedItem(await response.json());
                } catch (err) {
                  console.error("API call failed:", err);
                  setSelectedItem(sourceData);
                }
              }}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
