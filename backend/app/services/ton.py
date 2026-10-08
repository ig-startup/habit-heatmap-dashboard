"""TON Center public API client — fetches the current balance of a TON wallet address."""
import httpx

BALANCE_URL = "https://toncenter.com/api/v2/getAddressBalance"
NANOTON = 1_000_000_000


async def fetch_balance(address: str) -> float:
    """Fetch the current balance (in TON) for a wallet address. No API key required."""
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(BALANCE_URL, params={"address": address})
        response.raise_for_status()
        payload = response.json()

    if not payload.get("ok"):
        raise ValueError(f"TON Center error: {payload}")

    return int(payload["result"]) / NANOTON
