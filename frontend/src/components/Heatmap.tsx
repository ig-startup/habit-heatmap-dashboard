import { useMemo } from "react";

import type { MetricEvent } from "../api";
import { CELL, GAP, STEP, mondayIndex } from "./gridConstants";

interface Props {
  year: number;
  events: MetricEvent[];
  color: string;
}

const MONTH_LABELS = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"];

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
    // align grid start to the Monday on/before Jan 1
    const gridStart = new Date(start);
    gridStart.setUTCDate(gridStart.getUTCDate() - mondayIndex(gridStart));
    const end = new Date(Date.UTC(year, 11, 31));

    const days: { date: string; value: number; inYear: boolean }[] = [];
    const cursor = new Date(gridStart);
    while (cursor <= end || mondayIndex(cursor) !== 0) {
      const iso = cursor.toISOString().slice(0, 10);
      days.push({
        date: iso,
        value: valueByDate.get(iso) ?? 0,
        inYear: cursor.getUTCFullYear() === year,
      });
      cursor.setUTCDate(cursor.getUTCDate() + 1);
      if (cursor > end && mondayIndex(cursor) === 0) break;
    }

    const weeksArr: typeof days[] = [];
    for (let i = 0; i < days.length; i += 7) {
      weeksArr.push(days.slice(i, i + 7));
    }

    // One entry per month boundary, pinpointing the exact cell (week column + day row)
    // where the new month starts — a week column can hold the tail of one month and the
    // start of the next, so the boundary isn't always a clean column edge.
    const months: { label: string; weekIndex: number; dayRow: number }[] = [];
    days.forEach((d, i) => {
      if (!d.inYear) return;
      const prevInYear = i > 0 && days[i - 1].inYear;
      const isNewMonth = !prevInYear || new Date(days[i - 1].date).getUTCMonth() !== new Date(d.date).getUTCMonth();
      if (isNewMonth) {
        months.push({ label: MONTH_LABELS[new Date(d.date).getUTCMonth()], weekIndex: Math.floor(i / 7), dayRow: i % 7 });
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
      {monthPositions.slice(1).map((m) => {
        const colLeft = m.weekIndex * STEP - GAP / 2;
        const colRight = colLeft + STEP;
        const rowTop = 16 + m.dayRow * STEP - GAP / 2;
        // dayRow 0: the new month starts on a Monday, so the boundary is a plain column
        // edge. Otherwise it's a staircase: the row above rowTop in this column is still
        // the old month, so the line steps out to the right edge for those rows.
        const pathD =
          m.dayRow === 0
            ? `M ${colLeft} 16 L ${colLeft} ${height}`
            : `M ${colRight} 16 L ${colRight} ${rowTop} L ${colLeft} ${rowTop} L ${colLeft} ${height}`;
        return (
          <path
            key={`sep-${m.label}-${m.weekIndex}-${m.dayRow}`}
            d={pathD}
            fill="none"
            stroke="#30363d"
            strokeWidth={1}
          />
        );
      })}
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
