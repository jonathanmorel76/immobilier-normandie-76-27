import { useState } from "react";
import { SlidersHorizontal, RotateCcw, Train, Bus, Workflow, Home, TreePine, Euro, MapPin } from "lucide-react";

function RangeSlider({ label, icon: Icon, min, max, step, valueMin, valueMax, onChangeMin, onChangeMax, format }) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon size={14} className="text-gray-500" />}
        <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">{label}</span>
      </div>
      <div className="flex gap-2 items-center">
        <input
          type="number"
          value={valueMin ?? ""}
          onChange={(e) => onChangeMin(e.target.value === "" ? null : Number(e.target.value))}
          placeholder={`Min (${format(min)})`}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <span className="text-gray-400 text-xs shrink-0">à</span>
        <input
          type="number"
          value={valueMax ?? ""}
          onChange={(e) => onChangeMax(e.target.value === "" ? null : Number(e.target.value))}
          placeholder={`Max (${format(max)})`}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>
    </div>
  );
}

function WalkSlider({ label, icon: Icon, color, value, onChange }) {
  const options = [null, 5, 10, 15, 20, 30, 45, 60];
  return (
    <div className="mb-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} className={color} />
        <span className="text-xs font-semibold text-gray-600">{label}</span>
        {value && (
          <span className={`ml-auto text-xs font-bold ${color}`}>≤ {value} min</span>
        )}
      </div>
      <div className="flex gap-1 flex-wrap">
        {options.map((opt) => (
          <button
            key={opt ?? "all"}
            onClick={() => onChange(opt)}
            className={`text-xs px-2 py-1 rounded-full transition-all ${
              value === opt
                ? "bg-blue-600 text-white shadow"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {opt === null ? "Tous" : `${opt}min`}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function FilterPanel({ filters, updateFilter, resetFilters, total, isLoading }) {
  return (
    <aside className="w-full md:w-80 shrink-0 bg-white border-r border-gray-200 flex flex-col h-full overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-600 to-blue-700">
        <div className="flex items-center gap-2">
          <SlidersHorizontal size={18} className="text-white" />
          <h2 className="text-white font-bold text-base">Filtres de recherche</h2>
        </div>
        <p className="text-blue-200 text-xs mt-1">
          {isLoading ? "Chargement…" : `${total} bien${total > 1 ? "s" : ""} trouvé${total > 1 ? "s" : ""}`}
        </p>
      </div>

      {/* Filtres */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">

        {/* Département */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <MapPin size={14} className="text-gray-500" />
            <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Département</span>
          </div>
          <div className="flex gap-2">
            {[
              { value: "all", label: "Les deux" },
              { value: "76", label: "Seine-Maritime (76)" },
              { value: "27", label: "Eure (27)" },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => updateFilter("department", opt.value)}
                className={`flex-1 text-xs py-2 px-1 rounded-lg font-medium transition-all ${
                  filters.department === opt.value
                    ? "bg-blue-600 text-white shadow"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Type de bien */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Home size={14} className="text-gray-500" />
            <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Type de bien</span>
          </div>
          <div className="flex gap-2 flex-wrap">
            {[
              { value: null, label: "Tous" },
              { value: "Maison", label: "Maison" },
              { value: "Appartement", label: "Appart." },
              { value: "Terrain", label: "Terrain" },
            ].map((opt) => (
              <button
                key={opt.value ?? "all"}
                onClick={() => updateFilter("propertyType", opt.value)}
                className={`flex-1 text-xs py-2 px-1 rounded-lg font-medium transition-all ${
                  filters.propertyType === opt.value
                    ? "bg-blue-600 text-white shadow"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <hr className="border-gray-100 my-3" />

        {/* Prix */}
        <RangeSlider
          label="Prix de vente"
          icon={Euro}
          min={0}
          max={1000000}
          step={5000}
          valueMin={filters.minPrice}
          valueMax={filters.maxPrice}
          onChangeMin={(v) => updateFilter("minPrice", v)}
          onChangeMax={(v) => updateFilter("maxPrice", v)}
          format={(v) => `${(v / 1000).toFixed(0)}k€`}
        />

        {/* Surface habitable */}
        <RangeSlider
          label="Surface habitable (m²)"
          icon={Home}
          min={0}
          max={500}
          step={5}
          valueMin={filters.minSurface}
          valueMax={filters.maxSurface}
          onChangeMin={(v) => updateFilter("minSurface", v)}
          onChangeMax={(v) => updateFilter("maxSurface", v)}
          format={(v) => `${v}m²`}
        />

        {/* Surface extérieure */}
        <RangeSlider
          label="Surface extérieure (m²)"
          icon={TreePine}
          min={0}
          max={5000}
          step={50}
          valueMin={filters.minExterior}
          valueMax={filters.maxExterior}
          onChangeMin={(v) => updateFilter("minExterior", v)}
          onChangeMax={(v) => updateFilter("maxExterior", v)}
          format={(v) => `${v}m²`}
        />

        <hr className="border-gray-100 my-3" />

        {/* Transports */}
        <div className="mb-2">
          <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
            Proximité transports (à pied)
          </span>
        </div>

        <WalkSlider
          label="Gare / Train"
          icon={Train}
          color="text-blue-600"
          value={filters.maxTrainWalk}
          onChange={(v) => updateFilter("maxTrainWalk", v)}
        />
        <WalkSlider
          label="Arrêt de bus"
          icon={Bus}
          color="text-purple-600"
          value={filters.maxBusWalk}
          onChange={(v) => updateFilter("maxBusWalk", v)}
        />
        <WalkSlider
          label="Tram"
          icon={Workflow}
          color="text-green-600"
          value={filters.maxTramWalk}
          onChange={(v) => updateFilter("maxTramWalk", v)}
        />

        <hr className="border-gray-100 my-3" />

        {/* Source */}
        <div className="mb-4">
          <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide block mb-2">Source</span>
          <div className="flex gap-1.5 flex-wrap">
            {[
              { value: null, label: "Toutes" },
              { value: "bienici", label: "BienIci" },
              { value: "paruvendu", label: "ParuVendu" },
              { value: "notaires", label: "Notaires" },
            ].map((opt) => (
              <button
                key={opt.value ?? "all"}
                onClick={() => updateFilter("source", opt.value)}
                className={`text-xs py-2 px-2.5 rounded-lg font-medium transition-all ${
                  filters.source === opt.value
                    ? "bg-blue-600 text-white shadow"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Reset */}
      <div className="px-4 py-3 border-t border-gray-100">
        <button
          onClick={resetFilters}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 transition-all font-medium"
        >
          <RotateCcw size={14} />
          Réinitialiser les filtres
        </button>
      </div>
    </aside>
  );
}
