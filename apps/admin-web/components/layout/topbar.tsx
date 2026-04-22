"use client";

import { FormEvent, useMemo, useState } from "react";
import { Bell, Search } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";

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
  const router = useRouter();
  const { user } = useAuth();
  const [searchValue, setSearchValue] = useState("");
  const title = routeTitles.find(([key]) => pathname === key || pathname.startsWith(`${key}/`))?.[1] ?? "Admin Console";
  const adminName = user?.full_name ?? "Admin";
  const adminInitials = useMemo(() => {
    const parts = adminName
      .split(" ")
      .map((part) => part.trim())
      .filter(Boolean);

    if (parts.length === 0) {
      return "AD";
    }

    return parts
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? "")
      .join("");
  }, [adminName]);
  const adminRole = user?.approved_role ?? "ADMIN";

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuery = searchValue.trim();

    if (!trimmedQuery) {
      return;
    }

    router.push(`/workorders?workorder_code=${encodeURIComponent(trimmedQuery)}`);
  }

  return (
    <header className="sticky top-0 z-30 flex flex-col gap-4 border-b border-line bg-canvas/95 px-6 py-4 backdrop-blur md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-brand">ML Technologies</p>
        <p className="mt-1 text-3xl font-semibold tracking-tight text-ink">{title}</p>
      </div>
      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <form role="search" onSubmit={handleSearch} className="flex min-w-[18rem] items-center gap-2 rounded-panel border border-line bg-panel px-3 py-2 shadow-sm">
          <Search className="h-4 w-4 text-neutral" />
          <span className="sr-only">Search</span>
          <input
            className="w-full border-0 bg-transparent p-0 text-sm text-ink outline-none ring-0 placeholder:text-neutral focus:outline-none"
            value={searchValue}
            onChange={(event) => setSearchValue(event.target.value)}
            placeholder="Search by workorder code"
            aria-label="Search by workorder code"
          />
        </form>
        <button type="button" aria-label="Notifications" className="inline-flex h-11 w-11 items-center justify-center rounded-panel border border-line bg-panel text-slate-700 transition hover:border-slate-400 hover:bg-slate-50">
          <Bell className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-3 rounded-panel border border-line bg-panel px-2 py-2">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand text-sm font-extrabold text-white">{adminInitials}</span>
          <div>
            <strong className="block text-sm font-semibold text-ink">{adminName}</strong>
            <span className="block text-xs font-bold uppercase tracking-[0.12em] text-neutral">{adminRole}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
