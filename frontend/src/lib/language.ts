const STORAGE_KEY = "reportChatLanguage";

export function getReportChatLanguage(): string {
  const v = localStorage.getItem(STORAGE_KEY);
  return (v && v.trim()) ? v.trim() : "de";
}
