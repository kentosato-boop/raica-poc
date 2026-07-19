import { Activity, BriefcaseBusiness, Database, GitPullRequestArrow, LayoutDashboard, PlugZap, Sparkles, UsersRound, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ViewKey } from "../types";

const items: Array<{ key: ViewKey; label: string; icon: LucideIcon }> = [
  { key: "dashboard", label: "ダッシュボード", icon: LayoutDashboard },
  { key: "candidates", label: "候補者", icon: UsersRound },
  { key: "jobs", label: "求人", icon: BriefcaseBusiness },
  { key: "matching", label: "AIマッチング", icon: Sparkles },
  { key: "actions", label: "対応キュー", icon: GitPullRequestArrow },
  { key: "integrations", label: "連携・同期", icon: PlugZap },
];

export function Sidebar({ view, onChange, open, onClose, openActions }: { view: ViewKey; onChange: (view: ViewKey) => void; open: boolean; onClose: () => void; openActions: number }) {
  return (
    <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
      <div className="brand-row">
        <div className="app-icon" aria-hidden="true"><Activity size={19} strokeWidth={2.4} /></div>
        <div><strong>RAiCA</strong><span>Recruitment Intelligence</span></div>
        <button className="icon-button sidebar-close" onClick={onClose} title="メニューを閉じる"><X size={18} /></button>
      </div>
      <div className="sidebar-section-label">ワークスペース</div>
      <nav className="sidebar-nav" aria-label="メインナビゲーション">
        {items.map(({ key, label, icon: Icon }) => (
          <button key={key} className={view === key ? "active" : ""} onClick={() => { onChange(key); onClose(); }}>
            <Icon size={17} strokeWidth={1.9} />
            <span>{label}</span>
            {key === "actions" && openActions > 0 && <span className="nav-count">{openActions}</span>}
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="db-state"><Database size={15} /><span>PostgreSQL ready</span><i /></div>
        <div className="version">RAiCA 2.0</div>
      </div>
    </aside>
  );
}
