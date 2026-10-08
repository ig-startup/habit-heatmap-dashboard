// Shared grid sizing so every metric card's chart lines up at the same cell size and width.
export const CELL = 11;
export const GAP = 3;
export const STEP = CELL + GAP;

/** Day-of-week index with Monday = 0 ... Sunday = 6 (JS getUTCDay() has Sunday = 0). */
export function mondayIndex(date: Date): number {
  return (date.getUTCDay() + 6) % 7;
}

/** Number of week-columns the Yearly heatmap renders for a given year (Monday-aligned grid). */
export function weeksInYear(year: number): number {
  const gridStart = new Date(Date.UTC(year, 0, 1));
  gridStart.setUTCDate(gridStart.getUTCDate() - mondayIndex(gridStart));
  const gridEnd = new Date(Date.UTC(year, 11, 31));
  gridEnd.setUTCDate(gridEnd.getUTCDate() + (6 - mondayIndex(gridEnd)));
  const totalDays = Math.round((gridEnd.getTime() - gridStart.getTime()) / 86400000) + 1;
  return totalDays / 7;
}
