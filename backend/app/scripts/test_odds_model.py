import asyncio
from app.services.fpl import fetch_player_history
from app.services.odds_model import calculate_market_odds, MARKET_PREDICATES

TEST_FPL_ID = 116 # Lewis Dunk
TEST_POSITION = "DEF"


async def main():
    history = await fetch_player_history(TEST_FPL_ID)
    print(f"Fetched {len(history)} gameweeks of history.\n")

    for market_code in MARKET_PREDICATES:
        result = calculate_market_odds(market_code, history, TEST_POSITION)
        if result:
            print(f"{market_code:28} prob={result['probability']:.2f}  "
                  f"odds={result['odds_decimal']}  (n={result['sample_size']})")
        else:
            print(f"{market_code:28} n/a for this position")


if __name__ == "__main__":
    asyncio.run(main())