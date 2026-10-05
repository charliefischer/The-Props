"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";

type LeaderboardRow = {
  user_id: string;
  username: string;
  balance: number;
  total_funded: number;
  profit: number;
};

export default function LeaderboardPage() {
  const { id: leagueId } = useParams<{ id: string }>();
  const { user, logout } = useAuth();
  const [rows, setRows] = useState<LeaderboardRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch(`/leagues/${leagueId}/leaderboard`)
      .then(setRows)
      .catch((err) => setError(err.message));
  }, [leagueId]);

  return (
    <ProtectedRoute>
      <div className="max-w-3xl mx-auto p-6">
        <div className="flex justify-between items-center mb-2">
          <h1 className="text-2xl font-bold">Leaderboard</h1>
          <div className="text-sm">
            {user?.username} · <button onClick={logout} className="underline">Log out</button>
          </div>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          <Link href={`/leagues/${leagueId}`} className="underline">Back to league</Link>
        </p>

        {error && <p className="text-red-600">{error}</p>}

        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b">
              <th className="py-2">#</th>
              <th className="py-2">Player</th>
              <th className="py-2 text-right">Profit</th>
              <th className="py-2 text-right">Balance</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.user_id} className={`border-b ${r.user_id === user?.id ? "font-semibold" : ""}`}>
                <td className="py-2">{i + 1}</td>
                <td className="py-2">{r.username}{r.user_id === user?.id ? " (you)" : ""}</td>
                <td className={`py-2 text-right ${r.profit > 0 ? "text-green-600" : r.profit < 0 ? "text-red-600" : ""}`}>
                  {r.profit > 0 ? "+" : ""}{r.profit}
                </td>
                <td className="py-2 text-right text-gray-500">{r.balance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ProtectedRoute>
  );
}