import { useCallback, useEffect, useState } from "react";

import { fetchMetrics, type MetricWithStats } from "./api";
import CompetitionPage from "./components/CompetitionPage";
import HeatmapCard from "./components/HeatmapCard";

type Page = "dashboard" | "competition";

const CHALLENGE_PATH = "/challenge";

function pageFromPath(): Page {
  return window.location.pathname.replace(/\/+$/, "") === CHALLENGE_PATH ? "competition" : "dashboard";
}

export default function App() {
  const [page, setPage] = useState<Page>(pageFromPath);

  useEffect(() => {
    const onPopState = () => setPage(pageFromPath());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);
  const [metrics, setMetrics] = useState<MetricWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    fetchMetrics()
      .then(setMetrics)
      .catch(() => setError("Не удалось загрузить метрики"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  const selectPage = (next: Page) => {
    setPage(next);
    window.history.pushState({}, "", next === "competition" ? CHALLENGE_PATH : "/");
  };

  return (
    <div className="min-h-screen bg-bg">
      <header className="max-w-5xl mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h1 className="font-mono text-lg lowercase tracking-wide text-text">Трекер активностей</h1>
          <nav className="flex gap-3 font-mono text-xs">
            <button
              onClick={() => selectPage("dashboard")}
              className={page === "dashboard" ? "text-text" : "text-muted"}
            >
              трекер
            </button>
            <button
              onClick={() => selectPage("competition")}
              className={page === "competition" ? "text-text" : "text-muted"}
            >
              соревнование
            </button>
          </nav>
        </div>

        {page === "dashboard" ? (
          <>
            {error && <p className="text-sm text-red-400 font-mono">{error}</p>}
            {loading && <p className="text-sm text-muted font-mono">загрузка...</p>}

            <div className="flex flex-col gap-3">
              {!loading && metrics.length === 0 && (
                <p className="text-sm text-muted font-mono">Метрик пока нет</p>
              )}
              {metrics.map((metric) => (
                <HeatmapCard key={metric.id} metric={metric} />
              ))}
            </div>
          </>
        ) : (
          <CompetitionPage />
        )}
      </header>
    </div>
  );
}
