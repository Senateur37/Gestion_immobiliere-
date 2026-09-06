import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Ecriture } from '../types'

const nombre = new Intl.NumberFormat('fr-FR')

export default function Comptabilite() {
  const [ecritures, setEcritures] = useState<Ecriture[] | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<Ecriture[]>('/accounting/entries/')
      .then(setEcritures)
      .catch((e) => setErreur(e.message))
  }, [])

  if (erreur) return <div className="erreur">{erreur}</div>

  const desequilibrees = ecritures?.filter((e) => !e.est_equilibree).length ?? 0

  return (
    <>
      <h1>Comptabilité</h1>
      <p className="intro">
        Le journal SYSCOHADA, alimenté automatiquement par les encaissements.
      </p>

      <div className="grille" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="carte">
          <div className="libelle">Écritures</div>
          <div className="valeur">{ecritures?.length ?? 0}</div>
          <div className="detail">200 plus récentes</div>
        </div>
        <div className={desequilibrees > 0 ? 'carte alerte' : 'carte'}>
          <div className="libelle">Déséquilibrées</div>
          <div className="valeur">{desequilibrees}</div>
          <div className="detail">
            {desequilibrees === 0 ? 'Toutes équilibrées' : 'À corriger sans délai'}
          </div>
        </div>
      </div>

      {ecritures === null && <p className="intro">Chargement...</p>}

      {ecritures?.map((e) => (
        <section className="panneau" key={e.id} style={{ marginBottom: 14, padding: 18 }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
              gap: 12,
              flexWrap: 'wrap',
              marginBottom: 10,
            }}
          >
            <div>
              <strong>{e.libelle}</strong>
              <span className="sous">
                {e.reference} · journal {e.journal} ·{' '}
                {new Date(e.date_ecriture).toLocaleDateString('fr-FR')}
              </span>
            </div>
            <span className={`etiquette ${e.est_equilibree ? 'paid' : 'retard'}`}>
              {e.est_equilibree ? 'Équilibrée' : 'Déséquilibrée'}
            </span>
          </div>

          <div className="defilement">
            <table>
              <thead>
                <tr>
                  <th>Compte</th>
                  <th>Intitulé</th>
                  <th className="montant">Débit</th>
                  <th className="montant">Crédit</th>
                </tr>
              </thead>
              <tbody>
                {e.lignes.map((l, index) => (
                  <tr key={`${e.id}-${index}`}>
                    <td>{l.compte}</td>
                    <td>{l.intitule}</td>
                    <td className="montant">
                      {Number(l.debit) > 0 ? nombre.format(Number(l.debit)) : ''}
                    </td>
                    <td className="montant">
                      {Number(l.credit) > 0 ? nombre.format(Number(l.credit)) : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}

      {ecritures?.length === 0 && (
        <section className="panneau">
          <div className="vide">
            Aucune écriture. Elles sont produites automatiquement à chaque encaissement.
          </div>
        </section>
      )}
    </>
  )
}
