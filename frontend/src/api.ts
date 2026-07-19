import type { ActionItem, AiAnalysisResult, AuditItem, Candidate, DashboardData, Integration, Job, MatchItem, OutboxEvent, RecommendationDraft, RevivalData, SyncRun } from "./types";

const API_KEY = import.meta.env.VITE_RAICA_API_KEY as string | undefined;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(API_KEY ? { "X-RAICA-Key": API_KEY } : {}),
      ...options?.headers,
    },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || payload.error || `HTTP ${response.status}`);
  return payload as T;
}

async function requestBlob(path: string): Promise<Blob> {
  const response = await fetch(path, { headers: API_KEY ? { "X-RAICA-Key": API_KEY } : {} });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  return response.blob();
}

export const api = {
  health: () => request<{ ok: boolean; version: string; environment: string }>("/health"),
  dashboard: (role = "ra", owner = "") => request<DashboardData>(`/api/v1/dashboard?role=${encodeURIComponent(role)}&owner=${encodeURIComponent(owner)}`),
  candidates: (query = "", status = "") => request<Candidate[]>(`/api/v1/candidates?q=${encodeURIComponent(query)}&status=${encodeURIComponent(status)}`),
  candidate: (candidateId: string) => request<Candidate>(`/api/v1/candidates/${candidateId}`),
  uploadSkillSheet: (candidateId: string, file: File) => { const form = new FormData(); form.append("file", file); return request<{ candidate: Candidate; analysis: { skills: string[]; specialization: string | null; specialization_years: number } }>(`/api/v1/candidates/${candidateId}/skill-sheet`, { method: "POST", body: form }); },
  downloadSkillSheet: (candidateId: string) => requestBlob(`/api/v1/candidates/${candidateId}/skill-sheet`),
  candidateMatches: (candidateId: string) => request<MatchItem[]>(`/api/v1/candidates/${candidateId}/matches`),
  revival: (role: "ra" | "ca", owner: string) => request<RevivalData>(`/api/v1/revival?role=${encodeURIComponent(role)}&owner=${encodeURIComponent(owner)}`),
  jobs: (query = "", includeClosed = false) => request<Job[]>(`/api/v1/jobs?q=${encodeURIComponent(query)}&include_closed=${includeClosed}`),
  matches: (jobId: string) => request<MatchItem[]>(`/api/v1/jobs/${jobId}/matches`),
  rerunMatches: (jobId: string, actor: string) => request<{ generated: number; matches: MatchItem[] }>(`/api/v1/jobs/${jobId}/matches/run`, { method: "POST", body: JSON.stringify({ actor }) }),
  aiAnalysis: (jobId: string, actor: string) => request<AiAnalysisResult>(`/api/v1/jobs/${jobId}/ai-analysis`, { method: "POST", body: JSON.stringify({ actor }) }),
  decideMatch: (matchId: string, status: string, actor: string) => request<{ id: string; recommendation_status: string; recommendation_draft: RecommendationDraft | null }>(`/api/v1/matches/${matchId}`, { method: "PATCH", body: JSON.stringify({ status, actor }) }),
  recommendationDraft: (matchId: string) => request<RecommendationDraft>(`/api/v1/matches/${matchId}/recommendation-draft`),
  sendContact: (payload: { channel: "gmail" | "zalo" | "phone"; candidate_id?: string; company_id?: string; recipient?: string; subject?: string; body: string; human_approved_by: string }) => request<{ id: string; delivery_status: string; delivery_error: string | null }>("/api/v1/contacts", { method: "POST", body: JSON.stringify(payload) }),
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
