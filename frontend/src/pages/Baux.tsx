import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Bail } from '../types'

const nombre = new Intl.NumberFormat('fr-FR')

export default function Baux() {
  const [baux, setBaux] = useState<Bail[] | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  function recharger() {
    api.get<Bail[]>('/leases/').then(setBaux).catch((e) => setErreur(e.message))
  }

  useEffect(recharger, [])

  async function genererEcheancier(id: number, numero: string) {
    setErreur(null)
    setMessage(null)
    try {
      const resultat = await api.post<{ created: number }>(`/leases/${id}/schedule/`, {})
      // La génération est rejouable : le dire évite que l'utilisateur
      // croie à un échec quand rien n'a été créé.
      setMessage(
        resultat.created > 0
          ? `${resultat.created} échéance(s) générée(s) pour ${numero}.`
          : `L'échéancier de ${numero} était déjà complet.`,
      )
    } catch (e) {
      setErreur((e as Error).message)
    }
  }

  if (erreur && !baux) return <div className="erreur">{erreur}</div>

  return (
    <>
      <h1>Baux</h1>
      <p className="intro">Les contrats de location de votre organisation.</p>

      {erreur && <div className="erreur">{erreur}</div>}
      {message && <div className="succes">{message}</div>}

      <section className="panneau">
        <div className="defilement">
          <table>
            <thead>
              <tr>
                <th>Numéro</th>
                <th>Unité</th>
                <th>Locataire</th>
                <th>Période</th>
                <th className="montant">Loyer</th>
                <th>État</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {baux?.map((b) => (
                <tr key={b.id}>
                  <td>{b.lease_number}</td>
                  <td>{b.unit_label}</td>
                  <td>{b.tenant_name}</td>
                  <td>
                    {new Date(b.start_date).toLocaleDateString('fr-FR')}
                    <span className="sous">
                      au {new Date(b.end_date).toLocaleDateString('fr-FR')}
                    </span>
                  </td>
                  <td className="montant">{nombre.format(Number(b.rent_amount))}</td>
                  <td>
                    <span className="etiquette paid">{b.status_display}</span>
                  </td>
                  <td>
                    <button
                      className="bouton discret"
                      onClick={() => genererEcheancier(b.id, b.lease_number)}
                    >
                      Générer l&apos;échéancier
                    </button>
                  </td>
                </tr>
              ))}
              {baux?.length === 0 && (
                <tr>
                  <td colSpan={7} className="vide">
                    Aucun bail enregistré.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}
