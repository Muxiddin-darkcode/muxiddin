export type UserRole = "ADMIN" | "TEACHER" | "STUDENT";

export type LoginResponse = {
  access: string;
  refresh: string;
  role: UserRole;
  full_name?: string;
};

export type RefreshResponse = {
  access: string;
};
