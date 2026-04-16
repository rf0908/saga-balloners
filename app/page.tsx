import { EXTERNAL_LINKS, TEAM_NAME } from '@/lib/constants';
import {
  loadStandings,
  loadPlayerStats,
  getTeamStatus,
  getNextGame,
  getUpcomingGames,
  getRecentResults,
  isWin,
  getSagaScore,
  getOpponentScore,
} from '@/lib/data';
import { Game } from '@/lib/types';
import { normalizeTeamName } from '@/lib/teams';
import Countdown from './Countdown';
function formatDate(dateStr: string, timeStr: string): string {
  const d = new Date(`${dateStr}T${timeStr}:00+09:00`);
  return d.toLocaleDateString('ja-JP', { month: 'numeric', day: 'numeric', weekday: 'short' });
}

function GameCard({ game }: { game: Game }) {
  const finished = game.status === 'FINISHED';
  const win = finished ? isWin(game) : null;
  const sagaScore = getSagaScore(game);
  const opponentScore = getOpponentScore(game);

  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex justify-between items-center">
      <div>
        <div className="text-xs text-gray-400">
          {formatDate(game.date, game.time)} {game.time} — {game.venue}
          <span className="ml-1 text-[10px] text-gray-300">{game.section}</span>
        </div>
        <div className="font-bold mt-0.5">
          vs {normalizeTeamName(game.opponent)}{' '}
          <span className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded font-normal">
            {game.isHome ? 'HOME' : 'AWAY'}
          </span>
        </div>
      </div>
      <div className="text-right flex flex-col items-end gap-1.5">
        {finished && sagaScore !== undefined && opponentScore !== undefined ? (
          <>
            <div className="text-lg font-black tabular-nums">
              {sagaScore} — {opponentScore}
            </div>
            <div className={`text-xs font-bold ${win ? 'text-[#E91E8C]' : 'text-gray-400'}`}>
              {win ? '✓ 勝利' : '✗ 敗戦'}
            </div>
            {game.highlightUrl && (
              <a
                href={game.highlightUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[11px] border border-orange-400 text-orange-500 px-2 py-0.5 rounded-full"
              >
                ▶ HL
              </a>
            )}
            {game.reportUrl && (
              <a
                href={game.reportUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[11px] border border-gray-300 text-gray-500 px-2 py-0.5 rounded-full"
              >
                戦評
              </a>
            )}
          </>
        ) : (
          <div className="flex gap-2">
            {game.ticketUrl && (
              <a
                href={game.ticketUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[11px] border border-[#E91E8C] text-[#E91E8C] px-2.5 py-1 rounded-full font-bold"
              >
                TICKET
              </a>
            )}
            <a
              href={game.basketballLiveUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] bg-orange-500 text-white px-2.5 py-1 rounded-full font-bold"
            >
              LIVE ↗
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

export default function HomePage() {
  const nextGame = getNextGame();
  const upcomingGames = getUpcomingGames(true);
  const recentResults = getRecentResults(5);
  const { standing } = getTeamStatus();
  const westStandings = loadStandings().west;
  const playerStats = loadPlayerStats();
  const players = playerStats.players;

  return (
    <div className="max-w-md mx-auto bg-gray-50 min-h-screen pb-10 font-sans">
      {/* ヘッダー */}
      <header className="bg-gradient-to-r from-[#0088CC] to-[#00A0E9] text-white p-4 sticky top-0 z-10 shadow-md">
        <a
          href="https://www.bleague.jp/club_detail/?TeamID=1638&tab=1"
          target="_blank"
          rel="noopener noreferrer"
          className="flex flex-col items-center gap-0.5 active:opacity-80"
        >
          <span className="text-[10px] text-blue-200 uppercase tracking-widest font-medium">B.LEAGUE</span>
          <h1 className="text-xl font-black text-center tracking-widest">{TEAM_NAME}</h1>
          <span className="text-[10px] text-blue-200 tracking-wider">OFFICIAL SITE ↗</span>
        </a>
      </header>

      {/* 次の試合：大きく表示 */}
      {nextGame ? (
        <section className="p-4">
          <div className="rounded-2xl shadow-xl overflow-hidden border-2 border-[#00A0E9]">
            {/* ヘッダーバー */}
            <div className="bg-gradient-to-r from-[#0088CC] to-[#00A0E9] text-white text-xs py-1.5 px-3 font-black uppercase text-center tracking-widest">
              ▶ Next Match
            </div>
            {/* コンテンツ */}
            <div className="bg-white p-5 text-center">
              <div className="text-sm font-bold text-[#00A0E9] mb-0.5">
                {formatDate(nextGame.date, nextGame.time)} {nextGame.time}
              </div>
              <div className="text-xs text-gray-400 mb-4">
                {nextGame.venue} &nbsp;|&nbsp; {nextGame.section} &nbsp;|&nbsp; {nextGame.isHome ? '🏠 ホーム' : '✈ アウェイ'}
              </div>
              <div className="flex justify-around items-center mb-5">
                <div className="flex flex-col items-center gap-1">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#00A0E9] to-[#E91E8C] flex items-center justify-center text-white font-black text-xs shadow-md">
                    佐賀
                  </div>
                  <span className="text-xs font-bold text-gray-700">佐賀バルーナーズ</span>
                </div>
                <div className="text-3xl font-black italic text-gray-300">VS</div>
                <div className="flex flex-col items-center gap-1">
                  <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 font-bold text-xs shadow-sm">
                    相手
                  </div>
                  <span className="text-xs font-bold text-gray-700">{normalizeTeamName(nextGame.opponent)}</span>
                </div>
              </div>
              <div className="flex gap-3 justify-center mb-0">
                {nextGame.ticketUrl && (
                  <a
                    href={nextGame.ticketUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 border-2 border-[#E91E8C] text-[#E91E8C] py-2.5 rounded-full font-bold text-sm text-center active:scale-95 transition-transform"
                  >
                    🎟 チケット
                  </a>
                )}
                <a
                  href={nextGame.basketballLiveUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 bg-orange-500 text-white py-2.5 rounded-full font-bold text-sm text-center shadow-md active:scale-95 transition-transform"
                >
                  ▶ バスケットLIVE
                </a>
              </div>
            </div>
            {/* カウントダウン */}
            <div className="bg-gradient-to-r from-[#0088CC] to-[#00A0E9] px-5 pb-5">
              <Countdown targetDate={nextGame.date} targetTime={nextGame.time} />
            </div>
          </div>
        </section>
      ) : (
        <section className="p-4">
          <div className="bg-white rounded-2xl shadow-lg p-6 text-center text-gray-400 text-sm border-2 border-gray-100">
            次の試合情報はありません
          </div>
        </section>
      )}

      {/* 順位・勝敗数 */}
      <section className="px-4 mb-4">
        <div className="bg-gradient-to-r from-[#003E6B] to-[#005A99] text-white rounded-xl p-4 flex justify-between items-center shadow-lg">
          <div>
            <span className="text-xs text-blue-300 block uppercase tracking-widest">Standing</span>
            <span className="text-2xl font-black">西地区 {standing.rank}位</span>
          </div>
          <div className="text-right">
            <span className="text-lg font-bold">
              {standing.win}勝 {standing.loss}敗
            </span>
            <span className="text-xs text-[#E91E8C] block font-black mt-0.5">{standing.streak}</span>
          </div>
        </div>
      </section>

      {/* 地区順位表 */}
      <section className="px-4 mb-6">
        <h3 className="font-bold text-gray-700 mb-2 text-sm uppercase tracking-wide">
          西地区 順位表
        </h3>
        <div className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-xs text-gray-400 uppercase">
                <th className="py-2 px-3 text-left font-medium">順位</th>
                <th className="py-2 px-3 text-left font-medium">チーム</th>
                <th className="py-2 px-3 text-right font-medium">勝</th>
                <th className="py-2 px-3 text-right font-medium">敗</th>
                <th className="py-2 px-3 text-right font-medium">連続</th>
              </tr>
            </thead>
            <tbody>
              {westStandings.map((s) => (
                <tr
                  key={s.rank}
                  className={`border-t border-gray-50 ${s.team === '佐賀バルーナーズ' ? 'bg-[#E8F6FD] font-bold text-[#00A0E9]' : 'text-gray-700'}`}
                >
                  <td className="py-2.5 px-3">{s.rank}</td>
                  <td className="py-2.5 px-3">{s.team}</td>
                  <td className="py-2.5 px-3 text-right tabular-nums">{s.win}</td>
                  <td className="py-2.5 px-3 text-right tabular-nums">{s.loss}</td>
                  <td className="py-2.5 px-3 text-right text-xs text-gray-400 font-normal">{s.streak}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 今後のスケジュール */}
      {upcomingGames.length > 0 && (
        <section className="px-4 mb-6">
          <h3 className="font-bold text-gray-700 mb-2 text-sm uppercase tracking-wide">
            Upcoming Matches
          </h3>
          <div className="space-y-3">
            {upcomingGames.map((game) => (
              <GameCard key={game.scheduleKey} game={game} />
            ))}
          </div>
        </section>
      )}

      {/* 直近の結果 */}
      {recentResults.length > 0 && (
        <section className="px-4">
          <h3 className="font-bold text-gray-700 mb-2 text-sm uppercase tracking-wide">
            Recent Results
          </h3>
          <div className="space-y-3">
            {recentResults.map((game) => (
              <GameCard key={game.scheduleKey} game={game} />
            ))}
          </div>
        </section>
      )}

      {/* 個人スタッツ */}
      {players.length > 0 && (
        <section className="px-4 mb-6">
          <h3 className="font-bold text-gray-700 mb-2 text-sm uppercase tracking-wide">
            Player Stats
          </h3>
          <div className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-gray-50 text-[10px] text-gray-400 uppercase">
                  <th className="py-2 px-2 text-left font-medium w-6">#</th>
                  <th className="py-2 px-2 text-left font-medium">選手</th>
                  <th className="py-2 px-1 text-right font-medium">得点</th>
                  <th className="py-2 px-1 text-right font-medium">RB</th>
                  <th className="py-2 px-1 text-right font-medium">AS</th>
                  <th className="py-2 px-1 text-right font-medium">ST</th>
                </tr>
              </thead>
              <tbody>
                {players.map((p, i) => (
                  <tr key={i} className="border-t border-gray-50 text-gray-700">
                    <td className="py-2 px-2 text-gray-400 tabular-nums">{p.number || '—'}</td>
                    <td className="py-2 px-2 font-medium">
                      {p.name}
                      {p.position && (
                        <span className="ml-1 text-[9px] text-gray-400">{p.position}</span>
                      )}
                    </td>
                    <td className="py-2 px-1 text-right tabular-nums font-bold text-[#00A0E9]">
                      {p.points.toFixed(1)}
                    </td>
                    <td className="py-2 px-1 text-right tabular-nums text-gray-500">
                      {p.rebounds.toFixed(1)}
                    </td>
                    <td className="py-2 px-1 text-right tabular-nums text-gray-500">
                      {p.assists.toFixed(1)}
                    </td>
                    <td className="py-2 px-1 text-right tabular-nums text-gray-500">
                      {(p.steals ?? 0).toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {playerStats.updatedAt && (
              <p className="text-[9px] text-gray-300 text-right px-3 py-1">
                更新: {new Date(playerStats.updatedAt).toLocaleDateString('ja-JP')}
              </p>
            )}
          </div>
        </section>
      )}

      {/* フッター */}
      <footer className="text-center text-xs text-gray-300 mt-8 px-4">
        データは B.LEAGUE 公式サイトより取得。最新情報は
        <a
          href={EXTERNAL_LINKS.officialSite}
          className="underline ml-1"
          target="_blank"
          rel="noopener noreferrer"
        >
          公式サイト
        </a>
        をご確認ください。
      </footer>
    </div>
  );
}
