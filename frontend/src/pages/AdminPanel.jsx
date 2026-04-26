import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../store'
import api from '../api'
import toast from 'react-hot-toast'
import {
  Settings, Play, CheckSquare, Users, Trophy,
  BarChart3, LogOut, ChevronLeft, ShieldCheck,
  Coins, Clock, AlertCircle
} from 'lucide-react'

// ── Sub-componentes ──────────────────────────────────────────────────────────

function ConfigSection({ cfg, onRefresh }) {
  const [rodadaIni, setRodadaIni] = useState('')
  const [saving, setSaving] = useState(false)

  const salvar = async () => {
    setSaving(true)
    try {
      await api.post('/admin/config', { rodada_inicial: Number(rodadaIni) })
      toast.success('Configuração salva!')
      onRefresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro')
    } finally { setSaving(false) }
  }

  if (cfg?.rodada_inicial) return (
    <div className="card">
      <p className="stat-label mb-3">CONFIGURAÇÃO</p>
      <div className="grid grid-cols-2 gap-3 text-sm font-mono">
        <div><span className="text-[#4a7a5a]">Rodada inicial:</span> <span className="text-goal-400">{cfg.rodada_inicial}</span></div>
        <div><span className="text-[#4a7a5a]">Total rodadas:</span> <span className="text-goal-400">{cfg.total_rodadas}</span></div>
        <div><span className="text-[#4a7a5a]">Rodada ativa:</span> <span className="text-goal-400">{cfg.rodada_ativa || '—'}</span></div>
        <div><span className="text-[#4a7a5a]">Próxima:</span> <span className="text-yellow-400">{cfg.proxima_rodada || '—'}</span></div>
      </div>
    </div>
  )

  return (
    <div className="card">
      <p className="stat-label mb-3">CONFIGURAÇÃO INICIAL</p>
      <p className="text-xs text-[#4a7a5a] font-mono mb-4">
        Define a rodada de início das apostas. Irreversível.
      </p>
      <input className="input mb-3" type="number" placeholder="Rodada inicial (ex: 8)"
        value={rodadaIni} onChange={e => setRodadaIni(e.target.value)} />
      <button onClick={salvar} className="btn-primary w-full" disabled={saving}>
        {saving ? 'Salvando...' : 'SALVAR'}
      </button>
    </div>
  )
}

function AbrirRodadaSection({ cfg, onRefresh }) {
  const [jogos, setJogos] = useState([])
  const [confirmados, setConfirmados] = useState({})
  const [prazo, setPrazo] = useState('')
  const [step, setStep] = useState('jogos')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!cfg?.proxima_rodada) return
    api.get(`/rodadas/${cfg.proxima_rodada}`).then(r => setJogos(r.data.jogos))
  }, [cfg?.proxima_rodada])

  const toggleJogo = idx => setConfirmados(p => ({ ...p, [idx]: !p[idx] }))

  const abrir = async () => {
    const idxConf = jogos.filter(j => confirmados[j.idx]).map(j => j.idx)
    if (!idxConf.length) { toast.error('Confirme ao menos 1 jogo'); return }
    if (!prazo) { toast.error('Informe o prazo'); return }
    setSaving(true)
    try {
      await api.post('/admin/abrir-rodada', { jogos_confirmados: idxConf, prazo })
      toast.success(`Rodada ${cfg.proxima_rodada} aberta!`)
      onRefresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro')
    } finally { setSaving(false) }
  }

  if (!cfg?.proxima_rodada) return (
    <div className="card">
      <p className="text-[#4a7a5a] font-mono text-sm">Todas as rodadas processadas.</p>
    </div>
  )

  if (cfg.rodada_ativa && !cfg.prazo_expirado) return (
    <div className="card border border-goal-500/20">
      <p className="stat-label mb-1">RODADA {cfg.rodada_ativa} — ABERTA</p>
      <p className="text-xs font-mono text-[#4a7a5a]">
        Prazo: <span className="text-yellow-400">{cfg.prazo?.slice(0,16)}</span>
      </p>
    </div>
  )

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="stat-label">ABRIR RODADA</p>
          <p className="font-display text-3xl text-goal-400 tracking-wider">
            {cfg.proxima_rodada}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setStep('jogos')}
            className={`text-xs font-mono px-3 py-1.5 rounded-lg border transition-colors
              ${step === 'jogos' ? 'border-goal-500 text-goal-400' : 'border-[#1a3d28] text-[#4a7a5a]'}`}>
            1. JOGOS
          </button>
          <button onClick={() => setStep('prazo')}
            className={`text-xs font-mono px-3 py-1.5 rounded-lg border transition-colors
              ${step === 'prazo' ? 'border-goal-500 text-goal-400' : 'border-[#1a3d28] text-[#4a7a5a]'}`}>
            2. PRAZO
          </button>
        </div>
      </div>

      {step === 'jogos' && (
        <>
          <p className="text-xs text-[#4a7a5a] font-mono">
            Confirme os jogos que ocorrem nesta rodada:
          </p>
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {jogos.map(j => (
              <label key={j.idx}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                  ${confirmados[j.idx] ? 'border-goal-500/50 bg-goal-500/5' : 'border-[#1a3d28] hover:border-[#2d5a3d]'}`}>
                <input type="checkbox" checked={!!confirmados[j.idx]}
                  onChange={() => toggleJogo(j.idx)}
                  className="accent-goal-500 w-4 h-4 flex-shrink-0" />
                <span className="text-xs font-mono text-[#4a7a5a] w-5">{j.idx}</span>
                <span className="text-sm flex-1">
                  <strong>{j.casa}</strong>
                  <span className="text-[#4a7a5a] mx-2">×</span>
                  <strong>{j.visit}</strong>
                </span>
              </label>
            ))}
          </div>
          <div className="flex justify-between text-xs font-mono text-[#4a7a5a]">
            <span>{Object.values(confirmados).filter(Boolean).length} confirmado(s)</span>
            <button onClick={() => {
              const all = {}
              jogos.forEach(j => { all[j.idx] = true })
              setConfirmados(all)
            }} className="text-goal-500 hover:underline">selecionar todos</button>
          </div>
          <button onClick={() => setStep('prazo')} className="btn-primary w-full">
            PRÓXIMO: PRAZO
          </button>
        </>
      )}

      {step === 'prazo' && (
        <>
          <div>
            <label className="stat-label block mb-2">DATA E HORA LIMITE</label>
            <input className="input" placeholder="DD/MM/AAAA HH:MM"
              value={prazo} onChange={e => setPrazo(e.target.value)} />
            <p className="text-xs text-[#4a7a5a] font-mono mt-1">
              Ex: 25/01/2025 20:00
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setStep('jogos')} className="btn-ghost flex-1">VOLTAR</button>
            <button onClick={abrir} className="btn-primary flex-1" disabled={saving}>
              {saving ? 'Abrindo...' : 'ABRIR RODADA'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

function ResultadoSection({ cfg, onRefresh }) {
  const [rodada, setRodada] = useState(null)
  const [resultados, setResultados] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!cfg?.rodada_ativa || !cfg?.prazo_expirado) return
    api.get(`/rodadas/${cfg.rodada_ativa}`).then(r => {
      setRodada(r.data)
      const init = {}
      r.data.jogos.filter(j => j.confirmado).forEach(j => { init[j.idx] = null })
      setResultados(init)
    })
  }, [cfg?.rodada_ativa, cfg?.prazo_expirado])

  const salvar = async () => {
    const payload = Object.entries(resultados).map(([idx, venc]) => ({
      jogo_idx: Number(idx),
      vencedor: venc,
    }))
    setSaving(true)
    try {
      await api.post('/admin/resultado', payload)
      toast.success('Resultado inserido e eliminações processadas!')
      onRefresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro')
    } finally { setSaving(false) }
  }

  if (!cfg?.rodada_ativa) return (
    <div className="card">
      <div className="flex items-center gap-2 text-[#4a7a5a]">
        <AlertCircle size={16}/>
        <p className="text-sm font-mono">Abra uma rodada para inserir resultado.</p>
      </div>
    </div>
  )

  if (!cfg?.prazo_expirado) return (
    <div className="card border border-yellow-900/30">
      <div className="flex items-center gap-2 text-yellow-600">
        <Clock size={16}/>
        <p className="text-sm font-mono">
          Apostas ainda abertas. Aguarde o prazo encerrar para inserir resultado.
        </p>
      </div>
    </div>
  )

  const jogosConf = rodada?.jogos?.filter(j => j.confirmado) || []

  return (
    <div className="card space-y-4">
      <div>
        <p className="stat-label">RESULTADO</p>
        <p className="font-display text-3xl text-goal-400 tracking-wider">
          RODADA {cfg.rodada_ativa}
        </p>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
        {jogosConf.map(j => (
          <div key={j.idx} className="card bg-pitch-900/50 space-y-2">
            <p className="text-xs font-mono text-[#4a7a5a]">JOGO {j.idx}</p>
            <div className="grid grid-cols-3 gap-2 text-sm">
              {[
                { label: j.casa, val: j.casa },
                { label: 'EMPATE', val: null },
                { label: j.visit, val: j.visit },
              ].map(op => (
                <button key={String(op.val)} onClick={() => setResultados(p => ({ ...p, [j.idx]: op.val }))}
                  className={`py-2 rounded-lg border text-xs font-bold transition-all
                    ${resultados[j.idx] === op.val
                      ? op.val === null
                        ? 'border-yellow-500 bg-yellow-500/20 text-yellow-400'
                        : 'border-goal-500 bg-goal-500/20 text-goal-400'
                      : 'border-[#1a3d28] hover:border-[#2d5a3d] text-[#6b9c7c]'}`}>
                  {op.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <button onClick={salvar} className="btn-primary w-full" disabled={saving}>
        {saving ? 'Processando...' : 'SALVAR E PROCESSAR ELIMINAÇÕES'}
      </button>
    </div>
  )
}

function CreditarSection() {
  const [form, setForm] = useState({ celular: '', quantidade: '', motivo: '' })
  const [saving, setSaving] = useState(false)

  const salvar = async () => {
    if (!form.celular || !form.quantidade) { toast.error('Preencha todos os campos'); return }
    setSaving(true)
    try {
      const { data } = await api.post('/admin/creditar', {
        celular: form.celular,
        quantidade: Number(form.quantidade),
        motivo: form.motivo || 'recarga admin',
      })
      toast.success(`Créditos adicionados! Saldo: ${data.saldo}`)
      setForm({ celular: '', quantidade: '', motivo: '' })
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro')
    } finally { setSaving(false) }
  }

  return (
    <div className="card space-y-3">
      <p className="stat-label">ADICIONAR CRÉDITOS</p>
      <input className="input" placeholder="Celular do apostador"
        value={form.celular} onChange={e => setForm(p => ({ ...p, celular: e.target.value }))} />
      <input className="input" type="number" placeholder="Quantidade"
        value={form.quantidade} onChange={e => setForm(p => ({ ...p, quantidade: e.target.value }))} />
      <input className="input" placeholder="Motivo (opcional)"
        value={form.motivo} onChange={e => setForm(p => ({ ...p, motivo: e.target.value }))} />
      <button onClick={salvar} className="btn-primary w-full" disabled={saving}>
        {saving ? 'Salvando...' : 'ADICIONAR'}
      </button>
    </div>
  )
}

function VencedoresSection() {
  const [grupos, setGrupos] = useState([])
  useEffect(() => {
    api.get('/admin/vencedores').then(r => setGrupos(r.data.grupos))
  }, [])
  return (
    <div className="space-y-3">
      {grupos.map(g => (
        <div key={g.gid} className="card">
          <div className="flex justify-between items-start mb-3">
            <div>
              <p className="font-display text-xl tracking-wider">{g.nome}</p>
              <p className="text-xs font-mono text-[#4a7a5a]">
                R.{g.rodada_inicio} · {g.membros} apostadores
              </p>
            </div>
            <span className={g.vencedores.length > 0 ? 'badge-venc' :
              g.em_andamento ? 'badge-vivo' : 'badge-elim'}>
              {g.vencedores.length > 0 ? 'ENCERRADO' : g.em_andamento ? 'EM ANDAMENTO' : 'SEM VENCEDOR'}
            </span>
          </div>
          {g.vencedores.map(v => (
            <div key={v.uid} className="flex items-center gap-3 p-3 rounded-lg
              bg-yellow-500/10 border border-yellow-500/20 mb-2">
              <Trophy size={18} className="text-yellow-400 flex-shrink-0"/>
              <div>
                <p className="font-bold text-yellow-400">{v.nome}</p>
                <p className="text-xs font-mono text-[#6b9c7c]">
                  {v.percurso.join(' → ')}
                </p>
              </div>
            </div>
          ))}
          {g.em_andamento && g.ativos.map(a => (
            <div key={a.uid} className="flex items-center gap-2 text-sm text-[#6b9c7c] font-mono">
              <span className="text-goal-500">●</span> {a.nome}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

function ApostadoresSection() {
  const [apostadores, setApostadores] = useState([])
  useEffect(() => {
    api.get('/admin/apostadores').then(r => setApostadores(r.data.apostadores))
  }, [])
  return (
    <div className="space-y-2">
      {apostadores.map(a => (
        <div key={a.uid} className="card flex items-center justify-between">
          <div>
            <p className="font-semibold text-sm">{a.nome}</p>
            <p className="text-xs font-mono text-[#4a7a5a]">{a.celular_fmt}</p>
          </div>
          <div className="flex gap-3 text-xs font-mono">
            <span className="text-goal-400">{a.funis_vivos} vivos</span>
            <span className="text-[#4a7a5a]">{a.funis_total} total</span>
            <span className="text-yellow-400">{a.saldo} créditos</span>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Painel principal ─────────────────────────────────────────────────────────

const TABS = [
  { id: 'config',      label: 'Config',     icon: Settings },
  { id: 'rodada',      label: 'Rodada',     icon: Play },
  { id: 'resultado',   label: 'Resultado',  icon: CheckSquare },
  { id: 'apostadores', label: 'Apostadores',icon: Users },
  { id: 'vencedores',  label: 'Vencedores', icon: Trophy },
  { id: 'creditos',    label: 'Créditos',   icon: Coins },
]

export default function AdminPanel() {
  const [tab, setTab] = useState('config')
  const [cfg, setCfg] = useState(null)
  const { logout } = useAuth()
  const nav = useNavigate()

  const carregarCfg = () => {
    api.get('/admin/config').then(r => setCfg(r.data)).catch(() => {})
  }
  useEffect(() => { carregarCfg() }, [])

  const handleLogout = () => { logout(); nav('/login') }

  return (
    <div className="min-h-screen field-bg">
      {/* Header admin */}
      <header className="border-b border-[#1a3d28] bg-pitch-900/90 backdrop-blur sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-yellow-400"/>
            <span className="font-display text-xl text-yellow-400 tracking-widest">
              PAINEL ADMIN
            </span>
          </div>
          <div className="flex items-center gap-3">
            {cfg?.rodada_ativa > 0 && (
              <span className={`text-xs font-mono px-2 py-1 rounded border
                ${cfg.prazo_expirado
                  ? 'border-red-900 text-red-400 bg-red-950/30'
                  : 'border-goal-500/40 text-goal-400 bg-goal-500/5'}`}>
                R.{cfg.rodada_ativa} {cfg.prazo_expirado ? '· EXPIRADO' : '· ABERTA'}
              </span>
            )}
            <button onClick={handleLogout}
              className="flex items-center gap-1 text-[#4a7a5a] hover:text-red-400 transition-colors text-sm">
              <LogOut size={14}/>
            </button>
          </div>
        </div>

        {/* Tab nav */}
        <div className="max-w-4xl mx-auto px-4 flex gap-1 pb-2 overflow-x-auto">
          {TABS.map(t => {
            const Icon = t.icon
            return (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs
                  font-mono whitespace-nowrap transition-colors
                  ${tab === t.id
                    ? 'bg-goal-500/20 text-goal-400 border border-goal-500/30'
                    : 'text-[#4a7a5a] hover:text-goal-400'}`}>
                <Icon size={12}/> {t.label}
              </button>
            )
          })}
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {tab === 'config'      && <ConfigSection cfg={cfg} onRefresh={carregarCfg}/>}
        {tab === 'rodada'      && <AbrirRodadaSection cfg={cfg} onRefresh={carregarCfg}/>}
        {tab === 'resultado'   && <ResultadoSection cfg={cfg} onRefresh={carregarCfg}/>}
        {tab === 'apostadores' && <ApostadoresSection/>}
        {tab === 'vencedores'  && <VencedoresSection/>}
        {tab === 'creditos'    && <CreditarSection/>}
      </main>
    </div>
  )
}
