import { useState } from "react";
import PropertyCard from "./PropertyCard.jsx";
import { List, LayoutGrid } from "lucide-react";

export default function PropertyList({ properties, selectedId, onSelect, isLoading }) {
  const [view, setView] = useState("list"); // "list" | "grid"

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Chargement des annonces…</p>
        </div>
      </div>
    );
  }

  if (!properties.length) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center px-6">
          <p className="text-4xl mb-3">🏡</p>
          <p className="text-gray-700 font-semibold">Aucun bien trouvé</p>
          <p className="text-gray-400 text-sm mt-1">
            Modifiez vos filtres ou lancez un nouveau scraping.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full bg-gray-50">
      {/* Barre de contrôle */}
      <div className="px-4 py-2 bg-white border-b border-gray-100 flex items-center justify-between shrink-0">
        <span className="text-xs text-gray-500">{properties.length} annonce{properties.length > 1 ? "s" : ""}</span>
        <div className="flex gap-1">
          <button
            onClick={() => setView("list")}
            className={`p-1.5 rounded ${view === "list" ? "bg-blue-100 text-blue-600" : "text-gray-400 hover:text-gray-600"}`}
          >
            <List size={16} />
          </button>
          <button
            onClick={() => setView("grid")}
            className={`p-1.5 rounded ${view === "grid" ? "bg-blue-100 text-blue-600" : "text-gray-400 hover:text-gray-600"}`}
          >
            <LayoutGrid size={16} />
          </button>
        </div>
      </div>

      {/* Liste */}
      <div className={`flex-1 overflow-y-auto p-3 ${view === "grid" ? "grid grid-cols-2 gap-3 content-start" : "space-y-3"}`}>
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
