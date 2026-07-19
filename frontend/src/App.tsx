import { CheckCircle2, CircleAlert, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import type { ActionItem, Candidate, DashboardData, Integration, Job, MatchItem, OutboxEvent, SyncRun, ViewKey } from "./types";
import { ActionsView } from "./views/ActionsView";
import { CandidatesView } from "./views/CandidatesView";
import { DashboardView } from "./views/DashboardView";
import { IntegrationsView } from "./views/IntegrationsView";
import { JobsView } from "./views/JobsView";
import { MatchingView } from "./views/MatchingView";

type Toast = { message: string; tone: "success" | "error" } | null;

export default function App() {
  const [view, setView] = useState<ViewKey>("dashboard");
  const [role, setRole] = useState<"ra" | "ca">("ra");
  const [dark, setDark] = useState(() => localStorage.getItem("raica-theme") === "dark");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [search, setSearch] = useState("");
  const [toast, setToast] = useState<Toast>(null);

  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [candidateStatus, setCandidateStatus] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [matchingBusy, setMatchingBusy] = useState(false);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [actionStatus, setActionStatus] = useState("open");
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [syncRuns, setSyncRuns] = useState<SyncRun[]>([]);
  const [outbox, setOutbox] = useState<OutboxEvent[]>([]);
  const [integrationBusy, setIntegrationBusy] = useState("");

  const actor = role === "ra" ? "RA 太郎" : "CA Hương";

  const notify = useCallback((message: string, tone: "success" | "error" = "success") => {
    setToast({ message, tone });
    window.setTimeout(() => setToast(null), 3600);
  }, []);

  const loadDashboard = useCallback(async () => {
    try { setDashboard(await api.dashboard()); } catch (error) { notify((error as Error).message, "error"); }
  }, [notify]);

  const loadJobs = useCallback(async () => {
    try {
      const result = await api.jobs();
      setJobs(result);
      setSelectedJobId(current => current || result[0]?.id || "");
    } catch (error) { notify((error as Error).message, "error"); }
  }, [notify]);

  const loadIntegrations = useCallback(async () => {
    try {
      const [connections, runs, events] = await Promise.all([api.integrations(), api.syncRuns(), api.outbox()]);
      setIntegrations(connections); setSyncRuns(runs); setOutbox(events);
    } catch (error) { notify((error as Error).message, "error"); }
  }, [notify]);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("raica-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    api.health().then(() => setApiOnline(true)).catch(() => setApiOnline(false));
    loadDashboard(); loadJobs();
  }, [loadDashboard, loadJobs]);

  useEffect(() => {
    if (view !== "candidates") return;
    const timer = window.setTimeout(() => api.candidates(search, candidateStatus).then(result => { setCandidates(result); setSelectedCandidate(current => result.find(item => item.id === current?.id) ?? result[0] ?? null); }).catch(error => notify(error.message, "error")), 180);
    return () => window.clearTimeout(timer);
  }, [view, search, candidateStatus, notify]);

  useEffect(() => {
    if (!selectedJobId || view !== "matching") return;
    api.matches(selectedJobId).then(setMatches).catch(error => notify(error.message, "error"));
  }, [view, selectedJobId, notify]);

  useEffect(() => {
    if (view !== "actions") return;
    api.actions(role, actionStatus).then(setActions).catch(error => notify(error.message, "error"));
  }, [view, role, actionStatus, notify]);

  useEffect(() => { if (view === "integrations") loadIntegrations(); }, [view, loadIntegrations]);

  const handleSearch = (value: string) => {
    setSearch(value);
    if (value && view !== "candidates") setView("candidates");
  };

  const openMatching = (jobId?: string) => {
    if (jobId) setSelectedJobId(jobId);
    setView("matching");
  };

  const rerunMatching = async () => {
    if (!selectedJobId) return;
    setMatchingBusy(true);
    try {
      const result = await api.rerunMatches(selectedJobId, actor);
      setMatches(result.matches);
      await loadJobs(); await loadDashboard();
      notify(`${result.generated}名をDBへ再スコアリングしました`);
    } catch (error) { notify((error as Error).message, "error"); }
    finally { setMatchingBusy(false); }
  };

  const decideMatch = async (matchId: string, status: "approved" | "rejected") => {
    try {
      await api.decideMatch(matchId, status, actor);
      setMatches(items => items.map(item => item.id === matchId ? { ...item, recommendation_status: status } : item));
      await loadDashboard();
      notify(status === "approved" ? "推薦を承認し、選考レコードを更新しました" : "見送り理由を監査ログへ記録しました");
    } catch (error) { notify((error as Error).message, "error"); }
  };

  const updateAction = async (id: string, status: "done" | "open" | "snoozed") => {
    try {
      await api.updateAction(id, status, actor);
      setActions(await api.actions(role, actionStatus));
      await loadDashboard();
      notify(status === "done" ? "対応を完了しました" : "対応状態を更新しました");
    } catch (error) { notify((error as Error).message, "error"); }
  };

  const testIntegration = async (provider: string) => {
    setIntegrationBusy(provider);
    try {
      const result = await api.testIntegration(provider, actor);
      await loadIntegrations();
      notify(result.status === "connected" ? `${provider}へ接続できました` : result.error || "接続設定が必要です", result.status === "connected" ? "success" : "error");
    } catch (error) { notify((error as Error).message, "error"); }
    finally { setIntegrationBusy(""); }
  };

  const syncPorters = async () => {
    setIntegrationBusy("porters");
    try {
      const result = await api.syncPorters(actor);
      await Promise.all([loadIntegrations(), loadJobs(), loadDashboard()]);
      notify(result.status === "completed" ? `${result.records_written}件を同期しました` : result.error_message || "Porters設定が必要です", result.status === "completed" ? "success" : "error");
    } catch (error) { notify((error as Error).message, "error"); }
    finally { setIntegrationBusy(""); }
  };

  const retryOutbox = async (eventId: string) => {
    try { await api.retryOutbox(eventId, actor); await loadIntegrations(); notify("送信を再試行しました"); }
    catch (error) { notify((error as Error).message, "error"); }
  };

  return (
    <div className="app-shell">
      <Sidebar view={view} onChange={setView} open={sidebarOpen} onClose={() => setSidebarOpen(false)} openActions={dashboard?.counts.open_actions ?? 0} />
      <div className="app-main">
        <Topbar role={role} onRole={setRole} search={search} onSearch={handleSearch} dark={dark} onDark={() => setDark(value => !value)} onMenu={() => setSidebarOpen(true)} apiOnline={apiOnline} />
        <main className="main-content">
          {view === "dashboard" && <DashboardView data={dashboard} role={role} onOpenActions={() => setView("actions")} />}
          {view === "candidates" && <CandidatesView candidates={candidates} selected={selectedCandidate} onSelect={setSelectedCandidate} status={candidateStatus} onStatus={setCandidateStatus} onMatching={() => openMatching()} />}
          {view === "jobs" && <JobsView jobs={jobs} onMatching={openMatching} />}
          {view === "matching" && <MatchingView jobs={jobs} selectedJobId={selectedJobId} onJob={setSelectedJobId} matches={matches} loading={matchingBusy} onRerun={rerunMatching} onDecision={decideMatch} />}
          {view === "actions" && <ActionsView actions={actions} role={role} onRole={setRole} status={actionStatus} onStatus={setActionStatus} onUpdate={updateAction} />}
          {view === "integrations" && <IntegrationsView integrations={integrations} syncRuns={syncRuns} outbox={outbox} busy={integrationBusy} onTest={testIntegration} onSync={syncPorters} onRetry={retryOutbox} />}
        </main>
      </div>
      {sidebarOpen && <button className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} aria-label="メニューを閉じる" />}
      {toast && <div className={`toast toast-${toast.tone}`}>{toast.tone === "success" ? <CheckCircle2 size={17} /> : <CircleAlert size={17} />}<span>{toast.message}</span><button onClick={() => setToast(null)}><X size={15} /></button></div>}
    </div>
  );
}
