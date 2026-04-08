/**
 * IPL-style auction voice / commentary lines (randomised per event).
 */

function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]!;
}

/** Crore amounts in commentary: snap to nearest ¼ cr (e.g. 1.3 → 1.25, 2.8 → 2.75). */
function formatCroresQuarterCr(lakhs: number): string {
  const cr = lakhs / 100;
  const q = Math.round(cr * 4) / 4;
  const n = Math.round(q * 100) / 100;
  const whole = Math.floor(n + 1e-9);
  const frac = n - whole;
  if (frac <= 1e-6) {
    return `₹${whole} crore`;
  }
  const s = n.toFixed(2).replace(/\.?0+$/, '');
  return `₹${s} crore`;
}

/** Natural phrasing: ₹30 lakhs, ₹1 crore, ₹2.75 crore (¼-cr steps for crores) */
export function formatLakhsPhrase(lakhs: number): string {
  if (!Number.isFinite(lakhs) || lakhs <= 0) {
    return '₹—';
  }
  if (lakhs >= 100) {
    return formatCroresQuarterCr(lakhs);
  }
  return `₹${Math.round(lakhs)} lakhs`;
}

export interface TeamLite {
  id: string;
  short_code: string;
  name: string;
  is_user?: boolean;
}

// --- 1. Starting the Auction (new lot) ---
const OPENING_LINES_BASE = (amt: string) =>
  [
    `The bidding starts at ${amt}.`,
    `Base price set at ${amt}. Who will open the bidding?`,
    `Let's begin! Any takers for this player?`,
  ] as const;

export function pickOpeningLine(baseLakhs: number): string {
  const amt = formatLakhsPhrase(baseLakhs);
  return pick([...OPENING_LINES_BASE(amt)]);
}

// --- 2. First Bid ---
function firstBidLines(short: string, full: string, amt: string): string[] {
  return [
    `${short} starts the bidding at ${amt}.`,
    `${full} enter the race at ${amt}.`,
    `${short} opens the bid!`,
  ];
}

// --- 3. Increasing Bids ---
function raiseLines(short: string, full: string, amt: string): string[] {
  return [
    `${short} raises it to ${amt}.`,
    `${short} responds with ${amt}.`,
    `${short} jumps in at ${amt}.`,
    `${short} pushes the bid to ${amt}.`,
    `${full} go to ${amt}.`,
  ];
}

// --- 4. Competitive Bidding ---
const COMPETITIVE_GENERIC = [
  'A bidding war is underway!',
  'Both teams are not backing down!',
] as const;

export function pickCompetitiveTwoTeam(shortA: string, shortB: string): string {
  if (shortA && shortB) {
    return pick([
      `It's getting intense between ${shortA} and ${shortB}!`,
      `${shortA} and ${shortB} — neither side is backing off!`,
    ]);
  }
  return pick([...COMPETITIVE_GENERIC]);
}

// --- 5. New Team Joins ---
function newTeamLines(full: string, short: string): string[] {
  return [
    `${full} join the bidding!`,
    `Here comes ${short} into the contest!`,
    `${full} throw their hat in the ring!`,
  ];
}

// --- 6. Near Timer End ---
export const TIMER_GOING_ONCE = ['Going once...', 'Going once… any advance?'] as const;
export const TIMER_GOING_TWICE = ['Going twice...', 'Going twice…'] as const;
export const TIMER_LAST_CHANCE = ['Last chance for any other team!', 'Final call — any other bids?'] as const;

// --- 7. Sold ---
function soldLines(short: string, full: string, amt: string, playerName: string): string[] {
  return [
    `SOLD! ${short} gets ${playerName} for ${amt}!`,
    `And it's ${full} who secure the player!`,
    `What a buy by ${short}! ${playerName} for ${amt}.`,
  ];
}

// --- 8. Unsold ---
const UNSOLD = [
  'No bids for this player.',
  'The player remains UNSOLD.',
  "We'll move to the next player.",
] as const;

// --- 9. Auto-Bid / AI ---
function aiLines(short: string, full: string): string[] {
  return [
    `${short} quickly places another bid!`,
    `${short} jumps in with a smart bid!`,
    `${short} is showing strong interest in this player.`,
    `${full} stay aggressive here!`,
  ];
}

// --- 10. Budget Pressure ---
function budgetLines(short: string, full: string): string[] {
  return [
    `${short} is running low on budget!`,
    `${full} need to be careful with their remaining purse.`,
  ];
}

// --- 11. Squad Full (informational; rarely triggered from bid flow) ---
export function pickSquadFullLine(short: string, full: string): string {
  return pick([
    `${short} cannot bid further, squad is full.`,
    `${full} have reached maximum squad size.`,
  ]);
}

// --- 12. Big Moments ---
const BIG_JUMP = [
  "That's a huge jump in price!",
  'What a surprising bid!',
  'This could be a steal at this price!',
] as const;

function teamLabel(team: TeamLite): { short: string; full: string } {
  const short = team.short_code || team.name.slice(0, 3).toUpperCase();
  return { short, full: team.name };
}

export interface BidCommentaryInput {
  team: TeamLite;
  amountLakhs: number;
  /** First bid on this lot */
  isFirstBidOnLot: boolean;
  /** This team had not bid on this lot before */
  isNewTeamOnLot: boolean;
  /** Number of bids placed on this lot (including this one) */
  bidCountOnLot: number;
  /** Distinct teams that have bid this lot */
  distinctBiddersOnLot: number;
  /** Previous highest bid in lakhs before this bid */
  previousBidLakhs: number;
  /** Previous leader team id, if any */
  previousBidderId: string | null;
  /** True if bidding team is AI (not user-controlled) */
  isAiBidder: boolean;
  /** Remaining budget in lakhs for bidder */
  bidderBudgetLakhs: number;
}

export function pickBidCommentary(input: BidCommentaryInput): string {
  const { short, full } = teamLabel(input.team);
  const amt = formatLakhsPhrase(input.amountLakhs);
  const prevAmt = input.previousBidLakhs;

  // Big jump: e.g. +50L or +40% in one step
  const jump = input.amountLakhs - prevAmt;
  const bigJump = prevAmt > 0 && (jump >= 50 || jump >= prevAmt * 0.35);
  if (bigJump && Math.random() < 0.45) {
    return pick([...BIG_JUMP]);
  }

  if (input.bidderBudgetLakhs > 0 && input.bidderBudgetLakhs < 2000 && Math.random() < 0.2) {
    return pick(budgetLines(short, full));
  }

  if (input.isFirstBidOnLot) {
    return pick(firstBidLines(short, full, amt));
  }

  if (input.isNewTeamOnLot && Math.random() < 0.55) {
    return pick(newTeamLines(full, short));
  }

  if (input.distinctBiddersOnLot >= 2 && input.bidCountOnLot >= 4 && Math.random() < 0.28) {
    return pick([...COMPETITIVE_GENERIC]);
  }

  if (input.isAiBidder && Math.random() < 0.35) {
    return pick(aiLines(short, full));
  }

  return pick(raiseLines(short, full, amt));
}

export interface SoldCommentaryInput {
  team: TeamLite;
  playerName: string;
  soldPriceLakhs: number;
}

export function pickSoldCommentary(input: SoldCommentaryInput): string {
  const { short, full } = teamLabel(input.team);
  const amt = formatLakhsPhrase(input.soldPriceLakhs);
  return pick(soldLines(short, full, amt, input.playerName));
}

export function pickUnsoldCommentary(): string {
  return pick([...UNSOLD]);
}
