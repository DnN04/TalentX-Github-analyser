import { useEffect, useState } from 'react'
import styles from './ScoreCard.module.css'

function getScoreStyle(score) {
  if (score < 40) return { color: '#e85d5d', bar: '#e85d5d' }
  if (score <= 70) return { color: '#f5a623', bar: '#f5a623' }
  return { color: '#00c3dc', bar: '#00c3dc' }
}

export default function ScoreCard({ score }) {
  const [animated, setAnimated] = useState(false)
  const style = getScoreStyle(score)

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 80)
    return () => clearTimeout(t)
  }, [score])

  return (
    <div className={styles.card}>
      <span className={styles.label}>Talent Score</span>
      <span className={styles.number} style={{ color: style.color }}>
        {score}
      </span>
      <span className={styles.sub}>out of 100</span>
      <div className={styles.barTrack}>
        <div
          className={styles.barFill}
          style={{
            width: animated ? `${score}%` : '0%',
            background: style.bar,
          }}
        />
      </div>
    </div>
  )
}