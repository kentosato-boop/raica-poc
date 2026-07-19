import { CheckCircle2, Clock3, MoreHorizontal, RotateCcw } from "lucide-react";
import { Badge, statusTone } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import type { ActionItem } from "../types";

const queueLabels: Record<string, string> = { client_chase: "企業催促", client_call: "企業電話", candidate_follow: "候補者フォロー" };

export function ActionsView({ actions, role, onRole, status, onStatus, onUpdate }: { actions: ActionItem[]; role: "ra" | "ca"; onRole: (role: "ra" | "ca") => void; status: string; onStatus: (status: string) => void; onUpdate: (id: string, status: "done" | "open" | "snoozed") => void }) {
  return (
    <div className="view-stack">
      <div className="page-heading compact-heading"><div><span className="eyebrow">ACTION QUEUE</span><h1>対応キュー</h1><p>AI提案は人が確認し、完了状態をDBと外部タスクへ反映します。</p></div><div className="segmented"><button className={role === "ra" ? "selected" : ""} onClick={() => onRole("ra")}>RA</button><button className={role === "ca" ? "selected" : ""} onClick={() => onRole("ca")}>CA</button></div></div>
      <div className="filter-toolbar"><div className="segmented compact">{[["open", "未完了"], ["snoozed", "保留"], ["done", "完了"], ["", "すべて"]].map(([value, label]) => <button key={label} className={status === value ? "selected" : ""} onClick={() => onStatus(value)}>{label}</button>)}</div><span>{actions.length}件</span></div>
      <section className="surface action-table-surface">
        {actions.length ? <div className="action-table-list">{actions.map(item => <article className="queue-row" key={item.id}>
          <div className={`queue-icon severity-${item.severity}`}><Clock3 size={17} /></div>
          <div className="queue-main"><div><Badge tone="neutral">{queueLabels[item.queue_type] ?? item.queue_type}</Badge><Badge tone={statusTone(item.severity)}>{item.severity}</Badge></div><h2>{item.target_label}</h2><p>{item.reason}</p></div>
          <div className="queue-date"><span>期限</span><strong>{item.due_date}</strong></div>
          <div className="queue-actions">
            {item.status !== "done" ? <><button className="icon-button" onClick={() => onUpdate(item.id, "snoozed")} title="保留"><MoreHorizontal size={17} /></button><button className="button primary small" onClick={() => onUpdate(item.id, "done")}><CheckCircle2 size={15} />完了</button></> : <button className="button secondary small" onClick={() => onUpdate(item.id, "open")}><RotateCcw size={15} />戻す</button>}
          </div>
        </article>)}</div> : <EmptyState title="該当する対応はありません" body="ロールまたは状態フィルタを変更してください。" />}
      </section>
    </div>
  );
}
