import { Train, Bus, MapPin, Home, Expand, TreePine, ExternalLink } from "lucide-react";

function formatPrice(price) {
  if (!price) return "Prix NC";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(price);
}

function TransportBadge({ minutes, name, icon: Icon, color }) {
  if (!minutes) return null;
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium ${color}`}>
      <Icon size={10} />
      {Math.round(minutes)} min · {name}
    </span>
  );
}

export default function PropertyCard({ property, isSelected, onClick }) {
  const priceColor =
    !property.price ? "bg-stone-100 text-stone-500"
    : property.price < 200000 ? "bg-emerald-50 text-emerald-700"
    : property.price < 400000 ? "bg-amber-50 text-amber-700"
    : "bg-red-50 text-red-700";

  const sourceStyles = {
    pap: "bg-sky-50 text-sky-600",
    bienici: "bg-emerald-50 text-emerald-600",
    paruvendu: "bg-violet-50 text-violet-600",
    notaires: "bg-amber-50 text-amber-700",
    leboncoin: "bg-orange-50 text-orange-600",
  };

  const sourceLabels = {
    pap: "PAP.fr",
    bienici: "BienIci",
    paruvendu: "ParuVendu",
    notaires: "Notaires",
    leboncoin: "LeBonCoin",
  };

  return (
    <div
      onClick={onClick}
      className={`p-2.5 rounded-xl border cursor-pointer transition-all hover:shadow-md ${
        isSelected
          ? "border-amber-500 bg-amber-50/50 shadow-md ring-1 ring-amber-300/30"
          : "border-stone-200 bg-white hover:border-amber-300"
      }`}
    >
      {/* Image */}
      {property.images?.length > 0 && (
        <div className="w-full h-32 rounded-lg overflow-hidden mb-2 bg-stone-100">
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
        <p className="text-xs font-semibold text-stone-800 leading-tight line-clamp-2 flex-1">
          {property.title}
        </p>
        <span className={`shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded-md ${priceColor}`}>
          {formatPrice(property.price)}
        </span>
      </div>

      {/* Ville */}
      {property.city && (
        <p className="text-[10px] text-stone-500 flex items-center gap-1 mb-1.5">
          <MapPin size={10} />
          {property.city}
          {property.department && <span className="ml-1 text-stone-400">(Dép. {property.department})</span>}
        </p>
      )}

      {/* Métriques */}
      <div className="flex flex-wrap gap-1.5 mb-1.5">
        {property.surface && (
          <span className="inline-flex items-center gap-1 text-[10px] text-stone-600 bg-stone-50 px-1.5 py-0.5 rounded-full border border-stone-100">
            <Home size={10} /> {property.surface} m²
          </span>
        )}
        {property.exterior_surface && (
          <span className="inline-flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50/60 px-1.5 py-0.5 rounded-full border border-emerald-100">
            <TreePine size={10} /> {property.exterior_surface} m²
          </span>
        )}
        {property.rooms && (
          <span className="text-[10px] text-stone-600 bg-stone-50 px-1.5 py-0.5 rounded-full border border-stone-100">
            {property.rooms} pièces
          </span>
        )}
      </div>

      {/* Transports */}
      <div className="flex flex-wrap gap-1 mb-1.5">
        <TransportBadge
          minutes={property.nearest_train_min}
          name={property.nearest_train_name}
          icon={Train}
          color="bg-sky-50 text-sky-700"
        />
        <TransportBadge
          minutes={property.nearest_bus_min}
          name={property.nearest_bus_name}
          icon={Bus}
          color="bg-violet-50 text-violet-700"
        />
      </div>

      {/* Source + lien */}
      <div className="flex items-center justify-between mt-0.5">
        <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-medium ${
          sourceStyles[property.source] || "bg-stone-50 text-stone-500"
        }`}>
          {sourceLabels[property.source] || property.source}
        </span>
        <a
          href={property.source_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-[10px] text-amber-700 hover:text-amber-900 flex items-center gap-1 font-medium"
        >
          Voir l'annonce <ExternalLink size={10} />
        </a>
      </div>
    </div>
  );
}
