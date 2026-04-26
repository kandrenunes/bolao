import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../store'
import api from '../api'
import { Trophy, Flame, Target, Coins, ChevronRight, Clock } from 'lucide-react'

function CountdownTimer({ prazo }) {
  const [left, setLeft] = useState('')
  useEffect(() => {
    const tick = () => {
      const diff = new Date(prazo) - new Date()
      if (diff <= 0) { setLeft('Encerrado'); return }
      const h = Math.floor(diff / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      const s = Math.floor((diff % 60000) / 1000)
      setLeft(`${h}h ${m}m ${s}s`)
    }
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [prazo])
  return <span className="font-mono text-yellow-400">{left}</span>
}

export default function Dashboard() {
  const { user } = useAuth()
  const nav = useNavigate()
  const [situacao, setSituacao] = useState(null)
  const [rodadas, setRodadas] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/usuario/situacao'),
      api.get('/rodadas'),
    ]).then(([s, r]) => {
      setSituacao(s.data)
      setRodadas(r.data)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-goal-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  const totalFunis  = situacao?.grupos?.reduce((a, g) => a + g.funis_total, 0) || 0
  const funisVivos  = situacao?.grupos?.reduce((a, g) => a + g.funis_vivos, 0) || 0
  const vencimentos = situacao?.grupos?.filter(g => g.vencedor).length || 0

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="section-title">OLÁ, {user?.nome?.split(' ')[0]?.toUpperCase()}</h2>
        <p className="text-[#4a7a5a] font-mono text-sm mt-1">
          SALDO: <span className="text-goal-400">{situacao?.saldo || 0} CRÉDITO(S)</span>
        </p>
      </div>

      {/* Rodada ativa banner */}
      {rodadas?.rodada_ativa > 0 && (
        <div className={`card border ${rodadas.prazo_expirado
          ? 'border-red-900/50 bg-red-950/20'
          : 'border-goal-500/30 bg-goal-500/5'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">RODADA ATIVA</p>
              <p className="font-display text-4xl text-goal-400 tracking-wider">
                {rodadas.rodada_ativa}
              </p>
            </div>
            <div className="text-right">
              {rodadas.prazo_expirado ? (
                <span className="badge-elim text-sm">PRAZO ENCERRADO</span>
              ) : (
                <>
                  <p className="stat-label flex items-center gap-1 justify-end">
                    <Clock size={10}/> FECHA EM
                  </p>
                  <CountdownTimer prazo={rodadas.prazo} />
                </>
              )}
            </div>
          </div>
          {!rodadas.prazo_expirado && (
            <button onClick={() => nav('/apostas')}
              className="btn-primary w-full mt-4 flex items-center justify-center gap-2">
              FAZER APOSTAS <ChevronRight size={16}/>
            </button>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="stat-box">
          <span className="stat-label flex items-center gap-1"><Target size={10}/>Funis Vivos</span>
          <span className="stat-value text-goal-400">{funisVivos}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label flex items-center gap-1"><Flame size={10}/>Total Funis</span>
          <span className="stat-value">{totalFunis}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label flex items-center gap-1"><Trophy size={10}/>Vitórias</span>
          <span className="stat-value text-yellow-400">{vencimentos}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label flex items-center gap-1"><Coins size={10}/>Créditos</span>
          <span className="stat-value">{situacao?.saldo || 0}</span>
        </div>
      </div>

      {/* Grupos */}
      {situacao?.grupos?.length > 0 ? (
        <div className="space-y-3">
          <h3 className="font-display text-xl text-[#6b9c7c] tracking-wider">MEUS GRUPOS</h3>
          {situacao.grupos.map(g => (
            <div key={g.gid} className="card">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-display text-xl tracking-wider">{g.nome}</p>
                  <p className="text-xs font-mono text-[#4a7a5a]">A partir da R.{g.rodada_inicio}</p>
                </div>
                <div className="flex gap-2">
                  {g.vencedor && <span className="badge-venc">VENCEDOR</span>}
                  {g.eliminado && <span className="badge-elim">ELIMINADO</span>}
                  {!g.vencedor && !g.eliminado && (
                    <span className="badge-vivo">{g.funis_vivos} VIVO(S)</span>
                  )}
                </div>
              </div>

              {/* Funis */}
              <div className="space-y-1">
                {g.funis.map((f, i) => {
                  const ultimo = f.historico?.at(-1)
                  return (
                    <div key={f.id}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                        ${f.vencedor ? 'bg-yellow-500/10 border border-yellow-500/20' :
                          f.eliminado ? 'bg-red-500/5 border border-red-900/20' :
                          'bg-pitch-800/50 border border-[#1a3d28]'}`}>
                      <span className="font-mono text-xs text-[#4a7a5a] w-8">F{i+1}</span>
                      <div className="flex gap-1 flex-wrap flex-1">
                        {f.historico?.map((h, hi) => (
                          <span key={hi}
                            className={`text-xs font-mono px-1.5 py-0.5 rounded
                              ${h.resultado === 'venceu' ? 'text-goal-400 bg-goal-500/10' :
                                h.resultado === 'eliminado' ? 'text-red-400 bg-red-500/10 line-through' :
                                'text-yellow-400 bg-yellow-500/10'}`}>
                            R{h.rodada}:{h.time.slice(0,8)}
                          </span>
                        ))}
                      </div>
                      {f.vencedor && <Trophy size={14} className="text-yellow-400"/>}
                      {f.eliminado && <span className="text-xs text-red-500">✕</span>}
                      {!f.vencedor && !f.eliminado &&
                        <span className="text-xs text-goal-500">●</span>}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <Trophy size={40} className="text-[#1a3d28] mx-auto mb-4"/>
          <p className="text-[#4a7a5a] font-mono">NENHUMA APOSTA AINDA</p>
          <p className="text-xs text-[#2d5a3d] mt-1 font-mono mb-6">
            Aguarde uma rodada aberta para apostar
          </p>
          {rodadas?.aberta_e_valida && (
            <button onClick={() => nav('/apostas')} className="btn-primary">
              FAZER PRIMEIRA APOSTA
            </button>
          )}
        </div>
      )}
    </div>
  )
}
