export type Unit = "count" | "duration" | "boolean";
export type Aggregation = "sum" | "max" | "last";
export type SourceType = "github" | "metrika" | "ton" | "webhook" | "manual";

export interface MetricWithStats {
  id: number;
  name: string;
  icon: string;
  color: string;
  unit: Unit;
  aggregation: Aggregation;
  source_type: SourceType;
  created_at: string;
  today_value: number | null;
  streak: number;
  total_days_tracked: number;
}

export interface MetricEvent {
  date: string;
  value: number;
  meta: Record<string, unknown>;
}

const API_BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status}`);
  }
  return res.json();
}

export function fetchMetrics(): Promise<MetricWithStats[]> {
  return request<MetricWithStats[]>("/metrics");
}

export function fetchHeatmap(metricId: number, year: number): Promise<MetricEvent[]> {
  return request<MetricEvent[]>(`/metrics/${metricId}/heatmap?year=${year}`);
}

export interface CompetitionDailyPoint {
  date: string;
  value: number;
  points: number;
}

export interface CompetitionWeekPoint {
  week_start: string;
  raw_total: number;
  points_total: number;
}

export interface CompetitionPlayer {
  id: string;
  label: string;
  icon: string;
  color: string;
  metric_found: boolean;
  daily: CompetitionDailyPoint[];
  weekly: CompetitionWeekPoint[];
  cumulative_points: number;
}

export interface CompetitionOut {
  start_date: string;
  weeks: number;
  players: CompetitionPlayer[];
}

export function fetchCompetition(): Promise<CompetitionOut> {
  return request<CompetitionOut>("/competition");
}

export interface CreateMetricInput {
  name: string;
  icon: string;
  unit: Unit;
}

export function createMetric(input: CreateMetricInput): Promise<MetricWithStats> {
  return request<MetricWithStats>("/metrics", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
