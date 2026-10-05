"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";

type Market = { code: string; display_name: string; probability: number; odds_decimal: number };
type PlayerOdds = { player_id: string; player_name: string; gameweek: number | null; markets: Market[] };
type SquadPlayer = { id: string; name: string; team: string; position: string };
type Bet = { id: string; player_id: string; odds_decimal: number; stake: number; status: string };

export default function LeagueDetailPage() {
  const { id: leagueId } = useParams<{ id: string }>();
  const { user, logout } = useAuth();

  const [balance, setBalance] = useState<number | null>(null);
  const [squad, setSquad] = useState<SquadPlayer[]>([]);
  const [oddsByPlayer, setOddsByPlayer] = useState<Record<string, PlayerOdds>>({});
  const [myBets, setMyBets] = useState<Bet[]>([]);
  const [expandedPlayer, setExpandedPlayer] = useState<string | null>(null);
  const [selectedMarket, setSelectedMarket] = useState<string | null>(null);
  const [stake, setStake] = useState("");
  const [error, setError] = useState("");
  const [placing, setPlacing] = useState(false);

  useEffect(() => {
    loadAll();
  }, [leagueId]);

  async function loadAll() {
    try {
      const [bal, mySquad, bets] = await Promise.all([
        apiFetch(`/leagues/${leagueId}/balance`),
        apiFetch("/squad"),
        apiFetch(`/leagues/${leagueId}/bets`),
      ]);
      setBalance(bal.balance);
      setSquad(mySquad);
      setMyBets(bets);

      const oddsResults = await Promise.all(
        mySquad.map((p: SquadPlayer) => apiFetch(`/players/${p.id}/odds`))
      );
      const oddsMap: Record<string, PlayerOdds> = {};
      oddsResults.forEach((o: PlayerOdds) => {
        oddsMap[o.player_id] = o;
      });
      setOddsByPlayer(oddsMap);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function betOnPlayerThisGameweek(playerId: string) {
    const gw = oddsByPlayer[playerId]?.gameweek;
    return myBets.find((b) => b.player_id === playerId); // same-gameweek dedup handled server-side too
  }

  function openPlayer(playerId: string) {
    setExpandedPlayer(expandedPlayer === playerId ? null : playerId);
    setSelectedMarket(null);
    setStake("");
    setError("");
  }

  async function placeBet(playerId: string) {
    if (!selectedMarket || !stake) return;
    setError("");
    setPlacing(true);
    try {
      await apiFetch(`/leagues/${leagueId}/bets`, {
        method: "POST",
        body: JSON.stringify({
          player_id: playerId,
          prop_market_code: selectedMarket,
          stake: parseFloat(stake),
        }),
      });
      setExpandedPlayer(null);
      setSelectedMarket(null);
      setStake("");
      await loadAll();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setPlacing(false);
    }
  }

  return (
    <ProtectedRoute>
      <div className="max-w-3xl mx-auto p-6">
        <div className="flex justify-between items-center mb-2">
          <h1 className="text-2xl font-bold">League</h1>
          <div className="text-sm">
            {user?.username} · <button onClick={logout} className="underline">Log out</button>
          </div>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          Balance: <span className="font-semibold">{balance ?? "..."} credits</span> ·{" "}
          <Link href={`/leagues/${leagueId}/leaderboard`} className="underline">Leaderboard</Link> ·{" "}
          <Link href="/leagues" className="underline">All leagues</Link>
        </p>

        {error && <p className="text-red-600 mb-4">{error}</p>}

        <h2 className="font-semibold mb-2">Your squad — place a bet</h2>
        <ul>
          {squad.map((player) => {
            const odds = oddsByPlayer[player.id];
            const alreadyBet = betOnPlayerThisGameweek(player.id);
            const isExpanded = expandedPlayer === player.id;

            return (
              <li key={player.id} className="border-b py-3">
                <button
                  onClick={() => openPlayer(player.id)}
                  className="w-full flex justify-between items-center text-left"
                >
                  <span>
                    {player.name}{" "}
                    <span className="text-gray-500 text-sm">({player.team}, {player.position})</span>
                  </span>
                  {alreadyBet ? (
                    <span className="text-xs text-gray-400">
                      Bet placed · {alreadyBet.status}
                    </span>
                  ) : (
                    <span className="text-sm underline">{isExpanded ? "Close" : "View odds"}</span>
                  )}
                </button>

                {isExpanded && (
                  <div className="mt-3 pl-2">
                    {!odds || odds.markets.length === 0 ? (
                      <p className="text-sm text-gray-500">No markets available this gameweek yet.</p>
                    ) : (
                      <>
                        <div className="grid grid-cols-2 gap-2 mb-3">
                          {odds.markets.map((m) => (
                            <button
                              key={m.code}
                              onClick={() => setSelectedMarket(m.code)}
                              className={`text-sm text-left border rounded px-3 py-2 ${
                                selectedMarket === m.code ? "border-black bg-gray-50" : "border-gray-200"
                              }`}
                            >
                              {m.display_name}
                              <br />
                              <span className="text-gray-500">odds: {m.odds_decimal}</span>
                            </button>
                          ))}
                        </div>

                        {selectedMarket && (
                          <div className="flex items-center gap-2">
                            <input
                              type="number"
                              min="0.5"
                              step="0.5"
                              placeholder="Stake"
                              value={stake}
                              onChange={(e) => setStake(e.target.value)}
                              className="border rounded px-3 py-2 w-28"
                            />
                            <button
                              onClick={() => placeBet(player.id)}
                              disabled={placing || !stake}
                              className="bg-black text-white rounded px-4 py-2 text-sm disabled:opacity-50"
                            >
                              Place bet
                            </button>
                            {stake && (
                              <span className="text-sm text-gray-500">
                                to win{" "}
                                {(
                                  parseFloat(stake) *
                                  (odds.markets.find((m) => m.code === selectedMarket)?.odds_decimal || 0)
                                ).toFixed(2)}
                              </span>
                            )}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>

        {squad.length === 0 && (
          <p className="text-gray-500">
            No players in your squad yet. <Link href="/squad" className="underline">Go pick some</Link>.
          </p>
        )}

        <h2 className="font-semibold mt-8 mb-2">Your bets this gameweek</h2>
        {myBets.length === 0 && <p className="text-gray-500">No bets placed yet.</p>}
        <ul>
          {myBets.map((b) => {
            const playerName = squad.find((p) => p.id === b.player_id)?.name || b.player_id;
            return (
              <li key={b.id} className="flex justify-between border-b py-2 text-sm">
                <span>{playerName}</span>
                <span>
                  stake {b.stake} @ {b.odds_decimal} ·{" "}
                  <span
                    className={
                      b.status === "won" ? "text-green-600" :
                      b.status === "lost" ? "text-red-600" : "text-gray-500"
                    }
                  >
                    {b.status}
                  </span>
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </ProtectedRoute>
  );
}