import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Bien } from '../types'

export default function Biens() {
  const [biens, setBiens] = useState<Bien[] | null>(null)
  const [recherche, setRecherche] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    const requete = recherche ? `/properties/?q=${encodeURIComponent(recherche)}` : '/properties/'
    api.get<Bien[]>(requete).then(setBiens).catch((e) => setErreur(e.message))
  }, [recherche])

  if (erreur) return <div className="erreur">{erreur}</div>

  return (
    <>
      <h1>Biens immobiliers</h1>
      <p className="intro">Le patrimoine de votre organisation.</p>

      <label className="champ" style={{ maxWidth: 340 }}>
        <span>Rechercher</span>
        <input
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          placeholder="Nom ou ville"
        />
      </label>

      <section className="panneau">
        <div className="defilement">
          <table>
            <thead>
              <tr>
                <th>Bien</th>
                <th>Ville</th>
                <th>Type</th>
                <th className="montant">Surface</th>
                <th className="montant">Unités</th>
              </tr>
            </thead>
            <tbody>
              {biens?.map((bien) => (
                <tr key={bien.id}>
                  <td>
                    {bien.name}
                    <span className="sous">{bien.address}</span>
                  </td>
                  <td>{bien.city}</td>
                  <td>{bien.property_type_display}</td>
                  <td className="montant">{Number(bien.total_area)} m²</td>
                  <td className="montant">{bien.units_count}</td>
                </tr>
              ))}
              {biens?.length === 0 && (
                <tr>
                  <td colSpan={5} className="vide">
                    Aucun bien pour cette recherche.
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
