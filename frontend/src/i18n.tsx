import { createContext, useContext } from "react";

export type Locale = "ja" | "vi" | "en";

const ja = {
  workspace: "ワークスペース", dashboard: "ダッシュボード", candidates: "人材データベース", jobs: "案件", matching: "推薦候補", revival: "休眠掘り起こし", myBall: "自分のボール", integrations: "連携・同期",
  searchCandidates: "候補者名・スキル・職種を検索", searchJobs: "案件名・企業・勤務地を検索", dashboardRa: "RAダッシュボード", dashboardCa: "CAダッシュボード",
  recommendations: "推薦数", interviews: "面談設定数", wins: "成約数", newJobs: "新規案件", thisMonth: "今月", last7Days: "直近7日", openItems: "未完了",
  pipeline: "選考パイプライン", pipelineSub: "自分の担当範囲", activity: "最近の更新", details: "詳細", upload: "スキルシート取込", findMatches: "この候補者に合う案件を探す",
  internalParallel: "社内並行", externalParallel: "他社並行", specialty: "専門領域", specialtyYears: "専門経験", recentTenure: "直近勤続", remote: "勤務志向", skillSheet: "スキルシート", caMemo: "CAメモ",
  all: "すべて", active: "活動中", process: "選考中", dormant: "休眠", jobOrders: "案件一覧", aiCandidates: "推薦候補", viewMatches: "推薦候補を見る",
  matchingTitle: "推薦候補", rerun: "AI再マッチング", approve: "推薦を承認", approved: "承認済み", reject: "見送り", evidence: "推薦根拠", ngCheck: "条件確認",
  recommendationMail: "推薦メール", recipient: "送信先", subject: "件名", sendGmail: "Gmailで送信", cancel: "閉じる", attachment: "添付", noAttachment: "スキルシート未登録",
  mine: "今日、自分が動かすもの", theirs: "相手待ち", complete: "完了", hold: "保留", restore: "戻す", due: "期限", actionsEmpty: "該当するタスクはありません",
  revivalTitle: "休眠候補者の掘り起こし", revivalSub: "過去の接触履歴と現在の案件から再接触候補を抽出", generateMessage: "AI文面を作成", database: "DATABASE", apiConnected: "API接続済み",
};

type Dictionary = Record<keyof typeof ja, string>;

const en: Dictionary = {
  workspace: "Workspace", dashboard: "Dashboard", candidates: "Talent database", jobs: "Job orders", matching: "Recommendations", revival: "Re-engagement", myBall: "My actions", integrations: "Integrations",
  searchCandidates: "Search candidates, skills, or roles", searchJobs: "Search jobs, companies, or locations", dashboardRa: "RA Dashboard", dashboardCa: "CA Dashboard",
  recommendations: "Recommendations", interviews: "Interviews set", wins: "Placements", newJobs: "New jobs", thisMonth: "This month", last7Days: "Last 7 days", openItems: "Open",
  pipeline: "Selection pipeline", pipelineSub: "My assigned scope", activity: "Recent updates", details: "Details", upload: "Import skill sheet", findMatches: "Find matching jobs",
  internalParallel: "Internal processes", externalParallel: "External processes", specialty: "Specialty", specialtyYears: "Specialty tenure", recentTenure: "Recent tenure", remote: "Work preference", skillSheet: "Skill sheet", caMemo: "CA notes",
  all: "All", active: "Active", process: "In process", dormant: "Dormant", jobOrders: "Job orders", aiCandidates: "Candidates", viewMatches: "View recommendations",
  matchingTitle: "Recommended candidates", rerun: "Run AI matching", approve: "Approve recommendation", approved: "Approved", reject: "Reject", evidence: "Recommendation evidence", ngCheck: "Requirement check",
  recommendationMail: "Recommendation email", recipient: "Recipient", subject: "Subject", sendGmail: "Send with Gmail", cancel: "Close", attachment: "Attachment", noAttachment: "No skill sheet",
  mine: "My actions for today", theirs: "Waiting on others", complete: "Complete", hold: "Hold", restore: "Restore", due: "Due", actionsEmpty: "No matching tasks",
  revivalTitle: "Re-engage dormant candidates", revivalSub: "Find candidates to contact again from history and current jobs", generateMessage: "Generate AI message", database: "DATABASE", apiConnected: "API connected",
};

const vi: Dictionary = {
  workspace: "Không gian làm việc", dashboard: "Bảng điều khiển", candidates: "Cơ sở dữ liệu ứng viên", jobs: "Đơn tuyển dụng", matching: "Ứng viên đề xuất", revival: "Kích hoạt lại", myBall: "Việc của tôi", integrations: "Liên kết · Đồng bộ",
  searchCandidates: "Tìm ứng viên, kỹ năng hoặc vị trí", searchJobs: "Tìm việc, công ty hoặc địa điểm", dashboardRa: "Bảng điều khiển RA", dashboardCa: "Bảng điều khiển CA",
  recommendations: "Số đề xuất", interviews: "Lịch phỏng vấn", wins: "Chốt tuyển", newJobs: "Việc mới", thisMonth: "Tháng này", last7Days: "7 ngày gần đây", openItems: "Chưa xong",
  pipeline: "Quy trình tuyển chọn", pipelineSub: "Phạm vi phụ trách", activity: "Cập nhật gần đây", details: "Chi tiết", upload: "Nhập skill sheet", findMatches: "Tìm việc phù hợp",
  internalParallel: "Song song nội bộ", externalParallel: "Song song bên ngoài", specialty: "Chuyên môn", specialtyYears: "Số năm chuyên môn", recentTenure: "Thâm niên gần nhất", remote: "Mong muốn làm việc", skillSheet: "Skill sheet", caMemo: "Ghi chú CA",
  all: "Tất cả", active: "Đang hoạt động", process: "Đang tuyển chọn", dormant: "Ngủ", jobOrders: "Danh sách việc", aiCandidates: "Ứng viên đề xuất", viewMatches: "Xem đề xuất",
  matchingTitle: "Ứng viên đề xuất", rerun: "Chạy AI matching", approve: "Duyệt đề xuất", approved: "Đã duyệt", reject: "Loại", evidence: "Căn cứ đề xuất", ngCheck: "Kiểm tra điều kiện",
  recommendationMail: "Email giới thiệu", recipient: "Người nhận", subject: "Tiêu đề", sendGmail: "Gửi bằng Gmail", cancel: "Đóng", attachment: "Tệp đính kèm", noAttachment: "Chưa có skill sheet",
  mine: "Việc tôi cần làm hôm nay", theirs: "Đang chờ đối phương", complete: "Hoàn thành", hold: "Tạm giữ", restore: "Khôi phục", due: "Hạn", actionsEmpty: "Không có công việc phù hợp",
  revivalTitle: "Kích hoạt ứng viên ngủ", revivalSub: "Tìm người nên liên hệ lại từ lịch sử và việc đang tuyển", generateMessage: "Tạo tin nhắn AI", database: "CƠ SỞ DỮ LIỆU", apiConnected: "Đã kết nối API",
};

export type CopyKey = keyof typeof ja;
const dictionaries = { ja, en, vi };
const I18nContext = createContext({ locale: "ja" as Locale, t: (key: CopyKey) => ja[key] });

export const I18nProvider = I18nContext.Provider;
export function createTranslator(locale: Locale) { return (key: CopyKey) => dictionaries[locale][key] || ja[key]; }
export function useI18n() { return useContext(I18nContext); }
