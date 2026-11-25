import { useNavigate, useSearchParams } from 'react-router-dom'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { AlertList } from '../types/models'
import { SeverityBadge, StatusBadge } from '../components/badges'

const SEVERITIES = ['', 'faible', 'moyen', 'eleve'] as const
const STATUSES = ['', 'new', 'validated', 'false_positive', 'escalated'] as const
const SIZE = 25

export default function AlertsPage() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const severity = params.get('severity') ?? ''
  const status = params.get('status') ?? ''
  const q = params.get('q') ?? ''
  const page = Math.max(1, Number(params.get('page') ?? '1'))

  // Build the API query string from the URL state (single source of truth).
  const qs = new URLSearchParams()
  if (severity) qs.set('severity', severity)
  if (status) qs.set('status', status)
  if (q) qs.set('q', q)
  qs.set('page', String(page))
  qs.set('size', String(SIZE))

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: ['alerts', qs.toString()],
    queryFn: () => api<AlertList>(`/alerts?${qs.toString()}`),
    placeholderData: keepPreviousData,
  })

  // Merge changes into the URL. Any filter change resets pagination to page 1;
  // explicit page changes keep the page key.
  function update(next: Record<string, string>) {
    const p = new URLSearchParams(params)
    for (const [k, v] of Object.entries(next)) {
      if (v) p.set(k, v)
      else p.delete(k)
    }
    if (!('page' in next)) p.delete('page')
    setParams(p, { replace: true })
  }

  const total = data?.total ?? 0
  const pages = Math.max(1, Math.ceil(total / SIZE))

  const inputCls =
    'rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500'

  return (
    <div>
      <h2 className="mb-4 text-xl font-semibold">Alerts</h2>

      <div className="mb-4 flex flex-wrap gap-2">
        <select value={severity} onChange={(e) => update({ severity: e.target.value })} className={inputCls}>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>{s || 'all severities'}</option>
          ))}
        </select>
        <select value={status} onChange={(e) => update({ status: e.target.value })} className={inputCls}>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s ? s.replace('_', ' ') : 'all statuses'}</option>
          ))}
        </select>
        <input
          value={q}
          onChange={(e) => update({ q: e.target.value })}
          placeholder="search description / agent / technique"
          className={`min-w-64 flex-1 ${inputCls}`}
        />
      </div>

      {error && <p className="mb-3 text-red-400">API unreachable — is the backend running on :8000?</p>}

      <div className="overflow-hidden rounded-lg border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900 text-slate-400">
            <tr>
              <th className="px-3 py-2 font-medium">Time</th>
              <th className="px-3 py-2 font-medium">Severity</th>
              <th className="px-3 py-2 font-medium">Source</th>
              <th className="px-3 py-2 font-medium">Src IP</th>
              <th className="px-3 py-2 font-medium">Rule</th>
              <th className="px-3 py-2 font-medium">Technique</th>
              <th className="px-3 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {data?.items.map((a) => (
              <tr
                key={a.id}
                onClick={() => navigate(`/alerts/${a.id}`)}
                className="cursor-pointer hover:bg-slate-900/50"
              >
                <td className="whitespace-nowrap px-3 py-2 text-slate-400">
                  {new Date(a.ts).toLocaleString()}
                </td>
                <td className="px-3 py-2"><SeverityBadge severity={a.severity} /></td>
                <td className="px-3 py-2">{a.agent}</td>
                <td className="px-3 py-2 text-slate-400">{a.src_ip ?? '—'}</td>
                <td className="px-3 py-2 text-slate-400">{a.rule_id}</td>
                <td className="px-3 py-2">{a.technique ?? '—'}</td>
                <td className="px-3 py-2"><StatusBadge status={a.status} /></td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-slate-500">
                  No alerts match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex items-center justify-between text-sm text-slate-400">
        <span>
          {isLoading ? 'Loading…' : `${total} alert(s)`}
          {isFetching && !isLoading ? ' · updating…' : ''}
        </span>
        <div className="flex items-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => update({ page: String(page - 1) })}
            className="rounded-md border border-slate-700 px-2 py-1 disabled:opacity-40"
          >
            Prev
          </button>
          <span>Page {page} / {pages}</span>
          <button
            disabled={page >= pages}
            onClick={() => update({ page: String(page + 1) })}
            className="rounded-md border border-slate-700 px-2 py-1 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
