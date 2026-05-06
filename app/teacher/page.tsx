import { AssignmentsTable } from "@/components/dashboard/assignments-table";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { AuthGuard } from "@/components/auth/auth-guard";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { uz } from "@/lib/i18n/uz";

export default function TeacherPage() {
  return (
    <AuthGuard allow={["TEACHER"]}>
      <DashboardShell title={uz.sidebar.oqituvchi} role="Teacher">
        <div className="space-y-5">
          <StatsCards />
          <AssignmentsTable />
        </div>
      </DashboardShell>
    </AuthGuard>
  );
}
