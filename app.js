(function () {
  "use strict";

  const apiState = {
    candidates: [],
    jobs: [],
    matchesByUiId: new Map(),
    candidateDbIdByUiId: new Map(),
    nextUiId: 101,
  };

  async function api(path, options) {
    const response = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    return payload;
  }

  function daysSince(value) {
    if (!value) return 0;
    return Math.max(0, Math.floor((Date.now() - new Date(`${value}T00:00:00`).getTime()) / 86400000));
  }

  function initials(name) {
    return name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join("").toUpperCase();
  }

  function candidateUiId(dbId) {
    for (const [uiId, candidateId] of apiState.candidateDbIdByUiId) {
      if (candidateId === dbId) return uiId;
    }
    const uiId = apiState.nextUiId++;
    apiState.candidateDbIdByUiId.set(uiId, dbId);
    return uiId;
  }

  function mapCandidate(candidate) {
    const id = candidateUiId(candidate.id);
    CAND_EXTRA[id] = {
      age: candidate.age || 0,
      sex: candidate.gender || "M",
      exp: candidate.years_experience,
      ca: candidate.ca_owner,
      wish: candidate.desired_salary_million ? `${candidate.desired_salary_million}M VND` : "—",
      commute: candidate.commute_minutes ? `${candidate.commute_minutes}分` : "—",
      par: [],
      memo: candidate.notes || "",
      wk: candidate.work_style,
    };
    return {
      id,
      dbId: candidate.id,
      ini: initials(candidate.name),
      name: candidate.name,
      meta: `${candidate.age || "—"}歳・経験${candidate.years_experience}年`,
      metaVi: `${candidate.age || "—"} tuổi · ${candidate.years_experience} năm KN`,
      job: candidate.role_title,
      jobVi: candidate.role_title,
      jobEn: candidate.role_title,
      jlpt: candidate.jlpt || "—",
      last: `${daysSince(candidate.last_contact_date)}日前`,
      lastVi: `${daysSince(candidate.last_contact_date)} ngày trước`,
      lastEn: `${daysSince(candidate.last_contact_date)} d ago`,
      status: candidate.status,
      ...CAND_EXTRA[id],
    };
  }

  function mapJob(job) {
    return {
      dbId: job.id,
      t: job.title,
      tVi: job.title,
      tEn: job.title,
      c: job.company_name,
      cVi: job.company_name,
      cEn: job.company_name,
      loc: job.location || "—",
      sal: `${job.salary_min_million || "—"}〜${job.salary_max_million || "—"}M VND`,
      n: job.ai_candidate_count,
      s: job.status,
      cat: job.category,
      ind: job.industry,
      d: daysSince(job.received_date),
    };
  }

  function mapMatch(match, job) {
    const id = candidateUiId(match.candidate_id);
    const extra = CAND_EXTRA[id] || {};
    EVID[id] = {
      simPct: match.similarity_pct,
      state: match.ng_check.startsWith("要件ずらし") ? "warn" : "ok",
      note: `${match.ng_check}。${match.evidence_quote}`,
      sim: [{ who: `${job.company_name}の成約パターン`, note: match.evidence_quote }],
      ng: [{ t: match.ng_check, ok: !match.ng_check.startsWith("要件ずらし"), note: match.evidence_quote }],
      quote: [match.evidence_quote],
    };
    apiState.matchesByUiId.set(id, match);
    if (["approved", "process"].includes(match.recommendation_status)) REC_STATE.add(id);
    return {
      id,
      dbId: match.candidate_id,
      ini: initials(match.candidate_name),
      name: match.candidate_name,
      meta: `${match.age || "—"}歳・経験${match.years_experience}年`,
      metaVi: `${match.age || "—"} tuổi · ${match.years_experience} năm KN`,
      job: `${job.title}（${job.company_name}）`,
      jobVi: job.title,
      jobId: job.id,
      score: match.score,
      why: match.evidence_quote,
      whyVi: match.evidence_quote,
      whyLong: match.evidence_quote,
      shift: match.ng_check.startsWith("要件ずらし") ? match.ng_check : null,
      breakdown: [
        ["スキル", match.skill_score],
        ["経験年数", match.experience_score],
        ["日本語力", match.japanese_score],
        ["給与レンジ", match.salary_score],
        ["通勤", match.commute_score],
      ],
      jlpt: match.jlpt || "—",
      status: match.recommendation_status === "process" ? "process" : "active",
      ...extra,
    };
  }

  async function loadCoreData() {
    const [candidates, jobs, stats] = await Promise.all([
      api("/api/candidates"),
      api("/api/jobs"),
      api("/api/stats"),
    ]);
    apiState.candidates = candidates;
    apiState.jobs = jobs;

    const mappedCandidates = candidates.map(mapCandidate);
    CAND_DB.splice(0, CAND_DB.length, ...mappedCandidates);
    JOBS.splice(0, JOBS.length, ...jobs.map(mapJob));
    MATCH_JOBS.splice(0, MATCH_JOBS.length, ...jobs.filter(job => job.status !== "closed").map(job => ({
      id: job.id,
      t: `${job.title} — ${job.company_name}`,
      tVi: `${job.title} — ${job.company_name}`,
      tEn: `${job.title} — ${job.company_name}`,
      d: daysSince(job.received_date),
      n: job.ai_candidate_count,
      urgent: job.status === "urgent",
    })));

    const sync = document.getElementById("syncStatus");
    sync.textContent = `DB接続済 ${stats.candidates}候補 / ${stats.jobs}求人`;
    sync.title = "SQLite APIから取得した最新データ";
    document.getElementById("navDeskCount").textContent = stats.open_queue;
    renderJobs();
    renderCands();
    renderJobPick();
  }

  pickJob = async function (id) {
    selJob = id;
    const job = apiState.jobs.find(item => item.id === id);
    document.getElementById("matchJobTitle").textContent = `${job.title} — ${job.company_name}`;
    document.getElementById("matchTbody").innerHTML = '<tr><td colspan="5"><div class="empty"><b>DBから推薦候補を取得中</b></div></td></tr>';
    try {
      const matches = await api(`/api/matches?job_id=${encodeURIComponent(id)}`);
      CANDS.splice(0, CANDS.length, ...matches.map(match => mapMatch(match, job)));
      renderJobPick();
      renderMatch();
    } catch (error) {
      toast(`取得に失敗しました: ${error.message}`);
    }
  };

  recommend = async function (uiId) {
    const match = apiState.matchesByUiId.get(uiId);
    if (!match || REC_STATE.has(uiId)) return;
    try {
      await api(`/api/matches/${encodeURIComponent(match.id)}`, {
        method: "PATCH",
        body: JSON.stringify({ recommendation_status: "approved", actor: ROLE === "ca" ? "CA Hương" : "RA 太郎" }),
      });
      REC_STATE.add(uiId);
      renderMatch();
      renderAiRecs();
      toast(`${match.candidate_name}さんの推薦をDBに保存しました`);
    } catch (error) {
      toast(`推薦の保存に失敗しました: ${error.message}`);
    }
  };

  document.getElementById("matchingRunBtn").addEventListener("click", async () => {
    if (!selJob) return toast("先に案件を選択してください");
    const button = document.getElementById("matchingRunBtn");
    button.disabled = true;
    button.textContent = "計算中…";
    try {
      const result = await api("/api/matching/run", {
        method: "POST",
        body: JSON.stringify({ job_id: selJob, actor: ROLE === "ca" ? "CA Hương" : "RA 太郎" }),
      });
      await loadCoreData();
      await pickJob(selJob);
      toast(`${result.generated}名を再スコアリングし、DBへ保存しました`);
    } catch (error) {
      toast(`再計算に失敗しました: ${error.message}`);
    } finally {
      button.disabled = false;
      button.textContent = t("btnRerun", "AI再マッチング");
    }
  });

  document.getElementById("csvImportBtn").addEventListener("click", () => {
    toast("Porters CSVを data/ に配置後、APIから安全に取り込めます");
  });

  loadCoreData().catch(error => {
    document.getElementById("syncStatus").textContent = "静的デモ表示中";
    toast(`DB接続に失敗しました: ${error.message}`);
  });
})();
