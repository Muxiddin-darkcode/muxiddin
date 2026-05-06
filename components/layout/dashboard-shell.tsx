"use client";

import { Bell, LayoutDashboard, Users, GraduationCap, CalendarDays, BookOpen } from "lucide-react";
import { ReactNode } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { uz } from "@/lib/i18n/uz";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { clearSession } from "@/lib/auth/storage";

const links = [
  { label: uz.sidebar.boshqaruvPaneli, icon: LayoutDashboard },
  { label: uz.sidebar.guruhlar, icon: Users },
  { label: uz.sidebar.darsJadvali, icon: CalendarDays },
  { label: uz.sidebar.topshiriqlar, icon: BookOpen }
];

export function DashboardShell({
  title,
  role,
  children
}: {
  title: string;
  role: "Admin" | "Teacher" | "Student";
  children: ReactNode;
}) {
  const router = useRouter();

  const handleLogout = () => {
    clearSession();
    router.replace("/login");
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="grid min-h-screen md:grid-cols-[260px_1fr]">
        <aside className="bg-sidebar p-4 text-sidebar-foreground">
          <div className="mb-8 flex items-center gap-3 px-2 pt-2">
            <GraduationCap className="h-7 w-7" />
            <div>
              <p className="text-lg font-bold">{uz.appName}</p>
              <p className="text-xs text-slate-300">LMS Platforma</p>
            </div>
          </div>
          <nav className="space-y-1">
            {links.map((link) => (
              <button
                key={link.label}
                className={cn(
                  "flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition hover:bg-white/10"
                )}
              >
                <link.icon className="h-4 w-4" />
                {link.label}
              </button>
            ))}
          </nav>
        </aside>

        <main>
          <header className="sticky top-0 z-10 flex items-center justify-between border-b bg-white/90 px-5 py-3 backdrop-blur">
            <div>
              <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
              <p className="text-sm text-slate-500">{role} kabineti</p>
            </div>
            <div className="flex items-center gap-4">
              <button className="rounded-full border p-2">
                <Bell className="h-4 w-4" />
              </button>
              <div className="text-sm font-medium text-slate-700">O'zbekcha</div>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                {uz.auth.chiqish}
              </Button>
            </div>
          </header>
          <motion.section
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="p-5"
          >
            {children}
          </motion.section>
        </main>
      </div>
    </div>
  );
}
