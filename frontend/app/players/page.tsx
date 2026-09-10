"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";

type Player = { id: string; name: string; team: string; position: string };

export default function PlayersPage() {
  const { user, logout } = useAuth();
  const [players, setPlayers] = useState<Player[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch("/players")
      .then(setPlayers)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <ProtectedRoute>
      <div className="max-w-3xl mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Players</h1>
          <div className="text-sm">
            {user?.username} · <button onClick={logout} className="underline">Log out</button>
          </div>
        </div>

        {error && <p className="text-red-600">{error}</p>}

        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b">
              <th className="py-2">Name</th>
              <th className="py-2">Team</th>
              <th className="py-2">Position</th>
            </tr>
          </thead>
          <tbody>
            {players.map((p) => (
              <tr key={p.id} className="border-b">
                <td className="py-2">{p.name}</td>
                <td className="py-2">{p.team}</td>
                <td className="py-2">{p.position}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ProtectedRoute>
  );
}