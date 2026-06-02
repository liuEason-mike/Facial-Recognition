export type SuspectPersonality = 'cooperative' | 'resistant' | 'silent' | 'arrogant'

export interface SuspectInfo {
  id: string
  name: string
  gender?: string
  age?: number
  occupation?: string
  personality?: SuspectPersonality
}

export interface EvidenceItem {
  id: string
  type: string
  title: string
  description: string
  strength?: 'weak' | 'medium' | 'strong'
}

export interface InterrogationPoint {
  id: string
  title: string
  description: string
  priority?: 'low' | 'medium' | 'high'
}

export interface SimulationCaseDetail {
  id: number
  title: string
  case_number?: string
  category?: string
  difficulty?: string
  description?: string
  incident_date?: string
  location?: string
  suspect_info: SuspectInfo
  evidence_chain: EvidenceItem[]
  interrogation_points: InterrogationPoint[]
}
