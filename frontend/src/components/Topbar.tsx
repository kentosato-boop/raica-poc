import { Bell, Menu, Moon, Search, Sun } from "lucide-react";

export function Topbar({ role, onRole, search, onSearch, dark, onDark, onMenu, apiOnline }: { role: "ra" | "ca"; onRole: (role: "ra" | "ca") => void; search: string; onSearch: (value: string) => void; dark: boolean; onDark: () => void; onMenu: () => void; apiOnline: boolean }) {
  return (
    <header className="topbar">
      <button className="icon-button mobile-menu" onClick={onMenu} title="メニュー"><Menu size={19} /></button>
      <div className="search-control">
        <Search size={16} />
        <input value={search} onChange={event => onSearch(event.target.value)} placeholder="候補者・求人を検索" aria-label="検索" />
        <kbd>⌘ K</kbd>
      </div>
      <div className="topbar-spacer" />
      <div className="api-state" title={apiOnline ? "API接続済み" : "API接続を確認してください"}><i className={apiOnline ? "online" : ""} />{apiOnline ? "Live" : "Offline"}</div>
      <div className="segmented" aria-label="担当ロール">
        <button className={role === "ra" ? "selected" : ""} onClick={() => onRole("ra")}>RA</button>
        <button className={role === "ca" ? "selected" : ""} onClick={() => onRole("ca")}>CA</button>
      </div>
      <button className="icon-button" onClick={onDark} title={dark ? "ライト表示" : "ダーク表示"}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
      <button className="icon-button notification-button" title="通知"><Bell size={18} /><span /></button>
      <div className="user-avatar" title={role === "ra" ? "RA 太郎" : "CA Hương"}>{role === "ra" ? "RT" : "CH"}</div>
    </header>
  );
}
