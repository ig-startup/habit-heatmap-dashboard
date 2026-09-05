import { useMemo } from "react";

import type { MetricEvent } from "../api";

interface Props {
  year: number;
  events: MetricEvent[];
  color: string;
}

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const CELL = 11;
const GAP = 3;
const STEP = CELL + GAP;

function intensityLevel(value: number, max: number): number {
  if (value <= 0 || max <= 0) return 0;
  const ratio = value / max;
  if (ratio <= 0.25) return 1;
  if (ratio <= 0.5) return 2;
  if (ratio <= 0.75) return 3;
  return 4;
}

function levelColor(level: number, color: string): string {
  if (level === 0) return "#21262d";
  const opacity = [0, 0.3, 0.5, 0.75, 1][level];
  return withOpacity(color, opacity);
}

function withOpacity(hex: string, opacity: number): string {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

export default function Heatmap({ year, events, color }: Props) {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const { weeks, monthPositions, maxValue } = useMemo(() => {
    const valueByDate = new Map(events.map((e) => [e.date, e.value]));
    const start = new Date(Date.UTC(year, 0, 1));
    // align grid start to the Sunday on/before Jan 1
    const gridStart = new Date(start);
    gridStart.setUTCDate(gridStart.getUTCDate() - gridStart.getUTCDay());
    const end = new Date(Date.UTC(year, 11, 31));

    const days: { date: string; value: number; inYear: boolean }[] = [];
    const cursor = new Date(gridStart);
    while (cursor <= end || cursor.getUTCDay() !== 0) {
      const iso = cursor.toISOString().slice(0, 10);
      days.push({
        date: iso,
        value: valueByDate.get(iso) ?? 0,
        inYear: cursor.getUTCFullYear() === year,
      });
      cursor.setUTCDate(cursor.getUTCDate() + 1);
      if (cursor > end && cursor.getUTCDay() === 0) break;
    }

    const weeksArr: typeof days[] = [];
    for (let i = 0; i < days.length; i += 7) {
      weeksArr.push(days.slice(i, i + 7));
    }

    const months: { label: string; weekIndex: number }[] = [];
    let lastMonth = -1;
    weeksArr.forEach((week, idx) => {
      const firstInYearDay = week.find((d) => d.inYear);
      if (!firstInYearDay) return;
      const month = new Date(firstInYearDay.date).getUTCMonth();
      if (month !== lastMonth) {
        months.push({ label: MONTH_LABELS[month], weekIndex: idx });
        lastMonth = month;
      }
    });

    const max = Math.max(0, ...events.map((e) => e.value));

    return { weeks: weeksArr, monthPositions: months, maxValue: max };
  }, [year, events]);

  const width = weeks.length * STEP;
  const height = 7 * STEP + 16;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      style={{ maxWidth: width, height: "auto", display: "block" }}
      role="img"
      aria-label={`Активность за ${year} год`}
    >
      {monthPositions.map((m) => (
        <text
          key={`${m.label}-${m.weekIndex}`}
          x={m.weekIndex * STEP}
          y={10}
          fontSize={10}
          fill="#7d8590"
          fontFamily="Space Mono, monospace"
        >
          {m.label}
        </text>
      ))}
      {weeks.map((week, wi) =>
        week.map((day, di) => {
          if (!day.inYear) return null;
          const level = intensityLevel(day.value, maxValue);
          const isToday = day.date === today;
          return (
            <rect
              key={day.date}
              x={wi * STEP}
              y={16 + di * STEP}
              width={CELL}
              height={CELL}
              rx={2}
              fill={levelColor(level, color)}
              stroke={isToday ? "#e6edf3" : "none"}
              strokeWidth={isToday ? 1.5 : 0}
            >
              <title>{`${day.date}: ${day.value}`}</title>
            </rect>
          );
        })
      )}
    </svg>
  );
}
