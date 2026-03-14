import { useState, useEffect } from "react";
import { RefreshCw, CheckCircle, AlertCircle, Loader, ChevronDown, ChevronUp } from "lucide-react";
import { startScrape, fetchScrapeStatus } from "../services/api.js";

export default function ScrapingPanel({ onScrapingDone }) {
  const [isOpen, setIsOpen] = useState(false);
  const [source, setSource] = useState("all");
  const [status, setStatus] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState(null);

  // Polling toutes les 5s quand un job tourne
  useEffect(() => {
    if (!isPolling) return;
    const interval = setInterval(async () => {
      try {
        const data = await fetchScrapeStatus();
        setStatus(data);
        if (data.status === "done" || data.status === "error" || data.status === "idle") {
          setIsPolling(false);
          if (data.status === "done") {
            onScrapingDone?.();
          }
        }
      } catch (e) {
        console.error(e);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [isPolling, onScrapingDone]);

  const handleStart = async () => {
    setError(null);
    try {
      await startScrape(source);
      setIsPolling(true);
      const data = await fetchScrapeStatus();
      setStatus(data);
    } catch (e) {
      setError(e.message);
    }
  };

  const isRunning = status?.status === "running" || status?.status === "pending";

  return (
    <div className="border-b border-stone-200/60 bg-stone-50">
      {/* Toggle */}
      <button
        onClick={() => setIsOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-stone-700 hover:bg-stone-100/60 transition-colors"
      >
        <div className="flex items-center gap-2">
          <RefreshCw size={14} className={isRunning ? "animate-spin text-amber-700" : "text-stone-400"} />
          <span>Mettre à jour les annonces</span>
          {isRunning && (
            <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium animate-pulse">
              En cours…
            </span>
          )}
          {status?.status === "done" && (
            <span className="text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
              ✓ Terminé
            </span>
          )}
        </div>
        {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {/* Panneau dépliant */}
      {isOpen && (
        <div className="px-4 pb-4 bg-stone-50 border-t border-stone-100">
          <div className="mt-3 space-y-3">
            {/* Sélecteur source */}
            <div>
              <label className="text-[10px] text-stone-400 block mb-1 uppercase tracking-wider font-semibold">Source des annonces</label>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { value: "all", label: "Toutes" },
                  { value: "bienici", label: "BienIci" },
                  { value: "paruvendu", label: "ParuVendu" },
                  { value: "notaires", label: "Notaires" },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setSource(opt.value)}
                    disabled={isRunning}
                    className={`text-[11px] py-1.5 px-2.5 rounded-lg transition-all disabled:opacity-50 font-medium ${
                      source === opt.value
                        ? "bg-amber-800 text-white shadow-sm"
                        : "bg-white border border-stone-200 text-stone-500 hover:bg-stone-100"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Bouton lancer */}
            <button
              onClick={handleStart}
              disabled={isRunning}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-amber-800 to-amber-700 text-white rounded-lg text-sm font-semibold hover:from-amber-900 hover:to-amber-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              {isRunning ? (
                <>
                  <Loader size={14} className="animate-spin" />
                  Scraping en cours…
                </>
              ) : (
                <>
                  <RefreshCw size={14} />
                  Lancer le scraping
                </>
              )}
            </button>

            {/* Résultats */}
            {status?.job && (
              <div className={`rounded-lg p-3 text-xs space-y-1 ${
                status.status === "done" ? "bg-emerald-50 text-emerald-800"
                : status.status === "error" ? "bg-red-50 text-red-800"
                : "bg-amber-50 text-amber-800"
              }`}>
                {status.status === "done" && (
                  <>
                    <p className="font-semibold flex items-center gap-1">
                      <CheckCircle size={12} /> Scraping terminé
                    </p>
                    <p>{status.job.properties_found} annonces trouvées</p>
                    <p>{status.job.properties_new} nouvelles annonces ajoutées</p>
                  </>
                )}
                {status.status === "running" && (
                  <p className="flex items-center gap-1">
                    <Loader size={12} className="animate-spin" />
                    Récupération des annonces en cours…
                  </p>
                )}
                {status.status === "error" && (
                  <p className="flex items-center gap-1">
                    <AlertCircle size={12} />
                    Erreur : {status.job.error_message}
                  </p>
                )}
              </div>
            )}

            {error && (
              <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">
                ⚠ {error}
              </p>
            )}

            <p className="text-[10px] text-stone-400 leading-relaxed">
              Récupère les annonces BienIci, ParuVendu et Notaires de France
              pour la Seine-Maritime (76) et l'Eure (27). Durée estimée : 5-15 minutes.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
