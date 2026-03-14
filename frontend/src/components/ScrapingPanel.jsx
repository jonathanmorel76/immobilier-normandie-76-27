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
    <div className="border-b border-gray-200 bg-white">
      {/* Toggle */}
      <button
        onClick={() => setIsOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <RefreshCw size={15} className={isRunning ? "animate-spin text-blue-600" : "text-gray-500"} />
          <span>Mettre à jour les annonces</span>
          {isRunning && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium animate-pulse">
              En cours…
            </span>
          )}
          {status?.status === "done" && (
            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
              ✓ Terminé
            </span>
          )}
        </div>
        {isOpen ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
      </button>

      {/* Panneau dépliant */}
      {isOpen && (
        <div className="px-4 pb-4 bg-gray-50 border-t border-gray-100">
          <div className="mt-3 space-y-3">
            {/* Sélecteur source */}
            <div>
              <label className="text-xs text-gray-500 block mb-1">Source des annonces</label>
              <div className="flex gap-2">
                {[
                  { value: "all", label: "Toutes sources" },
                  { value: "pap", label: "PAP.fr" },
                  { value: "bienici", label: "BienIci" },
                  { value: "leboncoin", label: "LeBonCoin" },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setSource(opt.value)}
                    disabled={isRunning}
                    className={`flex-1 text-xs py-1.5 rounded-lg transition-all disabled:opacity-50 ${
                      source === opt.value
                        ? "bg-blue-600 text-white"
                        : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-100"
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
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              {isRunning ? (
                <>
                  <Loader size={15} className="animate-spin" />
                  Scraping en cours…
                </>
              ) : (
                <>
                  <RefreshCw size={15} />
                  Lancer le scraping
                </>
              )}
            </button>

            {/* Résultats */}
            {status?.job && (
              <div className={`rounded-lg p-3 text-xs space-y-1 ${
                status.status === "done" ? "bg-green-50 text-green-800"
                : status.status === "error" ? "bg-red-50 text-red-800"
                : "bg-blue-50 text-blue-800"
              }`}>
                {status.status === "done" && (
                  <>
                    <p className="font-semibold flex items-center gap-1">
                      <CheckCircle size={13} /> Scraping terminé
                    </p>
                    <p>{status.job.properties_found} annonces trouvées</p>
                    <p>{status.job.properties_new} nouvelles annonces ajoutées</p>
                  </>
                )}
                {status.status === "running" && (
                  <p className="flex items-center gap-1">
                    <Loader size={13} className="animate-spin" />
                    Récupération des annonces en cours…
                  </p>
                )}
                {status.status === "error" && (
                  <p className="flex items-center gap-1">
                    <AlertCircle size={13} />
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

            <p className="text-xs text-gray-400 leading-relaxed">
              Récupère les annonces PAP.fr, BienIci et LeBonCoin pour la Seine-Maritime (76)
              et l'Eure (27). Durée estimée : 5-15 minutes.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
