import { CheckCircle2, CircleAlert, X } from "lucide-react";
import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { RecommendationComposer } from "./components/RecommendationComposer";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { createTranslator, I18nProvider, type Locale } from "./i18n";
import type { ActionItem, Candidate, DashboardData, Integration, Job, MatchItem, OutboxEvent, RecommendationDraft, SyncRun, ViewKey } from "./types";
import { DashboardView } from "./views/DashboardView";

const ActionsView = lazy(() => import("./views/ActionsView").then(module => ({ default: module.ActionsView })));
const CandidatesView = lazy(() => import("./views/CandidatesView").then(module => ({ default: module.CandidatesView })));
const IntegrationsView = lazy(() => import("./views/IntegrationsView").then(module => ({ default: module.IntegrationsView })));
const JobsView = lazy(() => import("./views/JobsView").then(module => ({ default: module.JobsView })));
const MatchingView = lazy(() => import("./views/MatchingView").then(module => ({ default: module.MatchingView })));
const RevivalView = lazy(() => import("./views/RevivalView").then(module => ({ default: module.RevivalView })));

type Toast = { message: string; tone: "success" | "error" } | null;

export default function App() {
  const [view, setView] = useState<ViewKey>("dashboard");
  const [role, setRole] = useState<"ra" | "ca">("ra");
  const [locale, setLocale] = useState<Locale>(() => (localStorage.getItem("raica-locale") as Locale) || "ja");
  const [dark, setDark] = useState(() => localStorage.getItem("raica-theme") === "dark");
  const [navVisible, setNavVisible] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [search, setSearch] = useState("");
  const [toast, setToast] = useState<Toast>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [candidateStatus, setCandidateStatus] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [uploading, setUploading] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [candidateMatches, setCandidateMatches] = useState<MatchItem[]>([]);
  const [matchingBusy, setMatchingBusy] = useState(false);
  const [draft, setDraft] = useState<RecommendationDraft | null>(null);
  const [sending, setSending] = useState(false);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [actionStatus, setActionStatus] = useState("open");
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [syncRuns, setSyncRuns] = useState<SyncRun[]>([]);
  const [outbox, setOutbox] = useState<OutboxEvent[]>([]);
  const [integrationBusy, setIntegrationBusy] = useState("");

  const actor = role === "ra" ? "RA 太郎" : "CA Huong";
  const t = createTranslator(locale);
  const notify = useCallback((message: string, tone: "success" | "error" = "success") => {
    setToast({ message, tone });
    window.setTimeout(() => setToast(null), 3600);
  }, []);

  const loadDashboard = useCallback(async () => {
    try { setDashboard(await api.dashboard(role, actor)); } catch (error) { notify((error as Error).message, "error"); }
  }, [actor, notify, role]);
  const loadJobs = useCallback(async (query = "") => {
    try {
      const result = await api.jobs(query);
      setJobs(result);
      setSelectedJobId(current => result.some(item => item.id === current) ? current : result[0]?.id || "");
    } catch (error) { notify((error as Error).message, "error"); }
  }, [notify]);
  const loadIntegrations = useCallback(async () => {
    try {
      const [connections, runs, events] = await Promise.all([api.integrations(), api.syncRuns(), api.outbox()]);
      setIntegrations(connections); setSyncRuns(runs); setOutbox(events);
    } catch (error) { notify((error as Error).message, "error"); }
  }, [notify]);

  useEffect(() => { document.documentElement.dataset.theme = dark ? "dark" : "light"; localStorage.setItem("raica-theme", dark ? "dark" : "light"); }, [dark]);
  useEffect(() => { localStorage.setItem("raica-locale", locale); document.documentElement.lang = locale; }, [locale]);
  useEffect(() => { api.health().then(() => setApiOnline(true)).catch(() => setApiOnline(false)); loadJobs(); }, [loadJobs]);
  useEffect(() => { setSearch(""); loadDashboard(); }, [role, loadDashboard]);

  useEffect(() => {
    if (view !== "candidates" && view !== "revival") return;
    const timer = window.setTimeout(() => {
      const status = view === "revival" ? "dormant" : candidateStatus;
      const query = view === "candidates" && role === "ra" ? search : "";
      api.candidates(query, status).then(result => { setCandidates(result); setSelectedCandidate(current => result.find(item => item.id === current?.id) ?? result[0] ?? null); }).catch(error => notify(error.message, "error"));
    }, 180);
    return () => window.clearTimeout(timer);
  }, [view, role, search, candidateStatus, notify]);
  useEffect(() => { if (view === "jobs") { const timer = window.setTimeout(() => loadJobs(role === "ca" ? search : ""), 180); return () => window.clearTimeout(timer); } }, [view, role, search, loadJobs]);
  useEffect(() => { if (selectedJobId && (view === "matching" || view === "jobs")) api.matches(selectedJobId).then(setMatches).catch(error => notify(error.message, "error")); }, [view, selectedJobId, notify]);
  useEffect(() => { if (view === "actions") api.actions(role, actionStatus).then(setActions).catch(error => notify(error.message, "error")); }, [view, role, actionStatus, notify]);
  useEffect(() => { if (view === "integrations") loadIntegrations(); }, [view, loadIntegrations]);

  const handleSearch = (value: string) => { setSearch(value); if (value) setView(role === "ra" ? "candidates" : "jobs"); };
  const openMatching = (jobId?: string) => { if (jobId) setSelectedJobId(jobId); setView("matching"); };
  const uploadSkillSheet = async (file: File) => {
    if (!selectedCandidate) return;
    setUploading(true);
    try {
      const result = await api.uploadSkillSheet(selectedCandidate.id, file);
      setSelectedCandidate(result.candidate);
      setCandidates(items => items.map(item => item.id === result.candidate.id ? result.candidate : item));
      notify(`${file.name}: ${result.analysis.skills.length} skills imported`);
    } catch (error) { notify((error as Error).message, "error"); } finally { setUploading(false); }
  };
  const loadCandidateMatches = async () => {
    if (!selectedCandidate) return;
    try { setCandidateMatches(await api.candidateMatches(selectedCandidate.id)); }
    catch (error) { notify((error as Error).message, "error"); }
  };
  const rerunMatching = async () => {
    if (!selectedJobId) return;
    setMatchingBusy(true);
    try { const result = await api.rerunMatches(selectedJobId, actor); setMatches(result.matches); await Promise.all([loadJobs(), loadDashboard()]); notify(`${result.generated} candidates scored`); }
    catch (error) { notify((error as Error).message, "error"); } finally { setMatchingBusy(false); }
  };
  const decideMatch = async (matchId: string, status: "approved" | "rejected") => {
    try {
      const result = await api.decideMatch(matchId, status, actor);
      setMatches(items => items.map(item => item.id === matchId ? { ...item, recommendation_status: status } : item));
      if (result.recommendation_draft) setDraft(result.recommendation_draft);
      await loadDashboard();
      notify(status === "approved" ? "推薦文を作成しました" : "見送りを記録しました");
    } catch (error) { notify((error as Error).message, "error"); }
  };
  const sendRecommendation = async (values: { recipient: string; subject: string; body: string }) => {
    if (!draft) return;
    setSending(true);
    try {
      const result = await api.sendContact({ channel: "gmail", candidate_id: draft.candidate_id, company_id: draft.company_id, recipient: values.recipient, subject: values.subject, body: values.body, human_approved_by: actor });
      setDraft(null);
      notify(result.delivery_status === "delivered" ? "Gmailで送信しました" : "Gmail送信キューへ保存しました", result.delivery_status === "failed" ? "error" : "success");
    } catch (error) { notify((error as Error).message, "error"); } finally { setSending(false); }
  };
  const updateAction = async (id: string, status: "done" | "open" | "snoozed") => { try { await api.updateAction(id, status, actor); setActions(await api.actions(role, actionStatus)); await loadDashboard(); notify("Task updated"); } catch (error) { notify((error as Error).message, "error"); } };
  const testIntegration = async (provider: string) => { setIntegrationBusy(provider); try { const result = await api.testIntegration(provider, actor); await loadIntegrations(); notify(result.status === "connected" ? `${provider} connected` : result.error || "Configuration required", result.status === "connected" ? "success" : "error"); } catch (error) { notify((error as Error).message, "error"); } finally { setIntegrationBusy(""); } };
  const syncPorters = async () => { setIntegrationBusy("porters"); try { const result = await api.syncPorters(actor); await Promise.all([loadIntegrations(), loadJobs(), loadDashboard()]); notify(result.status === "completed" ? `${result.records_written} records synced` : result.error_message || "Porters configuration required", result.status === "completed" ? "success" : "error"); } catch (error) { notify((error as Error).message, "error"); } finally { setIntegrationBusy(""); } };
  const retryOutbox = async (eventId: string) => { try { await api.retryOutbox(eventId, actor); await loadIntegrations(); notify("Retry queued"); } catch (error) { notify((error as Error).message, "error"); } };

  return <I18nProvider value={{ locale, t }}>
    <div className={`app-shell ${navVisible ? "" : "nav-hidden"}`}>
      {navVisible && <Sidebar view={view} onChange={setView} open={sidebarOpen} onClose={() => setSidebarOpen(false)} openActions={dashboard?.counts.open_actions ?? 0} />}
      <div className="app-main">
        <Topbar role={role} onRole={setRole} search={search} onSearch={handleSearch} dark={dark} onDark={() => setDark(value => !value)} onMenu={() => { setNavVisible(true); setSidebarOpen(true); }} navVisible={navVisible} onNavVisible={() => setNavVisible(value => !value)} apiOnline={apiOnline} locale={locale} onLocale={setLocale} />
        <main className="main-content"><Suspense fallback={<div className="view-loading" aria-label="読み込み中"><i /><span>Loading</span></div>}>
          {view === "dashboard" && <DashboardView data={dashboard} role={role} onOpenActions={() => setView("actions")} />}
          {view === "candidates" && <CandidatesView role={role} candidates={candidates} selected={selectedCandidate} onSelect={candidate => { setSelectedCandidate(candidate); setCandidateMatches([]); }} status={candidateStatus} onStatus={setCandidateStatus} matches={candidateMatches} onLoadMatches={loadCandidateMatches} onUpload={uploadSkillSheet} uploading={uploading} />}
          {view === "jobs" && <JobsView role={role} jobs={jobs} selectedJobId={selectedJobId} onSelect={setSelectedJobId} matches={matches} loading={matchingBusy} onRerun={rerunMatching} onDecision={decideMatch} />}
          {view === "matching" && <MatchingView jobs={jobs} selectedJobId={selectedJobId} onJob={setSelectedJobId} matches={matches} loading={matchingBusy} onRerun={rerunMatching} onDecision={decideMatch} />}
          {view === "revival" && <RevivalView candidates={candidates} onSelect={candidate => { setSelectedCandidate(candidate); setView("candidates"); }} />}
          {view === "actions" && <ActionsView actions={actions} role={role} onRole={setRole} status={actionStatus} onStatus={setActionStatus} onUpdate={updateAction} />}
          {view === "integrations" && <IntegrationsView integrations={integrations} syncRuns={syncRuns} outbox={outbox} busy={integrationBusy} onTest={testIntegration} onSync={syncPorters} onRetry={retryOutbox} />}
        </Suspense></main>
      </div>
      {sidebarOpen && <button className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} aria-label="Close menu" />}
      {draft && <RecommendationComposer draft={draft} sending={sending} onClose={() => setDraft(null)} onSend={sendRecommendation} />}
      {toast && <div className={`toast toast-${toast.tone}`}>{toast.tone === "success" ? <CheckCircle2 size={17} /> : <CircleAlert size={17} />}<span>{toast.message}</span><button onClick={() => setToast(null)}><X size={15} /></button></div>}
    </div>
  </I18nProvider>;
}
