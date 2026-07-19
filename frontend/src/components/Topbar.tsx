import { Bell, Menu, Moon, PanelLeftClose, PanelLeftOpen, Search, Sun } from "lucide-react";
import type { Locale } from "../i18n";
import { useI18n } from "../i18n";

export function Topbar({ role, onRole, search, onSearch, dark, onDark, onMenu, navVisible, onNavVisible, apiOnline, locale, onLocale }: { role: "ra" | "ca"; onRole: (role: "ra" | "ca") => void; search: string; onSearch: (value: string) => void; dark: boolean; onDark: () => void; onMenu: () => void; navVisible: boolean; onNavVisible: () => void; apiOnline: boolean; locale: Locale; onLocale: (locale: Locale) => void }) {
  const { t } = useI18n();
  return (
    <header className="topbar">
      <button className="icon-button mobile-menu" onClick={onMenu} title="メニュー"><Menu size={19} /></button>
      <button className="icon-button desktop-nav-toggle" onClick={onNavVisible} title={navVisible ? "サイドバーを隠す" : "サイドバーを表示"}>{navVisible ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}</button>
      <div className="search-control">
        <Search size={16} />
        <input value={search} onChange={event => onSearch(event.target.value)} placeholder={role === "ra" ? t("searchCandidates") : t("searchJobs")} aria-label={role === "ra" ? "スキルシートから候補者を検索" : "企業情報から案件を検索"} />
        <kbd>⌘ K</kbd>
      </div>
      <div className="topbar-spacer" />
      <div className="api-dot" title={apiOnline ? t("apiConnected") : "API offline"}><i className={apiOnline ? "online" : ""} /></div>
      <div className="segmented" aria-label="担当ロール">
        <button className={role === "ra" ? "selected" : ""} onClick={() => onRole("ra")}>RA</button>
        <button className={role === "ca" ? "selected" : ""} onClick={() => onRole("ca")}>CA</button>
      </div>
      <div className="segmented language-segment" aria-label="Language"><button className={locale === "ja" ? "selected" : ""} onClick={() => onLocale("ja")}>日本語</button><button className={locale === "vi" ? "selected" : ""} onClick={() => onLocale("vi")}>Tiếng Việt</button><button className={locale === "en" ? "selected" : ""} onClick={() => onLocale("en")}>English</button></div>
      <button className="icon-button theme-toggle" onClick={onDark} title={dark ? "ライト表示" : "ダーク表示"}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
      <button className="icon-button notification-button" title="通知"><Bell size={18} /><span /></button>
      <div className="topbar-user"><span><strong>{role === "ra" ? "RA 太郎" : "CA Hương"}</strong><small>{role === "ra" ? "RA（企業担当）" : "CA（候補者担当）"} · GA Vietnam</small></span><div className="user-avatar">{role === "ra" ? "RT" : "CH"}</div></div>
    </header>
  );
}
