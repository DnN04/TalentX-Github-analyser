import styles from './LanguagePills.module.css'

const LANG_COLORS = {
  JavaScript: '#f1e05a',
  TypeScript: '#3178c6',
  Python: '#3572a5',
  Go: '#00add8',
  Rust: '#dea584',
  C: '#555555',
  'C++': '#f34b7d',
  'C#': '#178600',
  Java: '#b07219',
  Ruby: '#701516',
  PHP: '#4f5d95',
  Swift: '#ffac45',
  Kotlin: '#a97bff',
  Shell: '#89e051',
  HTML: '#e34c26',
  CSS: '#563d7c',
  Makefile: '#427819',
  Perl: '#0298c3',
  Scala: '#c22d40',
  Haskell: '#5e5086',
}

export default function LanguagePills({ languages }) {
  return (
    <div className={styles.card}>
      <p className={styles.title}>Top Languages</p>
      <div className={styles.pills}>
        {languages.map((lang) => (
          <span key={lang} className={styles.pill}>
            <span
              className={styles.dot}
              style={{ background: LANG_COLORS[lang] ?? '#8b8b8b' }}
            />
            {lang}
          </span>
        ))}
      </div>
    </div>
  )
}
