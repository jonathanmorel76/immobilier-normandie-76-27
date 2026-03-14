import { useState } from "react";
import { SlidersHorizontal, RotateCcw, Train, Bus, Workflow, Home, TreePine, Euro, MapPin } from "lucide-react";

function RangeSlider({ label, icon: Icon, min, max, step, valueMin, valueMax, onChangeMin, onChangeMax, format }) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon size={13} className="text-amber-700/60" />}
        <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">{label}</span>
      </div>
      <div className="flex gap-2 items-center">
        <input
          type="number"
          value={valueMin ?? ""}
          onChange={(e) => onChangeMin(e.target.value === "" ? null : Number(e.target.value))}
          placeholder={`Min (${format(min)})`}
          className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 transition-all"
        />
        <span className="text-stone-400 text-xs shrink-0">à</span>
        <input
          type="number"
          value={valueMax ?? ""}
          onChange={(e) => onChangeMax(e.target.value === "" ? null : Number(e.target.value))}
          placeholder={`Max (${format(max)})`}
          className="w-full text-sm border border-stone-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 transition-all"
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
        <Icon size={13} className={color} />
        <span className="text-[11px] font-semibold text-stone-500">{label}</span>
        {value && (
          <span className={`ml-auto text-[11px] font-bold ${color}`}>≤ {value} min</span>
        )}
      </div>
      <div className="flex gap-1 flex-wrap">
        {options.map((opt) => (
          <button
            key={opt ?? "all"}
            onClick={() => onChange(opt)}
            className={`text-[11px] px-2 py-0.5 rounded-full transition-all ${
              value === opt
                ? "bg-amber-800 text-white shadow-sm"
                : "bg-stone-100 text-stone-500 hover:bg-stone-200"
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
    <aside className="w-full md:w-80 shrink-0 bg-stone-50 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3.5 border-b border-stone-200/60 bg-gradient-to-r from-amber-900 to-amber-800">
        <div className="flex items-center gap-2">
          <SlidersHorizontal size={16} className="text-amber-200" />
          <h2 className="text-white font-bold text-sm">Filtres de recherche</h2>
        </div>
        <p className="text-amber-200/70 text-[11px] mt-0.5 font-medium">
          {isLoading ? "Chargement…" : `${total} bien${total > 1 ? "s" : ""} trouvé${total > 1 ? "s" : ""}`}
        </p>
      </div>

      {/* Filtres */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">

        {/* Département */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <MapPin size={13} className="text-amber-700/60" />
            <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">Département</span>
          </div>
          <div className="flex gap-1.5">
            {[
              { value: "all", label: "Les deux" },
              { value: "76", label: "Seine-Mar. (76)" },
              { value: "27", label: "Eure (27)" },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => updateFilter("department", opt.value)}
                className={`flex-1 text-[11px] py-1.5 px-1 rounded-lg font-medium transition-all ${
                  filters.department === opt.value
                    ? "bg-amber-800 text-white shadow-sm"
                    : "bg-white text-stone-500 border border-stone-200 hover:bg-stone-100"
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
            <Home size={13} className="text-amber-700/60" />
            <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">Type de bien</span>
          </div>
          <div className="flex gap-1.5 flex-wrap">
            {[
              { value: null, label: "Tous" },
              { value: "Maison", label: "Maison" },
              { value: "Appartement", label: "Appart." },
              { value: "Terrain", label: "Terrain" },
            ].map((opt) => (
              <button
                key={opt.value ?? "all"}
                onClick={() => updateFilter("propertyType", opt.value)}
                className={`flex-1 text-[11px] py-1.5 px-1 rounded-lg font-medium transition-all ${
                  filters.propertyType === opt.value
                    ? "bg-amber-800 text-white shadow-sm"
                    : "bg-white text-stone-500 border border-stone-200 hover:bg-stone-100"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <hr className="border-stone-200/60 my-3" />

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

        <hr className="border-stone-200/60 my-3" />

        {/* Transports */}
        <div className="mb-2">
          <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">
            Proximité transports (à pied)
          </span>
        </div>

        <WalkSlider
          label="Gare / Train"
          icon={Train}
          color="text-sky-600"
          value={filters.maxTrainWalk}
          onChange={(v) => updateFilter("maxTrainWalk", v)}
        />
        <WalkSlider
          label="Arrêt de bus"
          icon={Bus}
          color="text-violet-600"
          value={filters.maxBusWalk}
          onChange={(v) => updateFilter("maxBusWalk", v)}
        />
        <WalkSlider
          label="Tram"
          icon={Workflow}
          color="text-emerald-600"
          value={filters.maxTramWalk}
          onChange={(v) => updateFilter("maxTramWalk", v)}
        />

        <hr className="border-stone-200/60 my-3" />

        {/* Source */}
        <div className="mb-4">
          <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider block mb-2">Source</span>
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
                className={`text-[11px] py-1.5 px-2.5 rounded-lg font-medium transition-all ${
                  filters.source === opt.value
                    ? "bg-amber-800 text-white shadow-sm"
                    : "bg-white text-stone-500 border border-stone-200 hover:bg-stone-100"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Reset */}
      <div className="px-4 py-3 border-t border-stone-200/60">
        <button
          onClick={resetFilters}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-sm text-stone-600 bg-white border border-stone-200 hover:bg-stone-100 transition-all font-medium"
        >
          <RotateCcw size={13} />
          Réinitialiser les filtres
        </button>
      </div>
    </aside>
  );
}
