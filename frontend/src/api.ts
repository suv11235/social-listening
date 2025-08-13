import ky from 'ky'

const API_URL = (import.meta as any).env?.VITE_API_URL || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://localhost:8000')

const api = ky.create({ prefixUrl: API_URL })

export type Mention = {
  id: number
  title?: string | null
  summary?: string | null
  url: string
  source: string
  author?: string | null
  published_at?: string | null
  fetched_at: string
  sentiment?: number | null
}

export function fetchMentions(query?: string, source?: string, limit = 20, offset = 0) {
  const params = new URLSearchParams()
  if (query && query.trim() !== '') params.set('query', query)
  if (source && source.trim() !== '') params.set('source', source)
  params.set('limit', String(limit))
  params.set('offset', String(offset))
  return api
    .get('mentions', { searchParams: params })
    .json<Mention[]>()
}

export function ingestRss(url: string) {
  return api.post('ingest/rss', { json: { url } }).json<{ status: string; added: number }>()
}

export function ingestHNSearch(query: string, hitsPerPage = 50) {
  return api.post('ingest/hn-search', { json: { query, hits_per_page: hitsPerPage } }).json<{ status: string; added: number }>()
}

export function ingestMastoSearch(instance: string, query: string, limit = 40) {
  return api.post('ingest/masto-search', { json: { instance, query, limit } }).json<{ status: string; added: number }>()
}

export function ingestRedditSearch(query: string, subreddit?: string | null, limit = 25) {
  return api.post('ingest/reddit/search', { json: { query, subreddit: subreddit ?? null, limit } }).json<{ status: string; added: number }>()
}
