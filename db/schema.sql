PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS candidates (
  id TEXT PRIMARY KEY,
  porters_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active', 'process', 'dormant')),
  ca_owner TEXT NOT NULL,
  role_title TEXT NOT NULL,
  years_experience REAL NOT NULL DEFAULT 0,
  jlpt TEXT,
  desired_salary_million REAL,
  commute_minutes INTEGER,
  work_style TEXT NOT NULL DEFAULT 'onsite',
  last_contact_date TEXT,
  avg_response_days REAL,
  notes TEXT,
  age INTEGER,
  gender TEXT CHECK (gender IN ('M', 'F') OR gender IS NULL),
  skills_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS companies (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  industry TEXT NOT NULL,
  avg_reply_days REAL,
  hiring_signal TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  porters_id TEXT UNIQUE NOT NULL,
  company_id TEXT NOT NULL,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  industry TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('open', 'urgent', 'phase2', 'closed')),
  salary_min_million REAL,
  salary_max_million REAL,
  received_date TEXT NOT NULL,
  ai_candidate_count INTEGER NOT NULL DEFAULT 0,
  location TEXT,
  min_experience_years REAL NOT NULL DEFAULT 0,
  min_jlpt TEXT,
  max_commute_minutes INTEGER,
  required_skills_json TEXT NOT NULL DEFAULT '[]',
  FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS matches (
  id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL,
  job_id TEXT NOT NULL,
  score INTEGER NOT NULL,
  skill_score INTEGER NOT NULL,
  experience_score INTEGER NOT NULL,
  japanese_score INTEGER NOT NULL,
  salary_score INTEGER NOT NULL,
  commute_score INTEGER NOT NULL,
  similarity_pct INTEGER NOT NULL,
  ng_check TEXT NOT NULL,
  evidence_quote TEXT NOT NULL,
  recommendation_status TEXT NOT NULL DEFAULT 'shortlisted'
    CHECK (recommendation_status IN ('shortlisted', 'approved', 'rejected', 'process')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(candidate_id, job_id),
  FOREIGN KEY (candidate_id) REFERENCES candidates(id),
  FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS contact_logs (
  id TEXT PRIMARY KEY,
  candidate_id TEXT,
  company_id TEXT,
  channel TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
  sent_at TEXT NOT NULL,
  subject TEXT,
  body TEXT,
  human_approved_by TEXT,
  response_at TEXT,
  FOREIGN KEY (candidate_id) REFERENCES candidates(id),
  FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS action_queue (
  id TEXT PRIMARY KEY,
  owner_role TEXT NOT NULL CHECK (owner_role IN ('ra', 'ca')),
  queue_type TEXT NOT NULL,
  target_label TEXT NOT NULL,
  due_date TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('ok', 'due', 'over', 'call')),
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'done', 'snoozed')),
  source_ref TEXT
);

CREATE TABLE IF NOT EXISTS applications (
  id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL,
  job_id TEXT NOT NULL,
  stage TEXT NOT NULL CHECK (stage IN (
    'intent_check', 'recommended', 'screening', 'first_interview',
    'final_interview', 'offer', 'closed_won', 'closed_lost'
  )),
  recommended_at TEXT,
  last_event_at TEXT NOT NULL,
  company_ok INTEGER NOT NULL DEFAULT 0 CHECK (company_ok IN (0, 1)),
  candidate_ok INTEGER NOT NULL DEFAULT 0 CHECK (candidate_ok IN (0, 1)),
  lost_reason TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(candidate_id, job_id),
  FOREIGN KEY (candidate_id) REFERENCES candidates(id),
  FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  details_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_matches_job_score ON matches(job_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_queue_role_status ON action_queue(owner_role, status, due_date);
CREATE INDEX IF NOT EXISTS idx_applications_stage ON applications(stage, last_event_at);
