#!/usr/bin/env python3
"""
B.LEAGUE B1 全地区 順位表スクレイパー
取得元: https://www.bleague.jp/standings/

使い方:
  pip3 install requests beautifulsoup4
  python3 scripts/scrape_standings.py              # stdout に JSON 出力
  python3 scripts/scrape_standings.py --save       # public/data/standings.json に保存

注意:
  B.LEAGUE のページは JavaScript レンダリングのため、
  サーバーサイドの JSON API が利用できない場合は手動更新が必要です。
  スクリプト実行時に [DEBUG] 行を確認してください。
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import sys
import re

SEASON_YEAR = "2025"
BASE_URL = "https://www.bleague.jp/standings/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# チーム名正規化マスタ（略称・表記ゆれ → 正式名）
TEAM_MASTER = {
    # 東地区
    "北海道ゲームチェンジャーズ": "北海道ゲームチェンジャーズ",
    "レバンガ北海道": "北海道ゲームチェンジャーズ",
    "北海道": "北海道ゲームチェンジャーズ",
    "秋田ノーザンハピネッツ": "秋田ノーザンハピネッツ",
    "秋田": "秋田ノーザンハピネッツ",
    "仙台89ers": "仙台89ers",
    "仙台": "仙台89ers",
    "茨城ロボッツ": "茨城ロボッツ",
    "茨城": "茨城ロボッツ",
    "宇都宮ブレックス": "宇都宮ブレックス",
    "宇都宮": "宇都宮ブレックス",
    "千葉ジェッツ": "千葉ジェッツ",
    "千葉": "千葉ジェッツ",
    "アルバルク東京": "アルバルク東京",
    "東京": "アルバルク東京",
    "川崎ブレイブサンダース": "川崎ブレイブサンダース",
    "川崎": "川崎ブレイブサンダース",
    # 中地区
    "新潟アルビレックスBB": "新潟アルビレックスBB",
    "新潟": "新潟アルビレックスBB",
    "サンロッカーズ渋谷": "サンロッカーズ渋谷",
    "渋谷": "サンロッカーズ渋谷",
    "横浜DeNAビーコルセアーズ": "横浜DeNAビーコルセアーズ",
    "横浜": "横浜DeNAビーコルセアーズ",
    "三遠ネオフェニックス": "三遠ネオフェニックス",
    "三遠": "三遠ネオフェニックス",
    "名古屋ダイヤモンドドルフィンズ": "名古屋ダイヤモンドドルフィンズ",
    "名古屋D": "名古屋ダイヤモンドドルフィンズ",
    "FE名古屋": "FE名古屋",
    "シーホース三河": "シーホース三河",
    "三河シーホース": "シーホース三河",
    "三河": "シーホース三河",
    "滋賀レイクス": "滋賀レイクス",
    "滋賀": "滋賀レイクス",
    # 西地区
    "京都ハンナリーズ": "京都ハンナリーズ",
    "京都": "京都ハンナリーズ",
    "大阪エヴェッサ": "大阪エヴェッサ",
    "大阪": "大阪エヴェッサ",
    "島根スサノオマジック": "島根スサノオマジック",
    "島根": "島根スサノオマジック",
    "広島ドラゴンフライズ": "広島ドラゴンフライズ",
    "広島": "広島ドラゴンフライズ",
    "長崎ヴェルカ": "長崎ヴェルカ",
    "長崎": "長崎ヴェルカ",
    "佐賀バルーナーズ": "佐賀バルーナーズ",
    "佐賀": "佐賀バルーナーズ",
    "琉球ゴールデンキングス": "琉球ゴールデンキングス",
    "琉球": "琉球ゴールデンキングス",
    "福岡ライジングゼファー": "福岡ライジングゼファー",
    "福岡": "福岡ライジングゼファー",
}

DIVISION_LABELS = {
    "east":    ["東地区", "East"],
    "central": ["中地区", "Central"],
    "west":    ["西地区", "West"],
}


def normalize_team(name: str) -> str:
    return TEAM_MASTER.get(name, name)


def convert_streak(text: str) -> str:
    """W4 → 4連勝, L2 → 2連敗 に変換"""
    text = text.strip()
    m = re.match(r"W(\d+)$", text)
    if m:
        return f"{m.group(1)}連勝"
    m = re.match(r"L(\d+)$", text)
    if m:
        return f"{m.group(1)}連敗"
    if re.match(r"\d+連[勝敗]", text):
        return text
    return ""


def detect_division(text: str):
    """テキストから地区名を検出する"""
    for div, labels in DIVISION_LABELS.items():
        if any(label in text for label in labels):
            return div
    return None


def parse_standings_table(table) -> list:
    """table 要素から順位データをパースする"""
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells or tr.find("th"):
            continue
        texts = [c.get_text(strip=True) for c in cells]
        if not texts or not texts[0].isdigit():
            continue

        try:
            rank = int(texts[0])

            # チーム名: span.sp-dn が正式名（略称は span.pc-tab-dn）
            team_cell = cells[1] if len(cells) > 1 else None
            team = ""
            if team_cell:
                name_span = team_cell.select_one("span.sp-dn")
                if name_span:
                    team = name_span.get_text(strip=True)
                else:
                    # フォールバック: テキスト全体を TEAM_MASTER で正規化
                    team = normalize_team(texts[1])

            # 固定列インデックス: rank(0), team(1), win(2), loss(3), ...streak(12)
            win  = int(texts[2]) if len(texts) > 2  and texts[2].isdigit()  else 0
            loss = int(texts[3]) if len(texts) > 3  and texts[3].isdigit()  else 0
            streak = convert_streak(texts[12]) if len(texts) > 12 else ""

            if team:
                rows.append({"rank": rank, "team": team, "win": win, "loss": loss, "streak": streak})
        except (ValueError, IndexError):
            continue
    return rows


def parse_standings_from_html(html: str) -> dict:
    """HTML から全地区の順位データをパースする"""
    soup = BeautifulSoup(html, "html.parser")
    result = {"east": [], "central": [], "west": []}
    seen_table_ids = set()

    # 見出し → テーブルのマッピング（同一テーブルは1回だけ処理）
    current_div = None
    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name in ("h2", "h3", "h4"):
            detected = detect_division(el.get_text())
            if detected:
                current_div = detected
        elif el.name == "table" and current_div:
            table_id = id(el)
            if table_id in seen_table_ids:
                continue
            seen_table_ids.add(table_id)
            rows = parse_standings_table(el)
            if rows:
                result[current_div].extend(rows)
                current_div = None  # 1見出し1テーブル対応

    return result


def parse_standings_from_next_data(html: str):
    """Next.js の __NEXT_DATA__ 埋め込み JSON からデータを取得する"""
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script or not script.string:
        return None

    try:
        next_data = json.loads(script.string)
    except json.JSONDecodeError:
        return None

    print("[DEBUG] __NEXT_DATA__ が見つかりました", flush=True)
    # B.LEAGUE の Next.js ページ構造に合わせてデータを探す
    # props.pageProps 以下に standings データがある可能性が高い
    props = next_data.get("props", {}).get("pageProps", {})

    # standings キーを再帰的に探す
    def find_standings(obj, depth=0):
        if depth > 5:
            return None
        if isinstance(obj, dict):
            for key in obj:
                if "standing" in key.lower() or "ranking" in key.lower():
                    print(f"[DEBUG] キー '{key}' を検出: {type(obj[key])}", flush=True)
                result = find_standings(obj[key], depth + 1)
                if result:
                    return result
        elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if "rank" in obj[0] or "win" in obj[0] or "wins" in obj[0]:
                return obj
        return None

    raw = find_standings(props)
    if raw:
        print(f"[DEBUG] standings データ候補: {len(raw)} 件", flush=True)

    return None  # 構造が分かり次第、ここを実装


def fetch_standings() -> dict:
    result = {"east": [], "central": [], "west": []}

    # --- 試行1: JSON API（schedule と同じパターン） ---
    print("[1/3] JSON API を試みます...", flush=True)
    for params in [
        {"data_format": "json", "year": SEASON_YEAR},
        {"data_format": "json", "year": SEASON_YEAR, "tab": "1"},
    ]:
        try:
            r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            content_type = r.headers.get("content-type", "")
            print(f"  URL: {r.url}", flush=True)
            print(f"  Status: {r.status_code} / Content-Type: {content_type}", flush=True)
            if "json" in content_type:
                data = r.json()
                print(f"  JSON キー: {list(data.keys()) if isinstance(data, dict) else type(data)}", flush=True)
                # topics 形式（HTML 文字列配列）の場合
                if isinstance(data, dict) and "topics" in data:
                    for html_block in data["topics"]:
                        parsed = parse_standings_from_html(html_block)
                        for div in ("east", "central", "west"):
                            result[div].extend(parsed.get(div, []))
                    if any(result.values()):
                        print("  → topics HTML から取得成功", flush=True)
                        return result
                break
        except Exception as e:
            print(f"  エラー: {e}", flush=True)

    # --- 試行2: __NEXT_DATA__ 埋め込みデータ ---
    print("[2/3] __NEXT_DATA__ を確認します...", flush=True)
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        next_result = parse_standings_from_next_data(r.text)
        if next_result:
            return next_result
    except Exception as e:
        print(f"  エラー: {e}", flush=True)

    # --- 試行3: HTML テーブルのパース ---
    print("[3/3] HTML テーブルをパースします...", flush=True)
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        print(f"  table 要素数: {len(tables)}", flush=True)

        parsed = parse_standings_from_html(r.text)
        for div in ("east", "central", "west"):
            result[div].extend(parsed.get(div, []))

        if any(result.values()):
            print("  → HTML テーブルから取得成功", flush=True)
            return result
        else:
            print("  WARNING: HTML から順位データを取得できませんでした", flush=True)
            print("  B.LEAGUE のページは JS レンダリングのため、手動更新が必要な場合があります", flush=True)
            print("  → lib/data.ts の STATIC_STANDINGS を直接編集してください", flush=True)
    except Exception as e:
        print(f"  エラー: {e}", flush=True)

    return result


if __name__ == "__main__":
    save_to_file = "--save" in sys.argv

    standings = fetch_standings()
    standings["updatedAt"] = datetime.now().isoformat()

    total = sum(len(v) for v in standings.values() if isinstance(v, list))
    print(f"\n取得結果: 東{len(standings['east'])}チーム / 中{len(standings['central'])}チーム / 西{len(standings['west'])}チーム", flush=True)

    json_str = json.dumps(standings, ensure_ascii=False, indent=2)

    if save_to_file:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "..", "public", "data", "standings.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"保存: {os.path.abspath(output_path)}", flush=True)
    else:
        print(json_str)
