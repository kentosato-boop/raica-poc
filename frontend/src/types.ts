export type ViewKey = "dashboard" | "candidates" | "jobs" | "matching" | "revival" | "actions" | "integrations";

export interface DashboardData {
  counts: {
    candidates: number;
    active_candidates: number;
    dormant_candidates: number;
    open_jobs: number;
    applications: number;
    open_actions: number;
    pending_outbox: number;
    recommendations: number;
    interviews: number;
    closed_won: number;
    new_jobs: number;
    new_inflow: number;
  };
  pipeline: Record<string, number>;
  pipeline_scope: string;
  companies: string[];
  actions: ActionItem[];
  my_actions: ActionItem[];
  waiting_actions: ActionItem[];
  new_inflow: NewInflowLead[];
  targets: { recommendations: number; interviews: number; closed_won: number; new_jobs: number };
  activity: AuditItem[];
}

export interface NewInflowLead {
  id: string;
  name: string;
  specialization: string | null;
  role_title: string;
  ca_owner: string;
  inflow_days: number;
}

export interface Candidate {
  id: string;
  porters_id: string;
  name: string;
  status: string;
  ca_owner: string;
  email: string | null;
  role_title: string;
  age: number | null;
  gender: string | null;
  years_experience: number;
  jlpt: string | null;
  current_salary_million: number | null;
  desired_salary_million: number | null;
  commute_minutes: number | null;
  work_style: string;
  work_style_options: string[];
  remote_preference: string;
  specialization: string | null;
  specialization_years: number;
  recent_tenure_years: number;
  current_location: string | null;
  desired_locations: string[];
  inflow_date: string | null;
  inflow_days: number | null;
  available_from: string | null;
  work_authorization: string | null;
  source_channel: string | null;
  preferred_contact_channel: string | null;
  consent_status: string;
  skills: string[];
  internal_parallel_count: number;
  external_parallel_count: number;
  current_processes: Array<{ scope: "internal" | "external"; label: string; stage: string }>;
  skill_sheet_filename: string | null;
  skill_sheet_uploaded_at: string | null;
  last_contact_date: string | null;
  avg_response_days: number | null;
  notes: string | null;
  search_match?: string;
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
  preferred_age_min: number | null;
  preferred_age_max: number | null;
  remote_mode: string;
  specialization: string | null;
  min_specialization_years: number;
  min_jlpt: string | null;
  max_commute_minutes: number | null;
  required_skills: string[];
  ai_candidate_count: number;
  search_match?: string;
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
  candidate_internal_parallel: number;
  candidate_external_parallel: number;
  candidate_skill_sheet: string | null;
  job_id: string;
  job_title: string;
  company_name: string;
  score: number;
  scores: Record<string, number>;
  ai_rank: number | null;
  ai_recommended: boolean;
  ng_check: string;
  evidence_quote: string;
  recommendation_status: string;
  updated_at: string;
}

export interface AiAnalysisEntry {
  candidate_id: string;
  candidate_name: string;
  fit_reason: string;
  concerns: string;
  verdict: "推薦" | "要検討" | "見送り検討" | string;
}

export interface AiAnalysisResult {
  job_id: string;
  source: "llm" | "rule-based" | "none";
  model: string | null;
  reason: string | null;
  analyses: AiAnalysisEntry[];
}

export interface RevivalItem {
  id: string;
  kind: "company" | "candidate";
  name: string;
  owner: string;
  primary_label: string;
  secondary_label: string;
  last_contact_date: string | null;
  dormant_days: number;
  priority_score: number;
  status: string;
  signal: string | null;
  reason: string | null;
  recommendation: string;
  channel: string;
  target_id: string;
  job_id?: string | null;
  job_title?: string | null;
  company_name?: string | null;
}

export interface RevivalData {
  role: "ra" | "ca";
  mode: "company_job_revival" | "candidate_job_revival";
  items: RevivalItem[];
}

export interface ActionItem {
  id: string;
  owner_role: "ra" | "ca";
  ball_owner: "mine" | "theirs";
  queue_type: string;
  target_label: string;
  due_date: string;
  severity: "ok" | "due" | "over" | "call";
  reason: string;
  status: "open" | "done" | "snoozed";
  source_ref: string | null;
  target_type: "candidate" | "job" | null;
  target_id: string | null;
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

export interface RecommendationDraft {
  match_id: string;
  candidate_id: string;
  company_id: string;
  recipient_label: string;
  recipient: string | null;
  subject: string;
  body: string;
  skill_sheet_filename: string | null;
}
