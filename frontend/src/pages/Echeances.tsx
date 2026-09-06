import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Echeance } from '../types'

const nombre = new Intl.NumberFormat('fr-FR')

const FILTRES = [
  { valeur: '', libelle: 'Toutes' },
  { valeur: 'pending', libelle: 'À payer' },
  { valeur: 'partial', libelle: 'Partielles' },
  { valeur: 'paid', libelle: 'Payées' },
  { valeur: 'overdue', libelle: 'En retard' },
]

function dateCourte(iso: string) {
  return new Date(iso).toLocaleDateString('fr-FR')
}

export default function Echeances() {
  const [echeances, setEcheances] = useState<Echeance[] | null>(null)
  const [filtre, setFiltre] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    const requete = filtre ? `/rent-charges/?status=${filtre}` : '/rent-charges/'
    api.get<Echeance[]>(requete).then(setEcheances).catch((e) => setErreur(e.message))
  }, [filtre])

  if (erreur) return <div className="erreur">{erreur}</div>

  const total = echeances?.reduce((somme, e) => somme + Number(e.amount_outstanding), 0) ?? 0

  return (
    <>
      <h1>Échéances</h1>
      <p className="intro">Ce que vos locataires doivent, et ce qui reste à encaisser.</p>

      <div className="filtres">
        {FILTRES.map((f) => (
          <button
            key={f.valeur}
            className={filtre === f.valeur ? 'actif' : ''}
            onClick={() => setFiltre(f.valeur)}
          >
            {f.libelle}
          </button>
        ))}
      </div>

      <div className="grille" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="carte">
          <div className="libelle">Échéances affichées</div>
          <div className="valeur">{echeances?.length ?? 0}</div>
        </div>
        <div className="carte alerte">
          <div className="libelle">Reste à encaisser</div>
          <div className="valeur">{nombre.format(total)}</div>
          <div className="detail">FCFA</div>
        </div>
      </div>

      <section className="panneau">
        <div className="defilement">
          <table>
            <thead>
              <tr>
                <th>Période</th>
                <th>Unité</th>
                <th>Locataire</th>
                <th>Échéance</th>
                <th className="montant">Dû</th>
                <th className="montant">Reste</th>
                <th>État</th>
              </tr>
            </thead>
            <tbody>
              {echeances?.map((e) => {
                const enRetard =
                  Number(e.amount_outstanding) > 0 && new Date(e.due_date) < new Date()
                return (
                  <tr key={e.id}>
                    <td>
                      {e.kind_display}
                      <span className="sous">
                        {dateCourte(e.period_start)} → {dateCourte(e.period_end)}
                      </span>
                    </td>
                    <td>{e.unit_label}</td>
                    <td>{e.tenant_name}</td>
                    <td>
                      {dateCourte(e.due_date)}
                      {enRetard && <span className="sous" style={{ color: 'var(--danger)' }}>en retard</span>}
                    </td>
                    <td className="montant">{nombre.format(Number(e.amount_due))}</td>
                    <td className="montant">{nombre.format(Number(e.amount_outstanding))}</td>
                    <td>
                      <span className={`etiquette ${e.status}`}>{e.status_display}</span>
                    </td>
                  </tr>
                )
              })}
              {echeances?.length === 0 && (
                <tr>
                  <td colSpan={7} className="vide">
                    Aucune échéance pour ce filtre.
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
