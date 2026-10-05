from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.player import Player
from app.models.reference import GameWeek, PropMarket, PlayerOdds
from app.users import current_active_user

router = APIRouter(prefix="/players", tags=["odds"])


@router.get("/{player_id}/odds")
async def get_player_odds(
    player_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_active_user),
):
    player = await db.get(Player, player_id)
    if not player:
        raise HTTPException(404, "Player not found")

    current_gw = (await db.execute(
        select(GameWeek).where(GameWeek.is_current == True)
    )).scalar_one_or_none()
    if not current_gw:
        return {"player_id": player_id, "gameweek": None, "markets": []}

    result = await db.execute(
        select(PlayerOdds, PropMarket)
        .join(PropMarket, PropMarket.id == PlayerOdds.prop_market_id)
        .where(
            PlayerOdds.player_id == player_id,
            PlayerOdds.gameweek_id == current_gw.id,
        )
    )
    rows = result.all()

    return {
        "player_id": player_id,
        "player_name": player.name,
        "gameweek": current_gw.fpl_event_id,
        "deadline": current_gw.deadline_time.isoformat(),
        "markets": [
            {
                "code": market.code,
                "display_name": market.display_name,
                "probability": odds.probability,
                "odds_decimal": odds.odds_decimal,
            }
            for odds, market in rows
        ],
    }