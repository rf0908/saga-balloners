#!/usr/bin/env python3
"""
佐賀バルーナーズ スケジュール取得スクリプト
取得元: B.LEAGUE 公式サイト（データ形式: JSON）

使い方:
  pip3 install requests beautifulsoup4
  python3 scripts/fetch_schedule.py              # stdout に JSON 出力
  python3 scripts/fetch_schedule.py --save       # public/data/games.json に保存
"""

import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import json
import os
import sys

# === 設定 ===
CLUB_ID = "1638"          # 佐賀バルーナーズのクラブID
TEAM_NAME = "佐賀"        # チーム名（HTML内での表記）
SEASON_YEAR = "2025"      # シーズン開始年（2025-26なら"2025"）
SCAN_START = date(2026, 3, 1)    # 直近のデータのみ取得（古いデータはstatic fallbackに任せる）
SCAN_END   = date(2026, 5, 31)

BASE_URL = "https://www.bleague.jp/schedule/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# 会場略称 → 正式名
VENUE_NAMES = {
    "Sアリ": "SAGAアリーナ",
    "カミアリ": "カミアリーナ",
    "滋賀DH": "滋賀ダイハツアリーナ",
    "ゼビオ": "ゼビオアリーナ仙台",
    "一宮総体": "一宮市総合体育館",
    "沖アリ": "沖縄アリーナ",
    "CNA": "CNAアリーナ★秋田",
}

# B1全24チーム 正式名称マスタ（表記ゆれ・略称 → 正式名）
B1_TEAM_MASTER = {
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
    "三河シーホース": "シーホース三河",  # 表記ゆれ修正
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

# 試合終了とみなすステータステキスト（B.LEAGUE HTMLで確認された表記）
FINISHED_STATUS_TEXTS = [
    "FINAL", "FINISH", "終了", "試合終了", "GAME OVER", "ENDED",
]


def normalize_team(name: str) -> str:
    """チーム名を正式名称に正規化する"""
    return B1_TEAM_MASTER.get(name, name)


def extract_score(el) -> str:
    """スコア要素から数値文字列を安全に抽出する"""
    if not el:
        return ""
    text = el.get_text(strip=True)
    # 整数部分のみ取得（"89.0" → "89", " 89 " → "89"）
    text = text.strip().split(".")[0].strip()
    return text


def is_game_finished(status_text: str, home_score: str, away_score: str) -> bool:
    """試合が終了しているかどうか判定する"""
    # ステータステキストで判定
    normalized = status_text.upper()
    for marker in FINISHED_STATUS_TEXTS:
        if marker.upper() in normalized:
            return True
    # スコアが両方とも数値なら終了とみなす（ステータス問わず）
    if home_score.isdigit() and away_score.isdigit():
        return True
    return False


def parse_game(html: str, game_date: date):
    soup = BeautifulSoup(html, "html.parser")
    li = soup.find("li", class_="list-item")
    if not li:
        return None

    schedule_key = li.get("id")

    # チーム名取得
    home_name = li.select_one(".team.home .team-name")
    away_name = li.select_one(".team.away .team-name")
    home_raw = home_name.get_text(strip=True) if home_name else ""
    away_raw = away_name.get_text(strip=True) if away_name else ""
    home = normalize_team(home_raw)
    away = normalize_team(away_raw)

    # スコア取得（複数セレクタを試行）
    home_score_el = (
        li.select_one(".home-score span")
        or li.select_one(".score .home")
        or li.select_one("[class*='score'][class*='home']")
        or li.select_one(".score-home span")
    )
    away_score_el = (
        li.select_one(".away-score span")
        or li.select_one(".score .away")
        or li.select_one("[class*='score'][class*='away']")
        or li.select_one(".score-away span")
    )
    home_score = extract_score(home_score_el)
    away_score = extract_score(away_score_el)

    # アリーナ・節・時刻
    arena_spans = li.select(".info-arena span")
    section = arena_spans[0].get_text(strip=True) if len(arena_spans) > 0 else ""
    venue_raw = arena_spans[1].get_text(strip=True) if len(arena_spans) > 1 else ""
    time_str = arena_spans[2].get_text(strip=True) if len(arena_spans) > 2 else ""

    venue_parts = venue_raw.split("|")
    venue_abbr = venue_parts[1].strip() if len(venue_parts) > 1 else venue_raw
    venue = VENUE_NAMES.get(venue_abbr, venue_abbr)

    # ステータス取得
    state_el = li.select_one(".info-scorestate")
    status_text = state_el.get_text(strip=True) if state_el else ""

    finished = is_game_finished(status_text, home_score, away_score)
    result = None
    if finished and home_score.isdigit() and away_score.isdigit():
        result = {"home": int(home_score), "away": int(away_score)}

    # ホーム判定: B.LEAGUE HTML 内の表記（略称）で比較
    is_home = home_raw == TEAM_NAME
    opponent = away if is_home else home

    # チケットURL
    ticket_el = li.select_one(".data-link a.btn.primary")
    ticket_url = ticket_el.get("href") if ticket_el else None

    # 戦評ページURL（終了試合のみ）
    report_url = None
    if finished:
        # まずリンクから取得を試みる
        for a in li.select(".data-link a"):
            href = a.get("href", "")
            if "game_detail" in href:
                if href.startswith("/"):
                    href = "https://www.bleague.jp" + href
                report_url = href
                break
        # リンクがない場合はURLパターンから生成
        if not report_url:
            report_url = f"https://www.bleague.jp/game_detail/?scheduleKey={schedule_key}&tab=2"

    game = {
        "scheduleKey": schedule_key,
        "date": str(game_date),
        "time": time_str,
        "opponent": opponent,
        "isHome": is_home,
        "venue": venue,
        "section": section,
        "status": "FINISHED" if finished else "BEFORE",
        "result": result,
        "basketballLiveUrl": f"https://basketball.mb.softbank.jp/lives/{schedule_key}/",
        "highlightUrl": (
            f"https://basketball.mb.softbank.jp/api/v1/video/highlight?game_id={schedule_key}"
            if finished else None
        ),
        "ticketUrl": ticket_url,
        "reportUrl": report_url,
    }

    return game


def fetch_all_games():
    seen = set()
    games = []
    d = SCAN_START

    while d <= SCAN_END:
        params = {
            "data_format": "json",
            "year": SEASON_YEAR if d.month >= 10 else str(d.year - 1),
            "mon": str(d.month).zfill(2),
            "day": str(d.day).zfill(2),
            "club": CLUB_ID,
            "tab": "1",
        }
        try:
            r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=5)
            data = r.json()
        except Exception as e:
            d += timedelta(days=1)
            continue

        for html in data.get("topics", []):
            g = parse_game(html, d)
            if g and g["scheduleKey"] not in seen:
                seen.add(g["scheduleKey"])
                print(f"  {d} {g['opponent']} {g['status']}", flush=True)
                games.append(g)

        d += timedelta(days=1)

    # 日付昇順にソート
    games.sort(key=lambda g: (g["date"], g.get("time", "")))
    return games


if __name__ == "__main__":
    save_to_file = "--save" in sys.argv

    print(f"スキャン範囲: {SCAN_START} 〜 {SCAN_END}", flush=True)
    games = fetch_all_games()
    finished_count = sum(1 for g in games if g["status"] == "FINISHED")
    before_count   = sum(1 for g in games if g["status"] == "BEFORE")
    print(f"取得試合数: {len(games)} (終了: {finished_count} / 未来: {before_count})", flush=True)

    json_str = json.dumps(games, ensure_ascii=False, indent=2)

    if save_to_file:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "..", "public", "data", "games.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"保存: {os.path.abspath(output_path)}", flush=True)
    else:
        print(json_str)
