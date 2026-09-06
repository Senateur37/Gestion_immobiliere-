import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Bail, CompteFinancier, Encaissement } from '../types'

const nombre = new Intl.NumberFormat('fr-FR')

const MODES = [
  { valeur: 'cash', libelle: 'Espèces' },
  { valeur: 'orange_money', libelle: 'Orange Money' },
  { valeur: 'moov_money', libelle: 'Moov Money' },
  { valeur: 'bank_transfer', libelle: 'Virement bancaire' },
  { valeur: 'check', libelle: 'Chèque' },
  { valeur: 'card', libelle: 'Carte bancaire' },
]

function aujourdhui() {
  return new Date().toISOString().slice(0, 10)
}

export default function Encaissements() {
  const [encaissements, setEncaissements] = useState<Encaissement[] | null>(null)
  const [baux, setBaux] = useState<Bail[]>([])
  const [comptes, setComptes] = useState<CompteFinancier[]>([])
  const [erreur, setErreur] = useState<string | null>(null)
  const [succes, setSucces] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  const [bail, setBail] = useState('')
  const [compte, setCompte] = useState('')
  const [montant, setMontant] = useState('')
  const [date, setDate] = useState(aujourdhui())
  const [mode, setMode] = useState('cash')
  const [reference, setReference] = useState('')

  function recharger() {
    api.get<Encaissement[]>('/payments/').then(setEncaissements).catch((e) => setErreur(e.message))
  }

  useEffect(() => {
    recharger()
    api.get<Bail[]>('/leases/?status=active').then(setBaux).catch(() => setBaux([]))
    api.get<CompteFinancier[]>('/accounts/').then(setComptes).catch(() => setComptes([]))
  }, [])

  async function enregistrer(evenement: React.FormEvent) {
    evenement.preventDefault()
    setErreur(null)
    setSucces(null)
    setEnvoi(true)
    try {
      const cree = await api.post<Encaissement>('/payments/record/', {
        lease: Number(bail),
        compte: Number(compte),
        amount: montant,
        payment_date: date,
        method: mode,
        external_reference: reference,
      })
      // Le reliquat non imputé est une avance, pas une anomalie : on le
      // dit explicitement plutôt que de laisser deviner.
      const avance = Number(cree.amount_unallocated)
      setSucces(
        avance > 0
          ? `Encaissement ${cree.reference} enregistré. ${nombre.format(avance)} FCFA restent en avance.`
          : `Encaissement ${cree.reference} enregistré et imputé.`,
      )
      setMontant('')
      setReference('')
      recharger()
    } catch (e) {
      setErreur((e as Error).message)
    } finally {
      setEnvoi(false)
    }
  }

  const total = encaissements?.reduce((somme, e) => somme + Number(e.amount), 0) ?? 0

  return (
    <>
      <h1>Encaissements</h1>
      <p className="intro">Les sommes reçues, avec leur imputation sur les échéances.</p>

      {erreur && <div className="erreur">{erreur}</div>}
      {succes && <div className="succes">{succes}</div>}

      <section className="panneau" style={{ padding: 22, marginBottom: 24 }}>
        <h2 style={{ fontSize: '1.05rem', marginBottom: 16 }}>Enregistrer un encaissement</h2>
        <form
          onSubmit={enregistrer}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
            gap: 14,
          }}
        >
          <label className="champ">
            <span>Bail</span>
            <select value={bail} onChange={(e) => setBail(e.target.value)} required>
              <option value="">Choisir...</option>
              {baux.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.lease_number} - {b.tenant_name}
                </option>
              ))}
            </select>
          </label>

          <label className="champ">
            <span>Compte encaisseur</span>
            <select value={compte} onChange={(e) => setCompte(e.target.value)} required>
              <option value="">Choisir...</option>
              {comptes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nom} ({c.code})
                </option>
              ))}
            </select>
          </label>

          <label className="champ">
            <span>Montant reçu</span>
            <input
              type="number"
              min="1"
              step="1"
              value={montant}
              onChange={(e) => setMontant(e.target.value)}
              required
            />
          </label>

          <label className="champ">
            <span>Date</span>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </label>

          <label className="champ">
            <span>Mode de paiement</span>
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              {MODES.map((m) => (
                <option key={m.valeur} value={m.valeur}>
                  {m.libelle}
                </option>
              ))}
            </select>
          </label>

          <label className="champ">
            <span>Référence externe</span>
            <input
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              placeholder="N° de transaction"
            />
          </label>

          <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 16 }}>
            <button className="bouton" disabled={envoi}>
              {envoi ? 'Enregistrement...' : 'Enregistrer'}
            </button>
          </div>
        </form>
      </section>

      <div className="grille" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="carte">
          <div className="libelle">Total encaissé</div>
          <div className="valeur">{nombre.format(total)}</div>
          <div className="detail">FCFA</div>
        </div>
      </div>

      <section className="panneau">
        <div className="defilement">
          <table>
            <thead>
              <tr>
                <th>Référence</th>
                <th>Locataire</th>
                <th>Date</th>
                <th className="montant">Montant</th>
                <th className="montant">Imputé</th>
                <th className="montant">Avance</th>
              </tr>
            </thead>
            <tbody>
              {encaissements?.map((e) => (
                <tr key={e.id}>
                  <td>
                    {e.reference}
                    <span className="sous">
                      {e.method_display}
                      {e.external_reference ? ` · ${e.external_reference}` : ''}
                    </span>
                  </td>
                  <td>
                    {e.tenant_name}
                    <span className="sous">{e.lease_number}</span>
                  </td>
                  <td>{new Date(e.payment_date).toLocaleDateString('fr-FR')}</td>
                  <td className="montant">{nombre.format(Number(e.amount))}</td>
                  <td className="montant">{nombre.format(Number(e.amount_allocated))}</td>
                  <td className="montant">
                    {Number(e.amount_unallocated) > 0
                      ? nombre.format(Number(e.amount_unallocated))
                      : '-'}
                  </td>
                </tr>
              ))}
              {encaissements?.length === 0 && (
                <tr>
                  <td colSpan={6} className="vide">
                    Aucun encaissement enregistré.
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
