"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type User = { id: string; email: string; username: string };

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    refreshUser();
  }, []);

  async function refreshUser() {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const me = await apiFetch("/users/me");
      setUser(me);
    } catch {
      localStorage.removeItem("token");
    } finally {
      setLoading(false);
    }
  }

  async function login(email: string, password: string) {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/jwt/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) throw new Error("Invalid email or password");
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    await refreshUser();
    router.push("/players");
  }

  async function register(email: string, username: string, password: string) {
    await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, username, password }),
    });
    await login(email, password);
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
    router.push("/login");
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}