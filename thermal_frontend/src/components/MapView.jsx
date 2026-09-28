import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { dummyCoordsFor, AOI_CENTER } from "../utils/coords";

const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const selectedIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [32, 52],
  iconAnchor: [16, 52],
  popupAnchor: [1, -40],
  shadowSize: [52, 52],
  className: "marker-selected",
});

export default function MapView({ assessments, selectedId, onSelect }) {
  return (
    <MapContainer
      center={AOI_CENTER}
      zoom={5}
      scrollWheelZoom
      style={{ height: "100%", width: "100%" }}
    >
  <TileLayer
    url="https://mt1.google.com/vt/lyrs=m&hl=en&gl=IN&x={x}&y={y}&z={z}"
    attribution="&copy; Google Maps"
/>
      {assessments.map((row) => {
        const { lat, lon } = dummyCoordsFor(row.source_id);
        const isSelected = row.source_id === selectedId;
        return (
          <Marker
            key={row.source_id}
            position={[lat, lon]}
            icon={isSelected ? selectedIcon : defaultIcon}
            eventHandlers={{ click: () => onSelect(row) }}
          >
            <Popup>
              <strong>{row.source_id}</strong>
              <br />
              Tier: {row.priority_tier}
              <br />
              Class: {row.classification?.class_label ?? "unknown"}
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
