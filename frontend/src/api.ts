import type { ActionItem, AuditItem, Candidate, DashboardData, Integration, Job, MatchItem, OutboxEvent, SyncRun } from "./types";

const API_KEY = import.meta.env.VITE_RAICA_API_KEY as string | undefined;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-RAICA-Key": API_KEY } : {}),
      ...options?.headers,
    },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || payload.error || `HTTP ${response.status}`);
  return payload as T;
}

export const api = {
  health: () => request<{ ok: boolean; version: string; environment: string }>("/health"),
  dashboard: () => request<DashboardData>("/api/v1/dashboard"),
  candidates: (query = "", status = "") => request<Candidate[]>(`/api/v1/candidates?q=${encodeURIComponent(query)}&status=${encodeURIComponent(status)}`),
  jobs: () => request<Job[]>("/api/v1/jobs"),
  matches: (jobId: string) => request<MatchItem[]>(`/api/v1/jobs/${jobId}/matches`),
  rerunMatches: (jobId: string, actor: string) => request<{ generated: number; matches: MatchItem[] }>(`/api/v1/jobs/${jobId}/matches/run`, { method: "POST", body: JSON.stringify({ actor }) }),
  decideMatch: (matchId: string, status: string, actor: string) => request<{ id: string; recommendation_status: string }>(`/api/v1/matches/${matchId}`, { method: "PATCH", body: JSON.stringify({ status, actor }) }),
  actions: (role = "", status = "") => request<ActionItem[]>(`/api/v1/actions?role=${encodeURIComponent(role)}&status=${encodeURIComponent(status)}`),
  updateAction: (actionId: string, status: string, actor: string) => request<ActionItem>(`/api/v1/actions/${actionId}`, { method: "PATCH", body: JSON.stringify({ status, actor }) }),
  integrations: () => request<Integration[]>("/api/v1/integrations"),
  testIntegration: (provider: string, actor: string) => request<{ provider: string; status: string; error: string | null }>(`/api/v1/integrations/${provider}/test`, { method: "POST", body: JSON.stringify({ actor }) }),
  syncPorters: (actor: string) => request<{ id: string; status: string; records_read: number; records_written: number; error_message: string | null }>("/api/v1/sync/porters", { method: "POST", body: JSON.stringify({ actor }) }),
  syncRuns: () => request<SyncRun[]>("/api/v1/sync-runs"),
  outbox: () => request<OutboxEvent[]>("/api/v1/outbox"),
  retryOutbox: (eventId: string, actor: string) => request<{ id: string; status: string; attempts: number; last_error: string | null }>(`/api/v1/outbox/${eventId}/retry`, { method: "POST", body: JSON.stringify({ actor }) }),
  audit: () => request<AuditItem[]>("/api/v1/audit"),
};
