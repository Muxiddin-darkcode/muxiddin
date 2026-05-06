import { type UserRole } from "@/lib/auth/types";

const ACCESS_TOKEN_KEY = "tugarak_access_token";
const REFRESH_TOKEN_KEY = "tugarak_refresh_token";
const USER_ROLE_KEY = "tugarak_user_role";

export function saveSession(access: string, refresh: string, role: UserRole) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  localStorage.setItem(USER_ROLE_KEY, role);
}

export function clearSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_ROLE_KEY);
}

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getUserRole() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(USER_ROLE_KEY) as UserRole | null;
}
