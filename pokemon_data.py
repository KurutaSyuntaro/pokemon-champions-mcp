"""ポケモンのタイプ相性・性格データ"""

# タイプ相性チャート: TYPE_CHART[攻撃タイプ][防御タイプ] = 倍率
TYPE_CHART: dict[str, dict[str, float]] = {
    "normal":   {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire":     {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0, "rock": 0.5, "dragon": 0.5, "steel": 2.0},
    "water":    {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0, "rock": 2.0, "dragon": 0.5},
    "electric": {"water": 2.0, "electric": 0.5, "grass": 0.5, "ground": 0.0, "flying": 2.0, "dragon": 0.5},
    "grass":    {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5, "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0, "dragon": 0.5, "steel": 0.5},
    "ice":      {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5, "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5},
    "fighting": {"normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0, "dark": 2.0, "steel": 2.0, "fairy": 0.5},
    "poison":   {"grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0.0, "fairy": 2.0},
    "ground":   {"fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0, "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0},
    "flying":   {"electric": 0.5, "grass": 2.0, "fighting": 2.0, "bug": 2.0, "rock": 0.5, "steel": 0.5},
    "psychic":  {"fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0.0, "steel": 0.5},
    "bug":      {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0, "steel": 0.5, "fairy": 0.5},
    "rock":     {"fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5, "flying": 2.0, "bug": 2.0, "steel": 0.5},
    "ghost":    {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
    "dragon":   {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
    "dark":     {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5, "fairy": 0.5},
    "steel":    {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0, "rock": 2.0, "steel": 0.5, "fairy": 2.0},
    "fairy":    {"fire": 0.5, "poison": 0.5, "fighting": 2.0, "dragon": 2.0, "dark": 2.0, "steel": 0.5},
}

ALL_TYPES = list(TYPE_CHART.keys())

# 防御側のタイプ弱点・耐性・無効
TYPE_DEFENSE: dict[str, dict[str, list[str]]] = {
    "normal":   {"weak": ["fighting"], "resist": [], "immune": ["ghost"]},
    "fire":     {"weak": ["water", "ground", "rock"], "resist": ["fire", "grass", "ice", "bug", "steel", "fairy"], "immune": []},
    "water":    {"weak": ["electric", "grass"], "resist": ["fire", "water", "ice", "steel"], "immune": []},
    "electric": {"weak": ["ground"], "resist": ["electric", "flying", "steel"], "immune": []},
    "grass":    {"weak": ["fire", "ice", "poison", "flying", "bug"], "resist": ["water", "electric", "grass", "ground"], "immune": []},
    "ice":      {"weak": ["fire", "fighting", "rock", "steel"], "resist": ["ice"], "immune": []},
    "fighting": {"weak": ["flying", "psychic", "fairy"], "resist": ["bug", "rock", "dark"], "immune": []},
    "poison":   {"weak": ["ground", "psychic"], "resist": ["fighting", "poison", "bug", "grass", "fairy"], "immune": []},
    "ground":   {"weak": ["water", "grass", "ice"], "resist": ["poison", "rock"], "immune": ["electric"]},
    "flying":   {"weak": ["electric", "ice", "rock"], "resist": ["fighting", "bug", "grass"], "immune": ["ground"]},
    "psychic":  {"weak": ["bug", "ghost", "dark"], "resist": ["fighting", "psychic"], "immune": []},
    "bug":      {"weak": ["fire", "flying", "rock"], "resist": ["fighting", "ground", "grass"], "immune": []},
    "rock":     {"weak": ["water", "grass", "fighting", "ground", "steel"], "resist": ["normal", "fire", "poison", "flying"], "immune": []},
    "ghost":    {"weak": ["ghost", "dark"], "resist": ["poison", "bug"], "immune": ["normal", "fighting"]},
    "dragon":   {"weak": ["ice", "dragon", "fairy"], "resist": ["fire", "water", "electric", "grass"], "immune": []},
    "dark":     {"weak": ["fighting", "bug", "fairy"], "resist": ["ghost", "dark"], "immune": ["psychic"]},
    "steel":    {"weak": ["fire", "fighting", "ground"], "resist": ["normal", "grass", "ice", "flying", "psychic", "bug", "rock", "dragon", "steel", "fairy"], "immune": ["poison"]},
    "fairy":    {"weak": ["poison", "steel"], "resist": ["fighting", "bug", "dark"], "immune": ["dragon"]},
}

# 性格データ: NATURES[英語名] = {"up": 上昇ステータス, "down": 下降ステータス}
NATURES: dict[str, dict[str, str | None]] = {
    "hardy":   {"up": None, "down": None},
    "lonely":  {"up": "attack", "down": "defense"},
    "brave":   {"up": "attack", "down": "speed"},
    "adamant": {"up": "attack", "down": "special-attack"},
    "naughty": {"up": "attack", "down": "special-defense"},
    "bold":    {"up": "defense", "down": "attack"},
    "relaxed": {"up": "defense", "down": "speed"},
    "impish":  {"up": "defense", "down": "special-attack"},
    "lax":     {"up": "defense", "down": "special-defense"},
    "timid":   {"up": "speed", "down": "attack"},
    "hasty":   {"up": "speed", "down": "defense"},
    "jolly":   {"up": "speed", "down": "special-attack"},
    "naive":   {"up": "speed", "down": "special-defense"},
    "modest":  {"up": "special-attack", "down": "attack"},
    "mild":    {"up": "special-attack", "down": "defense"},
    "quiet":   {"up": "special-attack", "down": "speed"},
    "rash":    {"up": "special-attack", "down": "special-defense"},
    "calm":    {"up": "special-defense", "down": "attack"},
    "gentle":  {"up": "special-defense", "down": "defense"},
    "sassy":   {"up": "special-defense", "down": "speed"},
    "careful": {"up": "special-defense", "down": "special-attack"},
    "quirky":  {"up": None, "down": None},
    "serious": {"up": None, "down": None},
    "bashful": {"up": None, "down": None},
    "docile":  {"up": None, "down": None},
}

# 性格の日本語名
NATURE_JA: dict[str, str] = {
    "hardy": "がんばりや", "lonely": "さみしがり", "brave": "ゆうかん",
    "adamant": "いじっぱり", "naughty": "やんちゃ", "bold": "ずぶとい",
    "relaxed": "のんき", "impish": "わんぱく", "lax": "のうてんき",
    "timid": "おくびょう", "hasty": "せっかち", "jolly": "ようき",
    "naive": "むじゃき", "modest": "ひかえめ", "mild": "おっとり",
    "quiet": "れいせい", "rash": "うっかりや", "calm": "おだやか",
    "gentle": "おとなしい", "sassy": "なまいき", "careful": "しんちょう",
    "quirky": "きまぐれ", "serious": "まじめ", "bashful": "てれや",
    "docile": "すなお",
}

# ステータス名の日本語
STAT_JA: dict[str, str] = {
    "hp": "HP",
    "attack": "こうげき",
    "defense": "ぼうぎょ",
    "special-attack": "とくこう",
    "special-defense": "とくぼう",
    "speed": "すばやさ",
}

# タイプ名の日本語
TYPE_JA: dict[str, str] = {
    "normal": "ノーマル", "fire": "ほのお", "water": "みず",
    "electric": "でんき", "grass": "くさ", "ice": "こおり",
    "fighting": "かくとう", "poison": "どく", "ground": "じめん",
    "flying": "ひこう", "psychic": "エスパー", "bug": "むし",
    "rock": "いわ", "ghost": "ゴースト", "dragon": "ドラゴン",
    "dark": "あく", "steel": "はがね", "fairy": "フェアリー",
}


def calc_type_effectiveness(attacking_types: list[str], defending_types: list[str]) -> float:
    """攻撃タイプ群 → 防御タイプ群の最大倍率を計算"""
    best = 0.0
    for atk in attacking_types:
        multiplier = 1.0
        for dfn in defending_types:
            multiplier *= TYPE_CHART.get(atk, {}).get(dfn, 1.0)
        best = max(best, multiplier)
    return best


def get_type_weaknesses(types: list[str]) -> dict[str, float]:
    """タイプの組み合わせに対する各攻撃タイプの倍率を計算"""
    result: dict[str, float] = {}
    for atk_type in ALL_TYPES:
        multiplier = 1.0
        for def_type in types:
            multiplier *= TYPE_CHART.get(atk_type, {}).get(def_type, 1.0)
        if multiplier != 1.0:
            result[atk_type] = multiplier
    return result
