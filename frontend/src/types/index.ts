/** Contrats de l'API v1, tels que le front les consomme. */

export type Organisation = {
  id: number
  name: string
  slug: string
  kind: string
  currency: string
  primary_color: string
}

export type Membership = {
  organization: Organisation
  role: string
  role_display: string
  is_default: boolean
}

export type Utilisateur = {
  id: number
  username: string
  email: string
  full_name: string
  phone: string
  memberships: Membership[]
}

export type TableauDeBord = {
  organization: { name: string; currency: string }
  portfolio: {
    properties: number
    units: number
    occupied_units: number
    occupancy_rate: number
  }
  leases: { active: number; total: number }
  finance: {
    open_charges: number
    outstanding: number
    overdue_charges: number
    overdue_amount: number
    collected: number
  }
}

export type Bien = {
  id: number
  name: string
  address: string
  city: string
  property_type: string
  property_type_display: string
  total_area: string
  is_active: boolean
  units_count: number
}

export type Echeance = {
  id: number
  lease_number: string
  tenant_name: string
  unit_label: string
  kind_display: string
  period_start: string
  period_end: string
  due_date: string
  amount_due: string
  amount_outstanding: string
  status: string
  status_display: string
}

export type Encaissement = {
  id: number
  reference: string
  lease_number: string
  tenant_name: string
  amount: string
  amount_allocated: string
  amount_unallocated: string
  payment_date: string
  method_display: string
  external_reference: string
}

export type Bail = {
  id: number
  lease_number: string
  unit_label: string
  tenant_name: string
  start_date: string
  end_date: string
  rent_amount: string
  status: string
  status_display: string
}

export type CompteFinancier = {
  id: number
  code: string
  nom: string
  type: string
  solde_actuel: string
}

export type Unite = {
  id: number
  property: number
  property_name: string
  unit_number: string
  area: string
  rooms: number
  bedrooms: number
  rent_amount: string
  deposit_amount: string
  status: string
  status_display: string
}

export type Locataire = {
  id: number
  full_name: string
  username: string
  email: string
  phone: string
  leases_count: number
  active_lease: string | null
  balance: string
}

export type Intervention = {
  id: number
  title: string
  unit_label: string
  category_display: string
  priority: string
  priority_display: string
  status: string
  status_display: string
  submitted_at: string
  cost: string | null
}

export type DocumentFichier = {
  id: number
  title: string
  category: string
  category_display: string
  file_size: number
  mime_type: string
  is_signed: boolean
  expires_at: string | null
  created_at: string
}

export type LigneEcriture = {
  compte: string
  intitule: string
  debit: string
  credit: string
}

export type Ecriture = {
  id: number
  reference: string
  date_ecriture: string
  libelle: string
  journal: string
  total_debit: string
  total_credit: string
  est_equilibree: boolean
  lignes: LigneEcriture[]
}

export type Membre = {
  id: number
  full_name: string
  username: string
  email: string
  role: string
  role_display: string
  is_active: boolean
}

export type Rapport = {
  rent: { monthly_total: string; average: number; active_leases: number }
  units_by_status: Record<string, number>
  charges_by_status: Record<string, number>
  outstanding: string
  collected: string
  maintenance_open: number
  treasury: { code: string; nom: string; solde: string }[]
}
