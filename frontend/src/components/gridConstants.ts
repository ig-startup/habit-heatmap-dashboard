// Shared grid sizing so every metric card's chart lines up at the same cell size and width.
export const CELL = 11;
export const GAP = 3;
export const STEP = CELL + GAP;

/** Number of week-columns the Yearly heatmap renders for a given year (Sunday-aligned grid). */
export function weeksInYear(year: number): number {
  const gridStart = new Date(Date.UTC(year, 0, 1));
  gridStart.setUTCDate(gridStart.getUTCDate() - gridStart.getUTCDay());
  const gridEnd = new Date(Date.UTC(year, 11, 31));
  gridEnd.setUTCDate(gridEnd.getUTCDate() + (6 - gridEnd.getUTCDay()));
  const totalDays = Math.round((gridEnd.getTime() - gridStart.getTime()) / 86400000) + 1;
  return totalDays / 7;
}
