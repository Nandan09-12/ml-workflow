import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AdminShell } from "@/components/layout/admin-shell";
import { AdminGuard } from "@/components/auth/AdminGuard";
import Providers from "@/app/providers";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "ML Workflow Admin Web",
  description: "Admin console for DT Check-in operations, workorders, submissions, and user approvals.",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <AdminGuard>
            <AdminShell>{children}</AdminShell>
          </AdminGuard>
        </Providers>
      </body>
    </html>
  );
}
