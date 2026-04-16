#!/usr/bin/env python3
"""
佐賀バルーナーズ 個人スタッツ取得スクリプト
取得元: B.LEAGUE 公式サイト クラブ詳細ページ

使い方:
  pip3 install requests beautifulsoup4
  python3 scripts/scrape_player_stats.py              # stdout に JSON 出力
  python3 scripts/scrape_player_stats.py --save       # public/data/player_stats.json に保存
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import re
import sys

TEAM_ID = "1638"       # 佐賀バルーナーズ
SEASON_YEAR = "2025"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# クラブ詳細ページ（タブ番号は公式サイトに依存）
CLUB_URLS = [
    f"https://www.bleague.jp/club_detail/?TeamID={TEAM_ID}&tab=5",
    f"https://www.bleague.jp/club_detail/?TeamID={TEAM_ID}&tab=4",
    f"https://www.bleague.jp/club_detail/?TeamID={TEAM_ID}&tab=3",
]
# JSON API パターンも試みる
JSON_URLS = [
    f"https://www.bleague.jp/stats/?data_format=json&year={SEASON_YEAR}&club={TEAM_ID}",
    f"https://www.bleague.jp/stats/?data_format=json&year={SEASON_YEAR}&club={TEAM_ID}&tab=1",
]

# ポジション略称の正規化
POSITION_MAP = {
    "G": "G", "F": "F", "C": "C",
    "PG": "PG", "SG": "SG", "SF": "SF", "PF": "PF",
    "F/G": "F/G", "G/F": "G/F", "F/C": "F/C",
    "ガード": "G", "フォワード": "F", "センター": "C",
}


def safe_float(s: str) -> float:
    """文字列を安全に float に変換。失敗時は 0.0 を返す"""
    try:
        return float(s.replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def parse_stats_table(table) -> list:
    """<table> 要素から個人スタッツをパースする。
    B.LEAGUE club_detail ページの2行ヘッダー構造に対応。

    データ行の列構造（実測値）:
      [0]#  [1]名前  [2]シーズン  [3]大会  [4]ポジション  [5]試合数
      [6]MIN合計  [7]MINPG  [8]PPG  ...
      [23]RPG  [24]APG  [25]TOPG  [26]STPG  [27]BSPG
    """
    # 固定列インデックス（2行ヘッダーの#列オフセット込み）
    IDX_NUM  = 0
    IDX_NAME = 1
    IDX_PO   = 4
    IDX_G    = 5
    IDX_PPG  = 8
    IDX_RPG  = 23
    IDX_APG  = 24
    IDX_STPG = 26
    IDX_BSPG = 27
    MIN_COLS = IDX_BSPG + 1  # 最低限必要な列数

    rows = []
    all_rows = table.find_all("tr")

    # ヘッダー行数を検出（#または英略称PPGが含まれる行）
    data_start = 0
    for i, tr in enumerate(all_rows):
        texts = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
        if "PPG" in texts or "RPG" in texts:
            data_start = i + 1
            break

    for tr in all_rows[data_start:]:
        cells = tr.find_all(["th", "td"])
        texts = [c.get_text(strip=True) for c in cells]
        if len(texts) < MIN_COLS:
            continue
        # 最初のセルが背番号（数値）か空の場合のみ処理
        if texts[IDX_NUM] and not texts[IDX_NUM].isdigit():
            continue
        name = texts[IDX_NAME]
        if not name or name in ("SEASON", "TYPE", "PLAYER"):
            continue
        try:
            rows.append({
                "number":   int(texts[IDX_NUM]) if texts[IDX_NUM].isdigit() else 0,
                "name":     name,
                "position": POSITION_MAP.get(texts[IDX_PO], texts[IDX_PO]),
                "games":    int(safe_float(texts[IDX_G])),
                "points":   safe_float(texts[IDX_PPG]),
                "rebounds": safe_float(texts[IDX_RPG]),
                "assists":  safe_float(texts[IDX_APG]),
                "steals":   safe_float(texts[IDX_STPG]),
                "blocks":   safe_float(texts[IDX_BSPG]),
            })
        except (IndexError, ValueError):
            continue

    return rows


def try_json_api():
    """JSON API からスタッツ取得を試みる"""
    for url in JSON_URLS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            ct = r.headers.get("content-type", "")
            print(f"  URL: {r.url}", flush=True)
            print(f"  Status: {r.status_code} / Content-Type: {ct}", flush=True)
            if "json" in ct:
                data = r.json()
                print(f"  JSON キー: {list(data.keys()) if isinstance(data, dict) else type(data)}", flush=True)
                # topics 形式の場合 HTML をパース
                if isinstance(data, dict) and "topics" in data:
                    players = []
                    for html_block in data["topics"]:
                        soup = BeautifulSoup(html_block, "html.parser")
                        for table in soup.find_all("table"):
                            players.extend(parse_stats_table(table))
                    if players:
                        return players
        except Exception as e:
            print(f"  エラー: {e}", flush=True)
    return None


def try_html_scrape() -> list:
    """クラブ詳細ページの HTML からスタッツ取得を試みる"""
    for url in CLUB_URLS:
        try:
            print(f"  URL: {url}", flush=True)
            r = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.find("title")
            print(f"  Title: {title.get_text() if title else 'N/A'}", flush=True)

            # __NEXT_DATA__ を確認
            next_script = soup.find("script", {"id": "__NEXT_DATA__"})
            if next_script and next_script.string:
                next_data = json.loads(next_script.string)
                # 選手データを再帰的に探す
                players = find_players_in_json(next_data)
                if players:
                    print(f"  → __NEXT_DATA__ から {len(players)} 人取得", flush=True)
                    return players

            # HTML テーブルをパース
            tables = soup.find_all("table")
            print(f"  table 要素数: {len(tables)}", flush=True)
            for table in tables:
                players = parse_stats_table(table)
                if len(players) >= 3:   # 3人以上取れれば成功とみなす
                    print(f"  → HTML table から {len(players)} 人取得", flush=True)
                    return players
        except Exception as e:
            print(f"  エラー: {e}", flush=True)
    return []


def find_players_in_json(obj, depth: int = 0) -> list:
    """JSON オブジェクトから選手スタッツ配列を再帰的に探す"""
    if depth > 6:
        return []
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        keys = set(obj[0].keys())
        if any(k in keys for k in ("name", "playerName", "points", "pts", "rebounds")):
            return normalize_json_players(obj)
    if isinstance(obj, dict):
        for v in obj.values():
            result = find_players_in_json(v, depth + 1)
            if result:
                return result
    return []


def normalize_json_players(raw: list) -> list:
    """JSON 形式の選手データを統一フォーマットに変換"""
    result = []
    for p in raw:
        player = {
            "name":     p.get("name") or p.get("playerName") or p.get("選手名") or "",
            "number":   int(p.get("number") or p.get("shirtNumber") or p.get("背番号") or 0),
            "position": p.get("position") or p.get("pos") or p.get("ポジション") or "",
            "games":    int(p.get("games") or p.get("gp") or p.get("試合数") or 0),
            "points":   safe_float(str(p.get("points") or p.get("pts") or p.get("得点") or 0)),
            "rebounds": safe_float(str(p.get("rebounds") or p.get("reb") or p.get("リバウンド") or 0)),
            "assists":  safe_float(str(p.get("assists") or p.get("ast") or p.get("アシスト") or 0)),
            "steals":   safe_float(str(p.get("steals") or p.get("stl") or p.get("スチール") or 0)),
            "blocks":   safe_float(str(p.get("blocks") or p.get("blk") or p.get("ブロック") or 0)),
        }
        if player["name"]:
            result.append(player)
    return result


def fetch_player_stats() -> list:
    """個人スタッツを取得する（複数手段でフォールバック）"""

    print("[1/2] JSON API を試みます...", flush=True)
    players = try_json_api()
    if players:
        return players

    print("[2/2] HTML スクレイピングを試みます...", flush=True)
    players = try_html_scrape()
    if players:
        return players

    print("  WARNING: スタッツデータを取得できませんでした", flush=True)
    print("  B.LEAGUE のページは JS レンダリングのため、手動更新が必要な場合があります", flush=True)
    return []


if __name__ == "__main__":
    save_to_file = "--save" in sys.argv

    players = fetch_player_stats()
    # 得点平均の降順でソート
    players.sort(key=lambda p: p.get("points", 0), reverse=True)
    print(f"\n取得選手数: {len(players)}", flush=True)

    output = {
        "players": players,
        "updatedAt": datetime.now().isoformat(),
    }
    json_str = json.dumps(output, ensure_ascii=False, indent=2)

    if save_to_file:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "..", "public", "data", "player_stats.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"保存: {os.path.abspath(output_path)}", flush=True)
    else:
        print(json_str)
