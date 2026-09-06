/**
 * Tableau de donnees, avec ses etats de chargement, d'erreur et de vide.
 *
 * Les six ecrans qui l'utilisent partagent ainsi le meme comportement :
 * un ecran vide ne doit jamais ressembler a un ecran casse.
 */
import type { ReactNode } from 'react'

type Props<T> = {
  colonnes: { cle: string; titre: string; alignerADroite?: boolean }[]
  lignes: T[] | null
  erreur?: string | null
  messageVide?: string
  rendu: (ligne: T) => ReactNode
}

export default function Tableau<T>({
  colonnes,
  lignes,
  erreur,
  messageVide = 'Rien à afficher pour le moment.',
  rendu,
}: Props<T>) {
  if (erreur) return <div className="erreur">{erreur}</div>

  return (
    <section className="panneau">
      <div className="defilement">
        <table>
          <thead>
            <tr>
              {colonnes.map((colonne) => (
                <th key={colonne.cle} className={colonne.alignerADroite ? 'montant' : undefined}>
                  {colonne.titre}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {lignes === null && (
              <tr>
                <td colSpan={colonnes.length} className="vide">
                  Chargement...
                </td>
              </tr>
            )}
            {lignes?.map(rendu)}
            {lignes?.length === 0 && (
              <tr>
                <td colSpan={colonnes.length} className="vide">
                  {messageVide}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
