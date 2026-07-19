INSERT OR IGNORE INTO companies (id, name, industry, avg_reply_days, hiring_signal, notes) VALUES
('co-a', 'A社', 'mfg', 2.5, '第2工場拡張', 'ライン長と第2ラインの採用実績あり'),
('co-b', 'B社', 'mfg', 4.0, 'QC増員', '品質管理職の面接リードタイムが長め'),
('co-c', 'C社', 'mfg', 3.0, 'CNC急募', '急募時は面接設定が早い'),
('co-d', 'D社', 'trade', 2.0, '総務通訳3枠', '日本語要件を重視'),
('co-e', 'E社', 'log', 5.0, '倉庫ライン欠員', '返信遅延時は電話切替が有効'),
('co-f', 'F社', 'it', 3.5, 'Backend増員', '技術面接スピードが重要');

INSERT OR IGNORE INTO jobs (
  id, porters_id, company_id, title, category, industry, status,
  salary_min_million, salary_max_million, received_date, ai_candidate_count
) VALUES
('job-a-line', 'PT-J-0001', 'co-a', 'ライン長', 'worker', 'mfg', 'open', 13.0, 15.0, '2026-07-07', 18),
('job-a-phase2', 'PT-J-0002', 'co-a', '第2ライン要員', 'worker', 'mfg', 'phase2', 11.0, 13.5, '2026-07-10', 14),
('job-b-qc', 'PT-J-0003', 'co-b', 'QCスタッフ', 'worker', 'mfg', 'open', 12.0, 14.0, '2026-07-09', 11),
('job-c-cnc', 'PT-J-0004', 'co-c', 'CNCオペレーター', 'worker', 'mfg', 'urgent', 13.0, 16.0, '2026-07-13', 9),
('job-d-interpreter', 'PT-J-0005', 'co-d', '総務通訳', 'jp', 'trade', 'open', 14.0, 18.0, '2026-07-08', 7),
('job-f-backend', 'PT-J-0006', 'co-f', 'Backend Engineer', 'eng', 'it', 'urgent', 25.0, 35.0, '2026-07-16', 5);

INSERT OR IGNORE INTO candidates (
  id, porters_id, name, status, ca_owner, role_title, years_experience,
  jlpt, desired_salary_million, commute_minutes, work_style, last_contact_date,
  avg_response_days, notes
) VALUES
('cand-hoa', 'PT-C-0001', 'Nguyen Thi Hoa', 'process', 'CA Huong', 'Line Leader', 5, 'N3', 14.0, 35, 'onsite', '2026-07-16', 1.5, '希望14M。通訳常駐ラインなら前向き。'),
('cand-son', 'PT-C-0002', 'Phan Van Son', 'process', 'CA Huong', 'Line Staff', 3, 'N4', 12.0, 40, 'onsite', '2026-07-10', 2.0, '夜勤不可。A社第2ラインは日勤中心なら推薦可。'),
('cand-minh', 'PT-C-0003', 'Tran Van Minh', 'active', 'CA Linh', 'QC Staff', 4, 'N3', 13.0, 25, 'onsite', '2026-07-15', 2.5, '品質記録と改善提案の経験あり。'),
('cand-huy', 'PT-C-0004', 'Le Quang Huy', 'active', 'CA Linh', 'CNC Operator', 6, 'N4', 15.0, 30, 'onsite', '2026-07-14', 2.0, 'CNC旋盤と夜勤対応が可能。'),
('cand-trang', 'PT-C-0005', 'Pham Thu Trang', 'process', 'CA Mai', 'Interpreter', 4, 'N2', 16.0, 45, 'onsite', '2026-07-15', 1.8, '総務通訳経験。既読後の意思決定に時間がかかる。'),
('cand-mai', 'PT-C-0006', 'Ngo Thi Mai', 'active', 'CA Huong', 'Line Staff', 2, 'N3', 12.5, 35, 'onsite', '2026-07-19', 1.2, 'A社2024年成約者と近い経歴。'),
('cand-quan', 'PT-C-0007', 'Dang Minh Quan', 'active', 'CA Linh', 'Backend Engineer', 5, 'N3', 30.0, 0, 'remote', '2026-07-18', 1.0, '他社で技術面接通過済み。スピード勝負。'),
('cand-dormant-1', 'PT-C-9001', 'Vu Thi Lan', 'dormant', 'CA Mai', 'Factory Staff', 3, 'N4', 11.5, 45, 'onsite', '2025-03-01', 3.5, 'Zalo OA連携済み。家庭都合で一度辞退。');

INSERT OR IGNORE INTO matches (
  id, candidate_id, job_id, score, skill_score, experience_score, japanese_score,
  salary_score, commute_score, similarity_pct, ng_check, evidence_quote, recommendation_status
) VALUES
('m-hoa-a', 'cand-hoa', 'job-a-line', 94, 95, 92, 88, 90, 91, 92, '夜勤辞退パターンなし', '面談メモ: ライン管理5年、通訳常駐なら日本語業務に対応可。', 'process'),
('m-son-a2', 'cand-son', 'job-a-phase2', 82, 79, 84, 70, 88, 82, 81, '夜勤不可のため日勤枠限定', '職務経歴書: 組立ライン3年、リーダー補佐経験あり。', 'shortlisted'),
('m-minh-b', 'cand-minh', 'job-b-qc', 91, 92, 89, 84, 86, 94, 89, '給与・通勤とも許容範囲', '職務経歴書: QC工程で不良率改善プロジェクトに参加。', 'shortlisted'),
('m-huy-c', 'cand-huy', 'job-c-cnc', 88, 93, 91, 65, 82, 90, 86, '日本語はN4だが現場用語経験あり', '面談メモ: CNC旋盤6年、夜勤対応可、急募案件に即日面接可。', 'shortlisted'),
('m-trang-d', 'cand-trang', 'job-d-interpreter', 90, 88, 86, 96, 84, 78, 87, '意思決定遅延リスクあり', '職務経歴書: 日本人管理者の総務通訳を4年担当。', 'process'),
('m-mai-a2', 'cand-mai', 'job-a-phase2', 85, 82, 76, 86, 90, 84, 84, '経験2年だがN3で補完可能', '面談メモ: A社2024年成約者と同型。日勤希望。', 'shortlisted'),
('m-quan-f', 'cand-quan', 'job-f-backend', 87, 90, 88, 78, 82, 100, 83, '他社選考先行のため即対応必要', '職務経歴書: Node.js/Python API開発5年、検索基盤の経験あり。', 'shortlisted');

INSERT OR IGNORE INTO action_queue (
  id, owner_role, queue_type, target_label, due_date, severity, reason, source_ref
) VALUES
('q-ra-son', 'ra', 'client_chase', 'A社 / Phan Van Son', '2026-07-19', 'over', '書類5営業日無返答。企業平均2.5日も超過。', 'm-son-a2'),
('q-ra-huy', 'ra', 'client_chase', 'C社 / Le Quang Huy', '2026-07-19', 'due', '推薦から3営業日目。催促1回目。', 'm-huy-c'),
('q-ra-long', 'ra', 'client_call', 'E社 / Do Van Long', '2026-07-19', 'call', '催促2回後も9営業日未返信。電話切替。', NULL),
('q-ca-hoa', 'ca', 'candidate_follow', 'Nguyen Thi Hoa', '2026-07-19', 'over', '平均反応1.5日超過。電話推奨。', 'cand-hoa'),
('q-ca-trang', 'ca', 'candidate_follow', 'Pham Thu Trang', '2026-07-19', 'call', '既読無反応2回。D社へ本日中に一次回答が必要。', 'cand-trang');

UPDATE candidates SET age=27, gender='F', skills_json='["line_management","5s","kaizen"]' WHERE id='cand-hoa';
UPDATE candidates SET age=33, gender='M', skills_json='["line_management","assembly"]' WHERE id='cand-son';
UPDATE candidates SET age=31, gender='M', skills_json='["qc","iso9001","kaizen"]' WHERE id='cand-minh';
UPDATE candidates SET age=24, gender='M', skills_json='["cnc","lathe","night_shift"]' WHERE id='cand-huy';
UPDATE candidates SET age=29, gender='F', skills_json='["interpretation","administration"]' WHERE id='cand-trang';
UPDATE candidates SET age=28, gender='F', skills_json='["line_management","assembly"]' WHERE id='cand-mai';
UPDATE candidates SET age=26, gender='M', skills_json='["backend","python","nodejs"]' WHERE id='cand-quan';
UPDATE candidates SET age=30, gender='F', skills_json='["assembly"]' WHERE id='cand-dormant-1';

UPDATE jobs SET location='Bac Ninh', min_experience_years=4, min_jlpt='N3', max_commute_minutes=45,
  required_skills_json='["line_management","5s"]' WHERE id='job-a-line';
UPDATE jobs SET location='Bac Ninh', min_experience_years=2, min_jlpt='N4', max_commute_minutes=45,
  required_skills_json='["line_management","assembly"]' WHERE id='job-a-phase2';
UPDATE jobs SET location='Hung Yen', min_experience_years=3, min_jlpt='N4', max_commute_minutes=45,
  required_skills_json='["qc","kaizen"]' WHERE id='job-b-qc';
UPDATE jobs SET location='Ha Noi', min_experience_years=3, min_jlpt='N4', max_commute_minutes=40,
  required_skills_json='["cnc","lathe"]' WHERE id='job-c-cnc';
UPDATE jobs SET location='Ha Noi', min_experience_years=3, min_jlpt='N2', max_commute_minutes=60,
  required_skills_json='["interpretation","administration"]' WHERE id='job-d-interpreter';
UPDATE jobs SET location='Ha Noi / Remote', min_experience_years=4, min_jlpt='N3', max_commute_minutes=0,
  required_skills_json='["backend","python"]' WHERE id='job-f-backend';

INSERT OR IGNORE INTO applications (
  id, candidate_id, job_id, stage, recommended_at, last_event_at, company_ok, candidate_ok
) VALUES
('app-hoa-a', 'cand-hoa', 'job-a-line', 'offer', '2026-07-08', '2026-07-14', 1, 0),
('app-son-a2', 'cand-son', 'job-a-phase2', 'screening', '2026-07-10', '2026-07-10', 0, 1),
('app-minh-b', 'cand-minh', 'job-b-qc', 'first_interview', '2026-07-10', '2026-07-15', 0, 1),
('app-huy-c', 'cand-huy', 'job-c-cnc', 'screening', '2026-07-14', '2026-07-14', 0, 1),
('app-trang-d', 'cand-trang', 'job-d-interpreter', 'intent_check', '2026-07-10', '2026-07-16', 1, 0);
