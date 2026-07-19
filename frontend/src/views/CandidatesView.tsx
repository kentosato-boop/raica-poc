import { BriefcaseBusiness, ExternalLink, FileText, FileUp, MapPin, SlidersHorizontal, Sparkles } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { Badge, statusTone } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { useI18n } from "../i18n";
import type { Candidate, MatchItem } from "../types";

const statusLabels: Record<string, Record<string, string>> = {
  ja: { active: "活動中", process: "選考中", dormant: "休眠" },
  vi: { active: "Đang hoạt động", process: "Đang tuyển chọn", dormant: "Tạm nghỉ" },
  en: { active: "Active", process: "In process", dormant: "Dormant" },
};
const workLabels: Record<string, string> = { remote: "リモート", onsite: "常駐", hybrid: "ハイブリッド", flexible: "相談可" };
const specializationLabels: Record<string, string> = {
  data_engineering: "AI・データエンジニア", backend: "バックエンドエンジニア", frontend: "フロントエンドエンジニア",
  line_management: "製造ライン管理", production_planning: "生産計画・在庫管理", qc: "品質管理", cnc: "CNC加工",
  interpretation: "通訳・総務", accounting: "会計・経理", assembly: "製造・組立", warehouse: "倉庫管理",
};
const consentLabels: Record<string, string> = { confirmed: "同意確認済み", reconfirm_required: "再同意が必要" };
const specialty = (candidate: Candidate) => specializationLabels[candidate.specialization || ""] || candidate.role_title;

export function CandidatesView({ role, search, candidates, selected, onSelect, status, onStatus, matches, onLoadMatches, onUpload, onDownload, uploading }: {
  role: "ra" | "ca"; search: string; candidates: Candidate[]; selected: Candidate | null; onSelect: (candidate: Candidate) => void;
  status: string; onStatus: (status: string) => void; matches: MatchItem[]; onLoadMatches: () => void;
  onUpload: (file: File) => void; onDownload: (candidate: Candidate) => void; uploading: boolean;
}) {
  const { t, locale } = useI18n();
  const fileInput = useRef<HTMLInputElement>(null);
  const [specialization, setSpecialization] = useState("");
  const [location, setLocation] = useState("");
  const [parallel, setParallel] = useState("");
  const specializationOptions = useMemo(() => Array.from(new Set(candidates.map(candidate => candidate.specialization).filter(Boolean))).sort() as string[], [candidates]);
  const locationOptions = useMemo(() => Array.from(new Set(candidates.map(candidate => candidate.current_location).filter(Boolean))).sort() as string[], [candidates]);
  const filteredCandidates = useMemo(() => candidates.filter(candidate => {
    const hasSpecialization = !specialization || candidate.specialization === specialization;
    const hasLocation = !location || candidate.current_location === location;
    const parallelTotal = candidate.internal_parallel_count + candidate.external_parallel_count;
    const hasParallel = parallel === "has" ? parallelTotal > 0 : parallel === "none" ? parallelTotal === 0 : true;
    return hasSpecialization && hasLocation && hasParallel;
  }), [candidates, parallel, specialization, location]);
  return <div className="view-stack">
    <div className="page-heading compact-heading">
      <div><span className="eyebrow">TALENT DATABASE</span><h1>{t("candidates")}</h1><p>{search ? `「${search}」を候補者情報・スキルシートから検索` : "候補者情報・並行状況・スキルシートを一覧で確認"}</p></div>
      <button className="button secondary" disabled={!selected || uploading} onClick={() => fileInput.current?.click()}><FileUp size={16} />{uploading ? "取込中" : "スキルシート登録"}</button>
      <input ref={fileInput} type="file" accept=".pdf,.docx,.txt,.md,.csv" hidden onChange={event => { const file = event.target.files?.[0]; if (file) onUpload(file); event.target.value = ""; }} />
    </div>
    <div className="filter-toolbar database-toolbar">
      <div className="segmented compact">{["", "active", "process", "dormant"].map(value => <button key={value || "all"} className={status === value ? "selected" : ""} onClick={() => onStatus(value)}>{value ? statusLabels[locale][value] : t("all")}</button>)}</div>
      <div className="advanced-filters" aria-label="候補者フィルター">
        <label><span><SlidersHorizontal size={13} />専門</span><select value={specialization} onChange={event => setSpecialization(event.target.value)}><option value="">すべて</option>{specializationOptions.map(value => <option key={value} value={value}>{specializationLabels[value] || value}</option>)}</select></label>
        <label><span><MapPin size={13} />勤務地</span><select value={location} onChange={event => setLocation(event.target.value)}><option value="">すべて</option>{locationOptions.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
        <label><span>並行</span><select value={parallel} onChange={event => setParallel(event.target.value)}><option value="">すべて</option><option value="has">あり</option><option value="none">なし</option></select></label>
      </div>
      <span>{filteredCandidates.length} / {candidates.length}名</span>
    </div>
    <section className="surface table-surface database-surface">
      {filteredCandidates.length ? <div className="table-scroll"><table className="data-table database-table"><thead><tr>
        <th>候補者</th><th>状態</th><th>専門領域</th><th>経験・年齢</th><th>希望年収</th><th>勤務地</th><th>並行</th><th>流入</th><th>スキルシート</th>
      </tr></thead><tbody>{filteredCandidates.map(candidate => {
        const parallelTotal = candidate.internal_parallel_count + candidate.external_parallel_count;
        const workStyles = (candidate.work_style_options?.length ? candidate.work_style_options : [candidate.work_style]).map(mode => workLabels[mode] || mode).join("・");
        return <tr key={candidate.id} className={selected?.id === candidate.id ? "selected-row" : ""} onClick={() => onSelect(candidate)}>
        <td><div className="person-cell"><div className="person-avatar">{candidate.name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div><div><strong>{candidate.name}</strong><small>{candidate.role_title}</small>{candidate.search_match && <span className="search-match">{candidate.search_match}一致</span>}</div></div></td>
        <td><Badge tone={statusTone(candidate.status)}>{statusLabels[locale][candidate.status] || candidate.status}</Badge></td>
        <td><span className="cell-primary">{specialty(candidate)}</span><small className="cell-subline">専門 {candidate.specialization_years}年</small></td>
        <td><span className="cell-primary">{candidate.years_experience}年 · {candidate.age ?? "—"}歳</span><small className="cell-subline">現年収 {candidate.current_salary_million ?? "—"}M</small></td>
        <td><span className="cell-primary">{candidate.desired_salary_million ?? "—"}M VND</span><small className="cell-subline">{workStyles}</small></td>
        <td><span className="cell-primary">{candidate.current_location || "—"}</span><small className="cell-subline">稼働 {candidate.available_from || "要確認"}</small></td>
        <td>{parallelTotal ? <span className="parallel-pill" title={`社内 ${candidate.internal_parallel_count} · 社外 ${candidate.external_parallel_count}`}>計{parallelTotal}</span> : <span className="parallel-pill zero">なし</span>}</td>
        <td>{candidate.inflow_days != null ? <span className={`inflow-cell${candidate.inflow_days <= 3 ? " fresh" : ""}`}><strong>{candidate.inflow_days}</strong>日目</span> : <span className="muted-cell">—</span>}</td>
        <td>{candidate.skill_sheet_filename ? <button className="file-link" onClick={event => { event.stopPropagation(); onDownload(candidate); }}><FileText size={14} /><span>{candidate.skill_sheet_filename}</span><ExternalLink size={12} /></button> : <span className="muted-cell">未登録</span>}</td>
      </tr>; })}</tbody></table></div> : <EmptyState title="該当する候補者はいません" body="検索条件を変更してください。" />}
    </section>
    {selected && <section className="surface record-detail" aria-live="polite">
      <div className="record-detail-head"><div className="inspector-person"><div className="person-avatar large">{selected.name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div><div><h2>{selected.name}</h2><p>{selected.role_title} · {selected.porters_id}</p></div></div><Badge tone={statusTone(selected.status)}>{statusLabels[locale][selected.status] || selected.status}</Badge></div>
      <div className="record-detail-grid">
        <div><h3>基本・希望条件</h3><dl className="detail-list"><div><dt>職種・専門領域</dt><dd>{specialty(selected)} / {selected.specialization_years}年</dd></div><div><dt>年齢・経験</dt><dd>{selected.age ?? "—"}歳 / 通算{selected.years_experience}年</dd></div><div><dt>現年収 → 希望</dt><dd>{selected.current_salary_million ?? "—"}M → {selected.desired_salary_million ?? "—"}M VND</dd></div><div><dt>勤務形態</dt><dd>{(selected.work_style_options || []).map(mode => workLabels[mode] || mode).join("・") || workLabels[selected.work_style]}</dd></div><div><dt>通勤許容</dt><dd><MapPin size={14} />{selected.commute_minutes ?? "—"}分</dd></div></dl></div>
        <div><h3>並行状況</h3><div className="parallel-summary"><div><span>社内並行</span><strong>{selected.internal_parallel_count}</strong></div><div><span>社外並行</span><strong>{selected.external_parallel_count}</strong></div></div><div className="process-list">{selected.current_processes.length ? selected.current_processes.map((process, index) => <div key={`${process.label}-${index}`}><BriefcaseBusiness size={14} /><span><strong>{process.label}</strong><small>{process.scope === "internal" ? "社内" : "社外"} · {process.stage}</small></span></div>) : <span className="muted-cell">並行選考なし</span>}</div></div>
        <div><h3>稼働・登録情報</h3><dl className="detail-list"><div><dt>稼働開始</dt><dd>{selected.available_from || "要確認"}</dd></div><div><dt>現在地</dt><dd>{selected.current_location || "—"}</dd></div><div><dt>希望勤務地</dt><dd>{(selected.desired_locations || []).join("・") || "—"}</dd></div><div><dt>就労資格</dt><dd>{selected.work_authorization || "—"}</dd></div><div><dt>流入元</dt><dd>{selected.source_channel || "—"}</dd></div><div><dt>希望連絡</dt><dd>{selected.preferred_contact_channel || "—"}</dd></div><div><dt>個人情報</dt><dd>{consentLabels[selected.consent_status] || selected.consent_status}</dd></div></dl></div>
        <div><h3>スキル・メモ</h3><div className="skill-cloud">{selected.skills.map(skill => <span key={skill}>{skill}</span>)}</div><div className="note-box"><p>{selected.notes || "—"}</p></div></div>
      </div>
      {role === "ca" && <div className="candidate-match-area"><button className="button primary" onClick={onLoadMatches}><Sparkles size={16} />この候補者に合う案件を探す</button>{matches.length > 0 && <div className="inline-match-list">{matches.slice(0, 4).map(match => <article key={match.id}><div><strong>{match.job_title}</strong><span>{match.company_name}</span></div><b>{match.score}</b><small>{match.evidence_quote}</small></article>)}</div>}</div>}
    </section>}
  </div>;
}
