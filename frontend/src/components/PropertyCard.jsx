import { Train, Bus, MapPin, Home, Expand, TreePine, ExternalLink } from "lucide-react";

function formatPrice(price) {
  if (!price) return "Prix NC";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(price);
}

function TransportBadge({ minutes, name, icon: Icon, color }) {
  if (!minutes) return null;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      <Icon size={11} />
      {Math.round(minutes)} min · {name}
    </span>
  );
}

export default function PropertyCard({ property, isSelected, onClick }) {
  const priceColor =
    !property.price ? "bg-gray-100 text-gray-600"
    : property.price < 200000 ? "bg-green-100 text-green-700"
    : property.price < 400000 ? "bg-orange-100 text-orange-700"
    : "bg-red-100 text-red-700";

  return (
    <div
      onClick={onClick}
      className={`p-3 rounded-xl border cursor-pointer transition-all hover:shadow-md ${
        isSelected
          ? "border-blue-500 bg-blue-50 shadow-md"
          : "border-gray-200 bg-white hover:border-blue-300"
      }`}
    >
      {/* Image */}
      {property.images?.length > 0 && (
        <div className="w-full h-36 rounded-lg overflow-hidden mb-2 bg-gray-100">
          <img
            src={property.images[0]}
            alt={property.title}
            className="w-full h-full object-cover"
            onError={(e) => { e.target.parentElement.style.display = "none"; }}
          />
        </div>
      )}

      {/* Titre + prix */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <p className="text-sm font-semibold text-gray-800 leading-tight line-clamp-2 flex-1">
          {property.title}
        </p>
        <span className={`shrink-0 text-xs font-bold px-2 py-1 rounded-lg ${priceColor}`}>
          {formatPrice(property.price)}
        </span>
      </div>

      {/* Ville */}
      {property.city && (
        <p className="text-xs text-gray-500 flex items-center gap-1 mb-2">
          <MapPin size={11} />
          {property.city}
          {property.department && <span className="ml-1 text-gray-400">(Dép. {property.department})</span>}
        </p>
      )}

      {/* Métriques */}
      <div className="flex flex-wrap gap-2 mb-2">
        {property.surface && (
          <span className="inline-flex items-center gap-1 text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">
            <Home size={11} /> {property.surface} m²
          </span>
        )}
        {property.exterior_surface && (
          <span className="inline-flex items-center gap-1 text-xs text-gray-600 bg-green-50 px-2 py-0.5 rounded-full">
            <TreePine size={11} /> {property.exterior_surface} m²
          </span>
        )}
        {property.rooms && (
          <span className="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">
            {property.rooms} pièces
          </span>
        )}
      </div>

      {/* Transports */}
      <div className="flex flex-wrap gap-1 mb-2">
        <TransportBadge
          minutes={property.nearest_train_min}
          name={property.nearest_train_name}
          icon={Train}
          color="bg-blue-100 text-blue-700"
        />
        <TransportBadge
          minutes={property.nearest_bus_min}
          name={property.nearest_bus_name}
          icon={Bus}
          color="bg-purple-100 text-purple-700"
        />
      </div>

      {/* Source + lien */}
      <div className="flex items-center justify-between mt-1">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
          { pap: "bg-blue-50 text-blue-600", bienici: "bg-green-50 text-green-600", paruvendu: "bg-purple-50 text-purple-600", leboncoin: "bg-orange-50 text-orange-600" }[property.source] || "bg-gray-50 text-gray-600"
        }`}>
          {{ pap: "PAP.fr", bienici: "BienIci", paruvendu: "ParuVendu", leboncoin: "LeBonCoin" }[property.source] || property.source}
        </span>
        <a
          href={property.source_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1"
        >
          Voir l'annonce <ExternalLink size={11} />
        </a>
      </div>
    </div>
  );
}
