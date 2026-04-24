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

## データソース

- [PokeAPI](https://pokeapi.co/) — ポケモンのステータス、タイプ、特性データ

> ⚠️ ポケモンチャンピオンズ固有のゲーム内仕様（バトルルール等）は本家ゲームとは異なる場合があります。
> 種族値・タイプ相性などの基礎データは共通です。
