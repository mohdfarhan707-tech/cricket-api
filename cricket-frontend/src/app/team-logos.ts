export const FALLBACK_LOGO =
  'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Cricket_ball.svg/120px-Cricket_ball.svg.png';

type LogoRule = { test: RegExp; url: string };

// NOTE: We match by *team name text* coming from the API.
// Keep patterns forgiving to handle "Women", punctuation, or abbreviations.
const TEAM_LOGO_RULES: LogoRule[] = [
  // --- SA20 ---
  {
    test: /sunrisers\s+eastern\s+cape/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/thumb/8/82/Sunrisers_Eastern_Cape_Logo.svg/330px-Sunrisers_Eastern_Cape_Logo.svg.png',
  },
  {
    test: /joburg\s+super\s+kings/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/thumb/c/ca/Joburg_Super_Kings_Logo.svg/330px-Joburg_Super_Kings_Logo.svg.png',
  },
  {
    test: /\bmi\s+cape\s+town\b/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/thumb/5/53/MI_Cape_Town_%E2%80%93_Logo.svg/330px-MI_Cape_Town_%E2%80%93_Logo.svg.png',
  },
  {
    test: /paarl\s+royals/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/thumb/8/8e/Paarl_Royals_logo_%282%29.svg/330px-Paarl_Royals_logo_%282%29.svg.png',
  },
  {
    test: /pretoria\s+capitals/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/thumb/f/fa/Pretoria_Capitals_logo.svg/330px-Pretoria_Capitals_logo.svg.png',
  },
  {
    test: /durban('?s)?\s+super\s+giants/i,
    url: "https://upload.wikimedia.org/wikipedia/en/thumb/8/8c/Durban%27s_Super_Giants_Logo.svg/330px-Durban%27s_Super_Giants_Logo.svg.png",
  },

  // --- WPL ---
  {
    test: /mumbai\s+indians/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/thumb/c/cd/Mumbai_Indians_Logo.svg/330px-Mumbai_Indians_Logo.svg.png',
  },
  {
    test: /delhi\s+capitals/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/thumb/2/2f/Delhi_Capitals.svg/330px-Delhi_Capitals.svg.png',
  },
  {
    test: /royal\s+challengers\s+(bangalore|bengaluru)/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/thumb/d/d4/Royal_Challengers_Bengaluru_Logo.svg/330px-Royal_Challengers_Bengaluru_Logo.svg.png',
  },
  {
    test: /\bup\s+warriorz\b/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/a/a0/UP_Warriors%28z%29_WPL_logo.png',
  },
  {
    test: /gujarat\s+giants/i,
    url: 'https://upload.wikimedia.org/wikipedia/en/thumb/d/da/Gujarat_Giants_WPL_logo.svg/330px-Gujarat_Giants_WPL_logo.svg.png',
  },

  // --- ICC T20 World Cup (national teams – flags) ---
  // Italy before England so "England,Italy" gets Italy flag and logo
  { test: /italy/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/330px-Flag_of_Italy.svg.png' },
  { test: /\bindia\b/i, url: 'https://upload.wikimedia.org/wikipedia/en/thumb/4/41/Flag_of_India.svg/330px-Flag_of_India.svg.png' },
  { test: /\baustralia\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Flag_of_Australia_%28converted%29.svg/330px-Flag_of_Australia_%28converted%29.svg.png' },
  { test: /\bengland\b/i, url: 'https://upload.wikimedia.org/wikipedia/en/thumb/b/be/Flag_of_England.svg/330px-Flag_of_England.svg.png' },
  { test: /\bpakistan\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Flag_of_Pakistan.svg/330px-Flag_of_Pakistan.svg.png' },
  { test: /south\s+africa/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Flag_of_South_Africa.svg/330px-Flag_of_South_Africa.svg.png' },
  { test: /new\s+zealand/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Flag_of_New_Zealand.svg/330px-Flag_of_New_Zealand.svg.png' },
  { test: /west\s+indies/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/WestIndiesCricketFlagPre1999.svg/330px-WestIndiesCricketFlagPre1999.svg.png' },
  { test: /sri\s+lanka/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Flag_of_Sri_Lanka.svg/330px-Flag_of_Sri_Lanka.svg.png' },
  { test: /\bafghanistan\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Flag_of_Afghanistan_%282013%E2%80%932021%29.svg/330px-Flag_of_Afghanistan_%282013%E2%80%932021%29.svg.png' },
  { test: /\bbangladesh\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Flag_of_Bangladesh.svg/330px-Flag_of_Bangladesh.svg.png' },
  { test: /\bireland\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Flag_of_Ireland.svg/330px-Flag_of_Ireland.svg.png' },
  { test: /\bzimbabwe\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Flag_of_Zimbabwe.svg/330px-Flag_of_Zimbabwe.svg.png' },
  { test: /\bscotland\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Flag_of_Scotland.svg/330px-Flag_of_Scotland.svg.png' },
  { test: /netherlands|holland/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Flag_of_the_Netherlands.svg/330px-Flag_of_the_Netherlands.svg.png' },
  { test: /\busa\b|united\s+states|america/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Flag_of_the_United_States.svg/330px-Flag_of_the_United_States.svg.png' },
  { test: /\bcanada\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Flag_of_Canada.svg/330px-Flag_of_Canada.svg.png' },
  { test: /\bnamibia\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Flag_of_Namibia.svg/330px-Flag_of_Namibia.svg.png' },
  { test: /\buganda\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Flag_of_Uganda.svg/330px-Flag_of_Uganda.svg.png' },
  { test: /\boman\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Flag_of_Oman.svg/330px-Flag_of_Oman.svg.png' },
  { test: /\bnepal\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Flag_of_Nepal.svg/330px-Flag_of_Nepal.svg.png' },
  { test: /uae|united\s+arab\s+emirates/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/330px-Flag_of_the_United_Arab_Emirates.svg.png' },
  { test: /\bpapua\s+new\s+guinea\b|png\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Flag_of_Papua_New_Guinea.svg/330px-Flag_of_Papua_New_Guinea.svg.png' },
  { test: /\bsaudi\s+arabia\b/i, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Flag_of_Saudi_Arabia.svg/330px-Flag_of_Saudi_Arabia.svg.png' },
];

export function resolveTeamLogoUrl(teamName: string | null | undefined): string {
  const name = (teamName || '').trim();
  if (!name) return FALLBACK_LOGO;
  const hit = TEAM_LOGO_RULES.find((r) => r.test.test(name));
  return hit?.url ?? FALLBACK_LOGO;
}

export function getFallbackTeamLogoUrl(): string {
  return FALLBACK_LOGO;
}

