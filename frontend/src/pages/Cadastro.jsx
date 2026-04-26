import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../store'
import api from '../api'
import toast from 'react-hot-toast'

export default function Cadastro() {
  const [form, setForm] = useState({
    nome: '', celular: '', senha: '', confirma: '',
    email: '', pix: '', time_coracao: '', whatsapp: true,
  })
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const nav = useNavigate()

  const f = (k, v) => setForm(p => ({ ...p, [k]: v }))

  const submit = async e => {
    e.preventDefault()
    if (form.senha !== form.confirma) { toast.error('Senhas não conferem'); return }
    if (form.senha.length < 4) { toast.error('Senha mínimo 4 caracteres'); return }
    setLoading(true)
    try {
      const { data } = await api.post('/auth/cadastro', {
        nome: form.nome, celular: form.celular, senha: form.senha,
        email: form.email, pix: form.pix || form.celular,
        time_coracao: form.time_coracao, whatsapp: form.whatsapp,
      })
      login({ uid: data.uid, nome: data.nome, role: 'user' }, data.token)
      toast.success('Cadastro realizado!')
      nav('/')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro no cadastro')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen field-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl text-goal-400 tracking-widest mb-1">
            NOVO APOSTADOR
          </h1>
          <p className="text-[#4a7a5a] text-xs font-mono">PASSO {step} DE 2</p>
        </div>

        <form onSubmit={step === 1 ? e => { e.preventDefault(); setStep(2) } : submit}
              className="card space-y-4">
          {step === 1 && <>
            <div>
              <label className="stat-label block mb-2">Nome completo</label>
              <input className="input" placeholder="João Silva" value={form.nome}
                onChange={e => f('nome', e.target.value)} required />
            </div>
            <div>
              <label className="stat-label block mb-2">Celular (DDD + número)</label>
              <input className="input" placeholder="(21) 99999-9999" value={form.celular}
                onChange={e => f('celular', e.target.value)} required />
            </div>
            <div className="flex items-center gap-3">
              <input type="checkbox" id="wa" checked={form.whatsapp}
                onChange={e => f('whatsapp', e.target.checked)}
                className="accent-goal-500 w-4 h-4" />
              <label htmlFor="wa" className="text-sm text-[#6b9c7c]">
                Este celular é WhatsApp
              </label>
            </div>
            <button type="submit" className="btn-primary w-full mt-2">
              PRÓXIMO
            </button>
          </>}

          {step === 2 && <>
            <div>
              <label className="stat-label block mb-2">Senha (mín. 4 caracteres)</label>
              <input type="password" className="input" placeholder="••••••••"
                value={form.senha} onChange={e => f('senha', e.target.value)} required />
            </div>
            <div>
              <label className="stat-label block mb-2">Confirmar senha</label>
              <input type="password" className="input" placeholder="••••••••"
                value={form.confirma} onChange={e => f('confirma', e.target.value)} required />
            </div>
            <div>
              <label className="stat-label block mb-2">Chave PIX (opcional)</label>
              <input className="input" placeholder={form.celular || 'celular, email ou CPF'}
                value={form.pix} onChange={e => f('pix', e.target.value)} />
              <p className="text-xs text-[#4a7a5a] mt-1 font-mono">
                Vazio = usa o celular como PIX
              </p>
            </div>
            <div>
              <label className="stat-label block mb-2">Time do coração (opcional)</label>
              <input className="input" placeholder="Flamengo" value={form.time_coracao}
                onChange={e => f('time_coracao', e.target.value)} />
            </div>
            <div className="flex gap-2 mt-2">
              <button type="button" onClick={() => setStep(1)} className="btn-ghost flex-1">
                VOLTAR
              </button>
              <button type="submit" className="btn-primary flex-1" disabled={loading}>
                {loading ? 'Salvando...' : 'CADASTRAR'}
              </button>
            </div>
          </>}
        </form>

        <p className="text-center mt-4 text-[#4a7a5a] text-sm">
          Já tem conta?{' '}
          <Link to="/login" className="text-goal-400 hover:underline">Entrar</Link>
        </p>
      </div>
    </div>
  )
}
