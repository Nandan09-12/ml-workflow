"use client";

import {
  ClipboardList,
  FileSpreadsheet,
  LayoutDashboard,
  PackageOpen,
  ShieldCheck,
  UserRoundCheck,
  Users,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/daily-submissions", label: "Daily Submissions", icon: ClipboardList },
  { href: "/workorders", label: "Workorders", icon: PackageOpen },
  { href: "/users", label: "Users", icon: Users },
  { href: "/users/pending", label: "Pending Users", icon: UserRoundCheck },
  { href: "/no-submission-yet", label: "No Submission Yet", icon: ShieldCheck },
  { href: "/reports", label: "Reports", icon: FileSpreadsheet },
];

export function Sidebar() {
  const pathname = usePathname();
  const activeHref = navItems
    .filter(({ href }) => pathname === href || (href !== "/dashboard" && pathname.startsWith(`${href}/`)))
    .sort((left, right) => right.href.length - left.href.length)[0]?.href;

  return (
    <aside className="flex h-auto flex-col gap-6 border-b border-line bg-panel p-4 lg:sticky lg:top-0 lg:h-screen lg:border-b-0 lg:border-r">
      <div className="rounded-panel border border-line bg-white p-4 text-center shadow-sm">
        <div className="flex justify-center">
          <Image src="/ml-technologies-logo.jpeg" alt="ML Technologies" width={176} height={72} className="h-auto w-auto max-w-full" priority />
        </div>
        <div className="mt-3">
          <strong className="block text-sm font-semibold text-ink">ML Technologies</strong>
          <span className="mt-1 block text-xs font-bold uppercase tracking-[0.14em] text-neutral">DT Check-in V1</span>
        </div>
      </div>
      <nav className="flex gap-1 overflow-x-auto lg:grid" aria-label="Admin navigation">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = activeHref === href;

          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex min-h-11 min-w-max items-center gap-3 rounded-panel px-3 py-2 text-sm font-semibold transition lg:min-w-0",
                active ? "bg-brand-soft text-brand" : "text-slate-700 hover:bg-slate-50 hover:text-ink",
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto rounded-panel border border-line bg-slate-50 p-4 text-sm text-neutral">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-3 w-3 rounded-full bg-success shadow-[0_0_0_4px_rgba(31,122,83,0.14)]" />
          <div>
            <strong className="block text-sm font-semibold text-ink">Admin Console</strong>
            <span className="text-xs uppercase tracking-[0.12em]">Docker-first frontend</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
