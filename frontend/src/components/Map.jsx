import { useEffect, useRef, useMemo, useState, useCallback } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";

// Fix icônes Leaflet avec Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Limites de la Normandie (76 + 27) avec marge
const NORMANDIE_BOUNDS = L.latLngBounds(
  [48.3, -0.3],  // Sud-Ouest
  [50.1, 2.0]    // Nord-Est
);
const NORMANDIE_CENTER = [49.44, 1.09];
const DEFAULT_ZOOM = 9;
const MIN_ZOOM = 8;
const MAX_ZOOM = 18;

// SVG paths pour chaque type de bien
const TYPE_ICONS = {
  maison: `<path d="M12 6 L8 10 L8 15 L16 15 L16 10 Z" fill="white" stroke="none"/>
            <path d="M12 6 L7 10.5 L8 10.5 L8 15 L11 15 L11 12 L13 12 L13 15 L16 15 L16 10.5 L17 10.5 Z" fill="white" stroke="none"/>`,
  appartement: `<path d="M8 7 L8 16 L16 16 L16 7 Z" fill="white" stroke="none"/>
                 <rect x="9.5" y="8.5" width="2" height="1.5" rx="0.2" fill="currentColor" opacity="0.5"/>
                 <rect x="12.5" y="8.5" width="2" height="1.5" rx="0.2" fill="currentColor" opacity="0.5"/>
                 <rect x="9.5" y="11.5" width="2" height="1.5" rx="0.2" fill="currentColor" opacity="0.5"/>
                 <rect x="12.5" y="11.5" width="2" height="1.5" rx="0.2" fill="currentColor" opacity="0.5"/>
                 <rect x="11" y="14" width="2" height="2" rx="0.2" fill="currentColor" opacity="0.5"/>`,
  terrain: `<circle cx="12" cy="9" r="3" fill="white" stroke="none"/>
            <rect x="11.3" y="11.5" width="1.4" height="3" rx="0.3" fill="white"/>
            <rect x="8" y="14.5" width="8" height="1" rx="0.5" fill="white" opacity="0.6"/>`,
  parking: `<text x="12" y="15" text-anchor="middle" font-size="10" font-weight="bold" fill="white" font-family="sans-serif">P</text>`,
  default: `<circle cx="12" cy="12" r="4" fill="white"/>`,
};

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

function getPriceColor(price) {
  if (!price) return "#78716c";
  if (price < 200000) return "#16a34a";
  if (price < 400000) return "#d97706";
  return "#dc2626";
}

function createPropertyIcon(price, propertyType) {
  const color = getPriceColor(price);
  const typeKey = getTypeKey(propertyType);
  const innerIcon = TYPE_ICONS[typeKey] || TYPE_ICONS.default;

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="28" height="40">
      <path fill="${color}" stroke="white" stroke-width="1.5"
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

// Icône cluster
function createClusterIcon(count) {
  let size, bgColor, textSize;
  if (count < 10) {
    size = 36; bgColor = "#92400e"; textSize = "12px";
  } else if (count < 30) {
    size = 42; bgColor = "#78350f"; textSize = "13px";
  } else {
    size = 50; bgColor = "#451a03"; textSize = "14px";
  }

  return L.divIcon({
    html: `<div style="
      width:${size}px;height:${size}px;
      background:${bgColor};
      border:3px solid rgba(255,255,255,0.85);
      border-radius:50%;
      display:flex;align-items:center;justify-content:center;
      color:white;font-weight:700;font-size:${textSize};
      font-family:Inter,sans-serif;
      box-shadow:0 2px 8px rgba(0,0,0,0.25);
    ">${count}</div>`,
    className: "",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
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

// Clustering simple : regroupe les points proches en pixels
function clusterProperties(properties, map, radius) {
  const zoom = map.getZoom();
  const bounds = map.getBounds();
  const visible = properties.filter((p) => {
    if (!p.latitude || !p.longitude) return false;
    return bounds.contains([p.latitude, p.longitude]);
  });

  // Zoom >= 14 : pas de clustering
  if (zoom >= 14) {
    return visible.map((p) => ({ type: "single", property: p }));
  }

  const used = new Set();
  const result = [];

  for (let i = 0; i < visible.length; i++) {
    if (used.has(i)) continue;

    const p = visible[i];
    const pt = map.latLngToContainerPoint([p.latitude, p.longitude]);
    const cluster = [p];
    used.add(i);

    for (let j = i + 1; j < visible.length; j++) {
      if (used.has(j)) continue;
      const q = visible[j];
      const qt = map.latLngToContainerPoint([q.latitude, q.longitude]);
      const dx = pt.x - qt.x;
      const dy = pt.y - qt.y;
      if (dx * dx + dy * dy < radius * radius) {
        cluster.push(q);
        used.add(j);
      }
    }

    if (cluster.length === 1) {
      result.push({ type: "single", property: p });
    } else {
      // Centre moyen du cluster
      const lat = cluster.reduce((s, c) => s + c.latitude, 0) / cluster.length;
      const lng = cluster.reduce((s, c) => s + c.longitude, 0) / cluster.length;
      result.push({ type: "cluster", lat, lng, count: cluster.length, properties: cluster });
    }
  }

  return result;
}

// Composant pour centrer sur le bien sélectionné
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

// Composant qui regroupe et affiche les marqueurs
function ClusteredMarkers({ properties, selectedId, onSelect }) {
  const map = useMap();
  const [items, setItems] = useState([]);

  const recompute = useCallback(() => {
    const clustered = clusterProperties(properties, map, 50);
    setItems(clustered);
  }, [properties, map]);

  useMapEvents({
    moveend: recompute,
    zoomend: recompute,
  });

  useEffect(() => {
    // Petite attente pour que la carte soit prête
    const timer = setTimeout(recompute, 100);
    return () => clearTimeout(timer);
  }, [recompute]);

  return (
    <>
      {items.map((item, idx) => {
        if (item.type === "cluster") {
          return (
            <Marker
              key={`cluster-${idx}`}
              position={[item.lat, item.lng]}
              icon={createClusterIcon(item.count)}
              eventHandlers={{
                click: () => {
                  map.flyTo([item.lat, item.lng], map.getZoom() + 2, { duration: 0.5 });
                },
              }}
            />
          );
        }

        const prop = item.property;
        return (
          <Marker
            key={prop.id}
            position={[prop.latitude, prop.longitude]}
            icon={createPropertyIcon(prop.price, prop.property_type)}
            eventHandlers={{
              click: () => onSelect(prop.id === selectedId ? null : prop.id),
            }}
          >
            <Popup maxWidth={260}>
              <div style={{ fontFamily: "Inter, sans-serif", fontSize: "13px", maxWidth: "240px" }}>
                <p style={{ fontWeight: 600, color: "#292524", margin: "0 0 4px", lineHeight: 1.3 }}>{prop.title}</p>
                <p style={{ fontSize: "16px", fontWeight: 700, color: "#92400e", margin: "0 0 4px" }}>{formatPrice(prop.price)}</p>
                {prop.city && (
                  <p style={{ fontSize: "11px", color: "#78716c", margin: "0 0 4px" }}>📍 {prop.city}</p>
                )}
                <div style={{ display: "flex", gap: "8px", marginBottom: "4px", fontSize: "11px", color: "#57534e" }}>
                  {prop.surface && <span>🏠 {prop.surface} m²</span>}
                  {prop.exterior_surface && <span>🌿 {prop.exterior_surface} m²</span>}
                  {prop.rooms && <span>🛏 {prop.rooms} p.</span>}
                </div>
                {prop.nearest_train_min && (
                  <p style={{ fontSize: "11px", color: "#0284c7", margin: "0 0 2px" }}>
                    🚂 Gare : {Math.round(prop.nearest_train_min)} min — {prop.nearest_train_name}
                  </p>
                )}
                {prop.nearest_bus_min && (
                  <p style={{ fontSize: "11px", color: "#7c3aed", margin: "0 0 2px" }}>
                    🚌 Bus : {Math.round(prop.nearest_bus_min)} min — {prop.nearest_bus_name}
                  </p>
                )}
                <a
                  href={prop.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ display: "inline-block", marginTop: "6px", fontSize: "11px", color: "#92400e", textDecoration: "none" }}
                >
                  Voir l'annonce ↗
                </a>
              </div>
            </Popup>
          </Marker>
        );
      })}
    </>
  );
}

export default function Map({ properties, selectedId, onSelect }) {
  return (
    <MapContainer
      center={NORMANDIE_CENTER}
      zoom={DEFAULT_ZOOM}
      minZoom={MIN_ZOOM}
      maxZoom={MAX_ZOOM}
      maxBounds={NORMANDIE_BOUNDS}
      maxBoundsViscosity={1.0}
      className="w-full h-full"
      style={{ zIndex: 0 }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <FlyToSelected properties={properties} selectedId={selectedId} />
      <ClusteredMarkers properties={properties} selectedId={selectedId} onSelect={onSelect} />
    </MapContainer>
  );
}
