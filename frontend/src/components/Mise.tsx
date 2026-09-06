/**
 * Coquille de l'application.
 *
 * Le menu reprend celui de l'interface Django : les deux fronts
 * coexistent pendant la migration, et un utilisateur qui passe de l'un a
 * l'autre doit retrouver les memes entrees au meme endroit.
 */
import { NavLink, useNavigate } from 'react-router-dom'
import type { ReactNode } from 'react'

import { useAuth } from '../auth/AuthContext'

type Lien = {
  vers: string
  libelle: string
  groupe: string
  /** Role minimum requis, quand l'ecran n'est pas ouvert a tous. */
  role?: 'manager' | 'accountant'
}

const LIENS: Lien[] = [
  { vers: '/', libelle: 'Tableau de bord', groupe: 'Pilotage' },
  { vers: '/biens', libelle: 'Biens immobiliers', groupe: 'Pilotage' },
  { vers: '/unites', libelle: 'Unités locatives', groupe: 'Pilotage' },
  { vers: '/baux', libelle: 'Baux', groupe: 'Pilotage' },
  { vers: '/locataires', libelle: 'Locataires', groupe: 'Pilotage' },

  { vers: '/rapports', libelle: 'Rapports', groupe: 'Opérations' },
  { vers: '/echeances', libelle: 'Échéances', groupe: 'Opérations' },
  { vers: '/encaissements', libelle: 'Encaissements', groupe: 'Opérations' },
  { vers: '/maintenance', libelle: 'Maintenance', groupe: 'Opérations' },
  { vers: '/documents', libelle: 'Documents', groupe: 'Opérations' },
  { vers: '/comptabilite', libelle: 'Comptabilité', groupe: 'Opérations', role: 'accountant' },

  { vers: '/utilisateurs', libelle: 'Utilisateurs', groupe: 'Administration', role: 'manager' },
]

// Hierarchie des roles, identique a celle du serveur. Le menu masque ce
// qui serait de toute facon refuse : c'est un confort d'affichage, la
// verification restant cote serveur.
const RANG: Record<string, number> = {
  owner: 40,
  manager: 30,
  accountant: 20,
  agent: 10,
}

export default function Mise({ children }: { children: ReactNode }) {
  const { utilisateur, organisation, deconnexion } = useAuth()
  const naviguer = useNavigate()

  const rangUtilisateur = RANG[organisation?.role ?? ''] ?? 0
  const visibles = LIENS.filter((lien) => !lien.role || rangUtilisateur >= RANG[lien.role])
  const groupes = [...new Set(visibles.map((l) => l.groupe))]

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">ImmoPilot</div>

        {groupes.map((groupe) => (
          <div key={groupe}>
            <div className="nav-group">{groupe}</div>
            {visibles
              .filter((l) => l.groupe === groupe)
              .map((lien) => (
                <NavLink
                  key={lien.vers}
                  to={lien.vers}
                  end={lien.vers === '/'}
                  className={({ isActive }) => `nav-link${isActive ? ' actif' : ''}`}
                >
                  {lien.libelle}
                </NavLink>
              ))}
          </div>
        ))}
      </aside>

      <main className="contenu">
        <header className="barre">
          <div>
            <div className="eyebrow">{organisation?.organization.name ?? 'Espace'}</div>
            <div className="sous">
              {utilisateur?.full_name} · {organisation?.role_display}
            </div>
          </div>
          <button
            className="bouton discret"
            onClick={() => {
              deconnexion()
              naviguer('/connexion')
            }}
          >
            Se déconnecter
          </button>
        </header>
        {children}
      </main>
    </div>
  )
}
