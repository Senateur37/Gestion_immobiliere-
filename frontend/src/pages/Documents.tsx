import { useEffect, useState } from 'react'

import { api } from '../api/client'
import Tableau from '../components/Tableau'
import type { DocumentFichier } from '../types'

function taille(octets: number) {
  if (octets < 1024) return `${octets} o`
  if (octets < 1024 * 1024) return `${Math.round(octets / 1024)} Ko`
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`
}

export default function Documents() {
  const [documents, setDocuments] = useState<DocumentFichier[] | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    api.get<DocumentFichier[]>('/documents/').then(setDocuments).catch((e) => setErreur(e.message))
  }, [])

  return (
    <>
      <h1>Documents</h1>
      <p className="intro">Contrats, diagnostics, quittances et pièces légales.</p>

      <Tableau
        colonnes={[
          { cle: 'titre', titre: 'Document' },
          { cle: 'categorie', titre: 'Catégorie' },
          { cle: 'taille', titre: 'Taille', alignerADroite: true },
          { cle: 'signe', titre: 'Signé' },
          { cle: 'expire', titre: 'Expire le' },
        ]}
        lignes={documents}
        erreur={erreur}
        messageVide="Aucun document enregistré."
        rendu={(d) => (
          <tr key={d.id}>
            <td>
              {d.title}
              <span className="sous">{d.mime_type}</span>
            </td>
            <td>{d.category_display}</td>
            <td className="montant">{taille(d.file_size)}</td>
            <td>
              <span className={`etiquette ${d.is_signed ? 'paid' : 'cancelled'}`}>
                {d.is_signed ? 'Signé' : 'Non signé'}
              </span>
            </td>
            <td>{d.expires_at ? new Date(d.expires_at).toLocaleDateString('fr-FR') : '-'}</td>
          </tr>
        )}
      />
    </>
  )
}
