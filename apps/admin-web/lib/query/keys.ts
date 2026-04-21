export const queryKeys = {
  me: ["me"] as const,
  dashboard: (filters?: Record<string, string>) => ["dashboard", filters ?? {}] as const,
  dailySubmissions: (filters?: Record<string, string>) => ["daily-submissions", filters ?? {}] as const,
  dailySubmission: (submissionId: string) => ["daily-submission", submissionId] as const,
  workorders: (filters?: Record<string, string>) => ["workorders", filters ?? {}] as const,
  workorder: (workorderId: string) => ["workorder", workorderId] as const,
  users: (filters?: Record<string, string>) => ["users", filters ?? {}] as const,
  pendingUsers: ["pending-users"] as const,
  noSubmissionYet: (date: string) => ["no-submission-yet", date] as const,
};
