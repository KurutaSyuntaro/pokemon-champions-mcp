"""ポケモンチャンピオンズ育成支援 MCP サーバー"""

import asyncio

from mcp.server.fastmcp import FastMCP

import pokeapi
from pokemon_data import (
    NATURES,
    NATURE_JA,
    STAT_JA,
    TYPE_JA,
    ALL_TYPES,
    get_type_weaknesses,
)

mcp = FastMCP(
    "pokemon-champions",
    instructions="ポケモンチャンピオンズの育成・パーティ構築を支援するMCPサーバーです。",
)


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def _format_stat_bar(value: int, max_val: int = 255) -> str:
    """種族値をバーで可視化"""
    bar_len = int(value / max_val * 20)
    return "█" * bar_len + "░" * (20 - bar_len)


async def _fetch_pokemon_full(query: str) -> tuple[dict, dict, str]:
    """ポケモンデータ+種族データ+日本語名を取得（並列化済み）"""
    pokemon_id = await pokeapi.resolve_pokemon_id(query)
    if pokemon_id is None:
        raise ValueError(f"「{query}」に一致するポケモンが見つかりません。英語名・日本語名・図鑑番号で検索できます。")
    pokemon, species = await pokeapi.get_pokemon_and_species(str(pokemon_id))
    ja_name = await pokeapi.get_japanese_name(species)
    return pokemon, species, ja_name


async def _fetch_pokemon_full_batch(queries: list[str]) -> list[tuple[dict, dict, str]]:
    """複数ポケモンのデータを並列一括取得"""
    # まず全IDを解決
    ids = await asyncio.gather(*(pokeapi.resolve_pokemon_id(q) for q in queries))
    for q, pid in zip(queries, ids):
        if pid is None:
            raise ValueError(f"「{q}」に一致するポケモンが見つかりません。")
    # pokemon + species を並列取得
    pairs = await asyncio.gather(*(pokeapi.get_pokemon_and_species(str(pid)) for pid in ids))
    results = []
    for pokemon, species in pairs:
        ja_name = await pokeapi.get_japanese_name(species)
        results.append((pokemon, species, ja_name))
    return results


# ---------------------------------------------------------------------------
# Tool: ポケモン検索
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_pokemon(name: str) -> str:
    """ポケモンの種族値・タイプ・特性を検索します。英語名・日本語名・図鑑番号で検索できます。

    Args:
        name: ポケモンの名前（例: pikachu, ピカチュウ, 25）
    """
    try:
        pokemon, species, ja_name = await _fetch_pokemon_full(name)
    except ValueError as e:
        return str(e)

    # 種族値
    stats: dict[str, int] = {}
    for s in pokemon["stats"]:
        stats[s["stat"]["name"]] = s["base_stat"]
    total = sum(stats.values())

    # タイプ
    types = [t["type"]["name"] for t in pokemon["types"]]
    types_ja = [f"{TYPE_JA.get(t, t)}" for t in types]

    # 特性
    abilities = []
    for a in pokemon["abilities"]:
        try:
            ability_data = await pokeapi.get_ability(a["ability"]["name"])
            ab_ja = await pokeapi.get_japanese_ability_name(ability_data)
        except Exception:
            ab_ja = a["ability"]["name"]
        hidden = "（夢特性）" if a["is_hidden"] else ""
        abilities.append(f"{ab_ja}{hidden}")

    # 弱点・耐性
    weakness_map = get_type_weaknesses(types)
    weaknesses = [f"{TYPE_JA.get(t, t)}(x{v})" for t, v in weakness_map.items() if v > 1.0]
    resistances = [f"{TYPE_JA.get(t, t)}(x{v})" for t, v in weakness_map.items() if 0 < v < 1.0]
    immunities = [f"{TYPE_JA.get(t, t)}" for t, v in weakness_map.items() if v == 0.0]

    lines = [
        f"## {ja_name} (#{pokemon['id']})",
        f"タイプ: {' / '.join(types_ja)}",
        f"特性: {', '.join(abilities)}",
        "",
        "### 種族値",
    ]
    for stat_name, stat_val in stats.items():
        bar = _format_stat_bar(stat_val)
        lines.append(f"  {STAT_JA.get(stat_name, stat_name):5s} {stat_val:>3d} {bar}")
    lines.append(f"  {'合計':5s} {total:>3d}")
    lines.append("")

    if weaknesses:
        lines.append(f"弱点: {', '.join(weaknesses)}")
    if resistances:
        lines.append(f"耐性: {', '.join(resistances)}")
    if immunities:
        lines.append(f"無効: {', '.join(immunities)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: 育成構成提案
# ---------------------------------------------------------------------------

@mcp.tool()
async def recommend_build(
    name: str,
    role: str = "auto",
) -> str:
    """ポケモンの育成構成（性格・努力値配分）を提案します。

    Args:
        name: ポケモンの名前（例: garchomp, ガブリアス, 445）
        role: 役割（auto=自動判定, physical_attacker, special_attacker, physical_tank, special_tank, speed_attacker, balanced）
    """
    try:
        pokemon, species, ja_name = await _fetch_pokemon_full(name)
    except ValueError as e:
        return str(e)

    stats: dict[str, int] = {}
    for s in pokemon["stats"]:
        stats[s["stat"]["name"]] = s["base_stat"]

    types = [t["type"]["name"] for t in pokemon["types"]]

    # 役割の自動判定
    if role == "auto":
        role = _detect_role(stats)

    # 性格・努力値の提案
    nature_name, ev_spread = _suggest_nature_and_evs(stats, role)
    nature_ja = NATURE_JA.get(nature_name, nature_name)
    nature_info = NATURES[nature_name]

    lines = [
        f"## {ja_name} の育成提案",
        f"判定された役割: **{_role_ja(role)}**",
        "",
        "### 性格",
        f"  おすすめ: **{nature_ja}**（{nature_name}）",
    ]
    if nature_info["up"]:
        lines.append(f"    ↑ {STAT_JA.get(nature_info['up'], nature_info['up'])} / ↓ {STAT_JA.get(nature_info['down'], nature_info['down'])}")

    lines.append("")
    lines.append("### 努力値配分")
    for stat_key, ev_val in ev_spread.items():
        if ev_val > 0:
            lines.append(f"  {STAT_JA.get(stat_key, stat_key):5s}: {ev_val}")

    lines.append("")
    lines.append("### 育成のポイント")
    lines.extend(_build_tips(stats, types, role))

    return "\n".join(lines)


def _detect_role(stats: dict[str, int]) -> str:
    """種族値から最適な役割を自動判定"""
    atk = stats.get("attack", 0)
    spa = stats.get("special-attack", 0)
    df = stats.get("defense", 0)
    spd = stats.get("special-defense", 0)
    spd_stat = stats.get("speed", 0)
    hp = stats.get("hp", 0)

    bulk = hp + df + spd
    offense = max(atk, spa)

    if offense >= 100 and spd_stat >= 90:
        return "physical_attacker" if atk >= spa else "special_attacker"
    if offense >= 100 and spd_stat >= 80:
        return "speed_attacker"
    if bulk >= 280 and offense < 90:
        return "physical_tank" if df >= spd else "special_tank"
    if atk >= spa and atk >= 80:
        return "physical_attacker"
    if spa > atk and spa >= 80:
        return "special_attacker"
    return "balanced"


def _suggest_nature_and_evs(stats: dict[str, int], role: str) -> tuple[str, dict[str, int]]:
    """役割に基づいて性格と努力値配分を提案"""
    ev: dict[str, int] = {
        "hp": 0, "attack": 0, "defense": 0,
        "special-attack": 0, "special-defense": 0, "speed": 0,
    }

    if role == "physical_attacker":
        nature = "jolly" if stats.get("speed", 0) >= 80 else "adamant"
        ev["attack"] = 252
        ev["speed"] = 252
        ev["hp"] = 4

    elif role == "special_attacker":
        nature = "timid" if stats.get("speed", 0) >= 80 else "modest"
        ev["special-attack"] = 252
        ev["speed"] = 252
        ev["hp"] = 4

    elif role == "speed_attacker":
        if stats.get("attack", 0) >= stats.get("special-attack", 0):
            nature = "jolly"
            ev["attack"] = 252
        else:
            nature = "timid"
            ev["special-attack"] = 252
        ev["speed"] = 252
        ev["hp"] = 4

    elif role == "physical_tank":
        nature = "impish"
        ev["hp"] = 252
        ev["defense"] = 252
        ev["special-defense"] = 4

    elif role == "special_tank":
        nature = "calm"
        ev["hp"] = 252
        ev["special-defense"] = 252
        ev["defense"] = 4

    elif role == "balanced":
        nature = "adamant" if stats.get("attack", 0) >= stats.get("special-attack", 0) else "modest"
        ev["hp"] = 252
        if stats.get("attack", 0) >= stats.get("special-attack", 0):
            ev["attack"] = 252
        else:
            ev["special-attack"] = 252
        ev["speed"] = 4

    else:
        nature = "adamant"
        ev["attack"] = 252
        ev["hp"] = 252
        ev["speed"] = 4

    return nature, ev


def _role_ja(role: str) -> str:
    """役割名を日本語化"""
    mapping = {
        "physical_attacker": "物理アタッカー",
        "special_attacker": "特殊アタッカー",
        "speed_attacker": "高速アタッカー",
        "physical_tank": "物理受け",
        "special_tank": "特殊受け",
        "balanced": "バランス型",
    }
    return mapping.get(role, role)


def _build_tips(stats: dict[str, int], types: list[str], role: str) -> list[str]:
    """育成のアドバイスを生成"""
    tips = []
    spd = stats.get("speed", 0)
    atk = stats.get("attack", 0)
    spa = stats.get("special-attack", 0)

    if "attacker" in role:
        if spd >= 100:
            tips.append("- すばやさが高いため、上から殴れるアタッカーとして運用できます")
        elif spd >= 70:
            tips.append("- すばやさは中程度。きあいのタスキや先制技でカバーを検討")
        else:
            tips.append("- すばやさが低め。トリックルームとの相性が良いです")

    if "tank" in role:
        tips.append("- 回復技や状態異常技があれば優先的に採用しましょう")
        if stats.get("hp", 0) >= 100:
            tips.append("- HP種族値が高いため、たべのこしとの相性が良いです")

    if atk >= 100 and spa >= 100:
        tips.append("- 物理・特殊両方の種族値が高く、両刀型も選択肢に入ります")

    weakness_map = get_type_weaknesses(types)
    x4_weak = [TYPE_JA.get(t, t) for t, v in weakness_map.items() if v >= 4.0]
    if x4_weak:
        tips.append(f"- ⚠️ 4倍弱点: {', '.join(x4_weak)}（要注意）")

    if not tips:
        tips.append("- 種族値のバランスが良く、柔軟な育成が可能です")

    return tips


# ---------------------------------------------------------------------------
# Tool: パーティ分析
# ---------------------------------------------------------------------------

@mcp.tool()
async def analyze_team(pokemon_names: list[str]) -> str:
    """パーティ（最大6体）のタイプバランスを分析し、弱点と改善点を提案します。

    Args:
        pokemon_names: ポケモン名のリスト（例: ["garchomp", "rotom-wash", "ferrothorn"]）
    """
    if len(pokemon_names) == 0:
        return "ポケモンを1体以上指定してください。"
    if len(pokemon_names) > 6:
        return "パーティは最大6体です。"

    try:
        fetched = await _fetch_pokemon_full_batch(pokemon_names)
    except ValueError as e:
        return str(e)

    team_data = []
    for (pokemon, species, ja_name), pname in zip(fetched, pokemon_names):
        types = [t["type"]["name"] for t in pokemon["types"]]
        stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}
        team_data.append({"name": ja_name, "types": types, "stats": stats, "en_name": pname})

    lines = [f"## パーティ分析 ({len(team_data)}体)"]
    lines.append("")

    # メンバー一覧
    lines.append("### メンバー")
    for p in team_data:
        types_ja = " / ".join(TYPE_JA.get(t, t) for t in p["types"])
        total = sum(p["stats"].values())
        lines.append(f"- {p['name']} ({types_ja}) 合計種族値: {total}")
    lines.append("")

    # タイプカバー分析（攻撃面）
    lines.append("### 攻撃面タイプカバー")
    team_attack_types = set()
    for p in team_data:
        team_attack_types.update(p["types"])

    covered = []
    not_covered = []
    for target_type in ALL_TYPES:
        is_super_effective = False
        for atk_type in team_attack_types:
            from pokemon_data import TYPE_CHART
            if TYPE_CHART.get(atk_type, {}).get(target_type, 1.0) > 1.0:
                is_super_effective = True
                break
        if is_super_effective:
            covered.append(TYPE_JA.get(target_type, target_type))
        else:
            not_covered.append(TYPE_JA.get(target_type, target_type))

    lines.append(f"抜群を取れるタイプ ({len(covered)}/{len(ALL_TYPES)}): {', '.join(covered)}")
    if not_covered:
        lines.append(f"⚠️ カバーできていないタイプ: {', '.join(not_covered)}")
    lines.append("")

    # 防御面の弱点分析
    lines.append("### チーム弱点分析")
    type_weakness_count: dict[str, int] = {t: 0 for t in ALL_TYPES}
    type_resist_count: dict[str, int] = {t: 0 for t in ALL_TYPES}

    for p in team_data:
        wmap = get_type_weaknesses(p["types"])
        for t in ALL_TYPES:
            mult = wmap.get(t, 1.0)
            if mult > 1.0:
                type_weakness_count[t] += 1
            elif mult < 1.0:
                type_resist_count[t] += 1

    # 2体以上が弱点を持つタイプを警告
    danger_types = [(t, c) for t, c in type_weakness_count.items() if c >= 2]
    danger_types.sort(key=lambda x: x[1], reverse=True)
    if danger_types:
        lines.append("以下のタイプに複数メンバーが弱点を持っています:")
        for t, c in danger_types:
            lines.append(f"  ⚠️ {TYPE_JA.get(t, t)}: {c}体が弱点")
    else:
        lines.append("✅ 特定タイプに弱点が集中していません。バランス良好です。")
    lines.append("")

    # 耐性に優れたタイプ
    good_resist = [(t, c) for t, c in type_resist_count.items() if c >= 3]
    if good_resist:
        good_resist.sort(key=lambda x: x[1], reverse=True)
        lines.append("耐性に優れたタイプ:")
        for t, c in good_resist:
            lines.append(f"  ✅ {TYPE_JA.get(t, t)}: {c}体が半減以下")
        lines.append("")

    # ステータスバランス
    lines.append("### ステータスバランス")
    avg_stats: dict[str, float] = {}
    for stat_name in ["hp", "attack", "defense", "special-attack", "special-defense", "speed"]:
        avg = sum(p["stats"].get(stat_name, 0) for p in team_data) / len(team_data)
        avg_stats[stat_name] = avg
        lines.append(f"  {STAT_JA.get(stat_name, stat_name):5s} 平均: {avg:.0f}")

    fastest = max(team_data, key=lambda p: p["stats"].get("speed", 0))
    slowest = min(team_data, key=lambda p: p["stats"].get("speed", 0))
    lines.append(f"\n最速: {fastest['name']} (すばやさ {fastest['stats'].get('speed', 0)})")
    lines.append(f"最遅: {slowest['name']} (すばやさ {slowest['stats'].get('speed', 0)})")

    # 改善提案
    lines.append("")
    lines.append("### 改善提案")
    suggestions = _generate_team_suggestions(team_data, type_weakness_count, not_covered)
    lines.extend(suggestions)

    return "\n".join(lines)


def _generate_team_suggestions(
    team_data: list[dict],
    weakness_count: dict[str, int],
    uncovered_types: list[str],
) -> list[str]:
    """パーティ改善提案を生成"""
    suggestions = []

    # 弱点集中
    danger = [t for t, c in weakness_count.items() if c >= 3]
    if danger:
        danger_ja = [TYPE_JA.get(t, t) for t in danger]
        suggestions.append(f"- {', '.join(danger_ja)}タイプの技に3体以上が弱点です。耐性を持つポケモンの追加を検討してください。")

    # カバー不足
    if len(uncovered_types) >= 5:
        suggestions.append(f"- 攻撃面のタイプカバーが不足しています。多様なタイプの技を覚えるポケモンを検討してください。")

    # 全員が物理or特殊に偏っている
    physical_count = sum(1 for p in team_data if p["stats"].get("attack", 0) > p["stats"].get("special-attack", 0))
    if physical_count == len(team_data):
        suggestions.append("- 全員が物理寄りです。特殊アタッカーの追加を検討してください。")
    elif physical_count == 0:
        suggestions.append("- 全員が特殊寄りです。物理アタッカーの追加を検討してください。")

    # 速度帯
    speeds = [p["stats"].get("speed", 0) for p in team_data]
    if all(s < 70 for s in speeds):
        suggestions.append("- 全体的にすばやさが低めです。トリックルーム要員か高速ポケモンの追加を検討してください。")

    if not suggestions:
        suggestions.append("- 良くバランスの取れたパーティです！")

    return suggestions


# ---------------------------------------------------------------------------
# Tool: タイプ相性チェック
# ---------------------------------------------------------------------------

@mcp.tool()
async def check_type_matchup(
    attacking_type: str,
    defending_types: list[str],
) -> str:
    """タイプ相性の倍率を計算します。

    Args:
        attacking_type: 攻撃側のタイプ（例: fire）
        defending_types: 防御側のタイプのリスト（例: ["grass", "steel"]）
    """
    from pokemon_data import TYPE_CHART

    atk = attacking_type.lower().strip()
    defs = [d.lower().strip() for d in defending_types]

    if atk not in ALL_TYPES:
        # 日本語タイプ名からの逆引き
        ja_to_en = {v: k for k, v in TYPE_JA.items()}
        if atk in ja_to_en:
            atk = ja_to_en[atk]
        else:
            return f"「{attacking_type}」は有効なタイプ名ではありません。"

    resolved_defs = []
    ja_to_en = {v: k for k, v in TYPE_JA.items()}
    for d in defs:
        if d in ALL_TYPES:
            resolved_defs.append(d)
        elif d in ja_to_en:
            resolved_defs.append(ja_to_en[d])
        else:
            return f"「{d}」は有効なタイプ名ではありません。"

    multiplier = 1.0
    for d in resolved_defs:
        multiplier *= TYPE_CHART.get(atk, {}).get(d, 1.0)

    atk_ja = TYPE_JA.get(atk, atk)
    def_ja = " / ".join(TYPE_JA.get(d, d) for d in resolved_defs)

    if multiplier == 0:
        result = "効果なし"
    elif multiplier >= 4:
        result = f"x{multiplier} (4倍弱点！)"
    elif multiplier >= 2:
        result = f"x{multiplier} (効果抜群)"
    elif multiplier == 1:
        result = "x1.0 (等倍)"
    elif multiplier >= 0.5:
        result = f"x{multiplier} (いまひとつ)"
    else:
        result = f"x{multiplier} (いまひとつ)"

    return f"{atk_ja} → {def_ja}: {result}"


# ---------------------------------------------------------------------------
# Tool: 選出アドバイス（高速版）
# ---------------------------------------------------------------------------

def _matchup_score(
    my_types: list[str],
    opp_types: list[str],
) -> float:
    """自分のタイプ→相手のタイプへの攻撃相性スコアを計算"""
    from pokemon_data import TYPE_CHART
    best = 1.0
    for atk_t in my_types:
        mult = 1.0
        for def_t in opp_types:
            mult *= TYPE_CHART.get(atk_t, {}).get(def_t, 1.0)
        if mult > best:
            best = mult
    return best


def _defensive_score(
    my_types: list[str],
    opp_types: list[str],
) -> float:
    """相手のタイプ→自分のタイプへの被ダメ倍率（低い方が良い）"""
    from pokemon_data import TYPE_CHART
    worst = 1.0
    for atk_t in opp_types:
        mult = 1.0
        for def_t in my_types:
            mult *= TYPE_CHART.get(atk_t, {}).get(def_t, 1.0)
        if mult > worst:
            worst = mult
    return worst


@mcp.tool()
async def suggest_selection(
    my_team: list[str],
    opponent_team: list[str],
    battle_format: str = "singles",
) -> str:
    """相手パーティに対する選出（3体 or 4体）をタイプ相性ベースで即座に提案します。
    選出画面の制限時間内に使うための高速ツールです。

    Args:
        my_team: 自分のパーティのポケモン名リスト（6体）
        opponent_team: 相手のパーティのポケモン名リスト（3〜6体）
        battle_format: singles または doubles
    """
    # 両チーム並列取得
    try:
        my_fetched, opp_fetched = await asyncio.gather(
            _fetch_pokemon_full_batch(my_team),
            _fetch_pokemon_full_batch(opponent_team),
        )
    except ValueError as e:
        return str(e)

    my_data = []
    for (pokemon, species, ja_name), name in zip(my_fetched, my_team):
        types = [t["type"]["name"] for t in pokemon["types"]]
        stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}
        my_data.append({"name": ja_name, "en": name, "types": types, "stats": stats})

    opp_data = []
    for (pokemon, species, ja_name), name in zip(opp_fetched, opponent_team):
        types = [t["type"]["name"] for t in pokemon["types"]]
        stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}
        opp_data.append({"name": ja_name, "en": name, "types": types, "stats": stats})

    pick_count = 4 if battle_format == "doubles" else 3

    # 各自ポケモンのスコア計算: 攻撃相性 + 耐性
    scores: list[tuple[float, int]] = []
    for i, me in enumerate(my_data):
        atk_score = sum(_matchup_score(me["types"], opp["types"]) for opp in opp_data)
        def_penalty = sum(_defensive_score(me["types"], opp["types"]) for opp in opp_data)
        # 攻撃貢献 - 被ダメリスク
        total = atk_score - def_penalty * 0.5
        scores.append((total, i))

    scores.sort(reverse=True)

    # 上位から選出候補を構築（タイプ被りを考慮）
    selected_indices: list[int] = []
    selected_types: set[str] = set()
    for _, idx in scores:
        if len(selected_indices) >= pick_count:
            break
        me = my_data[idx]
        # 同じタイプが3体以上にならないよう調整
        type_overlap = sum(1 for t in me["types"] if t in selected_types)
        if type_overlap >= 2 and len(selected_indices) >= pick_count - 1:
            continue
        selected_indices.append(idx)
        selected_types.update(me["types"])

    # 足りない場合は残りから追加
    if len(selected_indices) < pick_count:
        for _, idx in scores:
            if idx not in selected_indices:
                selected_indices.append(idx)
            if len(selected_indices) >= pick_count:
                break

    # 相手の脅威分析（最も注意すべきポケモン）
    threats: list[tuple[float, int]] = []
    for j, opp in enumerate(opp_data):
        threat = 0.0
        for i in selected_indices:
            me = my_data[i]
            threat += _defensive_score(me["types"], opp["types"])
        threats.append((threat, j))
    threats.sort(reverse=True)

    # 出力
    lines = [f"## 選出提案 ({'ダブル' if battle_format == 'doubles' else 'シングル'})", ""]

    lines.append(f"### 選出 ({pick_count}体)")
    for rank, idx in enumerate(selected_indices, 1):
        me = my_data[idx]
        types_ja = "/".join(TYPE_JA.get(t, t) for t in me["types"])
        # 相手の誰に強いか
        good_vs = []
        for opp in opp_data:
            m = _matchup_score(me["types"], opp["types"])
            if m >= 2.0:
                good_vs.append(opp["name"])
        vs_str = f" → 有利: {', '.join(good_vs)}" if good_vs else ""
        lines.append(f"  {rank}. **{me['name']}** ({types_ja}){vs_str}")

    lines.append("")
    lines.append("### 相手の注意ポケモン")
    for threat_val, j in threats[:2]:
        opp = opp_data[j]
        types_ja = "/".join(TYPE_JA.get(t, t) for t in opp["types"])
        # 選出の中で誰が対処できるか
        counters = []
        for i in selected_indices:
            me = my_data[i]
            if _matchup_score(me["types"], opp["types"]) >= 2.0:
                counters.append(me["name"])
        counter_str = f" ← 対処: {', '.join(counters)}" if counters else " ← 対処手段が薄い！要注意"
        lines.append(f"  ⚠️ **{opp['name']}** ({types_ja}){counter_str}")

    # 初手提案
    lines.append("")
    if battle_format == "doubles":
        if len(selected_indices) >= 2:
            first = my_data[selected_indices[0]]["name"]
            second = my_data[selected_indices[1]]["name"]
            lines.append(f"### 初手: {first} + {second}")
    else:
        first = my_data[selected_indices[0]]["name"]
        lines.append(f"### 初手: {first}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: ポケモン条件検索（タイプ＋種族値）
# ---------------------------------------------------------------------------

@mcp.tool()
async def find_pokemon(
    type1: str,
    type2: str = "",
    min_speed: int = 0,
    min_attack: int = 0,
    min_sp_attack: int = 0,
    min_defense: int = 0,
    min_sp_defense: int = 0,
    min_hp: int = 0,
    min_total: int = 0,
) -> str:
    """タイプや種族値の条件でポケモンを検索します。構築の候補探しに最適です。

    Args:
        type1: タイプ1（例: みず, fire）
        type2: タイプ2（例: じめん, ground）※指定すると複合タイプ検索
        min_speed: すばやさ下限
        min_attack: こうげき下限
        min_sp_attack: とくこう下限
        min_defense: ぼうぎょ下限
        min_sp_defense: とくぼう下限
        min_hp: HP下限
        min_total: 合計種族値下限
    """
    ja_to_en = {v: k for k, v in TYPE_JA.items()}

    t1 = type1.lower().strip()
    if t1 in ja_to_en:
        t1 = ja_to_en[t1]
    if t1 not in ALL_TYPES:
        return f"「{type1}」は有効なタイプ名ではありません。"

    t2 = None
    if type2:
        t2 = type2.lower().strip()
        if t2 in ja_to_en:
            t2 = ja_to_en[t2]
        if t2 not in ALL_TYPES:
            return f"「{type2}」は有効なタイプ名ではありません。"

    # タイプ別ポケモン一覧取得
    if t2:
        names1, names2 = await asyncio.gather(
            pokeapi.get_type_pokemon_names(t1),
            pokeapi.get_type_pokemon_names(t2),
        )
        candidates = list(set(names1) & set(names2))
    else:
        candidates = await pokeapi.get_type_pokemon_names(t1)

    if not candidates:
        type_desc = f"{TYPE_JA.get(t1, t1)}/{TYPE_JA.get(t2, t2)}" if t2 else TYPE_JA.get(t1, t1)
        return f"{type_desc}タイプのポケモンは見つかりませんでした。"

    # ポケモンデータを並列取得
    async def _fetch_safe(name: str):
        try:
            return name, await pokeapi.get_pokemon(name)
        except Exception:
            return name, None

    fetched = await asyncio.gather(*(_fetch_safe(n) for n in candidates))

    # 種族値フィルタ
    matches = []
    for name, data in fetched:
        if data is None:
            continue
        stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
        total = sum(stats.values())
        if stats.get("speed", 0) < min_speed:
            continue
        if stats.get("attack", 0) < min_attack:
            continue
        if stats.get("special-attack", 0) < min_sp_attack:
            continue
        if stats.get("defense", 0) < min_defense:
            continue
        if stats.get("special-defense", 0) < min_sp_defense:
            continue
        if stats.get("hp", 0) < min_hp:
            continue
        if total < min_total:
            continue
        types = [t["type"]["name"] for t in data["types"]]
        matches.append({
            "name": name, "id": data["id"],
            "stats": stats, "total": total, "types": types,
            "species_name": data["species"]["name"],
        })

    if not matches:
        return "条件に一致するポケモンが見つかりませんでした。"

    matches.sort(key=lambda x: x["total"], reverse=True)

    # 日本語名取得（上位のみ）
    display_limit = 30
    show = matches[:display_limit]

    async def _ja_name(entry):
        try:
            species = await pokeapi.get_species(entry["species_name"])
            ja = await pokeapi.get_japanese_name(species)
            if entry["name"] != entry["species_name"]:
                suffix = entry["name"].replace(entry["species_name"], "").strip("-")
                if suffix:
                    ja = f"{ja}({suffix})"
            return ja
        except Exception:
            return entry["name"]

    ja_names = await asyncio.gather(*(_ja_name(m) for m in show))

    # 出力
    type_desc = TYPE_JA.get(t1, t1)
    if t2:
        type_desc += f" / {TYPE_JA.get(t2, t2)}"
    conds = []
    if min_speed: conds.append(f"素早≧{min_speed}")
    if min_attack: conds.append(f"攻撃≧{min_attack}")
    if min_sp_attack: conds.append(f"特攻≧{min_sp_attack}")
    if min_defense: conds.append(f"防御≧{min_defense}")
    if min_sp_defense: conds.append(f"特防≧{min_sp_defense}")
    if min_hp: conds.append(f"HP≧{min_hp}")
    if min_total: conds.append(f"合計≧{min_total}")
    cond_str = f"（{', '.join(conds)}）" if conds else ""

    lines = [f"## {type_desc}タイプ{cond_str} ({len(matches)}匹)", ""]
    lines.append("| # | 名前 | タイプ | HP | 攻撃 | 防御 | 特攻 | 特防 | 素早 | 合計 |")
    lines.append("|---|------|--------|--:|----:|----:|----:|----:|----:|----:|")
    for m, ja in zip(show, ja_names):
        s = m["stats"]
        t_ja = "/".join(TYPE_JA.get(t, t) for t in m["types"])
        lines.append(
            f"| {m['id']} | {ja} | {t_ja} "
            f"| {s.get('hp',0)} | {s.get('attack',0)} | {s.get('defense',0)} "
            f"| {s.get('special-attack',0)} | {s.get('special-defense',0)} | {s.get('speed',0)} "
            f"| {m['total']} |"
        )
    if len(matches) > display_limit:
        lines.append(f"\n*他{len(matches) - display_limit}匹は省略*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: 日本語名パターン検索
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_pokemon_by_name(
    prefix: str = "",
    suffix: str = "",
    contains: str = "",
) -> str:
    """日本語名のパターンでポケモンを検索します。前方一致・後方一致・部分一致を組み合わせられます。

    Args:
        prefix: 名前の先頭文字列（例: イ）
        suffix: 名前の末尾文字列（例: イ）
        contains: 名前に含まれる文字列（例: ブ）
    """
    if not prefix and not suffix and not contains:
        return "prefix, suffix, contains のいずれかを指定してください。"

    ja_map = await pokeapi.get_ja_name_map()

    # ja_map は小文字キー→IDだが、日本語カタカナは小文字変換しても同じなのでそのまま使える
    # ただし元の表記を復元するため species を引く必要がある
    # まずキーでフィルタリング
    matches: list[tuple[str, int]] = []
    for name_lower, pid in ja_map.items():
        name = name_lower  # 日本語カタカナは .lower() しても変わらない
        if prefix and not name.startswith(prefix.lower()):
            continue
        if suffix and not name.endswith(suffix.lower()):
            continue
        if contains and contains.lower() not in name:
            continue
        matches.append((name, pid))

    # ID順でソート
    matches.sort(key=lambda x: x[1])

    if not matches:
        cond = []
        if prefix:
            cond.append(f"「{prefix}」で始まる")
        if suffix:
            cond.append(f"「{suffix}」で終わる")
        if contains:
            cond.append(f"「{contains}」を含む")
        return f"{'、'.join(cond)}ポケモンは見つかりませんでした。"

    # ローマ字名を除外（カタカナ/ひらがなのみ残す）
    import re
    filtered = [(n, pid) for n, pid in matches if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', n)]
    if not filtered:
        filtered = matches

    lines = []
    cond = []
    if prefix:
        cond.append(f"「{prefix}」で始まる")
    if suffix:
        cond.append(f"「{suffix}」で終わる")
    if contains:
        cond.append(f"「{contains}」を含む")
    lines.append(f"## {'、'.join(cond)}ポケモン ({len(filtered)}匹)")
    lines.append("")

    for name, pid in filtered:
        lines.append(f"- #{pid:04d} {name}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

def main():
    mcp.run()


if __name__ == "__main__":
    main()
