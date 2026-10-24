import { useMemo } from "react";

import type { CompetitionWeekPoint } from "../api";

interface PlayerWeekly {
  label: string;
  color: string;
  weekly: CompetitionWeekPoint[];
}

interface Props {
  players: PlayerWeekly[];
}

const BAR_WIDTH = 22;
const BAR_GAP = 2;
const COLUMN_GAP = 14;
const CHART_HEIGHT = 110;
const LABEL_HEIGHT = 16;

/**
 * Weekly points comparison: one column per week, one bar per player side by side,
 * scaled against the highest points_total in the visible window so the two players
 * are always directly comparable. Continuous bar height (unlike GrowthStaircase's
 * discretized rows) since weekly point totals are a smooth 0..~700 range.
 */
export default function PointsBars({ players }: Props) {
  const weeks = players[0]?.weekly ?? [];
  const columnWidth = players.length * BAR_WIDTH + (players.length - 1) * BAR_GAP;
  const step = columnWidth + COLUMN_GAP;
  const width = weeks.length * step;
  const height = LABEL_HEIGHT + CHART_HEIGHT + LABEL_HEIGHT;

  const maxPoints = useMemo(
    () => Math.max(1, ...players.flatMap((p) => p.weekly.map((w) => w.points_total))),
    [players]
  );

  const dateFmt = useMemo(
    () => new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "2-digit" }),
    []
  );

  if (weeks.length === 0) {
    return <p className="text-xs text-muted font-mono h-24 flex items-center">пока нет данных</p>;
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      style={{ maxWidth: width, height: "auto", display: "block" }}
      role="img"
      aria-label="Баллы по неделям"
    >
      {weeks.map((week, wi) => {
        const x0 = wi * step;
        return (
          <g key={week.week_start}>
            {players.map((player, pi) => {
              const points = player.weekly[wi]?.points_total ?? 0;
              const raw = player.weekly[wi]?.raw_total ?? 0;
              const barHeight = (points / maxPoints) * CHART_HEIGHT;
              const x = x0 + pi * (BAR_WIDTH + BAR_GAP);
              const y = LABEL_HEIGHT + (CHART_HEIGHT - barHeight);
              return (
                <g key={player.label}>
                  <rect
                    x={x}
                    y={y}
                    width={BAR_WIDTH}
                    height={Math.max(0, barHeight)}
                    rx={2}
                    fill={player.color}
                    opacity={points > 0 ? 1 : 0.15}
                  >
                    <title>{`${player.label}, неделя с ${week.week_start}: ${Math.round(points)} баллов (сырое значение: ${raw})`}</title>
                  </rect>
                  {points > 0 && (
                    <text
                      x={x + BAR_WIDTH / 2}
                      y={y - 3}
                      fontSize={9}
                      fill="#e6edf3"
                      fontFamily="Space Mono, monospace"
                      textAnchor="middle"
                    >
                      {Math.round(points)}
                    </text>
                  )}
                </g>
              );
            })}
            <text
              x={x0 + columnWidth / 2}
              y={height - 3}
              fontSize={8}
              fill="#7d8590"
              fontFamily="Space Mono, monospace"
              textAnchor="middle"
            >
              {dateFmt.format(new Date(`${week.week_start}T00:00:00Z`))}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
