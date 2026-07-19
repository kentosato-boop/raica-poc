import { FileText, Mail, Send, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useI18n } from "../i18n";
import type { RecommendationDraft } from "../types";

export function RecommendationComposer({ draft, sending, onClose, onSend }: { draft: RecommendationDraft; sending: boolean; onClose: () => void; onSend: (values: { recipient: string; subject: string; body: string }) => void }) {
  const { t } = useI18n();
  const [recipient, setRecipient] = useState(draft.recipient ?? "");
  const [subject, setSubject] = useState(draft.subject);
  const [body, setBody] = useState(draft.body);
  useEffect(() => { setRecipient(draft.recipient ?? ""); setSubject(draft.subject); setBody(draft.body); }, [draft]);
  return <div className="modal-backdrop" role="presentation">
    <section className="composer-modal" role="dialog" aria-modal="true" aria-label={t("recommendationMail")}>
      <header><div><Mail size={18} /><span><strong>{t("recommendationMail")}</strong><small>{draft.recipient_label}</small></span></div><button className="icon-button" onClick={onClose} title={t("cancel")}><X size={18} /></button></header>
      <div className="composer-fields">
        <label><span>{t("recipient")}</span><input type="email" value={recipient} onChange={event => setRecipient(event.target.value)} placeholder="recruit@example.com" /></label>
        <label><span>{t("subject")}</span><input value={subject} onChange={event => setSubject(event.target.value)} /></label>
        <label><span>Body</span><textarea value={body} onChange={event => setBody(event.target.value)} /></label>
      </div>
      <div className="composer-attachment"><FileText size={16} /><span><small>{t("attachment")}</small><strong>{draft.skill_sheet_filename || t("noAttachment")}</strong></span></div>
      <footer><button className="button secondary" onClick={onClose}>{t("cancel")}</button><button className="button primary" disabled={!recipient || !subject || !body || sending} onClick={() => onSend({ recipient, subject, body })}><Send size={16} />{sending ? "..." : t("sendGmail")}</button></footer>
    </section>
  </div>;
}
