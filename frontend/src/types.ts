export type ViewKey = "dashboard" | "candidates" | "jobs" | "matching" | "actions" | "integrations";

export interface DashboardData {
  counts: {
    candidates: number;
    active_candidates: number;
    dormant_candidates: number;
    open_jobs: number;
    applications: number;
    open_actions: number;
    pending_outbox: number;
  };
  pipeline: Record<string, number>;
  actions: ActionItem[];
  activity: AuditItem[];
}

export interface Candidate {
  id: string;
  porters_id: string;
  name: string;
  status: string;
  ca_owner: string;
  role_title: string;
  age: number | null;
  gender: string | null;
  years_experience: number;
  jlpt: string | null;
  desired_salary_million: number | null;
  commute_minutes: number | null;
  work_style: string;
  skills: string[];
  last_contact_date: string | null;
  avg_response_days: number | null;
  notes: string | null;
}

export interface Job {
  id: string;
  porters_id: string;
  company_id: string;
  company_name: string;
  title: string;
  category: string;
  industry: string;
  status: string;
  location: string | null;
  salary_min_million: number | null;
  salary_max_million: number | null;
  received_date: string;
  min_experience_years: number;
  min_jlpt: string | null;
  max_commute_minutes: number | null;
  required_skills: string[];
  ai_candidate_count: number;
}

export interface MatchItem {
  id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_role: string;
  candidate_age: number | null;
  candidate_jlpt: string | null;
  candidate_experience: number;
  candidate_owner: string;
  candidate_notes: string | null;
  job_id: string;
  job_title: string;
  company_name: string;
  score: number;
  scores: Record<string, number>;
  similarity_pct: number;
  ng_check: string;
  evidence_quote: string;
  recommendation_status: string;
  updated_at: string;
}

export interface ActionItem {
  id: string;
  owner_role: "ra" | "ca";
  queue_type: string;
  target_label: string;
  due_date: string;
  severity: "ok" | "due" | "over" | "call";
  reason: string;
  status: "open" | "done" | "snoozed";
  source_ref: string | null;
}

export interface Integration {
  provider: "porters" | "gmail" | "zalo" | "asana";
  configured: boolean;
  status: string;
  last_checked_at: string | null;
  last_success_at: string | null;
  last_error: string | null;
  capabilities: string[];
}

export interface SyncRun {
  id: string;
  provider: string;
  resource: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  records_read: number;
  records_written: number;
  error_message: string | null;
}

export interface OutboxEvent {
  id: string;
  provider: string;
  event_type: string;
  aggregate_id: string;
  status: string;
  attempts: number;
  last_error: string | null;
  available_at: string;
  processed_at: string | null;
}

export interface AuditItem {
  id: number;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, unknown>;
  created_at: string;
}
