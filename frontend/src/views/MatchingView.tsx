import { Check, ChevronDown, CircleGauge, RefreshCw, Sparkles, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge, statusTone } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import type { Job, MatchItem } from "../types";

const scoreLabels: Record<string, string> = { skill: "スキル", experience: "経験", japanese: "日本語", salary: "給与", commute: "通勤" };

export function MatchingView({ jobs, selectedJobId, onJob, matches, loading, onRerun, onDecision }: { jobs: Job[]; selectedJobId: string; onJob: (jobId: string) => void; matches: MatchItem[]; loading: boolean; onRerun: () => void; onDecision: (matchId: string, status: "approved" | "rejected") => Promise<void> }) {
  const [selected, setSelected] = useState<MatchItem | null>(null);
  useEffect(() => setSelected(matches[0] ?? null), [matches]);
  const selectedJob = jobs.find(job => job.id === selectedJobId);

  return (
    <div className="view-stack">
      <div className="page-heading compact-heading"><div><span className="eyebrow">AI MATCHING</span><h1>推薦候補</h1><p>求人要件と候補者DBを5軸で評価し、根拠と一緒に表示します。</p></div><button className="button primary" disabled={!selectedJobId || loading} onClick={onRerun}><RefreshCw size={16} className={loading ? "spin" : ""} />再スコアリング</button></div>
      <div className="matching-layout">
        <aside className="job-picker surface">
          <div className="section-head"><div><h2>対象求人</h2><p>新着・急募順</p></div><ChevronDown size={16} /></div>
          <div className="job-picker-list">
            {jobs.map(job => <button key={job.id} className={selectedJobId === job.id ? "selected" : ""} onClick={() => onJob(job.id)}><span><strong>{job.title}</strong><small>{job.company_name} · {job.location}</small></span><Badge tone={statusTone(job.status)}>{job.ai_candidate_count}</Badge></button>)}
          </div>
        </aside>
        <section className="surface match-list-surface">
          <div className="section-head"><div><h2>{selectedJob?.title ?? "求人を選択"}</h2><p>{selectedJob ? `${selectedJob.company_name} · ${matches.length}名を表示` : "左から求人を選択してください"}</p></div>{selectedJob && <Badge tone="info">閾値 70</Badge>}</div>
          {matches.length ? <div className="match-list">
            {matches.map(item => <button key={item.id} className={`match-row ${selected?.id === item.id ? "selected" : ""}`} onClick={() => setSelected(item)}>
              <div className="person-avatar">{item.candidate_name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div>
              <div className="match-person"><strong>{item.candidate_name}</strong><span>{item.candidate_role} · {item.candidate_experience}年 · {item.candidate_jlpt ?? "JLPT未登録"}</span></div>
              <div className="evidence-preview"><span><Check size={13} />成約類似 {item.similarity_pct}%</span><small>{item.ng_check}</small></div>
              <div className={`score-ring score-${item.score >= 90 ? "high" : item.score >= 80 ? "mid" : "low"}`}><strong>{item.score}</strong></div>
              <Badge tone={statusTone(item.recommendation_status)}>{item.recommendation_status}</Badge>
            </button>)}
          </div> : <EmptyState title={selectedJobId ? "候補者がありません" : "求人を選択"} body={selectedJobId ? "再スコアリングを実行してください。" : "求人を選ぶと候補者を取得します。"} />}
        </section>
        <aside className="inspector match-inspector">
          {selected ? <>
            <div className="match-score-head"><div><span>総合スコア</span><strong>{selected.score}</strong></div><CircleGauge size={28} /></div>
            <h2>{selected.candidate_name}</h2><p className="inspector-subtitle">{selected.candidate_owner} · {selected.candidate_role}</p>
            <div className="score-breakdown">{Object.entries(selected.scores).map(([key, score]) => <div key={key}><span>{scoreLabels[key] ?? key}</span><div><i style={{ width: `${score}%` }} /></div><strong>{score}</strong></div>)}</div>
            <div className="evidence-block"><div><Sparkles size={15} />推薦根拠</div><p>{selected.evidence_quote}</p></div>
            <div className="evidence-block muted"><div>NG照合</div><p>{selected.ng_check}</p></div>
            <div className="decision-row"><button className="button secondary" onClick={() => onDecision(selected.id, "rejected")}><ThumbsDown size={16} />見送り</button><button className="button primary" onClick={() => onDecision(selected.id, "approved")} disabled={selected.recommendation_status === "approved"}><ThumbsUp size={16} />{selected.recommendation_status === "approved" ? "承認済み" : "推薦を承認"}</button></div>
          </> : <EmptyState title="候補者を選択" body="スコアの詳細と推薦根拠を確認できます。" />}
        </aside>
      </div>
    </div>
  );
}
