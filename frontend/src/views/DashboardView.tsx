import { ArrowUpRight, BadgeCheck, BriefcaseBusiness, CalendarCheck2, UserCheck } from "lucide-react";
import { Badge, statusTone } from "../components/Badge";
import { useI18n } from "../i18n";
import type { DashboardData } from "../types";

const stageLabels: Record<string, Record<string, string>> = {
  ja: { intent_check: "意向確認", recommended: "推薦", screening: "書類選考", first_interview: "一次面接", final_interview: "最終面接", offer: "オファー", closed_won: "成約" },
  vi: { intent_check: "Xác nhận ý định", recommended: "Đã đề xuất", screening: "Sàng lọc hồ sơ", first_interview: "PV vòng 1", final_interview: "PV cuối", offer: "Offer", closed_won: "Chốt tuyển" },
  en: { intent_check: "Intent check", recommended: "Recommended", screening: "Screening", first_interview: "First interview", final_interview: "Final interview", offer: "Offer", closed_won: "Placement" },
};

export function DashboardView({ data, role, onOpenActions }: { data: DashboardData | null; role: "ra" | "ca"; onOpenActions: () => void }) {
  const { t, locale } = useI18n();
  const counts = data?.counts;
  const kpis = [
    { label: t("recommendations"), value: counts?.recommendations ?? 0, detail: t("thisMonth"), icon: UserCheck, tone: "blue" },
    { label: t("interviews"), value: counts?.interviews ?? 0, detail: t("thisMonth"), icon: CalendarCheck2, tone: "green" },
    { label: t("wins"), value: counts?.closed_won ?? 0, detail: t("thisMonth"), icon: BadgeCheck, tone: "red" },
    { label: t("newJobs"), value: counts?.new_jobs ?? 0, detail: t("last7Days"), icon: BriefcaseBusiness, tone: "orange" },
  ];
  const maxStage = Math.max(1, ...Object.values(data?.pipeline ?? {}));

  return (
    <div className="view-stack">
      <div className="page-heading dashboard-heading">
        <div><span className="eyebrow">TODAY</span><h1>{role === "ra" ? t("dashboardRa") : t("dashboardCa")}</h1></div>
        <button className="button secondary" onClick={onOpenActions}>{t("myBall")}<ArrowUpRight size={16} /></button>
      </div>

      <section className="kpi-grid" aria-label="KPI">
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
          <div className="section-head"><div><h2>{t("mine")}</h2><p>{t("openItems")} · {data?.actions.length ?? 0}</p></div><Badge tone="danger">{data?.actions.length ?? 0}</Badge></div>
          <div className="action-list">
            {(data?.actions ?? []).map(item => (
              <button className="action-row" key={item.id} onClick={onOpenActions}>
                <span className={`severity-dot severity-${item.severity}`} />
                <span className="action-copy"><strong>{item.target_label}</strong><small>{item.reason}</small></span>
                <span className="action-meta"><Badge tone={statusTone(item.severity)}>{item.severity}</Badge><small>{item.due_date}</small></span>
              </button>
            ))}
          </div>
        </section>

        <section className="surface pipeline-surface">
          <div className="section-head"><div><h2>{t("pipeline")}</h2><p>{data?.pipeline_scope || t("pipelineSub")}</p></div><Badge tone="info">{Object.values(data?.pipeline ?? {}).reduce((sum, value) => sum + value, 0)}</Badge></div>
          {data?.companies?.length ? <div className="company-scope">{data.companies.map(company => <span key={company}>{company}</span>)}</div> : null}
          <div className="pipeline-list">
            {Object.entries(data?.pipeline ?? {}).map(([stage, count]) => (
              <div className="pipeline-row" key={stage}>
                <span>{stageLabels[locale][stage] ?? stage}</span>
                <div className="pipeline-track"><i style={{ width: `${Math.max(8, count / maxStage * 100)}%` }} /></div>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="activity-band">
        <div className="section-head"><div><h2>{t("activity")}</h2></div></div>
        <div className="activity-grid">{(data?.activity ?? []).slice(0, 4).map(item => <article className="activity-item" key={item.id}><div className="activity-avatar">{item.actor.slice(0, 2)}</div><div><strong>{item.action}</strong><span>{item.entity_type} · {item.entity_id}</span></div><time>{new Date(item.created_at).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" })}</time></article>)}</div>
      </section>
    </div>
  );
}
