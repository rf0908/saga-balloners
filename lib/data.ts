import { existsSync, readFileSync } from 'fs';
import path from 'path';
import { Game, Standing, AllStandings, PlayerStats } from './types';

// 会場略称 → 正式名
const VENUE_NAMES: Record<string, string> = {
  'Sアリ': 'SAGAアリーナ',
  'カミアリ': 'カミアリーナ',
  '滋賀DH': '滋賀ダイハツアリーナ',
  'ゼビオ': 'ゼビオアリーナ仙台',
  '一宮総体': '一宮市総合体育館',
  '沖アリ': '沖縄アリーナ',
  'CNA': 'CNAアリーナ★秋田',
};

function v(abbr: string): string {
  return VENUE_NAMES[abbr] ?? abbr;
}

// 戦評ページURL を生成
function reportUrl(scheduleKey: string): string {
  return `https://www.bleague.jp/game_detail/?ScheduleKey=${scheduleKey}&tab=2`;
}

// --- スタティックフォールバックデータ ---
// scripts/fetch_schedule.py を実行すると public/data/games.json が生成され、こちらが優先される

const STATIC_GAMES: Game[] = [
  // --- 終了した試合（新しい順） ---
  { scheduleKey: '505323', date: '2026-03-29', time: '14:05', opponent: '茨城ロボッツ',   isHome: true,  venue: v('Sアリ'),    section: '第27節', status: 'FINISHED', result: { home: 90, away: 86 }, basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505323/', highlightUrl: 'https://basketball.mb.softbank.jp/api/v1/video/highlight?game_id=505323', reportUrl: reportUrl('505323') },
  { scheduleKey: '505322', date: '2026-03-16', time: '14:05', opponent: '茨城ロボッツ',   isHome: true,  venue: v('Sアリ'),    section: '第27節', status: 'FINISHED', result: { home: 80, away: 83 }, basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505322/', highlightUrl: 'https://basketball.mb.softbank.jp/api/v1/video/highlight?game_id=505322', reportUrl: reportUrl('505322') },
  { scheduleKey: '505297', date: '2026-03-15', time: '14:05', opponent: '島根スサノオマジック', isHome: false, venue: v('カミアリ'), section: '第26節', status: 'FINISHED', result: { home: 80, away: 77 }, basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505297/', highlightUrl: 'https://basketball.mb.softbank.jp/api/v1/video/highlight?game_id=505297', reportUrl: reportUrl('505297') },
  { scheduleKey: '505296', date: '2026-03-12', time: '15:05', opponent: '島根スサノオマジック', isHome: false, venue: v('カミアリ'), section: '第26節', status: 'FINISHED', result: { home: 91, away: 96 }, basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505296/', highlightUrl: 'https://basketball.mb.softbank.jp/api/v1/video/highlight?game_id=505296', reportUrl: reportUrl('505296') },
  { scheduleKey: '505272', date: '2026-03-09', time: '19:05', opponent: '三遠ネオフェニックス', isHome: true,  venue: v('Sアリ'),    section: '第25節', status: 'FINISHED', result: { home: 91, away: 96 }, basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505272/', highlightUrl: 'https://basketball.mb.softbank.jp/api/v1/video/highlight?game_id=505272', reportUrl: reportUrl('505272') },
  { scheduleKey: '505256', date: '2026-03-08', time: '14:05', opponent: '宇都宮ブレックス', isHome: true,  venue: v('Sアリ'),    section: '第24節', status: 'FINISHED', result: { home: 82, away: 87 }, basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505256/', highlightUrl: 'https://basketball.mb.softbank.jp/api/v1/video/highlight?game_id=505256', reportUrl: reportUrl('505256') },
  { scheduleKey: '505255', date: '2026-03-01', time: '14:05', opponent: '宇都宮ブレックス', isHome: true,  venue: v('Sアリ'),    section: '第24節', status: 'FINISHED', result: { home: 87, away: 90 }, basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505255/', highlightUrl: 'https://basketball.mb.softbank.jp/api/v1/video/highlight?game_id=505255', reportUrl: reportUrl('505255') },

  // --- 今後の試合 ---
  { scheduleKey: '505335', date: '2026-04-01', time: '19:05', opponent: '滋賀レイクス',    isHome: false, venue: v('滋賀DH'),  section: '第28節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505335/', ticketUrl: 'https://www.bleague-ticket.jp/sales/LS/20260401' },
  { scheduleKey: '505339', date: '2026-04-04', time: '15:05', opponent: '仙台89ers',       isHome: false, venue: v('ゼビオ'),   section: '第29節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505339/', ticketUrl: 'https://www.bleague-ticket.jp/sales/SE/20260404' },
  { scheduleKey: '505340', date: '2026-04-05', time: '14:05', opponent: '仙台89ers',       isHome: false, venue: v('ゼビオ'),   section: '第29節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505340/', ticketUrl: 'https://www.bleague-ticket.jp/sales/SE/20260405' },
  { scheduleKey: '505375', date: '2026-04-06', time: '19:05', opponent: '北海道ゲームチェンジャーズ', isHome: true,  venue: v('Sアリ'),    section: '第30節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505375/', ticketUrl: 'https://www.bleague-ticket.jp/sales/SG/20260408' },
  { scheduleKey: '505400', date: '2026-04-09', time: '14:05', opponent: '京都ハンナリーズ', isHome: true,  venue: v('Sアリ'),    section: '第31節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505400/', ticketUrl: 'https://www.bleague-ticket.jp/sales/SG/20260411' },
  { scheduleKey: '505401', date: '2026-04-12', time: '13:05', opponent: '京都ハンナリーズ', isHome: true,  venue: v('Sアリ'),    section: '第31節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505401/', ticketUrl: 'https://www.bleague-ticket.jp/sales/SG/20260412' },
  { scheduleKey: '505415', date: '2026-04-13', time: '19:05', opponent: 'シーホース三河',  isHome: true,  venue: v('Sアリ'),    section: '第32節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505415/', ticketUrl: 'https://www.bleague-ticket.jp/sales/SG/20260415' },
  { scheduleKey: '505431', date: '2026-04-16', time: '15:35', opponent: 'FE名古屋',        isHome: false, venue: v('一宮総体'), section: '第33節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505431/', ticketUrl: 'https://www.bleague-ticket.jp/sales/FE/20260418' },
  { scheduleKey: '505432', date: '2026-04-19', time: '15:35', opponent: 'FE名古屋',        isHome: false, venue: v('一宮総体'), section: '第33節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505432/', ticketUrl: 'https://www.bleague-ticket.jp/sales/FE/20260419' },
  { scheduleKey: '505454', date: '2026-04-20', time: '19:05', opponent: '名古屋ダイヤモンドドルフィンズ', isHome: true, venue: v('Sアリ'), section: '第34節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505454/', ticketUrl: 'https://www.bleague-ticket.jp/sales/SG/20260422' },
  { scheduleKey: '505480', date: '2026-04-23', time: '18:05', opponent: '琉球ゴールデンキングス', isHome: false, venue: v('沖アリ'), section: '第35節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505480/', ticketUrl: 'https://www.bleague-ticket.jp/sales/RG/20260425' },
  { scheduleKey: '505481', date: '2026-04-26', time: '18:05', opponent: '琉球ゴールデンキングス', isHome: false, venue: v('沖アリ'), section: '第35節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505481/', ticketUrl: 'https://www.bleague-ticket.jp/sales/RG/20260426' },
  { scheduleKey: '505484', date: '2026-05-01', time: '14:05', opponent: '秋田ノーザンハピネッツ', isHome: false, venue: v('CNA'), section: '第36節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505484/', ticketUrl: 'https://www.bleague-ticket.jp/sales/AN/20260502' },
  { scheduleKey: '505485', date: '2026-05-03', time: '14:05', opponent: '秋田ノーザンハピネッツ', isHome: false, venue: v('CNA'), section: '第36節', status: 'BEFORE', basketballLiveUrl: 'https://basketball.mb.softbank.jp/lives/505485/', ticketUrl: 'https://www.bleague-ticket.jp/sales/AN/20260503' },
];

const STATIC_STANDINGS: AllStandings = {
  east: [],
  central: [],
  west: [
    { rank: 1, team: '長崎ヴェルカ',             win: 37, loss: 9,  streak: '3連勝'  },
    { rank: 2, team: '琉球ゴールデンキングス',     win: 33, loss: 13, streak: '2連勝'  },
    { rank: 3, team: '広島ドラゴンフライズ',       win: 31, loss: 15, streak: '1連勝'  },
    { rank: 4, team: '大阪エヴェッサ',             win: 29, loss: 17, streak: '1連敗'  },
    { rank: 5, team: '島根スサノオマジック',        win: 27, loss: 19, streak: '2連敗'  },
    { rank: 6, team: '三遠ネオフェニックス',       win: 27, loss: 19, streak: '10連勝' },
    { rank: 7, team: '佐賀バルーナーズ',           win: 23, loss: 23, streak: '1連勝'  },
    { rank: 8, team: '富山グラウジーズ',            win: 18, loss: 28, streak: '1連敗'  },
  ],
};

// --- JSON ファイルから読み込む（呼び出し毎に最新ファイルを参照） ---

function loadJSON<T>(filename: string, fallback: T): T {
  try {
    const p = path.join(process.cwd(), 'public', 'data', filename);
    if (existsSync(p)) {
      return JSON.parse(readFileSync(p, 'utf-8')) as T;
    }
  } catch {
    // JSON が壊れている場合はフォールバック
  }
  return fallback;
}

// データロード関数（呼び出し毎に読み直す → dev/本番どちらでも常に最新）
export function loadGames(): Game[] {
  return loadJSON<Game[]>('games.json', STATIC_GAMES);
}

export function loadStandings(): AllStandings {
  return loadJSON<AllStandings>('standings.json', STATIC_STANDINGS);
}

export function loadPlayerStats(): PlayerStats {
  return loadJSON<PlayerStats>('player_stats.json', { players: [] });
}

// JST (UTC+9) の日付文字列を返す
function toJSTDateStr(now: Date): string {
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10);
}

export function getNextGame(now: Date = new Date()): Game | undefined {
  const today = toJSTDateStr(now);
  return loadGames().find((g) => g.status === 'BEFORE' && g.date >= today);
}

export function getUpcomingGames(excludeFirst = true, now: Date = new Date()): Game[] {
  const today = toJSTDateStr(now);
  const upcoming = loadGames().filter((g) => g.status === 'BEFORE' && g.date >= today);
  return excludeFirst ? upcoming.slice(1) : upcoming;
}

export function getRecentResults(limit = 5): Game[] {
  const finished = loadGames().filter((g) => g.status === 'FINISHED');
  return finished.slice(-limit).reverse();
}

export function getTeamStatus() {
  const standings = loadStandings();
  const sagaStanding = standings.west.find((s) => s.team === '佐賀バルーナーズ');
  return {
    standing: sagaStanding
      ? { rank: sagaStanding.rank, win: sagaStanding.win, loss: sagaStanding.loss, streak: sagaStanding.streak }
      : { rank: 7, win: 24, loss: 23, streak: '2連勝' },
  };
}

/** 佐賀の得点 */
export function getSagaScore(game: Game): number | undefined {
  if (!game.result) return undefined;
  return game.isHome ? game.result.home : game.result.away;
}

/** 相手の得点 */
export function getOpponentScore(game: Game): number | undefined {
  if (!game.result) return undefined;
  return game.isHome ? game.result.away : game.result.home;
}

/** 勝利かどうか */
export function isWin(game: Game): boolean {
  if (!game.result) return false;
  const saga = getSagaScore(game)!;
  const opp = getOpponentScore(game)!;
  return saga > opp;
}
