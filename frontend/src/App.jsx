import { useState, useRef } from 'react'
import ScoreCard from './components/ScoreCard'
import SkillCard from './components/SkillCard'
import ContributionsChart from './components/ContributionsChart'
import LanguagePills from './components/LanguagePills'
import StrengthsList from './components/StrengthsList'
import AchievementBadges from './components/AchievementBadges'
import { getMockData } from './data/mockData'
import styles from './App.module.css'

const GitHubIcon = () => (
  <svg className={styles.navLogo} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
  </svg>
)

const SearchIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <path d="m21 21-4.35-4.35"/>
  </svg>
)

export default function App() {
  const [username, setUsername] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [useMock, setUseMock] = useState(false)
  const inputRef = useRef(null)

  async function analyze() {
    const name = username.trim()
    if (!name) { setError('Please enter a GitHub username.'); inputRef.current?.focus(); return }
    setError(null); setResult(null); setLoading(true)
    try {
      let data
      if (useMock) {
        await new Promise((r) => setTimeout(r, 900))
        data = getMockData(name)
      } else {
        const res = await fetch('http://localhost:8000/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: name }),
        })
        if (!res.ok) { const b = await res.json().catch(() => ({})); throw new Error(b.detail ?? `API ${res.status}`) }
        data = await res.json()
      }
      setResult({ data, username: name })
    } catch (err) {
      setError(err.message?.includes('fetch')
        ? 'Cannot reach backend at localhost:8000. Make sure FastAPI is running.'
        : `Analysis failed: ${err.message}`)
    } finally { setLoading(false) }
  }

  return (
    <div className={styles.page}>
      <nav className={styles.navbar}>
        <div className={styles.navBrand}>
          <GitHubIcon />
          <div>
            <div className={styles.navTitle}>GitHub Talent Analyzer</div>
            <div className={styles.navSub}>AI-Powered Developer Intelligence</div>
          </div>
        </div>
        <div className={styles.navTag}>Beta</div>
      </nav>

      <div className={styles.container}>
        <div className={styles.hero}>
          <p className={styles.heroEyebrow}>Developer Intelligence Platform</p>
          <h1 className={styles.heroTitle}>Discover <span>Hidden</span> Developer Talent</h1>
          <p className={styles.heroSub}>Enter a GitHub username to generate an AI-powered talent score, skill classification, and deep activity insights.</p>

          <div className={styles.searchRow}>
            <div className={styles.inputWrap}>
              <span className={styles.inputIcon}><SearchIcon /></span>
              <input ref={inputRef} type="text" className={styles.input}
                placeholder="GitHub username  (e.g. torvalds, gaearon)"
                value={username} onChange={(e) => setUsername(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && analyze()}
                disabled={loading} aria-label="GitHub username" />
            </div>
            <button className={styles.analyzeBtn} onClick={analyze} disabled={loading}>
              {loading ? 'Analyzing…' : 'Analyze'}
            </button>
          </div>

          <label className={styles.mockToggle}>
            <input type="checkbox" checked={useMock} onChange={(e) => setUseMock(e.target.checked)} />
            <span>Mock data</span>
            <span className={styles.mockHint}>{useMock ? '(disable to call localhost:8000)' : '(calling real API)'}</span>
          </label>
        </div>

        {error && (
          <div className={styles.errorBox} role="alert">
            <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm-.75 3.5a.75.75 0 011.5 0v3.25a.75.75 0 01-1.5 0V4.5zm.75 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
            {error}
          </div>
        )}

        {loading && (
          <div className={styles.spinnerWrap} aria-label="Loading">
            <div className={styles.spinner}/>
            <span className={styles.spinnerText}>Fetching GitHub data…</span>
          </div>
        )}

        {result && !loading && (
          <section aria-label="Analysis results">
            <div className={styles.sectionDivider}><span className={styles.sectionLabel}>Overview</span></div>
            <div className={styles.topGrid}>
              <ScoreCard score={result.data.talent_score} />
              <SkillCard username={result.username} skillLevel={result.data.skill_level} meta={result.data._meta ?? result.data.raw_metrics ?? {}} />
            </div>

            <div className={styles.sectionDivider}><span className={styles.sectionLabel}>Achievements</span></div>
            <div className={styles.badgesRow}>
              <AchievementBadges data={result.data} />
            </div>

            <div className={styles.sectionDivider}><span className={styles.sectionLabel}>Feature Breakdown</span></div>
            <div className={styles.chartRow}>
              <ContributionsChart data={result.data.feature_contributions} />
            </div>

            <div className={styles.sectionDivider}><span className={styles.sectionLabel}>Profile Details</span></div>
            <div className={styles.bottomGrid}>
              <LanguagePills languages={result.data.top_languages} />
              <StrengthsList strengths={result.data.strengths} />
            </div>
          </section>
        )}

        {!result && !loading && !error && (
          <div className={styles.placeholder}>
            <svg width="52" height="52" viewBox="0 0 24 24" fill="currentColor" style={{opacity:0.2}}>
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            <p>Enter a GitHub username above to begin analysis</p>
            <p className={styles.placeholderHint}>Try: <code>torvalds</code> or <code>gaearon</code></p>
          </div>
        )}
      </div>
    </div>
  )
}