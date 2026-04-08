export interface Match {
  external_id?: string;  // CricAPI match ID for scorecard
  name?: string;
  status: string;
  team_home: string;
  team_away: string;
  home_score?: string;
  away_score?: string;
  scorecard_data?: any;
  /** Set when this object was built from a live-feed row (for UI rules). */
  from_live_feed?: boolean;
  /** Live API: true when the fixture has ended. */
  is_finished?: boolean;
}

export interface Series {
  name: string;
  external_id: string;
  matches: Match[];
}

export interface LiveMatch {
  external_id: string;
  name: string;
  status: string;
  team_home: string;
  team_away: string;
  home_score?: string;
  away_score?: string;
  is_live?: boolean;
  is_finished?: boolean;
  /** Present when scorecard was fetched and cached server-side */
  scorecard_data?: unknown;
}
