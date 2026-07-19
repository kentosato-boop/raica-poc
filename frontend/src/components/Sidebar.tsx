import { Activity, BriefcaseBusiness, Database, GitPullRequestArrow, History, LayoutDashboard, PlugZap, Sparkles, UsersRound, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useI18n, type CopyKey } from "../i18n";
import type { ViewKey } from "../types";

const items: Array<{ key: ViewKey; label: CopyKey; icon: LucideIcon }> = [
  { key: "dashboard", label: "dashboard", icon: LayoutDashboard },
  { key: "candidates", label: "candidates", icon: UsersRound },
  { key: "jobs", label: "jobs", icon: BriefcaseBusiness },
  { key: "matching", label: "matching", icon: Sparkles },
  { key: "revival", label: "revival", icon: History },
  { key: "actions", label: "myBall", icon: GitPullRequestArrow },
  { key: "integrations", label: "integrations", icon: PlugZap },
];

export function Sidebar({ view, onChange, open, onClose, openActions }: { view: ViewKey; onChange: (view: ViewKey) => void; open: boolean; onClose: () => void; openActions: number }) {
  const { t } = useI18n();
  return (
    <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
      <div className="brand-row">
        <div className="app-icon" aria-hidden="true"><Activity size={19} strokeWidth={2.4} /></div>
        <div><strong>RAiCA</strong><span>Recruitment Intelligence</span></div>
        <button className="icon-button sidebar-close" onClick={onClose} title="メニューを閉じる"><X size={18} /></button>
      </div>
      <div className="sidebar-section-label">{t("workspace")}</div>
      <nav className="sidebar-nav" aria-label="メインナビゲーション">
        {items.map(({ key, label, icon: Icon }) => (
          <button key={key} className={view === key ? "active" : ""} onClick={() => { onChange(key); onClose(); }}>
            <Icon size={17} strokeWidth={1.9} />
            <span>{t(label)}</span>
            {key === "actions" && openActions > 0 && <span className="nav-count">{openActions}</span>}
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="db-state"><Database size={15} /><span>Data synced</span><i /></div>
        <div className="version">RAiCA 2.0</div>
      </div>
    </aside>
  );
}
