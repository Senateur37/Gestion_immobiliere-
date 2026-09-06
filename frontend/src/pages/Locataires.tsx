import { useEffect, useState } from 'react'

import { api } from '../api/client'
import Tableau from '../components/Tableau'
import type { Locataire } from '../types'

const nombre = new Intl.NumberFormat('fr-FR')

export default function Locataires() {
  const [locataires, setLocataires] = useState<Locataire[] | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    api.get<Locataire[]>('/tenants/').then(setLocataires).catch((e) => setErreur(e.message))
  }, [])

  return (
    <>
      <h1>Locataires</h1>
      <p className="intro">
        Les personnes liées à votre organisation par un bail, et ce qu&apos;elles doivent.
      </p>

      <Tableau
        colonnes={[
          { cle: 'nom', titre: 'Locataire' },
          { cle: 'contact', titre: 'Contact' },
          { cle: 'bail', titre: 'Bail actif' },
          { cle: 'baux', titre: 'Baux', alignerADroite: true },
          { cle: 'solde', titre: 'Solde dû', alignerADroite: true },
        ]}
        lignes={locataires}
        erreur={erreur}
        messageVide="Aucun locataire rattaché à un bail."
        rendu={(l) => (
          <tr key={l.id}>
            <td>
              {l.full_name}
              <span className="sous">{l.username}</span>
            </td>
            <td>
              {l.email || '-'}
              {l.phone && <span className="sous">{l.phone}</span>}
            </td>
            <td>{l.active_lease ?? <span className="sous">aucun</span>}</td>
            <td className="montant">{l.leases_count}</td>
            <td className="montant">
              {Number(l.balance) > 0 ? (
                <strong style={{ color: 'var(--danger)' }}>
                  {nombre.format(Number(l.balance))}
                </strong>
              ) : (
                nombre.format(Number(l.balance))
              )}
            </td>
          </tr>
        )}
      />
    </>
  )
}
