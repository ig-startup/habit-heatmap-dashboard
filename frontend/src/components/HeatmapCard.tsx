import { useEffect, useState } from "react";

import { fetchHeatmap, type MetricEvent, type MetricWithStats } from "../api";
import Heatmap from "./Heatmap";

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
    <div className="bg-surface border border-border rounded-lg p-5 flex flex-col gap-4">
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-2xl">{metric.icon}</span>
        <span className="font-mono text-sm text-text">{metric.name}</span>
      </div>

      {loading ? (
        <div className="h-24 flex items-center text-muted text-xs font-mono">загрузка...</div>
      ) : (
        <Heatmap year={year} events={events} color={metric.color} />
      )}
    </div>
  );
}
