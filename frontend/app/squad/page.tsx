"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import Link from "next/link";

type Player = { id: string; name: string; team: string; position: string };

const MAX_SQUAD_SIZE = 15;

export default function SquadPage() {
  const { user, logout } = useAuth();
  const [allPlayers, setAllPlayers] = useState<Player[]>([]);
  const [squad, setSquad] = useState<Player[]>([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [players, mySquad] = await Promise.all([
        apiFetch("/players"),
        apiFetch("/squad"),
      ]);
      setAllPlayers(players);
      setSquad(mySquad);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const squadIds = new Set(squad.map((p) => p.id));

  async function addPlayer(playerId: string) {
    setError("");
    setBusyId(playerId);
    try {
      await apiFetch(`/squad/add/${playerId}`, { method: "POST" });
      await loadData();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  async function removePlayer(playerId: string) {
    setError("");
    setBusyId(playerId);
    try {
      await apiFetch(`/squad/remove/${playerId}`, { method: "DELETE" });
      await loadData();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <ProtectedRoute>
      <div className="max-w-3xl mx-auto p-6">
        <div className="flex justify-between items-center mb-2">
          <h1 className="text-2xl font-bold">My Squad</h1>
          <div className="text-sm">
            {user?.username} · <button onClick={logout} className="underline">Log out</button>
          </div>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          {squad.length} / {MAX_SQUAD_SIZE} players ·{" "}
          <Link href="/players" className="underline">View all players</Link>
        </p>

        {error && <p className="text-red-600 mb-4">{error}</p>}

        <h2 className="font-semibold mb-2">Current squad</h2>
        {squad.length === 0 && <p className="text-gray-500 mb-4">No players yet.</p>}
        <ul className="mb-8">
          {squad.map((p) => (
            <li key={p.id} className="flex justify-between items-center border-b py-2">
              <span>{p.name} <span className="text-gray-500 text-sm">({p.team}, {p.position})</span></span>
              <button
                onClick={() => removePlayer(p.id)}
                disabled={busyId === p.id}
                className="text-red-600 text-sm underline disabled:opacity-50"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>

        <h2 className="font-semibold mb-2">Add players</h2>
        <ul>
          {allPlayers
            .filter((p) => !squadIds.has(p.id))
            .map((p) => (
              <li key={p.id} className="flex justify-between items-center border-b py-2">
                <span>{p.name} <span className="text-gray-500 text-sm">({p.team}, {p.position})</span></span>
                <button
                  onClick={() => addPlayer(p.id)}
                  disabled={busyId === p.id || squad.length >= MAX_SQUAD_SIZE}
                  className="text-blue-600 text-sm underline disabled:opacity-50"
                >
                  Add
                </button>
              </li>
            ))}
        </ul>
      </div>
    </ProtectedRoute>
  );
}