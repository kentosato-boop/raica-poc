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
  notes TEXT
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
