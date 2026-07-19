import { BriefcaseBusiness, CalendarClock, ChevronRight, FileUp, MapPin, Sparkles } from "lucide-react";
import { useRef } from "react";
import { Badge, statusTone } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import type { Candidate } from "../types";

const statusLabels: Record<string, Record<string, string>> = {
  ja: { active: "活動中", process: "選考中", dormant: "休眠" },
  vi: { active: "Đang hoạt động", process: "Đang tuyển chọn", dormant: "Ngủ" },
  en: { active: "Active", process: "In process", dormant: "Dormant" },
};

export function CandidatesView({ candidates, selected, onSelect, status, onStatus, onMatching, onUpload, uploading }: { candidates: Candidate[]; selected: Candidate | null; onSelect: (candidate: Candidate) => void; status: string; onStatus: (status: string) => void; onMatching: () => void; onUpload: (file: File) => void; uploading: boolean }) {
  const { t, locale } = useI18n();
  const fileInput = useRef<HTMLInputElement>(null);
  return (
    <div className="view-stack">
      <div className="page-heading compact-heading">
        <div><span className="eyebrow">{t("database")}</span><h1>{t("candidates")}</h1></div>
        <button className="button secondary" disabled={!selected || uploading} onClick={() => fileInput.current?.click()}><FileUp size={16} />{uploading ? "..." : t("upload")}</button>
        <input ref={fileInput} type="file" accept=".pdf,.docx,.txt,.md,.csv" hidden onChange={event => { const file = event.target.files?.[0]; if (file) onUpload(file); event.target.value = ""; }} />
      </div>
      <div className="filter-toolbar">
        <div className="segmented compact">
          {["", "active", "process", "dormant"].map(value => <button key={value || "all"} className={status === value ? "selected" : ""} onClick={() => onStatus(value)}>{value ? statusLabels[locale][value] : t("all")}</button>)}
        </div>
        <span>{candidates.length}</span>
      </div>
      <div className="master-detail candidate-layout">
        <section className="surface table-surface">
          {candidates.length ? (
            <div className="table-scroll"><table className="data-table"><thead><tr><th>{t("candidates")}</th><th>{t("specialty")}</th><th>{t("internalParallel")} / {t("externalParallel")}</th><th>{t("skillSheet")}</th><th /></tr></thead><tbody>
              {candidates.map(candidate => (
                <tr key={candidate.id} className={selected?.id === candidate.id ? "selected-row" : ""} onClick={() => onSelect(candidate)}>
                  <td><div className="person-cell"><div className="person-avatar">{candidate.name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div><div><strong>{candidate.name}</strong><small>{candidate.role_title} · {candidate.years_experience}年</small></div></div></td>
                  <td><strong className="cell-title">{candidate.specialization || candidate.role_title}</strong><small>{candidate.specialization_years}年 · {candidate.remote_preference}</small></td>
                  <td><div className="parallel-counts"><Badge tone="info">{candidate.internal_parallel_count}</Badge><Badge tone="warning">{candidate.external_parallel_count}</Badge></div></td>
                  <td>{candidate.skill_sheet_filename ? <Badge tone="success">{candidate.skill_sheet_filename}</Badge> : <span className="muted-cell">—</span>}</td>
                  <td><button className="button secondary small detail-button" onClick={event => { event.stopPropagation(); onSelect(candidate); }}>{t("details")}<ChevronRight size={14} /></button></td>
                </tr>
              ))}
            </tbody></table></div>
          ) : <EmptyState title="No results" body="Search or filter conditions can be changed." />}
        </section>
        <aside className="inspector candidate-inspector">
          {selected ? <>
            <div className="inspector-person"><div className="person-avatar large">{selected.name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div><div><h2>{selected.name}</h2><p>{selected.role_title} · {selected.porters_id}</p></div></div>
            <div className="inspector-status"><Badge tone={statusTone(selected.status)}>{statusLabels[locale][selected.status] ?? selected.status}</Badge><span>{selected.ca_owner}</span></div>
            <dl className="detail-list">
              <div><dt>{t("specialty")}</dt><dd>{selected.specialization || "—"}</dd></div>
              <div><dt>{t("specialtyYears")}</dt><dd>{selected.specialization_years}年</dd></div>
              <div><dt>{t("recentTenure")}</dt><dd>{selected.recent_tenure_years}年</dd></div>
              <div><dt>{t("remote")}</dt><dd>{selected.remote_preference}</dd></div>
              <div><dt>年齢 / 日本語</dt><dd>{selected.age ?? "—"} / {selected.jlpt ?? "—"}</dd></div>
              <div><dt>希望給与</dt><dd>{selected.desired_salary_million ? `${selected.desired_salary_million}M VND` : "—"}</dd></div>
              <div><dt>通勤許容</dt><dd><MapPin size={14} />{selected.commute_minutes ?? "—"}分</dd></div>
              <div><dt>平均反応</dt><dd><CalendarClock size={14} />{selected.avg_response_days ?? "—"}日</dd></div>
            </dl>
            <div className="parallel-summary"><div><span>{t("internalParallel")}</span><strong>{selected.internal_parallel_count}</strong></div><div><span>{t("externalParallel")}</span><strong>{selected.external_parallel_count}</strong></div></div>
            <div className="process-list">{selected.current_processes.length ? selected.current_processes.map((process, index) => <div key={`${process.label}-${index}`}><BriefcaseBusiness size={14} /><span><strong>{process.label}</strong><small>{process.scope === "internal" ? t("internalParallel") : t("externalParallel")} · {process.stage}</small></span></div>) : <span className="muted-cell">並行選考なし</span>}</div>
            <div className="skill-cloud">{selected.skills.map(skill => <span key={skill}>{skill}</span>)}</div>
            <div className="skill-sheet-state"><FileUp size={15} /><span><strong>{selected.skill_sheet_filename || t("noAttachment")}</strong><small>{selected.skill_sheet_uploaded_at ? new Date(selected.skill_sheet_uploaded_at).toLocaleDateString(locale) : ""}</small></span></div>
            <div className="note-box"><strong>{t("caMemo")}</strong><p>{selected.notes || "—"}</p></div>
            <button className="button primary full" onClick={onMatching}><Sparkles size={16} />{t("findMatches")}</button>
          </> : <EmptyState title={t("details")} body="Select a candidate." />}
        </aside>
      </div>
    </div>
  );
}
