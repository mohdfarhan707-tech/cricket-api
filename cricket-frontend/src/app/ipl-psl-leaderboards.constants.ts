/**
 * IPL / PSL player leaderboards (Orange & Purple caps, PSL batting/bowling).
 * Source: user-provided 2026 season snapshots. Update rows in this file as the season progresses.
 *
 * Note: IPL Purple Cap rows 2–5 are illustrative placeholders — replace with official stats when available.
 */

export interface IplOrangeCapRow {
  pos: number;
  name: string;
  teamShort: string;
  runs: number;
  mat: number;
  inns: number;
  notOut: number;
  hs: string;
  avg: number;
  bf: number;
  sr: number;
  hundreds: number;
  fifties: number;
  fours: number;
  sixes: number;
}

export interface IplPurpleCapRow {
  pos: number;
  name: string;
  teamShort: string;
  wkts: number;
  mat: number;
  inns: number;
  overs: string;
  runsConc: number;
  bbi: string;
  avg: number;
  econ: number;
  sr: number;
  fourW: number;
  fiveW: number;
}

export interface PslMostRunsRow {
  pos: number;
  name: string;
  teamShort: string;
  span: string;
  mat: number;
  inns: number;
  notOut: number;
  runs: number;
  hs: string;
  avg: number;
  bf: number;
  sr: number;
  hundreds: number;
  fifties: number;
  ducks: number;
  fours: number;
  sixes: number;
}

export interface PslMostWicketsRow {
  pos: number;
  name: string;
  teamShort: string;
  span: string;
  mat: number;
  inns: number;
  balls: number;
  overs: string;
  mdns: number;
  runsConc: number;
  wkts: number;
  bbi: string;
  avg: number;
  econ: number;
  sr: number;
  fourW: number;
  fiveW: number;
}

export const IPL_ORANGE_CAP_2026: IplOrangeCapRow[] = [
  {
    pos: 1,
    name: 'Sameer Rizvi',
    teamShort: 'DC',
    runs: 160,
    mat: 2,
    inns: 2,
    notOut: 1,
    hs: '90',
    avg: 160.0,
    bf: 98,
    sr: 163.26,
    hundreds: 0,
    fifties: 2,
    fours: 12,
    sixes: 11,
  },
  {
    pos: 2,
    name: 'Heinrich Klaasen',
    teamShort: 'SRH',
    runs: 145,
    mat: 3,
    inns: 3,
    notOut: 0,
    hs: '62',
    avg: 48.33,
    bf: 98,
    sr: 147.95,
    hundreds: 0,
    fifties: 2,
    fours: 11,
    sixes: 4,
  },
  {
    pos: 3,
    name: 'Rohit Sharma',
    teamShort: 'MI',
    runs: 113,
    mat: 2,
    inns: 2,
    notOut: 0,
    hs: '78',
    avg: 56.5,
    bf: 64,
    sr: 176.56,
    hundreds: 0,
    fifties: 1,
    fours: 11,
    sixes: 7,
  },
  {
    pos: 4,
    name: 'Devdutt Padikkal',
    teamShort: 'RCB',
    runs: 111,
    mat: 2,
    inns: 2,
    notOut: 0,
    hs: '61',
    avg: 55.5,
    bf: 55,
    sr: 201.81,
    hundreds: 0,
    fifties: 2,
    fours: 12,
    sixes: 6,
  },
  {
    pos: 5,
    name: 'Cooper Connolly',
    teamShort: 'PBKS',
    runs: 108,
    mat: 2,
    inns: 2,
    notOut: 1,
    hs: '72*',
    avg: 108.0,
    bf: 66,
    sr: 163.63,
    hundreds: 0,
    fifties: 1,
    fours: 11,
    sixes: 5,
  },
];

/** Row 1 from provided snapshot; rows 2–5 illustrative — replace from official leaderboard. */
export const IPL_PURPLE_CAP_2026: IplPurpleCapRow[] = [
  {
    pos: 1,
    name: 'Ravi Bishnoi',
    teamShort: 'RR',
    wkts: 5,
    mat: 2,
    inns: 2,
    overs: '7.0',
    runsConc: 57,
    bbi: '4/27',
    avg: 11.4,
    econ: 8.14,
    sr: 8.4,
    fourW: 1,
    fiveW: 0,
  },
  {
    pos: 2,
    name: 'Varun Chakaravarthy',
    teamShort: 'KKR',
    wkts: 4,
    mat: 3,
    inns: 3,
    overs: '10.0',
    runsConc: 72,
    bbi: '3/21',
    avg: 18.0,
    econ: 7.2,
    sr: 15.0,
    fourW: 0,
    fiveW: 0,
  },
  {
    pos: 3,
    name: 'Mohammed Siraj',
    teamShort: 'GT',
    wkts: 4,
    mat: 2,
    inns: 2,
    overs: '8.0',
    runsConc: 61,
    bbi: '3/24',
    avg: 15.25,
    econ: 7.62,
    sr: 12.0,
    fourW: 0,
    fiveW: 0,
  },
  {
    pos: 4,
    name: 'Trent Boult',
    teamShort: 'MI',
    wkts: 4,
    mat: 3,
    inns: 3,
    overs: '11.2',
    runsConc: 84,
    bbi: '3/28',
    avg: 21.0,
    econ: 7.41,
    sr: 17.0,
    fourW: 0,
    fiveW: 0,
  },
  {
    pos: 5,
    name: 'Yuzvendra Chahal',
    teamShort: 'PBKS',
    wkts: 3,
    mat: 2,
    inns: 2,
    overs: '7.4',
    runsConc: 52,
    bbi: '2/19',
    avg: 17.33,
    econ: 6.78,
    sr: 15.33,
    fourW: 0,
    fiveW: 0,
  },
];

export const PSL_MOST_RUNS_2026: PslMostRunsRow[] = [
  {
    pos: 1,
    name: 'Sameer Minhas',
    teamShort: 'IU',
    span: '2026-2026',
    mat: 3,
    inns: 3,
    notOut: 1,
    runs: 180,
    hs: '82*',
    avg: 90.0,
    bf: 105,
    sr: 171.42,
    hundreds: 0,
    fifties: 2,
    ducks: 0,
    fours: 16,
    sixes: 9,
  },
  {
    pos: 2,
    name: 'Sahibzada Farhan',
    teamShort: 'MS',
    span: '2026-2026',
    mat: 4,
    inns: 4,
    notOut: 1,
    runs: 164,
    hs: '106*',
    avg: 54.66,
    bf: 90,
    sr: 182.22,
    hundreds: 1,
    fifties: 0,
    ducks: 0,
    fours: 12,
    sixes: 12,
  },
  {
    pos: 3,
    name: 'Hasan Nawaz',
    teamShort: 'QG',
    span: '2026-2026',
    mat: 4,
    inns: 4,
    notOut: 1,
    runs: 158,
    hs: '66*',
    avg: 52.66,
    bf: 122,
    sr: 129.5,
    hundreds: 0,
    fifties: 2,
    ducks: 0,
    fours: 13,
    sixes: 6,
  },
  {
    pos: 4,
    name: 'SPD Smith',
    teamShort: 'MS',
    span: '2026-2026',
    mat: 4,
    inns: 4,
    notOut: 0,
    runs: 139,
    hs: '53',
    avg: 34.75,
    bf: 88,
    sr: 157.95,
    hundreds: 0,
    fifties: 1,
    ducks: 0,
    fours: 12,
    sixes: 8,
  },
  {
    pos: 5,
    name: 'Saud Shakeel',
    teamShort: 'QG',
    span: '2026-2026',
    mat: 4,
    inns: 4,
    notOut: 0,
    runs: 135,
    hs: '56',
    avg: 33.75,
    bf: 96,
    sr: 140.62,
    hundreds: 0,
    fifties: 1,
    ducks: 0,
    fours: 15,
    sixes: 4,
  },
];

export const PSL_MOST_WICKETS_2026: PslMostWicketsRow[] = [
  {
    pos: 1,
    name: 'Hasan Ali',
    teamShort: 'KK',
    span: '2026-2026',
    mat: 3,
    inns: 3,
    balls: 72,
    overs: '12.0',
    mdns: 0,
    runsConc: 76,
    wkts: 8,
    bbi: '4/27',
    avg: 9.5,
    econ: 6.33,
    sr: 9.0,
    fourW: 1,
    fiveW: 0,
  },
  {
    pos: 2,
    name: 'Shaheen Shah Afridi',
    teamShort: 'LQ',
    span: '2026-2026',
    mat: 3,
    inns: 3,
    balls: 66,
    overs: '11.0',
    mdns: 0,
    runsConc: 78,
    wkts: 6,
    bbi: '4/18',
    avg: 13.0,
    econ: 7.09,
    sr: 11.0,
    fourW: 1,
    fiveW: 0,
  },
  {
    pos: 3,
    name: 'Abrar Ahmed',
    teamShort: 'QG',
    span: '2026-2026',
    mat: 4,
    inns: 4,
    balls: 96,
    overs: '16.0',
    mdns: 0,
    runsConc: 133,
    wkts: 6,
    bbi: '3/23',
    avg: 22.16,
    econ: 8.31,
    sr: 16.0,
    fourW: 0,
    fiveW: 0,
  },
  {
    pos: 4,
    name: 'Shadab Khan',
    teamShort: 'IU',
    span: '2026-2026',
    mat: 3,
    inns: 3,
    balls: 60,
    overs: '10.0',
    mdns: 0,
    runsConc: 79,
    wkts: 5,
    bbi: '3/23',
    avg: 15.8,
    econ: 7.9,
    sr: 12.0,
    fourW: 0,
    fiveW: 0,
  },
  {
    pos: 5,
    name: 'Ahmed Daniyal',
    teamShort: 'QG',
    span: '2026-2026',
    mat: 4,
    inns: 3,
    balls: 68,
    overs: '11.2',
    mdns: 0,
    runsConc: 91,
    wkts: 5,
    bbi: '3/36',
    avg: 18.2,
    econ: 8.02,
    sr: 13.6,
    fourW: 0,
    fiveW: 0,
  },
];
