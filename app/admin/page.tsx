import { AssignmentsTable } from "@/components/dashboard/assignments-table";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { AuthGuard } from "@/components/auth/auth-guard";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { uz } from "@/lib/i18n/uz";

export default function AdminPage() {
  return (
    <AuthGuard allow={["ADMIN"]}>
      <DashboardShell title={uz.sidebar.admin} role="Admin">
        <div className="space-y-5">
          <StatsCards />
          <AssignmentsTable />
        </div>
      </DashboardShell>
    </AuthGuard>
  );
}
