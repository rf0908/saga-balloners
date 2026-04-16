export type GameStatus = 'BEFORE' | 'LIVE' | 'FINISHED';

export type Game = {
  scheduleKey: string;
  date: string;           // "2026-03-01"
  time: string;           // "14:05"
  opponent: string;
  isHome: boolean;
  venue: string;
  section: string;
  status: GameStatus;
  result?: { home: number; away: number };
  basketballLiveUrl: string;
  highlightUrl?: string;
  ticketUrl?: string;
  reportUrl?: string;     // 公式戦評ページ URL (終了試合のみ)
};

export type Standing = {
  rank: number;
  team: string;
  win: number;
  loss: number;
  streak: string;
};

export type AllStandings = {
  east: Standing[];
  central: Standing[];
  west: Standing[];
  updatedAt?: string;
};

export type PlayerStat = {
  name: string;
  number: number;
  position: string;
  games: number;
  points: number;    // 平均得点
  rebounds: number;  // 平均リバウンド
  assists: number;   // 平均アシスト
  steals?: number;
  blocks?: number;
};

export type PlayerStats = {
  players: PlayerStat[];
  updatedAt?: string;
};
