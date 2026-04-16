// Mock responses for development — keyed by lowercase GitHub username.
// Any unrecognized username falls back to "generic".
export const MOCK_DATA = {
  torvalds: {
    talent_score: 97,
    skill_level: 'Expert',
    top_languages: ['C', 'Shell', 'Makefile', 'Python', 'Perl'],
    strengths: [
      'Exceptional commit consistency across 30+ years of activity',
      'Pioneered one of the most influential open-source projects globally',
      'Extremely high language diversity across systems-level tooling',
      'Strong community engagement — thousands of forks and stars',
    ],
    feature_contributions: { commits: 92, repos: 78, stars: 99, languages: 85 },
    _meta: { repos: 12, stars: 187400, followers: 224000 },
  },
  gaearon: {
    talent_score: 91,
    skill_level: 'Expert',
    top_languages: ['JavaScript', 'TypeScript', 'HTML', 'CSS', 'Python'],
    strengths: [
      'Core contributor to React — one of the most widely used UI libraries',
      'Highly consistent open-source contribution over many years',
      'Deep specialization in JavaScript ecosystem and tooling',
      'High repository star count reflecting strong public impact',
    ],
    feature_contributions: { commits: 88, repos: 82, stars: 96, languages: 72 },
    _meta: { repos: 58, stars: 84000, followers: 93000 },
  },
  generic: {
    talent_score: 72,
    skill_level: 'Advanced',
    top_languages: ['JavaScript', 'TypeScript', 'Python', 'Go', 'Rust'],
    strengths: [
      'Consistent commit activity across the past 12 months',
      'Strong diversity across frontend and backend stacks',
      'Several high-starred repositories showing public impact',
      'Active open-source contributor with merged pull requests',
    ],
    feature_contributions: { commits: 68, repos: 74, stars: 61, languages: 80 },
    _meta: { repos: 34, stars: 420, followers: 312 },
  },
}

export function getMockData(username) {
  return MOCK_DATA[username.toLowerCase()] ?? MOCK_DATA.generic
}
