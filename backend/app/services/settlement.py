from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.betting import Bet, LedgerEntry
from app.models.reference import GameWeek, PropMarket
from app.models.player import Player
from app.models.league import LeagueMembership, League
from app.services.fpl import fetch_player_history
from app.services.odds_model import MARKET_PREDICATES
from app.services.balance import get_balance


async def settle_gameweek_bets(db: AsyncSession, gameweek: GameWeek) -> dict:
    """Resolve every still-pending bet for a gameweek. Safe to re-run —
    only ever touches bets with status='pending'."""
    pending_bets = (await db.execute(
        select(Bet).where(Bet.gameweek_id == gameweek.id, Bet.status == "pending")
    )).scalars().all()

    counts = {"won": 0, "lost": 0, "void": 0, "errors": 0}
    if not pending_bets:
        counts["settled"] = 0
        return counts

    history_cache: dict[int, list[dict]] = {}  # avoid refetching the same player twice

    for bet in pending_bets:
        player = await db.get(Player, bet.player_id)
        market = await db.get(PropMarket, bet.prop_market_id)

        if not player or not market:
            print(f"Skipping bet {bet.id}: missing player or market record")
            counts["errors"] += 1
            continue

        if player.fpl_id not in history_cache:
            try:
                history_cache[player.fpl_id] = await fetch_player_history(player.fpl_id)
            except Exception as e:
                print(f"Skipping bet {bet.id}: could not fetch history for {player.name} ({e})")
                counts["errors"] += 1
                continue

        gw_entry = next(
            (g for g in history_cache[player.fpl_id] if g.get("round") == gameweek.fpl_event_id),
            None,
        )

        if gw_entry is None or gw_entry.get("minutes", 0) == 0:
            # No record of them playing — postponed match, injury, or an unused
            # sub. They never got a fair chance at the prop, so void and refund
            # rather than record it as a loss.
            await _resolve_bet(db, bet, status="void", payout=bet.stake)
            counts["void"] += 1
            continue

        predicate = MARKET_PREDICATES.get(market.code)
        if predicate is None:
            print(f"Skipping bet {bet.id}: no settlement rule for market '{market.code}'")
            counts["errors"] += 1
            continue

        if predicate(gw_entry):
            payout = round(bet.stake * bet.odds_decimal, 2)
            await _resolve_bet(db, bet, status="won", payout=payout)
            counts["won"] += 1
        else:
            await _resolve_bet(db, bet, status="lost", payout=0)
            counts["lost"] += 1

    await db.commit()
    counts["settled"] = counts["won"] + counts["lost"] + counts["void"]
    return counts


async def _resolve_bet(db: AsyncSession, bet: Bet, status: str, payout: float):
    bet.status = status
    bet.settled_at = datetime.now(timezone.utc)

    if payout > 0:
        current_balance = await get_balance(db, bet.league_membership_id)
        db.add(LedgerEntry(
            league_membership_id=bet.league_membership_id,
            bet_id=bet.id,
            gameweek_id=bet.gameweek_id,
            type="payout",
            amount=payout,
            balance_after=current_balance + payout,
        ))
    # A genuine loss gets no ledger entry — the stake was already
    # deducted when the bet was placed; nothing further to record.


async def grant_weekly_topups(db: AsyncSession, gameweek: GameWeek) -> int:
    """Grant every league's weekly top-up to every member, once per
    (membership, gameweek) pair. Safe to re-run."""
    memberships = (await db.execute(select(LeagueMembership))).scalars().all()
    granted = 0

    for membership in memberships:
        already_funded = (await db.execute(
            select(LedgerEntry).where(
                LedgerEntry.league_membership_id == membership.id,
                LedgerEntry.gameweek_id == gameweek.id,
                LedgerEntry.type.in_(["starting_grant", "topup"]),
            )
        )).scalar_one_or_none()

        if already_funded:
            # Covers two cases: this is the gameweek they joined in (already
            # got starting_grant), or we've already topped them up for it.
            continue

        league = await db.get(League, membership.league_id)
        current_balance = await get_balance(db, membership.id)

        db.add(LedgerEntry(
            league_membership_id=membership.id,
            gameweek_id=gameweek.id,
            type="topup",
            amount=league.weekly_topup,
            balance_after=current_balance + league.weekly_topup,
        ))
        granted += 1

    await db.commit()
    return granted