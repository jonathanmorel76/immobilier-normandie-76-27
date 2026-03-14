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

// SVG paths pour chaque type de bien (centrés dans un cercle de rayon 5 à cx=12, cy=11)
const TYPE_ICONS = {
  // Maison : toit triangulaire + corps
  maison: `<path d="M12 6 L8 10 L8 15 L16 15 L16 10 Z" fill="white" stroke="none"/>
            <path d="M12 6 L7 10.5 L8 10.5 L8 15 L11 15 L11 12 L13 12 L13 15 L16 15 L16 10.5 L17 10.5 Z" fill="white" stroke="none" stroke-width="0.3"/>`,
  // Appartement / Immeuble : building
  appartement: `<path d="M8 7 L8 16 L16 16 L16 7 Z" fill="white" stroke="none"/>
                 <rect x="9.5" y="8.5" width="2" height="1.5" rx="0.2" fill="currentColor" opacity="0.5"/>
                 <rect x="12.5" y="8.5" width="2" height="1.5" rx="0.2" fill="currentColor" opacity="0.5"/>
                 <rect x="9.5" y="11.5" width="2" height="1.5" rx="0.2" fill="currentColor" opacity="0.5"/>
                 <rect x="12.5" y="11.5" width="2" height="1.5" rx="0.2" fill="currentColor" opacity="0.5"/>
                 <rect x="11" y="14" width="2" height="2" rx="0.2" fill="currentColor" opacity="0.5"/>`,
  // Terrain : arbre + sol
  terrain: `<circle cx="12" cy="9" r="3" fill="white" stroke="none"/>
            <rect x="11.3" y="11.5" width="1.4" height="3" rx="0.3" fill="white"/>
            <rect x="8" y="14.5" width="8" height="1" rx="0.5" fill="white" opacity="0.6"/>`,
  // Parking : lettre P
  parking: `<text x="12" y="15" text-anchor="middle" font-size="10" font-weight="bold" fill="white" font-family="sans-serif">P</text>`,
  // Défaut : point
  default: `<circle cx="12" cy="12" r="4" fill="white"/>`,
};

// Détecter le type de bien à partir du champ property_type
function getTypeKey(propertyType) {
  if (!propertyType) return "default";
  const t = propertyType.toLowerCase();
  if (t.includes("maison")) return "maison";
  if (t.includes("appartement") || t.includes("appart")) return "appartement";
  if (t.includes("immeuble")) return "appartement";
  if (t.includes("terrain")) return "terrain";
  if (t.includes("parking") || t.includes("garage")) return "parking";
  if (t.includes("local") || t.includes("commerce")) return "appartement";
  return "default";
}

// Icônes par type de bien + couleur par prix
function createPropertyIcon(price, propertyType) {
  let color;
  if (!price) color = "#78716c"; // stone-500
  else if (price < 200000) color = "#16a34a";
  else if (price < 400000) color = "#d97706";
  else color = "#dc2626";

  const typeKey = getTypeKey(propertyType);
  const innerIcon = TYPE_ICONS[typeKey] || TYPE_ICONS.default;

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="28" height="40">
      <filter id="s" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="1" stdDeviation="1" flood-opacity="0.25"/>
      </filter>
      <path filter="url(#s)" fill="${color}" stroke="white" stroke-width="1.5"
        d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24S24 21 24 12C24 5.4 18.6 0 12 0z"/>
      <g style="color:${color}">${innerIcon}</g>
    </svg>`;

  return L.divIcon({
    className: "",
    html: svg,
    iconSize: [28, 40],
    iconAnchor: [14, 40],
    popupAnchor: [0, -40],
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
          icon={createPropertyIcon(prop.price, prop.property_type)}
          eventHandlers={{
            click: () => onSelect(prop.id === selectedId ? null : prop.id),
          }}
        >
          <Popup maxWidth={260}>
            <div className="text-sm font-sans">
              <p className="font-semibold text-stone-800 mb-1 leading-tight">{prop.title}</p>
              <p className="text-lg font-bold text-amber-800 mb-1">{formatPrice(prop.price)}</p>
              {prop.city && (
                <p className="text-xs text-stone-500 mb-1">📍 {prop.city}</p>
              )}
              <div className="flex gap-2 mb-1 text-xs text-stone-600">
                {prop.surface && <span>🏠 {prop.surface} m²</span>}
                {prop.exterior_surface && <span>🌿 {prop.exterior_surface} m²</span>}
                {prop.rooms && <span>🛏 {prop.rooms} p.</span>}
              </div>
              {prop.nearest_train_min && (
                <p className="text-xs text-sky-600">
                  🚂 Gare : {Math.round(prop.nearest_train_min)} min à pied — {prop.nearest_train_name}
                </p>
              )}
              {prop.nearest_bus_min && (
                <p className="text-xs text-violet-600">
                  🚌 Bus : {Math.round(prop.nearest_bus_min)} min — {prop.nearest_bus_name}
                </p>
              )}
              <a
                href={prop.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-xs text-amber-700 hover:underline"
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
