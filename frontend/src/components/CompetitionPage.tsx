import { useEffect, useState } from "react";

import { fetchCompetition, type CompetitionOut } from "../api";
import Heatmap from "./Heatmap";
import PointsBars from "./PointsBars";

export default function CompetitionPage() {
  const year = new Date().getFullYear();
  const [competition, setCompetition] = useState<CompetitionOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchCompetition()
      .then((data) => {
        if (!cancelled) setCompetition(data);
      })
      .catch(() => {
        if (!cancelled) setError("Не удалось загрузить соревнование");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <p className="text-sm text-muted font-mono">загрузка...</p>;
  }
  if (error || !competition) {
    return <p className="text-sm text-red-400 font-mono">{error ?? "Нет данных"}</p>;
  }

  const [a, b] = competition.players;
  const leader =
    a && b
      ? a.cumulative_points === b.cumulative_points
        ? "Ничья"
        : a.cumulative_points > b.cumulative_points
          ? `${a.label} ведёт`
          : `${b.label} ведёт`
      : null;

  return (
    <div className="flex flex-col gap-6">
      {leader && <p className="font-mono text-sm text-text">{leader}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {competition.players.map((player) => (
          <div
            key={player.id}
            className="bg-surface border border-border rounded-lg p-5 flex flex-col gap-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{player.icon}</span>
                <span className="font-mono text-sm text-text">{player.label}</span>
              </div>
              <span className="font-mono text-lg text-text">{Math.round(player.cumulative_points)}</span>
            </div>

            {player.metric_found ? (
              <Heatmap
                year={year}
                range={{ startDate: competition.start_date, weeks: competition.weeks }}
                events={player.daily.map((d) => ({ date: d.date, value: d.value, meta: {} }))}
                color={player.color}
              />
            ) : (
              <p className="text-xs text-muted font-mono h-24 flex items-center">пока нет данных</p>
            )}
          </div>
        ))}
      </div>

      <div className="bg-surface border border-border rounded-lg p-5 flex flex-col gap-4">
        <span className="font-mono text-sm text-text">Баллы по неделям</span>
        <PointsBars
          players={competition.players.map((p) => ({ label: p.label, color: p.color, weekly: p.weekly }))}
        />
      </div>
    </div>
  );
}
