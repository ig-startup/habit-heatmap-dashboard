import { useMemo } from "react";

import type { MetricEvent } from "../api";
import { CELL, STEP, weeksInYear } from "./gridConstants";

interface Props {
  year: number;
  events: MetricEvent[];
}

const MONTH_LABELS = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"];
const DARK_BG = "#21262d";
const LIGHT_GRAY = "#454c54";
const ORANGE = "#ff5a36";
const ROWS = 7;
const LABEL_HEIGHT = 16;

/**
 * Same total column count as the Yearly heatmap (`weeksInYear`) so cards line up in width.
 * Each column is one day: the light-gray bar is that day's trailing 7-day max (rolling
 * window), the orange bar on top of it is the day's actual value. Both are scaled against
 * the highest 7-day max in the visible window, so the tallest recent week reaches full height.
 */
export default function GrowthStaircase({ year, events }: Props) {
  const { visibleDays, months, maxScale, columns } = useMemo(() => {
    const columns = weeksInYear(year);
    const valueByDate = new Map(events.map((e) => [e.date, e.value]));
    const sorted = [...events].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
    const visible = sorted.slice(-columns);
    const blanks = columns - visible.length;

    const withWeekMax = visible.map((e) => {
      const d = new Date(`${e.date}T00:00:00Z`);
      let weekMax = 0;
      for (let i = 0; i < 7; i++) {
        const dd = new Date(d);
        dd.setUTCDate(dd.getUTCDate() - i);
        const iso = dd.toISOString().slice(0, 10);
        const v = valueByDate.get(iso) ?? 0;
        if (v > weekMax) weekMax = v;
      }
      return { date: e.date, value: e.value, weekMax };
    });

    const maxScale = Math.max(0, ...withWeekMax.map((d) => d.weekMax));

    const monthsMap = new Map<string, { label: string; weekIndex: number }>();
    withWeekMax.forEach((d, i) => {
      const dt = new Date(`${d.date}T00:00:00Z`);
      const monthKey = `${dt.getUTCFullYear()}-${dt.getUTCMonth()}`;
      if (!monthsMap.has(monthKey)) {
        monthsMap.set(monthKey, { label: MONTH_LABELS[dt.getUTCMonth()], weekIndex: blanks + i });
      }
    });

    return {
      visibleDays: withWeekMax.map((d, i) => ({ ...d, columnIndex: blanks + i })),
      months: Array.from(monthsMap.values()),
      maxScale,
      columns,
    };
  }, [events, year]);

  const width = columns * STEP;
  const height = LABEL_HEIGHT + ROWS * STEP;
  const numberFmt = useMemo(() => new Intl.NumberFormat("ru-RU"), []);

  if (maxScale <= 0) {
    return <p className="text-xs text-muted font-mono h-24 flex items-center">пока нет данных</p>;
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      style={{ maxWidth: width, height: "auto", display: "block" }}
      role="img"
      aria-label="Посетители сайта: сегодня против максимума за неделю"
    >
      {months.map((m) => (
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
      {visibleDays.map((day) => {
        const grayFilled = Math.min(ROWS, Math.round((day.weekMax / maxScale) * ROWS));
        const orangeFilled = Math.min(ROWS, Math.round((day.value / maxScale) * ROWS));
        const cells = [];
        for (let r = 0; r < ROWS; r++) {
          const fill = r < orangeFilled ? ORANGE : r < grayFilled ? LIGHT_GRAY : DARK_BG;
          const y = LABEL_HEIGHT + ROWS * STEP - (r + 1) * STEP;
          cells.push(
            <rect key={r} x={day.columnIndex * STEP} y={y} width={CELL} height={CELL} rx={2} fill={fill}>
              <title>{`${day.date}: ${numberFmt.format(day.value)} (макс. за неделю: ${numberFmt.format(day.weekMax)})`}</title>
            </rect>
          );
        }
        return <g key={day.date}>{cells}</g>;
      })}
    </svg>
  );
}
