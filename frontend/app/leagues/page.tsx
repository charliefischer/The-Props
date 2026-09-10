"use client";

import { useEffect, useState, FormEvent } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import Link from "next/link";

type League = { id: string; name: string; invite_code: string };

export default function LeaguesPage() {
  const { user, logout } = useAuth();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [newLeagueName, setNewLeagueName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    loadLeagues();
  }, []);

  async function loadLeagues() {
    try {
      setLeagues(await apiFetch("/leagues"));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!newLeagueName.trim()) return;
    setError("");
    setBusy(true);
    try {
      await apiFetch(`/leagues?name=${encodeURIComponent(newLeagueName)}`, {
        method: "POST",
      });
      setNewLeagueName("");
      await loadLeagues();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleJoin(e: FormEvent) {
    e.preventDefault();
    if (!joinCode.trim()) return;
    setError("");
    setBusy(true);
    try {
      await apiFetch(`/leagues/join/${joinCode.trim().toUpperCase()}`, {
        method: "POST",
      });
      setJoinCode("");
      await loadLeagues();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <ProtectedRoute>
      <div className="max-w-3xl mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">My Leagues</h1>
          <div className="text-sm">
            {user?.username} · <button onClick={logout} className="underline">Log out</button>
          </div>
        </div>

        {error && <p className="text-red-600 mb-4">{error}</p>}

        <h2 className="font-semibold mb-2">Your leagues</h2>
        {leagues.length === 0 && <p className="text-gray-500 mb-6">No leagues yet.</p>}
        <ul className="mb-8">
          {leagues.map((l) => (
            <li key={l.id} className="flex justify-between items-center border-b py-2">
              <span>{l.name}</span>
              <span className="text-sm text-gray-500">
                Invite code: <span className="font-mono">{l.invite_code}</span>
              </span>
            </li>
          ))}
        </ul>

        <div className="grid grid-cols-2 gap-8">
          <form onSubmit={handleCreate}>
            <h2 className="font-semibold mb-2">Create a league</h2>
            <input
              type="text"
              placeholder="League name"
              value={newLeagueName}
              onChange={(e) => setNewLeagueName(e.target.value)}
              className="border rounded px-3 py-2 w-full mb-2"
            />
            <button
              type="submit"
              disabled={busy}
              className="bg-black text-white rounded py-2 px-4 w-full disabled:opacity-50"
            >
              Create
            </button>
          </form>

          <form onSubmit={handleJoin}>
            <h2 className="font-semibold mb-2">Join a league</h2>
            <input
              type="text"
              placeholder="Invite code"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              className="border rounded px-3 py-2 w-full mb-2 font-mono uppercase"
            />
            <button
              type="submit"
              disabled={busy}
              className="bg-black text-white rounded py-2 px-4 w-full disabled:opacity-50"
            >
              Join
            </button>
          </form>
        </div>

        <p className="mt-8 text-sm">
          <Link href="/squad" className="underline">My squad</Link> ·{" "}
          <Link href="/players" className="underline">All players</Link>
        </p>
      </div>
    </ProtectedRoute>
  );
}