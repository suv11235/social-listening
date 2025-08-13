import React, { useEffect, useMemo, useState } from 'react'
import { fetchMentions, ingestRss, ingestHNSearch, ingestMastoSearch, ingestRedditSearch, Mention } from './api'

export default function App() {
  const [feedUrl, setFeedUrl] = useState('https://news.ycombinator.com/rss')
  const [hnQuery, setHnQuery] = useState('"body shaming" OR body-shaming OR fat')
  const [mastoInstance, setMastoInstance] = useState('mastodon.social')
  const [mastoQuery, setMastoQuery] = useState('body shaming OR fat')
  const [redditQuery, setRedditQuery] = useState('body shaming OR fat')
  const [redditSub, setRedditSub] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [mentions, setMentions] = useState<Mention[]>([])
  const [error, setError] = useState<string | null>(null)

  const filteredMentions = useMemo(() => mentions, [mentions])

  async function refresh() {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchMentions(query || undefined, undefined, 50, 0)
      setMentions(data)
    } catch (e: any) {
      setError(e?.message || 'Failed to load mentions')
    } finally {
      setLoading(false)
    }
  }

  async function handleIngestRSS(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await ingestRss(feedUrl)
      await refresh()
    } catch (e: any) {
      setError(e?.message || 'Failed to ingest feed')
    } finally {
      setLoading(false)
    }
  }

  async function handleIngestHN(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await ingestHNSearch(hnQuery, 50)
      await refresh()
    } catch (e: any) {
      setError(e?.message || 'Failed to ingest Hacker News search')
    } finally {
      setLoading(false)
    }
  }

  async function handleIngestMasto(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await ingestMastoSearch(mastoInstance, mastoQuery, 40)
      await refresh()
    } catch (e: any) {
      setError(e?.message || 'Failed to ingest Mastodon search')
    } finally {
      setLoading(false)
    }
  }

  async function handleIngestReddit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await ingestRedditSearch(redditQuery, redditSub || null, 25)
      await refresh()
    } catch (e: any) {
      setError(e?.message || 'Failed to ingest Reddit search')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div style={{ fontFamily: 'ui-sans-serif, system-ui, -apple-system', padding: 24, maxWidth: 960, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 8 }}>Social Listening</h1>
      <p style={{ color: '#666', marginTop: 0 }}>Ingest RSS feeds, search Hacker News, Mastodon, or Reddit, then browse mentions.</p>

      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: '1fr' }}>
        <form onSubmit={handleIngestRSS} style={{ display: 'flex', gap: 8 }}>
          <input
            type="url"
            value={feedUrl}
            onChange={(e) => setFeedUrl(e.target.value)}
            placeholder="Enter RSS feed URL"
            style={{ flex: 1, padding: 8, borderRadius: 6, border: '1px solid #ccc' }}
            required
          />
          <button type="submit" style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #222', background: '#111', color: 'white' }}>
            Ingest RSS
          </button>
        </form>

        <form onSubmit={handleIngestHN} style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            value={hnQuery}
            onChange={(e) => setHnQuery(e.target.value)}
            placeholder='HN search (e.g., "body shaming" OR fat)'
            style={{ flex: 1, padding: 8, borderRadius: 6, border: '1px solid #ccc' }}
          />
          <button type="submit" style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #222', background: '#111', color: 'white' }}>
            Search HN
          </button>
        </form>

        <form onSubmit={handleIngestMasto} style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            value={mastoInstance}
            onChange={(e) => setMastoInstance(e.target.value)}
            placeholder="Mastodon instance (e.g., mastodon.social)"
            style={{ width: 260, padding: 8, borderRadius: 6, border: '1px solid #ccc' }}
            required
          />
          <input
            type="text"
            value={mastoQuery}
            onChange={(e) => setMastoQuery(e.target.value)}
            placeholder='Mastodon search (e.g., body shaming OR fat)'
            style={{ flex: 1, padding: 8, borderRadius: 6, border: '1px solid #ccc' }}
            required
          />
          <button type="submit" style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #222', background: '#111', color: 'white' }}>
            Search Mastodon
          </button>
        </form>

        <form onSubmit={handleIngestReddit} style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            value={redditQuery}
            onChange={(e) => setRedditQuery(e.target.value)}
            placeholder='Reddit search (e.g., body shaming OR fat)'
            style={{ flex: 1, padding: 8, borderRadius: 6, border: '1px solid #ccc' }}
            required
          />
          <input
            type="text"
            value={redditSub}
            onChange={(e) => setRedditSub(e.target.value)}
            placeholder='Subreddit (optional, e.g., askreddit)'
            style={{ width: 240, padding: 8, borderRadius: 6, border: '1px solid #ccc' }}
          />
          <button type="submit" style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #222', background: '#111', color: 'white' }}>
            Search Reddit
          </button>
        </form>
      </div>

      <div style={{ display: 'flex', gap: 8, margin: '12px 0' }}>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search mentions"
          style={{ flex: 1, padding: 8, borderRadius: 6, border: '1px solid #ccc' }}
        />
        <button onClick={refresh} style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #ccc' }}>Refresh</button>
      </div>

      {loading && <div>Loading…</div>}
      {error && <div style={{ color: 'crimson' }}>{error}</div>}

      <ul style={{ listStyle: 'none', padding: 0, marginTop: 16 }}>
        {filteredMentions.map((m) => (
          <li key={m.id} style={{ padding: 12, border: '1px solid #eee', borderRadius: 8, marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
              <a href={m.url} target="_blank" rel="noreferrer" style={{ fontWeight: 600, textDecoration: 'none' }}>
                {m.title || m.url}
              </a>
              <span style={{ color: '#666', fontSize: 12 }}>{m.source}</span>
            </div>
            {m.summary && <p style={{ marginTop: 8, marginBottom: 8 }}>{m.summary}</p>}
            <div style={{ color: '#666', fontSize: 12 }}>
              {m.author && <span>By {m.author} · </span>}
              {m.published_at ? new Date(m.published_at).toLocaleString() : 'Unspecified time'}
              {typeof m.sentiment === 'number' && (
                <span> · Sentiment: {m.sentiment.toFixed(2)}</span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
