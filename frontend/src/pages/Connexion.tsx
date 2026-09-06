import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export default function Connexion() {
  const { connexion } = useAuth()
  const naviguer = useNavigate()
  const [identifiant, setIdentifiant] = useState('')
  const [motDePasse, setMotDePasse] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  async function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault()
    setErreur(null)
    setEnvoi(true)
    try {
      await connexion(identifiant, motDePasse)
      naviguer('/')
    } catch {
      // Message volontairement identique quel que soit le champ fautif :
      // il ne doit pas reveler quels identifiants existent.
      setErreur('Identifiant ou mot de passe incorrect.')
    } finally {
      setEnvoi(false)
    }
  }

  return (
    <div className="page-connexion">
      <form className="carte-connexion" onSubmit={soumettre}>
        <div className="brand" style={{ color: 'var(--text-main)', textAlign: 'center' }}>
          ImmoPilot
        </div>
        <p className="intro" style={{ textAlign: 'center' }}>
          Gérez votre patrimoine avec élégance.
        </p>

        {erreur && <div className="erreur">{erreur}</div>}

        <label className="champ">
          <span>Identifiant</span>
          <input
            value={identifiant}
            onChange={(e) => setIdentifiant(e.target.value)}
            autoComplete="username"
            required
          />
        </label>

        <label className="champ">
          <span>Mot de passe</span>
          <input
            type="password"
            value={motDePasse}
            onChange={(e) => setMotDePasse(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        <button className="bouton" style={{ width: '100%', justifyContent: 'center' }} disabled={envoi}>
          {envoi ? 'Connexion…' : 'Accéder à l’espace'}
        </button>
      </form>
    </div>
  )
}
