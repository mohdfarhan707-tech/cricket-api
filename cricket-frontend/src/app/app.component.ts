import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { BblStatsData, CricketService, LeagueStandingRow, MatchHighlightsResponse, MiniAuctionState, NewsItem, RankingKind, RankingsResponse, TeamFormStat, TeamHeadToHeadStat, TeamLastNStat, TeamSquadPlayer, TeamSquadResponse, UpcomingMatch } from './cricket.service';
import { AuthService } from './auth.service';
import { Series, Match, LiveMatch } from './series.model';
import { Scorecard } from './scorecard.model';
import {
  pickBidCommentary,
  pickCompetitiveTwoTeam,
  pickOpeningLine,
  pickSoldCommentary,
  pickUnsoldCommentary,
  TIMER_GOING_ONCE,
  TIMER_GOING_TWICE,
  TIMER_LAST_CHANCE,
} from './auction-commentary';
import {
  IPL_AUCTION_FRANCHISES,
  IPL_CODE_ACCENT_MAP,
  PSL_AUCTION_FRANCHISES,
  PSL_CODE_ACCENT_MAP,
} from './ipl-auction.constants';
import {
  IPL_ORANGE_CAP_2026,
  IPL_PURPLE_CAP_2026,
  PSL_MOST_RUNS_2026,
  PSL_MOST_WICKETS_2026,
} from './ipl-psl-leaderboards.constants';
import { FALLBACK_LOGO, getFallbackTeamLogoUrl, resolveTeamLogoUrl } from './team-logos';
import { forkJoin } from 'rxjs';
import html2canvas from 'html2canvas';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit, OnDestroy {
  seriesData: Series[] = []; 
  masterData: Series[] = [];
  activeTab: string = 'all';
  private collapsedSeries = new Set<string>();

  liveMatches: LiveMatch[] = [];
  liveResults: LiveMatch[] = [];
  newsItems: NewsItem[] = [];
  upcomingMatches: UpcomingMatch[] = [];

  // 'all' -> All series, 'series' -> specific series from masterData, 'ipl'/'psl' -> special leagues
  selectedLeagueId: string = '';
  selectedLeagueType: 'all' | 'series' | 'ipl' | 'psl' | 'bbl' | 'wc' = 'all';
  leagueSubTab: 'matches' | 'points' | 'stats' = 'matches';
  wcPointsStage: 'group' | 'super8' = 'group';
  headerPage: 'home' | 'news' | 'rankings' | 'teams' | 'fixtures' | 'matchcentre' | 'matchreport' | 'auction' = 'home';
  /** Mini auction (IPL/PSL) — session persisted in backend + sessionStorage id */
  auctionLeague: 'ipl' | 'psl' = 'ipl';
  auctionTeamCode = 'MI';
  auctionSessionId: string | null = null;
  auctionState: MiniAuctionState | null = null;
  auctionError: string | null = null;
  auctionLoading = false;
  auctionCreating = false;
  private auctionPollTimer: ReturnType<typeof setInterval> | null = null;

  readonly auctionIplCodes = ['MI', 'CSK', 'RCB', 'KKR', 'RR', 'SRH', 'DC', 'PBKS', 'LSG', 'GT'];
  readonly auctionPslCodes = ['IU', 'KK', 'LQ', 'MS', 'PZ', 'QG'];
  /** Mini auction sidebar tabs (WK grouped under batters) */
  auctionPlayerTab: 'bat' | 'bowl' | 'ar' | 'unsold' = 'bat';
  /** Fetched from API — same roster as backend pool (`ipl_players_data` / `psl_players_data`) */
  auctionPreviewPlayers: Array<Record<string, unknown>> = [];
  auctionPreviewLoading = false;
  auctionPreviewError: string | null = null;
  /** Floating toasts when any team raises the bid */
  auctionBidToasts: { id: number; message: string }[] = [];
  private auctionToastSeq = 0;
  private auctionBidSnapshot: { playerIdx: number; bidLakhs: number; bidderId: string | null } | null = null;
  /** Tracks bidders / timer flags for dynamic commentary on the active lot */
  private auctionCommentaryLot: {
    playerIdx: number;
    bidderIds: string[];
    bidHistory: string[];
    bidCount: number;
    timerFlags: { once: boolean; twice: boolean; last: boolean };
  } | null = null;
  auctionControlLoading = false;
  headerSubTab: 'team' | 'batter' | 'bowler' | 'allrounder' = 'team';

  // BBL points table (static values shown in UI, matching your screenshot)
  bblPointsTable: { team: string; qualified: boolean; P: number; W: number; L: number; NR: number; NRR: string; Pts: number }[] = [
    { team: 'Perth Scorchers', qualified: true, P: 10, W: 7, L: 3, NR: 0, NRR: '+1.363', Pts: 14 },
    { team: 'Sydney Sixers', qualified: true, P: 10, W: 6, L: 3, NR: 1, NRR: '+0.605', Pts: 13 },
    { team: 'Hobart Hurricanes', qualified: true, P: 10, W: 6, L: 3, NR: 1, NRR: '+0.331', Pts: 13 },
    { team: 'Melbourne Stars', qualified: false, P: 10, W: 6, L: 4, NR: 0, NRR: '+0.759', Pts: 12 },
    { team: 'Brisbane Heat', qualified: false, P: 10, W: 5, L: 5, NR: 0, NRR: '-0.431', Pts: 10 },
    { team: 'Adelaide Strikers', qualified: false, P: 10, W: 4, L: 6, NR: 0, NRR: '-0.231', Pts: 8 },
    { team: 'Melbourne Renegades', qualified: false, P: 10, W: 3, L: 7, NR: 0, NRR: '-1.202', Pts: 6 },
    { team: 'Sydney Thunder', qualified: false, P: 10, W: 2, L: 8, NR: 0, NRR: '-1.212', Pts: 4 },
  ];
  /** IPL / PSL points from backend (Cricbuzz series via RapidAPI). */
  leagueStandingsIpl: LeagueStandingRow[] | null = null;
  leagueStandingsPsl: LeagueStandingRow[] | null = null;
  leagueStandingsLoading = false;
  leagueStandingsError: string | null = null;
  leagueStandingsTitleIpl = '';
  leagueStandingsTitlePsl = '';
  wcPointsGroups: { group: string; rows: { team: string; P: number; W: number; L: number; NR: number; NRR: string; Pts: number }[] }[] = [
    {
      group: 'Group A',
      rows: [
        { team: 'India', P: 4, W: 4, L: 0, NR: 0, NRR: '+2.500', Pts: 8 },
        { team: 'Pakistan', P: 4, W: 3, L: 1, NR: 0, NRR: '+0.976', Pts: 6 },
        { team: 'United States of America', P: 4, W: 2, L: 2, NR: 0, NRR: '+0.788', Pts: 4 },
        { team: 'Netherlands', P: 4, W: 1, L: 3, NR: 0, NRR: '-1.217', Pts: 2 },
        { team: 'Namibia', P: 4, W: 0, L: 4, NR: 0, NRR: '-3.108', Pts: 0 },
      ],
    },
    {
      group: 'Group B',
      rows: [
        { team: 'Zimbabwe', P: 4, W: 3, L: 0, NR: 1, NRR: '+1.506', Pts: 7 },
        { team: 'Sri Lanka', P: 4, W: 3, L: 1, NR: 0, NRR: '+1.741', Pts: 6 },
        { team: 'Australia', P: 4, W: 2, L: 2, NR: 0, NRR: '+1.523', Pts: 4 },
        { team: 'Ireland', P: 4, W: 1, L: 2, NR: 1, NRR: '+0.150', Pts: 3 },
        { team: 'Oman', P: 4, W: 0, L: 4, NR: 0, NRR: '-4.845', Pts: 0 },
      ],
    },
    {
      group: 'Group C',
      rows: [
        { team: 'West Indies', P: 4, W: 4, L: 0, NR: 0, NRR: '+1.874', Pts: 8 },
        { team: 'England', P: 4, W: 3, L: 1, NR: 0, NRR: '+0.201', Pts: 6 },
        { team: 'Scotland', P: 4, W: 1, L: 3, NR: 0, NRR: '+0.184', Pts: 2 },
        { team: 'Italy', P: 4, W: 1, L: 3, NR: 0, NRR: '-1.020', Pts: 2 },
        { team: 'Nepal', P: 4, W: 1, L: 3, NR: 0, NRR: '-1.349', Pts: 2 },
      ],
    },
    {
      group: 'Group D',
      rows: [
        { team: 'South Africa', P: 4, W: 4, L: 0, NR: 0, NRR: '+1.943', Pts: 8 },
        { team: 'New Zealand', P: 4, W: 3, L: 1, NR: 0, NRR: '+1.227', Pts: 6 },
        { team: 'Afghanistan', P: 4, W: 2, L: 2, NR: 0, NRR: '+0.889', Pts: 4 },
        { team: 'United Arab Emirates', P: 4, W: 1, L: 3, NR: 0, NRR: '-1.364', Pts: 2 },
        { team: 'Canada', P: 4, W: 0, L: 4, NR: 0, NRR: '-2.426', Pts: 0 },
      ],
    },
  ];
  wcSuper8PointsGroups: { group: string; rows: { team: string; P: number; W: number; L: number; NR: number; NRR: string; Pts: number }[] }[] = [
    {
      group: 'Super Eights, Group 1',
      rows: [
        { team: 'South Africa', P: 3, W: 3, L: 0, NR: 0, NRR: '+2.259', Pts: 6 },
        { team: 'India', P: 3, W: 2, L: 1, NR: 0, NRR: '+0.106', Pts: 4 },
        { team: 'West Indies', P: 3, W: 1, L: 2, NR: 0, NRR: '+0.993', Pts: 2 },
        { team: 'Zimbabwe', P: 3, W: 0, L: 3, NR: 0, NRR: '-3.415', Pts: 0 },
      ],
    },
    {
      group: 'Super Eights, Group 2',
      rows: [
        { team: 'England', P: 3, W: 3, L: 0, NR: 0, NRR: '+1.096', Pts: 6 },
        { team: 'New Zealand', P: 3, W: 1, L: 1, NR: 1, NRR: '+1.390', Pts: 3 },
        { team: 'Pakistan', P: 3, W: 1, L: 1, NR: 1, NRR: '-0.123', Pts: 3 },
        { team: 'Sri Lanka', P: 3, W: 0, L: 3, NR: 0, NRR: '-1.950', Pts: 0 },
      ],
    },
  ];
  wcStatsData = {
    topRunScorers: [
      { name: 'Sahibzada Farhan', teamShort: 'PAK', runs: 383, innings: 6, average: 76.6 },
      { name: 'Tim Seifert', teamShort: 'NZ', runs: 326, innings: 8, average: 46.57 },
      { name: 'Sanju Samson', teamShort: 'IND', runs: 321, innings: 5, average: 80.25 },
    ],
    topWicketTakers: [
      { name: 'Jasprit Bumrah', teamShort: 'IND', wickets: 14, innings: 8, average: 12.42 },
      { name: 'Varun Chakravarthy', teamShort: 'IND', wickets: 14, innings: 9, average: 20.5 },
      { name: 'Shadley van Schalkwyk', teamShort: 'USA', wickets: 13, innings: 4, average: 7.76 },
    ],
    bestBattingStrikeRates: [
      { name: 'Finn Allen', teamShort: 'NZ', strikeRate: 200, innings: 8, average: 49.66 },
      { name: 'Sanju Samson', teamShort: 'IND', strikeRate: 199.37, innings: 5, average: 80.25 },
      { name: 'Mitchell Marsh', teamShort: 'AUS', strikeRate: 196.66, innings: 2, average: 118 },
    ],
    bestBowlingEconomy: [
      { name: 'Josh Little', teamShort: 'IRE', economy: 4, innings: 1, average: 5.33 },
      { name: 'Paul van Meekeren', teamShort: 'NED', economy: 5, innings: 1, average: 10 },
      { name: 'George Dockrell', teamShort: 'IRE', economy: 6, innings: 3, average: 13.5 },
    ],
    smartStatsTotalImpact: [
      { name: 'Will Jacks', teamShort: 'ENG', impactPts: 477.12, runs: 226, wickets: 9 },
      { name: 'Rachin Ravindra', teamShort: 'NZ', impactPts: 384.49, runs: 129, wickets: 12 },
      { name: 'Ishan Kishan', teamShort: 'IND', impactPts: 374.56, runs: 317, wickets: null },
    ],
  };
  private readonly bblVenueByMatchNumber: Record<number, string> = {
    1: 'Perth Stadium, Perth',
    2: 'GMHBA Stadium, Geelong',
    3: 'Bellerive Oval, Hobart',
    4: 'Sydney Cricket Ground, Sydney',
    5: 'Melbourne Cricket Ground, Melbourne',
    6: 'The Gabba, Brisbane',
    7: 'Sydney Showground Stadium, Sydney',
    8: 'Adelaide Oval, Adelaide',
    9: 'Perth Stadium, Perth',
    10: 'Docklands Stadium (Marvel Stadium), Melbourne',
    11: 'Manuka Oval, Canberra',
    12: 'Perth Stadium, Perth',
    13: 'The Gabba, Brisbane',
    14: 'Manuka Oval, Canberra',
    15: 'Adelaide Oval, Adelaide',
    16: 'Sydney Cricket Ground, Sydney',
    17: 'Melbourne Cricket Ground, Melbourne',
    18: 'Bellerive Oval, Hobart',
    19: 'GMHBA Stadium, Geelong',
    20: 'Perth Stadium, Perth',
    21: 'Sydney Showground Stadium, Sydney',
    22: 'Docklands Stadium, Melbourne',
    23: 'Perth Stadium, Perth',
    24: 'Coffs Harbour International Stadium, Coffs Harbour',
    25: 'Adelaide Oval, Adelaide',
    26: 'Perth Stadium, Perth',
    27: 'Sydney Cricket Ground, Sydney',
    28: 'Melbourne Cricket Ground, Melbourne',
    29: 'The Gabba, Brisbane',
    30: 'Bellerive Oval, Hobart',
    31: 'Manuka Oval, Canberra',
    32: 'Adelaide Oval, Adelaide',
    33: 'Docklands Stadium, Melbourne',
    34: 'Perth Stadium, Perth',
    35: 'Sydney Showground Stadium, Sydney',
    36: 'Melbourne Cricket Ground, Melbourne',
    37: 'The Gabba, Brisbane',
    38: 'Bellerive Oval, Hobart',
    39: 'Adelaide Oval, Adelaide',
    40: 'Sydney Cricket Ground, Sydney',
    41: 'Perth Stadium, Perth',
    42: 'Bellerive Oval, Hobart',
    43: 'Sydney Cricket Ground, Sydney',
    44: 'Perth Stadium, Perth',
  };

  rankingsTeams: RankingsResponse<any> | null = null;
  rankingsBatsmen: RankingsResponse<any> | null = null;
  rankingsBowlers: RankingsResponse<any> | null = null;
  rankingsAllRounders: RankingsResponse<any> | null = null;
  rankingsLoading = false;

  scorecardModalOpen = false;
  scorecardLoading = false;
  scorecardError: string | null = null;
  scorecardData: Scorecard | null = null;
  selectedMatch: Match | null = null;
  highlightsModalOpen = false;
  highlightsLoading = false;
  highlightsError: string | null = null;
  highlightsData: MatchHighlightsResponse | null = null;
  highlightsSelectedVideoId: string | null = null;
  highlightsEmbedUrl: SafeResourceUrl | null = null;
  highlightsSelectedUrl: string | null = null;
  highlightsSelectedMatch: Match | null = null;
  private highlightsOpenedAtMs = 0;

  matchCentreTab: 'info' | 'squad' | 'scorecard' | 'buildxi' = 'info';
  selectedUpcoming: UpcomingMatch | null = null;

  matchCentreScorecardLoading = false;
  matchCentreScorecardError: string | null = null;
  matchCentreScorecardData: Scorecard | null = null;
  bblSummaryModalOpen = false;
  wcSummaryModalOpen = false;
  matchCentreSelectedBblInningsIdx = 0;
  selectedBblMatch: Match | null = null;
  /** Fetch scorecard from live endpoint (current-matches feed). False once a fixture is finished (use DB-backed matches API). */
  matchCentreUseLiveScorecardApi = false;
  /** Bumps when a new scorecard HTTP request starts; stale responses are ignored. */
  private matchCentreScorecardReqGen = 0;
  /** Show SCORECARD tab for series other than BBL/WC (e.g. IPL completed on home). */
  matchCentreAllowScorecardTab = false;
  /** Hide Build XI when opening match centre from home scored cards (non-upcoming). */
  matchCentreHideBuildXiTab = false;
  private matchCentreTicker: any = null;
  matchCentreNowMs = Date.now();
  matchCentreTeamA: TeamLastNStat | null = null;
  matchCentreTeamB: TeamLastNStat | null = null;
  matchCentreComparisonLoading = false;
  matchCentreH2H: TeamHeadToHeadStat | null = null;
  matchCentreH2HLoading = false;
  matchCentreFormA: TeamFormStat | null = null;
  matchCentreFormB: TeamFormStat | null = null;
  matchCentreFormLoading = false;
  matchCentreSquadLoading = false;
  matchCentreSquadA: { batters: TeamSquadPlayer[]; allrounders: TeamSquadPlayer[]; bowlers: TeamSquadPlayer[] } | null = null;
  matchCentreSquadB: { batters: TeamSquadPlayer[]; allrounders: TeamSquadPlayer[]; bowlers: TeamSquadPlayer[] } | null = null;

  // Build Your XI (WorldCup/Upcoming match centre)
  matchCentreXISelected: { team: 'A' | 'B'; category: 'batters' | 'allrounders' | 'bowlers'; player: TeamSquadPlayer }[] = [];
  matchCentreXIMsg: string | null = null;
  matchCentreXIError: string | null = null;

  // BBL stats tab (league view)
  bblStatsLoading = false;
  bblStatsError: string | null = null;
  bblStatsData: BblStatsData | null = null;

  /** Static IPL / PSL leaderboards (same card layout as BBL stats). */
  readonly iplOrangeCap2026 = IPL_ORANGE_CAP_2026;
  readonly iplPurpleCap2026 = IPL_PURPLE_CAP_2026;
  readonly pslMostRuns2026 = PSL_MOST_RUNS_2026;
  readonly pslMostWickets2026 = PSL_MOST_WICKETS_2026;

  // Fantasy XI after confirmation
  matchCentreXIFantasyConfirmed = false;
  matchCentreXICaptainKey: string | null = null;
  matchCentreXIWkKey: string | null = null;
  matchCentreXIScreenshotLoading = false;
  matchCentreXIImpactKey: string | null = null;

  // World Cup match report (full page)
  selectedWorldCupReport: Match | null = null;
  matchReportLoading = false;
  matchReportError: string | null = null;
  matchReportData: Scorecard | null = null;

  matchReportEssayTitle: string = '';
  matchReportEssayDateLine: string = '';
  matchReportEssayParagraphs: string[] = [];

  darkMode = false;

  /** When true, staff users see the public CricLive app instead of the admin console. */
  adminViewPublicApp = false;

  // Teams page (IPL / PSL)
  teamPageLeague: 'ipl' | 'psl' | 'bbl' = 'ipl';
  teamPageSelectedCode: string | null = null; // IPL code (CSK) or PSL key (HK, IU, ...)
  teamPageTab: 'matches' | 'squad' = 'matches';
  teamPageSquadLoading = false;
  teamPageSquad: { batters: TeamSquadPlayer[]; allrounders: TeamSquadPlayer[]; bowlers: TeamSquadPlayer[] } | null = null;

  constructor(
    private cricketService: CricketService,
    public auth: AuthService,
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef,
  ) {}

  get authToolbarLabel(): string {
    const u = this.auth.currentUser();
    if (!u) return '';
    return (u.email || u.username || '').trim();
  }

  logout(): void {
    this.adminViewPublicApp = false;
    this.auth.logout();
    this.cdr.markForCheck();
  }

  onAuthDone(): void {
    this.adminViewPublicApp = false;
    if (!this.auth.isAdmin()) {
      this.openHeaderPage('home');
    }
    this.cdr.markForCheck();
  }

  showAdminDashboard(): boolean {
    return this.auth.isLoggedIn() && this.auth.isAdmin() && !this.adminViewPublicApp;
  }

  goToAdminPanel(): void {
    this.adminViewPublicApp = false;
    this.cdr.markForCheck();
  }

  onOpenPublicSiteFromAdmin(): void {
    this.adminViewPublicApp = true;
    this.openHeaderPage('home');
    this.cdr.markForCheck();
  }

  private refreshLiveMatches() {
    this.cricketService.getLiveMatches().subscribe({
      next: (data) => {
        this.liveMatches = data || [];
      },
      error: (err) => console.error('Live matches error:', err)
    });
  }

  private refreshLiveResults() {
    this.cricketService.getLiveResults().subscribe({
      next: (data) => {
        this.liveResults = data || [];
      },
      error: (err) => console.error('Live results error:', err)
    });
  }

  ngOnInit() {
    this.cricketService.getMatches().subscribe({
      next: (data) => {
        this.masterData = data;
        this.seriesData = data; // Initialize the display variable
      },
      error: (err) => console.error('Connection Error:', err)
    });

    this.refreshLiveMatches();
    this.refreshLiveResults();

    this.cricketService.getUpcomingMatches().subscribe({
      next: (data) => { this.upcomingMatches = data || []; },
      error: (err) => console.error('Upcoming error:', err)
    });

    this.cricketService.getNews().subscribe({
      next: (data) => {
        this.newsItems = data || [];
      },
      error: (err) => console.error('News error:', err)
    });

    this.auth.user$.subscribe(() => this.cdr.markForCheck());
  }

  ngOnDestroy() {
    if (this.matchCentreTicker) {
      clearInterval(this.matchCentreTicker);
      this.matchCentreTicker = null;
    }
    this.stopAuctionPoll();
  }

  // Logic to handle tab switching (Results, Live, Upcoming)
  applyFilter(status: string) {
    this.activeTab = status;
    this.headerPage = 'home';
    // Re-fetch so ended/live transitions appear without hard refresh
    if (status === 'live') {
      this.refreshLiveMatches();
    }
    if (status === 'all' || status === 'results') {
      this.refreshLiveResults();
      // keep live count fresh as well
      this.refreshLiveMatches();
    }
    if (status === 'all') {
      this.seriesData = this.masterData;
    } else if (status === 'live') {
      // live tab uses separate liveMatches list; keep seriesData unchanged
      this.seriesData = this.masterData;
    } else {
      this.seriesData = this.masterData.map(series => ({
        ...series,
        matches: series.matches.filter(m => {
          const mStatus = m.status.toLowerCase();
          // Maps "completed" or "result" to the Results tab
          if (status === 'results') return mStatus === 'completed' || mStatus === 'result';
          return mStatus === status;
        })
      })).filter(series => series.matches.length > 0);
    }
  }

  openHeaderPage(page: 'home' | 'news' | 'rankings' | 'teams' | 'fixtures' | 'matchcentre' | 'auction') {
    if (!this.auth.isLoggedIn()) {
      return;
    }
    if (page !== 'auction') {
      this.stopAuctionPoll();
    }
    this.headerPage = page;
    // Prevent scorecard overlays from sticking across navigation.
    if (page !== 'home') {
      this.scorecardModalOpen = false;
      this.scorecardData = null;
      this.scorecardLoading = false;
      this.scorecardError = null;
      this.selectedMatch = null;
      this.selectedWorldCupReport = null;
      this.closeHighlights();
    }
    if (page === 'rankings') {
      this.loadRankings('teams');
    }
    if (page === 'teams') {
      this.teamPageSelectedCode = null;
      this.teamPageTab = 'matches';
      this.teamPageLeague = 'ipl';
      this.teamPageSquad = null;
      this.teamPageSquadLoading = false;
    }
    if (page === 'auction') {
      this.auctionSessionId = sessionStorage.getItem('miniAuctionSessionId');
      if (this.auctionSessionId) {
        // Avoid showing the franchise grid while a session exists but state isn't loaded yet
        // (otherwise local auctionTeamCode can disagree with the real user team, often MI).
        this.auctionState = null;
        this.loadAuctionPoolPreview();
        this.refreshAuctionState();
        this.startAuctionPoll();
      } else {
        this.auctionState = null;
        this.loadAuctionPoolPreview();
      }
    }
  }

  stopAuctionPoll() {
    if (this.auctionPollTimer) {
      clearInterval(this.auctionPollTimer);
      this.auctionPollTimer = null;
    }
  }

  startAuctionPoll() {
    this.stopAuctionPoll();
    if (!this.auctionSessionId) return;
    this.auctionPollTimer = setInterval(() => this.refreshAuctionState(), 1200);
  }

  refreshAuctionState() {
    if (!this.auctionSessionId) return;
    this.cricketService.getMiniAuctionState(this.auctionSessionId).subscribe({
      next: (s) => {
        const prev = this.auctionState;
        this.auctionState = s;
        this.syncAuctionUiFromState(s);
        this.auctionError = null;
        // If setup state ever arrives without a player array, still show a sidebar list from preview API
        if (s.status === 'setup' && (!s.players || s.players.length === 0)) {
          this.loadAuctionPoolPreview();
        }
        this.maybeCommentaryLotResolved(prev, s);
        this.maybeAuctionRunningCommentary(prev, s);
        this.cdr.markForCheck();
        if (s.status === 'finished') {
          this.stopAuctionPoll();
        }
      },
      error: (err) => {
        this.auctionError = err?.error?.error || 'Auction state failed';
        if (err?.status === 404) {
          sessionStorage.removeItem('miniAuctionSessionId');
          this.auctionSessionId = null;
          this.auctionState = null;
          this.stopAuctionPoll();
          this.loadAuctionPoolPreview();
        }
        this.cdr.markForCheck();
      },
    });
  }

  /** Sold / unsold when the hammer lot advances. */
  private maybeCommentaryLotResolved(prev: MiniAuctionState | null, s: MiniAuctionState) {
    if (!prev || prev.current_player_index === s.current_player_index) {
      return;
    }
    const resolvedIdx = prev.current_player_index;
    const rows = (s.players || []) as Array<{
      order_index: number;
      status: string;
      name: string;
      sold_price_lakhs?: number | null;
      sold_to_id?: string | null;
    }>;
    const row = rows.find((p) => p.order_index === resolvedIdx);
    if (!row) {
      return;
    }
    if (row.status === 'sold' && row.sold_to_id) {
      const team = s.teams.find((t) => t.id === row.sold_to_id);
      if (team) {
        this.pushAuctionBidToast(
          pickSoldCommentary({
            team,
            playerName: row.name,
            soldPriceLakhs: Number(row.sold_price_lakhs ?? 0),
          }),
          5200,
        );
      }
    } else if (row.status === 'unsold') {
      this.pushAuctionBidToast(pickUnsoldCommentary(), 4000);
    }
  }

  /** Opening lines, timer patter, and varied bid commentary (IPL-style). */
  private maybeAuctionRunningCommentary(prev: MiniAuctionState | null, s: MiniAuctionState) {
    if (s.status !== 'running' || !s.current_lot) {
      if (s.status !== 'running') {
        this.auctionBidSnapshot = null;
        this.auctionCommentaryLot = null;
      }
      return;
    }

    const lot = s.current_lot;
    const notPaused = !lot.paused;

    const idx = s.current_player_index;
    const bid = lot.current_bid_lakhs;
    const bidderId = lot.highest_bidder_id ?? null;
    const prevSnap = this.auctionBidSnapshot;

    const pickT = <T extends readonly string[]>(arr: T): string => arr[Math.floor(Math.random() * arr.length)]!;

    // New lot → reset + opening line
    if (!prevSnap || prevSnap.playerIdx !== idx) {
      this.auctionCommentaryLot = {
        playerIdx: idx,
        bidderIds: [],
        bidHistory: [],
        bidCount: 0,
        timerFlags: { once: false, twice: false, last: false },
      };
      const player = lot.player as Record<string, unknown>;
      const base = Number(player['base_price_lakhs'] ?? 0);
      this.pushAuctionBidToast(pickOpeningLine(base), 3800);
      this.auctionBidSnapshot = { playerIdx: idx, bidLakhs: bid, bidderId };
      return;
    }

    const lotSt = this.auctionCommentaryLot;
    if (!lotSt || lotSt.playerIdx !== idx) {
      this.auctionBidSnapshot = { playerIdx: idx, bidLakhs: bid, bidderId };
      return;
    }

    // Near hammer (timer) — only while clock is running
    const sec = lot.seconds_left ?? 0;
    if (notPaused && sec > 0) {
      if (sec <= 5 && !lotSt.timerFlags.once) {
        lotSt.timerFlags.once = true;
        this.pushAuctionBidToast(pickT(TIMER_GOING_ONCE), 2600);
      } else if (sec <= 3 && !lotSt.timerFlags.twice) {
        lotSt.timerFlags.twice = true;
        this.pushAuctionBidToast(pickT(TIMER_GOING_TWICE), 2600);
      } else if (sec <= 1 && !lotSt.timerFlags.last) {
        lotSt.timerFlags.last = true;
        this.pushAuctionBidToast(pickT(TIMER_LAST_CHANCE), 2800);
      }
    }

    // New bid (frozen while paused)
    if (notPaused && bidderId && (bid > prevSnap.bidLakhs || bidderId !== prevSnap.bidderId)) {
      const team = s.teams.find((t) => t.id === bidderId);
      if (team) {
        const isFirstBid = !prevSnap.bidderId && !!bidderId;
        const isNewTeam = !lotSt.bidderIds.includes(bidderId);
        lotSt.bidCount += 1;
        lotSt.bidHistory.push(bidderId);
        if (isNewTeam) {
          lotSt.bidderIds.push(bidderId);
        }

        let msg: string;
        if (lotSt.bidderIds.length >= 2 && lotSt.bidCount >= 3 && Math.random() < 0.22) {
          // Use the latest two distinct teams that actually bid, not the first two on this lot.
          const latestDistinct: string[] = [];
          for (let i = lotSt.bidHistory.length - 1; i >= 0 && latestDistinct.length < 2; i -= 1) {
            const id = lotSt.bidHistory[i];
            if (!latestDistinct.includes(id)) {
              latestDistinct.push(id);
            }
          }
          if (latestDistinct.length >= 2) {
            const a = s.teams.find((x) => x.id === latestDistinct[1])?.short_code ?? '';
            const b = s.teams.find((x) => x.id === latestDistinct[0])?.short_code ?? '';
            msg = pickCompetitiveTwoTeam(a, b);
          } else {
            msg = pickBidCommentary({
              team,
              amountLakhs: bid,
              isFirstBidOnLot: isFirstBid,
              isNewTeamOnLot: isNewTeam,
              bidCountOnLot: lotSt.bidCount,
              distinctBiddersOnLot: lotSt.bidderIds.length,
              previousBidLakhs: prevSnap.bidLakhs,
              previousBidderId: prevSnap.bidderId,
              isAiBidder: !team.is_user,
              bidderBudgetLakhs: team.budget_lakhs,
            });
          }
        } else {
          msg = pickBidCommentary({
            team,
            amountLakhs: bid,
            isFirstBidOnLot: isFirstBid,
            isNewTeamOnLot: isNewTeam,
            bidCountOnLot: lotSt.bidCount,
            distinctBiddersOnLot: lotSt.bidderIds.length,
            previousBidLakhs: prevSnap.bidLakhs,
            previousBidderId: prevSnap.bidderId,
            isAiBidder: !team.is_user,
            bidderBudgetLakhs: team.budget_lakhs,
          });
        }
        this.pushAuctionBidToast(msg, 4200);
      }
    }

    this.auctionBidSnapshot = { playerIdx: idx, bidLakhs: bid, bidderId };
  }

  private pushAuctionBidToast(message: string, durationMs = 4000) {
    const id = ++this.auctionToastSeq;
    this.auctionBidToasts = [...this.auctionBidToasts, { id, message }].slice(-5);
    this.cdr.markForCheck();
    setTimeout(() => {
      this.auctionBidToasts = this.auctionBidToasts.filter((t) => t.id !== id);
      this.cdr.markForCheck();
    }, durationMs);
  }

  isAuctionLiveOrPausedView(): boolean {
    const st = this.auctionState?.status;
    return st === 'running' || st === 'paused' || st === 'finished';
  }

  stopMiniAuction() {
    if (!this.auctionSessionId) return;
    this.auctionControlLoading = true;
    this.cricketService.stopMiniAuction(this.auctionSessionId).subscribe({
      next: (r) => {
        this.auctionState = r.state;
        this.syncAuctionUiFromState(r.state);
        this.auctionControlLoading = false;
        this.auctionError = null;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.auctionControlLoading = false;
        this.auctionError = err?.error?.error || 'Could not pause auction';
      },
    });
  }

  resumeMiniAuction() {
    if (!this.auctionSessionId) return;
    this.auctionControlLoading = true;
    this.cricketService.resumeMiniAuction(this.auctionSessionId).subscribe({
      next: (r) => {
        this.auctionState = r.state;
        this.syncAuctionUiFromState(r.state);
        this.auctionControlLoading = false;
        this.auctionError = null;
        this.startAuctionPoll();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.auctionControlLoading = false;
        this.auctionError = err?.error?.error || 'Could not resume auction';
      },
    });
  }

  restartMiniAuction() {
    if (!this.auctionSessionId) return;
    if (!confirm('Restart with a fresh player pool? Current progress will be cleared.')) {
      return;
    }
    this.auctionControlLoading = true;
    this.cricketService.restartMiniAuction(this.auctionSessionId).subscribe({
      next: (r) => {
        this.auctionState = r.state;
        this.syncAuctionUiFromState(r.state);
        this.auctionControlLoading = false;
        this.auctionBidSnapshot = null;
        this.auctionCommentaryLot = null;
        this.auctionBidToasts = [];
        this.stopAuctionPoll();
        this.auctionError = null;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.auctionControlLoading = false;
        this.auctionError = err?.error?.error || 'Could not restart auction';
      },
    });
  }

  createMiniAuctionSession() {
    this.auctionCreating = true;
    this.auctionError = null;
    const code = String(this.auctionTeamCode || '')
      .trim()
      .toUpperCase();
    this.cricketService.createMiniAuction(this.auctionLeague, code).subscribe({
      next: (res) => {
        this.auctionSessionId = res.session_id;
        sessionStorage.setItem('miniAuctionSessionId', res.session_id);
        this.auctionCreating = false;
        this.auctionState = null;
        const ut = res.user_team as { short_code?: string } | undefined;
        if (ut?.short_code) {
          this.auctionTeamCode = String(ut.short_code).toUpperCase();
        }
        this.loadAuctionPoolPreview();
        this.refreshAuctionState();
      },
      error: (err) => {
        this.auctionCreating = false;
        this.auctionError = err?.error?.error || 'Could not create auction';
      },
    });
  }

  beginMiniAuction() {
    if (!this.auctionSessionId) return;
    this.auctionLoading = true;
    this.cricketService.beginMiniAuction(this.auctionSessionId).subscribe({
      next: (r) => {
        this.auctionState = r.state;
        this.syncAuctionUiFromState(r.state);
        this.auctionLoading = false;
        this.auctionBidSnapshot = null;
        this.auctionCommentaryLot = null;
        this.auctionBidToasts = [];
        this.startAuctionPoll();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.auctionLoading = false;
        this.auctionError = err?.error?.error || 'Could not start auction';
      },
    });
  }

  placeMiniAuctionBid() {
    if (!this.auctionSessionId || !this.auctionState?.user_team_id) return;
    this.cricketService.bidMiniAuction(this.auctionSessionId, this.auctionState.user_team_id).subscribe({
      next: (s) => {
        const prev = this.auctionState;
        this.auctionState = s;
        this.syncAuctionUiFromState(s);
        this.auctionError = null;
        this.maybeCommentaryLotResolved(prev, s);
        this.maybeAuctionRunningCommentary(prev, s);
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.auctionError = err?.error?.error || err?.error?.details || 'Bid failed';
      },
    });
  }

  resetMiniAuctionSession() {
    this.stopAuctionPoll();
    sessionStorage.removeItem('miniAuctionSessionId');
    this.auctionSessionId = null;
    this.auctionState = null;
    this.auctionError = null;
    this.auctionBidSnapshot = null;
    this.auctionCommentaryLot = null;
    this.auctionBidToasts = [];
    this.loadAuctionPoolPreview();
  }

  getAuctionTeamCodes(): string[] {
    return this.auctionLeague === 'ipl' ? this.auctionIplCodes : this.auctionPslCodes;
  }

  getAuctionFranchises(): ReadonlyArray<{ code: string; name: string; accent: string }> {
    return this.auctionLeague === 'ipl' ? IPL_AUCTION_FRANCHISES : PSL_AUCTION_FRANCHISES;
  }

  getFranchiseLogoUrl(franchiseFullName: string): string {
    return resolveTeamLogoUrl(franchiseFullName);
  }

  switchAuctionLeague(l: 'ipl' | 'psl'): void {
    if (this.auctionLeague === l) {
      return;
    }
    this.auctionLeague = l;
    this.auctionTeamCode = this.getAuctionTeamCodes()[0];
    this.auctionPlayerTab = 'bat';
    this.resetMiniAuctionSession();
  }

  setAuctionPlayerTab(tab: 'bat' | 'bowl' | 'ar' | 'unsold'): void {
    this.auctionPlayerTab = tab;
  }

  selectAuctionTeamCode(code: string): void {
    this.auctionTeamCode = String(code || '')
      .trim()
      .toUpperCase();
    this.cdr.markForCheck();
  }

  /** True while session id exists but GET /state/ has not returned yet. */
  isAuctionSessionStateLoading(): boolean {
    return !!this.auctionSessionId && !this.auctionState;
  }

  /** Pick franchise + confirm — only when no session has been created. */
  isAuctionFranchisePickPhase(): boolean {
    return !this.auctionSessionId;
  }

  /** Session created, auction not started — show Start / Reset only (no re-pick grid). */
  isAuctionPendingStartPhase(): boolean {
    return !!this.auctionSessionId && this.auctionState?.status === 'setup';
  }

  /** Sync league + selected franchise from authoritative server state. */
  private syncAuctionUiFromState(s: MiniAuctionState): void {
    if (s.league === 'ipl' || s.league === 'psl') {
      this.auctionLeague = s.league;
    }
    const ut = s.teams?.find((t) => t.is_user);
    if (ut?.short_code) {
      this.auctionTeamCode = String(ut.short_code).toUpperCase();
    }
  }

  /** CSS accent for live squad tiles (same gradients as franchise cards). */
  auctionSquadAccent(shortCode: string): string {
    const c = String(shortCode || '').toUpperCase();
    const league = this.auctionState?.league ?? this.auctionLeague;
    const map = league === 'psl' ? PSL_CODE_ACCENT_MAP : IPL_CODE_ACCENT_MAP;
    return map[c] || 'neutral';
  }

  /** Full label for the user-controlled franchise (pending start / summary). */
  getUserAuctionTeamLabel(): string {
    const ut = this.auctionState?.teams?.find((t) => t.is_user);
    if (ut) {
      return `${ut.short_code} · ${ut.name}`;
    }
    return this.auctionTeamCode;
  }

  trackByAuctionFranchiseCode(_i: number, fr: { code: string }): string {
    return fr.code;
  }

  /** True when sidebar should use live session rows (not pool-preview API). */
  isAuctionSidebarFromSession(): boolean {
    const st = this.auctionState;
    return !!(st?.players && Array.isArray(st.players) && st.players.length > 0);
  }

  /** Session API included a non-empty players array (vs preview fallback). */
  hasAuctionSessionPlayerList(): boolean {
    return this.isAuctionSidebarFromSession();
  }

  getAuctionSidebarPlayersRaw(): Array<Record<string, unknown>> {
    const st = this.auctionState;
    if (st?.players && Array.isArray(st.players) && st.players.length > 0) {
      return st.players as Array<Record<string, unknown>>;
    }
    // Session exists but pool not in state (or empty): show preview so sidebar isn't blank on "Ready to start"
    if (this.auctionSessionId) {
      return this.auctionPreviewPlayers;
    }
    return this.auctionPreviewPlayers;
  }

  /** Full name of user franchise for pending-start hero. */
  getUserAuctionTeamFullName(): string {
    const ut = this.auctionState?.teams?.find((t) => t.is_user);
    return ut?.name || '';
  }

  accentForUserAuctionTeam(): string {
    const ut = this.auctionState?.teams?.find((t) => t.is_user);
    const code = ut?.short_code || this.auctionTeamCode;
    return this.auctionSquadAccent(code);
  }

  loadAuctionPoolPreview(): void {
    this.auctionPreviewLoading = true;
    this.auctionPreviewError = null;
    this.cricketService.getMiniAuctionPoolPreview(this.auctionLeague).subscribe({
      next: (res) => {
        this.auctionPreviewPlayers = res.players as Array<Record<string, unknown>>;
        this.auctionPreviewLoading = false;
      },
      error: (err) => {
        this.auctionPreviewError = err?.error?.error || 'Could not load player pool from server';
        this.auctionPreviewPlayers = [];
        this.auctionPreviewLoading = false;
      },
    });
  }

  getAuctionUnsoldPlayers(): Array<Record<string, unknown>> {
    const st = this.auctionState;
    if (!st?.players || !Array.isArray(st.players)) {
      return [];
    }
    return (st.players as Array<Record<string, unknown>>).filter(
      (p) => String(p['status'] ?? '') === 'unsold',
    );
  }

  getAuctionUnsoldCount(): number {
    return this.getAuctionUnsoldPlayers().length;
  }

  getFilteredAuctionSidebarPlayers(): Array<Record<string, unknown>> {
    const tab = this.auctionPlayerTab;
    if (tab === 'unsold') {
      return this.getAuctionUnsoldPlayers();
    }
    return this.getAuctionSidebarPlayersRaw().filter((p) => {
      const c = String(p['category'] ?? '');
      if (tab === 'bat') {
        return c === 'Batsman' || c === 'WK';
      }
      if (tab === 'bowl') {
        return c === 'Bowler';
      }
      return c === 'All-rounder';
    });
  }

  formatAuctionBaseCr(lakhs: number | string | undefined | null): string {
    const n = Number(lakhs);
    if (!Number.isFinite(n) || n <= 0) {
      return '—';
    }
    const cr = n / 100;
    if (cr >= 1) {
      return `${cr.toFixed(2)} CR`;
    }
    return `${Math.round(n)} L`;
  }

  auctionPlayerAvatarUrl(name: string): string {
    const safe = encodeURIComponent((name || 'Player').slice(0, 48));
    return `https://ui-avatars.com/api/?name=${safe}&background=1e293b&color=fbbf24&size=96&rounded=true`;
  }

  auctionPlayerSubtitle(pl: Record<string, unknown>): string {
    const st = String(pl['status'] ?? '');
    const cat = String(pl['category'] ?? 'Player');
    const league = this.auctionLeague === 'psl' ? 'PSL' : 'IPL';
    if (st === 'sold') {
      return `Sold · ${league}`;
    }
    if (st === 'unsold') {
      return `Unsold · ${cat}`;
    }
    if (st === 'pending') {
      return `Awaiting lot · ${cat}`;
    }
    const role =
      cat === 'WK'
        ? 'Wicketkeeper'
        : cat === 'Batsman'
          ? 'Top-order batter'
          : cat === 'Bowler'
            ? 'Bowler'
            : cat === 'All-rounder'
              ? 'All-rounder'
              : cat;
    return `${role} · ${league} pool`;
  }

  openRankingsTab(tab: 'team' | 'batter' | 'bowler' | 'allrounder') {
    this.headerSubTab = tab;
    const kind: RankingKind =
      tab === 'team' ? 'teams' :
      tab === 'batter' ? 'batsmen' :
      tab === 'bowler' ? 'bowlers' : 'allrounders';
    this.loadRankings(kind);
  }

  private loadRankings(kind: RankingKind) {
    this.rankingsLoading = true;
    this.cricketService.getRankings(kind).subscribe({
      next: (data) => {
        if (kind === 'teams') this.rankingsTeams = data;
        else if (kind === 'batsmen') this.rankingsBatsmen = data;
        else if (kind === 'bowlers') this.rankingsBowlers = data;
        else this.rankingsAllRounders = data;
        this.rankingsLoading = false;
      },
      error: (err) => {
        console.error('Rankings error:', err);
        this.rankingsLoading = false;
      }
    });
  }

  getRankingsTitle(): string {
    if (this.headerSubTab === 'team') return "Men's Teams Ranking";
    if (this.headerSubTab === 'batter') return "Men's Batters Ranking";
    if (this.headerSubTab === 'bowler') return "Men's Bowlers Ranking";
    return "Men's All Rounders Ranking";
  }

  getActiveRankings(): RankingsResponse<any> | null {
    if (this.headerSubTab === 'team') return this.rankingsTeams;
    if (this.headerSubTab === 'batter') return this.rankingsBatsmen;
    if (this.headerSubTab === 'bowler') return this.rankingsBowlers;
    return this.rankingsAllRounders;
  }

  /** ISO timestamp when rankings were last synced from RapidAPI (backend). */
  getRankingsFetchedAt(): string {
    const r = this.getActiveRankings();
    const raw = r && (r as RankingsResponse<any>).fetched_at;
    if (!raw || typeof raw !== 'string') return '';
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleString();
  }

  isTeamRankings(): boolean {
    return this.headerSubTab === 'team';
  }

  formatNewsDate(iso: string | null | undefined): string {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleString();
  }

  setLeague(series: Series | null) {
    if (series && this.isIccMensT20WorldCupSeries(series.name)) {
      this.selectedLeagueType = 'wc';
    } else {
      this.selectedLeagueType = series ? 'series' : 'all';
    }
    this.selectedLeagueId = series?.external_id || '';
    this.leagueSubTab = 'matches';
    this.wcPointsStage = 'group';
  }

  selectIPLLeague() {
    this.selectedLeagueType = 'ipl';
    this.selectedLeagueId = '';
    this.leagueSubTab = 'matches';
    this.wcPointsStage = 'group';
  }

  selectPSLLeague() {
    this.selectedLeagueType = 'psl';
    this.selectedLeagueId = '';
    this.leagueSubTab = 'matches';
    this.wcPointsStage = 'group';
  }

  selectBBLLeague() {
    this.selectedLeagueType = 'bbl';
    this.selectedLeagueId = '';
    this.leagueSubTab = 'matches';
    this.wcPointsStage = 'group';
  }

  setLeagueSubTab(tab: 'matches' | 'points' | 'stats') {
    this.leagueSubTab = tab;
    if (tab === 'stats' && this.selectedLeagueType === 'bbl') {
      this.loadBblStatsIfNeeded();
    }
    if (tab === 'points' && (this.selectedLeagueType === 'ipl' || this.selectedLeagueType === 'psl')) {
      this.loadLeagueStandingsIfNeeded(this.selectedLeagueType);
    }
    if (tab !== 'stats') {
      // keep already loaded data; just stop showing loader
      this.bblStatsLoading = false;
    }
  }

  loadLeagueStandingsIfNeeded(league: 'ipl' | 'psl'): void {
    this.leagueStandingsLoading = true;
    this.leagueStandingsError = null;
    this.cricketService.getLeagueStandings(league).subscribe({
      next: (data) => {
        const rows = data?.rows || [];
        if (league === 'ipl') {
          this.leagueStandingsIpl = rows;
          this.leagueStandingsTitleIpl = (data?.series_name || '').trim();
        } else {
          this.leagueStandingsPsl = rows;
          this.leagueStandingsTitlePsl = (data?.series_name || '').trim();
        }
        this.leagueStandingsLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.leagueStandingsLoading = false;
        this.leagueStandingsError = err?.error?.error || 'Failed to load standings';
        this.cdr.markForCheck();
      },
    });
  }

  getSidebarSeries(): Series[] {
    // IPL/PSL/BBL have dedicated top-league buttons; hide duplicate rows.
    return (this.masterData || []).filter((s) => {
      const n = s?.name || '';
      return !this.isIplMasterSeriesName(n) && !this.isPslMasterSeriesName(n) && !this.isBblSeries(n);
    });
  }

  private isMainTrackedSeriesName(name: string | null | undefined): boolean {
    const n = String(name || '').toLowerCase();
    const isMainWc = /icc\s*men'?s\s*t20\s*world\s*cup\s*2026/.test(n);
    return this.isIplMasterSeriesName(n) || this.isPslMasterSeriesName(n) || this.isBblSeries(n) || isMainWc;
  }

  private loadBblStatsIfNeeded() {
    if (this.bblStatsLoading) return;
    if (this.bblStatsData) return;

    this.bblStatsLoading = true;
    this.bblStatsError = null;

    this.cricketService.getBblStats().subscribe({
      next: (resp) => {
        this.bblStatsData = resp?.data || null;
        this.bblStatsLoading = false;
      },
      error: (err) => {
        this.bblStatsError = err?.error?.error || 'Failed to load BBL stats';
        this.bblStatsLoading = false;
      },
    });
  }

  /** Center list series based on selected league and active tab rules. */
  getVisibleSeries(): Series[] {
    // For special leagues (IPL/PSL/BBL) we show a custom center layout, not series cards.
    if (this.selectedLeagueType === 'ipl' || this.selectedLeagueType === 'psl' || this.selectedLeagueType === 'bbl' || this.selectedLeagueType === 'wc') {
      return [];
    }

    // Start from full master data
    let base = this.masterData;
    if (this.selectedLeagueType === 'all') {
      base = base.filter((s) => this.isMainTrackedSeriesName(s?.name));
    }
    if (this.selectedLeagueType === 'series' && this.selectedLeagueId) {
      base = base.filter(s => s.external_id === this.selectedLeagueId);
    }

    if (this.activeTab === 'all') {
      return base
        .map(series => ({
          ...series,
          matches: this.sortLeagueCompletedByRecentDateDesc(
            (series.matches || []).filter(m => !String(m?.status || '').toLowerCase().includes('match starts at')),
          ),
        }))
        .filter(series => series.matches.length > 0);
    }
    if (this.activeTab === 'live') {
      // live tab is handled separately in template
      return base;
    }
    return base
      .map(series => ({
        ...series,
        matches: this.sortLeagueCompletedByRecentDateDesc(
          series.matches.filter(m => {
            const mStatus = (m.status || '').toLowerCase();
            if (this.activeTab === 'results') return mStatus === 'completed' || mStatus === 'result';
            return mStatus === this.activeTab;
          }),
        ),
      }))
      .filter(series => series.matches.length > 0);
  }

  /** Finished live matches should appear only in All + Results. */
  getFinishedLiveResultsVisible(): LiveMatch[] {
    if (this.activeTab === 'all' || this.activeTab === 'results') {
      const rows =
        this.selectedLeagueType === 'all'
          ? (this.liveResults || []).filter((m) => this.isMainTrackedSeriesName(m?.name))
          : this.liveResults || [];
      return this.sortLeagueCompletedByRecentDateDesc(rows);
    }
    return [];
  }

  /** Live matches only appear in Live tab. */
  getLiveMatchesVisible(): LiveMatch[] {
    if (this.activeTab !== 'live') return [];
    return this.liveMatches;
  }

  /** Upcoming tab uses upcomingMatches list only. */
  getUpcomingMatchesVisible(): UpcomingMatch[] {
    if (this.activeTab !== 'upcoming') return [];
    return this.upcomingMatches;
  }

  getIplFixtures(): UpcomingMatch[] {
    return this.upcomingMatches.filter(m => {
      const s = (m.series_name || '').toLowerCase();
      if (s.includes('indian premier league')) return true;
      // Cricbuzz sometimes leaves series_name blank; both teams are IPL franchises.
      return !!(this.getIplTeamCode(m.team_home) && this.getIplTeamCode(m.team_away));
    });
  }

  getPslFixtures(): UpcomingMatch[] {
    return this.upcomingMatches.filter(m => {
      const s = (m.series_name || '').toLowerCase();
      if (s.includes('pakistan super league')) return true;
      return !!(this.getPslTeamKey(m.team_home) && this.getPslTeamKey(m.team_away));
    });
  }

  /** Series `name` from main matches API (CricAPI sync), for IPL league cards. */
  isIplMasterSeriesName(name: string | null | undefined): boolean {
    return (name || '').toLowerCase().includes('indian premier league');
  }

  isPslMasterSeriesName(name: string | null | undefined): boolean {
    return (name || '').toLowerCase().includes('pakistan super league');
  }

  getIplMasterSeriesLabel(): string {
    for (const s of this.masterData) {
      if (this.isIplMasterSeriesName(s.name)) return s.name || 'Indian Premier League';
    }
    return 'Indian Premier League';
  }

  getPslMasterSeriesLabel(): string {
    for (const s of this.masterData) {
      if (this.isPslMasterSeriesName(s.name)) return s.name || 'Pakistan Super League';
    }
    return 'Pakistan Super League';
  }

  private isFinishedLeagueMatchStatus(status: string | null | undefined): boolean {
    const t = (String(status || '').toLowerCase());
    if (!t) return false;
    if (t.includes('live')) return false;
    if (t.includes('not started') || t.includes('scheduled') || t === 'upcoming' || t.includes('yet to begin')) {
      return false;
    }
    return (
      t.includes('won')
      || t === 'completed'
      || t === 'result'
      || t.includes('tie')
      || t.includes('no result')
      || t.includes('abandon')
    );
  }

  isFinishedStatusText(status: string | null | undefined): boolean {
    const t = String(status || '').toLowerCase();
    if (!t) return false;
    if (t.includes('live')) return false;
    if (
      t.includes('not started')
      || t.includes('scheduled')
      || t === 'upcoming'
      || t.includes('yet to begin')
      || t.includes('match starts at')
    ) {
      return false;
    }
    return (
      t.includes('won')
      || t === 'completed'
      || t === 'result'
      || t.includes('tie')
      || t.includes('no result')
      || t.includes('abandon')
    );
  }

  getIplCompletedMatches(): Match[] {
    for (const s of this.masterData) {
      if (!this.isIplMasterSeriesName(s.name) || !s.matches?.length) continue;
      return this.sortLeagueCompletedByRecentDateDesc(
        s.matches.filter(m => this.isFinishedLeagueMatchStatus(m.status)),
      );
    }
    return [];
  }

  getPslCompletedMatches(): Match[] {
    for (const s of this.masterData) {
      if (!this.isPslMasterSeriesName(s.name) || !s.matches?.length) continue;
      return this.sortLeagueCompletedByRecentDateDesc(
        s.matches.filter(m => this.isFinishedLeagueMatchStatus(m.status)),
      );
    }
    return [];
  }

  /** Finished matches for league pages (from live-results feed). */
  getIplFinishedLiveResults(): LiveMatch[] {
    return this.sortLeagueCompletedByRecentDateDesc(
      (this.liveResults || []).filter(m => {
        if (!(m?.name || '').toLowerCase().includes('indian premier league')) return false;
        return !!(m.is_finished || this.isFinishedStatusText(m?.status));
      }),
    );
  }

  getPslFinishedLiveResults(): LiveMatch[] {
    return this.sortLeagueCompletedByRecentDateDesc(
      (this.liveResults || []).filter(m => {
        if (!(m?.name || '').toLowerCase().includes('pakistan super league')) return false;
        return !!(m.is_finished || this.isFinishedStatusText(m?.status));
      }),
    );
  }

  iplPslMatchesTabIsEmpty(): boolean {
    if (this.selectedLeagueType === 'ipl') {
      return !this.getIplFinishedLiveResults().length && !this.getIplCompletedMatches().length && !this.getIplFixtures().length;
    }
    if (this.selectedLeagueType === 'psl') {
      return !this.getPslFinishedLiveResults().length && !this.getPslCompletedMatches().length && !this.getPslFixtures().length;
    }
    return false;
  }

  getBblFixtures(): UpcomingMatch[] {
    return this.upcomingMatches.filter(
      m => (m.series_name || '').toLowerCase().includes('big bash league'),
    );
  }

  /** BBL matches from main matches API (completed season), for league Matches tab. */
  getBblSeriesMatches(): Match[] {
    for (const s of this.masterData) {
      if (this.isBblSeries(s.name) && s.matches?.length) {
        return s.matches.slice().sort((a, b) => {
          const an = this.parseBblMatchNumber(a?.name);
          const bn = this.parseBblMatchNumber(b?.name);
          if (an != null && bn != null) return an - bn;
          if (an != null) return -1;
          if (bn != null) return 1;
          // Fallback stable sort by external_id numeric if possible.
          const ae = Number(String(a?.external_id || '').replace(/\D+/g, ''));
          const be = Number(String(b?.external_id || '').replace(/\D+/g, ''));
          if (Number.isFinite(ae) && Number.isFinite(be)) return ae - be;
          return String(a?.external_id || '').localeCompare(String(b?.external_id || ''));
        });
      }
    }
    return [];
  }

  getWorldCupSeriesMatches(): Match[] {
    for (const s of this.masterData) {
      if (this.isIccMensT20WorldCupSeries(s.name) && s.matches?.length) {
        return s.matches.slice().sort((a, b) => {
          const an = this.parseWcMatchNumber(a?.name);
          const bn = this.parseWcMatchNumber(b?.name);
          if (an != null && bn != null) return an - bn;
          if (an != null) return -1;
          if (bn != null) return 1;
          return String(a?.external_id || '').localeCompare(String(b?.external_id || ''));
        });
      }
    }
    return [];
  }

  private parseBblMatchNumber(name: string | null | undefined): number | null {
    const s = String(name || '').trim().toLowerCase();
    // Examples: "1st Match", "2nd Match", "3rd Match", "10th Match"
    const m = s.match(/(\d+)\s*(st|nd|rd|th)?\s*match\b/);
    if (!m) return null;
    const n = Number(m[1]);
    if (!Number.isFinite(n)) return null;
    return n;
  }

  private parseMatchDateStringToMs(value: string | null | undefined): number {
    const s = String(value || '').trim();
    if (!s) return 0;
    const t = Date.parse(s);
    if (!Number.isNaN(t)) return t;
    const dmy = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
    if (dmy) {
      const ms = Date.UTC(Number(dmy[3]), Number(dmy[2]) - 1, Number(dmy[1]));
      return Number.isNaN(ms) ? 0 : ms;
    }
    return 0;
  }

  /** CricAPI titles often end with "Apr 04, 2026" or include ISO dates. */
  private extractDateCandidateFromMatchName(name: string | null | undefined): string {
    const s = String(name || '');
    const iso = s.match(/\b(\d{4}-\d{2}-\d{2})\b/);
    if (iso) return iso[1];
    const months = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec';
    const re = new RegExp(`\\b(\\d{1,2})\\s+(${months})[a-z]*\\s*,?\\s*(\\d{4})\\b`, 'gi');
    let last = '';
    let m: RegExpExecArray | null;
    while ((m = re.exec(s)) !== null) {
      last = `${m[1]} ${m[2]} ${m[3]}`;
    }
    return last;
  }

  /** Prefer scorecard date, then parsed title date, then match number / id (newest-first sort). */
  private getLeagueCompletedMatchSortTimeMs(m: Match | LiveMatch): number {
    const scDate = (m as any)?.scorecard_data?.date;
    let ms = this.parseMatchDateStringToMs(scDate);
    if (ms) return ms;
    ms = this.parseMatchDateStringToMs(this.extractDateCandidateFromMatchName(m.name));
    if (ms) return ms;
    ms = this.parseMatchDateStringToMs(m.name);
    if (ms) return ms;
    const n = this.parseBblMatchNumber(m.name);
    if (n != null) return n;
    const ext = Number(String((m as any)?.external_id || '').replace(/\D+/g, ''));
    return Number.isFinite(ext) ? ext : 0;
  }

  private sortLeagueCompletedByRecentDateDesc<T extends Match | LiveMatch>(rows: T[]): T[] {
    return rows.slice().sort((a, b) => {
      const tb = this.getLeagueCompletedMatchSortTimeMs(b);
      const ta = this.getLeagueCompletedMatchSortTimeMs(a);
      if (tb !== ta) return tb - ta;
      return String(b.external_id || '').localeCompare(String(a.external_id || ''));
    });
  }

  private parseWcMatchNumber(name: string | null | undefined): number | null {
    const s = String(name || '').trim().toLowerCase();
    const m = s.match(/(\d+)\s*(st|nd|rd|th)?\s*match\b/);
    if (!m) return null;
    const n = Number(m[1]);
    if (!Number.isFinite(n)) return null;
    return n;
  }

  getWcMatchHeader(match: Match): string {
    const n = this.parseWcMatchNumber(match?.name || '');
    if (n == null) return '';
    return `t20, ${n} of 44`;
  }

  getWcMatchCardTitle(match: Match): string {
    const scName = String(((match as any)?.scorecard_data?.name || '')).trim();
    const raw = scName || String(match?.name || '').trim();
    if (!raw) return '';
    // Remove trailing tournament part from title.
    // Example:
    // "Pakistan vs Netherlands, 1st Match, Group A, ICC Men's T20 World Cup 2026"
    // -> "Pakistan vs Netherlands, 1st Match, Group A"
    return raw
      .replace(/,\s*icc\s*men'?s\s*t20\s*world\s*cup.*$/i, '')
      .trim();
  }

  /** Adapt live-feed row for helpers that expect `Match` + optional `scorecard_data`. */
  liveMatchAsMatch(m: LiveMatch): Match {
    return {
      external_id: m.external_id,
      name: m.name,
      status: m.status,
      team_home: m.team_home,
      team_away: m.team_away,
      home_score: m.home_score,
      away_score: m.away_score,
      scorecard_data: m.scorecard_data as any,
      from_live_feed: true,
      is_finished: m.is_finished === true,
    };
  }

  /** Match Reports on dashboard cards: hide for live-feed rows until the match is completed. */
  showLiveFeedMatchReportButton(isLiveFeed: boolean, match: Match | LiveMatch): boolean {
    if (!isLiveFeed) return true;
    const m = match as LiveMatch & Match;
    if (m.is_finished === true) return true;
    return this.isFinishedStatusText(m.status);
  }

  goToLiveMatches(): void {
    this.setLeague(null);
    this.applyFilter('live');
    setTimeout(() => {
      document.getElementById('crex-live-matches-anchor')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }, 120);
  }

  private isLiveFeedBblName(name: string | null | undefined): boolean {
    return /\bbig\s*bash\b/i.test(String(name || ''));
  }

  getLiveFeedSeriesLabelForActions(m: LiveMatch): string {
    if (this.isIccMensT20WorldCupSeries(m.name)) return "ICC Men's T20 World Cup 2026";
    if (this.isLiveFeedBblName(m.name)) return 'Big Bash League 2025-26';
    return '';
  }

  getDashboardLiveFeedCardTitle(m: LiveMatch): string {
    const mm = this.liveMatchAsMatch(m);
    if (this.isIccMensT20WorldCupSeries(m.name)) return this.getWcMatchCardTitle(mm) || m.name || '';
    if (this.isLiveFeedBblName(m.name)) return this.getBblVenueForMatch(mm) || m.name || '';
    return this.getMatchVenueFromScorecard(mm) || m.name || '';
  }

  getSeriesScoreCardTitle(match: Match, seriesName: string): string {
    if (this.isIccMensT20WorldCupSeries(seriesName)) return this.getWcMatchCardTitle(match) || match.name || '';
    if (this.isBblSeries(seriesName)) return this.getBblVenueForMatch(match) || match.name || '';
    return this.getMatchVenueFromScorecard(match) || match.name || '';
  }

  openDashboardSeriesMatch(match: Match, seriesName: string): void {
    this.openDashboardMatchCentre(match, seriesName, false);
  }

  /** Home dashboard scored cards → full match centre (live feed or series). */
  openDashboardMatchCentre(match: Match | LiveMatch, seriesName: string, isLiveFeed: boolean, ev?: Event): void {
    if (ev) ev.stopPropagation();
    if (isLiveFeed) {
      this.openLiveFeedMatchCentre(match as LiveMatch);
      return;
    }
    const m = match as Match;
    if (!m.external_id) return;
    if (this.isBblSeries(seriesName)) this.openBblMatchCentre(m, seriesName);
    else if (this.isIccMensT20WorldCupSeries(seriesName)) this.openWorldCupMatchCentre(m, seriesName);
    else this.openGenericMatchCentre(m, seriesName);
  }

  /** Match centre for a row from the live / recent-live-results API. */
  openLiveFeedMatchCentre(m: LiveMatch): void {
    this.closeHighlights();
    this.selectedBblMatch = null;
    const finished = !!m.is_finished;
    // Always use live-matches scorecard URL for feed rows: finished games are served from
    // LiveMatch.scorecard_data in the DB; the matches/ API often has no row for the same id.
    this.matchCentreUseLiveScorecardApi = true;
    this.matchCentreAllowScorecardTab = true;
    // Keep Build XI enabled for completed IPL/PSL matches opened from the live-results feed.
    this.matchCentreHideBuildXiTab = !(
      this.isIplMasterSeriesName(m.name) || this.isPslMasterSeriesName(m.name)
    );
    const mm = this.liveMatchAsMatch(m);
    this.selectedUpcoming = {
      external_id: m.external_id,
      team_home: m.team_home,
      team_away: m.team_away,
      series_name: this.getLiveFeedSeriesLabelForActions(m) || 'Live match',
      venue: this.getMatchVenueFromScorecard(mm) || this.getDashboardLiveFeedCardTitle(m) || m.name || '',
      status: m.status,
      start_time_utc: '',
      date_ist: this.getMatchDateFromScorecard(mm) || '',
      time_ist: '',
    } as UpcomingMatch;
    this.headerPage = 'matchcentre';
    this.matchCentreTab = 'scorecard';
    this.resetMatchCentrePanelsForScorecard();

    if (finished && this.isUsableEmbeddedScorecard(m.scorecard_data)) {
      this.matchCentreScorecardData = m.scorecard_data as Scorecard;
      this.matchCentreScorecardLoading = false;
      this.matchCentreScorecardError = null;
      return;
    }

    this.loadMatchCentreScorecardIfNeeded();
  }

  /** Match centre for completed/other series matches (not BBL/WC helpers). */
  openGenericMatchCentre(match: Match, seriesName: string): void {
    this.closeHighlights();
    this.selectedBblMatch = null;
    this.matchCentreUseLiveScorecardApi = false;
    this.matchCentreAllowScorecardTab = true;
    // Keep Build XI enabled for completed IPL/PSL matches.
    this.matchCentreHideBuildXiTab = !(
      this.isIplMasterSeriesName(seriesName) || this.isPslMasterSeriesName(seriesName)
    );
    this.selectedUpcoming = {
      external_id: match.external_id,
      team_home: match.team_home,
      team_away: match.team_away,
      series_name: seriesName,
      venue: this.getMatchVenueFromScorecard(match) || match.name || '',
      status: match.status,
      start_time_utc: '',
      date_ist: this.getMatchDateFromScorecard(match) || '',
      time_ist: '',
    } as UpcomingMatch;
    this.headerPage = 'matchcentre';
    this.matchCentreTab = 'scorecard';
    this.resetMatchCentrePanelsForScorecard();
    this.loadMatchCentreScorecardIfNeeded();
  }

  private resetMatchCentrePanelsForScorecard(): void {
    this.matchCentreTeamA = null;
    this.matchCentreTeamB = null;
    this.matchCentreComparisonLoading = false;
    this.matchCentreH2H = null;
    this.matchCentreH2HLoading = false;
    this.matchCentreFormA = null;
    this.matchCentreFormB = null;
    this.matchCentreFormLoading = false;
    this.matchCentreSquadLoading = false;
    this.matchCentreSquadA = null;
    this.matchCentreSquadB = null;
    this.matchCentreScorecardData = null;
    this.matchCentreScorecardError = null;
    this.matchCentreScorecardLoading = false;
    this.matchCentreSelectedBblInningsIdx = 0;
    this.matchCentreXISelected = [];
    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;
    this.matchCentreXIFantasyConfirmed = false;
    this.matchCentreXICaptainKey = null;
    this.matchCentreXIWkKey = null;
    this.matchCentreXIScreenshotLoading = false;
    this.matchCentreXIImpactKey = null;
    if (this.matchCentreTicker) {
      clearInterval(this.matchCentreTicker);
      this.matchCentreTicker = null;
    }
  }

  dashboardUseBblLayout(match: Match | LiveMatch, seriesName: string, isLiveFeed: boolean): boolean {
    if (isLiveFeed) return this.isLiveFeedBblName((match as LiveMatch).name);
    return this.isBblSeries(seriesName);
  }

  dashboardIsWcContext(match: Match | LiveMatch, seriesName: string, isLiveFeed: boolean): boolean {
    if (isLiveFeed) return this.isIccMensT20WorldCupSeries((match as LiveMatch).name);
    return this.isIccMensT20WorldCupSeries(seriesName);
  }

  dashboardMatchAdapter(match: Match | LiveMatch, isLiveFeed: boolean): Match {
    return isLiveFeed ? this.liveMatchAsMatch(match as LiveMatch) : (match as Match);
  }

  dashboardReportSeriesName(match: Match | LiveMatch, seriesName: string, isLiveFeed: boolean): string {
    if (isLiveFeed) return this.getLiveFeedSeriesLabelForActions(match as LiveMatch);
    return seriesName || '';
  }

  getBblMatchHeader(): string {
    const n = this.parseBblMatchNumber(this.selectedBblMatch?.name || '');
    if (n == null) return '';
    if (n === 44) return `final t20 ${n} of 44`;
    if (n >= 41) return `play-off t20 ${n} of 44`;
    return `t20 ${n} of 44`;
  }

  private getBblVenueForMatch(match: Match): string {
    const n = this.parseBblMatchNumber(match?.name || '');
    if (n == null) return this.getMatchVenueFromScorecard(match) || match.name || '';
    return this.bblVenueByMatchNumber[n] || this.getMatchVenueFromScorecard(match) || match.name || '';
  }

  isBblSeries(name: string | null | undefined): boolean {
    const n = (name || '').toLowerCase();
    return n.includes('big bash league');
  }

  getUpcomingGroupedByDate(): { date: string; matches: UpcomingMatch[] }[] {
    const rows = this.getUpcomingMatchesVisible().slice().sort((a, b) => {
      return new Date(a.start_time_utc).getTime() - new Date(b.start_time_utc).getTime();
    });
    const out: { date: string; matches: UpcomingMatch[] }[] = [];
    for (const m of rows) {
      const date = m.date_ist || '';
      const last = out[out.length - 1];
      if (!last || last.date !== date) out.push({ date, matches: [m] });
      else last.matches.push(m);
    }
    return out;
  }

  // Helper to count matches for the tab badges
  getMatchCount(status: string): number {
    if (status === 'live') {
      return this.liveMatches.length;
    }
    let count = 0;
    this.masterData.forEach(s => {
      s.matches.forEach(m => {
        const mStatus = m.status.toLowerCase();
        if (status === 'all') count++;
        else if (status === 'results' && (mStatus === 'completed' || mStatus === 'result')) count++;
        else if (mStatus === status) count++;
      });
    });
    if (status === 'results') {
      count += this.liveResults.length;
    }
    return count;
  }

  isSeriesCollapsed(series: Series): boolean {
    return this.collapsedSeries.has(series.external_id || series.name);
  }

  toggleSeries(series: Series) {
    const key = series.external_id || series.name;
    if (this.collapsedSeries.has(key)) this.collapsedSeries.delete(key);
    else this.collapsedSeries.add(key);
  }

  getSeriesFlag(name: string): string {
    const n = (name || '').toLowerCase();
    // Explicit mappings per your requirement
    if (n.includes('sa20') || n.includes('south africa')) return '🇿🇦';
    if (n.includes('women') || n.includes('wpl') || n.includes("women's premier league")) return '🇮🇳';
    if (n.includes('india')) return '🇮🇳';
    if (n.includes('australia') || n.includes('bbl')) return '🇦🇺';
    if (n.includes('pakistan') || n.includes('psl')) return '🇵🇰';
    if (n.includes('england') || n.includes('the hundred')) return '🏴';
    return '🏏';
  }

  getSeriesSubtitle(name: string): string {
    const n = (name || '').toLowerCase();
    if (n.includes('league')) return 'League';
    if (n.includes('t20')) return "T20";
    return 'Series';
  }

  getTabDotClass(tab: string): string {
    if (tab === 'live') return 'dot-live';
    if (tab === 'upcoming') return 'dot-upcoming';
    if (tab === 'results') return 'dot-results';
    return 'dot-all';
  }

  getTeamLogoUrl(teamName: string): string {
    // Use the same display normalization for logos, so "Pakistan,Namibia" uses Namibia flag.
    return resolveTeamLogoUrl(this.getDisplayTeamName(teamName));
  }

  /** Map franchise code to a name string that team-logos rules resolve (e.g. DC → Delhi Capitals). */
  leaderboardFranchiseNameForLogo(code: string, league: 'ipl' | 'psl'): string {
    const c = String(code || '').trim().toUpperCase();
    const ipl: Record<string, string> = {
      CSK: 'Chennai Super Kings',
      DC: 'Delhi Capitals',
      SRH: 'Sunrisers Hyderabad',
      MI: 'Mumbai Indians',
      RCB: 'Royal Challengers Bengaluru',
      PBKS: 'Punjab Kings',
      RR: 'Rajasthan Royals',
      KKR: 'Kolkata Knight Riders',
      GT: 'Gujarat Titans',
      LSG: 'Lucknow Super Giants',
    };
    const psl: Record<string, string> = {
      IU: 'Islamabad United',
      MS: 'Multan Sultans',
      QG: 'Quetta Gladiators',
      KK: 'Karachi Kings',
      LQ: 'Lahore Qalandars',
      PZ: 'Peshawar Zalmi',
    };
    const m = league === 'ipl' ? ipl : psl;
    return m[c] || c;
  }

  isFallbackLogo(teamName: string): boolean {
    const url = this.getTeamLogoUrl(teamName);
    return !url || url === FALLBACK_LOGO;
  }

  getInitials(teamName: string): string {
    const n = this.getDisplayTeamName(teamName);
    if (!n) return '?';
    const parts = n.split(/\s+/).filter(Boolean);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  /** Show "Italy" instead of "England,Italy" etc. when API returns concatenated names. */
  getDisplayTeamName(teamName: string): string {
    const n = (teamName || '').trim();
    if (/^england,?\s*italy$/i.test(n)) return 'Italy';
    if (/^italy,?\s*england$/i.test(n)) return 'England';
    // Generic: if backend sends "A,B" show only the second team (B)
    if (n.includes(',')) {
      const parts = n.split(',').map(p => p.trim()).filter(Boolean);
      if (parts.length >= 2) return parts[parts.length - 1];
    }
    return n || '';
  }

  onTeamLogoError(ev: Event) {
    const img = ev.target as HTMLImageElement | null;
    if (!img) return;
    img.onerror = null;
    img.src = getFallbackTeamLogoUrl();
  }

  openScorecard(match: Match) {
    const matchId = match.external_id;
    if (!matchId) return;
    this.selectedMatch = match;
    this.scorecardModalOpen = true;
    this.scorecardData = null;
    this.scorecardError = null;
    this.scorecardLoading = true;
    this.cricketService.getScorecard(matchId).subscribe({
      next: (data) => {
        this.scorecardData = data;
        this.scorecardLoading = false;
      },
      error: (err) => {
        this.scorecardError = err?.error?.error || 'Failed to load scorecard';
        this.scorecardLoading = false;
      }
    });
  }

  getScorecardTitle(match: Match | null): string {
    if (!match?.team_home && !match?.team_away) return '';
    return [match.team_home, match.team_away].filter(Boolean).join(' vs ');
  }

  private enrichScorecardFromMatch(sc: any, match: Match): any {
    if (!sc) return sc;
    const out = { ...sc };
    if (!(out.name || '').trim() && (match?.team_home || match?.team_away)) {
      const parts = [match.team_home || '', match.team_away || ''].filter(Boolean);
      out.name = parts.join(' vs ') || (match.name || '');
    }
    if (!(out.name || '').trim() && match?.name) out.name = match.name;
    return out;
  }

  openLiveScorecard(match: LiveMatch) {
    const matchId = match.external_id;
    if (!matchId) return;
    // Reuse same modal + scorecard state
    this.selectedMatch = {
      external_id: match.external_id,
      name: match.name,
      status: match.status,
      team_home: match.team_home,
      team_away: match.team_away,
      home_score: match.home_score,
      away_score: match.away_score,
    };
    this.scorecardModalOpen = true;
    this.scorecardData = null;
    this.scorecardError = null;
    this.scorecardLoading = true;
    this.cricketService.getLiveScorecard(matchId).subscribe({
      next: (data) => {
        this.scorecardData = data;
        this.scorecardLoading = false;
      },
      error: (err) => {
        this.scorecardError = err?.error?.error || 'Failed to load scorecard';
        this.scorecardLoading = false;
      }
    });
  }

  closeScorecard() {
    this.scorecardModalOpen = false;
    this.scorecardData = null;
    this.selectedMatch = null;
    this.scorecardError = null;
  }

  openMatchReport(match: Match, seriesName: string = '') {
    if (match.from_live_feed && !this.showLiveFeedMatchReportButton(true, match)) {
      return;
    }
    this.closeHighlights();
    const matchId = (match as any)?.external_id;
    this.selectedWorldCupReport = match;
    this.matchReportData = null;
    this.matchReportError = null;
    this.matchReportEssayTitle = '';
    this.matchReportEssayDateLine = '';
    this.matchReportEssayParagraphs = [];
    this.matchReportLoading = true;
    this.headerPage = 'matchreport';

    // Stop match-centre ticker if the user was previously there.
    if (this.matchCentreTicker) {
      clearInterval(this.matchCentreTicker);
      this.matchCentreTicker = null;
    }

    const cached: Scorecard | undefined = (match as any)?.scorecard_data as Scorecard | undefined;
    if (cached && (cached.scorecard?.length || cached.score?.length)) {
      this.matchReportData = cached;
      this.matchReportLoading = false;
      this.buildWorldCupMatchEssay(match, cached, seriesName);
      return;
    }

    // Fallback: load scorecard from API if cache isn't present.
    if (!matchId) {
      if (this.isInterruptedMatchStatus(match?.status || '')) {
        this.buildAbandonedMatchFallbackEssay(match, seriesName);
        this.matchReportLoading = false;
      } else {
        this.matchReportError = 'Scorecard not available for this match.';
        this.matchReportLoading = false;
      }
      return;
    }

    this.cricketService.getScorecard(matchId).subscribe({
      next: (data) => {
        this.matchReportData = data;
        this.matchReportLoading = false;
        this.buildWorldCupMatchEssay(match, data, seriesName);
      },
      error: (err) => {
        if (this.isInterruptedMatchStatus(match?.status || '')) {
          this.buildAbandonedMatchFallbackEssay(match, seriesName);
          this.matchReportLoading = false;
        } else {
          this.matchReportError = err?.error?.error || 'Failed to load match report';
          this.matchReportLoading = false;
        }
      }
    });
  }

  private isInterruptedMatchStatus(status: string): boolean {
    return /(abandon|abandoned|no\s*result|rain|called\s*off|stopp?ed|interrupted|wet\s*outfield|no\s*toss)/i.test(String(status || '').trim());
  }

  private buildAbandonedMatchFallbackEssay(match: Match, seriesName: string = '') {
    const home = this.getDisplayTeamName(match.team_home);
    const away = this.getDisplayTeamName(match.team_away);
    const isBblReport = /big\s*bash|bbl/i.test(seriesName || '') || (this.selectedLeagueType === 'bbl' && !/world\s*cup/i.test(seriesName || ''));
    this.matchReportEssayTitle = isBblReport
      ? `${home} Vs ${away} - BBL Match Report`
      : `${home} Vs ${away} - Match Report`;

    const venue = this.getMatchVenueFromScorecard(match) || '';
    const date = this.getMatchDateFromScorecard(match) || '';
    this.matchReportEssayDateLine = [venue, date].filter(Boolean).join(' • ');

    const statusText = String(match?.status || '').trim() || 'No result';
    const seed = Number(String((match as any)?.external_id || '').replace(/\D/g, '').slice(-3) || '1');
    const v = seed % 4;

    const p1 =
      v === 0
        ? `${home} and ${away} were unable to complete this fixture after persistent interruptions affected play.`
        : v === 1
          ? `This contest between ${home} and ${away} ended without a full result as conditions prevented a proper finish.`
          : v === 2
            ? `Weather and stoppages left this game incomplete, with both teams forced to settle for a non-result outcome.`
            : `The match never reached a decisive phase, and officials called it off before a winner could be confirmed.`;

    const p2 =
      v % 2 === 0
        ? `The official update recorded: ${statusText}.`
        : `${statusText} was listed as the final status for this fixture.`;

    const p3 =
      isBblReport
        ? `For BBL points-table context, this result means neither side takes a full-win swing from this game.`
        : `In World Cup context, both teams move on without a decisive points boost from this match.`;

    this.matchReportData = null;
    this.matchReportError = null;
    this.matchReportEssayParagraphs = [p1, p2, p3];
  }

  openWorldCupMatchReport(match: Match) {
    this.openMatchReport(match, "ICC Men's T20 World Cup 2026");
  }

  closeMatchReport() {
    this.headerPage = 'home';
    this.selectedWorldCupReport = null;
    this.matchReportLoading = false;
    this.matchReportError = null;
    this.matchReportData = null;
    this.matchReportEssayTitle = '';
    this.matchReportEssayDateLine = '';
    this.matchReportEssayParagraphs = [];
  }

  private buildYoutubeEmbedUrl(videoId: string): SafeResourceUrl {
    return this.sanitizer.bypassSecurityTrustResourceUrl(`https://www.youtube-nocookie.com/embed/${videoId}?rel=0`);
  }

  openWorldCupHighlights(match: Match) {
    const matchId = String((match as any)?.external_id || (match as any)?.id || '').trim();
    if (this.highlightsLoading) return;
    if (
      this.highlightsModalOpen &&
      this.highlightsSelectedMatch === match &&
      this.highlightsData?.items?.length
    ) {
      return;
    }
    this.scorecardModalOpen = false;
    this.highlightsOpenedAtMs = Date.now();
    this.highlightsModalOpen = true;
    this.highlightsLoading = true;
    this.highlightsError = null;
    this.highlightsData = null;
    this.highlightsSelectedVideoId = null;
    this.highlightsEmbedUrl = null;
    this.highlightsSelectedMatch = match;
    this.cdr.detectChanges();

    if (!matchId) {
      this.highlightsLoading = false;
      this.highlightsError = 'Match ID not found. This match may not support highlights.';
      this.cdr.detectChanges();
      return;
    }

    this.cricketService.getMatchHighlights(matchId).subscribe({
      next: (data) => {
        this.highlightsData = data;
        const first = Array.isArray(data?.items) ? data.items[0] : null;
        const firstId = first?.videoId || null;
        this.highlightsSelectedVideoId = firstId;
        this.highlightsSelectedUrl = first?.url || (firstId ? `https://www.youtube.com/watch?v=${firstId}` : null);
        this.highlightsEmbedUrl = firstId ? this.buildYoutubeEmbedUrl(firstId) : null;
        if (!firstId) this.highlightsError = 'No highlights found for this match.';
        this.highlightsLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.highlightsError = err?.error?.error || err?.error?.details || 'Failed to load highlights';
        this.highlightsLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  onWorldCupHighlightsClick(match: Match, ev?: Event) {
    if (ev) {
      ev.preventDefault?.();
      ev.stopPropagation?.();
      (ev as any).stopImmediatePropagation?.();
    }
    // Defer to next tick so parent card click cannot fire first
    setTimeout(() => this.openWorldCupHighlights(match), 0);
  }

  onBblHighlightsClick(match: Match, ev?: Event) {
    if (ev) {
      ev.preventDefault?.();
      ev.stopPropagation?.();
      (ev as any).stopImmediatePropagation?.();
    }
    setTimeout(() => this.openWorldCupHighlights(match), 0);
  }

  selectHighlightVideo(videoId: string) {
    const id = String(videoId || '').trim();
    if (!id) return;
    this.highlightsSelectedVideoId = id;
    this.highlightsEmbedUrl = this.buildYoutubeEmbedUrl(id);
    const hit = this.highlightsData?.items?.find((x) => x.videoId === id);
    this.highlightsSelectedUrl = hit?.url || `https://www.youtube.com/watch?v=${id}`;
  }

  closeHighlights() {
    this.highlightsModalOpen = false;
    this.highlightsLoading = false;
    this.highlightsError = null;
    this.highlightsData = null;
    this.highlightsSelectedVideoId = null;
    this.highlightsEmbedUrl = null;
    this.highlightsSelectedUrl = null;
    this.highlightsSelectedMatch = null;
  }

  closeHighlightsFromOverlay() {
    // Prevent immediate close from the same click event that opened the modal.
    if (Date.now() - this.highlightsOpenedAtMs < 220) return;
    this.closeHighlights();
  }

  private parseScorePair(s?: string): { r: number; w: number } | null {
    const raw = String(s || '').trim();
    if (!raw) return null;
    // expected formats: "190/9", "184/7"
    const parts = raw.split('/');
    if (parts.length < 2) return null;
    const r = Number(parts[0]);
    const w = Number(parts[1]);
    if (!Number.isFinite(r) || !Number.isFinite(w)) return null;
    return { r, w };
  }

  private oversToBalls(o: number, maxOvers: number): number {
    if (!Number.isFinite(o)) return 0;
    const whole = Math.floor(o);
    const ballsPart = Math.round((o - whole) * 10); // cricket format: 19.4 => 19 overs + 4 balls
    const totalOversBalls = whole * 6 + ballsPart;
    return Math.max(0, Math.min(totalOversBalls, maxOvers * 6));
  }

  private buildWorldCupMatchEssay(match: Match, sc: Scorecard, seriesName: string = '') {
    const home = this.getDisplayTeamName(match.team_home);
    const away = this.getDisplayTeamName(match.team_away);
    const isBblReport = /big\s*bash|bbl/i.test(seriesName || '') || (this.selectedLeagueType === 'bbl' && !/world\s*cup/i.test(seriesName || ''));
    this.matchReportEssayTitle = isBblReport
      ? `${home} Vs ${away} - BBL Match Report`
      : `${home} Vs ${away} - Match Report`;

    const venue = this.getMatchVenueFromScorecard(match) || '';
    const date = this.getMatchDateFromScorecard(match) || '';
    this.matchReportEssayDateLine = [venue, date].filter(Boolean).join(' • ');

    const statusText = String((sc as any)?.status || match.status || '').trim();
    const specialStop = /(abandon|abandoned|no\s*result|rain|called\s*off|stopp?ed|interrupted|wet\s*outfield)/i.test(statusText);
    if (specialStop) {
      const inningsArr = Array.isArray(sc?.scorecard) ? (sc.scorecard as any[]) : [];
      const scoreLines = Array.isArray(sc?.score) ? (sc.score as any[]) : [];
      const firstLine = scoreLines[0];
      const secondLine = scoreLines[1];
      const firstInn = inningsArr[0];
      const secondInn = inningsArr[1];

      const topBatterOf = (inn: any) => {
        const bat = Array.isArray(inn?.batting) ? inn.batting : [];
        let best: any = null;
        for (const b of bat) {
          if (!b?.batsman?.name) continue;
          if (!best || Number(b?.r) > Number(best?.r)) best = b;
        }
        return best;
      };
      const bestBowlerOf = (inn: any) => {
        const bowl = Array.isArray(inn?.bowling) ? inn.bowling : [];
        let best: any = null;
        for (const b of bowl) {
          if (!b?.bowler?.name) continue;
          const w = Number(b?.w);
          if (!Number.isFinite(w)) continue;
          if (!best || w > Number(best?.w) || (w === Number(best?.w) && Number(b?.r) < Number(best?.r))) best = b;
        }
        return best;
      };

      const topBat1 = firstInn ? topBatterOf(firstInn) : null;
      const topBat2 = secondInn ? topBatterOf(secondInn) : null;
      const bestBowl1 = firstInn ? bestBowlerOf(firstInn) : null;
      const bestBowl2 = secondInn ? bestBowlerOf(secondInn) : null;

      const seed = Number(String((match as any)?.external_id || '').replace(/\D/g, '').slice(-3) || '1');
      const v = seed % 4;

      const firstTotal = firstLine ? `${firstLine.r}/${firstLine.w}` : '';
      const secondTotal = secondLine ? `${secondLine.r}/${secondLine.w}` : '';
      const firstOvers = firstLine?.o != null ? `${Number(firstLine.o).toFixed(1)} ov` : '';
      const secondOvers = secondLine?.o != null ? `${Number(secondLine.o).toFixed(1)} ov` : '';

      const p1 =
        v === 0
          ? `The contest between ${home} and ${away} could not reach a full finish as conditions forced an early stop.`
          : v === 1
            ? `This game never got the uninterrupted run both sides wanted, and play was eventually halted before a clear result was possible.`
            : v === 2
              ? `${home} vs ${away} turned into a weather-hit fixture, with interruptions taking momentum away from both teams.`
              : `A promising start gave way to repeated delays, and the match ended without the usual closing phase.`;

      const p2 = [firstTotal && `${home}/${away} had reached ${firstTotal}${firstOvers ? ` in ${firstOvers}` : ''} in the first innings phase.`, secondTotal && `The reply/next phase stood at ${secondTotal}${secondOvers ? ` after ${secondOvers}` : ''}.`]
        .filter(Boolean)
        .join(' ');

      const p3 =
        topBat1?.batsman?.name || topBat2?.batsman?.name
          ? `Before the stoppage, ${topBat1?.batsman?.name ? `${topBat1.batsman.name} (${topBat1.r})` : ''}${topBat1?.batsman?.name && topBat2?.batsman?.name ? ' and ' : ''}${topBat2?.batsman?.name ? `${topBat2.batsman.name} (${topBat2.r})` : ''} provided the major batting moments.`
          : '';

      const p4 =
        bestBowl1?.bowler?.name || bestBowl2?.bowler?.name
          ? `${bestBowl1?.bowler?.name ? `${bestBowl1.bowler.name} picked up ${bestBowl1.w} wicket(s)` : ''}${bestBowl1?.bowler?.name && bestBowl2?.bowler?.name ? ', while ' : ''}${bestBowl2?.bowler?.name ? `${bestBowl2.bowler.name} returned ${bestBowl2.w}/${bestBowl2.r}` : ''} before the match was stopped.`
          : '';

      const p5 =
        v % 2 === 0
          ? `The official status reflects the interruption: ${statusText || 'No result'}.`
          : `${statusText || 'No result'} was recorded, with no winner possible from this shortened game.`;

      this.matchReportEssayParagraphs = [p1, p2, p3, p4, p5].filter(Boolean).slice(0, 6);
      return;
    }

    const scoreLines = Array.isArray(sc?.score) ? (sc.score as any[]) : [];
    const firstLine = scoreLines[0];
    const secondLine = scoreLines[1];
    const inningsArr = Array.isArray(sc?.scorecard) ? (sc.scorecard as any[]) : [];
    const firstInn = inningsArr[0];
    const secondInn = inningsArr[1];

    const maxOvers = 20;
    const homePair = this.parseScorePair(match.home_score);
    const awayPair = this.parseScorePair(match.away_score);

    // Determine batting order (first innings total belongs to either home or away by matching runs/wkts).
    let batFirstTeam = home;
    const firstR = Number(firstLine?.r);
    const firstW = Number(firstLine?.w);
    if (homePair && firstR === homePair.r && firstW === homePair.w) batFirstTeam = home;
    else if (awayPair && firstR === awayPair.r && firstW === awayPair.w) batFirstTeam = away;
    else {
      if (homePair && firstR === homePair.r) batFirstTeam = home;
      else if (awayPair && firstR === awayPair.r) batFirstTeam = away;
    }
    const batSecondTeam = batFirstTeam === home ? away : home;

    const firstTotal = firstLine ? `${firstLine.r}/${firstLine.w}` : '';
    const firstOvers = firstLine?.o != null ? `${Number(firstLine.o).toFixed(1)} ov` : '';
    const secondTotal = secondLine ? `${secondLine.r}/${secondLine.w}` : '';
    const secondOvers = secondLine?.o != null ? `${Number(secondLine.o).toFixed(1)} ov` : '';

    const firstRuns = Number(firstLine?.r);
    const secondRuns = Number(secondLine?.r);

    let winnerTeam = batFirstTeam;
    let winByText = '';
    let wicketsRemaining: number | null = null;

    if (Number.isFinite(firstRuns) && Number.isFinite(secondRuns)) {
      if (secondRuns >= firstRuns + 1) {
        winnerTeam = batSecondTeam;
        const wicketsLost = Number(secondLine?.w);
        wicketsRemaining = Number.isFinite(wicketsLost) ? Math.max(0, 10 - wicketsLost) : null;
        winByText = wicketsRemaining != null ? `by ${wicketsRemaining} wickets` : '';
      } else {
        winnerTeam = batFirstTeam;
        const runsWon = firstRuns - secondRuns;
        winByText = Number.isFinite(runsWon) ? `by ${runsWon} runs` : '';
      }
    }

    const topBatterOf = (inn: any) => {
      const bat = Array.isArray(inn?.batting) ? inn.batting : [];
      let best: any = null;
      for (const b of bat) {
        if (!b?.batsman?.name) continue;
        if (!best || Number(b?.r) > Number(best?.r)) best = b;
      }
      return best;
    };

    const topSrBatterOf = (inn: any) => {
      const bat = Array.isArray(inn?.batting) ? inn.batting : [];
      let best: any = null;
      for (const b of bat) {
        if (!b?.batsman?.name) continue;
        const sr = Number(b?.sr);
        if (!Number.isFinite(sr)) continue;
        if (!best || sr > Number(best?.sr)) best = b;
      }
      return best;
    };

    const bestBowlerOf = (inn: any) => {
      const bowl = Array.isArray(inn?.bowling) ? inn.bowling : [];
      let best: any = null;
      for (const b of bowl) {
        if (!b?.bowler?.name) continue;
        const w = Number(b?.w);
        if (!Number.isFinite(w)) continue;
        if (!best || w > Number(best?.w) || (w === Number(best?.w) && Number(b?.r) < Number(best?.r))) best = b;
      }
      return best;
    };

    const bestEconomyOf = (inn: any) => {
      const bowl = Array.isArray(inn?.bowling) ? inn.bowling : [];
      let best: any = null;
      for (const b of bowl) {
        if (!b?.bowler?.name) continue;
        const eco = Number(b?.eco);
        if (!Number.isFinite(eco)) continue;
        if (!best || eco < Number(best?.eco)) best = b;
      }
      return best;
    };

    const topBat1 = firstInn ? topBatterOf(firstInn) : null;
    const topBat2 = secondInn ? topBatterOf(secondInn) : null;
    const topSr1 = firstInn ? topSrBatterOf(firstInn) : null;
    const topSr2 = secondInn ? topSrBatterOf(secondInn) : null;

    const bestBowl1 = firstInn ? bestBowlerOf(firstInn) : null;
    const bestBowl2 = secondInn ? bestBowlerOf(secondInn) : null;
    const bestEco2 = secondInn ? bestEconomyOf(secondInn) : null;

    const paragraphs: string[] = [];

    const outcomeVariantSeed =
      (winnerTeam === batFirstTeam ? 1 : 2) +
      Math.round((Number(topBat1?.r) || 0) / 25) +
      Math.round((Number(bestBowl2?.w) || 0) * 2);
    const variantCount = 4;
    const variant = outcomeVariantSeed % variantCount;

    const chasedTarget = Number.isFinite(firstRuns) ? firstRuns + 1 : null;
    const chaseComfort =
      wicketsRemaining != null && Number.isFinite(wicketsRemaining) ? (wicketsRemaining >= 7 ? 'comfortable' : wicketsRemaining >= 4 ? 'controlled' : 'nervy') : 'nervy';

    // Paragraph 1: big-picture (varied templates)
    if (winnerTeam === batSecondTeam && chasedTarget != null) {
      const chaseLine =
        variant === 0
          ? `${batSecondTeam} chased ${chasedTarget} with ${chaseComfort} intent, turning pressure into progress.`
          : variant === 1
            ? `It was ${batSecondTeam}'s day in the chase: ${batFirstTeam} set the bar at ${firstTotal} (${firstOvers}), and the reply followed with purpose.`
            : variant === 2
              ? `${batSecondTeam} took the target on from ball one, steadily building momentum before finishing ${secondTotal} (${secondOvers}).`
              : `A target of ${chasedTarget} looked inviting, and ${batSecondTeam} kept finding the next boundary to land it at ${secondTotal}.`;
      paragraphs.push(`${chaseLine} ${winnerTeam} ${winByText}.`);
    } else if (Number.isFinite(firstRuns) && Number.isFinite(secondRuns)) {
      const runsWon = firstRuns - secondRuns;
      const defenseLine =
        variant === 0
          ? `${batFirstTeam} defended ${firstTotal} (${firstOvers}) with discipline, keeping the chase within reach but never letting it fully swing.`
          : variant === 1
            ? `${batFirstTeam} posted a total that required a perfect chase, then tightened the screws as ${batSecondTeam} fell short on ${secondTotal}.`
            : variant === 2
              ? `Under pressure late on, ${batFirstTeam} still held the line. ${batSecondTeam} managed ${secondTotal} (${secondOvers})—and ${batFirstTeam} won ${winByText}.`
              : `The numbers told the story: ${batFirstTeam} finished first with ${firstTotal} (${firstOvers}), and ${batSecondTeam} were ${runsWon} runs short at ${secondTotal}.`;
      paragraphs.push(defenseLine + ` ${winnerTeam} ${winByText}.`);
    } else {
      paragraphs.push(`${batFirstTeam} and ${batSecondTeam} produced a tense contest that ended with ${winnerTeam} getting the result.`);
    }

    // Paragraph 2: first innings anchor
    if (topBat1) {
      const runs = Number(topBat1.r);
      const balls = Number(topBat1.b);
      const fours = Number(topBat1['4s'] || 0);
      const sixes = Number(topBat1['6s'] || 0);
      const styleA =
        variant % 2 === 0
          ? `${topBat1.batsman.name} was the clear driver in the first innings, striking ${runs} off ${balls} balls.`
          : `${topBat1.batsman.name} anchored the innings with a score of ${runs} (from ${balls} balls), keeping the scoreboard ticking.`;
      const boundaryLine = fours + sixes > 0 ? `The boundaries kept coming—${fours} fours and ${sixes} sixes.` : `The innings stayed steady even without a big boundary spree.`;
      paragraphs.push(`${styleA} ${boundaryLine}`);
    } else {
      paragraphs.push(`Runs arrived in phases as ${batFirstTeam} built their innings to ${firstTotal} (${firstOvers}).`);
    }

    // Paragraph 3: second innings storyline (different for chase vs defend)
    if (winnerTeam === batSecondTeam && topBat2) {
      const runs2 = Number(topBat2.r);
      const balls2 = Number(topBat2.b);
      const sr2 = Number(topBat2.sr);
      const srPart = Number.isFinite(sr2) ? ` at a strike rate of ${sr2}` : '';
      const chasePara =
        variant === 0
          ? `${batSecondTeam} built the chase around ${topBat2.batsman.name}, who made ${runs2} off ${balls2} balls${srPart}.`
          : variant === 1
            ? `As the equation changed, ${topBat2.batsman.name} stayed composed—${runs2} from ${balls2} deliveries to take the chase forward.`
            : variant === 2
              ? `${batSecondTeam} kept their nerve, with ${topBat2.batsman.name} providing the final push (${runs2} off ${balls2}).`
              : `The chasing side looked comfortable once ${topBat2.batsman.name} got going—${runs2} off ${balls2} as ${batSecondTeam} finished ${secondTotal}.`;
      paragraphs.push(`${chasePara} ${wicketsRemaining != null ? `They still had ${wicketsRemaining} wickets in hand.` : ''}`.trim());
    } else if (winnerTeam === batFirstTeam && topBat2) {
      const runs2 = Number(topBat2.r);
      const balls2 = Number(topBat2.b);
      const strugglePara =
        variant === 0
          ? `${batSecondTeam} tried to chase the dream with ${topBat2.batsman.name}'s ${runs2} off ${balls2} balls, but the required momentum never fully arrived.`
          : variant === 1
            ? `Even when ${topBat2.batsman.name} showed intent (${runs2} from ${balls2}), ${batFirstTeam} responded with crucial overs to keep them short.`
            : variant === 2
              ? `For ${batSecondTeam}, ${topBat2.batsman.name} was the brightest light (${runs2} off ${balls2}), yet ${batFirstTeam} defended ${firstTotal}.`
              : `${topBat2.batsman.name} kept ${batSecondTeam} in the hunt (${runs2} off ${balls2}), but the total proved enough for ${batFirstTeam}.`;
      paragraphs.push(strugglePara);
    }

    // Paragraph 4: bowling impact (mix wickets + economy)
    if (bestBowl2) {
      const bowlerName = bestBowl2.bowler.name;
      const w = Number(bestBowl2.w);
      const r = Number(bestBowl2.r);
      const o = Number(bestBowl2.o);
      const m = Number(bestBowl2.m);
      const figures = Number.isFinite(o) && Number.isFinite(m) ? `${o}-${m}-${r}-${w}` : `${w}/${r}`;

      const bowlPara =
        variant === 0
          ? `The turning point came with the ball: ${bowlerName} took ${w} wicket(s) for ${r} runs, finishing with ${figures}.`
          : variant === 1
            ? `Bowling wins matches, and ${bowlerName} proved it—${w} wickets for ${r} runs (${figures}).`
            : variant === 2
              ? `A disciplined spell by ${bowlerName} (${figures}) disrupted the rhythm and swung the contest toward ${winnerTeam}.`
              : `When it mattered most, ${bowlerName} delivered (${figures}) to limit ${batSecondTeam} and set up the final result.`;
      paragraphs.push(bowlPara);

      if (winnerTeam === batFirstTeam && bestEco2 && bestEco2.bowler?.name && bestEco2.bowler.name !== bowlerName) {
        paragraphs.push(`${bestEco2.bowler.name} also kept things tight with an economy of ${Number(bestEco2.eco).toFixed(2)}.`);
      } else if (winnerTeam === batSecondTeam && bestEco2 && bestEco2.bowler?.name) {
        paragraphs.push(`${bestEco2.bowler.name} kept the scoring rate under control (economy ${Number(bestEco2.eco).toFixed(2)}).`);
      }
    } else if (bestBowl1 && variant % 2 === 0) {
      paragraphs.push(`${bestBowl1.bowler.name} struck early for breakthroughs, helping ${batSecondTeam} stay in the game.`);
    }

    // Paragraph 5: top strike-rate detail (variety)
    const srPick = winnerTeam === batSecondTeam ? topSr2 : topSr1;
    if (srPick?.batsman?.name) {
      const srVal = Number(srPick.sr);
      if (Number.isFinite(srVal)) {
        paragraphs.push(`${srPick.batsman.name} posted the highest strike-rate in the innings at ${srVal}, giving the team momentum at critical moments.`);
      }
    }

    this.matchReportEssayParagraphs = paragraphs.filter(Boolean).slice(0, 6);
  }

  /**
   * BBL match centre: show full-page tabs (Match Info / Squad / Scorecard).
   * This reuses the existing scorecard API and team squad API where possible.
   */
  openBblMatchCentre(match: Match, seriesName: string = 'Big Bash League 2025-26', ev?: Event) {
    if (ev) ev.stopPropagation();
    this.closeHighlights();
    this.selectedBblMatch = match;
    this.matchCentreUseLiveScorecardApi = false;
    this.matchCentreAllowScorecardTab = false;
    this.matchCentreHideBuildXiTab = false;

    this.selectedUpcoming = {
      external_id: match.external_id,
      team_home: match.team_home,
      team_away: match.team_away,
      series_name: seriesName,
      venue: this.getBblVenueForMatch(match),
      status: match.status,
      start_time_utc: '',
      date_ist: this.getMatchDateFromScorecard(match) || '',
      time_ist: '',
    } as UpcomingMatch;

    this.headerPage = 'matchcentre';
    this.matchCentreTab = 'scorecard';

    // Reset match-centre panels.
    this.matchCentreTeamA = null;
    this.matchCentreTeamB = null;
    this.matchCentreComparisonLoading = false;
    this.matchCentreH2H = null;
    this.matchCentreH2HLoading = false;
    this.matchCentreFormA = null;
    this.matchCentreFormB = null;
    this.matchCentreFormLoading = false;

    this.matchCentreSquadLoading = false;
    this.matchCentreSquadA = null;
    this.matchCentreSquadB = null;

    // Reset Build XI state (not shown for BBL).
    this.matchCentreXISelected = [];
    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;
    this.matchCentreXIFantasyConfirmed = false;
    this.matchCentreXICaptainKey = null;
    this.matchCentreXIWkKey = null;
    this.matchCentreXIScreenshotLoading = false;
    this.matchCentreXIImpactKey = null;

    // Load scorecard for the default tab.
    this.matchCentreScorecardData = null;
    this.matchCentreScorecardError = null;
    this.matchCentreScorecardLoading = false;
    this.loadMatchCentreScorecardIfNeeded();
  }

  openWorldCupMatchCentre(match: Match, seriesName: string = "ICC Men's T20 World Cup 2026", ev?: Event) {
    if (ev) ev.stopPropagation();
    this.closeHighlights();
    this.selectedBblMatch = null;
    this.matchCentreUseLiveScorecardApi = false;
    this.matchCentreAllowScorecardTab = false;
    this.matchCentreHideBuildXiTab = false;

    this.selectedUpcoming = {
      external_id: match.external_id,
      team_home: match.team_home,
      team_away: match.team_away,
      series_name: seriesName,
      venue: this.getMatchVenueFromScorecard(match) || match.name || '',
      status: match.status,
      start_time_utc: '',
      date_ist: this.getMatchDateFromScorecard(match) || '',
      time_ist: '',
    } as UpcomingMatch;

    this.headerPage = 'matchcentre';
    this.matchCentreTab = 'info';

    this.matchCentreTeamA = null;
    this.matchCentreTeamB = null;
    this.matchCentreComparisonLoading = false;
    this.matchCentreH2H = null;
    this.matchCentreH2HLoading = false;
    this.matchCentreFormA = null;
    this.matchCentreFormB = null;
    this.matchCentreFormLoading = false;
    this.matchCentreSquadLoading = false;
    this.matchCentreSquadA = null;
    this.matchCentreSquadB = null;

    this.matchCentreScorecardData = null;
    this.matchCentreScorecardError = null;
    this.matchCentreScorecardLoading = false;

    this.matchCentreXISelected = [];
    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;
    this.matchCentreXIFantasyConfirmed = false;
    this.matchCentreXICaptainKey = null;
    this.matchCentreXIWkKey = null;
    this.matchCentreXIScreenshotLoading = false;
    this.matchCentreXIImpactKey = null;
    this.loadMatchCentreScorecardIfNeeded();
  }

  openMatchCentre(m: UpcomingMatch, ev?: Event) {
    if (ev) ev.stopPropagation();
    this.closeHighlights();
    this.selectedBblMatch = null;
    this.matchCentreUseLiveScorecardApi = false;
    this.matchCentreAllowScorecardTab = false;
    this.matchCentreHideBuildXiTab = false;
    this.selectedUpcoming = m;
    this.matchCentreTab = 'info';
    this.headerPage = 'matchcentre';
    this.matchCentreTeamA = null;
    this.matchCentreTeamB = null;
    this.matchCentreComparisonLoading = false;
    this.matchCentreH2H = null;
    this.matchCentreH2HLoading = false;
    this.matchCentreFormA = null;
    this.matchCentreFormB = null;
    this.matchCentreFormLoading = false;
    this.matchCentreSquadLoading = false;
    this.matchCentreSquadA = null;
    this.matchCentreSquadB = null;

    this.matchCentreScorecardLoading = false;
    this.matchCentreScorecardError = null;
    this.matchCentreScorecardData = null;

    // reset Build Your XI selection state
    this.matchCentreXISelected = [];
    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;
    this.matchCentreXIFantasyConfirmed = false;
    this.matchCentreXICaptainKey = null;
    this.matchCentreXIWkKey = null;
    this.matchCentreXIScreenshotLoading = false;
    this.matchCentreXIImpactKey = this.isIplUpcomingMatch(m) ? null : null;
    this.matchCentreNowMs = Date.now();
    if (this.matchCentreTicker) clearInterval(this.matchCentreTicker);
    this.matchCentreTicker = setInterval(() => {
      this.matchCentreNowMs = Date.now();
    }, 1000);

    // Load "Last 10 matches" per-team stats (manual DB data)
    const iplA = this.getIplTeamCode(m.team_home);
    const iplB = this.getIplTeamCode(m.team_away);
    const pslA = this.getPslTeamKey(m.team_home);
    const pslB = this.getPslTeamKey(m.team_away);

    // IPL: last10 + form + head-to-head
    if (iplA && iplB) {
      this.matchCentreComparisonLoading = true;
      this.matchCentreFormLoading = true;
      this.matchCentreH2HLoading = true;

      forkJoin({
        a: this.cricketService.getTeamLastN(iplA, 'overall'),
        b: this.cricketService.getTeamLastN(iplB, 'overall'),
        fa: this.cricketService.getTeamForm(iplA, 5),
        fb: this.cricketService.getTeamForm(iplB, 5),
      }).subscribe({
        next: ({ a: aRow, b: bRow, fa, fb }) => {
          this.matchCentreTeamA = aRow;
          this.matchCentreTeamB = bRow;
          this.matchCentreFormA = fa;
          this.matchCentreFormB = fb;
          this.matchCentreComparisonLoading = false;
          this.matchCentreFormLoading = false;
        },
        error: () => {
          this.matchCentreTeamA = null;
          this.matchCentreTeamB = null;
          this.matchCentreFormA = null;
          this.matchCentreFormB = null;
          this.matchCentreComparisonLoading = false;
          this.matchCentreFormLoading = false;
        }
      });

      this.cricketService.getHeadToHead(iplA, iplB, 'overall').subscribe({
        next: (data) => {
          this.matchCentreH2H = data;
          this.matchCentreH2HLoading = false;
        },
        error: () => {
          this.matchCentreH2H = null;
          this.matchCentreH2HLoading = false;
        }
      });
      return;
    }

    // PSL: last10 + form + head-to-head
    if (pslA && pslB) {
      const aCode = this.getTeamCodeDisplay(m.team_home);
      const bCode = this.getTeamCodeDisplay(m.team_away);
      this.matchCentreComparisonLoading = true;
      this.matchCentreFormLoading = true;
      this.matchCentreH2HLoading = true;

      forkJoin({
        a: this.cricketService.getTeamLastN(aCode, 'overall'),
        b: this.cricketService.getTeamLastN(bCode, 'overall'),
        fa: this.cricketService.getTeamForm(aCode, 5),
        fb: this.cricketService.getTeamForm(bCode, 5),
      }).subscribe({
        next: ({ a: aRow, b: bRow, fa, fb }) => {
          this.matchCentreTeamA = aRow;
          this.matchCentreTeamB = bRow;
          this.matchCentreComparisonLoading = false;
          this.matchCentreFormA = fa;
          this.matchCentreFormB = fb;
          this.matchCentreFormLoading = false;
        },
        error: () => {
          this.matchCentreTeamA = null;
          this.matchCentreTeamB = null;
          this.matchCentreComparisonLoading = false;
          this.matchCentreFormA = null;
          this.matchCentreFormB = null;
          this.matchCentreFormLoading = false;
        }
      });

      this.cricketService.getHeadToHead(aCode, bCode, 'overall').subscribe({
        next: (data) => {
          this.matchCentreH2H = data;
          this.matchCentreH2HLoading = false;
        },
        error: () => {
          this.matchCentreH2H = null;
          this.matchCentreH2HLoading = false;
        }
      });
    }
  }

  closeMatchCentre() {
    this.closeHighlights();
    this.headerPage = 'home';
    this.selectedBblMatch = null;
    this.selectedUpcoming = null;
    this.matchCentreTeamA = null;
    this.matchCentreTeamB = null;
    this.matchCentreComparisonLoading = false;
    this.matchCentreH2H = null;
    this.matchCentreH2HLoading = false;
    this.matchCentreFormA = null;
    this.matchCentreFormB = null;
    this.matchCentreFormLoading = false;
    this.matchCentreSquadLoading = false;
    this.matchCentreSquadA = null;
    this.matchCentreSquadB = null;

    this.matchCentreXISelected = [];
    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;
    this.matchCentreXIFantasyConfirmed = false;
    this.matchCentreXICaptainKey = null;
    this.matchCentreXIWkKey = null;
    this.matchCentreXIScreenshotLoading = false;
    this.matchCentreXIImpactKey = null;

    this.matchCentreScorecardLoading = false;
    this.matchCentreScorecardError = null;
    this.matchCentreScorecardData = null;
    this.bblSummaryModalOpen = false;
    this.wcSummaryModalOpen = false;
    this.matchCentreSelectedBblInningsIdx = 0;
    this.matchCentreUseLiveScorecardApi = false;
    this.matchCentreAllowScorecardTab = false;
    this.matchCentreHideBuildXiTab = false;
    if (this.matchCentreTicker) {
      clearInterval(this.matchCentreTicker);
      this.matchCentreTicker = null;
    }
  }

  setMatchCentreTab(tab: 'info' | 'squad' | 'scorecard' | 'buildxi') {
    if (tab === 'buildxi' && this.matchCentreHideBuildXiTab) {
      tab = 'info';
    }
    this.matchCentreTab = tab;
    if (tab === 'squad' || tab === 'buildxi') {
      this.loadMatchCentreSquadsIfNeeded();
    }
    if (tab === 'scorecard' || tab === 'info') {
      // Live feed scorecards must refetch when opening Scorecard (no stale DB snapshot).
      this.loadMatchCentreScorecardIfNeeded(
        this.matchCentreUseLiveScorecardApi && tab === 'scorecard',
      );
    }
  }

  openBblMatchSummary(ev?: Event) {
    if (ev) ev.stopPropagation();
    this.loadMatchCentreScorecardIfNeeded();
    this.bblSummaryModalOpen = true;
  }

  closeBblMatchSummary() {
    this.bblSummaryModalOpen = false;
  }

  openWorldCupMatchSummary(ev?: Event) {
    if (ev) ev.stopPropagation();
    this.loadMatchCentreScorecardIfNeeded();
    this.wcSummaryModalOpen = true;
  }

  closeWorldCupMatchSummary() {
    this.wcSummaryModalOpen = false;
  }

  getWcSummarySides(): Array<{
    team: string;
    logoTeam: string;
    score: string;
    overs: string;
    batters: Array<{ name: string; runs: string; balls: string }>;
    bowlers: Array<{ name: string; fig: string; overs: string }>;
  }> {
    const scoreRows: any[] = Array.isArray(this.matchCentreScorecardData?.score) ? this.matchCentreScorecardData!.score! : [];
    const inningsRows: any[] = Array.isArray(this.matchCentreScorecardData?.scorecard) ? this.matchCentreScorecardData!.scorecard! : [];
    const out: Array<{
      team: string;
      logoTeam: string;
      score: string;
      overs: string;
      batters: Array<{ name: string; runs: string; balls: string }>;
      bowlers: Array<{ name: string; fig: string; overs: string }>;
    }> = [];

    const limit = Math.min(scoreRows.length || 0, inningsRows.length || 0, 2);
    for (let i = 0; i < limit; i++) {
      const s = scoreRows[i] || {};
      const inn = inningsRows[i] || {};
      const team = this.getBblTeamLabel(s?.inning || inn?.inning || '');
      const logoTeam = i === 0 ? (this.selectedUpcoming?.team_home || team) : (this.selectedUpcoming?.team_away || team);
      const score = `${Number(s?.r || 0)}-${Number(s?.w || 0)}`;
      const ovNum = Number(s?.o);
      const overs = Number.isFinite(ovNum) ? `${ovNum.toFixed(1)} overs` : '';

      const batters = (Array.isArray(inn?.batting) ? inn.batting : [])
        .map((b: any) => ({
          name: String(b?.batsman?.name || '').trim(),
          runs: String(Number.isFinite(Number(b?.r)) ? Number(b.r) : 0),
          balls: String(Number.isFinite(Number(b?.b)) ? Number(b.b) : 0),
        }))
        .filter((x: any) => x.name)
        .sort((a: any, b: any) => Number(b.runs) - Number(a.runs))
        .slice(0, 4);

      const bowlers = (Array.isArray(inn?.bowling) ? inn.bowling : [])
        .map((b: any) => ({
          name: String(b?.bowler?.name || '').trim(),
          fig: `${Number.isFinite(Number(b?.w)) ? Number(b.w) : 0}-${Number.isFinite(Number(b?.r)) ? Number(b.r) : 0}`,
          overs: String(Number.isFinite(Number(b?.o)) ? Number(b.o) : ''),
        }))
        .filter((x: any) => x.name)
        .sort((a: any, b: any) => Number((b.fig || '0-0').split('-')[0]) - Number((a.fig || '0-0').split('-')[0]))
        .slice(0, 4);

      out.push({ team, logoTeam, score, overs, batters, bowlers });
    }
    return out;
  }

  getBblSummaryRows(): Array<{
    team: string;
    logoTeam: string;
    overs: string;
    score: string;
    batters: Array<{ name: string; value: string }>;
    bowlers: Array<{ name: string; value: string }>;
  }> {
    const scoreRows: any[] = Array.isArray(this.matchCentreScorecardData?.score) ? this.matchCentreScorecardData!.score! : [];
    const inningsRows: any[] = Array.isArray(this.matchCentreScorecardData?.scorecard) ? this.matchCentreScorecardData!.scorecard! : [];
    const out: Array<{
      team: string;
      logoTeam: string;
      overs: string;
      score: string;
      batters: Array<{ name: string; value: string }>;
      bowlers: Array<{ name: string; value: string }>;
    }> = [];

    const limit = Math.min(scoreRows.length || 0, inningsRows.length || 0, 2);
    for (let i = 0; i < limit; i++) {
      const s = scoreRows[i] || {};
      const inn = inningsRows[i] || {};
      const team = this.getBblTeamLabel(s?.inning || inn?.inning || '');
      const overs = Number.isFinite(Number(s?.o)) ? String(Number(s.o).toFixed(1)) : '';
      const score = `${Number(s?.r || 0)}/${Number(s?.w || 0)}`;

      const battersRaw: any[] = Array.isArray(inn?.batting) ? inn.batting : [];
      const bowlersRaw: any[] = Array.isArray(inn?.bowling) ? inn.bowling : [];

      const batters = battersRaw
        .map((b: any) => ({
          name: String(b?.batsman?.name || '').trim(),
          runs: Number(b?.r),
        }))
        .filter((x: any) => x.name)
        .sort((a: any, b: any) => (Number.isFinite(b.runs) ? b.runs : 0) - (Number.isFinite(a.runs) ? a.runs : 0))
        .slice(0, 3)
        .map((x: any) => ({ name: x.name, value: `${Number.isFinite(x.runs) ? x.runs : 0}` }));

      const bowlers = bowlersRaw
        .map((b: any) => ({
          name: String(b?.bowler?.name || '').trim(),
          w: Number(b?.w),
          r: Number(b?.r),
        }))
        .filter((x: any) => x.name)
        .sort((a: any, b: any) => {
          const dw = (Number.isFinite(b.w) ? b.w : 0) - (Number.isFinite(a.w) ? a.w : 0);
          if (dw !== 0) return dw;
          return (Number.isFinite(a.r) ? a.r : 999) - (Number.isFinite(b.r) ? b.r : 999);
        })
        .slice(0, 3)
        .map((x: any) => ({ name: x.name, value: `${Number.isFinite(x.w) ? x.w : 0}-${Number.isFinite(x.r) ? x.r : 0}` }));

      out.push({
        team,
        logoTeam: i === 0 ? (this.selectedUpcoming?.team_home || team) : (this.selectedUpcoming?.team_away || team),
        overs,
        score,
        batters,
        bowlers
      });
    }
    return out;
  }

  /** True if live-results payload already includes enough scorecard JSON to render without HTTP. */
  private isUsableEmbeddedScorecard(sc: unknown): sc is Scorecard {
    if (!sc || typeof sc !== 'object') return false;
    const o = sc as Record<string, unknown>;
    const score = o['score'];
    const scorecard = o['scorecard'];
    return (Array.isArray(score) && score.length > 0) || (Array.isArray(scorecard) && scorecard.length > 0);
  }

  private loadMatchCentreScorecardIfNeeded(forceReload = false) {
    if (!this.selectedUpcoming) return;

    if (forceReload) {
      this.matchCentreScorecardData = null;
    } else if (this.matchCentreScorecardData) {
      return;
    }

    if (this.matchCentreScorecardLoading && !forceReload) {
      return;
    }

    const matchId = String(this.selectedUpcoming.external_id || '').trim();
    if (!matchId) return;

    const gen = ++this.matchCentreScorecardReqGen;
    this.matchCentreScorecardLoading = true;
    this.matchCentreScorecardError = null;

    const req = this.matchCentreUseLiveScorecardApi
      ? this.cricketService.getLiveScorecard(matchId)
      : this.cricketService.getScorecard(matchId);

    req.subscribe({
      next: (data) => {
        if (gen !== this.matchCentreScorecardReqGen) return;
        this.matchCentreScorecardData = data;
        this.matchCentreSelectedBblInningsIdx = 0;
        this.matchCentreScorecardLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        if (gen !== this.matchCentreScorecardReqGen) return;
        this.matchCentreScorecardError = err?.error?.error || 'Failed to load scorecard';
        this.matchCentreScorecardLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  selectBblInnings(idx: number) {
    this.matchCentreSelectedBblInningsIdx = idx;
  }

  getBblFallOfWickets(inn: any): any[] {
    if (!inn) return [];
    const f =
      inn.fallOfWickets ||
      inn.fow ||
      inn.fall_of_wickets ||
      inn.fall_of_wickets_data ||
      [];
    return Array.isArray(f) ? f : [];
  }

  isBblFinalMatch(): boolean {
    const name = String(this.selectedBblMatch?.name || '').toLowerCase();
    const n = this.parseBblMatchNumber(this.selectedBblMatch?.name || '');
    return n === 44 || name.includes('final');
  }

  getBblFinalWinnerTeam(): string | null {
    if (!this.isBblFinalMatch()) return null;
    const sc: any = this.matchCentreScorecardData;
    const score = Array.isArray(sc?.score) ? sc.score : [];
    if (score.length < 2) return null;

    const first = score[0];
    const second = score[1];

    const firstTeam = this.getBblTeamLabel(first?.inning);
    const secondTeam = this.getBblTeamLabel(second?.inning);
    if (!firstTeam || !secondTeam) return null;
    if (firstTeam === secondTeam) return null;

    const firstRuns = Number(first?.r);
    const secondRuns = Number(second?.r);
    if (!Number.isFinite(firstRuns) || !Number.isFinite(secondRuns)) return null;

    // If 2nd innings runs beat 1st innings by 1+ => chase win, else 1st innings win.
    if (secondRuns >= firstRuns + 1) return secondTeam;
    if (firstRuns >= secondRuns + 1) return firstTeam;
    // Tie / no result (best-effort fallback)
    return null;
  }

  getMatchInfoResult(): string {
    const status = String(this.matchCentreScorecardData?.status || this.selectedUpcoming?.status || '').trim();
    if (!status) return 'Result unavailable';
    return status;
  }

  isWorldCupFinalMatch(): boolean {
    if (!this.selectedUpcoming || !this.isIccMensT20WorldCupSeries(this.selectedUpcoming.series_name)) return false;
    const name = String(this.matchCentreScorecardData?.name || '').toLowerCase();
    if (name.includes('final')) return true;
    const m = name.match(/(\d+)\s*(st|nd|rd|th)?\s*match\b/);
    return !!(m && Number(m[1]) === 55);
  }

  getWorldCupFinalWinnerTeam(): string | null {
    if (!this.isWorldCupFinalMatch()) return null;
    const result = this.getMatchInfoResult();
    const m = result.match(/^(.+?)\s+won\b/i);
    if (m && m[1]) return m[1].trim();
    return null;
  }


  isIplUpcomingMatch(m: UpcomingMatch | null | undefined): boolean {
    const name = (m?.series_name || '').toLowerCase();
    if (name.includes('indian premier league')) return true;
    // fallback: if both teams map to IPL codes, treat as IPL fixture
    return !!(m && this.getIplTeamCode(m.team_home) && this.getIplTeamCode(m.team_away));
  }

  private getXIPlayerKey(team: 'A' | 'B', category: 'batters' | 'allrounders' | 'bowlers', p: TeamSquadPlayer): string {
    const name = (p?.name || '').trim();
    const id = p && (p as any).id ? String((p as any).id) : '';
    const img = p && p.imageId != null ? String(p.imageId) : '';
    return `${team}|${category}|${id}|${img}|${name}`;
  }

  private isWicketkeeperCandidate(p: TeamSquadPlayer): boolean {
    const b = String(p?.battingStyle || '');
    const w = String(p?.bowlingStyle || '');
    const t = `${b} ${w}`.toLowerCase();
    return t.includes('wicket') || /\bwk\b/.test(t);
  }

  private xiStats() {
    const total = this.matchCentreXISelected.length;
    let bowls = 0;
    for (const sel of this.matchCentreXISelected) {
      if (sel.category === 'bowlers' || sel.category === 'allrounders') bowls++;
    }
    return {
      total,
      bowls,
      okCount: total === 11,
      okBowl: bowls >= 5,
      okAll: total === 11 && bowls >= 5,
    };
  }

  // Template helpers (Angular can only access public methods).
  getXIStats() {
    return this.xiStats();
  }

  isWicketkeeper(p: TeamSquadPlayer): boolean {
    return this.isWicketkeeperCandidate(p);
  }

  toggleXIPlayer(team: 'A' | 'B', category: 'batters' | 'allrounders' | 'bowlers', p: TeamSquadPlayer) {
    const key = this.getXIPlayerKey(team, category, p);
    const exists = this.matchCentreXISelected.some(
      (x) => this.getXIPlayerKey(x.team, x.category, x.player) === key
    );

    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;

    if (exists) {
      this.matchCentreXISelected = this.matchCentreXISelected.filter(
        (x) => this.getXIPlayerKey(x.team, x.category, x.player) !== key
      );
      // If player is removed and was selected as C or WK, clear it.
      if (this.matchCentreXICaptainKey === key) this.matchCentreXICaptainKey = null;
      if (this.matchCentreXIWkKey === key) this.matchCentreXIWkKey = null;
      if (this.matchCentreXIImpactKey === key) this.matchCentreXIImpactKey = null;
      return;
    }

    const stats = this.xiStats();
    if (stats.total >= 11) {
      this.matchCentreXIError = 'XI can include max 11 players.';
      return;
    }

    this.matchCentreXISelected = [...this.matchCentreXISelected, { team, category, player: p }];
  }

  chooseCaptain(team: 'A' | 'B', category: 'batters' | 'allrounders' | 'bowlers', p: TeamSquadPlayer) {
    const key = this.getXIPlayerKey(team, category, p);
    this.matchCentreXIError = null;
    this.matchCentreXIMsg = null;
    this.matchCentreXICaptainKey = key;
  }

  chooseWK(team: 'A' | 'B', category: 'batters' | 'allrounders' | 'bowlers', p: TeamSquadPlayer) {
    const key = this.getXIPlayerKey(team, category, p);
    this.matchCentreXIError = null;
    this.matchCentreXIMsg = null;

    if (category !== 'batters') {
      this.matchCentreXIError = 'WK must be selected from BATTERS only.';
      this.matchCentreXIWkKey = null;
      return;
    }

    this.matchCentreXIWkKey = key;
  }

  isCaptain(team: 'A' | 'B', category: 'batters' | 'allrounders' | 'bowlers', p: TeamSquadPlayer): boolean {
    return this.matchCentreXICaptainKey === this.getXIPlayerKey(team, category, p);
  }

  isWK(team: 'A' | 'B', category: 'batters' | 'allrounders' | 'bowlers', p: TeamSquadPlayer): boolean {
    return this.matchCentreXIWkKey === this.getXIPlayerKey(team, category, p);
  }

  chooseImpact(team: 'A' | 'B', category: 'batters' | 'allrounders' | 'bowlers', p: TeamSquadPlayer) {
    const key = this.getXIPlayerKey(team, category, p);
    // Impact player should not be one of the XI.
    if (this.matchCentreXISelected.some((s) => this.getXIPlayerKey(s.team, s.category, s.player) === key)) {
      this.matchCentreXIError = 'Impact player must be different from the Playing XI.';
      return;
    }
    this.matchCentreXIImpactKey = key;
    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;
  }

  clearImpact() {
    this.matchCentreXIImpactKey = null;
  }

  getImpactLabel(): string {
    if (!this.matchCentreXIImpactKey || !this.selectedUpcoming) return '';
    const [team, category, id, img, name] = this.matchCentreXIImpactKey.split('|');
    const t = team === 'A' ? this.getTeamCodeDisplay(this.selectedUpcoming.team_home) : this.getTeamCodeDisplay(this.selectedUpcoming.team_away);
    const n = (name || '').trim();
    if (!n) return '';
    const cat = category === 'batters' ? 'BAT' : category === 'allrounders' ? 'AR' : 'BOW';
    return `${t} • ${n} (${cat})`;
  }

  confirmXI() {
    const stats = this.xiStats();
    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;

    const parts: string[] = [];
    if (stats.total !== 11) parts.push('select exactly 11 players');
    if (!stats.okBowl) parts.push('select minimum 5 bowlers (allrounders count)');
    if (!this.matchCentreXICaptainKey) parts.push('select the captain');
    if (!this.matchCentreXIWkKey) parts.push('select the WK');

    if (parts.length) {
      this.matchCentreXIError = `To confirm: ${parts.join(', ')}.`;
      return;
    }

    const wkSel = this.matchCentreXISelected.find((s) => this.getXIPlayerKey(s.team, s.category, s.player) === this.matchCentreXIWkKey);
    if (!wkSel || wkSel.category !== 'batters') {
      this.matchCentreXIError = 'WK must be selected from BATTERS only.';
      this.matchCentreXIWkKey = null;
      return;
    }

    this.matchCentreXIFantasyConfirmed = true;
    this.matchCentreXIMsg = null;
  }

  closeFantasyXI() {
    this.matchCentreXIFantasyConfirmed = false;
    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;
  }

  backToEditXI() {
    this.matchCentreXIFantasyConfirmed = false;
    this.matchCentreXIMsg = null;
    this.matchCentreXIError = null;
  }

  takeFantasyXIScreenshot() {
    const el = document.getElementById('fantasyXI-capture');
    if (!el) return;
    this.matchCentreXIScreenshotLoading = true;
    this.matchCentreXIError = null;

    // html2canvas may fail if the player images don't allow CORS.
    html2canvas(el, { useCORS: true, backgroundColor: '#ffffff', scale: 2 })
      .then((canvas) => {
        const link = document.createElement('a');
        const stamp = new Date().toISOString().slice(0, 10);
        link.download = `fantasy-xi-${stamp}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
      })
      .catch(() => {
        this.matchCentreXIError = 'Screenshot failed (player images may block CORS).';
      })
      .finally(() => {
        this.matchCentreXIScreenshotLoading = false;
      });
  }

  isXISelected(team: 'A' | 'B', category: 'batters' | 'allrounders' | 'bowlers', p: TeamSquadPlayer): boolean {
    const key = this.getXIPlayerKey(team, category, p);
    return this.matchCentreXISelected.some((x) => this.getXIPlayerKey(x.team, x.category, x.player) === key);
  }

  private getIplTeamIdByCode(code: string): string {
    const c = (code || '').toUpperCase();
    const map: Record<string, string> = {
      RCB: '59',
      SRH: '255',
      CSK: '58',
      MI: '62',
      KKR: '63',
      RR: '64',
      PBKS: '65',
      GT: '971',
      LSG: '966',
      DC: '61',
    };
    return map[c] || '';
  }

  private parseSquad(resp: TeamSquadResponse | null | undefined) {
    const out = { batters: [] as TeamSquadPlayer[], allrounders: [] as TeamSquadPlayer[], bowlers: [] as TeamSquadPlayer[] };
    const rows = resp?.player || [];
    let section = '';
    for (const r of rows) {
      const name = (r?.name || '').toString().trim();
      const hasId = !!(r as any)?.id;
      if (!hasId) {
        section = name.toUpperCase();
        continue;
      }
      if (section.includes('BATSMEN') || section.includes('WICKET')) out.batters.push(r);
      else if (section.includes('ALL ROUNDER')) out.allrounders.push(r);
      else if (section.includes('BOWLER')) out.bowlers.push(r);
      else out.batters.push(r);
    }
    return out;
  }

  private buildDerivedSquadFromScorecard(teamName: string) {
    const out = { batters: [] as TeamSquadPlayer[], allrounders: [] as TeamSquadPlayer[], bowlers: [] as TeamSquadPlayer[] };
    const innings = Array.isArray(this.matchCentreScorecardData?.scorecard) ? this.matchCentreScorecardData!.scorecard! : [];
    if (!innings.length) return out;

    const normTeam = (this.getDisplayTeamName(teamName) || '').toLowerCase();
    const own = innings.find((inn: any) => String(inn?.inning || '').toLowerCase().includes(normTeam));
    if (!own) return out;

    const toPlayer = (name: string): TeamSquadPlayer => ({
      id: 0 as any,
      name,
      role: '',
      battingStyle: '',
      bowlingStyle: '',
      imageId: undefined,
    } as TeamSquadPlayer);

    out.batters = (Array.isArray((own as any)?.batting) ? (own as any).batting : [])
      .map((b: any) => String(b?.batsman?.name || '').trim())
      .filter((n: string) => !!n)
      .filter((n: string, i: number, a: string[]) => a.indexOf(n) === i)
      .map(toPlayer);

    const bowlingSource = innings.filter((inn: any) => !String(inn?.inning || '').toLowerCase().includes(normTeam));
    const bowlingRows: any[] = [];
    for (const inn of bowlingSource) {
      if (Array.isArray(inn?.bowling)) bowlingRows.push(...inn.bowling);
    }
    out.bowlers = bowlingRows
      .map((b: any) => String(b?.bowler?.name || '').trim())
      .filter((n: string) => !!n)
      .filter((n: string, i: number, a: string[]) => a.indexOf(n) === i)
      .map(toPlayer);

    return out;
  }

  private loadMatchCentreSquadsIfNeeded() {
    if (!this.selectedUpcoming) return;
    if (this.matchCentreSquadA && this.matchCentreSquadB) return;

    const aTeam = this.selectedUpcoming.team_home;
    const bTeam = this.selectedUpcoming.team_away;
    const isBbl = this.isBblSeries(this.selectedUpcoming.series_name);
    const isWc = this.isIccMensT20WorldCupSeries(this.selectedUpcoming.series_name);

    const aCode = this.getIplTeamCode(aTeam);
    const bCode = this.getIplTeamCode(bTeam);
    const aPsl = this.getPslTeamKey(aTeam);
    const bPsl = this.getPslTeamKey(bTeam);

    let aId = "";
    let bId = "";
    if (isWc) {
      const applyDerived = () => {
        this.matchCentreSquadA = this.buildDerivedSquadFromScorecard(this.selectedUpcoming!.team_home);
        this.matchCentreSquadB = this.buildDerivedSquadFromScorecard(this.selectedUpcoming!.team_away);
        this.matchCentreSquadLoading = false;
      };
      if (this.matchCentreScorecardData) {
        applyDerived();
        return;
      }
      this.matchCentreSquadLoading = true;
      this.loadMatchCentreScorecardIfNeeded();
      setTimeout(() => applyDerived(), 450);
      return;
    } else if (isBbl) {
      // For BBL we pass the team display code directly to the team-squad endpoint.
      aId = this.getTeamCodeDisplay(aTeam);
      bId = this.getTeamCodeDisplay(bTeam);
    } else if (aCode && bCode) {
      aId = this.getIplTeamIdByCode(aCode);
      bId = this.getIplTeamIdByCode(bCode);
    } else if (aPsl && bPsl) {
      // PSL squads are seeded manually into backend cache using these ids.
      aId = `psl-${this.getTeamCodeDisplay(this.selectedUpcoming.team_home)}`;
      bId = `psl-${this.getTeamCodeDisplay(this.selectedUpcoming.team_away)}`;
    } else {
      return;
    }
    if (!aId || !bId) return;

    this.matchCentreSquadLoading = true;
    forkJoin({
      a: this.cricketService.getTeamSquad(aId),
      b: this.cricketService.getTeamSquad(bId),
    }).subscribe({
      next: ({ a, b }) => {
        this.matchCentreSquadA = this.parseSquad(a);
        this.matchCentreSquadB = this.parseSquad(b);
        this.matchCentreSquadLoading = false;
      },
      error: () => {
        this.matchCentreSquadA = null;
        this.matchCentreSquadB = null;
        this.matchCentreSquadLoading = false;
      }
    });
  }

  getCricbuzzPlayerImageUrl(imageId: number | null | undefined): string {
    const id = Number(imageId);
    if (!Number.isFinite(id) || id <= 0) return '';
    return `https://www.cricbuzz.com/a/img/v1/152x152/i1/c${id}/i.jpg`;
  }

  // ---- Teams page helpers ----

  getIplTeamsList(): string[] {
    return ['CSK', 'DC', 'GT', 'KKR', 'LSG', 'MI', 'PBKS', 'RR', 'RCB', 'SRH'];
  }

  getPslTeamsList(): string[] {
    // PSL keys as used in getPslTeamKey
    return ['HK', 'IU', 'KK', 'LQ', 'MS', 'PZ', 'PND', 'QG'];
  }

  getPslTeamFullName(key: string): string {
    const map: Record<string, string> = {
      HK: 'Hyderabad Kingsmen',
      IU: 'Islamabad United',
      KK: 'Karachi Kings',
      LQ: 'Lahore Qalandars',
      MS: 'Multan Sultans',
      PZ: 'Peshawar Zalmi',
      PND: 'Pindiz',
      QG: 'Quetta Gladiators',
    };
    return map[key] || key;
  }

  openTeamsLeague(league: 'ipl' | 'psl' | 'bbl') {
    this.teamPageLeague = league;
    this.teamPageSelectedCode = null;
    this.teamPageTab = 'matches';
    this.teamPageSquad = null;
    this.teamPageSquadLoading = false;
  }

  selectTeamForView(code: string) {
    this.teamPageSelectedCode = code;
    this.teamPageTab = 'matches';
    this.teamPageSquad = null;
    this.teamPageSquadLoading = false;
  }

  setTeamPageTab(tab: 'matches' | 'squad') {
    this.teamPageTab = tab;
    if (tab === 'squad') {
      this.loadTeamPageSquadIfNeeded();
    }
  }

  private loadTeamPageSquadIfNeeded() {
    if (!this.teamPageSelectedCode) return;
    if (this.teamPageSquad) return;

    let teamId = '';
    if (this.teamPageLeague === 'ipl') {
      teamId = this.getIplTeamIdByCode(this.teamPageSelectedCode);
    } else if (this.teamPageLeague === 'psl') {
      // PSL squads use the same id pattern as match centre: psl-<display code>
      const codeDisplay = this.getPslTeamCodeDisplay(this.teamPageSelectedCode);
      teamId = codeDisplay ? `psl-${codeDisplay}` : '';
    } else {
      // BBL squads are seeded into TeamSquadCache by team initials keys:
      // PS/SS/BH/MR/HH/AS/MS/ST
      teamId = this.getTeamCodeDisplay(this.teamPageSelectedCode);
    }
    if (!teamId) return;

    this.teamPageSquadLoading = true;
    this.cricketService.getTeamSquad(teamId).subscribe({
      next: (resp) => {
        this.teamPageSquad = this.parseSquad(resp);
        this.teamPageSquadLoading = false;
      },
      error: () => {
        this.teamPageSquad = null;
        this.teamPageSquadLoading = false;
      }
    });
  }

  getPslTeamCodeDisplay(key: string): string {
    const map: Record<string, string> = {
      HK: 'HKS',
      IU: 'ISU',
      KK: 'KRK',
      LQ: 'LHQ',
      MS: 'MS',
      PZ: 'PSZ',
      PND: 'PND',
      QG: 'QTG',
    };
    return map[key] || key;
  }

  getTeamPageFixtures(): UpcomingMatch[] {
    if (!this.teamPageSelectedCode) return [];
    const isIpl = this.teamPageLeague === 'ipl';
    const isBbl = this.teamPageLeague === 'bbl';

    return this.upcomingMatches.filter((m) => {
      const series = (m.series_name || '').toLowerCase();
      if (isIpl && !series.includes('indian premier league')) return false;
      if (!isIpl && !isBbl && !series.includes('pakistan super league')) return false;
      if (isBbl && !series.includes('big bash league')) return false;

      if (isBbl) {
        const homeName = this.getDisplayTeamName(m.team_home).toLowerCase();
        const awayName = this.getDisplayTeamName(m.team_away).toLowerCase();
        const sel = (this.teamPageSelectedCode || '').toLowerCase();
        return homeName === sel || awayName === sel;
      }

      const homeCode = isIpl ? this.getIplTeamCode(m.team_home) : this.getPslTeamKey(m.team_home);
      const awayCode = isIpl ? this.getIplTeamCode(m.team_away) : this.getPslTeamKey(m.team_away);
      return homeCode === this.teamPageSelectedCode || awayCode === this.teamPageSelectedCode;
    });
  }

  private teamMatchBelongsToSelected(match: { team_home: string; team_away: string }): boolean {
    if (!this.teamPageSelectedCode) return false;
    const isIpl = this.teamPageLeague === 'ipl';
    const isBbl = this.teamPageLeague === 'bbl';
    if (isBbl) {
      const homeName = this.getDisplayTeamName(match.team_home).toLowerCase();
      const awayName = this.getDisplayTeamName(match.team_away).toLowerCase();
      const sel = (this.teamPageSelectedCode || '').toLowerCase();
      return homeName === sel || awayName === sel;
    }
    const homeCode = isIpl ? this.getIplTeamCode(match.team_home) : this.getPslTeamKey(match.team_home);
    const awayCode = isIpl ? this.getIplTeamCode(match.team_away) : this.getPslTeamKey(match.team_away);
    return homeCode === this.teamPageSelectedCode || awayCode === this.teamPageSelectedCode;
  }

  private teamPageSeriesNameMatch(seriesName: string | null | undefined): boolean {
    const s = String(seriesName || '').toLowerCase();
    if (this.teamPageLeague === 'ipl') return s.includes('indian premier league');
    if (this.teamPageLeague === 'psl') return s.includes('pakistan super league');
    return s.includes('big bash league');
  }

  getTeamPageCompletedSeriesMatches(): Match[] {
    if (!this.teamPageSelectedCode) return [];
    const out: Match[] = [];
    for (const s of this.masterData || []) {
      if (!this.teamPageSeriesNameMatch(s?.name)) continue;
      for (const m of s.matches || []) {
        if (!this.teamMatchBelongsToSelected(m)) continue;
        if (!this.isFinishedStatusText(m.status)) continue;
        out.push(m);
      }
    }
    return out;
  }

  getTeamPageCompletedLiveResults(): LiveMatch[] {
    if (!this.teamPageSelectedCode || this.teamPageLeague === 'bbl') return [];
    const rows = (this.liveResults || []).filter((m) => {
      if (!this.teamPageSeriesNameMatch(m?.name)) return false;
      if (!this.teamMatchBelongsToSelected(m)) return false;
      return this.isFinishedStatusText(m?.status);
    });
    if (this.teamPageLeague === 'ipl' || this.teamPageLeague === 'psl') {
      return this.sortLeagueCompletedByRecentDateDesc(rows);
    }
    return rows;
  }

  openTeamPageCompletedMatchCentre(match: Match): void {
    if (this.teamPageLeague === 'bbl') {
      this.openBblMatchCentre(match, 'Big Bash League 2025-26');
      return;
    }
    const seriesName = this.teamPageLeague === 'ipl' ? this.getIplMasterSeriesLabel() : this.getPslMasterSeriesLabel();
    this.openGenericMatchCentre(match, seriesName);
  }

  getMatchCentreCountdown(): { d: number; h: number; m: number; s: number } | null {
    const startIso = this.selectedUpcoming?.start_time_utc;
    const start = startIso ? new Date(startIso).getTime() : NaN;
    const now = this.matchCentreNowMs || Date.now();
    if (!Number.isFinite(start)) return null;
    let diff = Math.max(0, start - now);
    const d = Math.floor(diff / (24 * 3600 * 1000)); diff -= d * 24 * 3600 * 1000;
    const h = Math.floor(diff / (3600 * 1000)); diff -= h * 3600 * 1000;
    const m = Math.floor(diff / (60 * 1000)); diff -= m * 60 * 1000;
    const s = Math.floor(diff / 1000);
    return { d, h, m, s };
  }

  pad2(n: number): string {
    const x = Math.max(0, Math.floor(n || 0));
    return x < 10 ? `0${x}` : `${x}`;
  }

  getWinColorClass(pct: number): string {
    if (pct >= 80) return 'good';
    if (pct < 50) return 'bad';
    return '';
  }

  getHighestColorClass(score: number): string {
    if (score > 200) return 'good';
    return '';
  }

  getLowestColorClass(score: number): string {
    if (score < 100) return 'bad';
    return '';
  }

  getBarPct(a: number, b: number): number {
    const aa = Number(a) || 0;
    const bb = Number(b) || 0;
    const tot = aa + bb;
    if (tot <= 0) return 50;
    return Math.max(0, Math.min(100, (aa / tot) * 100));
  }

  formatAvg(n: number): string {
    const x = Number(n);
    if (!Number.isFinite(x)) return '0';
    return x % 1 === 0 ? `${x}` : x.toFixed(2);
  }

  getTeamAccentColor(teamName: string): string {
    const code = this.getIplTeamCode(teamName);
    if (code) {
      if (code === 'CSK') return '#fbbf24';
      if (code === 'RR') return '#1d4ed8';
      if (code === 'RCB') return '#d4af37';
      if (code === 'PBKS') return '#ef4444';
      if (code === 'DC') return '#0b2f6b';
      if (code === 'KKR') return '#7c2d12';
      if (code === 'GT') return '#0b2f6b';
      if (code === 'LSG') return '#38bdf8';
      if (code === 'MI') return '#2563eb';
      if (code === 'SRH') return '#f97316';
    }
    const psl = this.getPslTeamKey(teamName);
    if (psl) {
      if (psl === 'HK') return '#d4af37';
      if (psl === 'IU') return '#f97316';
      if (psl === 'KK') return '#1B2A52';
      if (psl === 'LQ') return '#dc2626';
      if (psl === 'MS') return '#16a34a';
      if (psl === 'PZ') return '#d4a10a';
      if (psl === 'PND') return '#c2410c';
      if (psl === 'QG') return '#3B2F8F';
    }
    return '#64748b';
  }

  getFormChars(form: string | null | undefined): string[] {
    const s = (form || '').trim().toUpperCase();
    return s.split('').filter(ch => ch === 'W' || ch === 'L').slice(0, 10);
  }

  getTeamCodeDisplay(teamName: string): string {
    const ipl = this.getIplTeamCode(teamName);
    if (ipl) return ipl;
    const psl = this.getPslTeamKey(teamName);
    if (psl) {
      const map: Record<string, string> = {
        HK: 'HKS',
        IU: 'ISU',
        KK: 'KRK',
        LQ: 'LHQ',
        MS: 'MS',
        PZ: 'PSZ',
        PND: 'PND',
        QG: 'QTG',
      };
      return map[psl] || psl;
    }
    const n = (this.getDisplayTeamName(teamName) || '').trim();
    if (/^[A-Z]{2,4}$/.test(n)) return n;
    return this.getInitials(teamName);
  }

  toggleDarkMode() {
    this.darkMode = !this.darkMode;
  }

  isIccMensT20WorldCupSeries(seriesName: string | null | undefined): boolean {
    const n = (seriesName || '').toLowerCase();
    return n.includes('icc men') && n.includes('t20') && n.includes('world cup');
  }

  getTeamOversFromScorecard(match: Match, teamName: string): string {
    const sc: any = (match as any)?.scorecard_data;
    const score = sc?.score;
    if (!Array.isArray(score)) return '';
    const team = (this.getDisplayTeamName(teamName) || '').toLowerCase();
    const row = score.find((x: any) => {
      const inn = String(x?.inning || '').toLowerCase();
      return team && inn.includes(team);
    });
    const o = row?.o;
    if (o == null) return '';
    const ov = Number(o);
    if (!Number.isFinite(ov)) return '';
    return `(${ov.toFixed(1)} ov)`;
  }

  getTeamScoreLineFromScorecard(match: Match, teamName: string): string {
    const sc: any = (match as any)?.scorecard_data;
    const score = sc?.score;
    if (!Array.isArray(score)) return '';
    const team = (this.getDisplayTeamName(teamName) || '').toLowerCase();
    const row = score.find((x: any) => {
      const inn = String(x?.inning || '').toLowerCase();
      return team && inn.includes(team);
    });
    const r = row?.r;
    const w = row?.w;
    if (r == null) return '';
    const rr = Number(r);
    const ww = w == null ? 0 : Number(w);
    if (!Number.isFinite(rr) || !Number.isFinite(ww)) return '';
    return `${rr}/${ww}`;
  }

  formatBblOvers(o: number | undefined | null): string {
    const x = Number(o);
    if (!Number.isFinite(x)) return '';
    return x.toFixed(1);
  }

  private getBblScoreRows(match: Match): any[] {
    const sc: any = (match as any)?.scorecard_data;
    const rows = sc?.score;
    return Array.isArray(rows) ? rows : [];
  }

  getBblTeamByScoreIndex(match: Match, idx: number): string {
    const rows = this.getBblScoreRows(match);
    const row = rows[idx];
    if (!row?.inning) return idx === 0 ? match.team_home : match.team_away;
    return this.getDisplayTeamName(String(row.inning));
  }

  getBblScoreLineByScoreIndex(match: Match, idx: number): string {
    const rows = this.getBblScoreRows(match);
    const row = rows[idx];
    if (!row) return idx === 0 ? (match.home_score || '-') : (match.away_score || '-');
    const r = row.r ?? 0;
    const w = row.w ?? 0;
    return `${r}/${w}`;
  }

  getBblOversByScoreIndex(match: Match, idx: number): string {
    const rows = this.getBblScoreRows(match);
    const row = rows[idx];
    if (!row || row.o == null) return '';
    const ov = this.formatBblOvers(row.o);
    return ov ? `(${ov} ov)` : '';
  }

  getBblBowlersOppositionTeam(match: Match, battingIdx: number): string {
    // If scorecardData.score[0] is batting-first, scorecardData.score[1] is the other team.
    return battingIdx === 0 ? this.getBblTeamByScoreIndex(match, 1) : this.getBblTeamByScoreIndex(match, 0);
  }

  getBblTeamLabel(teamName: string | undefined | null): string {
    let n = String(teamName || '').trim();
    // scorecard JSON may use labels like "Sydney Sixers Inning 1" / "Innings 1"
    n = n.replace(/\s+Inning(s)?\s*\d+.*$/i, '').trim();
    return this.getDisplayTeamName(n) || n;
  }

  getMatchVenueFromScorecard(match: Match): string {
    const sc: any = (match as any)?.scorecard_data;
    return String(sc?.venue || '').trim();
  }

  getMatchDateFromScorecard(match: Match): string {
    const sc: any = (match as any)?.scorecard_data;
    return String(sc?.date || '').trim();
  }


  private getIplTeamCode(teamName: string): string {
    const n = (this.getDisplayTeamName(teamName) || '').toLowerCase();
    if (!n) return '';
    if (/\bchennai\b|\bsuper\s*kings\b|\bcsk\b/.test(n)) return 'CSK';
    if (/\bmumbai\b|\bindians\b|\bmi\b/.test(n)) return 'MI';
    if (/\broyal\s*challengers\b|\bbengaluru\b|\bbangalore\b|\brcb\b/.test(n)) return 'RCB';
    if (/\bkolkata\b|\bknight\s*riders\b|\bkkr\b/.test(n)) return 'KKR';
    if (/\brajasthan\b|\broyals\b|\brr\b/.test(n)) return 'RR';
    if (/\bdelhi\b|\bcapitals\b|\bdc\b/.test(n)) return 'DC';
    // Avoid matching generic "kings" (e.g., Karachi Kings, etc.)
    if (/\bpunjab\b|\bpbks\b|\bkings\s*xi\s*punjab\b/.test(n)) return 'PBKS';
    // Important: do NOT match generic "hyderabad" (PSL Kingsmen would get misclassified)
    if (/\bsunrisers\b|\bsrh\b|\bsunrisers\s+hyderabad\b/.test(n)) return 'SRH';
    if (/\bgujarat\b|\btitans\b|\bgt\b/.test(n)) return 'GT';
    if (/\blucknow\b|\bsuper\s*giants\b|\blsg\b/.test(n)) return 'LSG';
    return '';
  }

  private getPslTeamKey(teamName: string): string {
    const n = (this.getDisplayTeamName(teamName) || '').toLowerCase();
    if (!n) return '';
    if (n.includes('hyderabad') && n.includes('kingsmen')) return 'HK';
    if (n.includes('islamabad') && n.includes('united')) return 'IU';
    if (n.includes('karachi') && n.includes('kings')) return 'KK';
    if (n.includes('lahore') && n.includes('qalandars')) return 'LQ';
    if (n.includes('multan') && n.includes('sultans')) return 'MS';
    if (n.includes('peshawar') && n.includes('zalmi')) return 'PZ';
    if (n.includes('pindi') || n.includes('pindiz') || n.includes('rawalpindi')) return 'PND';
    if (n.includes('quetta') && (n.includes('gladiators') || n.includes('gladiots'))) return 'QG';
    return '';
  }

  getTeamRingBg(teamName: string): string {
    // Return CSS background value (solid or gradient) for logo ring.
    const n = (this.getDisplayTeamName(teamName) || '')
      .replace(/\s+Innings\s*\d+.*$/i, '')
      .trim()
      .toLowerCase();

    // BBL ring colors per your request
    if (/\bperth\s+scorchers\b/i.test(n)) return 'orange'; // ps-orange
    if (/\bsydney\s+sixers\b/i.test(n)) return '#db2777'; // dark pink
    if (/\bbrisbane\s+heat\b/i.test(n)) return '#27A6B0';
    if (/\bmelbourne\s+renegades\b/i.test(n)) return '#EE343F';
    if (/\bhobart\s+hurricanes\b/i.test(n)) return '#674398';
    if (/\bsydney\s+thunder\b/i.test(n)) return '#97D700';
    if (/\badelaide\s+strikers\b/i.test(n)) return '#0084D6';
    if (/\bmelbourne\s+stars\b/i.test(n)) return '#00C853'; // bright green

    // ICC Men's T20 World Cup team ring colors (flag-inspired)
    if (/\bindia\b/i.test(n)) return '#1E3A8A';
    if (/\bpakistan\b/i.test(n)) return '#166534';
    if (/\busa\b|\bunited\s+states(\s+of\s+america)?\b/i.test(n)) return '#B31942'; // Old Glory red
    if (/\bnetherlands\b/i.test(n)) return '#F97316'; // orange
    if (/\bnamibia\b/i.test(n)) return '#1E40AF';
    if (/\bzimbabwe\b/i.test(n)) return '#15803D';
    if (/\bsri\s+lanka\b/i.test(n)) return '#EAB308'; // orangish yellow
    if (/\baustralia\b/i.test(n)) return '#1F3A8A';
    if (/\bireland\b/i.test(n)) return '#16A34A';
    if (/\boman\b/i.test(n)) return '#DC2626';
    if (/\bwest\s+indies\b/i.test(n)) return '#7C2D12';
    if (/\bengland\b/i.test(n)) return '#DC2626'; // red
    if (/\bscotland\b/i.test(n)) return '#2563EB';
    if (/\bitaly\b/i.test(n)) return '#16A34A';
    if (/\bnepal\b/i.test(n)) return '#DC2626';
    if (/\bsouth\s+africa\b/i.test(n)) return '#047857';
    if (/\bnew\s+zealand\b/i.test(n)) return '#111827';
    if (/\bafghanistan\b/i.test(n)) return '#111827'; // black
    if (/\bunited\s+arab\s+emirates\b|\buae\b/i.test(n)) return '#059669';
    if (/\bcanada\b/i.test(n)) return '#B91C1C';

    const code = this.getIplTeamCode(teamName);
    if (code) {
      if (code === 'CSK') return '#fbbf24';
      if (code === 'RR') return 'linear-gradient(135deg, #ec4899, #3b82f6)';
      if (code === 'RCB') return '#d4af37';
      if (code === 'PBKS') return '#ef4444';
      if (code === 'DC') return '#0b2f6b';
      if (code === 'KKR') return 'linear-gradient(135deg, #0f172a, #d4af37)';
      if (code === 'GT') return '#0b2f6b';
      if (code === 'LSG') return '#38bdf8';
      if (code === 'MI') return '#2563eb';
      if (code === 'SRH') return '#f97316';
      return '';
    }

    const psl = this.getPslTeamKey(teamName);
    if (!psl) return '';

    // PSL ring colors per your request
    if (psl === 'HK') return 'linear-gradient(135deg, #0b1220, #d4af37)'; // black + goldish
    if (psl === 'IU') return 'linear-gradient(135deg, #ef4444, #f97316)'; // red + orangish
    if (psl === 'KK') return '#1B2A52'; // dark royal blue
    if (psl === 'LQ') return '#dc2626'; // reddish
    if (psl === 'MS') return 'linear-gradient(135deg, #0b2f6b, #16a34a)'; // deep royal blue + greenish
    if (psl === 'PZ') return '#d4a10a'; // dark yellow
    if (psl === 'PND') return '#c2410c'; // dark dark orange
    if (psl === 'QG') return '#3B2F8F'; // dark purple
    return '';
  }

  getBblTeamsList(): string[] {
    return [
      'Perth Scorchers',
      'Sydney Sixers',
      'Hobart Hurricanes',
      'Melbourne Stars',
      'Brisbane Heat',
      'Adelaide Strikers',
      'Melbourne Renegades',
      'Sydney Thunder',
    ];
  }
}