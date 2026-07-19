import { Bell, LogOut, Menu, Moon, PanelLeftClose, PanelLeftOpen, Search, Sun } from "lucide-react";
import type { Locale } from "../i18n";
import { useI18n } from "../i18n";

export function Topbar({ role, search, onSearch, dark, onDark, onMenu, navVisible, onNavVisible, apiOnline, locale, onLocale, onLogout }: { role: "ra" | "ca"; search: string; onSearch: (value: string) => void; dark: boolean; onDark: () => void; onMenu: () => void; navVisible: boolean; onNavVisible: () => void; apiOnline: boolean; locale: Locale; onLocale: (locale: Locale) => void; onLogout: () => void }) {
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
      <select className="language-select topbar-language" value={locale} onChange={event => onLocale(event.target.value as Locale)} aria-label="Language"><option value="ja">日本語</option><option value="en">English</option><option value="vi">Tiếng Việt</option></select>
      <button className="icon-button theme-toggle" onClick={onDark} title={dark ? "ライト表示" : "ダーク表示"}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
      <button className="icon-button notification-button" title="通知"><Bell size={18} /><span /></button>
      <div className="topbar-user"><span><strong>{role === "ra" ? "RA 太郎" : "CA Hương"}</strong><small>{role === "ra" ? "RA（企業担当）" : "CA（候補者担当）"} · GA Vietnam</small></span><div className="user-avatar">{role === "ra" ? "RT" : "CH"}</div></div>
      <button className="icon-button" onClick={onLogout} title="ログアウト"><LogOut size={17} /></button>
    </header>
  );
}
