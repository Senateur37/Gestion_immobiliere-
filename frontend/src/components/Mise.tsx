/** Coquille de l'application : barre laterale et zone de contenu. */
import { NavLink, useNavigate } from 'react-router-dom'
import type { ReactNode } from 'react'

import { useAuth } from '../auth/AuthContext'

const LIENS = [
  { vers: '/', libelle: 'Tableau de bord', groupe: 'Pilotage' },
  { vers: '/biens', libelle: 'Biens immobiliers', groupe: 'Pilotage' },
  { vers: '/baux', libelle: 'Baux', groupe: 'Pilotage' },
  { vers: '/echeances', libelle: 'Échéances', groupe: 'Opérations' },
  { vers: '/encaissements', libelle: 'Encaissements', groupe: 'Opérations' },
]

export default function Mise({ children }: { children: ReactNode }) {
  const { utilisateur, organisation, deconnexion } = useAuth()
  const naviguer = useNavigate()

  const groupes = [...new Set(LIENS.map((l) => l.groupe))]

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">ImmoPilot</div>
        {groupes.map((groupe) => (
          <div key={groupe}>
            <div className="nav-group">{groupe}</div>
            {LIENS.filter((l) => l.groupe === groupe).map((lien) => (
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
