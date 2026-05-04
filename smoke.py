"""スモークテスト: 新規2ツールの E2E 動作確認"""
import asyncio
import server


async def main() -> None:
    print("[1] search_pokemon_by_move('flamethrower', limit=3)")
    out1 = await server.search_pokemon_by_move("flamethrower", limit=3)
    print(out1[:500])
    assert "## " in out1, "見出しなし"
    assert "習得ポケモン" in out1, "習得ポケモンセクションなし"
    print("=> OK\n")

    print("[2] search_moves_by_pokemon('pikachu', limit=5)")
    out2 = await server.search_moves_by_pokemon("pikachu", limit=5)
    print(out2[:500])
    assert "## " in out2, "見出しなし"
    assert "技（習得方法付き）" in out2, "技セクションなし"
    print("=> OK\n")

    print("[3] search_pokemon_by_move('かえんほうしゃ', limit=2) [日本語]")
    out3 = await server.search_pokemon_by_move("かえんほうしゃ", limit=2)
    print(out3[:300])
    assert "## " in out3, "見出しなし"
    print("=> OK\n")

    print("[4] search_moves_by_pokemon('ピカチュウ', limit=5) [日本語]")
    out4 = await server.search_moves_by_pokemon("ピカチュウ", limit=5)
    print(out4[:300])
    assert "## " in out4, "見出しなし"
    print("=> OK\n")

    print("=== ALL SMOKE TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
