import { ArrowUpRight, BriefcaseBusiness, CircleAlert, Clock3, Radio, UsersRound } from "lucide-react";
import { Badge, statusTone } from "../components/Badge";
import type { DashboardData } from "../types";

const stageLabels: Record<string, string> = {
  intent_check: "意向確認",
  recommended: "推薦",
  screening: "書類選考",
  first_interview: "一次面接",
  final_interview: "最終面接",
  offer: "オファー",
  closed_won: "成約",
};

export function DashboardView({ data, role, onOpenActions }: { data: DashboardData | null; role: "ra" | "ca"; onOpenActions: () => void }) {
  const counts = data?.counts;
  const kpis = [
    { label: "候補者DB", value: counts?.candidates ?? 0, detail: `アクティブ ${counts?.active_candidates ?? 0}`, icon: UsersRound, tone: "blue" },
    { label: "進行中求人", value: counts?.open_jobs ?? 0, detail: "Porters同期対象", icon: BriefcaseBusiness, tone: "green" },
    { label: "対応待ち", value: counts?.open_actions ?? 0, detail: `${role.toUpperCase()}の優先キュー`, icon: CircleAlert, tone: "orange" },
    { label: "送信待ち", value: counts?.pending_outbox ?? 0, detail: "Outbox再送対象", icon: Radio, tone: "violet" },
  ];
  const maxStage = Math.max(1, ...Object.values(data?.pipeline ?? {}));

  return (
    <div className="view-stack">
      <div className="page-heading">
        <div><span className="eyebrow">TODAY</span><h1>{role === "ra" ? "RAオペレーション" : "CAオペレーション"}</h1><p>止まっている案件と次のアクションを、ひとつの画面で確認します。</p></div>
        <button className="button secondary" onClick={onOpenActions}>対応キューを開く<ArrowUpRight size={16} /></button>
      </div>

      <section className="kpi-grid" aria-label="主要指標">
        {kpis.map(({ label, value, detail, icon: Icon, tone }) => (
          <article className="kpi-card" key={label}>
            <div className={`kpi-icon tone-${tone}`}><Icon size={18} /></div>
            <div className="kpi-label">{label}</div>
            <div className="kpi-value">{value.toLocaleString()}</div>
            <div className="kpi-detail">{detail}</div>
          </article>
        ))}
      </section>

      <div className="dashboard-grid">
        <section className="surface action-surface">
          <div className="section-head"><div><h2>今日動かすもの</h2><p>期限と学習値から優先順位を決定</p></div><Badge tone="danger">{data?.actions.length ?? 0}</Badge></div>
          <div className="action-list">
            {(data?.actions ?? []).filter(item => item.owner_role === role).map(item => (
              <button className="action-row" key={item.id} onClick={onOpenActions}>
                <span className={`severity-dot severity-${item.severity}`} />
                <span className="action-copy"><strong>{item.target_label}</strong><small>{item.reason}</small></span>
                <span className="action-meta"><Badge tone={statusTone(item.severity)}>{item.severity}</Badge><small>{item.due_date}</small></span>
              </button>
            ))}
          </div>
        </section>

        <section className="surface pipeline-surface">
          <div className="section-head"><div><h2>選考パイプライン</h2><p>DBに保存された現在のステージ</p></div><Badge tone="info">{counts?.applications ?? 0}件</Badge></div>
          <div className="pipeline-list">
            {Object.entries(data?.pipeline ?? {}).map(([stage, count]) => (
              <div className="pipeline-row" key={stage}>
                <span>{stageLabels[stage] ?? stage}</span>
                <div className="pipeline-track"><i style={{ width: `${Math.max(8, count / maxStage * 100)}%` }} /></div>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="activity-band">
        <div className="section-head"><div><h2>最新の操作履歴</h2><p>推薦・同期・送信の監査ログ</p></div><Clock3 size={17} /></div>
        <div className="activity-grid">
          {(data?.activity ?? []).slice(0, 4).map(item => (
            <div className="activity-item" key={item.id}>
              <div className="activity-avatar">{item.actor.slice(0, 2).toUpperCase()}</div>
              <div><strong>{item.action}</strong><span>{item.actor} · {item.entity_type} / {item.entity_id}</span></div>
              <time>{new Date(item.created_at).toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" })}</time>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
