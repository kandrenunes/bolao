import { useEffect, useState } from 'react'
import api from '../api'
import { Users, Trophy, Target } from 'lucide-react'

export default function Grupos() {
  const [grupos, setGrupos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/grupos').then(r => setGrupos(r.data.grupos)).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-goal-500 border-t-transparent rounded-full animate-spin"/>
    </div>
  )

  return (
    <div className="space-y-6">
      <h2 className="section-title">GRUPOS</h2>

      {grupos.length === 0 ? (
        <div className="card text-center py-16">
          <Users size={40} className="text-[#1a3d28] mx-auto mb-4"/>
          <p className="text-[#4a7a5a] font-mono">NENHUM GRUPO AINDA</p>
        </div>
      ) : grupos.map(g => (
        <div key={g.gid} className="card space-y-4">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <p className="font-display text-2xl tracking-wider">{g.nome}</p>
              <p className="text-xs font-mono text-[#4a7a5a]">
                Rodada {g.rodada_inicio} · {g.membros_total} apostador(es)
              </p>
            </div>
            <div className="text-right space-y-1">
              <div className="flex gap-2 justify-end">
                <span className={`badge-vivo`}>
                  {g.funis_vivos}/{g.funis_total} vivos
                </span>
                {g.vagas > 0 && (
                  <span className="text-xs font-mono px-2 py-0.5 rounded-full
                    bg-[#1a3d28] text-[#4a7a5a]">
                    {g.vagas} vagas
                  </span>
                )}
                {g.lotado && (
                  <span className="text-xs font-mono px-2 py-0.5 rounded-full
                    bg-red-900/30 text-red-400 border border-red-900/40">
                    LOTADO
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Barra de progresso dos funis */}
          <div>
            <div className="flex justify-between text-[10px] font-mono text-[#4a7a5a] mb-1">
              <span>FUNIS</span>
              <span>{g.funis_vivos} VIVOS</span>
            </div>
            <div className="h-1.5 bg-[#0a1a10] rounded-full overflow-hidden">
              <div
                className="h-full bg-goal-500 rounded-full transition-all"
                style={{ width: g.funis_total > 0 ? `${(g.funis_vivos / g.funis_total) * 100}%` : '0%' }}
              />
            </div>
          </div>

          {/* Apostadores */}
          <div className="space-y-2">
            {g.apostadores.map(a => (
              <div key={a.uid}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg
                  ${a.vencedor ? 'bg-yellow-500/10 border border-yellow-500/20' :
                    a.eliminado ? 'bg-red-500/5 border border-red-900/20 opacity-60' :
                    'bg-pitch-800/60 border border-[#1a3d28]'}`}>
                <div className="flex items-center gap-3">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold
                    ${a.vencedor ? 'bg-yellow-500/20 text-yellow-400' :
                      a.eliminado ? 'bg-red-500/10 text-red-500' :
                      'bg-goal-500/10 text-goal-400'}`}>
                    {a.nome.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{a.nome}</p>
                    {a.times_ativos?.length > 0 && (
                      <p className="text-xs font-mono text-[#4a7a5a]">
                        {a.times_ativos.join(', ')}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {a.vencedor && <Trophy size={14} className="text-yellow-400"/>}
                  {a.eliminado && <span className="badge-elim text-xs">ELIM</span>}
                  {!a.vencedor && !a.eliminado && (
                    <span className="badge-vivo">
                      {a.funis_vivos}/{a.funis_total}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
