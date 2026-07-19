import { CalendarClock, ChevronRight, MapPin, SlidersHorizontal, Sparkles, UserRoundSearch } from "lucide-react";
import { Badge, statusTone } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import type { Candidate } from "../types";

const statusLabels: Record<string, string> = { active: "アクティブ", process: "選考中", dormant: "休眠" };

export function CandidatesView({ candidates, selected, onSelect, status, onStatus, onMatching }: { candidates: Candidate[]; selected: Candidate | null; onSelect: (candidate: Candidate) => void; status: string; onStatus: (status: string) => void; onMatching: () => void }) {
  return (
    <div className="view-stack">
      <div className="page-heading compact-heading">
        <div><span className="eyebrow">DATABASE</span><h1>候補者</h1><p>Porters IDをキーに、条件・接触・選考状況を統合します。</p></div>
        <button className="button secondary"><SlidersHorizontal size={16} />表示項目</button>
      </div>
      <div className="filter-toolbar">
        <div className="segmented compact">
          {["", "active", "process", "dormant"].map(value => <button key={value || "all"} className={status === value ? "selected" : ""} onClick={() => onStatus(value)}>{value ? statusLabels[value] : "すべて"}</button>)}
        </div>
        <span>{candidates.length}名</span>
      </div>
      <div className="master-detail">
        <section className="surface table-surface">
          {candidates.length ? (
            <div className="table-scroll"><table className="data-table"><thead><tr><th>候補者</th><th>職種・経験</th><th>日本語</th><th>担当</th><th>最終接触</th><th>状態</th><th /></tr></thead><tbody>
              {candidates.map(candidate => (
                <tr key={candidate.id} className={selected?.id === candidate.id ? "selected-row" : ""} onClick={() => onSelect(candidate)}>
                  <td><div className="person-cell"><div className="person-avatar">{candidate.name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div><div><strong>{candidate.name}</strong><small>{candidate.porters_id}</small></div></div></td>
                  <td><strong className="cell-title">{candidate.role_title}</strong><small>{candidate.years_experience}年 · {candidate.work_style}</small></td>
                  <td><Badge tone={candidate.jlpt === "N2" ? "info" : "neutral"}>{candidate.jlpt ?? "未登録"}</Badge></td>
                  <td>{candidate.ca_owner}</td>
                  <td>{candidate.last_contact_date ?? "—"}</td>
                  <td><Badge tone={statusTone(candidate.status)}>{statusLabels[candidate.status] ?? candidate.status}</Badge></td>
                  <td><ChevronRight size={16} /></td>
                </tr>
              ))}
            </tbody></table></div>
          ) : <EmptyState title="候補者が見つかりません" body="検索語または状態フィルタを変更してください。" />}
        </section>
        <aside className="inspector">
          {selected ? <>
            <div className="inspector-person"><div className="person-avatar large">{selected.name.split(" ").map(part => part[0]).slice(0, 2).join("")}</div><div><h2>{selected.name}</h2><p>{selected.role_title}</p></div></div>
            <div className="inspector-status"><Badge tone={statusTone(selected.status)}>{statusLabels[selected.status] ?? selected.status}</Badge><span>{selected.ca_owner}</span></div>
            <dl className="detail-list">
              <div><dt>希望給与</dt><dd>{selected.desired_salary_million ? `${selected.desired_salary_million}M VND` : "—"}</dd></div>
              <div><dt>経験</dt><dd>{selected.years_experience}年</dd></div>
              <div><dt>日本語</dt><dd>{selected.jlpt ?? "未登録"}</dd></div>
              <div><dt>通勤許容</dt><dd><MapPin size={14} />{selected.commute_minutes ?? "—"}分</dd></div>
              <div><dt>平均反応</dt><dd><CalendarClock size={14} />{selected.avg_response_days ?? "—"}日</dd></div>
            </dl>
            <div className="skill-cloud">{selected.skills.map(skill => <span key={skill}>{skill}</span>)}</div>
            <div className="note-box"><strong>CAメモ</strong><p>{selected.notes || "メモはありません。"}</p></div>
            <button className="button primary full" onClick={onMatching}><Sparkles size={16} />この候補者の推薦先を探す</button>
          </> : <EmptyState title="候補者を選択" body="一覧から候補者を選ぶと詳細を確認できます。" />}
        </aside>
      </div>
    </div>
  );
}
