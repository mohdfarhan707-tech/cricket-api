export interface ScorecardBatsman {
  batsman: { name: string };
  dismissal?: string;
  'dismissal-text'?: string;
  r: number;
  b: number;
  '4s': number;
  '6s': number;
  sr: number;
}

export interface ScorecardBowler {
  bowler: { name: string };
  o: number;
  m: number;
  r: number;
  w: number;
  eco: number;
}

export interface ScorecardInning {
  inning: string;
  batting: ScorecardBatsman[];
  bowling: ScorecardBowler[];
}

export interface ScoreLine {
  r: number;
  w: number;
  o: number;
  inning: string;
}

export interface Scorecard {
  id: string;
  name: string;
  status: string;
  venue?: string;
  date?: string;
  matchType?: string;
  teams?: string[];
  teamInfo?: { name: string; shortname: string; img?: string }[];
  score?: ScoreLine[];
  scorecard?: ScorecardInning[];
}
