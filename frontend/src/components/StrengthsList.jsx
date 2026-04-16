import styles from './StrengthsList.module.css'

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <circle cx="8" cy="8" r="7.5" stroke="#00c3dc" strokeWidth="0.75" />
    <path
      d="M5 8l2 2 4-4"
      stroke="#00c3dc"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

export default function StrengthsList({ strengths }) {
  return (
    <div className={styles.card}>
      <p className={styles.title}>Strengths</p>
      <ul className={styles.list}>
        {strengths.map((s, i) => (
          <li key={i} className={styles.item}>
            <CheckIcon />
            <span>{s}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}