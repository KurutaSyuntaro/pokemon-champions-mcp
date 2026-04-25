# ポケモンチャンピオンズ育成支援 MCP サーバー

ポケモンチャンピオンズのバトル育成を支援する MCP (Model Context Protocol) サーバーです。  
PokeAPI からデータを取得し、育成構成の提案やパーティ分析を行います。

## 機能（ツール）

| ツール | 説明 |
|--------|------|
| `search_pokemon` | ポケモンの種族値・タイプ・特性を検索 |
| `recommend_build` | 性格・努力値配分の育成提案 |
| `analyze_team` | パーティのタイプバランス分析・改善提案 |
| `check_type_matchup` | タイプ相性の倍率計算 |
| `suggest_selection` | 相手パーティに対する選出提案（シングル/ダブル対応） |
| `find_pokemon` | タイプ・種族値条件でポケモンを検索（構築の候補探しに） |
| `search_pokemon_by_name` | 日本語名のパターン検索（前方/後方/部分一致） |

## セットアップ

### 前提条件

- Python 3.11 以上
- uv（推奨）または pip

### インストール

```bash
cd mcp
uv sync
```

## 使い方

### VS Code (GitHub Copilot) で使う

`.vscode/mcp.json` に以下を追加:

```json
{
  "servers": {
    "pokemon-champions": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "<このフォルダの絶対パス>", "python", "server.py"]
    }
  }
}
```

### Claude Desktop で使う

`claude_desktop_config.json` に以下を追加:

```json
{
  "mcpServers": {
    "pokemon-champions": {
      "command": "uv",
      "args": ["run", "--directory", "<このフォルダの絶対パス>", "python", "server.py"]
    }
  }
}
```

## 使用例

- 「ガブリアスの種族値を教えて」→ `search_pokemon("garchomp")`
- 「ミミッキュの育成構成を提案して」→ `recommend_build("mimikyu")`
- 「ガブリアス、ロトム、ナットレイのパーティ分析」→ `analyze_team(["garchomp", "rotom-wash", "ferrothorn"])`
- 「ほのお技でくさ/はがねに攻撃したときの倍率は？」→ `check_type_matchup("fire", ["grass", "steel"])`
- 「相手パーティに対する選出を考えて」→ `suggest_selection(my_team, opponent_team)`
- 「すばやさ100以上のみず/じめんタイプは？」→ `find_pokemon("みず", type2="じめん", min_speed=100)`
- 「イで始まりイで終わるポケモンは？」→ `search_pokemon_by_name(prefix="イ", suffix="イ")`

## データソース

- [PokeAPI](https://pokeapi.co/) — ポケモンのステータス、タイプ、特性データ

> ⚠️ ポケモンチャンピオンズ固有のゲーム内仕様（バトルルール等）は本家ゲームとは異なる場合があります。
> 種族値・タイプ相性などの基礎データは共通です。

## Author

[@kuruta_syuntaro](https://x.com/kuruta_syuntaro)

---

# Pokémon Champions Training Support MCP Server

An MCP (Model Context Protocol) server that assists with battle training in Pokémon Champions.  
It fetches data from PokeAPI and provides training build suggestions and party analysis.

## Features (Tools)

| Tool | Description |
|------|-------------|
| `search_pokemon` | Search base stats, types, and abilities of a Pokémon |
| `recommend_build` | Suggest nature and EV spreads for training builds |
| `analyze_team` | Analyze type balance and suggest improvements for a party |
| `check_type_matchup` | Calculate type matchup multipliers |
| `suggest_selection` | Suggest team selection against opponent's party (singles/doubles) |
| `find_pokemon` | Search Pokémon by type and base stat conditions |
| `search_pokemon_by_name` | Search Pokémon by Japanese name pattern (prefix/suffix/contains) |

## Setup

### Prerequisites

- Python 3.11+
- uv (recommended) or pip

### Installation

```bash
cd mcp
uv sync
```

## Usage

### With VS Code (GitHub Copilot)

Add the following to `.vscode/mcp.json`:

```json
{
  "servers": {
    "pokemon-champions": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "<absolute path to this folder>", "python", "server.py"]
    }
  }
}
```

### With Claude Desktop

Add the following to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pokemon-champions": {
      "command": "uv",
      "args": ["run", "--directory", "<absolute path to this folder>", "python", "server.py"]
    }
  }
}
```

## Examples

- "Show me Garchomp's base stats" → `search_pokemon("garchomp")`
- "Suggest a build for Mimikyu" → `recommend_build("mimikyu")`
- "Analyze a team of Garchomp, Rotom-Wash, Ferrothorn" → `analyze_team(["garchomp", "rotom-wash", "ferrothorn"])`
- "What's the multiplier for a Fire move against Grass/Steel?" → `check_type_matchup("fire", ["grass", "steel"])`
- "Suggest picks against opponent's team" → `suggest_selection(my_team, opponent_team)`
- "Water/Ground types with 100+ speed?" → `find_pokemon("water", type2="ground", min_speed=100)`
- "Pokémon names starting with イ and ending with イ?" → `search_pokemon_by_name(prefix="イ", suffix="イ")`

## Data Source

- [PokeAPI](https://pokeapi.co/) — Pokémon stats, types, and ability data

> ⚠️ Game-specific mechanics in Pokémon Champions (battle rules, etc.) may differ from the main series games.
> Base stats and type matchups are shared.

## Author

[@kuruta_syuntaro](https://x.com/kuruta_syuntaro)
