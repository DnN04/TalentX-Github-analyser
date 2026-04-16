import styles from './SkillCard.module.css'

const BADGE_CLASS = {
  Beginner: styles.beginner,
  Intermediate: styles.intermediate,
  Advanced: styles.advanced,
  Expert: styles.expert,
}

function formatCount(n) {
  if (n == null) return '—'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

export default function SkillCard({ username, skillLevel, meta = {} }) {
  const initials = username.slice(0, 2).toUpperCase()

  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <div className={styles.avatar}>
          <img
            src={`https://github.com/${username}.png?size=80`}
            alt={username}
            onError={(e) => {
              e.target.style.display = 'none'
              e.target.nextSibling.style.display = 'flex'
            }}
          />
          <span className={styles.initials} style={{ display: 'none' }}>
            {initials}
          </span>
        </div>
        <div className={styles.info}>
          <h2 className={styles.username}>{username}</h2>
          <p className={styles.url}>github.com/{username}</p>
        </div>
      </div>

      <div>
        <span className={`${styles.badge} ${BADGE_CLASS[skillLevel] ?? styles.beginner}`}>
          {skillLevel}
        </span>
      </div>

      <div className={styles.statsRow}>
        {[
          { label: 'Repos', value: formatCount(meta.repos) },
          { label: 'Stars', value: formatCount(meta.stars) },
          { label: 'Followers', value: formatCount(meta.followers) },
        ].map(({ label, value }) => (
          <div key={label} className={styles.stat}>
            <span className={styles.statValue}>{value}</span>
            <span className={styles.statLabel}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
