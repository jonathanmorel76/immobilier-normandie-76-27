import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import FilterPanel from "./components/FilterPanel.jsx";
import PropertyList from "./components/PropertyList.jsx";
import Map from "./components/Map.jsx";
import ScrapingPanel from "./components/ScrapingPanel.jsx";
import { useProperties } from "./hooks/useProperties.js";
import { MapPin, Map as MapIcon, Home, SlidersHorizontal } from "lucide-react";

export default function App() {
  const queryClient = useQueryClient();
  const {
    properties,
    total,
    isLoading,
    isError,
    filters,
    updateFilter,
    resetFilters,
    selectedId,
    setSelectedId,
  } = useProperties();

  // Sur mobile, basculer entre carte, liste et filtres
  const [mobileView, setMobileView] = useState("map"); // "map" | "list" | "filters"

  const handleScrapingDone = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["properties"] });
  }, [queryClient]);

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm shrink-0 z-10 border-b border-gray-200">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <MapPin size={16} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-gray-900 text-sm md:text-base leading-tight">
                Biens immobilier actuellement en vente sur la Seine-Maritime et l'Eure
              </h1>
            </div>
          </div>

          {/* Légende couleurs prix */}
          <div className="hidden md:flex items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-green-500 inline-block" /> &lt; 200k€
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-orange-500 inline-block" /> 200–400k€
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> &gt; 400k€
            </span>
          </div>
        </div>
      </header>

      {/* Corps principal */}
      <div className="flex flex-1 overflow-hidden pb-14 md:pb-0">
        {/* Colonne gauche : filtres + scraping (desktop + mobile filters) */}
        <div className={`shrink-0 flex flex-col bg-white border-r border-gray-200 h-full overflow-hidden ${
          mobileView === "filters" ? "flex w-full md:w-80" : "hidden md:flex md:w-80"
        }`}>
          {/* Scraping */}
          <ScrapingPanel onScrapingDone={handleScrapingDone} />

          {/* Filtres */}
          <FilterPanel
            filters={filters}
            updateFilter={updateFilter}
            resetFilters={resetFilters}
            total={total}
            isLoading={isLoading}
          />
        </div>

        {/* Panneau droit : carte + liste (desktop) */}
        <div className={`flex-1 flex flex-col overflow-hidden ${
          mobileView === "map" ? "flex" : "hidden md:flex"
        }`}>
          {/* Carte */}
          <div className="flex-1 relative min-h-0">
            {isError ? (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
                <div className="text-center">
                  <p className="text-red-500 font-semibold">Impossible de contacter le serveur</p>
                  <p className="text-gray-500 text-sm mt-1">Vérifiez que le backend tourne sur le port 8000.</p>
                </div>
              </div>
            ) : (
              <Map
                properties={properties}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            )}

            {/* Badge compteur flottant */}
            <div className="absolute top-3 right-3 z-[1000] bg-white shadow-md rounded-lg px-3 py-1.5 text-xs text-gray-700 font-medium border border-gray-100">
              {isLoading ? "…" : `${properties.filter(p => p.latitude && p.longitude).length} sur la carte`}
            </div>
          </div>

          {/* Barre de liste horizontale en bas (desktop uniquement) */}
          <div className="hidden md:flex h-64 border-t border-gray-200 overflow-hidden bg-gray-50">
            <PropertyList
              properties={properties}
              selectedId={selectedId}
              onSelect={setSelectedId}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Liste mobile pleine page */}
        {mobileView === "list" && (
          <div className="md:hidden flex-1 overflow-hidden">
            <PropertyList
              properties={properties}
              selectedId={selectedId}
              onSelect={(id) => {
                setSelectedId(id);
                setMobileView("map");
              }}
              isLoading={isLoading}
            />
          </div>
        )}
      </div>

      {/* Bottom nav mobile */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 z-50 flex safe-area-bottom">
        <button
          onClick={() => setMobileView("map")}
          className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors ${
            mobileView === "map" ? "text-blue-600" : "text-gray-400"
          }`}
        >
          <MapIcon size={20} />
          <span>Carte</span>
        </button>
        <button
          onClick={() => setMobileView("list")}
          className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors ${
            mobileView === "list" ? "text-blue-600" : "text-gray-400"
          }`}
        >
          <Home size={20} />
          <span>{total > 0 ? `Annonces (${total})` : "Annonces"}</span>
        </button>
        <button
          onClick={() => setMobileView("filters")}
          className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors ${
            mobileView === "filters" ? "text-blue-600" : "text-gray-400"
          }`}
        >
          <SlidersHorizontal size={20} />
          <span>Filtres</span>
        </button>
      </nav>
    </div>
  );
}
