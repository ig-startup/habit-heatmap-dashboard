import { useCallback, useEffect, useState } from "react";

import { fetchMetrics, type MetricWithStats } from "./api";
import AddMetricModal from "./components/AddMetricModal";
import HeatmapCard from "./components/HeatmapCard";
import ViewSwitcher from "./components/ViewSwitcher";

export default function App() {
  const [metrics, setMetrics] = useState<MetricWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

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
        <div className="flex items-center justify-between">
          <h1 className="font-mono text-lg lowercase tracking-wide text-text">habit heatmap dashboard</h1>
          <button
            onClick={() => setModalOpen(true)}
            className="w-8 h-8 flex items-center justify-center rounded border border-border text-muted hover:text-text hover:border-text font-mono text-lg leading-none"
            aria-label="Добавить метрику"
          >
            +
          </button>
        </div>

        <ViewSwitcher active="yearly" />

        {error && <p className="text-sm text-red-400 font-mono">{error}</p>}
        {loading && <p className="text-sm text-muted font-mono">загрузка...</p>}

        <div className="flex flex-col gap-3">
          {!loading && metrics.length === 0 && (
            <p className="text-sm text-muted font-mono">Метрик пока нет — добавь первую через "+"</p>
          )}
          {metrics.map((metric) => (
            <HeatmapCard key={metric.id} metric={metric} />
          ))}
        </div>
      </header>

      {modalOpen && <AddMetricModal onClose={() => setModalOpen(false)} onCreated={load} />}
    </div>
  );
}
