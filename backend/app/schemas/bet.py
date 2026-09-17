from pydantic import BaseModel, Field

class BetCreate(BaseModel):
    player_id: str
    prop_market_code: str
    stake: float = Field(gt=0)