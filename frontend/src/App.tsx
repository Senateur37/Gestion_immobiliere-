import { Navigate, Route, Routes } from 'react-router-dom'

import Mise from './components/Mise'
import { useAuth } from './auth/AuthContext'
import Baux from './pages/Baux'
import Biens from './pages/Biens'
import Comptabilite from './pages/Comptabilite'
import Connexion from './pages/Connexion'
import Documents from './pages/Documents'
import Echeances from './pages/Echeances'
import Encaissements from './pages/Encaissements'
import Locataires from './pages/Locataires'
import Maintenance from './pages/Maintenance'
import Rapports from './pages/Rapports'
import TableauDeBord from './pages/TableauDeBord'
import Unites from './pages/Unites'
import Utilisateurs from './pages/Utilisateurs'

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
        <Route path="/unites" element={<Unites />} />
        <Route path="/baux" element={<Baux />} />
        <Route path="/locataires" element={<Locataires />} />

        <Route path="/rapports" element={<Rapports />} />
        <Route path="/echeances" element={<Echeances />} />
        <Route path="/encaissements" element={<Encaissements />} />
        <Route path="/maintenance" element={<Maintenance />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/comptabilite" element={<Comptabilite />} />

        <Route path="/utilisateurs" element={<Utilisateurs />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Mise>
  )
}
