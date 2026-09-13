import { useMemo } from "react";

import type { MetricEvent } from "../api";
import { CELL, STEP, weeksInYear } from "./gridConstants";

interface Props {
  year: number;
  events: MetricEvent[];
  color: string;
}

const MONTH_LABELS = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"];
const HIGHLIGHT = "#ff5a36";
const EMPTY = "#21262d";
const ROWS = 14;
const LABEL_HEIGHT = 14;

function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace("#", "");
  return [parseInt(clean.slice(0, 2), 16), parseInt(clean.slice(2, 4), 16), parseInt(clean.slice(4, 6), 16)];
}

function withOpacity(hex: string, opacity: number): string {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

function lerpColor(from: string, to: string, t: number): string {
  const [r1, g1, b1] = hexToRgb(from);
  const [r2, g2, b2] = hexToRgb(to);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);
  return `rgb(${r}, ${g}, ${b})`;
}

function cellColor(color: string, combined: number): string {
  if (combined >= 0.85) {
    return lerpColor(color, HIGHLIGHT, (combined - 0.85) / 0.15);
  }
  const opacity = 0.25 + 0.75 * combined;
  return withOpacity(color, opacity);
}

/**
 * Same total column count as the Yearly heatmap (`weeksInYear`) so cards line up in width.
 * The most recent tracked day is pinned to the rightmost column; if there isn't enough
 * history yet the leftover columns on the left stay blank, and once there's more history
 * than fits, older days fall off the left edge.
 */
export default function GrowthStaircase({ year, events, color }: Props) {
  const { visibleDays, months, maxTotal, columns } = useMemo(() => {
    const columns = weeksInYear(year);
    const sorted = [...events].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
    const visible = sorted.slice(-columns);
    const blanks = columns - visible.length;

    let runningCum = 0;
    let currentMonth = "";
    const cum: number[] = [];
    const monthsMap = new Map<string, { label: string; lastIndex: number; total: number }>();

    visible.forEach((e, i) => {
      const d = new Date(`${e.date}T00:00:00Z`);
      const monthKey = `${d.getUTCFullYear()}-${d.getUTCMonth()}`;
      if (monthKey !== currentMonth) {
        runningCum = 0;
        currentMonth = monthKey;
      }
      runningCum += e.value;
      cum.push(runningCum);

      const columnIndex = blanks + i;
      const existing = monthsMap.get(monthKey);
      if (existing) {
        existing.lastIndex = columnIndex;
        existing.total = runningCum;
      } else {
        monthsMap.set(monthKey, { label: MONTH_LABELS[d.getUTCMonth()], lastIndex: columnIndex, total: runningCum });
      }
    });

    const max = Math.max(0, ...Array.from(monthsMap.values()).map((m) => m.total));

    return {
      visibleDays: visible.map((e, i) => ({ date: e.date, value: e.value, cum: cum[i], columnIndex: blanks + i })),
      months: Array.from(monthsMap.values()),
      maxTotal: max,
      columns,
    };
  }, [events, year]);

  const width = columns * STEP;
  const height = LABEL_HEIGHT + ROWS * STEP;
  const numberFmt = useMemo(() => new Intl.NumberFormat("ru-RU"), []);

  if (maxTotal <= 0) {
    return <p className="text-xs text-muted font-mono h-24 flex items-center">пока нет данных</p>;
  }

  const lastColumnIndex = visibleDays[visibleDays.length - 1]?.columnIndex ?? -1;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      style={{ maxWidth: width, height: "auto", display: "block" }}
      role="img"
      aria-label="Рост посетителей по месяцам"
    >
      {visibleDays.map((day) => {
        const filled = Math.min(ROWS, Math.round((day.cum / maxTotal) * ROWS));
        const colFactor = filled / ROWS;
        const isLastDay = day.columnIndex === lastColumnIndex;
        const cells = [];
        for (let r = 0; r < ROWS; r++) {
          if (r >= filled) {
            cells.push(
              <rect
                key={`bg-${r}`}
                x={day.columnIndex * STEP}
                y={LABEL_HEIGHT + ROWS * STEP - (r + 1) * STEP}
                width={CELL}
                height={CELL}
                rx={2}
                fill={EMPTY}
              />
            );
          }
        }
        for (let r = 0; r < filled; r++) {
          const rowRatio = (r + 1) / filled;
          const combined = Math.min(1, colFactor * 0.4 + rowRatio * 0.6);
          const isTip = isLastDay && r === filled - 1;
          const y = LABEL_HEIGHT + ROWS * STEP - (r + 1) * STEP;
          cells.push(
            <rect
              key={r}
              x={day.columnIndex * STEP}
              y={y}
              width={CELL}
              height={CELL}
              rx={2}
              fill={isTip ? HIGHLIGHT : cellColor(color, combined)}
            >
              <title>{`${day.date}: ${numberFmt.format(day.value)} (накоп. за месяц: ${numberFmt.format(day.cum)})`}</title>
            </rect>
          );
        }
        return <g key={day.date}>{cells}</g>;
      })}
      {months.map((m) => {
        const filled = Math.min(ROWS, Math.round((m.total / maxTotal) * ROWS));
        const peakY = LABEL_HEIGHT + ROWS * STEP - filled * STEP;
        const labelX = (m.lastIndex + 1) * STEP;
        return (
          <text
            key={m.label + m.lastIndex}
            x={labelX}
            y={Math.max(9, peakY - 3)}
            fontSize={9}
            textAnchor="end"
            fill="#7d8590"
            fontFamily="Space Mono, monospace"
          >
            {`${m.label}: ${numberFmt.format(m.total)}`}
          </text>
        );
      })}
    </svg>
  );
}
