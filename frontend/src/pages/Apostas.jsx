import { useEffect, useState } from 'react'
import api from '../api'
import toast from 'react-hot-toast'
import { Layers, Plus, Pencil, ChevronRight, X, Check } from 'lucide-react'

function TimePicker({ jogos, usados, onSelect, multi = false }) {
  const [selecionados, setSel] = useState([])
  const n = jogos.length
  const mapa = {}
  jogos.forEach((j, i) => {
    mapa[i + 1]     = j.casa
    mapa[i + 1 + n] = j.visit
  })

  const toggle = cod => {
    if (!multi) { onSelect([cod]); return }
    setSel(prev =>
      prev.includes(cod) ? prev.filter(c => c !== cod) : [...prev, cod]
    )
  }

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-1 gap-2">
        {jogos.map((j, i) => {
          const codCasa  = i + 1
          const codVisit = i + 1 + n
          return (
            <div key={i} className="grid grid-cols-2 gap-2">
              {[
                { cod: codCasa,  time: j.casa,  label: 'CASA' },
                { cod: codVisit, time: j.visit, label: 'VISIT' },
              ].map(({ cod, time, label }) => {
                const usado = usados?.includes(time)
                const sel   = multi ? selecionados.includes(cod) : false
                return (
                  <button key={cod} disabled={usado}
                    onClick={() => toggle(cod)}
                    className={`p-3 rounded-lg border text-left transition-all
                      ${usado
                        ? 'border-[#0f2318] bg-[#0a1a10] opacity-40 cursor-not-allowed'
                        : sel
                        ? 'border-goal-500 bg-goal-500/20 text-goal-400'
                        : 'border-[#1a3d28] hover:border-goal-500/50 hover:bg-pitch-800'
                      }`}>
                    <p className="text-[10px] font-mono text-[#4a7a5a] mb-0.5">{label}</p>
                    <p className="text-sm font-bold leading-tight">{time}</p>
                    {usado && <p className="text-[9px] font-mono text-red-500 mt-0.5">JÁ USADO</p>}
                  </button>
                )
              })}
            </div>
          )
        })}
      </div>
      {multi && selecionados.length > 0 && (
        <button onClick={() => onSelect(selecionados)}
          className="btn-primary w-full flex items-center justify-center gap-2">
          <Check size={16}/> CONFIRMAR {selecionados.length} TIME(S)
        </button>
      )}
    </div>
  )
}

export default function Apostas() {
  const [rodadas, setRodadas]   = useState(null)
  const [rodada,  setRodada]    = useState(null)
  const [status,  setStatus]    = useState(null)
  const [jogos,   setJogos]     = useState([])
  const [saldo,   setSaldo]     = useState(0)
  const [modo,    setModo]      = useState(null) // 'continuar' | 'nova' | 'alterar'
  const [funilAlvo, setFunilAlvo] = useState(null)
  const [loading, setLoading]   = useState(true)
  const [saving,  setSaving]    = useState(false)

  const carregar = async () => {
    try {
      const [ri, rs, rm] = await Promise.all([
        api.get('/rodadas'),
        api.get('/apostas/rodada-ativa'),
        api.get('/usuario/me'),
      ])
      setRodadas(ri.data)
      setStatus(rs.data)
      setSaldo(rm.data.saldo)
      if (ri.data.rodada_ativa) {
        const rj = await api.get(`/rodadas/${ri.data.rodada_ativa}`)
        setRodada(rj.data)
        setJogos(rj.data.jogos.filter(j => j.confirmado))
      }
    } catch {}
    setLoading(false)
  }

  useEffect(() => { carregar() }, [])

  const novaEntrada = async codigos => {
    setSaving(true)
    try {
      const { data } = await api.post('/apostas/nova-entrada', { codigos })
      toast.success(`${data.funis.length} funil(is) criado(s) no ${data.grupo.nome}!`)
      setModo(null)
      await carregar()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao apostar')
    } finally { setSaving(false) }
  }

  const continuarFunil = async (fid, codigos) => {
    setSaving(true)
    try {
      await api.post('/apostas/continuar-funil', { fid, codigo: codigos[0] })
      toast.success('Aposta registrada!')
      setModo(null); setFunilAlvo(null)
      await carregar()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao apostar')
    } finally { setSaving(false) }
  }

  const alterarAposta = async (fid, codigos) => {
    setSaving(true)
    try {
      const { data } = await api.put('/apostas/alterar', { fid, codigo: codigos[0] })
      toast.success(`Alterado: ${data.time_anterior} → ${data.time_novo}`)
      setModo(null); setFunilAlvo(null)
      await carregar()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao alterar')
    } finally { setSaving(false) }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-goal-500 border-t-transparent rounded-full animate-spin"/>
    </div>
  )

  if (!rodadas?.rodada_ativa) return (
    <div className="card text-center py-16">
      <Layers size={40} className="text-[#1a3d28] mx-auto mb-4"/>
      <p className="text-[#4a7a5a] font-mono">NENHUMA RODADA ABERTA</p>
      <p className="text-xs text-[#2d5a3d] font-mono mt-1">Aguarde o administrador abrir a próxima rodada</p>
    </div>
  )

  if (rodadas?.prazo_expirado) return (
    <div className="card text-center py-16">
      <p className="text-red-400 font-mono font-bold">PRAZO ENCERRADO</p>
      <p className="text-xs text-[#4a7a5a] font-mono mt-2">Apostas da Rodada {rodadas.rodada_ativa} encerradas</p>
    </div>
  )

  const { funis_sem_aposta = [], funis_apostados = [] } = status || {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="section-title">RODADA {rodadas.rodada_ativa}</h2>
          <p className="text-xs font-mono text-[#4a7a5a] mt-0.5">
            {jogos.length} jogos · Créditos: <span className="text-goal-400">{saldo}</span>
          </p>
        </div>
        {modo && (
          <button onClick={() => { setModo(null); setFunilAlvo(null) }}
            className="btn-ghost flex items-center gap-1 py-2 px-3 text-sm">
            <X size={14}/> Cancelar
          </button>
        )}
      </div>

      {/* ── MODO: Continuar funil ── */}
      {modo === 'continuar' && funilAlvo && (
        <div className="card border border-goal-500/30">
          <p className="stat-label mb-1">FUNIL A CONTINUAR</p>
          <p className="font-display text-lg tracking-wider mb-3">
            {funilAlvo.id.split('_').slice(0,2).join(' ').toUpperCase()}
          </p>
          <div className="flex gap-1 flex-wrap mb-4">
            {funilAlvo.historico?.map((h, i) => (
              <span key={i} className={`text-xs font-mono px-2 py-0.5 rounded
                ${h.resultado === 'venceu' ? 'bg-goal-500/10 text-goal-400' : 'bg-red-500/10 text-red-400'}`}>
                R{h.rodada}: {h.time}
              </span>
            ))}
          </div>
          <p className="text-xs text-[#4a7a5a] font-mono mb-3">
            Escolha 1 time · Gratuito (entrada já paga)
          </p>
          <TimePicker jogos={jogos} usados={funilAlvo.times_usados}
            onSelect={cods => continuarFunil(funilAlvo.id, cods)} />
        </div>
      )}

      {/* ── MODO: Alterar aposta ── */}
      {modo === 'alterar' && funilAlvo && (
        <div className="card border border-yellow-500/30">
          <p className="stat-label mb-1">ALTERAR APOSTA</p>
          <p className="font-mono text-sm text-yellow-400 mb-3">
            Atual: <strong>{funilAlvo.time_atual}</strong>
          </p>
          <p className="text-xs text-[#4a7a5a] font-mono mb-3">
            Escolha o novo time · Gratuito
          </p>
          <TimePicker jogos={jogos} usados={funilAlvo.times_usados?.filter(t => t !== funilAlvo.time_atual)}
            onSelect={cods => alterarAposta(funilAlvo.id, cods)} />
        </div>
      )}

      {/* ── MODO: Nova entrada ── */}
      {modo === 'nova' && (
        <div className="card border border-goal-500/30">
          <p className="stat-label mb-1">NOVA ENTRADA</p>
          <p className="text-xs text-[#4a7a5a] font-mono mb-1">
            Cada time = 1 funil = 1 crédito · Saldo: <span className="text-goal-400">{saldo}</span>
          </p>
          <p className="text-xs text-[#2d5a3d] font-mono mb-4">
            Selecione os times e confirme
          </p>
          <TimePicker jogos={jogos} usados={[]} multi onSelect={novaEntrada} />
        </div>
      )}

      {/* ── Funis aguardando aposta ── */}
      {!modo && funis_sem_aposta.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-display text-lg text-[#6b9c7c] tracking-wider">
            FUNIS AGUARDANDO ({funis_sem_aposta.length})
          </h3>
          {funis_sem_aposta.map(f => {
            const num = f.id.split('_').at(-1)
            const ultimo = f.historico?.at(-1)
            return (
              <div key={f.id} className="card flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold">Funil {num}</p>
                  {ultimo && (
                    <p className="text-xs font-mono text-[#4a7a5a]">
                      Último: {ultimo.time} (R{ultimo.rodada})
                    </p>
                  )}
                </div>
                <button
                  onClick={() => { setFunilAlvo(f); setModo('continuar') }}
                  className="btn-primary py-2 px-4 text-sm flex items-center gap-1">
                  APOSTAR <ChevronRight size={14}/>
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* ── Funis já apostados ── */}
      {!modo && funis_apostados.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-display text-lg text-[#6b9c7c] tracking-wider">
            JÁ APOSTADOS ({funis_apostados.length})
          </h3>
          {funis_apostados.map(f => {
            const num = f.id.split('_').at(-1)
            return (
              <div key={f.id} className="card flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold">Funil {num}</p>
                  <p className="text-xs font-mono text-goal-400">{f.time}</p>
                </div>
                <button
                  onClick={() => { setFunilAlvo({ ...f, time_atual: f.time }); setModo('alterar') }}
                  className="btn-ghost py-2 px-3 text-sm flex items-center gap-1">
                  <Pencil size={13}/> ALTERAR
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* ── Botão nova entrada ── */}
      {!modo && (
        <button onClick={() => setModo('nova')}
          className="btn-ghost w-full flex items-center justify-center gap-2">
          <Plus size={16}/> NOVA ENTRADA (1 CRÉDITO/FUNIL)
        </button>
      )}
    </div>
  )
}
