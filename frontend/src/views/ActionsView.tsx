import { CheckCircle2, Clock3, PauseCircle, RotateCcw } from "lucide-react";
import { Badge, statusTone } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import type { ActionItem } from "../types";

const queueLabels: Record<string, string> = { client_chase: "企業催促", client_call: "企業電話", candidate_follow: "候補者フォロー" };

export function ActionsView({ actions, status, onStatus, onUpdate }: { actions: ActionItem[]; status: string; onStatus: (status: string) => void; onUpdate: (id: string, status: "done" | "open" | "snoozed") => void }) {
  const { t } = useI18n();
  return (
    <div className="view-stack">
      <div className="page-heading compact-heading"><div><span className="eyebrow">MY ACTIONS</span><h1>{t("myBall")}</h1></div></div>
      <div className="filter-toolbar"><div className="segmented compact">{[["open", t("openItems")], ["snoozed", t("hold")], ["done", t("complete")], ["", t("all")]].map(([value, label]) => <button key={label} className={status === value ? "selected" : ""} onClick={() => onStatus(value)}>{label}</button>)}</div><span>{actions.length}</span></div>
      <section className="surface action-table-surface">
        {actions.length ? <div className="action-table-list">{actions.map(item => <article className="queue-row" key={item.id}>
          <div className={`queue-icon severity-${item.severity}`}><Clock3 size={17} /></div>
          <div className="queue-main"><div><Badge tone="neutral">{queueLabels[item.queue_type] ?? item.queue_type}</Badge><Badge tone={statusTone(item.severity)}>{item.severity}</Badge></div><h2>{item.target_label}</h2><p>{item.reason}</p></div>
          <div className="queue-date"><span>{t("due")}</span><strong>{item.due_date}</strong></div>
          <div className="queue-actions">
            {item.status !== "done" ? <><button className="button secondary small" onClick={() => onUpdate(item.id, "snoozed")}><PauseCircle size={15} />{t("hold")}</button><button className="button primary small" onClick={() => onUpdate(item.id, "done")}><CheckCircle2 size={15} />{t("complete")}</button></> : <button className="button secondary small" onClick={() => onUpdate(item.id, "open")}><RotateCcw size={15} />{t("restore")}</button>}
          </div>
        </article>)}</div> : <EmptyState title={t("actionsEmpty")} body="" />}
      </section>
    </div>
  );
}
