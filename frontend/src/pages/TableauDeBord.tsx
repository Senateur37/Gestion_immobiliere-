import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { TableauDeBord as Donnees } from '../types'

const nombre = new Intl.NumberFormat('fr-FR')

export default function TableauDeBord() {
  const [donnees, setDonnees] = useState<Donnees | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<Donnees>('/dashboard/')
      .then(setDonnees)
      .catch((e) => setErreur(e.message))
  }, [])

  if (erreur) return <div className="erreur">{erreur}</div>
  if (!donnees) return <p className="intro">Chargement…</p>

  const devise = donnees.organization.currency === 'XOF' ? 'FCFA' : donnees.organization.currency

  return (
    <>
      <h1>Tableau de bord</h1>
      <p className="intro">
        Ce que votre patrimoine rapporte, et ce qu’il reste à encaisser.
      </p>

      <div className="grille">
        <div className="carte">
          <div className="libelle">Biens</div>
          <div className="valeur">{donnees.portfolio.properties}</div>
          <div className="detail">{donnees.portfolio.units} unité(s) locative(s)</div>
        </div>
        <div className="carte">
          <div className="libelle">Occupation</div>
          <div className="valeur">{donnees.portfolio.occupancy_rate}%</div>
          <div className="detail">
            {donnees.portfolio.occupied_units} / {donnees.portfolio.units} occupée(s)
          </div>
        </div>
        <div className="carte">
          <div className="libelle">Baux actifs</div>
          <div className="valeur">{donnees.leases.active}</div>
          <div className="detail">{donnees.leases.total} au total</div>
        </div>
        <div className="carte">
          <div className="libelle">Encaissé</div>
          <div className="valeur">{nombre.format(Number(donnees.finance.collected))}</div>
          <div className="detail">{devise}</div>
        </div>
        <div className="carte">
          <div className="libelle">Reste à encaisser</div>
          <div className="valeur">{nombre.format(Number(donnees.finance.outstanding))}</div>
          <div className="detail">{donnees.finance.open_charges} échéance(s) ouverte(s)</div>
        </div>
        <div className="carte alerte">
          <div className="libelle">En retard</div>
          <div className="valeur">{nombre.format(Number(donnees.finance.overdue_amount))}</div>
          <div className="detail">{donnees.finance.overdue_charges} échéance(s) dépassée(s)</div>
        </div>
      </div>
    </>
  )
}
