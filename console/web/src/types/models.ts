// Hand-written mirror of the API schemas. `npm run gen:api` writes the canonical
// generated types to ./api.ts; these interfaces keep the app resilient even
// before that file exists, and give friendly union types for severity/status.

export type Severity = 'faible' | 'moyen' | 'eleve'
export type AlertStatus = 'new' | 'validated' | 'false_positive' | 'escalated'
export type Action = 'validate' | 'false_positive' | 'escalate'

export interface Alert {
  id: number
  ts: string
  agent: string
  rule_id: number
  rule_level: number
  severity: Severity
  technique: string | null
  src_ip: string | null
  description: string
  status: AlertStatus
  created_at: string
}

export interface AlertList {
  items: Alert[]
  total: number
  page: number
  size: number
}

export interface Ticket {
  id: number
  alert_id: number
  confiance_siem: string
  analyse_llm: string
  severity: Severity
  recommended_action: Action | null
  created_at: string
}

export interface Decision {
  id: number
  alert_id: number
  analyst: string
  action: Action
  old_status: string | null
  new_status: string
  comment: string | null
  created_at: string
}

export interface AlertDetail {
  alert: Alert
  ticket: Ticket | null
  decisions: Decision[]
}
