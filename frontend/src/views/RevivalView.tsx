import { History, MessageCircleMore, Sparkles } from "lucide-react";
import { Badge } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import type { Candidate } from "../types";

export function RevivalView({ candidates, onSelect }: { candidates: Candidate[]; onSelect: (candidate: Candidate) => void }) {
  const { t } = useI18n();
  return <div className="view-stack">
    <div className="page-heading compact-heading"><div><span className="eyebrow">RE-ENGAGEMENT</span><h1>{t("revivalTitle")}</h1><p>{t("revivalSub")}</p></div><History size={24} /></div>
    <section className="surface revival-list">
      {candidates.length ? candidates.map(candidate => <article className="revival-row" key={candidate.id}>
        <div className="person-avatar">{candidate.name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div>
        <div><strong>{candidate.name}</strong><span>{candidate.role_title} · {candidate.last_contact_date || "—"}</span></div>
        <p>{candidate.notes}</p><Badge tone="warning">Zalo / Gmail</Badge>
        <button className="button primary small" onClick={() => onSelect(candidate)}><Sparkles size={14} />{t("generateMessage")}<MessageCircleMore size={14} /></button>
      </article>) : <EmptyState title={t("revivalTitle")} body="No dormant candidates." />}
    </section>
  </div>;
}
