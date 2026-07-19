import { Check, CircleGauge, FileText, RefreshCw, Sparkles, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge, statusTone } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import type { Job, MatchItem } from "../types";

const scoreLabels: Record<string, Record<string, string>> = {
  ja: { skill: "スキル", experience: "総経験", japanese: "日本語", salary: "給与", commute: "通勤", age: "年齢", remote: "勤務形態", specialization: "専門経験", stability: "職歴安定" },
  vi: { skill: "Kỹ năng", experience: "Kinh nghiệm", japanese: "Tiếng Nhật", salary: "Lương", commute: "Đi lại", age: "Tuổi", remote: "Cách làm việc", specialization: "Chuyên môn", stability: "Ổn định" },
  en: { skill: "Skills", experience: "Experience", japanese: "Japanese", salary: "Salary", commute: "Commute", age: "Age", remote: "Work style", specialization: "Specialty", stability: "Stability" },
};

export function MatchingView({ jobs, selectedJobId, onJob, matches, loading, onRerun, onDecision }: { jobs: Job[]; selectedJobId: string; onJob: (jobId: string) => void; matches: MatchItem[]; loading: boolean; onRerun: () => void; onDecision: (matchId: string, status: "approved" | "rejected") => Promise<void> }) {
  const { t, locale } = useI18n();
  const [selected, setSelected] = useState<MatchItem | null>(null);
  useEffect(() => setSelected(matches[0] ?? null), [matches]);
  const selectedJob = jobs.find(job => job.id === selectedJobId);

  return (
    <div className="view-stack">
      <div className="page-heading compact-heading"><div><span className="eyebrow">AI MATCHING</span><h1>{t("matchingTitle")}</h1></div><button className="button primary" disabled={!selectedJobId || loading} onClick={onRerun}><RefreshCw size={16} className={loading ? "spin" : ""} />{t("rerun")}</button></div>
      <div className="job-context-bar surface"><div><span>対象案件</span><strong>{selectedJob?.company_name} · {selectedJob?.title}</strong></div><select value={selectedJobId} onChange={event => onJob(event.target.value)}>{jobs.map(job => <option key={job.id} value={job.id}>{job.company_name} / {job.title}</option>)}</select></div>
      <div className="matching-layout">
        <section className="surface match-list-surface">
          <div className="section-head"><div><h2>{t("aiCandidates")}</h2><p>{matches.length}</p></div>{selectedJob && <Badge tone="info">AI</Badge>}</div>
          {matches.length ? <div className="match-list">
            {matches.map(item => <button key={item.id} className={`match-row ${selected?.id === item.id ? "selected" : ""}`} onClick={() => setSelected(item)}>
              <div className="person-avatar">{item.candidate_name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div>
              <div className="match-person"><strong>{item.candidate_name}</strong><span>{item.candidate_role} · {item.candidate_experience}年 · {item.candidate_jlpt ?? "—"}</span><small>{t("internalParallel")} {item.candidate_internal_parallel} / {t("externalParallel")} {item.candidate_external_parallel}</small></div>
              <div className="evidence-preview"><span><Check size={13} />{t("evidence")}</span><small>{item.evidence_quote}</small></div>
              <div className={`score-ring score-${item.score >= 90 ? "high" : item.score >= 80 ? "mid" : "low"}`}><strong>{item.score}</strong></div>
              <Badge tone={statusTone(item.recommendation_status)}>{item.recommendation_status}</Badge>
            </button>)}
          </div> : <EmptyState title="No recommendations" body={t("rerun")} />}
        </section>
        <aside className="inspector match-inspector">
          {selected ? <>
            <div className="match-score-head"><div><span>AI score</span><strong>{selected.score}</strong></div><CircleGauge size={28} /></div>
            <h2>{selected.candidate_name}</h2><p className="inspector-subtitle">{selected.candidate_owner} · {selected.candidate_role}</p>
            <div className="parallel-summary"><div><span>{t("internalParallel")}</span><strong>{selected.candidate_internal_parallel}</strong></div><div><span>{t("externalParallel")}</span><strong>{selected.candidate_external_parallel}</strong></div></div>
            <div className="score-breakdown">{Object.entries(selected.scores).map(([key, score]) => <div key={key}><span>{scoreLabels[locale][key] ?? key}</span><div><i style={{ width: `${score}%` }} /></div><strong>{score}</strong></div>)}</div>
            <div className="evidence-block"><div><Sparkles size={15} />{t("evidence")}</div><p>{selected.evidence_quote}</p></div>
            <div className="evidence-block muted"><div>{t("ngCheck")}</div><p>{selected.ng_check}</p></div>
            <div className="attachment-line"><FileText size={14} /><span>{selected.candidate_skill_sheet || t("noAttachment")}</span></div>
            <div className="decision-row"><button className="button secondary" onClick={() => onDecision(selected.id, "rejected")}><ThumbsDown size={16} />{t("reject")}</button><button className="button primary" onClick={() => onDecision(selected.id, "approved")}><ThumbsUp size={16} />{selected.recommendation_status === "approved" ? t("approved") : t("approve")}</button></div>
          </> : <EmptyState title={t("details")} body="Select a candidate." />}
        </aside>
      </div>
    </div>
  );
}
