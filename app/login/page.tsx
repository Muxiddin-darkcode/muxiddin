"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { uz } from "@/lib/i18n/uz";
import { loginRequest } from "@/lib/auth/api";
import { type UserRole } from "@/lib/auth/types";

function routeByRole(role: UserRole) {
  if (role === "ADMIN") return "/admin";
  if (role === "TEACHER") return "/teacher";
  return "/student";
}

export default function LoginPage() {
  const router = useRouter();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");

    if (!login.trim() || !password.trim()) {
      setError(uz.auth.majburiyMaydon);
      return;
    }

    try {
      setLoading(true);
      const response = await loginRequest(login, password);
      router.replace(routeByRole(response.role));
    } catch {
      setError(uz.auth.xatolik);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container flex min-h-screen items-center justify-center py-10">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{uz.auth.kirish}</CardTitle>
          <p className="text-sm text-slate-500">{uz.auth.xushKelibsiz}</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-1">
              <label className="text-sm font-medium">{uz.auth.login}</label>
              <Input value={login} onChange={(e) => setLogin(e.target.value)} placeholder="+998901234567" />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">{uz.auth.parol}</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********"
              />
            </div>

            {error ? <p className="text-sm text-red-600">{error}</p> : null}

            <Button className="w-full" type="submit" disabled={loading}>
              {loading ? "Yuklanmoqda..." : uz.auth.kirishTugmasi}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
