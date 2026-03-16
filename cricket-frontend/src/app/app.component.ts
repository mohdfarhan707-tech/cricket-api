import { Component, OnInit } from '@angular/core';
import { CricketService, NewsItem } from './cricket.service';
import { Series, Match, LiveMatch } from './series.model';
import { Scorecard } from './scorecard.model';
import { FALLBACK_LOGO, getFallbackTeamLogoUrl, resolveTeamLogoUrl } from './team-logos';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  seriesData: Series[] = []; 
  masterData: Series[] = [];
  activeTab: string = 'all';
  private collapsedSeries = new Set<string>();

  liveMatches: LiveMatch[] = [];
  liveResults: LiveMatch[] = [];
  newsItems: NewsItem[] = [];

  selectedLeagueId: string = '';
  headerPage: 'home' | 'news' = 'home';

  scorecardModalOpen = false;
  scorecardLoading = false;
  scorecardError: string | null = null;
  scorecardData: Scorecard | null = null;
  selectedMatch: Match | null = null;

  constructor(private cricketService: CricketService) {}

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

    this.cricketService.getNews().subscribe({
      next: (data) => {
        this.newsItems = data || [];
      },
      error: (err) => console.error('News error:', err)
    });
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

  openHeaderPage(page: 'home' | 'news') {
    this.headerPage = page;
  }

  formatNewsDate(iso: string | null | undefined): string {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleString();
  }

  setLeague(series: Series | null) {
    this.selectedLeagueId = series?.external_id || '';
  }

  /** Center list series based on selected league and active tab rules. */
  getVisibleSeries(): Series[] {
    // Start from full master data
    let base = this.masterData;
    if (this.selectedLeagueId) {
      base = base.filter(s => s.external_id === this.selectedLeagueId);
    }

    if (this.activeTab === 'all') {
      return base;
    }
    if (this.activeTab === 'live') {
      // live tab is handled separately in template
      return base;
    }
    return base
      .map(series => ({
        ...series,
        matches: series.matches.filter(m => {
          const mStatus = (m.status || '').toLowerCase();
          if (this.activeTab === 'results') return mStatus === 'completed' || mStatus === 'result';
          return mStatus === this.activeTab;
        })
      }))
      .filter(series => series.matches.length > 0);
  }

  /** Finished live matches should appear only in All + Results. */
  getFinishedLiveResultsVisible(): LiveMatch[] {
    if (this.activeTab === 'all' || this.activeTab === 'results') return this.liveResults;
    return [];
  }

  /** Live matches only appear in Live tab. */
  getLiveMatchesVisible(): LiveMatch[] {
    if (this.activeTab !== 'live') return [];
    return this.liveMatches;
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
}