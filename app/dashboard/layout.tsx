import Link from "next/link";
import DashboardProjectTelemetry from "./DashboardProjectTelemetry";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <DashboardProjectTelemetry />
      <div className="dashboard-shell-nav-wrap">
        <nav className="dashboard-shell-nav" aria-label="Control Room">
          <Link href="/dashboard">Übersicht</Link>
          <Link href="/dashboard/traces">Traces</Link>
        </nav>
      </div>
      {children}
    </>
  );
}
