"use client";

import { Bell, Search } from "lucide-react";
import { usePathname } from "next/navigation";
import { currentAdmin } from "@/lib/mock/data";

const routeTitles: Array<[string, string]> = [
  ["/users/pending", "Pending Users"],
  ["/daily-submissions", "Daily Submissions"],
  ["/workorders", "Workorders"],
  ["/no-submission-yet", "No Submission Yet"],
  ["/reports", "Reports"],
  ["/users", "Users"],
  ["/dashboard", "Dashboard"],
];

export function Topbar() {
  const pathname = usePathname();
  const title = routeTitles.find(([key]) => pathname === key || pathname.startsWith(`${key}/`))?.[1] ?? "Admin Console";

  return (
    <header className="sticky top-0 z-30 flex flex-col gap-4 border-b border-line bg-canvas/95 px-6 py-4 backdrop-blur md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-brand">ML Technologies</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-ink">{title}</h1>
      </div>
      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <label className="flex min-w-[18rem] items-center gap-2 rounded-panel border border-line bg-panel px-3 py-2 shadow-sm">
          <Search className="h-4 w-4 text-neutral" />
          <span className="sr-only">Search</span>
          <input className="w-full border-0 bg-transparent p-0 text-sm text-ink outline-none ring-0 placeholder:text-neutral focus:outline-none" defaultValue="WO-NE-401" aria-label="Search workorders, testers, emails, or tickets" />
        </label>
        <button type="button" aria-label="Notifications" className="inline-flex h-11 w-11 items-center justify-center rounded-panel border border-line bg-panel text-slate-700 transition hover:border-slate-400 hover:bg-slate-50">
          <Bell className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-3 rounded-panel border border-line bg-panel px-2 py-2">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand text-sm font-extrabold text-white">{currentAdmin.initials}</span>
          <div>
            <strong className="block text-sm font-semibold text-ink">{currentAdmin.fullName}</strong>
            <span className="block text-xs font-bold uppercase tracking-[0.12em] text-neutral">{currentAdmin.role}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
