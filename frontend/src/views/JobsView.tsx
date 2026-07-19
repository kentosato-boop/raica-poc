import { Check, FileText, RefreshCw, Sparkles, X } from "lucide-react";
import { Badge, statusTone } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import type { Job, MatchItem } from "../types";

const statusLabels: Record<string, string> = { open: "募集中", urgent: "急募", phase2: "第2弾", closed: "終了" };
const workLabels: Record<string, string> = { remote: "リモート", onsite: "常駐", hybrid: "ハイブリッド" };

export function JobsView({ role, search, jobs, selectedJobId, onSelect, matches, loading, onRerun, onDecision }: {
  role: "ra" | "ca"; search: string; jobs: Job[]; selectedJobId: string; onSelect: (jobId: string) => void; matches: MatchItem[];
  loading: boolean; onRerun: () => void; onDecision: (id: string, status: "approved" | "rejected") => void;
}) {
  const { t } = useI18n(); const selected = jobs.find(job => job.id === selectedJobId) || null;
  return <div className="view-stack">
    <div className="page-heading compact-heading"><div><span className="eyebrow">JOB DATABASE</span><h1>{t("jobOrders")}</h1><p>{search ? `「${search}」を企業情報・案件要件から検索` : "案件条件と推薦候補を同じ画面で確認"}</p></div><Badge tone="info">{jobs.length}件</Badge></div>
    <section className="surface table-surface database-surface">{jobs.length ? <div className="table-scroll"><table className="data-table database-table jobs-table"><thead><tr><th>案件・企業</th><th>状態</th><th>勤務地</th><th>給与</th><th>経験</th><th>年齢</th><th>勤務形態</th><th>専門領域</th><th>推薦候補</th><th>受領日</th></tr></thead><tbody>{jobs.map(job => <tr key={job.id} className={selectedJobId === job.id ? "selected-row" : ""} onClick={() => onSelect(job.id)}><td><strong>{job.title}</strong><small>{job.company_name} · {job.porters_id}</small>{job.search_match && <span className="search-match">{job.search_match}一致</span>}</td><td><Badge tone={statusTone(job.status)}>{statusLabels[job.status] || job.status}</Badge></td><td>{job.location || "—"}</td><td>{job.salary_min_million ?? "—"}–{job.salary_max_million ?? "—"}M</td><td>{job.min_specialization_years || job.min_experience_years}年以上</td><td>{job.preferred_age_min ?? "—"}–{job.preferred_age_max ?? "—"}歳</td><td>{workLabels[job.remote_mode] || job.remote_mode}</td><td>{job.specialization || "—"}</td><td><Badge tone="success">{job.ai_candidate_count}名</Badge></td><td>{job.received_date}</td></tr>)}</tbody></table></div> : <EmptyState title="案件がありません" body="検索条件を変更してください。" />}</section>
    {selected && <section className="surface job-recommendation-panel"><div className="section-head"><div><span className="eyebrow">{role === "ra" ? "RA RECOMMENDATION" : "JOB DETAIL"}</span><h2>{selected.company_name} / {selected.title}</h2><p>{selected.required_skills.join(" · ")} · {workLabels[selected.remote_mode] || selected.remote_mode}</p></div>{role === "ra" && <button className="button primary" disabled={loading} onClick={onRerun}><RefreshCw size={16} className={loading ? "spin" : ""} />AIで推薦候補を更新</button>}</div>
      {role === "ra" && <div className="recommendation-table"><div className="recommendation-head"><span>推薦候補</span><span>適合度</span><span>根拠</span><span>並行状況</span><span>判断</span></div>{matches.map(match => <div className="recommendation-row" key={match.id}><div className="person-cell"><div className="person-avatar">{match.candidate_name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div><div><strong>{match.candidate_name}</strong><small>{match.candidate_role} · {match.candidate_experience}年</small></div></div><strong className="match-score">{match.score}</strong><p><Sparkles size={14} />{match.evidence_quote}</p><div className="parallel-compact"><span>社内 {match.candidate_internal_parallel}</span><span>社外 {match.candidate_external_parallel}</span>{match.candidate_skill_sheet && <span><FileText size={12} />PDF</span>}</div><div className="decision-buttons"><button title="推薦を承認" onClick={() => onDecision(match.id, "approved")}><Check size={15} /></button><button title="見送り" onClick={() => onDecision(match.id, "rejected")}><X size={15} /></button></div></div>)}</div>}
    </section>}
  </div>;
}
