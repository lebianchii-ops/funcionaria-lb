import streamlit as st
import json
import requests
import base64
from datetime import datetime, date, timedelta
import uuid
import calendar

st.set_page_config(page_title="LB Collection — Painel", page_icon="👜", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f5f4f0; }
[data-testid="stMain"] > div { padding-top: 1rem; }
.prio-header {
    border-radius: 8px 8px 0 0;
    background: white;
    padding: 10px 4px 6px;
    font-weight: 700;
    font-size: 0.95rem;
    margin-bottom: -1px;
}
.task-sep { border: none; border-top: 1px solid #f0f0f0; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

REPO      = "lebianchii-ops/funcionaria-lb"
DATA_FILE = "dados.json"
MES_NOME  = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
MES_ABREV = ["JAN","FEV","MAR","ABR","MAI","JUN","JUL","AGO","SET","OUT","NOV","DEZ"]
PRIOS     = ["Alta", "Média", "Baixa"]
COR       = {"Alta": "#e74c3c", "Média": "#f39c12", "Baixa": "#27ae60"}
EMOJI     = {"Alta": "🔴",     "Média": "🟡",       "Baixa": "🟢"}
CATS      = ["—", "K2 COMÉRCIO", "LB COLLECTION", "AMBOS (K2 e LB)",
             "K2 - AMZ", "K2 - ML", "K2 - SH", "K2 - TK TK", "K2 - VD",
             "LB Collection - AMZ", "LB Collection - ML", "LB Collection - SH",
             "LB Collection - TK TK", "LB Collection - VD"]
FILTRO_CATS = ["Todos"] + CATS
NOTA_OPCOES = ["Sim", "Não"]
# freela — 2 níveis só para mostrar a ordem do que fazer primeiro
FR_PRIOS  = ["Fazer primeiro", "Fazer depois"]
FR_COR    = {"Fazer primeiro": "#e74c3c", "Fazer depois": "#27ae60"}
FR_EMOJI  = {"Fazer primeiro": "🔴",      "Fazer depois": "🟢"}

# ─── helpers ────────────────────────────────────────────────────────────────

def fmt_data(d_str):
    try:
        return date.fromisoformat(d_str).strftime("%d/%m/%y")
    except Exception:
        return d_str

def filtro_categoria(key, label="🔍 Filtrar por marketplace"):
    return st.selectbox(label, FILTRO_CATS, key=key)

def aplica_filtro(lista, filtro):
    if filtro == "Todos":
        return lista
    return [x for x in lista if x.get("categoria", "—") == filtro]

def _marcar_pendente_conclusao(tipo, item_id):
    # callback do checkbox — roda antes do rerun, então pode resetar a própria caixinha com segurança
    chave = f"ck{item_id}" if tipo == "tarefa" else f"fck{item_id}"
    if st.session_state.get(chave):
        st.session_state["confirmar_pendente"] = (tipo, item_id)
        st.session_state[chave] = False

def get_token():
    t = st.secrets["github_token"]
    t = ''.join(c for c in t if ord(c) < 128).strip()
    if t.startswith("ghp_") or t.startswith("github_pat_"):
        return t
    try:
        return base64.b64decode(t).decode("ascii").strip()
    except Exception:
        return t

def carregar_dados():
    headers = {"Authorization": f"token {get_token()}"}
    url = f"https://api.github.com/repos/{REPO}/contents/{DATA_FILE}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()
        data = json.loads(base64.b64decode(content["content"]).decode())
        st.session_state["sha"] = content["sha"]
        return data
    return {"tarefas": [], "avisos": []}

def salvar_dados(data):
    headers = {"Authorization": f"token {get_token()}"}
    url = f"https://api.github.com/repos/{REPO}/contents/{DATA_FILE}"

    # busca SHA atual antes de salvar — evita conflito entre usuários simultâneos
    r_get = requests.get(url, headers=headers)
    if r_get.status_code == 200:
        sha_atual = r_get.json()["sha"]
        st.session_state["sha"] = sha_atual
    else:
        sha_atual = st.session_state.get("sha")

    content = base64.b64encode(
        json.dumps(data, ensure_ascii=False, indent=2).encode()
    ).decode()
    payload = {
        "message": f"update {datetime.now().strftime('%d/%m %H:%M')}",
        "content": content,
        "sha": sha_atual,
    }
    r = requests.put(url, headers=headers, json=payload)
    if r.status_code in [200, 201]:
        st.session_state["sha"] = r.json()["content"]["sha"]
        return True
    st.error(f"❌ Erro ao salvar (código {r.status_code}). Clique em 🔄 Atualizar dados e tente novamente.")
    return False

def html_mini_cal(ano, mes, hoje, datas_tarefas):
    calendar.setfirstweekday(6)
    semanas = calendar.monthcalendar(ano, mes)
    linhas = ""
    for semana in semanas:
        linhas += "<tr>"
        for dia in semana:
            if dia == 0:
                linhas += "<td></td>"
                continue
            d = date(ano, mes, dia)
            td = 'style="padding:3px 2px;white-space:nowrap;text-align:center;position:relative"'
            if d == hoje:
                linhas += (f'<td {td}><div style="background:#c0392b;color:#fff;border-radius:50%;'
                           f'width:24px;height:24px;display:inline-flex;align-items:center;'
                           f'justify-content:center;font-weight:700;font-size:0.78rem;margin:auto">'
                           f'{dia}</div></td>')
            elif str(d) in datas_tarefas:
                linhas += (f'<td {td}>'
                           f'<span style="font-size:0.78rem;font-weight:600">{dia}</span>'
                           f'<span style="position:absolute;bottom:1px;left:50%;transform:translateX(-50%);'
                           f'width:4px;height:4px;background:#e74c3c;border-radius:50%;display:block"></span>'
                           f'</td>')
            else:
                linhas += f'<td {td}><span style="font-size:0.78rem;color:#555">{dia}</span></td>'
        linhas += "</tr>"
    cab = "".join(
        f'<th style="font-size:0.65rem;color:#aaa;font-weight:600;padding:0 4px 6px;white-space:nowrap">{d}</th>'
        for d in ["D","S","T","Q","Q","S","S"])
    return f"""
    <div style="background:white;border-radius:12px;padding:14px 10px;
                box-shadow:0 1px 4px rgba(0,0,0,0.08);font-family:sans-serif;text-align:center;overflow:hidden">
      <div style="font-weight:700;font-size:0.82rem;margin-bottom:10px">{MES_NOME[mes-1].upper()} {ano}</div>
      <table style="width:100%;border-collapse:collapse">
        <tr>{cab}</tr>{linhas}
      </table>
    </div>"""

def html_dia(dia, nome, eventos, e_hoje):
    borda = "2px solid #c0392b" if e_hoje else "1px solid #e8e8e8"
    num = (f'<div style="background:#c0392b;color:#fff;border-radius:50%;width:28px;height:28px;'
           f'display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem">{dia.day}</div>'
           if e_hoje else
           f'<div style="font-size:1.3rem;font-weight:700;line-height:1.2">{dia.day}</div>')
    ev_html = ""
    for t in eventos:
        cor_b = COR.get(t.get("prioridade"), "#ccc")
        cor_g = {"Alta":"#fde8e8","Média":"#fef9e7","Baixa":"#eafaf1"}.get(t.get("prioridade"),"#f5f5f5")
        dot   = EMOJI.get(t.get("prioridade"), "⚪")
        titulo = t["titulo"][:14]+"…" if len(t["titulo"]) > 14 else t["titulo"]
        ev_html += (f'<div style="background:{cor_g};border-left:3px solid {cor_b};'
                    f'border-radius:4px;padding:3px 6px;margin-top:4px;font-size:0.72rem;font-weight:500">'
                    f'{dot} {titulo}</div>')
    if not ev_html:
        ev_html = '<div style="color:#ccc;font-size:0.7rem;font-style:italic;margin-top:6px">livre</div>'
    return (f'<div style="border:{borda};border-radius:10px;padding:10px 8px;'
            f'min-height:140px;background:white;height:100%">'
            f'<div style="font-size:0.6rem;font-weight:700;color:#aaa;letter-spacing:1px;margin-bottom:4px">'
            f'{nome} {MES_ABREV[dia.month-1]}</div>'
            f'{num}{ev_html}</div>')

# ── session state ────────────────────────────────────────────────────────────
for key, val in [("dados", None), ("semana_offset", 0), ("mes_offset", 0), ("editando", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state["dados"] is None:
    st.session_state["dados"] = carregar_dados()

dados = st.session_state["dados"]
dados.setdefault("tarefas", [])
dados.setdefault("avisos", [])
dados.setdefault("freelas", [])
dados.setdefault("entradas", [])

CATS_MIGRACAO = {
    "ML - LB Collection":    "LB Collection - ML",
    "SH - LB Collection":    "LB Collection - SH",
    "AMZ - LB Collection":   "LB Collection - AMZ",
    "TK TK - LB Collection": "LB Collection - TK TK",
    "LB - ML":               "LB Collection - ML",
    "LB - SH":               "LB Collection - SH",
    "LB - AMZ":              "LB Collection - AMZ",
    "LB - TK TK":            "LB Collection - TK TK",
    "LB - VD":               "LB Collection - VD",
    "K2 + LB":               "AMBOS (K2 e LB)",
}
precisa_migrar = False

def migra_categoria(item):
    global precisa_migrar
    if item.get("categoria") in CATS_MIGRACAO:
        item["categoria"] = CATS_MIGRACAO[item["categoria"]]
        precisa_migrar = True

for e in dados["entradas"]:
    e.setdefault("observacao", "")
    migra_categoria(e)
for f in dados["freelas"]:
    f.setdefault("feita", False)
    f.setdefault("feita_em", None)
    f.setdefault("descricao", "")
    f.setdefault("prioridade", FR_PRIOS[0])
    f.setdefault("categoria", "—")
    f.setdefault("obs_conclusao", "")
    migra_categoria(f)
for t in dados.get("tarefas", []):
    t.setdefault("feita", False)
    t.setdefault("feita_em", None)
    t.setdefault("descricao", "")
    t.setdefault("prioridade", "Baixa")
    t.setdefault("data", str(date.today()))
    t.setdefault("categoria", "—")
    t.setdefault("tipo", "evento")
    t.setdefault("obs_conclusao", "")
    migra_categoria(t)
for a in dados.get("avisos", []):
    a.setdefault("categoria", "—")
    migra_categoria(a)

if precisa_migrar and not st.session_state.get("migrado_cats"):
    st.session_state["migrado_cats"] = True
    salvar_dados(dados)

# ── dialog nova tarefa (definido uma vez, no nível do script) ─────────────
@st.dialog("Nova Tarefa")
def popup_nova_tarefa(data_inicial, prioridade_inicial="Baixa", tipo="evento"):
    titulo    = st.text_input("Título *", placeholder="O que precisa ser feito?")
    categoria = st.selectbox("Categoria / Marketplace", CATS)
    desc      = st.text_area("Descrição (opcional)", height=80)
    idx_prio  = PRIOS.index(prioridade_inicial) if prioridade_inicial in PRIOS else 0
    if tipo == "evento":
        c1, c2 = st.columns(2)
        with c1:
            data = st.date_input("Data", value=data_inicial, format="DD/MM/YYYY")
        with c2:
            prio = st.selectbox("Prioridade", PRIOS, index=idx_prio)
    else:
        data = None
        prio = st.selectbox("Prioridade", PRIOS, index=idx_prio)
    if st.button("✅ Adicionar tarefa", use_container_width=True, type="primary"):
        if not titulo.strip():
            st.warning("Por favor, preencha o título.")
            return
        dados["tarefas"].append({
            "id":         str(uuid.uuid4()),
            "titulo":     titulo.strip(),
            "categoria":  categoria,
            "descricao":  desc.strip(),
            "data":       str(data) if data else None,
            "tipo":       tipo,
            "prioridade": prio,
            "feita":      False,
            "feita_em":   None,
            "criado_em":  datetime.now().isoformat(),
        })
        if salvar_dados(dados):
            st.rerun()

@st.dialog("Confirmar conclusão")
def popup_confirmar_conclusao(item_id, tipo):
    colecao = "tarefas" if tipo == "tarefa" else "freelas"
    item = next((x for x in dados[colecao] if x["id"] == item_id), None)
    if not item:
        st.error("Item não encontrado.")
        return
    st.write(f"Marcar **{item['titulo']}** como concluída?")
    obs = st.text_area("Observação (opcional)", height=80, key=f"obs_{tipo}_{item_id}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Confirmar", use_container_width=True, type="primary",
                      key=f"confirmar_{tipo}_{item_id}"):
            item["feita"]         = True
            item["feita_em"]      = datetime.now().strftime("%d/%m/%y %H:%M")
            item["obs_conclusao"] = obs.strip()
            if salvar_dados(dados):
                st.rerun()
    with c2:
        if st.button("✕ Cancelar", use_container_width=True,
                      key=f"cancelar_{tipo}_{item_id}"):
            st.rerun()

@st.dialog("Editar Tarefa")
def popup_editar_tarefa(tarefa_id):
    t = next((x for x in dados["tarefas"] if x["id"] == tarefa_id), None)
    if not t:
        st.error("Tarefa não encontrada.")
        return
    nv_t   = st.text_input("Título", value=t["titulo"])
    nv_cat = st.selectbox("Categoria / Marketplace", CATS,
                          index=CATS.index(t.get("categoria", "—")) if t.get("categoria", "—") in CATS else 0)
    nv_d   = st.text_area("Descrição", value=t.get("descricao", ""), height=80)
    c1, c2 = st.columns(2)
    with c1:
        nv_dt = st.date_input("Data",
                              value=date.fromisoformat(t["data"]) if t.get("data") else date.today(),
                              format="DD/MM/YYYY")
    with c2:
        nv_p = st.selectbox("Prioridade", PRIOS,
                            index=PRIOS.index(t.get("prioridade", "Baixa")))
    obs_conc = st.text_area("Observação de conclusão (opcional)",
                             value=t.get("obs_conclusao", ""), height=70,
                             key=f"obsedit_{tarefa_id}")
    st.write("")
    c_sv, c_ok, c_del = st.columns(3)
    with c_sv:
        if st.button("💾 Salvar", use_container_width=True, type="primary"):
            for x in dados["tarefas"]:
                if x["id"] == tarefa_id:
                    x.update({"titulo": nv_t.strip(), "categoria": nv_cat,
                               "descricao": nv_d.strip(), "data": str(nv_dt), "prioridade": nv_p})
            if salvar_dados(dados):
                st.rerun()
    with c_ok:
        if st.button("✅ Marcar feita", use_container_width=True):
            for x in dados["tarefas"]:
                if x["id"] == tarefa_id:
                    x["feita"]         = True
                    x["feita_em"]      = datetime.now().strftime("%d/%m/%y %H:%M")
                    x["obs_conclusao"] = obs_conc.strip()
            if salvar_dados(dados):
                st.rerun()
    with c_del:
        if st.button("🗑️ Excluir", use_container_width=True):
            dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != tarefa_id]
            if salvar_dados(dados):
                st.rerun()

@st.dialog("Editar Entrada")
def popup_editar_entrada(entrada_id):
    e = next((x for x in dados["entradas"] if x["id"] == entrada_id), None)
    if not e:
        st.error("Entrada não encontrada.")
        return
    nv_dt = st.date_input("Dia que chegou",
                          value=date.fromisoformat(e["data"]) if e.get("data") else date.today(),
                          format="DD/MM/YYYY")
    nv_forn = st.text_input("Fornecedor", value=e.get("fornecedor", ""))
    nv_cat = st.selectbox("Categoria / Marketplace", CATS,
                          index=CATS.index(e.get("categoria", "—")) if e.get("categoria", "—") in CATS else 0)
    nv_bate = st.selectbox("A nota bate com a quantidade?", NOTA_OPCOES,
                           index=NOTA_OPCOES.index(e.get("nota_bate", "Sim")) if e.get("nota_bate", "Sim") in NOTA_OPCOES else 0)
    nv_obs = st.text_area("Observação", value=e.get("observacao", ""), height=80)
    st.write("")
    c_sv, c_del = st.columns(2)
    with c_sv:
        if st.button("💾 Salvar", use_container_width=True, type="primary", key=f"esv{entrada_id}"):
            e.update({"data": str(nv_dt), "fornecedor": nv_forn.strip(),
                       "categoria": nv_cat, "nota_bate": nv_bate,
                       "observacao": nv_obs.strip()})
            if salvar_dados(dados):
                st.rerun()
    with c_del:
        if st.button("🗑️ Excluir", use_container_width=True, key=f"edl{entrada_id}"):
            dados["entradas"] = [x for x in dados["entradas"] if x["id"] != entrada_id]
            if salvar_dados(dados):
                st.rerun()

@st.dialog("Editar Freela")
def popup_editar_freela(freela_id):
    f = next((x for x in dados["freelas"] if x["id"] == freela_id), None)
    if not f:
        st.error("Freela não encontrado.")
        return
    nv_t = st.text_input("Título", value=f["titulo"])
    nv_cat = st.selectbox("Categoria / Marketplace", CATS,
                          index=CATS.index(f.get("categoria", "—")) if f.get("categoria", "—") in CATS else 0,
                          key=f"fcat{freela_id}")
    nv_d = st.text_area("Descrição", value=f.get("descricao", ""), height=80)
    prio_atual = f.get("prioridade", FR_PRIOS[0])
    nv_p = st.selectbox("Ordem", FR_PRIOS,
                        index=FR_PRIOS.index(prio_atual) if prio_atual in FR_PRIOS else 0,
                        format_func=lambda p: f"{FR_EMOJI[p]} {p}")
    obs_conc = st.text_area("Observação de conclusão (opcional)",
                             value=f.get("obs_conclusao", ""), height=70,
                             key=f"fobsedit{freela_id}")
    st.write("")
    c_sv, c_ok, c_del = st.columns(3)
    with c_sv:
        if st.button("💾 Salvar", use_container_width=True, type="primary", key=f"fsv{freela_id}"):
            f.update({"titulo": nv_t.strip(), "categoria": nv_cat,
                       "descricao": nv_d.strip(), "prioridade": nv_p})
            if salvar_dados(dados):
                st.rerun()
    with c_ok:
        if st.button("✅ Marcar feito", use_container_width=True, key=f"fok{freela_id}"):
            f["feita"]         = True
            f["feita_em"]      = datetime.now().strftime("%d/%m/%y %H:%M")
            f["obs_conclusao"] = obs_conc.strip()
            if salvar_dados(dados):
                st.rerun()
    with c_del:
        if st.button("🗑️ Excluir", use_container_width=True, key=f"fdl{freela_id}"):
            dados["freelas"] = [x for x in dados["freelas"] if x["id"] != freela_id]
            if salvar_dados(dados):
                st.rerun()

# ── cabeçalho ────────────────────────────────────────────────────────────────
st.title("👜 LB Collection — Painel")
# valor atual do filtro global — o controle em si fica na coluna do mini-calendário (aba Tarefas),
# mas o valor vale para todas as abas
filtro_global = st.session_state.get("filtro_global", FILTRO_CATS[0])
tab1, tab_fr, tab_ent, tab2, tab3, tab4 = st.tabs(
    ["✅ Tarefas", "🧵 Freela", "📦 Entrada de Mercadoria", "📢 Avisos", "✔️ Concluídos", "❓ Ajuda"]
)

# pop-up de confirmação de conclusão — um único disparo por marcação de caixinha (evita reabrir sozinho)
_pendente = st.session_state.get("confirmar_pendente")
if _pendente:
    st.session_state["confirmar_pendente"] = None
    popup_confirmar_conclusao(_pendente[1], _pendente[0])

# ════════════════════════════════════════════════════════════════════════════
with tab1:
    hoje    = date.today()
    sem_off = st.session_state["semana_offset"]
    mes_off = st.session_state["mes_offset"]

    inicio_sem = hoje - timedelta(days=(hoje.weekday() + 1) % 7) + timedelta(weeks=sem_off)
    dias_sem   = [inicio_sem + timedelta(days=i) for i in range(7)]
    nomes_dia  = ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SÁB"]

    ano_cal = hoje.year
    mes_cal = hoje.month + mes_off
    while mes_cal > 12: mes_cal -= 12; ano_cal += 1
    while mes_cal < 1:  mes_cal += 12; ano_cal -= 1

    tarefas_ativas = aplica_filtro(
        [t for t in dados.get("tarefas", []) if not t.get("feita")], filtro_global
    )
    datas_tarefas  = {t.get("data") for t in tarefas_ativas}

    # ── barra de navegação ───────────────────────────────────────────────────
    nav = st.columns([1, 1, 4, 1, 5, 1])
    with nav[0]:
        if st.button("‹", key="mp", help="Mês anterior"):
            st.session_state["mes_offset"] -= 1; st.rerun()
    with nav[1]:
        if st.button("›", key="mn", help="Próximo mês"):
            st.session_state["mes_offset"] += 1; st.rerun()
    with nav[3]:
        if st.button("‹", key="sp", help="Semana anterior"):
            st.session_state["semana_offset"] -= 1; st.rerun()
    with nav[4]:
        d0, d6 = dias_sem[0], dias_sem[6]
        if d0.month == d6.month:
            lbl = f"{d0.day} – {d6.day} de {MES_NOME[d0.month-1]} {d0.year}"
        else:
            lbl = f"{d0.day}/{d0.month} – {d6.day}/{d6.month}/{d6.year}"
        st.markdown(f"<p style='text-align:center;font-weight:600;margin:6px 0 0'>{lbl}</p>",
                    unsafe_allow_html=True)
    with nav[5]:
        if st.button("›", key="sn", help="Próxima semana"):
            st.session_state["semana_offset"] += 1; st.rerun()

    # ── corpo do calendário ──────────────────────────────────────────────────
    col_mini, col_sem = st.columns([2, 9])

    with col_mini:
        st.markdown(html_mini_cal(ano_cal, mes_cal, hoje, datas_tarefas),
                    unsafe_allow_html=True)
        st.write("")
        if st.button("🔄 Atualizar dados", use_container_width=True,
                     help="Recarregar do servidor (use se outra pessoa atualizou)"):
            st.session_state["dados"] = None
            st.rerun()
        st.write("")
        filtro_categoria("filtro_global")

    with col_sem:
        cols_d = st.columns(7)
        for i, (dia, nome) in enumerate(zip(dias_sem, nomes_dia)):
            eventos_dia = [t for t in tarefas_ativas if t.get("data") == str(dia)]
            e_hoje = dia == hoje
            with cols_d[i]:
                borda_top = "border-top:3px solid #c0392b;" if e_hoje else ""
                num_html  = (
                    f'<span style="background:#c0392b;color:#fff;border-radius:50%;'
                    f'width:24px;height:24px;display:inline-flex;align-items:center;'
                    f'justify-content:center;font-weight:700;font-size:0.82rem">{dia.day}</span>'
                    if e_hoje else
                    f'<span style="font-size:1.2rem;font-weight:700">{dia.day}</span>'
                )
                with st.container(border=True):
                    st.markdown(
                        f"<div style='{borda_top}margin:-15px -15px 8px -15px;"
                        f"padding:8px 12px 6px;border-radius:7px 7px 0 0'>"
                        f"<div style='font-size:0.6rem;font-weight:700;color:#aaa;"
                        f"letter-spacing:1px'>{nome} {MES_ABREV[dia.month-1]}</div>"
                        f"{num_html}</div>",
                        unsafe_allow_html=True,
                    )
                    if eventos_dia:
                        for t in eventos_dia:
                            dot   = EMOJI.get(t.get("prioridade"), "⚪")
                            titulo_ev = t["titulo"][:13] + "…" if len(t["titulo"]) > 13 else t["titulo"]
                            if st.button(f"{dot} {titulo_ev}", key=f"ev_{t['id']}_{i}",
                                         use_container_width=True, help="Clique para editar"):
                                popup_editar_tarefa(t["id"])
                    else:
                        st.markdown(
                            "<span style='color:#ccc;font-size:0.72rem;font-style:italic'>livre</span>",
                            unsafe_allow_html=True,
                        )
                if st.button("＋", key=f"ad{i}", use_container_width=True,
                             help=f"Adicionar evento em {fmt_data(str(dia))}"):
                    popup_nova_tarefa(dia, tipo="evento")

    st.divider()

    # ── colunas de prioridade ────────────────────────────────────────────────
    pendentes = tarefas_ativas

    def render_col(col, prio):
        bloco = sorted(
            [t for t in pendentes if t.get("prioridade") == prio],
            key=lambda x: x.get("data") or x.get("criado_em", "")
        )
        cor = COR[prio]
        with col:
            with st.container(border=True):
                st.markdown(
                    f"<div style='border-top:4px solid {cor};border-radius:7px 7px 0 0;"
                    f"margin:-15px -15px 10px -15px;padding:10px 15px;font-weight:700;font-size:0.95rem'>"
                    f"{EMOJI[prio]} {prio} "
                    f"<span style='font-weight:400;font-size:0.8rem;color:#999'>({len(bloco)})</span></div>",
                    unsafe_allow_html=True,
                )
                if st.button(f"➕ Nova tarefa {prio.lower()}", key=f"nt_{prio}",
                             use_container_width=True):
                    popup_nova_tarefa(hoje, prio, tipo="tarefa")
                st.markdown("<hr class='task-sep'>", unsafe_allow_html=True)
                if not bloco:
                    st.caption("Nenhuma tarefa.")
                for idx, t in enumerate(bloco):
                    ed = st.session_state["editando"] == t["id"]
                    if ed:
                        is_evento = t.get("tipo", "evento") == "evento"
                        nv_t  = st.text_input("Título", value=t["titulo"],  key=f"et{t['id']}")
                        nv_d  = st.text_area("Descrição", value=t.get("descricao", ""), key=f"ed{t['id']}", height=80)
                        nv_cat = st.selectbox("Categoria", CATS,
                                              index=CATS.index(t.get("categoria","—")) if t.get("categoria","—") in CATS else 0,
                                              key=f"ecat{t['id']}")
                        if is_evento:
                            c1e, c2e = st.columns(2)
                            with c1e:
                                nv_dt = st.date_input(
                                    "Data",
                                    value=date.fromisoformat(t["data"]) if t.get("data") else hoje,
                                    key=f"edt{t['id']}", format="DD/MM/YYYY"
                                )
                            with c2e:
                                nv_p = st.selectbox("Prioridade", PRIOS,
                                                    index=PRIOS.index(t.get("prioridade", "Baixa")),
                                                    key=f"ep{t['id']}")
                        else:
                            nv_p = st.selectbox("Prioridade", PRIOS,
                                                index=PRIOS.index(t.get("prioridade", "Baixa")),
                                                key=f"ep{t['id']}")
                        bs, bc = st.columns(2)
                        with bs:
                            if st.button("💾 Salvar", key=f"sv{t['id']}", use_container_width=True):
                                for x in dados["tarefas"]:
                                    if x["id"] == t["id"]:
                                        upd = {
                                            "titulo": nv_t.strip(),
                                            "descricao": nv_d.strip(),
                                            "categoria": nv_cat,
                                            "prioridade": nv_p,
                                        }
                                        if is_evento:
                                            upd["data"] = str(nv_dt)
                                        x.update(upd)
                                st.session_state["editando"] = None
                                if salvar_dados(dados):
                                    st.rerun()
                        with bc:
                            if st.button("✕ Cancelar", key=f"cc{t['id']}", use_container_width=True):
                                st.session_state["editando"] = None
                                st.rerun()
                    else:
                        row = st.columns([7, 1, 1])
                        with row[0]:
                            st.checkbox(
                                f"**{t['titulo']}**",
                                value=False, key=f"ck{t['id']}",
                                on_change=_marcar_pendente_conclusao, args=("tarefa", t["id"])
                            )
                            cat = t.get("categoria", "—")
                            if t.get("descricao"):
                                st.caption(t["descricao"])
                            if t.get("tipo", "evento") == "evento" and t.get("data"):
                                info = fmt_data(t["data"])
                                if cat and cat != "—":
                                    info += f"  ·  {cat}"
                                st.caption(f"📅 {info}")
                            elif cat and cat != "—":
                                st.caption(cat)
                        with row[1]:
                            st.write("")
                            if st.button("✏️", key=f"e2{t['id']}", use_container_width=True, help="Editar"):
                                st.session_state["editando"] = t["id"]
                                st.rerun()
                        with row[2]:
                            st.write("")
                            if st.button("🗑️", key=f"dl{t['id']}", use_container_width=True, help="Excluir"):
                                dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                                if salvar_dados(dados):
                                    st.rerun()
                    if idx < len(bloco) - 1:
                        st.markdown("<hr class='task-sep'>", unsafe_allow_html=True)

    ca, cm, cb = st.columns(3)
    render_col(ca, "Alta")
    render_col(cm, "Média")
    render_col(cb, "Baixa")


# ════════════════════════════════════════════════════════════════════════════
with tab_fr:
    st.subheader("🧵 Freela")
    st.caption("Lista de tarefas do freela, em ordem: 🔴 Fazer primeiro · 🟢 Fazer depois. "
               "Marque a caixinha quando terminar — a tarefa sai daqui e vai para a aba ✔️ Concluídos.")

    with st.form("form_freela", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns([3, 2, 2])
        with fc1:
            fr_tit = st.text_input("Título *", placeholder="O que precisa ser feito?")
        with fc2:
            fr_prio = st.selectbox("Ordem", FR_PRIOS,
                                   format_func=lambda p: f"{FR_EMOJI[p]} {p}")
        with fc3:
            fr_cat = st.selectbox("Categoria / Marketplace", CATS, key="fr_cat_novo")
        fr_desc = st.text_area("Descrição (opcional)", height=70)
        if st.form_submit_button("➕ Adicionar tarefa de freela",
                                 use_container_width=True, type="primary"):
            if not fr_tit.strip():
                st.warning("Por favor, preencha o título.")
            else:
                dados["freelas"].insert(0, {
                    "id":         str(uuid.uuid4()),
                    "titulo":     fr_tit.strip(),
                    "descricao":  fr_desc.strip(),
                    "prioridade": fr_prio,
                    "categoria":  fr_cat,
                    "feita":      False,
                    "feita_em":   None,
                    "obs_conclusao": "",
                    "criado_em":  datetime.now().isoformat(),
                })
                if salvar_dados(dados):
                    st.rerun()

    st.divider()

    freelas_abertos = aplica_filtro(
        [f for f in dados["freelas"] if not f.get("feita")], filtro_global
    )

    def render_col_freela(col, prio):
        bloco = sorted([f for f in freelas_abertos
                        if f.get("prioridade", FR_PRIOS[0]) == prio],
                       key=lambda x: x.get("criado_em", ""))
        with col:
            with st.container(border=True):
                st.markdown(
                    f"<div style='border-top:4px solid {FR_COR[prio]};border-radius:7px 7px 0 0;"
                    f"margin:-15px -15px 10px -15px;padding:10px 15px;font-weight:700;font-size:0.95rem'>"
                    f"{FR_EMOJI[prio]} {prio} "
                    f"<span style='font-weight:400;font-size:0.8rem;color:#999'>({len(bloco)})</span></div>",
                    unsafe_allow_html=True,
                )
                if not bloco:
                    st.caption("Nenhuma tarefa.")
                for idx, f in enumerate(bloco):
                    row = st.columns([7, 1, 1])
                    with row[0]:
                        st.checkbox(f"**{f['titulo']}**", value=False, key=f"fck{f['id']}",
                                    on_change=_marcar_pendente_conclusao, args=("freela", f["id"]))
                        if f.get("descricao"):
                            st.caption(f["descricao"])
                        if f.get("categoria", "—") != "—":
                            st.caption(f["categoria"])
                    with row[1]:
                        st.write("")
                        if st.button("✏️", key=f"fe{f['id']}", use_container_width=True, help="Editar"):
                            popup_editar_freela(f["id"])
                    with row[2]:
                        st.write("")
                        if st.button("🗑️", key=f"fd{f['id']}", use_container_width=True, help="Excluir"):
                            dados["freelas"] = [x for x in dados["freelas"] if x["id"] != f["id"]]
                            if salvar_dados(dados):
                                st.rerun()
                    if idx < len(bloco) - 1:
                        st.markdown("<hr class='task-sep'>", unsafe_allow_html=True)

    if not freelas_abertos:
        st.info("Nenhuma tarefa de freela em aberto.")
    c_fp, c_fd = st.columns(2)
    render_col_freela(c_fp, FR_PRIOS[0])
    render_col_freela(c_fd, FR_PRIOS[1])

# ════════════════════════════════════════════════════════════════════════════
with tab_ent:
    st.subheader("📦 Entrada de Mercadoria")
    st.caption("Registre toda mercadoria que chegar: dia, fornecedor e se a nota bate com a quantidade recebida.")

    with st.form("form_entrada", clear_on_submit=True):
        ec1, ec2 = st.columns(2)
        with ec1:
            ent_data = st.date_input("Dia que chegou *", value=date.today(), format="DD/MM/YYYY")
        with ec2:
            ent_forn = st.text_input("Fornecedor *", placeholder="Nome do fornecedor")
        ec3, ec4 = st.columns(2)
        with ec3:
            ent_cat = st.selectbox("Categoria / Marketplace", CATS, key="ent_cat_novo")
        with ec4:
            ent_bate = st.selectbox("A nota bate com a quantidade?", NOTA_OPCOES)
        ent_obs = st.text_area("Observação (obrigatório se a nota não bater)", height=70)
        if st.form_submit_button("➕ Registrar entrada", use_container_width=True, type="primary"):
            if not ent_forn.strip():
                st.warning("Por favor, preencha o fornecedor.")
            elif ent_bate == "Não" and not ent_obs.strip():
                st.warning("A nota não bateu — preencha a observação explicando o que houve.")
            else:
                dados["entradas"].insert(0, {
                    "id":          str(uuid.uuid4()),
                    "data":        str(ent_data),
                    "fornecedor":  ent_forn.strip(),
                    "categoria":   ent_cat,
                    "nota_bate":   ent_bate,
                    "observacao":  ent_obs.strip(),
                    "criado_em":   datetime.now().isoformat(),
                })
                if salvar_dados(dados):
                    st.rerun()

    st.divider()

    entradas_lista = sorted(
        aplica_filtro(dados["entradas"], filtro_global),
        key=lambda x: x.get("data", ""), reverse=True
    )

    if not entradas_lista:
        st.info("Nenhuma entrada registrada.")

    for e in entradas_lista:
        with st.container(border=True):
            c1, c2, c3 = st.columns([8, 2, 1])
            with c1:
                bate = e.get("nota_bate", "Sim")
                icone_bate = "✅" if bate == "Sim" else "⚠️"
                st.markdown(f"**{e.get('fornecedor','')}**  ·  📅 {fmt_data(e.get('data',''))}")
                info_ent = f"{icone_bate} Nota bate: {bate}"
                if e.get("categoria", "—") != "—":
                    info_ent += f"  ·  {e['categoria']}"
                st.caption(info_ent)
                if e.get("observacao"):
                    st.caption(f"📝 {e['observacao']}")
            with c2:
                if st.button("✏️", key=f"eed{e['id']}", use_container_width=True, help="Editar"):
                    popup_editar_entrada(e["id"])
            with c3:
                if st.button("🗑️", key=f"edel{e['id']}", use_container_width=True, help="Excluir"):
                    dados["entradas"] = [x for x in dados["entradas"] if x["id"] != e["id"]]
                    if salvar_dados(dados):
                        st.rerun()

# ════════════════════════════════════════════════════════════════════════════
with tab3:
    feitas = aplica_filtro([t for t in dados.get("tarefas", []) if t.get("feita")], filtro_global)
    avisos_concluidos = aplica_filtro([a for a in dados.get("avisos", []) if a.get("concluido")], filtro_global)
    freelas_feitos = aplica_filtro([f for f in dados.get("freelas", []) if f.get("feita")], filtro_global)

    itens = ([("tarefa", t) for t in feitas]
             + [("freela", f) for f in freelas_feitos]
             + [("aviso", a) for a in avisos_concluidos])
    itens.sort(key=lambda x: x[1].get("feita_em") or x[1].get("concluido_em") or "", reverse=True)

    if not itens:
        st.info("Nada concluído ainda.")
    else:
        st.markdown(f"**{len(itens)} concluído(s)**")
        st.divider()
        for tipo, item in itens:
            if tipo == "tarefa":
                t = item
                c1, c2 = st.columns([10, 1], vertical_alignment="center")
                with c1:
                    prio_txt = t.get("prioridade", "")
                    dot = EMOJI.get(prio_txt, "")
                    st.markdown(f"🗹 Tarefa · ~~{t['titulo']}~~  {dot}")
                    feita_em = t.get("feita_em", "")
                    cat = t.get("categoria", "—")
                    info = f"✅ {feita_em}"
                    if cat and cat != "—":
                        info += f"  ·  {cat}"
                    st.caption(info)
                    if t.get("obs_conclusao"):
                        st.caption(f"📝 {t['obs_conclusao']}")
                with c2:
                    if st.button("🗑️", key=f"df{t['id']}", help="Excluir"):
                        dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                        if salvar_dados(dados):
                            st.rerun()
            elif tipo == "freela":
                f = item
                c1, c2 = st.columns([10, 1], vertical_alignment="center")
                with c1:
                    st.markdown(f"🧵 Freela · ~~{f['titulo']}~~")
                    info_f = f"✅ {f.get('feita_em','')}"
                    if f.get("categoria", "—") != "—":
                        info_f += f"  ·  {f['categoria']}"
                    st.caption(info_f)
                    if f.get("obs_conclusao"):
                        st.caption(f"📝 {f['obs_conclusao']}")
                with c2:
                    if st.button("↩️", key=f"reab_fr_{f['id']}", help="Reabrir freela"):
                        f["feita"]    = False
                        f["feita_em"] = None
                        if salvar_dados(dados):
                            st.rerun()
                    if st.button("🗑️", key=f"dfr_{f['id']}", help="Excluir"):
                        dados["freelas"] = [x for x in dados["freelas"] if x["id"] != f["id"]]
                        if salvar_dados(dados):
                            st.rerun()
            else:
                a = item
                c1, c2 = st.columns([10, 1], vertical_alignment="center")
                with c1:
                    st.markdown(f"📢 Aviso · ~~{a['texto']}~~")
                    info_a = f"✅ {a.get('concluido_em','')}  ·  {a.get('autor','')}"
                    if a.get("categoria", "—") != "—":
                        info_a += f"  ·  {a['categoria']}"
                    st.caption(info_a)
                    for r in a.get("respostas", []):
                        st.markdown(f"↳ ~~{r['texto']}~~")
                        st.caption(f"🕐 {r['autor']} · {r['data']}")
                with c2:
                    if st.button("↩️", key=f"reab_av_{a['id']}", help="Reabrir aviso"):
                        a["concluido"] = False
                        a["concluido_em"] = None
                        if salvar_dados(dados):
                            st.rerun()
                    if st.button("🗑️", key=f"dav_c_{a['id']}", help="Excluir aviso"):
                        dados["avisos"] = [x for x in dados["avisos"] if x["id"] != a["id"]]
                        if salvar_dados(dados):
                            st.rerun()
            st.markdown("<hr class='task-sep'>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("📢 Avisos")
    st.caption("Mural de mão dupla — Bruna e a funcionária podem postar e responder.")

    quem = st.selectbox("Você é:", ["Bruna", "Funcionária"], key="quem_sou")

    with st.form("form_aviso", clear_on_submit=True):
        av_txt = st.text_area("Nova mensagem", placeholder="Digite o aviso...")
        av_cat = st.selectbox("Categoria / Marketplace", CATS, key="av_cat_novo")
        if st.form_submit_button("📢 Publicar aviso", use_container_width=True, type="primary"):
            if av_txt.strip():
                dados["avisos"].insert(0, {
                    "id":         str(uuid.uuid4()),
                    "texto":      av_txt.strip(),
                    "autor":      quem,
                    "categoria":  av_cat,
                    "data":       datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "respostas":  [],
                })
                if salvar_dados(dados):
                    st.success("✅ Aviso publicado!")
                    st.rerun()
            else:
                st.warning("Digite uma mensagem antes de publicar.")

    st.divider()

    for a in dados.get("avisos", []):
        a.setdefault("respostas", [])
        a.setdefault("autor", "Bruna")
        a.setdefault("concluido", False)
        a.setdefault("concluido_em", None)
        a.setdefault("categoria", "—")

    abertos = aplica_filtro(
        [a for a in dados.get("avisos", []) if not a.get("concluido")], filtro_global
    )

    if not abertos:
        st.info("Nenhum aviso em aberto.")

    for a in abertos:
        with st.container(border=True):
            c1, c2, c3 = st.columns([8, 2, 1])
            with c1:
                st.markdown(f"**{a['texto']}**")
                info_av = f"🕐 {a['autor']} · {a['data']}"
                if a.get("categoria", "—") != "—":
                    info_av += f"  ·  {a['categoria']}"
                st.caption(info_av)
            with c2:
                if st.button("✅ Concluído", key=f"cc_av_{a['id']}", use_container_width=True,
                             help="Marcar como concluído"):
                    a["concluido"]    = True
                    a["concluido_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    if salvar_dados(dados):
                        st.rerun()
            with c3:
                if st.button("🗑️", key=f"dav{a['id']}", help="Excluir aviso"):
                    dados["avisos"] = [x for x in dados["avisos"] if x["id"] != a["id"]]
                    if salvar_dados(dados):
                        st.rerun()

            for r in a["respostas"]:
                st.markdown(f"↳ **{r['texto']}**")
                st.caption(f"🕐 {r['autor']} · {r['data']}")

            with st.form(f"form_resp_{a['id']}", clear_on_submit=True):
                resp_txt = st.text_input("Responder", placeholder="Escreva uma resposta...",
                                          label_visibility="collapsed")
                if st.form_submit_button("↳ Responder", use_container_width=True):
                    if resp_txt.strip():
                        a["respostas"].append({
                            "id":    str(uuid.uuid4()),
                            "texto": resp_txt.strip(),
                            "autor": quem,
                            "data":  datetime.now().strftime("%d/%m/%Y %H:%M"),
                        })
                        if salvar_dados(dados):
                            st.rerun()

# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("❓ Como usar o painel")
    st.caption("Guia rápido — leia isso antes de começar a usar.")

    with st.expander("📌 As abas principais", expanded=True):
        st.markdown("""
- **✅ Tarefas** — onde você organiza o trabalho do dia. Tem duas partes: o **calendário** (em cima) e as **3 colunas de prioridade** (embaixo: 🔴 Alta, 🟡 Média, 🟢 Baixa).
- **🧵 Freela** — lista de tarefas só do freela, separada das tarefas da loja.
- **📦 Entrada de Mercadoria** — registro de toda mercadoria que chegar (dia, fornecedor, se a nota bate com a quantidade e observação).
- **📢 Avisos** — mural de mão dupla entre Bruna e funcionária. Leia sempre que entrar.
- **✔️ Concluídos** — histórico de tudo que já foi marcado como feito: tarefas, freelas e avisos juntos (cada um com uma etiqueta indicando o tipo: 🗹 Tarefa, 🧵 Freela ou 📢 Aviso).

Tem um **filtro "🔍 Filtrar por marketplace"** na aba Tarefas, logo abaixo do botão "🔄 Atualizar dados" (embaixo do mini-calendário). Ele é único e vale para todas as abas ao mesmo tempo (Tarefas, Freela, Entrada de Mercadoria, Avisos, Concluídos), mesmo aparecendo só nessa aba — escolha uma categoria (ex: "LB Collection - ML") ou deixe em "Todos" para ver tudo.

**Categorias disponíveis:** "—" (sem categoria), "K2 COMÉRCIO", "LB COLLECTION" e "AMBOS (K2 e LB)" (para quando for dos dois juntos) primeiro, depois as combinações por marketplace em ordem alfabética (K2 - AMZ, K2 - ML, K2 - SH, K2 - TK TK, K2 - VD, LB Collection - AMZ, LB Collection - ML, LB Collection - SH, LB Collection - TK TK, LB Collection - VD).
        """)

    with st.expander("📦 Aba Entrada de Mercadoria", expanded=True):
        st.markdown("""
Use sempre que uma mercadoria chegar. Preencha:
- **Dia que chegou** e **Fornecedor** (obrigatórios)
- **Categoria / Marketplace** (opcional, ex: "LB Collection - ML", "K2 - SH")
- **A nota bate com a quantidade?** — Sim ou Não
- **Observação** — vira **obrigatória** se você marcar "Não", para explicar o que faltou ou veio errado

Clique em **➕ Registrar entrada**. Os registros ficam listados abaixo, do mais recente para o mais antigo — use **✏️** para corrigir algo ou **🗑️** para apagar.
        """)

    with st.expander("🧵 Aba Freela", expanded=True):
        st.markdown("""
É uma lista de tarefas à parte, só do freela — o que você cadastra aqui **não** aparece nas colunas de prioridade da aba Tarefas nem no calendário.

São **2 colunas**, que servem só para mostrar a ordem do que fazer:
- 🔴 **Fazer primeiro**
- 🟢 **Fazer depois**

**Para adicionar:** escreva o **Título** (único campo obrigatório), escolha em **Ordem** se é 🔴 ou 🟢, e se quiser preencha a **Descrição**. Depois clique em **➕ Adicionar tarefa de freela**.

**Para marcar como feita:** marque a **caixinha ☐ ao lado do título**. A tarefa sai desta aba na hora e vai para a aba **✔️ Concluídos**, com a etiqueta 🧵 Freela — assim dá para ver que aquilo era do freela e não da loja.

**Outros botões:**
- **✏️** — abre uma janelinha para mudar o título, a descrição ou a ordem (🔴/🟢). Também tem "✅ Marcar feito" lá dentro.
- **🗑️** — apaga de vez, não tem como desfazer.
- Em **✔️ Concluídos**, o **↩️** traz a tarefa de volta para esta aba, caso tenha marcado sem querer.
        """)

    with st.expander("🟢 Tarefa pontual × 📅 Evento — qual a diferença", expanded=True):
        st.markdown("""
Existem **dois jeitos** de adicionar algo no painel, e cada um serve pra uma coisa diferente:

**1. Tarefa pontual** — coisas do dia a dia, sem hora marcada
- Criada clicando em **"➕ Nova tarefa alta/média/baixa"** dentro de uma das 3 colunas
- Só pede: título, categoria, descrição e prioridade — **não pede data**
- Fica só na coluna de prioridade, **não aparece no calendário**
- Use para: tarefas que precisam ser feitas, mas não têm um dia certo (ex: "responder mensagens da Shopee")

**2. Evento** — compromissos com data certa
- Criado clicando no **"➕"** dentro de um dia do calendário
- Pede título, categoria, descrição, **data** e prioridade
- Aparece **no dia certo do calendário** E também na coluna de prioridade (ordenado pela data)
- Use para: coisas com prazo ou data marcada (ex: "enviar produto dia 28/07")

**Resumo:** se tem data certa → cria pelo **calendário**. Se não tem → cria pela **coluna de prioridade**.
        """)

    with st.expander("✏️ Editar, marcar como feita e excluir"):
        st.markdown("""
- **Editar:** clique no lápis ✏️ do lado da tarefa (nas colunas) ou clique em cima do evento (no calendário) — abre um formulário pra alterar.
- **Marcar como feita:** marque a caixinha ☐ do lado do título (tarefa ou freela) — abre uma **janela de confirmação** perguntando se quer mesmo marcar como concluída, com um campo de **Observação** (opcional). Só depois de clicar em **✅ Confirmar** é que a tarefa some da lista e vai para a aba **✔️ Concluídos**. Se clicar em **✕ Cancelar**, nada muda.
- **Excluir:** clique na lixeira 🗑️ — apaga de vez, não tem como desfazer.
        """)

    with st.expander("🔄 Botão 'Atualizar dados'"):
        st.markdown("""
Fica do lado esquerdo, embaixo do mini-calendário. Use se você (ou outra pessoa) acabou de mudar algo em outro celular/computador e a tela não atualizou sozinha — ele busca a versão mais recente salva no servidor.
        """)

    with st.expander("📢 Avisos"):
        st.markdown("""
Qualquer uma das duas (Bruna ou funcionária) pode publicar um aviso e responder a um aviso já existente — é uma conversa registrada, não só um recado de um lado só.

- Antes de postar ou responder, escolha em **"Você é:"** quem está escrevendo — assim fica registrado quem falou o quê.
- Respostas aparecem com **↳** embaixo do aviso original.
- Clique em **"✅ Concluído"** quando o aviso já foi resolvido/conversado — ele vai para a aba **✔️ Concluídos** (junto com as tarefas, marcado como "📢 Aviso"; dá pra reabrir com ↩️ se precisar).
- **Excluir (🗑️)** apaga o aviso inteiro (e as respostas dele) de vez — use só quando não precisar mais guardar aquilo.
        """)
        st.markdown("<hr class='task-sep'>", unsafe_allow_html=True)
