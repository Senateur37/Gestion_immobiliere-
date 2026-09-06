import { Navigate, Route, Routes } from 'react-router-dom'

import Mise from './components/Mise'
import { useAuth } from './auth/AuthContext'
import Baux from './pages/Baux'
import Biens from './pages/Biens'
import Connexion from './pages/Connexion'
import Echeances from './pages/Echeances'
import Encaissements from './pages/Encaissements'
import TableauDeBord from './pages/TableauDeBord'

export default function App() {
  const { utilisateur, chargement } = useAuth()

  // Tant que le profil n'est pas resolu, on n'affiche ni l'application ni
  // la page de connexion : rediriger trop tot ferait clignoter l'ecran
  // pour un utilisateur deja connecte dont le jeton est encore valide.
  if (chargement) return <p style={{ padding: 40 }}>Chargement...</p>

  if (!utilisateur) {
    return (
      <Routes>
        <Route path="/connexion" element={<Connexion />} />
        <Route path="*" element={<Navigate to="/connexion" replace />} />
      </Routes>
    )
  }

  return (
    <Mise>
      <Routes>
        <Route path="/" element={<TableauDeBord />} />
        <Route path="/biens" element={<Biens />} />
        <Route path="/baux" element={<Baux />} />
        <Route path="/echeances" element={<Echeances />} />
        <Route path="/encaissements" element={<Encaissements />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Mise>
  )
}
