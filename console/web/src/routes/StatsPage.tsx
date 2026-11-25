import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../lib/api'

type Stats = {
  by_severity_over_time: { day: string; severity: string; n: number }[]
  agreement_rate: number
  agreement_sample: number
  coverage: { manche: number | null; taux_couverture: number | null }[]
}

const SEV_COLORS: Record<string, string> = {
  faible: '#38bdf8', // sky-400
  moyen: '#fbbf24', // amber-400
  eleve: '#f87171', // red-400
}

const tooltipStyle = {
  background: '#0f172a',
  border: '1px solid #1e293b',
  borderRadius: 8,
  fontSize: 12,
  color: '#e2e8f0',
}

type SevRow = { day: string; faible: number; moyen: number; eleve: number }

function pivotSeverity(rows: Stats['by_severity_over_time']): SevRow[] {
  const byDay: Record<string, SevRow> = {}
  for (const r of rows) {
    byDay[r.day] ??= { day: r.day, faible: 0, moyen: 0, eleve: 0 }
    if (r.severity === 'faible' || r.severity === 'moyen' || r.severity === 'eleve') {
      byDay[r.day][r.severity] = r.n
    }
  }
  return Object.values(byDay).sort((a, b) => a.day.localeCompare(b.day))
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-300">{title}</h3>
      {children}
    </section>
  )
}

export default function StatsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api<Stats>('/stats'),
  })

  if (isLoading) return <p className="text-slate-400">Loading…</p>
  if (error) return <p className="text-red-400">Could not load stats — is the backend running?</p>
  if (!data) return null

  const sev = pivotSeverity(data.by_severity_over_time)
  const coverage = data.coverage
    .filter((c) => c.manche != null)
    .map((c) => ({ manche: c.manche, pct: Number(c.taux_couverture) }))
  const agreementPct = Math.round((data.agreement_rate ?? 0) * 100)
  const gauge = [{ name: 'agreement', value: agreementPct, fill: '#818cf8' }]

  return (
    <div>
      <h2 className="mb-4 text-xl font-semibold">Stats</h2>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Alerts by severity over time">
          {sev.length === 0 ? (
            <p className="text-sm text-slate-500">No alerts yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={sev}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="day" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#1e293b55' }} />
                <Legend />
                <Bar dataKey="faible" stackId="s" fill={SEV_COLORS.faible} />
                <Bar dataKey="moyen" stackId="s" fill={SEV_COLORS.moyen} />
                <Bar dataKey="eleve" stackId="s" fill={SEV_COLORS.eleve} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card title="Analyst ↔ agent agreement">
          <div className="relative">
            <ResponsiveContainer width="100%" height={260}>
              <RadialBarChart
                data={gauge}
                innerRadius="72%"
                outerRadius="100%"
                startAngle={90}
                endAngle={-270}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                <RadialBar background dataKey="value" cornerRadius={10} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-semibold">{agreementPct}%</span>
              <span className="text-xs text-slate-500">
                over {data.agreement_sample} decision(s)
              </span>
            </div>
          </div>
        </Card>

        <Card title="Detection coverage per round">
          {coverage.length === 0 ? (
            <p className="text-sm text-slate-500">
              No rounds scored yet — run <code className="text-slate-400">red/score_manche.py</code>.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={coverage}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="manche" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} domain={[0, 100]} unit="%" />
                <Tooltip contentStyle={tooltipStyle} />
                <Line
                  type="monotone"
                  dataKey="pct"
                  stroke="#34d399"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>
    </div>
  )
}
