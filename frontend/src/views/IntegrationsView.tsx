import { CheckCircle2, CloudCog, Mail, MessageCircle, PlugZap, RefreshCw, Send, Workflow } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Badge, statusTone } from "../components/Badge";
import type { Integration, OutboxEvent, SyncRun } from "../types";

const providerMeta: Record<string, { label: string; description: string; icon: LucideIcon; tone: string }> = {
  porters: { label: "Porters", description: "候補者・求人の正本データを同期", icon: CloudCog, tone: "blue" },
  gmail: { label: "Gmail", description: "企業向け推薦・催促メールを送信", icon: Mail, tone: "red" },
  zalo: { label: "Zalo OA", description: "候補者フォローをHITLで配信", icon: MessageCircle, tone: "blue" },
  asana: { label: "Asana", description: "対応キューを外部タスクへ同期", icon: Workflow, tone: "orange" },
};

export function IntegrationsView({ integrations, syncRuns, outbox, busy, onTest, onSync, onRetry }: { integrations: Integration[]; syncRuns: SyncRun[]; outbox: OutboxEvent[]; busy: string; onTest: (provider: string) => void; onSync: () => void; onRetry: (eventId: string) => void }) {
  return (
    <div className="view-stack">
      <div className="page-heading compact-heading"><div><span className="eyebrow">CONNECTIONS</span><h1>連携・同期</h1><p>認証情報、同期結果、送信キューを同じ画面で監視します。</p></div><button className="button primary" onClick={onSync} disabled={busy === "porters"}><RefreshCw size={16} className={busy === "porters" ? "spin" : ""} />Porters同期</button></div>
      <section className="integration-grid">
        {integrations.map(item => {
          const meta = providerMeta[item.provider];
          const Icon = meta.icon;
          return <article className="integration-card" key={item.provider}>
            <div className="integration-head"><div className={`integration-icon tone-${meta.tone}`}><Icon size={19} /></div><Badge tone={statusTone(item.status)}>{item.configured ? item.status : "要設定"}</Badge></div>
            <h2>{meta.label}</h2><p>{meta.description}</p>
            <div className="capability-list">{item.capabilities.map(capability => <span key={capability}><CheckCircle2 size={12} />{capability}</span>)}</div>
            {item.last_error && <div className="integration-error">{item.last_error}</div>}
            <div className="integration-foot"><span>{item.last_success_at ? `最終成功 ${new Date(item.last_success_at).toLocaleString("ja-JP")}` : "接続履歴なし"}</span><button className="button secondary small" onClick={() => onTest(item.provider)} disabled={busy === item.provider}><PlugZap size={14} />接続確認</button></div>
          </article>;
        })}
      </section>
      <div className="integration-detail-grid">
        <section className="surface">
          <div className="section-head"><div><h2>同期履歴</h2><p>API取得とDB書き込みの実績</p></div><CloudCog size={17} /></div>
          <div className="compact-list">{syncRuns.length ? syncRuns.map(run => <div className="compact-row" key={run.id}><div><strong>{run.provider} / {run.resource}</strong><span>{new Date(run.started_at).toLocaleString("ja-JP")}</span></div><div className="sync-count"><strong>{run.records_written}</strong><span>書込 / {run.records_read} 読込</span></div><Badge tone={statusTone(run.status)}>{run.status}</Badge></div>) : <div className="inline-empty">同期履歴はありません。</div>}</div>
        </section>
        <section className="surface">
          <div className="section-head"><div><h2>送信Outbox</h2><p>外部API障害時も失わない送信キュー</p></div><Send size={17} /></div>
          <div className="compact-list">{outbox.length ? outbox.map(event => <div className="compact-row" key={event.id}><div><strong>{event.provider} · {event.event_type}</strong><span>{event.aggregate_id}</span></div><div className="sync-count"><strong>{event.attempts}</strong><span>試行</span></div><Badge tone={statusTone(event.status)}>{event.status}</Badge>{event.status !== "delivered" && <button className="icon-button" onClick={() => onRetry(event.id)} title="再送"><RefreshCw size={15} /></button>}</div>) : <div className="inline-empty">送信待ちはありません。</div>}</div>
        </section>
      </div>
    </div>
  );
}
