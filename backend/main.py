"""main.py — FastAPI Bolao Survivor"""

import os, hashlib, re
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from backend.core import *
from backend.auth import (
    hash_senha, verificar_senha, criar_token,
    get_usuario_atual, get_admin_atual, SENHA_ADMIN as SENHA_ADMIN_ENV
)

# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(title="Bolao Survivor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    garantir_pasta_dados()
    # Carrega jogos na inicialização
    app.state.rodadas = carregar_jogos(ARQ_JOGOS)
    app.state.times   = listar_times(app.state.rodadas)


# ── Schemas ──────────────────────────────────────────────────────────────────
class LoginReq(BaseModel):
    celular: str
    senha: str

class CadastroReq(BaseModel):
    nome: str
    celular: str
    senha: str
    whatsapp: bool = False
    email: str = ""
    cpf: str = ""
    pix: str = ""
    time_coracao: str = ""

class ApostaReq(BaseModel):
    codigos: List[int]          # códigos dos times (índice no mapa de jogos)

class ApostaFunilReq(BaseModel):
    fid: str
    codigo: int                 # 1 time por funil

class AlterarApostaReq(BaseModel):
    fid: str
    codigo: int

class ResultadoJogoReq(BaseModel):
    jogo_idx: int               # índice do jogo (1-based)
    vencedor: Optional[str]     # None = empate

class AbrirRodadaReq(BaseModel):
    jogos_confirmados: List[int]
    prazo: str                  # "DD/MM/AAAA HH:MM"

class CreditarReq(BaseModel):
    celular: str
    quantidade: int
    motivo: str = "recarga admin"

class ConfigReq(BaseModel):
    rodada_inicial: int


# ── Helpers ──────────────────────────────────────────────────────────────────
def _mapa_jogos(num_rodada: int):
    rodadas = app.state.rodadas
    jogos   = rodadas.get(num_rodada, [])
    n       = len(jogos)
    mapa    = {}
    for i, (casa, visit) in enumerate(jogos, 1):
        mapa[i]     = casa
        mapa[i + n] = visit
    return mapa, jogos


def _usuario_ou_404(uid: str) -> dict:
    u = carregar_json(ARQ_USUARIOS, {}).get(uid)
    if not u:
        raise HTTPException(404, "Usuario nao encontrado")
    return u


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/auth/cadastro")
def cadastro(req: CadastroReq):
    cel = re.sub(r"\D", "", req.celular)
    if len(cel) < 10:
        raise HTTPException(400, "Celular invalido")
    usuarios = carregar_json(ARQ_USUARIOS, {})
    if cel in usuarios:
        raise HTTPException(409, "Celular ja cadastrado")
    pix = req.pix or cel
    usuarios[cel] = {
        "nome": req.nome, "celular": cel,
        "celular_fmt": f"({cel[:2]}) {cel[2:7]}-{cel[7:]}",
        "whatsapp": req.whatsapp, "email": req.email,
        "cpf": re.sub(r"\D", "", req.cpf),
        "pix": pix, "senha": hash_senha(req.senha),
        "time_coracao": req.time_coracao, "grupos": [],
        "cadastro_em": datetime.now().isoformat(timespec="seconds"),
    }
    salvar_json(ARQ_USUARIOS, usuarios)
    token = criar_token({"sub": cel, "role": "user"})
    return {"token": token, "uid": cel, "nome": req.nome}


@app.post("/api/auth/login")
def login(req: LoginReq):
    # Trata admin ANTES do re.sub
    if req.celular == "admin":
        if req.senha != SENHA_ADMIN_ENV:
            raise HTTPException(401, "Senha incorreta")
        token = criar_token({"sub": "admin", "role": "admin"})
        return {
            "token": token,
            "uid": "admin",
            "nome": "Admin",
            "role": "admin"
        }

    # Fluxo normal de usuário
    cel = re.sub(r"\D", "", req.celular)

    usuarios = carregar_json(ARQ_USUARIOS, {})
    u = usuarios.get(cel)

    if not u:
        raise HTTPException(404, "Usuario nao encontrado")

    if not verificar_senha(req.senha, u["senha"]):
        raise HTTPException(401, "Senha incorreta")

    token = criar_token({"sub": cel, "role": "user"})
    return {
        "token": token,
        "uid": cel,
        "nome": u["nome"],
        "role": "user"
    }


# ══════════════════════════════════════════════════════════════════════════════
# USUÁRIO
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/usuario/me")
def get_me(atual=Depends(get_usuario_atual)):
    uid = atual["uid"]
    if uid == "admin":
        return {"uid": "admin", "nome": "Admin", "role": "admin"}
    u = _usuario_ou_404(uid)
    return {
        "uid": uid,
        "nome": u["nome"],
        "celular_fmt": u.get("celular_fmt", uid),
        "email": u.get("email", ""),
        "pix": u.get("pix", ""),
        "time_coracao": u.get("time_coracao", ""),
        "grupos": u.get("grupos", []),
        "saldo": saldo_creditos(uid),
        "role": "user",
    }


@app.get("/api/usuario/situacao")
def get_situacao(atual=Depends(get_usuario_atual)):
    uid = atual["uid"]
    u   = _usuario_ou_404(uid)
    grupos_uid = u.get("grupos", [])
    grupos_info = carregar_grupos()
    resultado = []
    for gid in grupos_uid:
        g       = grupos_info.get(gid, {})
        funis   = funis_do_usuario(uid, gid)
        f_vivos = [f for f in funis if not f["eliminado"]]
        f_venc  = [f for f in funis if f.get("vencedor")]
        resultado.append({
            "gid": gid,
            "nome": g.get("nome", f"Grupo {gid}"),
            "rodada_inicio": g.get("rodada_inicial_grupo"),
            "funis_total": len(funis),
            "funis_vivos": len(f_vivos),
            "vencedor": len(f_venc) > 0,
            "eliminado": len(funis) > 0 and len(f_vivos) == 0 and len(f_venc) == 0,
            "funis": [
                {
                    "id": f["id"],
                    "eliminado": f["eliminado"],
                    "vencedor": f.get("vencedor", False),
                    "historico": f.get("historico", []),
                    "times_usados": f.get("times_usados", []),
                }
                for f in funis
            ],
        })
    return {
        "uid": uid,
        "nome": u["nome"],
        "saldo": saldo_creditos(uid),
        "grupos": resultado,
    }


# ══════════════════════════════════════════════════════════════════════════════
# RODADAS E JOGOS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/rodadas")
def get_rodadas():
    cfg        = carregar_config()
    rodadas    = app.state.rodadas
    resultados = carregar_json(ARQ_RESULTADOS, {})
    r_ini      = cfg.get("rodada_inicial", 1)
    r_at       = cfg.get("rodada_ativa", 0)
    total      = cfg.get("total_rodadas", max(rodadas.keys()))
    return {
        "rodada_inicial": r_ini,
        "rodada_ativa": r_at,
        "total_rodadas": total,
        "prazo": cfg.get("prazo_apostas", ""),
        "prazo_expirado": prazo_expirado(),
        "jogos_confirmados": cfg.get("jogos_confirmados", []),
        "rodadas_com_resultado": [int(r) for r in resultados],
        "aberta_e_valida": rodada_aberta_e_valida(),
    }


@app.get("/api/rodadas/{num}")
def get_rodada(num: int):
    rodadas    = app.state.rodadas
    resultados = carregar_json(ARQ_RESULTADOS, {})
    if num not in rodadas:
        raise HTTPException(404, "Rodada nao encontrada")
    cfg = carregar_config()
    idx_conf = cfg.get("jogos_confirmados", []) if cfg.get("rodada_ativa") == num else []
    jogos_raw = rodadas[num]
    jogos = []
    for i, (casa, visit) in enumerate(jogos_raw, 1):
        confirmado = (i in idx_conf) if idx_conf else True
        jogos.append({"idx": i, "casa": casa, "visit": visit, "confirmado": confirmado})
    resultado = resultados.get(str(num))
    return {
        "rodada": num,
        "jogos": jogos,
        "resultado": resultado,
        "aberta": cfg.get("rodada_ativa") == num,
        "prazo": cfg.get("prazo_apostas", "") if cfg.get("rodada_ativa") == num else "",
    }


@app.get("/api/times")
def get_times():
    return {"times": app.state.times}


# ══════════════════════════════════════════════════════════════════════════════
# APOSTAS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/apostas/rodada-ativa")
def get_apostas_rodada_ativa(atual=Depends(get_usuario_atual)):
    uid     = atual["uid"]
    cfg     = carregar_config()
    r_at    = cfg.get("rodada_ativa", 0)
    if not r_at:
        return {"rodada": None, "funis_sem_aposta": [], "funis_apostados": []}
    apostas  = carregar_json(ARQ_APOSTAS, {})
    f_vivos  = funis_vivos_usuario(uid)
    sem_aposta = []
    apostados  = []
    for f in f_vivos:
        chave = f"{uid}_{f['gid']}_{r_at}_{f['id']}"
        if chave in apostas:
            ap = apostas[chave]
            apostados.append({
                "fid": f["id"], "gid": f["gid"],
                "time": ap["time"], "chave": chave,
                "times_usados": f.get("times_usados", []),
            })
        else:
            sem_aposta.append({
                "fid": f["id"], "gid": f["gid"],
                "historico": f.get("historico", []),
                "times_usados": f.get("times_usados", []),
            })
    return {"rodada": r_at, "funis_sem_aposta": sem_aposta, "funis_apostados": apostados}


@app.post("/api/apostas/nova-entrada")
def nova_entrada(req: ApostaReq, atual=Depends(get_usuario_atual)):
    """Cria novos funis (entrada no grupo). Debita créditos."""
    uid = atual["uid"]
    if not rodada_aberta_e_valida():
        raise HTTPException(400, "Sem rodada aberta para apostas ou prazo encerrado")

    cfg     = carregar_config()
    r_at    = cfg.get("rodada_ativa")
    mapa, _ = _mapa_jogos(r_at)

    times_escolhidos = []
    for cod in req.codigos:
        if cod not in mapa:
            raise HTTPException(400, f"Codigo invalido: {cod}")
        times_escolhidos.append(mapa[cod])

    if len(times_escolhidos) != len(set(times_escolhidos)):
        raise HTTPException(400, "Times duplicados na aposta")

    qtd = len(times_escolhidos)
    if saldo_creditos(uid) < qtd:
        raise HTTPException(400, f"Saldo insuficiente. Necessario: {qtd}, disponivel: {saldo_creditos(uid)}")

    gid = alocar_grupo_com_vagas(uid, qtd)
    if not gid:
        raise HTTPException(400, "Sem grupo disponivel para esta quantidade de apostas")

    usuarios = carregar_json(ARQ_USUARIOS, {})
    if gid not in usuarios[uid].get("grupos", []):
        usuarios[uid].setdefault("grupos", []).append(gid)
        salvar_json(ARQ_USUARIOS, usuarios)

    apostas = carregar_json(ARQ_APOSTAS, {})
    funis_criados = []
    for t in times_escolhidos:
        fid   = criar_funil(uid, gid, r_at, t)
        chave = f"{uid}_{gid}_{r_at}_{fid}"
        apostas[chave] = {
            "uid": uid, "gid": gid, "fid": fid,
            "rodada": r_at, "time": t,
            "apostado_em": datetime.now().isoformat(timespec="seconds"),
            "automatica": False,
        }
        funis_criados.append({"fid": fid, "time": t})

    salvar_json(ARQ_APOSTAS, apostas)
    debitar_creditos_multiplos(uid, qtd, motivo=f"entrada Grupo {gid} — {qtd} funis")

    g = carregar_grupos().get(gid, {})
    return {
        "ok": True,
        "grupo": {"gid": gid, "nome": g.get("nome", f"Grupo {gid}")},
        "funis": funis_criados,
        "creditos_debitados": qtd,
        "saldo": saldo_creditos(uid),
    }


@app.post("/api/apostas/continuar-funil")
def continuar_funil(req: ApostaFunilReq, atual=Depends(get_usuario_atual)):
    """Aposta em funil vivo existente. Gratuito."""
    uid = atual["uid"]
    if not rodada_aberta_e_valida():
        raise HTTPException(400, "Sem rodada aberta para apostas ou prazo encerrado")

    cfg  = carregar_config()
    r_at = cfg.get("rodada_ativa")
    funis_d = carregar_funis()
    f    = funis_d.get(req.fid)

    if not f or f["uid"] != uid:
        raise HTTPException(404, "Funil nao encontrado")
    if f["eliminado"]:
        raise HTTPException(400, "Funil eliminado")

    mapa, _ = _mapa_jogos(r_at)
    if req.codigo not in mapa:
        raise HTTPException(400, "Codigo invalido")

    time_escolhido = mapa[req.codigo]
    ja_usados = set(f.get("times_usados", []))
    if time_escolhido in ja_usados:
        raise HTTPException(400, f"Time '{time_escolhido}' ja usado neste funil")

    gid   = f["gid"]
    chave = f"{uid}_{gid}_{r_at}_{req.fid}"
    apostas = carregar_json(ARQ_APOSTAS, {})
    apostas[chave] = {
        "uid": uid, "gid": gid, "fid": req.fid,
        "rodada": r_at, "time": time_escolhido,
        "apostado_em": datetime.now().isoformat(timespec="seconds"),
        "automatica": False,
    }
    salvar_json(ARQ_APOSTAS, apostas)
    return {"ok": True, "fid": req.fid, "time": time_escolhido}


@app.put("/api/apostas/alterar")
def alterar_aposta(req: AlterarApostaReq, atual=Depends(get_usuario_atual)):
    """Altera aposta já feita. Só dentro do prazo."""
    uid = atual["uid"]
    if not rodada_aberta_e_valida():
        raise HTTPException(400, "Prazo encerrado — nao e possivel alterar apostas")

    cfg  = carregar_config()
    r_at = cfg.get("rodada_ativa")
    funis_d = carregar_funis()
    f    = funis_d.get(req.fid)

    if not f or f["uid"] != uid:
        raise HTTPException(404, "Funil nao encontrado")

    mapa, _ = _mapa_jogos(r_at)
    if req.codigo not in mapa:
        raise HTTPException(400, "Codigo invalido")

    novo_time = mapa[req.codigo]
    gid   = f["gid"]
    chave = f"{uid}_{gid}_{r_at}_{req.fid}"
    apostas = carregar_json(ARQ_APOSTAS, {})
    ap_atual = apostas.get(chave)

    if not ap_atual:
        raise HTTPException(404, "Aposta nao encontrada para este funil nesta rodada")

    time_atual = ap_atual["time"]
    ja_usados_anteriores = {t for t in f.get("times_usados", []) if t != time_atual}
    if novo_time in ja_usados_anteriores:
        raise HTTPException(400, f"Time '{novo_time}' ja usado em rodada anterior deste funil")

    apostas[chave]["time"] = novo_time
    apostas[chave]["apostado_em"] = datetime.now().isoformat(timespec="seconds")
    apostas[chave]["automatica"] = False
    salvar_json(ARQ_APOSTAS, apostas)
    return {"ok": True, "fid": req.fid, "time_anterior": time_atual, "time_novo": novo_time}


# ══════════════════════════════════════════════════════════════════════════════
# GRUPOS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/grupos")
def get_grupos(atual=Depends(get_usuario_atual)):
    grupos   = carregar_grupos()
    usuarios = carregar_json(ARQ_USUARIOS, {})
    resultado = []
    for gid in sorted(grupos.keys(), key=int):
        g        = grupos[gid]
        membros  = g.get("membros", [])
        f_grp    = funis_do_grupo(gid)
        f_vivos  = funis_vivos_grupo(gid)
        usadas   = len(f_grp)
        apostadores = []
        for uid_m in membros:
            nome_m   = usuarios.get(uid_m, {}).get("nome", uid_m)
            f_uid    = funis_do_usuario(uid_m, gid)
            f_v      = [f for f in f_uid if not f["eliminado"]]
            f_vc     = [f for f in f_uid if f.get("vencedor")]
            times_vivos = [
                f["historico"][-1]["time"] if f.get("historico") else "?"
                for f in f_v
            ]
            apostadores.append({
                "uid": uid_m, "nome": nome_m,
                "funis_total": len(f_uid),
                "funis_vivos": len(f_v),
                "vencedor": len(f_vc) > 0,
                "eliminado": len(f_uid) > 0 and len(f_v) == 0 and len(f_vc) == 0,
                "times_ativos": times_vivos,
            })
        resultado.append({
            "gid": gid,
            "nome": g.get("nome"),
            "rodada_inicio": g.get("rodada_inicial_grupo"),
            "membros_total": len(membros),
            "funis_total": usadas,
            "funis_vivos": len(f_vivos),
            "vagas": max(0, LIMITE_GRUPO - usadas),
            "lotado": usadas >= LIMITE_GRUPO,
            "apostadores": apostadores,
        })
    return {"grupos": resultado}


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/admin/config")
def admin_get_config(admin=Depends(get_admin_atual)):
    cfg        = carregar_config()
    rodadas    = app.state.rodadas
    resultados = carregar_json(ARQ_RESULTADOS, {})
    r_ini      = cfg.get("rodada_inicial", 0)
    total      = cfg.get("total_rodadas", max(rodadas.keys()) if rodadas else 38)
    # Próxima rodada a abrir
    proxima = None
    if r_ini:
        r_at = cfg.get("rodada_ativa", 0)
        for r in range(r_ini, total + 1):
            if str(r) not in resultados and r != r_at:
                proxima = r
                break
    return {
        **cfg,
        "proxima_rodada": proxima,
        "total_rodadas": total,
        "prazo_expirado": prazo_expirado(),
    }


@app.post("/api/admin/config")
def admin_set_config(req: ConfigReq, admin=Depends(get_admin_atual)):
    if config_definida():
        raise HTTPException(400, "Configuracao ja definida e nao pode ser alterada")
    rodadas = app.state.rodadas
    total   = max(rodadas.keys())
    if req.rodada_inicial < 1 or req.rodada_inicial > total:
        raise HTTPException(400, f"Rodada inicial deve ser entre 1 e {total}")
    cfg = carregar_config()
    cfg.update({
        "rodada_inicial": req.rodada_inicial,
        "total_rodadas": total,
        "configurado_em": datetime.now().isoformat(timespec="seconds"),
    })
    salvar_config(cfg)
    return {"ok": True, "rodada_inicial": req.rodada_inicial}


@app.post("/api/admin/abrir-rodada")
def admin_abrir_rodada_api(req: AbrirRodadaReq, admin=Depends(get_admin_atual)):
    cfg        = carregar_config()
    r_ini      = cfg.get("rodada_inicial", 1)
    rodadas    = app.state.rodadas
    resultados = carregar_json(ARQ_RESULTADOS, {})
    total      = cfg.get("total_rodadas", max(rodadas.keys()))

    # Determina a próxima rodada automaticamente
    r_at = cfg.get("rodada_ativa", 0)
    proxima = None
    for r in range(r_ini, total + 1):
        if str(r) not in resultados and r != r_at:
            proxima = r
            break

    if proxima is None:
        raise HTTPException(400, "Todas as rodadas ja foram processadas")

    if not req.jogos_confirmados:
        raise HTTPException(400, "Pelo menos 1 jogo deve ser confirmado")

    try:
        prazo_dt = datetime.strptime(req.prazo, "%d/%m/%Y %H:%M")
        if prazo_dt <= datetime.now():
            raise HTTPException(400, "O prazo deve ser no futuro")
        prazo_iso = prazo_dt.isoformat(timespec="seconds")
    except ValueError:
        raise HTTPException(400, "Formato de prazo invalido. Use DD/MM/AAAA HH:MM")

    cfg["rodada_ativa"]      = proxima
    cfg["prazo_apostas"]     = prazo_iso
    cfg["jogos_confirmados"] = req.jogos_confirmados
    cfg["aberta_em"]         = datetime.now().isoformat(timespec="seconds")
    salvar_config(cfg)

    jogos_raw  = rodadas[proxima]
    jogos_conf = [
        {"idx": i, "casa": jogos_raw[i-1][0], "visit": jogos_raw[i-1][1]}
        for i in req.jogos_confirmados if 1 <= i <= len(jogos_raw)
    ]
    return {"ok": True, "rodada": proxima, "prazo": req.prazo, "jogos": jogos_conf}


@app.post("/api/admin/resultado")
def admin_inserir_resultado_api(resultados_jogos: List[ResultadoJogoReq],
                                admin=Depends(get_admin_atual)):
    cfg  = carregar_config()
    r_at = cfg.get("rodada_ativa", 0)

    if not r_at:
        raise HTTPException(400, "Nenhuma rodada ativa")
    if not prazo_expirado():
        raise HTTPException(400, "Prazo ainda nao encerrou")

    resultados = carregar_json(ARQ_RESULTADOS, {})
    if str(r_at) in resultados:
        raise HTTPException(400, "Resultado desta rodada ja foi inserido")

    rodadas   = app.state.rodadas
    vencedores = []
    for rj in resultados_jogos:
        if rj.vencedor:
            jogos_raw = rodadas.get(r_at, [])
            if 1 <= rj.jogo_idx <= len(jogos_raw):
                vencedores.append(rj.vencedor)

    resultados[str(r_at)] = {
        "rodada": r_at,
        "vencedores": vencedores,
        "inserido_em": datetime.now().isoformat(timespec="seconds"),
    }
    salvar_json(ARQ_RESULTADOS, resultados)

    # Apostas automáticas
    rel_auto = gerar_apostas_automaticas(r_at, rodadas)

    # Eliminações
    grupos   = carregar_grupos()
    rels     = {}
    for gid in sorted(grupos.keys(), key=int):
        rels[gid] = processar_eliminacao(gid, r_at)

    # Fecha rodada
    cfg["rodada_ativa"]      = 0
    cfg["prazo_apostas"]     = ""
    cfg["jogos_confirmados"] = []
    cfg["fechada_em"]        = datetime.now().isoformat(timespec="seconds")
    salvar_config(cfg)

    return {
        "ok": True,
        "rodada": r_at,
        "vencedores": vencedores,
        "apostas_automaticas": len([r for r in rel_auto if r.get("gerada")]),
        "grupos_processados": len(rels),
    }


@app.get("/api/admin/apostadores")
def admin_apostadores(admin=Depends(get_admin_atual)):
    usuarios = carregar_json(ARQ_USUARIOS, {})
    result   = []
    for uid, u in usuarios.items():
        grupos_uid = u.get("grupos", [])
        f_todos  = funis_do_usuario(uid)
        f_vivos  = [f for f in f_todos if not f["eliminado"]]
        f_venc   = [f for f in f_todos if f.get("vencedor")]
        result.append({
            "uid": uid,
            "nome": u["nome"],
            "celular_fmt": u.get("celular_fmt", uid),
            "grupos": grupos_uid,
            "saldo": saldo_creditos(uid),
            "funis_total": len(f_todos),
            "funis_vivos": len(f_vivos),
            "vencedor": len(f_venc) > 0,
        })
    return {"apostadores": result}


@app.get("/api/admin/vencedores")
def admin_vencedores(admin=Depends(get_admin_atual)):
    grupos   = carregar_grupos()
    usuarios = carregar_json(ARQ_USUARIOS, {})
    resultado = []
    for gid in sorted(grupos.keys(), key=int):
        g     = grupos[gid]
        f_grp = funis_do_grupo(gid)
        f_viv = funis_vivos_grupo(gid)
        venc  = [f for f in f_grp if f.get("vencedor")]
        uids_vencedores = list(dict.fromkeys(f["uid"] for f in venc))
        uids_vivos      = list(dict.fromkeys(f["uid"] for f in f_viv))
        resultado.append({
            "gid": gid,
            "nome": g.get("nome"),
            "rodada_inicio": g.get("rodada_inicial_grupo"),
            "membros": len(g.get("membros", [])),
            "em_andamento": len(f_viv) > 0 and len(venc) == 0,
            "encerrado": len(f_grp) > 0 and len(f_viv) == 0 and len(venc) == 0,
            "vencedores": [
                {
                    "uid": uid,
                    "nome": usuarios.get(uid, {}).get("nome", uid),
                    "percurso": [
                        h["time"] for h in
                        next(f for f in venc if f["uid"] == uid).get("historico", [])
                    ],
                }
                for uid in uids_vencedores
            ],
            "ativos": [
                {"uid": uid, "nome": usuarios.get(uid, {}).get("nome", uid)}
                for uid in uids_vivos
            ],
        })
    return {"grupos": resultado}


@app.post("/api/admin/creditar")
def admin_creditar(req: CreditarReq, admin=Depends(get_admin_atual)):
    cel = re.sub(r"\D", "", req.celular)
    u   = carregar_json(ARQ_USUARIOS, {}).get(cel)
    if not u:
        raise HTTPException(404, "Usuario nao encontrado")
    creditar(cel, req.quantidade, req.motivo)
    return {"ok": True, "uid": cel, "saldo": saldo_creditos(cel)}


@app.get("/api/admin/apostas/{num_rodada}")
def admin_apostas_rodada(num_rodada: int, admin=Depends(get_admin_atual)):
    apostas  = carregar_json(ARQ_APOSTAS, {})
    grupos   = carregar_grupos()
    usuarios = carregar_json(ARQ_USUARIOS, {})
    resultados = carregar_json(ARQ_RESULTADOS, {})
    venc_reais = set(resultados.get(str(num_rodada), {}).get("vencedores", []))

    da_rodada = {k: v for k, v in apostas.items() if v.get("rodada") == num_rodada}
    por_grupo = defaultdict(list)
    for ap in da_rodada.values():
        por_grupo[ap.get("gid", "?")].append(ap)

    resultado = []
    for gid, lista in por_grupo.items():
        gnome = grupos.get(gid, {}).get("nome", f"Grupo {gid}")
        por_uid = defaultdict(list)
        for ap in lista:
            por_uid[ap.get("uid", "?")].append(ap)
        apostadores = []
        for uid_a, aps in por_uid.items():
            nome_a = usuarios.get(uid_a, {}).get("nome", uid_a)
            apostadores.append({
                "uid": uid_a, "nome": nome_a,
                "apostas": [
                    {
                        "fid": ap.get("fid"),
                        "time": ap.get("time"),
                        "automatica": ap.get("automatica", False),
                        "venceu": ap.get("time") in venc_reais if venc_reais else None,
                    }
                    for ap in aps
                ],
            })
        resultado.append({"gid": gid, "nome": gnome, "apostadores": apostadores})

    return {"rodada": num_rodada, "grupos": resultado, "tem_resultado": bool(venc_reais)}


# ── Serve frontend (em produção) ──────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    