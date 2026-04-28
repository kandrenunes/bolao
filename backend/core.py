"""core.py — Logica de negocio do Bolao Survivor (sem UI)"""

import csv, os, json, re, hashlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PASTA_DADOS    = os.environ.get("DADOS_DIR", "dados")
ARQ_USUARIOS   = os.path.join(PASTA_DADOS, "usuarios.json")
ARQ_GRUPOS     = os.path.join(PASTA_DADOS, "grupos.json")
ARQ_APOSTAS    = os.path.join(PASTA_DADOS, "apostas.json")
ARQ_RESULTADOS = os.path.join(PASTA_DADOS, "resultados.json")
ARQ_STATUS     = os.path.join(PASTA_DADOS, "status.json")
ARQ_FUNIS      = os.path.join(PASTA_DADOS, "funis.json")
ARQ_CONFIG     = os.path.join(PASTA_DADOS, "config.json")
ARQ_CREDITOS   = os.path.join(PASTA_DADOS, "creditos.json")
ARQ_JOGOS      = os.environ.get("JOGOS_CSV", "jogos.csv")
LIMITE_GRUPO   = 10
SENHA_ADMIN    = os.environ.get("SENHA_ADMIN", "admin123")

def garantir_pasta_dados():
    Path(PASTA_DADOS).mkdir(parents=True, exist_ok=True)
    for arq in [ARQ_USUARIOS,ARQ_GRUPOS,ARQ_APOSTAS,ARQ_RESULTADOS,
                ARQ_STATUS,ARQ_FUNIS,ARQ_CONFIG,ARQ_CREDITOS]:
        if not os.path.exists(arq):
            salvar_json(arq, {})

def carregar_config() -> dict:
    return carregar_json(ARQ_CONFIG, {})


def salvar_config(cfg: dict):
    salvar_json(ARQ_CONFIG, cfg)


def config_definida() -> bool:
    return "rodada_inicial" in carregar_config()


def rodada_inicial() -> int:
    return carregar_config().get("rodada_inicial", 1)


def rodada_ativa() -> int:
    """Rodada explicitamente aberta pelo admin. 0 = nenhuma aberta."""
    return carregar_config().get("rodada_ativa", 0)


def prazo_apostas() -> str:
    """Retorna ISO string do prazo limite, ou '' se nao definido."""
    return carregar_config().get("prazo_apostas", "")


def rodada_atual() -> int:
    """
    Retorna a rodada ativa definida pelo admin.
    Fallback: primeira sem resultado >= rodada_inicial.
    """
    cfg = carregar_config()
    r_ativa = cfg.get("rodada_ativa", 0)
    if r_ativa:
        return r_ativa
    # Fallback legado
    r_inicial  = cfg.get("rodada_inicial", 1)
    resultados = carregar_json(ARQ_RESULTADOS, {})
    total      = cfg.get("total_rodadas", 38)
    for r in range(r_inicial, total + 1):
        if str(r) not in resultados:
            return r
    return total


def rodada_aberta_para_apostas() -> int:
    return rodada_atual()


def prazo_expirado() -> bool:
    """True se o prazo de apostas ja passou."""
    prazo = prazo_apostas()
    if not prazo:
        return False
    try:
        return datetime.now() > datetime.fromisoformat(prazo)
    except ValueError:
        return False


def jogos_confirmados_da_rodada() -> list:
    """Retorna lista de indices (1-based) dos jogos confirmados da rodada ativa."""
    return carregar_config().get("jogos_confirmados", [])


def rodada_aberta_e_valida() -> bool:
    """True se ha rodada ativa, prazo nao expirado e jogos confirmados."""
    cfg = carregar_config()
    return (
        bool(cfg.get("rodada_ativa", 0)) and
        bool(cfg.get("jogos_confirmados")) and
        not prazo_expirado()
    )


def garantir_pasta_dados():
    os.makedirs(PASTA_DADOS, exist_ok=True)


def carregar_json(caminho: str, padrao):
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho: str, dados):
    garantir_pasta_dados()
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════
# LEITURA DO CSV
# ══════════════════════════════════════════════

def carregar_jogos(caminho_csv: str) -> dict:
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo '{caminho_csv}' nao encontrado.")

    rodadas = defaultdict(list)

    with open(caminho_csv, newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        cols = {"rodada", "time_casa", "time_visitante"}

        if not cols.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                "CSV invalido: precisa ter as colunas "
                "rodada, time_casa, time_visitante"
            )

        for linha in reader:
            try:
                rodada = int(linha["rodada"].strip())
                casa = linha["time_casa"].strip()
                visit = linha["time_visitante"].strip()
                rodadas[rodada].append((casa, visit))
            except (ValueError, KeyError):
                continue

    return dict(sorted(rodadas.items()))


def listar_times(rodadas: dict) -> list:
    times = set()
    for jogos in rodadas.values():
        for casa, visit in jogos:
            times.add(casa)
            times.add(visit)
    return sorted(times)


# ══════════════════════════════════════════════
# VALIDAÇÕES
# ══════════════════════════════════════════════


def validar_celular(cel: str) -> bool:
    return len(re.sub(r"\D", "", cel)) in (10, 11)



# ══════════════════════════════════════════════
# MÓDULO: CRÉDITOS
# ══════════════════════════════════════════════

def carregar_creditos() -> dict:
    return carregar_json(ARQ_CREDITOS, {})


def salvar_creditos(creditos: dict):
    salvar_json(ARQ_CREDITOS, creditos)


def saldo_creditos(uid: str) -> int:
    return carregar_creditos().get(uid, {}).get("saldo", 0)


def debitar_credito(uid: str, motivo: str = "entrada no grupo") -> bool:
    """Debita 1 credito. Retorna True se ok, False se saldo insuficiente."""
    creditos = carregar_creditos()
    entrada  = creditos.get(uid, {"saldo": 0, "historico": []})
    if entrada["saldo"] <= 0:
        return False
    entrada["saldo"] -= 1
    entrada["historico"].append({
        "tipo":  "debito",
        "valor": -1,
        "motivo": motivo,
        "data":  datetime.now().isoformat(timespec="seconds"),
    })
    creditos[uid] = entrada
    salvar_creditos(creditos)
    return True


def debitar_creditos_multiplos(uid: str, quantidade: int, motivo: str = "entrada no grupo") -> bool:
    """
    Debita N creditos de uma vez.
    Retorna True se havia saldo suficiente, False caso contrario (nao debita nada).
    """
    creditos = carregar_creditos()
    entrada  = creditos.get(uid, {"saldo": 0, "historico": []})
    if entrada["saldo"] < quantidade:
        return False
    entrada["saldo"] -= quantidade
    entrada["historico"].append({
        "tipo":   "debito",
        "valor":  -quantidade,
        "motivo": motivo,
        "data":   datetime.now().isoformat(timespec="seconds"),
    })
    creditos[uid] = entrada
    salvar_creditos(creditos)
    return True


def ja_debitou_entrada(uid: str, gid: str = "") -> bool:
    """Retorna True se o usuario ja gastou seu credito de entrada neste grupo."""
    chave = f"{uid}_{gid}" if gid else uid
    return carregar_status().get(chave, {}).get("credito_entrada_debitado", False)


def marcar_credito_debitado(uid: str, gid: str = ""):
    """Compatibilidade — controle de entrada feito pela existencia de funis. Sem efeito."""
    pass


def creditar(uid: str, quantidade: int, motivo: str = "recarga admin"):
    """Adiciona creditos ao usuario."""
    creditos = carregar_creditos()
    entrada  = creditos.get(uid, {"saldo": 0, "historico": []})
    entrada["saldo"] += quantidade
    entrada["historico"].append({
        "tipo":      "credito",
        "valor":     quantidade,
        "motivo":    motivo,
        "data":      datetime.now().isoformat(timespec="seconds"),
    })
    creditos[uid] = entrada
    salvar_creditos(creditos)


def carregar_grupos() -> dict:
    return carregar_json(ARQ_GRUPOS, {})


def info_grupo(gid: str) -> dict:
    return carregar_grupos().get(gid, {})


def total_apostas_grupo(gid: str) -> int:
    """
    Conta o total de funis criados no grupo.
    Cada funil = 1 aposta para fins de limite do grupo (10 funis = grupo fechado).
    """
    return len(funis_do_grupo(gid))


def apostas_disponiveis_grupo(gid: str) -> int:
    """Retorna quantas apostas (times) ainda cabem no grupo."""
    return LIMITE_GRUPO - total_apostas_grupo(gid)


def vagas_grupo(gid: str) -> int:
    """Compatibilidade: retorna apostas disponiveis no grupo."""
    return apostas_disponiveis_grupo(gid)


def grupo_esta_aberto(gid: str) -> bool:
    """
    Grupo esta aberto para novas entradas somente se:
    1. A rodada atual for <= rodada_inicial_grupo (nao comecou a jogar), E
    2. Ainda ha apostas disponiveis (soma de times < 10)
    """
    g        = info_grupo(gid)
    r_at     = rodada_atual() if config_definida() else 1
    r_grupo  = g.get("rodada_inicial_grupo", 1)
    tem_vaga = apostas_disponiveis_grupo(gid) > 0
    return tem_vaga and r_at <= r_grupo


def grupo_aceita_apostas(gid: str, qtd_times: int) -> bool:
    """Verifica se o grupo tem espaco para mais 'qtd_times' apostas."""
    return apostas_disponiveis_grupo(gid) >= qtd_times


def alocar_grupo(uid: str) -> str:
    """
    Coloca o usuario no primeiro grupo aberto (apostas < 10 e rodada compativel).
    O limite e de 10 APOSTAS TOTAIS (soma de times apostados), nao de membros.
    Se nenhum grupo aberto existir, cria novo com rodada_inicial_grupo = rodada atual.
    """
    grupos = carregar_grupos()
    r_at   = rodada_atual() if config_definida() else 1

    for gid, g in sorted(grupos.items(), key=lambda x: int(x[0])):
        r_grupo = g.get("rodada_inicial_grupo", 1)
        if r_at <= r_grupo and apostas_disponiveis_grupo(gid) > 0:
            if uid not in g["membros"]:
                g["membros"].append(uid)
            salvar_json(ARQ_GRUPOS, grupos)
            return gid

    # Cria novo grupo
    novo_id = str(len(grupos) + 1)
    grupos[novo_id] = {
        "id":                   novo_id,
        "nome":                 f"Grupo {novo_id}",
        "membros":              [uid],
        "rodada_inicial_grupo": r_at,
        "criado_em":            datetime.now().isoformat(timespec="seconds"),
    }
    salvar_json(ARQ_GRUPOS, grupos)
    return novo_id


def alocar_grupo_com_vagas(uid: str, qtd_times: int) -> str:
    """
    Aloca o usuario em um grupo que tenha pelo menos qtd_times apostas disponiveis.
    Cria novo grupo se necessario.
    Retorna o gid alocado.
    """
    grupos = carregar_grupos()
    r_at   = rodada_atual() if config_definida() else 1

    for gid, g in sorted(grupos.items(), key=lambda x: int(x[0])):
        r_grupo = g.get("rodada_inicial_grupo", 1)
        if r_at <= r_grupo and apostas_disponiveis_grupo(gid) >= qtd_times:
            g["membros"].append(uid)
            salvar_json(ARQ_GRUPOS, grupos)
            return gid

    # Cria novo grupo
    novo_id = str(len(grupos) + 1)
    grupos[novo_id] = {
        "id":                   novo_id,
        "nome":                 f"Grupo {novo_id}",
        "membros":              [uid],
        "rodada_inicial_grupo": r_at,
        "criado_em":            datetime.now().isoformat(timespec="seconds"),
    }
    salvar_json(ARQ_GRUPOS, grupos)
    return novo_id


def carregar_funis() -> dict:
    return carregar_json(ARQ_FUNIS, {})


def salvar_funis(funis: dict):
    salvar_json(ARQ_FUNIS, funis)


def carregar_status() -> dict:
    """Compatibilidade — retorna funis como status para codigo legado."""
    return carregar_funis()


def salvar_status(status: dict):
    """Compatibilidade — filtra apenas registros validos de funis antes de salvar."""
    funis_validos = {k: v for k, v in status.items() if _funil_valido(v)}
    salvar_funis(funis_validos)


def _proximo_id_funil(uid: str, gid: str) -> str:
    """Gera ID sequencial para novo funil do usuario no grupo."""
    funis = carregar_funis()
    prefixo = f"{uid}_{gid}_"
    existentes = [k for k in funis if k.startswith(prefixo)]
    return f"{prefixo}{len(existentes) + 1}"


def criar_funil(uid: str, gid: str, rodada_inicio: int, time_inicial: str) -> str:
    """Cria um novo funil para o apostador no grupo. Retorna o ID do funil."""
    funis = carregar_funis()
    fid   = _proximo_id_funil(uid, gid)
    funis[fid] = {
        "id":                   fid,
        "uid":                  uid,
        "gid":                  gid,
        "rodada_inicio":        rodada_inicio,
        "historico":            [{"rodada": rodada_inicio, "time": time_inicial}],
        "times_usados":         [time_inicial],
        "eliminado":            False,
        "eliminado_na_rodada":  None,
        "vencedor":             False,
    }
    salvar_funis(funis)
    return fid


def _funil_valido(f: dict) -> bool:
    """Retorna True se o registro tem a estrutura minima de um funil."""
    return isinstance(f, dict) and "gid" in f and "uid" in f and "rodada_inicio" in f


def funis_do_usuario(uid: str, gid: str = "") -> list:
    """Retorna lista de funis de um usuario (opcionalmente filtrado por grupo)."""
    funis = carregar_funis()
    return [f for f in funis.values()
            if _funil_valido(f) and f["uid"] == uid and (not gid or f["gid"] == gid)]


def funis_vivos_usuario(uid: str, gid: str = "") -> list:
    """Retorna funis ainda nao eliminados."""
    return [f for f in funis_do_usuario(uid, gid) if not f.get("eliminado", False)]


def funis_do_grupo(gid: str) -> list:
    """Retorna todos os funis de um grupo."""
    funis = carregar_funis()
    return [f for f in funis.values() if _funil_valido(f) and f["gid"] == gid]


def funis_vivos_grupo(gid: str) -> list:
    return [f for f in funis_do_grupo(gid) if not f.get("eliminado", False)]


def iniciar_status_usuario(uid: str, gid: str):
    """Compatibilidade — funis sao criados em fazer_aposta. Nao faz nada."""
    pass


def times_usados_no_funil(fid: str) -> list:
    funis = carregar_funis()
    return funis.get(fid, {}).get("times_usados", [])


def todos_times_usados(uid: str, gid: str = "") -> list:
    """Uniao de todos os times usados pelo usuario em todos seus funis (opcional: por grupo)."""
    usados = set()
    for f in funis_do_usuario(uid, gid):
        usados.update(f.get("times_usados", []))
    return list(usados)


def times_usados(uid: str, gid: str = "") -> list:
    return todos_times_usados(uid, gid)


def esta_eliminado(uid: str, gid: str = "") -> bool:
    """True se TODOS os funis do usuario (no grupo) estiverem eliminados."""
    todos = funis_do_usuario(uid, gid)
    if not todos:
        return False
    return all(f["eliminado"] for f in todos)


def e_vencedor(uid: str, gid: str = "") -> bool:
    funis = carregar_funis()
    return any(f.get("vencedor") for f in funis.values()
               if f["uid"] == uid and (not gid or f["gid"] == gid))


def ja_debitou_entrada(uid: str, gid: str = "") -> bool:
    """True se o usuario ja tem ao menos um funil neste grupo (entrada paga)."""
    return len(funis_do_usuario(uid, gid)) > 0


def marcar_credito_debitado(uid: str, gid: str = ""):
    """Compatibilidade — controle feito pela existencia de funis."""
    pass


def ativos_do_grupo(gid: str) -> list:
    """UIDs com ao menos 1 funil vivo no grupo."""
    grupos  = carregar_grupos()
    membros = grupos.get(gid, {}).get("membros", [])
    return [uid for uid in membros if funis_vivos_usuario(uid, gid)]


def ativos_do_grupo_com_status(gid: str, status: dict) -> list:
    """Compatibilidade — usa funis."""
    return ativos_do_grupo(gid)


def _ultima_qtd_vencedora(uid: str, num_rodada: int,
                           apostas: dict, resultados: dict, gid: str = "") -> int:
    """Retorna quantos funis vivos o usuario tem (para aposta automatica)."""
    vivos = funis_vivos_usuario(uid, gid)
    return max(len(vivos), 1)


def processar_eliminacao(gid: str, num_rodada: int):
    """
    Para cada funil do grupo:
    - Busca a aposta do funil nesta rodada
    - Se o time apostado perdeu/empatou → elimina o funil
    - Regra coletiva: se TODOS os funis ativos seriam eliminados → nenhum e eliminado
    - Detecta vencedor: unico uid com funil vivo quando todos os outros sao eliminados
    """
    resultados = carregar_json(ARQ_RESULTADOS, {})
    funis      = carregar_funis()
    apostas    = carregar_json(ARQ_APOSTAS, {})
    usuarios   = carregar_json(ARQ_USUARIOS, {})

    chave_res = str(num_rodada)
    if chave_res not in resultados:
        return None

    vencedores_reais = set(resultados[chave_res]["vencedores"])
    funis_do_grp     = [f for f in funis.values() if f["gid"] == gid and not f["eliminado"]]

    if not funis_do_grp:
        return {"_empate_coletivo": False, "_eliminados_agora": [], "_vencedor": None}

    relatorio = {}

    # Calcula resultado de cada funil
    resultados_funil = {}   # fid → {apostou, time, sobreviveu}
    for f in funis_do_grp:
        fid          = f["id"]
        chave_aposta = f"{f['uid']}_{gid}_{num_rodada}_{fid}"
        aposta       = apostas.get(chave_aposta)

        if not aposta:
            resultados_funil[fid] = {"apostou": False, "time": None, "sobreviveu": None}
        else:
            time      = aposta["time"]
            sobreviveu = time in vencedores_reais
            resultados_funil[fid] = {"apostou": True, "time": time, "sobreviveu": sobreviveu}

        uid  = f["uid"]
        nome = usuarios.get(uid, {}).get("nome", uid)
        relatorio.setdefault(uid, {"nome": nome, "funis": {}})
        relatorio[uid]["funis"][fid] = resultados_funil[fid]

    # Regra coletiva: se TODOS os funis que apostaram seriam eliminados
    apostaram        = [fid for fid,r in resultados_funil.items() if r["apostou"]]
    todos_eliminariam = (len(apostaram) > 0 and
                         all(not resultados_funil[fid]["sobreviveu"] for fid in apostaram))
    relatorio["_empate_coletivo"] = todos_eliminariam

    # Aplica eliminações
    eliminados_agora = []
    for f in funis_do_grp:
        fid = f["id"]
        r   = resultados_funil[fid]
        if not r["apostou"]:
            continue
        if todos_eliminariam:
            # Empate coletivo: nenhum eliminado, time apostado adicionado ao historico
            if r["time"] not in f["times_usados"]:
                f["times_usados"].append(r["time"])
            f["historico"].append({"rodada": num_rodada, "time": r["time"],
                                   "resultado": "empate_coletivo"})
        elif r["sobreviveu"]:
            if r["time"] not in f["times_usados"]:
                f["times_usados"].append(r["time"])
            f["historico"].append({"rodada": num_rodada, "time": r["time"],
                                   "resultado": "venceu"})
        else:
            f["eliminado"]           = True
            f["eliminado_na_rodada"] = num_rodada
            f["historico"].append({"rodada": num_rodada, "time": r["time"],
                                   "resultado": "eliminado"})
            eliminados_agora.append(f["id"])

    relatorio["_eliminados_agora"] = eliminados_agora

    # Detecta vencedor: apenas 1 uid com funil vivo restante
    funis_vivos_pos = [f for f in funis.values()
                       if f["gid"] == gid and not f["eliminado"]]
    uids_vivos = list({f["uid"] for f in funis_vivos_pos})

    if len(uids_vivos) == 1:
        vencedor_uid = uids_vivos[0]
        for f in funis.values():
            if f["gid"] == gid and f["uid"] == vencedor_uid and not f["eliminado"]:
                f["vencedor"] = True
        relatorio["_vencedor"] = vencedor_uid
    elif len(uids_vivos) == 0:
        # Todos eliminados juntos — empate final
        for fid in eliminados_agora:
            funis[fid]["vencedor"]  = True
            funis[fid]["eliminado"] = False
        relatorio["_vencedor"] = [funis[fid]["uid"] for fid in eliminados_agora]
    else:
        relatorio["_vencedor"] = None

    salvar_funis(funis)
    return relatorio


def gerar_apostas_automaticas(num_rodada: int, rodadas: dict) -> list:
    """
    Para cada funil vivo que NAO apostou nesta rodada (em grupos em andamento):
    Escolhe 1 time em ordem alfabetica que ainda nao foi usado naquele funil.
    Debita credito apenas se for o primeiro funil do usuario neste grupo.
    """
    apostas    = carregar_json(ARQ_APOSTAS, {})
    resultados = carregar_json(ARQ_RESULTADOS, {})
    funis      = carregar_funis()
    grupos     = carregar_grupos()
    usuarios   = carregar_json(ARQ_USUARIOS, {})

    times_da_rodada = set()
    for casa, visit in rodadas.get(num_rodada, []):
        times_da_rodada.add(casa)
        times_da_rodada.add(visit)

    relatorio = []

    for gid, g in grupos.items():
        r_inicial = g.get("rodada_inicial_grupo", 1)
        if num_rodada <= r_inicial:
            continue  # grupo novo — sem aposta automatica

        for f in [f for f in funis.values() if f["gid"] == gid and not f["eliminado"]]:
            fid = f["id"]
            uid = f["uid"]
            chave_aposta = f"{uid}_{gid}_{num_rodada}_{fid}"

            if chave_aposta in apostas:
                continue  # ja apostou

            # Verifica se apostou em rodada anterior neste funil
            apostou_antes = any(h["rodada"] < num_rodada for h in f.get("historico", []))
            if not apostou_antes:
                relatorio.append({"fid": fid, "uid": uid, "gid": gid,
                                   "gerada": False, "motivo": "Funil novo — sem aposta anterior"})
                continue

            # Escolhe 1 time disponivel em ordem alfabetica
            ja_usados   = set(f.get("times_usados", []))
            disponiveis = sorted(t for t in times_da_rodada if t not in ja_usados)

            if not disponiveis:
                relatorio.append({"fid": fid, "uid": uid, "gid": gid,
                                   "gerada": False, "motivo": "Sem times disponiveis"})
                continue

            time_auto = disponiveis[0]

            # Credito: gratuito (ja pagou na entrada)
            apostas[chave_aposta] = {
                "uid": uid, "gid": gid, "fid": fid,
                "rodada": num_rodada, "time": time_auto,
                "apostado_em": datetime.now().isoformat(timespec="seconds"),
                "automatica": True,
            }
            relatorio.append({"fid": fid, "uid": uid, "gid": gid,
                               "gerada": True, "time": time_auto,
                               "nome": usuarios.get(uid, {}).get("nome", uid)})

    salvar_json(ARQ_APOSTAS, apostas)
    return relatorio


# ══════════════════════════════════════════════
# MÓDULO: USUÁRIOS
# ══════════════════════════════════════════════
