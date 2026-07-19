import { BriefcaseBusiness, Languages, LogIn, Moon, Sun, UsersRound } from "lucide-react";
import { useState } from "react";
import type { Locale } from "../i18n";

const copy = {
  ja: { title: "担当を選択してログイン", role: "担当", language: "表示言語", login: "ログイン", ra: "企業担当", ca: "候補者担当" },
  en: { title: "Choose your role to sign in", role: "Role", language: "Language", login: "Sign in", ra: "Client advisor", ca: "Candidate advisor" },
  vi: { title: "Chọn vai trò để đăng nhập", role: "Vai trò", language: "Ngôn ngữ", login: "Đăng nhập", ra: "Phụ trách doanh nghiệp", ca: "Phụ trách ứng viên" },
} satisfies Record<Locale, Record<string, string>>;

export function LoginView({ locale, onLocale, dark, onDark, onLogin }: { locale: Locale; onLocale: (locale: Locale) => void; dark: boolean; onDark: () => void; onLogin: (role: "ra" | "ca") => void }) {
  const [role, setRole] = useState<"ra" | "ca">("ra");
  const labels = copy[locale];
  return <main className="login-shell">
    <div className="login-top"><strong>RAiCA</strong><button className="icon-button" onClick={onDark} title={dark ? "Light mode" : "Dark mode"}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button></div>
    <form className="login-panel" onSubmit={event => { event.preventDefault(); onLogin(role); }}>
      <div className="login-heading"><span>RAiCA</span><h1>{labels.title}</h1></div>
      <fieldset className="login-fieldset"><legend>{labels.role}</legend><div className="role-options">
        <button type="button" className={role === "ra" ? "selected" : ""} onClick={() => setRole("ra")}><BriefcaseBusiness size={20} /><span><strong>RA</strong><small>{labels.ra}</small></span></button>
        <button type="button" className={role === "ca" ? "selected" : ""} onClick={() => setRole("ca")}><UsersRound size={20} /><span><strong>CA</strong><small>{labels.ca}</small></span></button>
      </div></fieldset>
      <label className="login-language"><span><Languages size={16} />{labels.language}</span><select value={locale} onChange={event => onLocale(event.target.value as Locale)}><option value="ja">日本語</option><option value="en">English</option><option value="vi">Tiếng Việt</option></select></label>
      <button className="button primary login-submit" type="submit"><LogIn size={17} />{labels.login}</button>
    </form>
  </main>;
}
