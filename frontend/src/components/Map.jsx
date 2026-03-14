import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { ExternalLink } from "lucide-react";

// Fix icônes Leaflet avec Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Icônes colorées par tranche de prix
function createPriceIcon(price) {
  let color;
  if (!price) color = "#6b7280";
  else if (price < 200000) color = "#16a34a";
  else if (price < 400000) color = "#ea580c";
  else color = "#dc2626";

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="24" height="36">
      <path fill="${color}" stroke="white" stroke-width="1.5"
        d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24S24 21 24 12C24 5.4 18.6 0 12 0z"/>
      <circle cx="12" cy="12" r="5" fill="white"/>
    </svg>`;

  return L.divIcon({
    className: "",
    html: svg,
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -36],
  });
}

function formatPrice(price) {
  if (!price) return "Prix NC";
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(price);
}

// Composant pour centrer la carte sur le bien sélectionné
function FlyToSelected({ properties, selectedId }) {
  const map = useMap();
  useEffect(() => {
    if (!selectedId) return;
    const prop = properties.find((p) => p.id === selectedId);
    if (prop?.latitude && prop?.longitude) {
      map.flyTo([prop.latitude, prop.longitude], 15, { duration: 1 });
    }
  }, [selectedId, properties, map]);
  return null;
}

// Centre de la Normandie (Rouen)
const NORMANDIE_CENTER = [49.44, 1.09];
const DEFAULT_ZOOM = 9;

export default function Map({ properties, selectedId, onSelect }) {
  const validProperties = properties.filter((p) => p.latitude && p.longitude);

  return (
    <MapContainer
      center={NORMANDIE_CENTER}
      zoom={DEFAULT_ZOOM}
      className="w-full h-full"
      style={{ zIndex: 0 }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <FlyToSelected properties={properties} selectedId={selectedId} />

      {validProperties.map((prop) => (
        <Marker
          key={prop.id}
          position={[prop.latitude, prop.longitude]}
          icon={createPriceIcon(prop.price)}
          eventHandlers={{
            click: () => onSelect(prop.id === selectedId ? null : prop.id),
          }}
        >
          <Popup maxWidth={260}>
            <div className="text-sm font-sans">
              <p className="font-semibold text-gray-800 mb-1 leading-tight">{prop.title}</p>
              <p className="text-lg font-bold text-blue-700 mb-1">{formatPrice(prop.price)}</p>
              {prop.city && (
                <p className="text-xs text-gray-500 mb-1">📍 {prop.city}</p>
              )}
              <div className="flex gap-2 mb-1 text-xs text-gray-600">
                {prop.surface && <span>🏠 {prop.surface} m²</span>}
                {prop.exterior_surface && <span>🌿 {prop.exterior_surface} m²</span>}
                {prop.rooms && <span>🛏 {prop.rooms} p.</span>}
              </div>
              {prop.nearest_train_min && (
                <p className="text-xs text-blue-600">
                  🚂 Gare : {Math.round(prop.nearest_train_min)} min à pied — {prop.nearest_train_name}
                </p>
              )}
              {prop.nearest_bus_min && (
                <p className="text-xs text-purple-600">
                  🚌 Bus : {Math.round(prop.nearest_bus_min)} min — {prop.nearest_bus_name}
                </p>
              )}
              <a
                href={prop.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-xs text-blue-500 hover:underline"
              >
                Voir l'annonce ↗
              </a>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
