import { useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { Action, Alert, AlertDetail, AlertStatus } from '../types/models'
import { SeverityBadge, StatusBadge } from '../components/badges'

const STATUS_FOR: Record<Action, AlertStatus> = {
  validate: 'validated',
  false_positive: 'false_positive',
  escalate: 'escalated',
}

const ACTIONS: { action: Action; label: string; cls: string }[] = [
  { action: 'validate', label: 'Validate', cls: 'bg-emerald-600 hover:bg-emerald-500' },
  { action: 'false_positive', label: 'False positive', cls: 'bg-slate-600 hover:bg-slate-500' },
  { action: 'escalate', label: 'Escalate', cls: 'bg-orange-600 hover:bg-orange-500' },
]

export default function AlertDetailPage() {
  const { id } = useParams()
  const qc = useQueryClient()
  const [comment, setComment] = useState('')
  const [analyst, setAnalyst] = useState('analyst')

  const { data, isLoading, error } = useQuery({
    queryKey: ['alert', id],
    queryFn: () => api<AlertDetail>(`/alerts/${id}`),
    enabled: !!id,
  })

  const mutation = useMutation({
    mutationFn: (action: Action) =>
      api<Alert>(`/alerts/${id}/decision`, {
        method: 'POST',
        body: JSON.stringify({ action, analyst, comment: comment || null }),
      }),
    // Optimistic update: flip the status immediately, roll back on error.
    onMutate: async (action) => {
      await qc.cancelQueries({ queryKey: ['alert', id] })
      const prev = qc.getQueryData<AlertDetail>(['alert', id])
      if (prev) {
        qc.setQueryData<AlertDetail>(['alert', id], {
          ...prev,
          alert: { ...prev.alert, status: STATUS_FOR[action] },
        })
      }
      return { prev }
    },
    onError: (_e, _action, ctx) => {
      if (ctx?.prev) qc.setQueryData(['alert', id], ctx.prev)
    },
    onSuccess: () => setComment(''),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['alert', id] })
      qc.invalidateQueries({ queryKey: ['alerts'] })
    },
  })

  if (isLoading) return <p className="text-slate-400">Loading…</p>
  if (error) return <p className="text-red-400">Could not load this alert.</p>
  if (!data) return null

  const { alert, ticket, decisions } = data
  const card = 'rounded-lg border border-slate-800 bg-slate-900/40 p-4'
  const row = (k: string, v: ReactNode) => (
    <div className="flex justify-between gap-4 py-1 text-sm">
      <span className="text-slate-500">{k}</span>
      <span className="text-right">{v}</span>
    </div>
  )

  return (
    <div className="max-w-5xl">
      <Link to="/alerts" className="text-sm text-indigo-400 hover:underline">
        ← Back to alerts
      </Link>
      <h2 className="mb-4 mt-2 flex items-center gap-2 text-xl font-semibold">
        Alert #{alert.id} <StatusBadge status={alert.status} />
      </h2>

      <div className="grid gap-4 md:grid-cols-2">
        <section className={card}>
          <h3 className="mb-2 text-sm font-semibold text-slate-300">Alert — SIEM facts</h3>
          {row('Time', new Date(alert.ts).toLocaleString())}
          {row('Severity', <SeverityBadge severity={alert.severity} />)}
          {row('Source', alert.agent)}
          {row('Src IP', alert.src_ip ?? '—')}
          {row('Rule', `${alert.rule_id} (level ${alert.rule_level})`)}
          {row('Technique', alert.technique ?? '—')}
          <p className="mt-3 border-t border-slate-800 pt-3 text-sm text-slate-300">
            {alert.description}
          </p>
        </section>

        <section className={card}>
          <h3 className="mb-2 text-sm font-semibold text-slate-300">Agent ticket — advisory</h3>
          {ticket ? (
            <>
              {row('SIEM confidence', ticket.confiance_siem)}
              {row('Suggested severity', <SeverityBadge severity={ticket.severity} />)}
              {row('Recommended', ticket.recommended_action ?? '—')}
              <p className="mt-3 border-t border-slate-800 pt-3 text-sm text-slate-300">
                {ticket.analyse_llm}
              </p>
            </>
          ) : (
            <p className="text-sm text-slate-500">No ticket written by the agent for this alert.</p>
          )}
        </section>
      </div>

      <section className={`mt-4 ${card}`}>
        <h3 className="mb-3 text-sm font-semibold text-slate-300">Decision</h3>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Optional comment…"
          rows={2}
          className="mb-3 w-full rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <div className="flex flex-wrap items-center gap-2">
          {ACTIONS.map((a) => (
            <button
              key={a.action}
              disabled={mutation.isPending}
              onClick={() => mutation.mutate(a.action)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 ${a.cls}`}
            >
              {a.label}
            </button>
          ))}
          <input
            value={analyst}
            onChange={(e) => setAnalyst(e.target.value)}
            aria-label="analyst"
            className="ml-auto w-32 rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm"
          />
        </div>
        {mutation.isError && <p className="mt-2 text-sm text-red-400">Decision failed — reverted.</p>}
      </section>

      <section className="mt-4">
        <h3 className="mb-2 text-sm font-semibold text-slate-300">Decision history</h3>
        {decisions.length === 0 ? (
          <p className="text-sm text-slate-500">No decisions yet.</p>
        ) : (
          <ul className="space-y-2">
            {decisions.map((d) => (
              <li
                key={d.id}
                className="rounded-md border border-slate-800 bg-slate-900/40 px-3 py-2 text-sm"
              >
                <div className="flex justify-between">
                  <span className="font-medium">{d.action.replace('_', ' ')}</span>
                  <span className="text-slate-500">{new Date(d.created_at).toLocaleString()}</span>
                </div>
                <div className="text-slate-400">
                  {d.analyst} · {d.old_status ?? '—'} → {d.new_status}
                </div>
                {d.comment && <div className="mt-1 text-slate-300">“{d.comment}”</div>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
