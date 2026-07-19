import { ArrowUpRight, Circle, CircleDot, Clock3 } from "lucide-react";
import { Badge, statusTone } from "../components/Badge";
import { useI18n } from "../i18n";
import type { ActionItem, DashboardData } from "../types";

function ActionList({ title, subtitle, items, waiting, onOpen }: { title: string; subtitle: string; items: ActionItem[]; waiting?: boolean; onOpen: () => void }) {
  return <section className="surface desk-list"><div className="section-head"><div><h2>{waiting ? <Circle size={15} /> : <CircleDot size={15} />}{title}</h2><p>{subtitle}</p></div><Badge tone={waiting ? "neutral" : "danger"}>{items.length}</Badge></div><div className="action-list">{items.map(item => <button className="action-row" key={item.id} onClick={onOpen}><span className={`severity-dot severity-${item.severity}`} /><span className="action-copy"><strong>{item.target_label}</strong><small>{item.reason}</small></span><span className="action-meta"><Badge tone={statusTone(item.severity)}>{item.severity === "over" ? "期限超過" : item.severity === "call" ? "電話" : item.severity === "due" ? "今日" : "未着手"}</Badge><small>{item.due_date}</small></span></button>)}</div></section>;
}

export function DashboardView({ data, role, onOpenActions }: { data: DashboardData | null; role: "ra" | "ca"; onOpenActions: () => void }) {
  const { t } = useI18n(); const counts = data?.counts; const targets = data?.targets;
  const kpis = [
    { key: "recommendations", label: t("recommendations"), value: counts?.recommendations ?? 0, target: targets?.recommendations ?? 20, tone: "green", note: "推薦予定と承認済みを集計" },
    { key: "interviews", label: t("interviews"), value: counts?.interviews ?? 0, target: targets?.interviews ?? 12, tone: "blue", note: "今月の面接・面談設定" },
    { key: "closed", label: t("wins"), value: counts?.closed_won ?? 0, target: targets?.closed_won ?? 3, tone: "red", note: "今月の成約目標" },
    { key: "jobs", label: t("newJobs"), value: counts?.new_jobs ?? 0, target: targets?.new_jobs ?? 6, tone: "blue", note: "直近7日間の新規案件" },
  ];
  return <div className="view-stack desk-view">
    <div className="page-heading dashboard-heading"><div><span className="eyebrow">MY DESK</span><h1>マイデスク <span>— {role === "ra" ? "RA 太郎" : "CA Hương"}</span></h1><p>今日の目標と、自分が動かす案件を確認します。</p></div><button className="button secondary" onClick={onOpenActions}>タスク一覧<ArrowUpRight size={16} /></button></div>
    <section className="kpi-grid" aria-label="KPI">{kpis.map(kpi => { const rate = Math.min(100, Math.round(kpi.value / Math.max(1, kpi.target) * 100)); return <article className="kpi-card desk-kpi" key={kpi.key}><div className="kpi-top"><span>{kpi.label}</span><Badge tone={rate >= 100 ? "success" : rate >= 60 ? "info" : "warning"}>{rate >= 100 ? "達成" : rate >= 60 ? "順調" : "先行"}</Badge></div><div className="kpi-value">{kpi.value}<small>/ {kpi.target}</small></div><div className={`goal-track tone-${kpi.tone}`}><i style={{ width: `${rate}%` }} /></div><p>{kpi.note}</p></article>; })}</section>
    <div className="desk-columns"><ActionList title="自分ボール — 今日動かすもの" subtitle="優先度と期限をもとに並び替え" items={data?.my_actions ?? []} onOpen={onOpenActions} /><ActionList title="相手待ち — 期限が来たらAIが提案" subtitle="企業・候補者からの返答を監視" items={data?.waiting_actions ?? []} waiting onOpen={onOpenActions} /></div>
    <section className="surface chase-queue"><div className="section-head"><div><h2><Clock3 size={16} />書類選考の催促キュー</h2><p>企業ごとの平均返答日数を超えた案件を優先表示</p></div></div><div className="queue-summary"><strong>{(data?.actions ?? []).filter(item => item.queue_type.includes("chase") || item.queue_type.includes("reply")).length}件</strong><span>AIが催促文面と連絡チャネルを提案します</span><button className="button secondary" onClick={onOpenActions}>キューを確認</button></div></section>
  </div>;
}
