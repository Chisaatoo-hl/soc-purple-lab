import type { Severity, AlertStatus } from '../types/models'

const pill = 'inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset'

const SEV: Record<Severity, string> = {
  eleve: 'bg-red-500/15 text-red-300 ring-red-500/30',
  moyen: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  faible: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <span className={`${pill} ${SEV[severity]}`}>{severity}</span>
}

const STATUS: Record<AlertStatus, string> = {
  new: 'bg-indigo-500/15 text-indigo-300 ring-indigo-500/30',
  validated: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  false_positive: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
  escalated: 'bg-orange-500/15 text-orange-300 ring-orange-500/30',
}

export function StatusBadge({ status }: { status: AlertStatus }) {
  return <span className={`${pill} ${STATUS[status]}`}>{status.replace('_', ' ')}</span>
}
