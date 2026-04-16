import styles from './AchievementBadges.module.css'

// Each badge has: id, icon (emoji-free SVG path), label, description, condition fn, tier (gold/silver/bronze/teal/purple)
function computeBadges(data) {
  const { talent_score, skill_level, feature_contributions, top_languages, _meta } = data
  const fc = feature_contributions
  const meta = _meta ?? {}

  const ALL = [
    {
      id: 'polyglot',
      icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z',
      label: 'Polyglot',
      desc: '5+ programming languages',
      tier: 'teal',
      earned: top_languages?.length >= 5,
    },
    {
      id: 'commit_king',
      icon: 'M17 12h-5v5h5v-5zM16 1v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-1V1h-2zm3 18H5V8h14v11z',
      label: 'Commit King',
      desc: 'Commit score 80+',
      tier: 'gold',
      earned: fc?.commits >= 80,
    },
    {
      id: 'star_power',
      icon: 'M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z',
      label: 'Star Power',
      desc: 'Star score 80+',
      tier: 'gold',
      earned: fc?.stars >= 80,
    },
    {
      id: 'expert_dev',
      icon: 'M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z',
      label: 'Expert Dev',
      desc: 'Reached Expert skill level',
      tier: 'purple',
      earned: skill_level === 'Expert',
    },
    {
      id: 'high_scorer',
      icon: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z',
      label: 'High Scorer',
      desc: 'Talent score 90+',
      tier: 'gold',
      earned: talent_score >= 90,
    },
    {
      id: 'repo_builder',
      icon: 'M20 6h-2.18c.07-.44.18-.88.18-1.36C18 2.53 15.48 1 13 1c-1.32 0-2.5.56-3.36 1.44L8 4.08 6.36 2.44C5.5 1.56 4.32 1 3 1 .52 1-2 2.53-2 4.64c0 .48.11.92.18 1.36H-2c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h22c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zM13 3c1.38 0 3 .76 3 1.64 0 1.1-1.35 2.26-4 3.16C9.35 6.9 8 5.74 8 4.64 8 3.76 9.62 3 11 3h2z',
      label: 'Repo Builder',
      desc: 'Repo score 80+',
      tier: 'silver',
      earned: fc?.repos >= 80,
    },
    {
      id: 'advanced_up',
      icon: 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z',
      label: 'Rising Star',
      desc: 'Advanced or above',
      tier: 'silver',
      earned: ['Advanced', 'Expert'].includes(skill_level),
    },
    {
      id: 'well_rounded',
      icon: 'M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 4l5 2.18V11c0 3.5-2.33 6.79-5 7.93-2.67-1.14-5-4.43-5-7.93V7.18L12 5z',
      label: 'Well Rounded',
      desc: 'All features scored 60+',
      tier: 'teal',
      earned: fc && Object.values(fc).every((v) => v >= 60),
    },
    {
      id: 'centurion',
      icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z',
      label: 'Centurion',
      desc: 'Perfect score of 100',
      tier: 'gold',
      earned: talent_score === 100,
    },
    {
      id: 'open_source',
      icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z',
      label: 'OSS Contributor',
      desc: 'Stars score above 50',
      tier: 'bronze',
      earned: fc?.stars >= 50,
    },
  ]

  return ALL
}

const TIER_STYLES = {
  gold:   { bg: 'rgba(255,200,70,0.1)',  border: 'rgba(255,200,70,0.35)',  icon: '#ffc846', label: '#ffc846' },
  silver: { bg: 'rgba(176,196,216,0.1)', border: 'rgba(176,196,216,0.3)', icon: '#b0c4d8', label: '#b0c4d8' },
  bronze: { bg: 'rgba(200,121,65,0.1)',  border: 'rgba(200,121,65,0.3)',  icon: '#c87941', label: '#c87941' },
  teal:   { bg: 'rgba(0,195,220,0.08)',  border: 'rgba(0,195,220,0.3)',   icon: '#00c3dc', label: '#00c3dc' },
  purple: { bg: 'rgba(167,139,250,0.1)', border: 'rgba(167,139,250,0.3)', icon: '#a78bfa', label: '#a78bfa' },
}

const TIER_LABELS = { gold: 'Gold', silver: 'Silver', bronze: 'Bronze', teal: 'Elite', purple: 'Rare' }

export default function AchievementBadges({ data }) {
  const badges = computeBadges(data)
  const earned = badges.filter((b) => b.earned)
  const locked = badges.filter((b) => !b.earned)

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.count}>{earned.length}/{badges.length} earned</span>
      </div>

      {earned.length > 0 && (
        <div className={styles.grid}>
          {earned.map((b) => {
            const t = TIER_STYLES[b.tier]
            return (
              <div
                key={b.id}
                className={styles.badge}
                style={{ background: t.bg, borderColor: t.border }}
                title={b.desc}
              >
                <div className={styles.iconWrap} style={{ color: t.icon }}>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                    <path d={b.icon} />
                  </svg>
                </div>
                <div className={styles.badgeLabel} style={{ color: t.label }}>{b.label}</div>
                <div className={styles.badgeTier}>{TIER_LABELS[b.tier]}</div>
                <div className={styles.badgeDesc}>{b.desc}</div>
              </div>
            )
          })}
        </div>
      )}

      {locked.length > 0 && (
        <>
          <p className={styles.lockedTitle}>Locked</p>
          <div className={styles.lockedRow}>
            {locked.map((b) => (
              <div key={b.id} className={styles.lockedBadge} title={b.desc}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style={{ opacity: 0.35 }}>
                  <path d={b.icon} />
                </svg>
                <span>{b.label}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
