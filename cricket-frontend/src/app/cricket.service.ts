import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Series, LiveMatch } from './series.model';
import { Scorecard } from './scorecard.model';

export interface NewsItem {
  id: number;
  source: string;
  title: string;
  link: string;
  summary: string;
  published_at: string | null;
  image_url: string;
}

export type RankingKind = 'teams' | 'batsmen' | 'bowlers' | 'allrounders';
export type RankingFormat = 'odi' | 't20' | 'test';

export interface TeamRankingRow {
  team_name: string;
  team_code: string;
  format_type: RankingFormat;
  rank: number;
  rating: number;
}

export interface PlayerRankingRow {
  player_name: string;
  country: string;
  format_type: RankingFormat;
  rank: number;
  rating: number;
  career_best_rating: number | null;
}

export interface RankingsResponse<T> {
  odi: T[];
  t20: T[];
  test: T[];
  /** Present when API returns sync metadata (ICC rankings cache). */
  fetched_at?: string | null;
}

export interface UpcomingMatch {
  external_id: string;
  team_home: string;
  team_away: string;
  series_name: string;
  venue: string;
  status: string;
  start_time_utc: string;
  date_ist: string;
  time_ist: string;
}

export interface LeagueStandingRow {
  team: string;
  team_s_name?: string;
  P: number;
  W: number;
  L: number;
  NR: number;
  NRR: string;
  Pts: number;
}

export interface LeagueStandingsResponse {
  league: string;
  series_id: string;
  series_name: string;
  rows: LeagueStandingRow[];
  fetched_at?: string;
}

export interface TeamLastNStat {
  team: string;
  scope: 'overall' | 'on_venue';
  last_n: number;
  matches_played: number;
  win_pct: number;
  avg_score: number;
  highest_score: number;
  lowest_score: number;
  updated_at: string;
}

export interface TeamHeadToHeadStat {
  team_a: string;
  team_b: string;
  scope: 'overall';
  played: number;
  won_a: number;
  won_b: number;
  highest_total_a: number;
  highest_total_b: number;
  lowest_total_a: number;
  lowest_total_b: number;
  tosses_won_a: number;
  tosses_won_b: number;
  elected_to_bat_a: number;
  elected_to_bat_b: number;
  elected_to_field_a: number;
  elected_to_field_b: number;
  won_toss_and_match_a: number;
  won_toss_and_match_b: number;
  toss_won_bat_first_match_won_a: number;
  toss_won_bat_first_match_won_b: number;
  toss_won_bowl_first_match_won_a: number;
  toss_won_bowl_first_match_won_b: number;
  avg_runs_a: number;
  avg_runs_b: number;
  updated_at: string;
}

export interface TeamFormStat {
  team: string;
  last_n: number;
  form: string;
  updated_at: string;
}

export interface TeamSquadPlayer {
  id?: string;
  name?: string;
  imageId?: number;
  battingStyle?: string;
  bowlingStyle?: string;
}

export interface TeamSquadResponse {
  player?: TeamSquadPlayer[];
}

export interface HighlightVideo {
  videoId: string;
  title: string;
  description: string;
  channelTitle: string;
  publishedAt: string;
  thumbnail: string;
  url: string;
}

export interface MatchHighlightsResponse {
  match_id: string;
  query: string;
  items: HighlightVideo[];
  cached: boolean;
}

export interface BblTopRunScorerRow {
  name: string;
  teamShort: string;
  runs: number;
  innings: number;
  average: number;
}

export interface BblTopWicketTakerRow {
  name: string;
  teamShort: string;
  wickets: number;
  innings: number;
  average: number;
}

export interface BblStrikeRateRow {
  name: string;
  teamShort: string;
  strikeRate: number;
  innings: number;
  average: number;
}

export interface BblEconomyRow {
  name: string;
  teamShort: string;
  economy: number;
  innings: number;
  average: number;
}

export interface BblImpactRow {
  name: string;
  teamShort: string;
  impactPts: number;
  runs: number;
  wickets: number | null;
}

export interface BblStatsData {
  topRunScorers: BblTopRunScorerRow[];
  topWicketTakers: BblTopWicketTakerRow[];
  bestBattingStrikeRates: BblStrikeRateRow[];
  bestBowlingEconomy: BblEconomyRow[];
  smartStatsTotalImpact: BblImpactRow[];
}

export interface SeriesStatsCacheResponse<T = any> {
  series_external_id: string;
  series_name: string;
  fetched_at: string;
  data: T;
}

@Injectable({
  providedIn: 'root'
})
export class CricketService {
  private apiUrl = 'http://127.0.0.1:8000/api/';

  constructor(private http: HttpClient) { }

  getMatches(): Observable<Series[]> {
    return this.http.get<Series[]>(this.apiUrl + 'matches/');
  }

  getScorecard(matchId: string): Observable<Scorecard> {
    const id = String(matchId || '').trim();
    return this.http.get<Scorecard>(`${this.apiUrl}matches/${id}/scorecard/`);
  }

  getLiveMatches(): Observable<LiveMatch[]> {
    return this.http.get<LiveMatch[]>(this.apiUrl + 'live-matches/');
  }

  getLiveScorecard(matchId: string): Observable<Scorecard> {
    return this.http.get<Scorecard>(`${this.apiUrl}live-matches/${matchId}/scorecard/`);
  }

  getLiveResults(): Observable<LiveMatch[]> {
    return this.http.get<LiveMatch[]>(this.apiUrl + 'live-results/');
  }

  getNews(): Observable<NewsItem[]> {
    return this.http.get<NewsItem[]>(this.apiUrl + 'news/');
  }

  getRankings(kind: RankingKind): Observable<RankingsResponse<any>> {
    return this.http.get<RankingsResponse<any>>(this.apiUrl + `rankings/${kind}/`);
  }

  getUpcomingMatches(): Observable<UpcomingMatch[]> {
    return this.http.get<UpcomingMatch[]>(this.apiUrl + 'upcoming-matches/');
  }

  getLeagueStandings(league: 'ipl' | 'psl', refresh = false): Observable<LeagueStandingsResponse> {
    const q = refresh ? '?league=' + league + '&refresh=1' : '?league=' + league;
    return this.http.get<LeagueStandingsResponse>(this.apiUrl + 'league-standings/' + q);
  }

  getTeamLastN(team: string, scope: 'overall' | 'on_venue' = 'overall'): Observable<TeamLastNStat> {
    return this.http.get<TeamLastNStat>(`${this.apiUrl}team-lastn/?team=${encodeURIComponent(team)}&scope=${encodeURIComponent(scope)}`);
  }

  getHeadToHead(a: string, b: string, scope: 'overall' = 'overall'): Observable<TeamHeadToHeadStat> {
    return this.http.get<TeamHeadToHeadStat>(`${this.apiUrl}head-to-head/?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}&scope=${encodeURIComponent(scope)}`);
  }

  getTeamForm(team: string, n: number = 5): Observable<TeamFormStat> {
    return this.http.get<TeamFormStat>(`${this.apiUrl}team-form/?team=${encodeURIComponent(team)}&n=${encodeURIComponent(String(n))}`);
  }

  getTeamSquad(teamId: string, refresh: boolean = false): Observable<TeamSquadResponse> {
    const r = refresh ? '&refresh=1' : '';
    return this.http.get<TeamSquadResponse>(`${this.apiUrl}team-squad/?team_id=${encodeURIComponent(teamId)}${r}`);
  }

  getMatchHighlights(matchId: string, refresh: boolean = false): Observable<MatchHighlightsResponse> {
    const id = String(matchId || '').trim();
    const r = refresh ? '?refresh=1' : '';
    return this.http.get<MatchHighlightsResponse>(`${this.apiUrl}matches/${id}/highlights/${r}`);
  }

  getBblStats(): Observable<SeriesStatsCacheResponse<BblStatsData>> {
    return this.http.get<SeriesStatsCacheResponse<BblStatsData>>(`${this.apiUrl}bbl-stats/`);
  }

  /** Mini auction (IPL / PSL) — backend persists session + cache. */
  createMiniAuction(league: 'ipl' | 'psl', userTeamCode: string): Observable<MiniAuctionCreateResponse> {
    return this.http.post<MiniAuctionCreateResponse>(`${this.apiUrl}auction/create/`, {
      league,
      user_team_code: userTeamCode,
    });
  }

  beginMiniAuction(sessionId: string): Observable<{ ok: boolean; state: MiniAuctionState }> {
    return this.http.post<{ ok: boolean; state: MiniAuctionState }>(
      `${this.apiUrl}auction/${sessionId}/begin/`,
      {},
    );
  }

  getMiniAuctionState(sessionId: string): Observable<MiniAuctionState> {
    return this.http.get<MiniAuctionState>(`${this.apiUrl}auction/${sessionId}/state/`);
  }

  bidMiniAuction(sessionId: string, teamId: string): Observable<MiniAuctionState> {
    return this.http.post<MiniAuctionState>(`${this.apiUrl}auction/${sessionId}/bid/`, { team_id: teamId });
  }

  stopMiniAuction(sessionId: string): Observable<{ ok: boolean; state: MiniAuctionState }> {
    return this.http.post<{ ok: boolean; state: MiniAuctionState }>(`${this.apiUrl}auction/${sessionId}/stop/`, {});
  }

  resumeMiniAuction(sessionId: string): Observable<{ ok: boolean; state: MiniAuctionState }> {
    return this.http.post<{ ok: boolean; state: MiniAuctionState }>(`${this.apiUrl}auction/${sessionId}/resume/`, {});
  }

  restartMiniAuction(sessionId: string): Observable<{ ok: boolean; state: MiniAuctionState }> {
    return this.http.post<{ ok: boolean; state: MiniAuctionState }>(`${this.apiUrl}auction/${sessionId}/restart/`, {});
  }

  /** Same IPL/PSL roster the backend uses to build the auction pool (not random frontend data). */
  getMiniAuctionPoolPreview(league: 'ipl' | 'psl'): Observable<MiniAuctionPoolPreviewResponse> {
    return this.http.get<MiniAuctionPoolPreviewResponse>(
      `${this.apiUrl}auction/pool-preview/?league=${encodeURIComponent(league)}`,
    );
  }
}

export interface MiniAuctionPoolPreviewResponse {
  league: string;
  count: number;
  players: Array<{
    name: string;
    category: string;
    base_price_lakhs: number;
  }>;
}

export interface MiniAuctionCreateResponse {
  session_id: string;
  league: string;
  user_team: Record<string, unknown>;
  teams: Record<string, unknown>[];
  player_count: number;
}

export interface MiniAuctionState {
  session_id: string;
  league: string;
  status: string;
  current_player_index: number;
  round_number: number;
  teams: Array<{
    id: string;
    name: string;
    short_code: string;
    is_user: boolean;
    budget_lakhs: number;
    budget_crores: number;
    squad_count: number;
    strategy: string;
  }>;
  players: unknown[];
  squads: Record<string, unknown[]>;
  current_lot: {
    player: Record<string, unknown>;
    current_bid_lakhs: number;
    next_bid_lakhs: number;
    highest_bidder_id: string | null;
    lot_ends_at: string | null;
    seconds_left: number;
    paused?: boolean;
  } | null;
  user_team_id: string | null;
  rules: {
    budget_crores: number;
    min_squad: number;
    max_squad: number;
    player_base_min_lakhs: number;
    player_base_max_lakhs: number;
    /** Base price tiers (lakhs): 30,40,50,75,100,150,200 */
    allowed_base_price_lakhs?: number[];
    /** Players per rolling window for unsold min/max rules */
    auction_window_size?: number;
    window_unsold_min?: number;
    window_unsold_max?: number;
    /** Unsold lots so far in the current window */
    window_unsold_count?: number;
  };
}