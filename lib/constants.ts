export const TEAM_NAME = '佐賀バルーナーズ';
export const TEAM_COLOR = '#00A0E9';

// 外部リンクは必ずここで一元管理する
export const EXTERNAL_LINKS = {
  officialSite: 'https://ballooners.jp/',
  ticketSite: 'https://bleague-ticket.psrv.jp/games/SG',
  // バスケットLIVEのURLは試合ごとに変わる場合があるため、
  // 試合固有のURLが取得できない場合は案内ページへ誘導する
  basketballLiveGuide: 'https://www.bleague.jp/basketlive/',
} as const;
