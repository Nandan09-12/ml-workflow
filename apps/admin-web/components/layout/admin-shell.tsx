"use client";

import type * as React from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

type AdminShellProps = React.PropsWithChildren;

export function AdminShell({ children }: AdminShellProps) {
  return (
    <div className="min-h-screen bg-canvas text-ink lg:grid lg:grid-cols-[260px_minmax(0,1fr)]">
      <div className="hidden lg:block">
        <Sidebar />
      </div>
      <main className="min-w-0">
        <div className="lg:hidden">
          <Sidebar />
        </div>
        <Topbar />
        <div className="px-4 py-6 md:px-6">{children}</div>
      </main>
    </div>
  );
}
