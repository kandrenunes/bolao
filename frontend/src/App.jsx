import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './store'
import Login from './pages/Login'
import Cadastro from './pages/Cadastro'
import Dashboard from './pages/Dashboard'
import Apostas from './pages/Apostas'
import Grupos from './pages/Grupos'
import AdminPanel from './pages/AdminPanel'
import Layout from './components/Layout'

function PrivateRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

function AdminRoute({ children }) {
  const { user } = useAuth()
  return user?.role === 'admin' ? children : <Navigate to="/" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login"   element={<Login />} />
      <Route path="/cadastro" element={<Cadastro />} />
      <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route index          element={<Dashboard />} />
        <Route path="apostas" element={<Apostas />} />
        <Route path="grupos"  element={<Grupos />} />
      </Route>
      <Route path="/admin" element={<AdminRoute><AdminPanel /></AdminRoute>} />
    </Routes>
  )
}
