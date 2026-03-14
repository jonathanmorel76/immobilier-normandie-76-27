import { useState } from "react";
import PropertyCard from "./PropertyCard.jsx";
import { List, LayoutGrid } from "lucide-react";

export default function PropertyList({ properties, selectedId, onSelect, isLoading }) {
  const [view, setView] = useState("list"); // "list" | "grid"

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-stone-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-9 w-9 border-2 border-amber-200 border-t-amber-700 mx-auto mb-3" />
          <p className="text-stone-400 text-sm">Chargement des annonces…</p>
        </div>
      </div>
    );
  }

  if (!properties.length) {
    return (
      <div className="flex-1 flex items-center justify-center bg-stone-50">
        <div className="text-center px-6">
          <p className="text-4xl mb-3">🏡</p>
          <p className="text-stone-700 font-semibold">Aucun bien trouvé</p>
          <p className="text-stone-400 text-sm mt-1">
            Modifiez vos filtres ou lancez un nouveau scraping.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full bg-stone-50">
      {/* Barre de contrôle */}
      <div className="px-4 py-2 bg-white/80 backdrop-blur-sm border-b border-stone-100 flex items-center justify-between shrink-0">
        <span className="text-[11px] text-stone-500 font-medium">{properties.length} annonce{properties.length > 1 ? "s" : ""}</span>
        <div className="flex gap-1">
          <button
            onClick={() => setView("list")}
            className={`p-1.5 rounded-lg transition-all ${view === "list" ? "bg-amber-100 text-amber-800" : "text-stone-400 hover:text-stone-600"}`}
          >
            <List size={14} />
          </button>
          <button
            onClick={() => setView("grid")}
            className={`p-1.5 rounded-lg transition-all ${view === "grid" ? "bg-amber-100 text-amber-800" : "text-stone-400 hover:text-stone-600"}`}
          >
            <LayoutGrid size={14} />
          </button>
        </div>
      </div>

      {/* Liste */}
      <div className={`flex-1 overflow-y-auto p-2.5 ${view === "grid" ? "grid grid-cols-2 gap-2.5 content-start" : "space-y-2.5"}`}>
        {properties.map((prop) => (
          <PropertyCard
            key={prop.id}
            property={prop}
            isSelected={prop.id === selectedId}
            onClick={() => onSelect(prop.id === selectedId ? null : prop.id)}
          />
        ))}
      </div>
    </div>
  );
}
