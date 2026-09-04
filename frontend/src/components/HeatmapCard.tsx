import { useEffect, useState } from "react";

import { fetchHeatmap, type MetricEvent, type MetricWithStats } from "../api";
import Heatmap from "./Heatmap";

function formatValue(metric: MetricWithStats): string {
  if (metric.today_value === null) return "—";
  if (metric.unit === "boolean") return metric.today_value > 0 ? "✓" : "—";
  if (metric.unit === "duration") return `${metric.today_value} мин`;
  return String(metric.today_value);
}

export default function HeatmapCard({ metric }: { metric: MetricWithStats }) {
  const year = new Date().getFullYear();
  const [events, setEvents] = useState<MetricEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchHeatmap(metric.id, year)
      .then((data) => {
        if (!cancelled) setEvents(data);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [metric.id, year]);

  return (
    <div className="bg-surface border border-border rounded-lg p-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-2xl">{metric.icon}</span>
        <span className="font-mono text-sm text-text">{metric.name}</span>
      </div>

      <div className="overflow-x-auto">
        {loading ? (
          <div className="h-24 flex items-center text-muted text-xs font-mono">загрузка...</div>
        ) : (
          <Heatmap year={year} events={events} color={metric.color} />
        )}
      </div>

      <div className="flex items-center gap-4 shrink-0 justify-between sm:justify-end">
        <span className="font-mono text-sm text-muted" title="Текущий streak">
          🔥 {metric.streak}
        </span>
        <span className="font-mono text-xs text-muted">{metric.total_days_tracked} дн.</span>
        <span className="font-mono text-sm px-2 py-1 rounded bg-bg border border-border text-text">
          {formatValue(metric)}
        </span>
      </div>
    </div>
  );
}
