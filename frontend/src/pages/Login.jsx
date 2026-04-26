import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../store'
import api from '../api'
import toast from 'react-hot-toast'

export default function Login() {
  const [form, setForm] = useState({ celular: '', senha: '' })
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const nav = useNavigate()

  const submit = async e => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', form)
      login({ uid: data.uid, nome: data.nome, role: data.role }, data.token)
      toast.success(`Bem-vindo, ${data.nome}!`)
      nav(data.role === 'admin' ? '/admin' : '/')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen field-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-10">
          <h1 className="font-display text-5xl text-goal-400 tracking-widest mb-2">
            BOLÃO SURVIVOR
          </h1>
          <p className="text-[#4a7a5a] text-sm font-mono">
            ÚLTIMO APOSTADOR EM PÉ VENCE
          </p>
        </div>

        <form onSubmit={submit} className="card space-y-4">
          <div>
            <label className="stat-label block mb-2">Celular</label>
            <input
              className="input"
              placeholder="(XX) 99999-9999"
              value={form.celular}
              onChange={e => setForm(f => ({ ...f, celular: e.target.value }))}
              required
            />
          </div>
          <div>
            <label className="stat-label block mb-2">Senha</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={form.senha}
              onChange={e => setForm(f => ({ ...f, senha: e.target.value }))}
              required
            />
          </div>
          <button type="submit" className="btn-primary w-full mt-2" disabled={loading}>
            {loading ? 'Entrando...' : 'ENTRAR'}
          </button>
        </form>

        <p className="text-center mt-4 text-[#4a7a5a] text-sm">
          Não tem conta?{' '}
          <Link to="/cadastro" className="text-goal-400 hover:underline">
            Cadastrar
          </Link>
        </p>
      </div>
    </div>
  )
}
