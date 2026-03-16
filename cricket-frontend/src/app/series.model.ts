export interface Match {
  external_id?: string;  // CricAPI match ID for scorecard
  name?: string;
  status: string;
  team_home: string;
  team_away: string;
  home_score?: string;
  away_score?: string;
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
}
