import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../store'
import { Trophy, Layers, Users, LogOut, ShieldCheck } from 'lucide-react'

export default function Layout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()

  const handleLogout = () => { logout(); nav('/login') }

  return (
    <div className="min-h-screen field-bg">
      {/* Top bar */}
      <header className="border-b border-[#1a3d28] bg-pitch-900/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <span className="font-display text-2xl text-goal-400 tracking-widest">
            BOLÃO SURVIVOR
          </span>
          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={({isActive}) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors
               ${isActive ? 'bg-goal-500/20 text-goal-400' : 'text-[#6b9c7c] hover:text-goal-400'}`
            }>
              <Trophy size={15}/> Dashboard
            </NavLink>
            <NavLink to="/apostas" className={({isActive}) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors
               ${isActive ? 'bg-goal-500/20 text-goal-400' : 'text-[#6b9c7c] hover:text-goal-400'}`
            }>
              <Layers size={15}/> Apostas
            </NavLink>
            <NavLink to="/grupos" className={({isActive}) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors
               ${isActive ? 'bg-goal-500/20 text-goal-400' : 'text-[#6b9c7c] hover:text-goal-400'}`
            }>
              <Users size={15}/> Grupos
            </NavLink>
            {user?.role === 'admin' && (
              <NavLink to="/admin" className="flex items-center gap-1.5 px-3 py-1.5
                rounded-lg text-sm text-yellow-400 hover:bg-yellow-500/10 transition-colors">
                <ShieldCheck size={15}/> Admin
              </NavLink>
            )}
            <button onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm
                         text-[#6b9c7c] hover:text-red-400 transition-colors ml-2">
              <LogOut size={15}/>
            </button>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
