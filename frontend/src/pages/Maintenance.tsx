import { useEffect, useState } from 'react'

import { api } from '../api/client'
import Tableau from '../components/Tableau'
import type { Intervention } from '../types'

const nombre = new Intl.NumberFormat('fr-FR')

const FILTRES = [
  { valeur: '', libelle: 'Toutes' },
  { valeur: 'submitted', libelle: 'Soumises' },
  { valeur: 'in_progress', libelle: 'En cours' },
  { valeur: 'completed', libelle: 'Terminées' },
]

const COULEUR_PRIORITE: Record<string, string> = {
  urgent: 'retard',
  high: 'pending',
  medium: 'partial',
  low: 'cancelled',
}

export default function Maintenance() {
  const [demandes, setDemandes] = useState<Intervention[] | null>(null)
  const [filtre, setFiltre] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    setDemandes(null)
    const requete = filtre ? `/maintenance/?status=${filtre}` : '/maintenance/'
    api.get<Intervention[]>(requete).then(setDemandes).catch((e) => setErreur(e.message))
  }, [filtre])

  return (
    <>
      <h1>Maintenance</h1>
      <p className="intro">Les interventions demandées sur votre patrimoine.</p>

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
          { cle: 'demande', titre: 'Demande' },
          { cle: 'unite', titre: 'Unité' },
          { cle: 'priorite', titre: 'Priorité' },
          { cle: 'etat', titre: 'État' },
          { cle: 'cout', titre: 'Coût', alignerADroite: true },
        ]}
        lignes={demandes}
        erreur={erreur}
        messageVide="Aucune intervention pour ce filtre."
        rendu={(d) => (
          <tr key={d.id}>
            <td>
              {d.title}
              <span className="sous">{d.category_display}</span>
            </td>
            <td>{d.unit_label}</td>
            <td>
              <span className={`etiquette ${COULEUR_PRIORITE[d.priority] ?? 'cancelled'}`}>
                {d.priority_display}
              </span>
            </td>
            <td>{d.status_display}</td>
            <td className="montant">{d.cost ? nombre.format(Number(d.cost)) : '-'}</td>
          </tr>
        )}
      />
    </>
  )
}
