import { useState, useMemo, useCallback, useEffect } from "react";
import { MapContainer, TileLayer, Marker, ZoomControl, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import useSupercluster from "use-supercluster";
import useSWR from "swr";

const API_URL = "https://thermo-trace.vercel.app/api/thermal-sources";

const fetcher = (url) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    return res.json();
  });

const LEGEND = [
  { label: "P1 · Critical", color: "#ef4444" },
  { label: "P2 · High", color: "#f97316" },
  { label: "P3 · Medium", color: "#eab308" },
  { label: "P4 · Low", color: "#22c55e" },
];

function tierCode(tier) {
  const match = typeof tier === "string" && tier.match(/P[1-4]/);
  return match ? match[0] : null;
}

function matchesFilters(row, filters) {
  if (!filters) return true;
  const { tiers, fireTypes, anomalyStatuses } = filters;
  if (tiers?.size > 0 && !tiers.has(tierCode(row.priority_tier))) return false;
  if (fireTypes?.size > 0 && !fireTypes.has(row.classification)) return false;
  if (anomalyStatuses?.size > 0 && !anomalyStatuses.has(row.anomaly_status)) return false;
  return true;
}

function buildClusterIcon(pointCount) {
  let size = 30;
  if (pointCount >= 1000) size = 50;
  else if (pointCount >= 100) size = 40;
  const bg =
    pointCount >= 1000
      ? "rgba(139, 0, 0, 0.85)"
      : pointCount >= 100
      ? "rgba(178, 34, 34, 0.8)"
      : "rgba(220, 20, 60, 0.75)";

  return L.divIcon({
    html: `<div style="
        width: ${size}px;
        height: ${size}px;
        background: ${bg};
        border: 2px solid #fff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 600;
        font-family: sans-serif;
        font-size: ${size >= 50 ? 15 : size >= 40 ? 13 : 12}px;
        box-shadow: 0 0 6px rgba(0,0,0,0.4);
      ">${pointCount}</div>`,
    className: "thermal-cluster-icon",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function buildPointIcon(priorityTier) {
  let color = "#22c55e"; 

  if (!priorityTier) color = "#9ca3af";
  else if (priorityTier.includes("P1")) color = "#ef4444";
  else if (priorityTier.includes("P2")) color = "#f97316";
  else if (priorityTier.includes("P3")) color = "#eab308";

  return L.divIcon({
    html: `<div style="
        width: 12px;
        height: 12px;
        background: ${color};
        border: 1.5px solid #fff;
        border-radius: 50%;
        box-shadow: 0 0 3px rgba(0,0,0,0.5);
      "></div>`,
    className: "thermal-point-icon",
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
}

function ClusterLayer({ points, onSourceClick }) {
  const map = useMap();
  const [bounds, setBounds] = useState(null);
  const [zoom, setZoom] = useState(map.getZoom());

  const updateMapState = useCallback(() => {
    const b = map.getBounds();
    setBounds([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]);
    setZoom(map.getZoom());
  }, [map]);

  useMapEvents({
    moveend: updateMapState,
    zoomend: updateMapState,
    load: updateMapState,
  });

  useMemo(() => {
    if (!bounds) {
      const b = map.getBounds();
      setBounds([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]);
    }
  }, []);

  const { clusters, supercluster } = useSupercluster({
    points,
    bounds,
    zoom,
    options: { radius: 75, maxZoom: 18 },
  });

  return (
    <>
      {clusters.map((cluster) => {
        const [lng, lat] = cluster.geometry.coordinates;
        const { cluster: isCluster, point_count: pointCount } = cluster.properties;

        if (isCluster) {
          return (
            <Marker
              key={`cluster-${cluster.id}`}
              position={[lat, lng]}
              icon={buildClusterIcon(pointCount)}
              eventHandlers={{
                click: () => {
                  const expansionZoom = Math.min(
                    supercluster.getClusterExpansionZoom(cluster.id),
                    18
                  );
                  map.flyTo([lat, lng], expansionZoom, { duration: 0.5 });
                },
              }}
            />
          );
        }

        const source = cluster.properties;
        return (
          <Marker
            key={`source-${source.source_id}`}
            position={[lat, lng]}
            icon={buildPointIcon(source.priority_tier)}
            eventHandlers={{
              click: () => onSourceClick?.(source),
            }}
          ></Marker>
        );
      })}
    </>
  );
}

function MapLegend() {
  return (
    <ul className="absolute bottom-4 left-4 z-[1000] flex flex-col gap-1.5">
      {LEGEND.map((item) => (
        <li key={item.label} className="flex items-center gap-2">
          <span
            className="h-2.5 w-2.5 shrink-0 rounded-full ring-1 ring-black/40"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-xs font-medium text-white [text-shadow:0_1px_3px_rgb(0_0_0_/_0.9)]">
            {item.label}
          </span>
        </li>
      ))}
    </ul>
  );
}

export default function ThermalMap({ onSourceClick, filters, onCountChange }) {
  const { data, error, isLoading } = useSWR(API_URL, fetcher, {
    revalidateOnFocus: false,
  });

  const points = useMemo(() => {
    if (!Array.isArray(data)) return [];
    return data
      .filter((row) => matchesFilters(row, filters))
      .map((row) => ({
        type: "Feature",
        properties: {
          cluster: false,
          source_id: row.source_id,
          detection_count: row.detection_count,
          priority_tier: row.priority_tier,
          classification: row.classification,
          anomaly_status: row.anomaly_status,
        },
        geometry: {
          type: "Point",
          coordinates: [row.lng, row.lat],
        },
      }));
  }, [data, filters]);

  useEffect(() => {
    if (error) console.error("Failed to load /api/thermal-sources:", error);
  }, [error]);

  useEffect(() => {
    onCountChange?.(isLoading ? null : points.length);
  }, [points.length, isLoading, onCountChange]);

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={[20.5937, 78.9629]}
        zoom={5}
        scrollWheelZoom
        zoomControl={false}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <ZoomControl position="bottomright" />
        {points.length > 0 && <ClusterLayer points={points} onSourceClick={onSourceClick} />}
      </MapContainer>

      <MapLegend />
    </div>
  );
}
