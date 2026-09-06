/**
 * Client de l'API v1.
 *
 * Un seul point de passage pour tous les appels : le jeton, le
 * rafraichissement et la traduction des erreurs y sont traites une fois,
 * plutot que repetes dans chaque ecran.
 */

const CLE_ACCES = 'immopilot.access'
const CLE_RAFRAICHISSEMENT = 'immopilot.refresh'
const CLE_ORGANISATION = 'immopilot.organization'

export type Jetons = { access: string; refresh: string }

export const jetons = {
  lire: () => localStorage.getItem(CLE_ACCES),
  lireRafraichissement: () => localStorage.getItem(CLE_RAFRAICHISSEMENT),
  ecrire: ({ access, refresh }: Jetons) => {
    localStorage.setItem(CLE_ACCES, access)
    localStorage.setItem(CLE_RAFRAICHISSEMENT, refresh)
  },
  effacer: () => {
    localStorage.removeItem(CLE_ACCES)
    localStorage.removeItem(CLE_RAFRAICHISSEMENT)
    localStorage.removeItem(CLE_ORGANISATION)
  },
}

export const organisationActive = {
  lire: () => localStorage.getItem(CLE_ORGANISATION),
  ecrire: (slug: string) => localStorage.setItem(CLE_ORGANISATION, slug),
}

/** Erreur portant le code metier renvoye par l'API. */
export class ErreurApi extends Error {
  code: string
  statut: number

  constructor(message: string, code: string, statut: number) {
    super(message)
    this.code = code
    this.statut = statut
  }
}

async function rafraichirLeJeton(): Promise<boolean> {
  const refresh = jetons.lireRafraichissement()
  if (!refresh) return false

  const reponse = await fetch('/api/v1/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!reponse.ok) return false

  const donnees = await reponse.json()
  localStorage.setItem(CLE_ACCES, donnees.access)
  return true
}

async function envoyer<T>(chemin: string, options: RequestInit, reessai = true): Promise<T> {
  const entetes: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  const jeton = jetons.lire()
  if (jeton) entetes.Authorization = `Bearer ${jeton}`

  // Le serveur verifie toujours que l'utilisateur est membre de
  // l'organisation demandee : cet en-tete est une preference, pas une
  // autorisation.
  const organisation = organisationActive.lire()
  if (organisation) entetes['X-Organization'] = organisation

  const reponse = await fetch(`/api/v1${chemin}`, { ...options, headers: entetes })

  // Un jeton expire se rafraichit une fois, sans que l'ecran appelant
  // ait a s'en occuper.
  if (reponse.status === 401 && reessai && (await rafraichirLeJeton())) {
    return envoyer<T>(chemin, options, false)
  }

  if (reponse.status === 204) return undefined as T

  const donnees = await reponse.json().catch(() => null)

  if (!reponse.ok) {
    const message =
      donnees?.detail ??
      (donnees ? Object.values(donnees).flat().join(' ') : null) ??
      'Une erreur est survenue.'
    throw new ErreurApi(message, donnees?.code ?? 'error', reponse.status)
  }

  return donnees as T
}

export const api = {
  get: <T>(chemin: string) => envoyer<T>(chemin, { method: 'GET' }),
  post: <T>(chemin: string, corps: unknown) =>
    envoyer<T>(chemin, { method: 'POST', body: JSON.stringify(corps) }),
}
