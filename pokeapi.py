"""PokeAPI クライアント（キャッシュ付き・コネクション共有）"""

import asyncio
import httpx

POKEAPI_BASE = "https://pokeapi.co/api/v2"

_cache: dict[str, dict] = {}
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """共有 httpx クライアントを取得（コネクションプール再利用）"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=15.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            http2=True,
        )
    return _client


async def _get(path: str) -> dict:
    """PokeAPI への GET リクエスト（インメモリキャッシュ付き）"""
    if path in _cache:
        return _cache[path]
    client = _get_client()
    resp = await client.get(f"{POKEAPI_BASE}/{path}")
    resp.raise_for_status()
    data = resp.json()
    _cache[path] = data
    return data


async def get_pokemon(name_or_id: str) -> dict:
    """ポケモンの基本データを取得"""
    return await _get(f"pokemon/{name_or_id.lower().strip()}")


async def get_species(name_or_id: str) -> dict:
    """ポケモンの種族データ（日本語名含む）を取得"""
    return await _get(f"pokemon-species/{name_or_id.lower().strip()}")


async def get_pokemon_and_species(name_or_id: str) -> tuple[dict, dict]:
    """ポケモンの基本データと種族データを並列取得"""
    key = name_or_id.lower().strip()
    return await asyncio.gather(
        _get(f"pokemon/{key}"),
        _get(f"pokemon-species/{key}"),
    )


async def get_type(type_name: str) -> dict:
    """タイプの詳細データを取得"""
    return await _get(f"type/{type_name.lower().strip()}")


async def get_ability(name_or_id: str) -> dict:
    """特性の詳細データを取得"""
    return await _get(f"ability/{name_or_id.lower().strip()}")


async def resolve_pokemon_id(query: str) -> int | None:
    """日本語名・英語名・IDからポケモンIDを解決する"""
    q = query.lower().strip()
    # 数字ならそのままID
    if q.isdigit():
        return int(q)
    # 英語名でまず試す
    try:
        data = await get_pokemon(q)
        return data["id"]
    except httpx.HTTPStatusError:
        pass
    # 日本語名の場合、種族リストから検索
    return await _search_by_japanese_name(q)


# 日本語名→ID のキャッシュ
_ja_name_map: dict[str, int] | None = None


async def _search_by_japanese_name(ja_name: str) -> int | None:
    """日本語名でポケモンを検索"""
    global _ja_name_map
    if _ja_name_map is None:
        _ja_name_map = {}
        # 種族リストを取得（全ポケモン）
        data = await _get("pokemon-species?limit=2000")
        for entry in data["results"]:
            species_name = entry["name"]
            try:
                species = await get_species(species_name)
                for name_entry in species.get("names", []):
                    if name_entry["language"]["name"] == "ja":
                        _ja_name_map[name_entry["name"].lower()] = species["id"]
                    elif name_entry["language"]["name"] == "ja-Hrkt":
                        _ja_name_map[name_entry["name"].lower()] = species["id"]
                    elif name_entry["language"]["name"] == "roomaji":
                        _ja_name_map[name_entry["name"].lower()] = species["id"]
            except Exception:
                continue
    return _ja_name_map.get(ja_name.lower())


async def get_ja_name_map() -> dict[str, int]:
    """日本語名→ID のマップを取得（初回呼び出し時に構築）"""
    global _ja_name_map
    if _ja_name_map is None:
        await _search_by_japanese_name("")  # キャッシュ構築のみ
    return _ja_name_map or {}


async def get_type_pokemon_names(type_name: str) -> list[str]:
    """指定タイプの全ポケモン英語名を取得"""
    data = await _get(f"type/{type_name.lower().strip()}")
    return [entry["pokemon"]["name"] for entry in data.get("pokemon", [])]


async def get_japanese_name(species_data: dict) -> str:
    """種族データから日本語名を取得"""
    for name_entry in species_data.get("names", []):
        if name_entry["language"]["name"] == "ja":
            return name_entry["name"]
    return species_data["name"]


async def get_japanese_ability_name(ability_data: dict) -> str:
    """特性データから日本語名を取得"""
    for name_entry in ability_data.get("names", []):
        if name_entry["language"]["name"] == "ja":
            return name_entry["name"]
    return ability_data["name"]
