import { useCallback, useEffect, useState } from "react";

import { fetchMetrics, type MetricWithStats } from "./api";
import HeatmapCard from "./components/HeatmapCard";

export default function App() {
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

  return (
    <div className="min-h-screen bg-bg">
      <header className="max-w-5xl mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">
        <h1 className="font-mono text-lg lowercase tracking-wide text-text">Трекер активностей</h1>

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
      </header>
    </div>
  );
}
