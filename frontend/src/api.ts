export type Unit = "count" | "duration" | "boolean";
export type Aggregation = "sum" | "max" | "last";
export type SourceType = "github" | "webhook" | "manual";

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
