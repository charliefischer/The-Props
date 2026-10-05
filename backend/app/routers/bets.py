from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import User
from app.models.league import LeagueMembership
from app.models.squad import SquadPlayer
from app.models.reference import GameWeek, PropMarket, PlayerOdds
from app.models.betting import Bet, LedgerEntry
from app.schemas.bet import BetCreate
from app.services.balance import get_membership, get_balance
from app.users import current_active_user

router = APIRouter(prefix="/leagues/{league_id}/bets", tags=["bets"])



@router.post("")
async def place_bet(
    league_id: str,
    body: BetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    membership = await get_membership(db, league_id, user.id)


    current_gw = (await db.execute(
        select(GameWeek).where(GameWeek.is_current == True)
    )).scalar_one_or_none()
    if not current_gw:
        raise HTTPException(400, "No active gameweek right now")

    # if datetime.now(timezone.utc) >= current_gw.deadline_time.replace(tzinfo=timezone.utc):
    #     raise HTTPException(400, "Betting deadline for this gameweek has passed")


    squad_entry = (await db.execute(
        select(SquadPlayer).where(
            SquadPlayer.user_id == user.id,
            SquadPlayer.player_id == body.player_id,
            SquadPlayer.removed_at.is_(None),
        )
    )).scalar_one_or_none()
    if not squad_entry:
        raise HTTPException(400, "That player is not on your squad")


    market = (await db.execute(
        select(PropMarket).where(PropMarket.code == body.prop_market_code)
    )).scalar_one_or_none()
    if not market:
        raise HTTPException(404, "Unknown prop market")


    odds_row = (await db.execute(
        select(PlayerOdds).where(
            PlayerOdds.player_id == body.player_id,
            PlayerOdds.prop_market_id == market.id,
            PlayerOdds.gameweek_id == current_gw.id,
        )
    )).scalar_one_or_none()
    if not odds_row:
        raise HTTPException(400, "No odds available for this player/market this week")


    existing_bet = (await db.execute(
        select(Bet).where(
            Bet.league_membership_id == membership.id,
            Bet.player_id == body.player_id,
            Bet.prop_market_id == market.id,
            Bet.gameweek_id == current_gw.id,
        )
    )).scalar_one_or_none()
    if existing_bet:
        raise HTTPException(400, "You've already bet on this player/market this gameweek")


    balance = await get_balance(db, membership.id)
    if body.stake > balance:
        raise HTTPException(400, f"Insufficient balance (have {balance}, need {body.stake})")


    bet = Bet(
        league_membership_id=membership.id,
        player_id=body.player_id,
        gameweek_id=current_gw.id,
        prop_market_id=market.id,
        odds_decimal=odds_row.odds_decimal,
        stake=body.stake,
        status="pending",
    )
    db.add(bet)
    await db.flush()

    new_balance = balance - body.stake
    db.add(LedgerEntry(
        league_membership_id=membership.id,
        bet_id=bet.id,
        type="stake",
        amount=-body.stake,
        balance_after=new_balance,
    ))

    await db.commit()

    return {
        "bet_id": bet.id,
        "player_id": body.player_id,
        "market": market.display_name,
        "odds_decimal": bet.odds_decimal,
        "stake": bet.stake,
        "potential_return": round(bet.stake * bet.odds_decimal, 2),
        "balance_after": new_balance,
    }


@router.get("")
async def list_bets(
    league_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
):
    membership = await get_membership(db, league_id, user.id)
    result = await db.execute(
        select(Bet).where(Bet.league_membership_id == membership.id).order_by(Bet.created_at.desc())
    )
    bets = result.scalars().all()
    return [
        {
            "id": b.id,
            "player_id": b.player_id,
            "gameweek_id": b.gameweek_id,
            "odds_decimal": b.odds_decimal,
            "stake": b.stake,
            "status": b.status,
        }
        for b in bets
    ]