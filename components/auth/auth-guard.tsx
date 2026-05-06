"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, getUserRole } from "@/lib/auth/storage";
import { type UserRole } from "@/lib/auth/types";

type Props = {
  allow: UserRole[];
  children: React.ReactNode;
};

export function AuthGuard({ allow, children }: Props) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    const role = getUserRole();

    if (!token || !role) {
      router.replace("/login");
      return;
    }

    if (!allow.includes(role)) {
      router.replace("/login");
      return;
    }

    setReady(true);
  }, [allow, router]);

  if (!ready) {
    return <div className="p-8 text-sm text-slate-500">Yuklanmoqda...</div>;
  }

  return <>{children}</>;
}
