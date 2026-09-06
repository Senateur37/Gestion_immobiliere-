import { useEffect, useState } from 'react'

import { api } from '../api/client'
import Tableau from '../components/Tableau'
import type { Membre } from '../types'

export default function Utilisateurs() {
  const [membres, setMembres] = useState<Membre[] | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    api.get<Membre[]>('/members/').then(setMembres).catch((e) => setErreur(e.message))
  }, [])

  return (
    <>
      <h1>Utilisateurs</h1>
      <p className="intro">
        Les membres de votre organisation. Le rôle détermine ce que chacun peut faire.
      </p>

      <Tableau
        colonnes={[
          { cle: 'nom', titre: 'Membre' },
          { cle: 'email', titre: 'Email' },
          { cle: 'role', titre: 'Rôle' },
          { cle: 'etat', titre: 'État' },
        ]}
        lignes={membres}
        erreur={erreur}
        messageVide="Aucun membre."
        rendu={(m) => (
          <tr key={m.id}>
            <td>
              {m.full_name}
              <span className="sous">{m.username}</span>
            </td>
            <td>{m.email || '-'}</td>
            <td>
              <span className="etiquette partial">{m.role_display}</span>
            </td>
            <td>
              <span className={`etiquette ${m.is_active ? 'paid' : 'cancelled'}`}>
                {m.is_active ? 'Actif' : 'Inactif'}
              </span>
            </td>
          </tr>
        )}
      />
    </>
  )
}
