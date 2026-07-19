import { ArrowRight, BriefcaseBusiness, MapPin, Sparkles } from "lucide-react";
import { Badge, statusTone } from "../components/Badge";
import { useI18n } from "../i18n";
import type { Job } from "../types";

const statusLabels: Record<string, string> = { open: "募集中", urgent: "急募", phase2: "第2弾", closed: "終了" };

export function JobsView({ jobs, onMatching }: { jobs: Job[]; onMatching: (jobId: string) => void }) {
  const { t } = useI18n();
  return (
    <div className="view-stack">
      <div className="page-heading compact-heading"><div><span className="eyebrow">JOB ORDERS</span><h1>{t("jobOrders")}</h1></div><Badge tone="info">{jobs.length}</Badge></div>
      <section className="jobs-grid">
        {jobs.map(job => (
          <article className="job-card" key={job.id}>
            <div className="job-card-head"><div className="job-icon"><BriefcaseBusiness size={18} /></div><Badge tone={statusTone(job.status)}>{statusLabels[job.status] ?? job.status}</Badge></div>
            <h2>{job.title}</h2><p className="company-name">{job.company_name}</p>
            <div className="job-meta"><span><MapPin size={14} />{job.location || "未登録"}</span><span>{job.received_date}受領</span></div>
            <div className="salary-row"><span>給与レンジ</span><strong>{job.salary_min_million ?? "—"}–{job.salary_max_million ?? "—"}M</strong></div>
            <div className="requirement-list">
              <span>経験 {job.min_experience_years}年以上</span><span>{job.min_jlpt || "日本語不問"}</span><span>{job.preferred_age_min ?? "—"}–{job.preferred_age_max ?? "—"}歳</span><span>{job.remote_mode}</span>
            </div>
            <div className="job-skills">{job.required_skills.map(skill => <span key={skill}>{skill}</span>)}</div>
            <div className="job-card-foot"><div><Sparkles size={15} /><strong>{job.ai_candidate_count}</strong><span>{t("aiCandidates")}</span></div><button className="icon-button" onClick={() => onMatching(job.id)} title={t("viewMatches")}><ArrowRight size={17} /></button></div>
          </article>
        ))}
      </section>
    </div>
  );
}
