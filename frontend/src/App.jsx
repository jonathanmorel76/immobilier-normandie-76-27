import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import FilterPanel from "./components/FilterPanel.jsx";
import PropertyList from "./components/PropertyList.jsx";
import Map from "./components/Map.jsx";
import ScrapingPanel from "./components/ScrapingPanel.jsx";
import { useProperties } from "./hooks/useProperties.js";
import { Map as MapIcon, Home, SlidersHorizontal } from "lucide-react";

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
    <div className="h-screen flex flex-col bg-stone-100">
      {/* Header */}
      <header className="shrink-0 z-10 bg-gradient-to-r from-amber-900 via-amber-800 to-yellow-700 shadow-lg">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center border border-white/10">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Maison à gauche */}
                <path d="M2 12 L7 7.5 L12 12 L12 19 L2 19 Z" fill="#fde68a" stroke="#fde68a" strokeWidth="0.5" strokeLinejoin="round"/>
                <path d="M2 12 L7 7.5 L12 12" fill="none" stroke="#fef3c7" strokeWidth="1.2" strokeLinejoin="round" strokeLinecap="round"/>
                <rect x="4.5" y="14" width="2" height="2.5" rx="0.3" fill="#92400e" opacity="0.5"/>
                <rect x="8" y="13.5" width="1.8" height="1.5" rx="0.2" fill="#92400e" opacity="0.35"/>
                {/* Immeuble à droite */}
                <rect x="13" y="6" width="9" height="13" rx="0.8" fill="#fde68a" stroke="#fef3c7" strokeWidth="0.8"/>
                <rect x="14.5" y="8" width="1.8" height="1.3" rx="0.2" fill="#92400e" opacity="0.4"/>
                <rect x="18" y="8" width="1.8" height="1.3" rx="0.2" fill="#92400e" opacity="0.4"/>
                <rect x="14.5" y="11" width="1.8" height="1.3" rx="0.2" fill="#92400e" opacity="0.4"/>
                <rect x="18" y="11" width="1.8" height="1.3" rx="0.2" fill="#92400e" opacity="0.4"/>
                <rect x="14.5" y="14" width="1.8" height="1.3" rx="0.2" fill="#92400e" opacity="0.4"/>
                <rect x="18" y="14" width="1.8" height="1.3" rx="0.2" fill="#92400e" opacity="0.4"/>
                <rect x="16.2" y="16.5" width="2" height="2.5" rx="0.3" fill="#92400e" opacity="0.5"/>
              </svg>
            </div>
            <div>
              <h1 className="font-bold text-white text-sm md:text-base leading-tight tracking-tight">
                Biens immobilier en vente
              </h1>
              <p className="text-amber-200/80 text-[10px] md:text-xs font-medium">
                Seine-Maritime (76) · Eure (27)
              </p>
            </div>
          </div>

          {/* Légende couleurs prix */}
          <div className="hidden md:flex items-center gap-3 text-xs text-amber-100/80">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block ring-1 ring-white/20" /> &lt; 200k€
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block ring-1 ring-white/20" /> 200–400k€
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-400 inline-block ring-1 ring-white/20" /> &gt; 400k€
            </span>
          </div>
        </div>
      </header>

      {/* Corps principal */}
      <div className="flex flex-1 overflow-hidden pb-14 md:pb-0">
        {/* Colonne gauche : filtres + scraping (desktop + mobile filters) */}
        <div className={`shrink-0 flex flex-col bg-stone-50 border-r border-stone-200 h-full overflow-hidden ${
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
              <div className="absolute inset-0 flex items-center justify-center bg-stone-100">
                <div className="text-center">
                  <p className="text-red-600 font-semibold">Impossible de contacter le serveur</p>
                  <p className="text-stone-500 text-sm mt-1">Vérifiez que le backend tourne sur le port 8000.</p>
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
            <div className="absolute top-3 right-3 z-[1000] bg-white/95 backdrop-blur-sm shadow-md rounded-xl px-3 py-1.5 text-xs text-stone-700 font-semibold border border-stone-200/60">
              {isLoading ? "…" : `${properties.filter(p => p.latitude && p.longitude).length} sur la carte`}
            </div>
          </div>

          {/* Barre de liste horizontale en bas (desktop uniquement) */}
          <div className="hidden md:flex h-64 border-t border-stone-200 overflow-hidden bg-stone-50">
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
      <nav className="md:hidden fixed bottom-0 inset-x-0 bg-white/95 backdrop-blur-md border-t border-stone-200 z-50 flex safe-area-bottom">
        <button
          onClick={() => setMobileView("map")}
          className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors ${
            mobileView === "map" ? "text-amber-800" : "text-stone-400"
          }`}
        >
          <MapIcon size={20} />
          <span>Carte</span>
        </button>
        <button
          onClick={() => setMobileView("list")}
          className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors ${
            mobileView === "list" ? "text-amber-800" : "text-stone-400"
          }`}
        >
          <Home size={20} />
          <span>{total > 0 ? `Annonces (${total})` : "Annonces"}</span>
        </button>
        <button
          onClick={() => setMobileView("filters")}
          className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors ${
            mobileView === "filters" ? "text-amber-800" : "text-stone-400"
          }`}
        >
          <SlidersHorizontal size={20} />
          <span>Filtres</span>
        </button>
      </nav>
    </div>
  );
}
