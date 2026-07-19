import type { ReactNode } from "react";

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "success" | "warning" | "danger" | "info" | "violet" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function statusTone(status: string): "neutral" | "success" | "warning" | "danger" | "info" | "violet" {
  if (["active", "open", "connected", "completed", "delivered", "approved"].includes(status)) return "success";
  if (["urgent", "over", "failed", "error", "rejected"].includes(status)) return "danger";
  if (["due", "pending", "not_configured"].includes(status)) return "warning";
  if (["process", "running", "shortlisted"].includes(status)) return "info";
  if (["phase2", "call", "snoozed"].includes(status)) return "violet";
  return "neutral";
}
