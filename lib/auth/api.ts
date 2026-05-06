import { clearSession, getAccessToken, getRefreshToken, saveSession } from "@/lib/auth/storage";
import { type LoginResponse, type RefreshResponse } from "@/lib/auth/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const AUTH_MODE = process.env.NEXT_PUBLIC_AUTH_MODE ?? "api";

function createMockLogin(login: string, password: string): LoginResponse {
  if (!password) throw new Error("AUTH_FAILED");

  const normalized = login.trim().toLowerCase();
  if (normalized === "admin") {
    return { access: "mock-access-admin", refresh: "mock-refresh-admin", role: "ADMIN", full_name: "Admin User" };
  }
  if (normalized === "teacher") {
    return {
      access: "mock-access-teacher",
      refresh: "mock-refresh-teacher",
      role: "TEACHER",
      full_name: "Teacher User"
    };
  }
  if (normalized === "student") {
    return {
      access: "mock-access-student",
      refresh: "mock-refresh-student",
      role: "STUDENT",
      full_name: "Student User"
    };
  }

  throw new Error("AUTH_FAILED");
}

export async function loginRequest(login: string, password: string) {
  if (AUTH_MODE === "mock") {
    const mockData = createMockLogin(login, password);
    saveSession(mockData.access, mockData.refresh, mockData.role);
    return mockData;
  }

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login, password })
  });

  if (!response.ok) throw new Error("AUTH_FAILED");
  const data = (await response.json()) as LoginResponse;
  saveSession(data.access, data.refresh, data.role);
  return data;
}

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error("NO_REFRESH_TOKEN");

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh })
  });

  if (!response.ok) {
    clearSession();
    throw new Error("REFRESH_FAILED");
  }

  const data = (await response.json()) as RefreshResponse;
  return data.access;
}

export async function apiFetch(input: string, init?: RequestInit) {
  const access = getAccessToken();
  const headers = new Headers(init?.headers ?? {});

  if (access) {
    headers.set("Authorization", `Bearer ${access}`);
  }

  const response = await fetch(`${API_BASE_URL}${input}`, { ...init, headers });

  if (response.status !== 401) return response;

  try {
    const newAccess = await refreshAccessToken();
    const refresh = getRefreshToken();
    const role = localStorage.getItem("tugarak_user_role");
    if (refresh && role) {
      saveSession(newAccess, refresh, role as "ADMIN" | "TEACHER" | "STUDENT");
    }

    headers.set("Authorization", `Bearer ${newAccess}`);
    return fetch(`${API_BASE_URL}${input}`, { ...init, headers });
  } catch {
    clearSession();
    return response;
  }
}
