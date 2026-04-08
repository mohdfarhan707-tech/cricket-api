/**
 * IPL mini-auction UI: franchise grid (player list comes from API: auction/pool-preview/).
 */

export type IplFranchiseAccent =
  | 'mi'
  | 'csk'
  | 'rcb'
  | 'kkr'
  | 'rr'
  | 'srh'
  | 'dc'
  | 'pbks'
  | 'lsg'
  | 'gt';

export interface AuctionFranchise {
  code: string;
  name: string;
  accent: IplFranchiseAccent;
}

export const IPL_AUCTION_FRANCHISES: AuctionFranchise[] = [
  { code: 'MI', name: 'Mumbai Indians', accent: 'mi' },
  { code: 'CSK', name: 'Chennai Super Kings', accent: 'csk' },
  { code: 'RCB', name: 'Royal Challengers Bengaluru', accent: 'rcb' },
  { code: 'KKR', name: 'Kolkata Knight Riders', accent: 'kkr' },
  { code: 'RR', name: 'Rajasthan Royals', accent: 'rr' },
  { code: 'SRH', name: 'Sunrisers Hyderabad', accent: 'srh' },
  { code: 'DC', name: 'Delhi Capitals', accent: 'dc' },
  { code: 'PBKS', name: 'Punjab Kings', accent: 'pbks' },
  { code: 'LSG', name: 'Lucknow Super Giants', accent: 'lsg' },
  { code: 'GT', name: 'Gujarat Titans', accent: 'gt' },
];

export type PslFranchiseAccent = 'iu' | 'kk' | 'lq' | 'ms' | 'pz' | 'qg';

export interface PslAuctionFranchise {
  code: string;
  name: string;
  accent: PslFranchiseAccent;
}

export const PSL_AUCTION_FRANCHISES: PslAuctionFranchise[] = [
  { code: 'IU', name: 'Islamabad United', accent: 'iu' },
  { code: 'KK', name: 'Karachi Kings', accent: 'kk' },
  { code: 'LQ', name: 'Lahore Qalandars', accent: 'lq' },
  { code: 'MS', name: 'Multan Sultans', accent: 'ms' },
  { code: 'PZ', name: 'Peshawar Zalmi', accent: 'pz' },
  { code: 'QG', name: 'Quetta Gladiators', accent: 'qg' },
];

/** Map API short_code → CSS accent suffix (live squad / cards). */
export const IPL_CODE_ACCENT_MAP: Record<string, string> = Object.fromEntries(
  IPL_AUCTION_FRANCHISES.map((f) => [f.code, f.accent]),
);
export const PSL_CODE_ACCENT_MAP: Record<string, string> = Object.fromEntries(
  PSL_AUCTION_FRANCHISES.map((f) => [f.code, f.accent]),
);
