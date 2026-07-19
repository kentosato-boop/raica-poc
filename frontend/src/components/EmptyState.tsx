import { Inbox } from "lucide-react";

export function EmptyState({ title, body }: { title: string; body: string }) {
  return <div className="empty-state"><Inbox size={24} /><strong>{title}</strong><span>{body}</span></div>;
}
