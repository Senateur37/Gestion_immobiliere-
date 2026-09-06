/**
 * Etat d'authentification, partage par toute l'application.
 *
 * Le profil est charge une fois a l'ouverture : il porte l'utilisateur et
 * ses organisations, de sorte qu'aucun ecran n'a besoin de les redemander.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { api, jetons, organisationActive } from '../api/client'
import type { Membership, Utilisateur } from '../types'

type EtatAuth = {
  utilisateur: Utilisateur | null
  organisation: Membership | null
  chargement: boolean
  connexion: (identifiant: string, motDePasse: string) => Promise<void>
  deconnexion: () => void
  changerOrganisation: (slug: string) => void
}

const ContexteAuth = createContext<EtatAuth | null>(null)

type ReponseConnexion = {
  access: string
  refresh: string
  user: Utilisateur
}

export function FournisseurAuth({ children }: { children: ReactNode }) {
  const [utilisateur, setUtilisateur] = useState<Utilisateur | null>(null)
  const [chargement, setChargement] = useState(true)
  const [slugActif, setSlugActif] = useState<string | null>(organisationActive.lire())

  // Au demarrage, un jeton peut deja etre en memoire : on verifie qu'il
  // vaut encore quelque chose plutot que de supposer l'utilisateur connecte.
  useEffect(() => {
    if (!jetons.lire()) {
      setChargement(false)
      return
    }
    api
      .get<Utilisateur>('/auth/me/')
      .then(setUtilisateur)
      .catch(() => jetons.effacer())
      .finally(() => setChargement(false))
  }, [])

  const connexion = useCallback(async (identifiant: string, motDePasse: string) => {
    const reponse = await api.post<ReponseConnexion>('/auth/login/', {
      username: identifiant,
      password: motDePasse,
    })
    jetons.ecrire({ access: reponse.access, refresh: reponse.refresh })

    const parDefaut =
      reponse.user.memberships.find((m) => m.is_default) ?? reponse.user.memberships[0]
    if (parDefaut) {
      organisationActive.ecrire(parDefaut.organization.slug)
      setSlugActif(parDefaut.organization.slug)
    }
    setUtilisateur(reponse.user)
  }, [])

  const deconnexion = useCallback(() => {
    jetons.effacer()
    setUtilisateur(null)
    setSlugActif(null)
  }, [])

  const changerOrganisation = useCallback((slug: string) => {
    organisationActive.ecrire(slug)
    setSlugActif(slug)
  }, [])

  const organisation = useMemo(() => {
    if (!utilisateur) return null
    return (
      utilisateur.memberships.find((m) => m.organization.slug === slugActif) ??
      utilisateur.memberships[0] ??
      null
    )
  }, [utilisateur, slugActif])

  const valeur = useMemo(
    () => ({ utilisateur, organisation, chargement, connexion, deconnexion, changerOrganisation }),
    [utilisateur, organisation, chargement, connexion, deconnexion, changerOrganisation],
  )

  return <ContexteAuth.Provider value={valeur}>{children}</ContexteAuth.Provider>
}

export function useAuth() {
  const contexte = useContext(ContexteAuth)
  if (!contexte) {
    throw new Error("useAuth doit etre appele a l'interieur de FournisseurAuth.")
  }
  return contexte
}
