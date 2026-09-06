import { useEffect, useState } from 'react'

import { api } from '../api/client'
import Tableau from '../components/Tableau'
import type { Unite } from '../types'

const nombre = new Intl.NumberFormat('fr-FR')

const FILTRES = [
  { valeur: '', libelle: 'Toutes' },
  { valeur: 'available', libelle: 'Disponibles' },
  { valeur: 'occupied', libelle: 'Occupées' },
  { valeur: 'maintenance', libelle: 'En maintenance' },
  { valeur: 'reserved', libelle: 'Réservées' },
]

export default function Unites() {
  const [unites, setUnites] = useState<Unite[] | null>(null)
  const [filtre, setFiltre] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    setUnites(null)
    const requete = filtre ? `/units/?status=${filtre}` : '/units/'
    api.get<Unite[]>(requete).then(setUnites).catch((e) => setErreur(e.message))
  }, [filtre])

  return (
    <>
      <h1>Unités locatives</h1>
      <p className="intro">Le détail de vos logements, et leur disponibilité.</p>

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

      <Tableau
        colonnes={[
          { cle: 'unite', titre: 'Unité' },
          { cle: 'bien', titre: 'Bien' },
          { cle: 'surface', titre: 'Surface', alignerADroite: true },
          { cle: 'pieces', titre: 'Pièces', alignerADroite: true },
          { cle: 'loyer', titre: 'Loyer', alignerADroite: true },
          { cle: 'etat', titre: 'État' },
        ]}
        lignes={unites}
        erreur={erreur}
        messageVide="Aucune unité pour ce filtre."
        rendu={(u) => (
          <tr key={u.id}>
            <td>{u.unit_number}</td>
            <td>{u.property_name}</td>
            <td className="montant">{Number(u.area)} m²</td>
            <td className="montant">
              {u.rooms}
              {u.bedrooms > 0 && <span className="sous">{u.bedrooms} chambre(s)</span>}
            </td>
            <td className="montant">{nombre.format(Number(u.rent_amount))}</td>
            <td>
              <span className={`etiquette ${u.status === 'occupied' ? 'paid' : 'pending'}`}>
                {u.status_display}
              </span>
            </td>
          </tr>
        )}
      />
    </>
  )
}
