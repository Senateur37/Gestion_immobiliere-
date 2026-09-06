import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Rapport } from '../types'

const nombre = new Intl.NumberFormat('fr-FR')

/** Barre de repartition : un chiffre seul ne montre pas les proportions. */
function Repartition({ donnees }: { donnees: Record<string, number> }) {
  const total = Object.values(donnees).reduce((somme, valeur) => somme + valeur, 0)
  if (total === 0) return <p className="sous">Aucune donnée.</p>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {Object.entries(donnees).map(([libelle, valeur]) => (
        <div key={libelle}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.86rem',
              marginBottom: 4,
            }}
          >
            <span>{libelle}</span>
            <span style={{ fontVariantNumeric: 'tabular-nums' }}>{valeur}</span>
          </div>
          <div
            style={{
              height: 6,
              background: 'var(--border-color)',
              borderRadius: 999,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${(valeur / total) * 100}%`,
                height: '100%',
                background: 'var(--primary)',
              }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Rapports() {
  const [rapport, setRapport] = useState<Rapport | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    api.get<Rapport>('/report/').then(setRapport).catch((e) => setErreur(e.message))
  }, [])

  if (erreur) return <div className="erreur">{erreur}</div>
  if (!rapport) return <p className="intro">Chargement...</p>

  return (
    <>
      <h1>Rapports</h1>
      <p className="intro">La performance de votre patrimoine, en un écran.</p>

      <div className="grille">
        <div className="carte">
          <div className="libelle">Loyer mensuel</div>
          <div className="valeur">{nombre.format(Number(rapport.rent.monthly_total))}</div>
          <div className="detail">
            moyenne {nombre.format(rapport.rent.average)} sur {rapport.rent.active_leases} bail(s)
          </div>
        </div>
        <div className="carte">
          <div className="libelle">Encaissé</div>
          <div className="valeur">{nombre.format(Number(rapport.collected))}</div>
          <div className="detail">FCFA</div>
        </div>
        <div className="carte alerte">
          <div className="libelle">Reste à encaisser</div>
          <div className="valeur">{nombre.format(Number(rapport.outstanding))}</div>
          <div className="detail">FCFA</div>
        </div>
        <div className="carte">
          <div className="libelle">Interventions ouvertes</div>
          <div className="valeur">{rapport.maintenance_open}</div>
          <div className="detail">à traiter</div>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 16,
        }}
      >
        <section className="panneau" style={{ padding: 20 }}>
          <h2 style={{ fontSize: '1rem', marginBottom: 14 }}>Unités par état</h2>
          <Repartition donnees={rapport.units_by_status} />
        </section>

        <section className="panneau" style={{ padding: 20 }}>
          <h2 style={{ fontSize: '1rem', marginBottom: 14 }}>Échéances par état</h2>
          <Repartition donnees={rapport.charges_by_status} />
        </section>

        <section className="panneau" style={{ padding: 20 }}>
          <h2 style={{ fontSize: '1rem', marginBottom: 14 }}>Trésorerie</h2>
          {rapport.treasury.length === 0 && <p className="sous">Aucun compte actif.</p>}
          {rapport.treasury.map((compte) => (
            <div
              key={compte.code}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '8px 0',
                borderBottom: '1px solid var(--border-color)',
              }}
            >
              <span>
                {compte.nom}
                <span className="sous">{compte.code}</span>
              </span>
              <strong style={{ fontVariantNumeric: 'tabular-nums' }}>
                {nombre.format(Number(compte.solde))}
              </strong>
            </div>
          ))}
        </section>
      </div>
    </>
  )
}
