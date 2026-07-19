import { BriefcaseBusiness, Building2, CalendarClock, Mail, MessageCircleMore, Phone, Radar, Sparkles, UserRound } from "lucide-react";
import { useState } from "react";
import { Badge } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import type { RevivalData, RevivalItem } from "../types";

const statusTone = (item: RevivalItem) => item.status === "hot" || item.priority_score >= 80 ? "danger" : item.priority_score >= 65 ? "warning" : "info";

export function RevivalView({ role, data, onOpen }: { role: "ra" | "ca"; data: RevivalData | null; onOpen: (item: RevivalItem) => void }) {
  const [proposalId, setProposalId] = useState("");
  const isRa = role === "ra";
  const items = data?.role === role ? data.items : [];
  const urgent = items.filter(item => item.priority_score >= 80).length;
  const averageDays = items.length ? Math.round(items.reduce((sum, item) => sum + item.dormant_days, 0) / items.length) : 0;

  return <div className="view-stack revival-view">
    <div className="page-heading compact-heading">
      <div><span className="eyebrow">{isRa ? "JOB REVIVAL / RA" : "CANDIDATE REVIVAL / CA"}</span><h1>{isRa ? "企業求人の掘り起こし" : "候補者への求人掘り起こし"}</h1><p>{isRa ? "休眠企業の採用再開シグナルから、過去求人を再起動します。" : "休眠候補者の希望条件に、現在募集中の案件を当てて再接触します。"}</p></div>
      <div className={`revival-role-mark ${isRa ? "ra" : "ca"}`}>{isRa ? <Building2 size={22} /> : <UserRound size={22} />}<span>{isRa ? "企業起点" : "候補者起点"}</span></div>
    </div>

    <section className="revival-kpis" aria-label="掘り起こし状況">
      <article><span>{isRa ? "対象企業" : "対象候補者"}</span><strong>{items.length}</strong><small>{isRa ? "採用停止・監視中" : "休眠ステータス"}</small></article>
      <article><span>優先対応</span><strong>{urgent}</strong><small>AI優先度80以上</small></article>
      <article><span>平均休眠期間</span><strong>{averageDays}<small>日</small></strong><small>最終接触から算出</small></article>
    </section>

    <section className="surface revival-database">
      <div className="section-head"><div><h2>{isRa ? <><Radar size={16} />求人再開シグナル</> : <><BriefcaseBusiness size={16} />現在の最適案件</>}</h2><p>{isRa ? "企業活動と過去取引をAIが監視" : "現在の求人DBと再マッチング"}</p></div><Badge tone="info">{items.length}件</Badge></div>
      {items.length ? <div className="revival-table-scroll"><div className={`revival-table ${isRa ? "company" : "candidate"}`}>
        <div className="revival-table-head"><span>{isRa ? "企業" : "候補者"}</span><span>{isRa ? "過去求人" : "現在の最適案件"}</span><span>最終接触</span><span>{isRa ? "採用再開シグナル" : "推薦根拠"}</span><span>優先度</span><span>アクション</span></div>
        {items.map(item => <div className="revival-record" key={item.id}>
          <div className="revival-identity"><div className="person-avatar">{item.name.slice(0, 2)}</div><span><strong>{item.name}</strong><small>{item.secondary_label} · {item.owner}</small></span></div>
          <div className="revival-target"><strong>{isRa ? item.primary_label : `${item.company_name || "案件再検索"} / ${item.job_title || "未選定"}`}</strong><small>{isRa ? item.reason : item.primary_label}</small></div>
          <div className="revival-contact"><CalendarClock size={14} /><span><strong>{item.last_contact_date || "未登録"}</strong><small>{item.dormant_days}日前</small></span></div>
          <p>{isRa ? item.signal : item.recommendation}</p>
          <div className="revival-score"><strong>{item.priority_score}</strong><Badge tone={statusTone(item)}>{item.priority_score >= 80 ? "優先" : "監視"}</Badge></div>
          <div className="revival-actions"><button className="button primary small" onClick={() => setProposalId(current => current === item.id ? "" : item.id)}><Sparkles size={14} />AI提案</button><button className="icon-button" title={isRa ? "過去求人を確認" : "候補者を確認"} onClick={() => onOpen(item)}>{isRa ? <BriefcaseBusiness size={16} /> : <UserRound size={16} />}</button></div>
          {proposalId === item.id && <div className="revival-proposal"><div><Sparkles size={15} /><span><strong>{isRa ? "求人再開のアプローチ案" : "候補者への再接触案"}</strong><p>{isRa ? `${item.name}の${item.primary_label}について、検知した「${item.signal}」を切り口に採用再開時期と要件変更を確認します。` : `${item.name}様へ「${item.company_name} / ${item.job_title}」を提案します。${item.recommendation}`}</p></span></div><div className="proposal-channels">{isRa ? <><Mail size={14} /><Phone size={14} /></> : <><MessageCircleMore size={14} /><Mail size={14} /></>}<span>{item.channel}</span></div></div>}
        </div>)}
      </div></div> : <EmptyState title={isRa ? "掘り起こし対象の企業はありません" : "掘り起こし対象の候補者はいません"} body="同期データと休眠条件を確認してください。" />}
    </section>
  </div>;
}
