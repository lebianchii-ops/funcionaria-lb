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
.bloco {
    background: #ffffff;
    border-radius: 14px;
    padding: 18px 16px;
    min-height: 320px;
    border-top: 4px solid #ccc;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.bloco-alta  { border-top-color: #e74c3c; }
.bloco-media { border-top-color: #f39c12; }
.bloco-baixa { border-top-color: #27ae60; }
.evento { border-radius: 5px; padding: 3px 7px; margin-bottom: 4px; font-size: 0.75rem; font-weight: 500; }
.evento-alta  { background: #fde8e8; border-left: 3px solid #e74c3c; }
.evento-media { background: #fef9e7; border-left: 3px solid #f39c12; }
.evento-baixa { background: #eafaf1; border-left: 3px solid #27ae60; }
div[data-testid="stButton"] button[kind="secondary"] {
    padding: 2px 6px;
    font-size: 0.7rem;
}
</style>
""", unsafe_allow_html=True)

REPO = "lebianchii-ops/funcionaria-lb"
DATA_FILE = "dados.json"

def get_token():
    t = st.secrets["github_token"]
    return ''.join(c for c in t if ord(c) < 128).strip()

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
    content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
    payload = {"message": f"update {datetime.now().strftime('%d/%m %H:%M')}", "content": content}
    sha = st.session_state.get("sha")
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload)
    if r.status_code in [200, 201]:
        st.session_state["sha"] = r.json()["content"]["sha"]
        return True
    return False

def mini_calendario_html(ano, mes, hoje, datas_com_tarefas):
    nomes_mes = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
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
            e_hoje = d == hoje
            tem_tarefa = str(d) in datas_com_tarefas
            if e_hoje:
                cel = f'<td style="text-align:center;padding:3px"><div style="background:#c0392b;color:white;border-radius:50%;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:0.82rem">{dia}</div></td>'
            elif tem_tarefa:
                cel = (f'<td style="text-align:center;padding:3px">'
                       f'<span style="font-size:0.82rem;font-weight:600;color:#222">{dia}</span>'
                       f'<div style="width:5px;height:5px;background:#e74c3c;border-radius:50%;margin:-1px auto 0"></div>'
                       f'</td>')
            else:
                cel = f'<td style="text-align:center;padding:3px;font-size:0.82rem;color:#444">{dia}</td>'
            linhas += cel
        linhas += "</tr>"

    return f"""
    <div style="background:white;border-radius:14px;padding:14px 12px;box-shadow:0 1px 4px rgba(0,0,0,0.08);font-family:sans-serif;width:100%;box-sizing:border-box">
        <div style="text-align:center;font-weight:700;font-size:0.82rem;margin-bottom:10px">
            {nomes_mes[mes-1].upper()} {ano}
        </div>
        <table style="width:100%;border-collapse:collapse">
            <tr>{''.join(f'<th style="text-align:center;font-size:0.68rem;color:#aaa;font-weight:600;padding-bottom:5px;white-space:nowrap">{d}</th>' for d in ["DOM","SEG","TER","QUA","QUI","SEX","SÁB"])}</tr>
            {linhas}
        </table>
    </div>"""

# ── init ────────────────────────────────────────────────────────────────────
if "dados" not in st.session_state:
    st.session_state["dados"] = carregar_dados()
if "semana_offset" not in st.session_state:
    st.session_state["semana_offset"] = 0
if "mes_offset" not in st.session_state:
    st.session_state["mes_offset"] = 0
if "editando" not in st.session_state:
    st.session_state["editando"] = None
if "data_nova" not in st.session_state:
    st.session_state["data_nova"] = None

dados = st.session_state["dados"]

for t in dados.get("tarefas", []):
    t.setdefault("feita", False)
    t.setdefault("feita_em", None)
    t.setdefault("descricao", "")
    t.setdefault("prioridade", "Baixa")
    t.setdefault("data", str(date.today()))

st.title("👜 LB Collection — Painel")
tab1, tab2 = st.tabs(["✅ Tarefas", "📢 Avisos"])

# ── TAB 1: TAREFAS ──────────────────────────────────────────────────────────
with tab1:

    hoje = date.today()
    offset = st.session_state["semana_offset"]
    inicio_semana = hoje - timedelta(days=(hoje.weekday() + 1) % 7) + timedelta(weeks=offset)
    dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]
    nomes_dia = ["DOM","SEG","TER","QUA","QUI","SEX","SÁB"]
    mes_abrev = ["JAN","FEV","MAR","ABR","MAI","JUN","JUL","AGO","SET","OUT","NOV","DEZ"]

    tarefas_ativas = [t for t in dados.get("tarefas", []) if not t.get("feita")]
    datas_com_tarefas = {t.get("data") for t in tarefas_ativas}

    # ── Navegação única no topo ─────────────────────────────────────────────
    mes_offset = st.session_state["mes_offset"]
    ano_cal = hoje.year
    mes_cal = hoje.month + mes_offset
    while mes_cal > 12:
        mes_cal -= 12; ano_cal += 1
    while mes_cal < 1:
        mes_cal += 12; ano_cal -= 1

    label_semana = (f"{dias_semana[0].day} de {mes_abrev[dias_semana[0].month-1].lower()}. "
                    f"– {dias_semana[6].day} de {mes_abrev[dias_semana[6].month-1].lower()}.")

    nav_col = st.columns([1, 1, 2.5, 1, 6, 1])
    with nav_col[0]:
        if st.button("‹", key="mes_prev", use_container_width=True, help="Mês anterior"):
            st.session_state["mes_offset"] -= 1; st.rerun()
    with nav_col[1]:
        if st.button("›", key="mes_next", use_container_width=True, help="Próximo mês"):
            st.session_state["mes_offset"] += 1; st.rerun()
    with nav_col[2]:
        st.markdown("")  # espaçador
    with nav_col[3]:
        if st.button("‹", key="sem_prev", use_container_width=True, help="Semana anterior"):
            st.session_state["semana_offset"] -= 1; st.rerun()
    with nav_col[4]:
        st.markdown(f"<div style='text-align:center;font-weight:600;padding-top:6px;color:#555'>{label_semana}</div>", unsafe_allow_html=True)
    with nav_col[5]:
        if st.button("›", key="sem_next", use_container_width=True, help="Próxima semana"):
            st.session_state["semana_offset"] += 1; st.rerun()

    # ── Corpo do calendário ─────────────────────────────────────────────────
    col_mini, col_semana = st.columns([2.5, 9])

    with col_mini:
        st.markdown(mini_calendario_html(ano_cal, mes_cal, hoje, datas_com_tarefas), unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("➕ Nova tarefa", use_container_width=True, key="btn_nova_tarefa"):
            st.session_state["data_nova"] = hoje
            st.session_state["abrir_form"] = True

    with col_semana:
        cols_dias = st.columns(7)
        for i, (dia, nome) in enumerate(zip(dias_semana, nomes_dia)):
            with cols_dias[i]:
                e_hoje = dia == hoje
                borda = "border:2px solid #c0392b;" if e_hoje else "border:1px solid #e8e8e8;"
                num_style = ("background:#c0392b;color:white;border-radius:50%;width:28px;height:28px;"
                             "display:inline-flex;align-items:center;justify-content:center;"
                             "font-weight:700;font-size:0.85rem;margin-bottom:6px;") if e_hoje else \
                            "font-size:1.4rem;font-weight:700;margin-bottom:4px;"
                eventos_dia = [t for t in tarefas_ativas if t.get("data") == str(dia)]
                eventos_html = ""
                for t in eventos_dia:
                    dot = {"Alta":"🔴","Média":"🟡","Baixa":"🟢"}.get(t.get("prioridade"),"⚪")
                    titulo = t["titulo"][:15]+"…" if len(t["titulo"])>15 else t["titulo"]
                    cls = {"Alta":"evento-alta","Média":"evento-media","Baixa":"evento-baixa"}.get(t.get("prioridade"),"evento-baixa")
                    eventos_html += f'<div class="evento {cls}">{dot} {titulo}</div>'
                if not eventos_html:
                    eventos_html = '<div style="color:#ccc;font-size:0.72rem;font-style:italic;margin-top:4px">livre</div>'

                st.markdown(f"""
                <div style="{borda}border-radius:10px;padding:10px 8px;min-height:140px;background:white;margin-bottom:6px">
                    <div style="font-size:0.62rem;font-weight:700;color:#aaa;letter-spacing:1px;margin-bottom:2px">{nome} {mes_abrev[dia.month-1]}</div>
                    <div style="{num_style}">{dia.day}</div>
                    {eventos_html}
                </div>""", unsafe_allow_html=True)

                if st.button("＋", key=f"add_dia_{i}", use_container_width=True):
                    st.session_state["data_nova"] = dia
                    st.session_state["abrir_form"] = True
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Formulário de nova tarefa ────────────────────────────────────────────
    data_pre = st.session_state.get("data_nova") or hoje
    abrir = st.session_state.get("abrir_form", False)

    with st.expander("➕ Nova tarefa", expanded=abrir):
        nt_titulo    = st.selectbox("Título", ["TK TK - LB Collection", "SH - LB Collection", "AMZ - LB Collection", "ML - LB Collection"], key="nt_titulo")
        nt_descricao = st.text_area("Descrição", key="nt_descricao")
        c1, c2 = st.columns(2)
        with c1:
            nt_data = st.date_input("Data", value=data_pre, key="nt_data")
        with c2:
            nt_prio = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"], key="nt_prio")
        if st.button("Adicionar tarefa"):
            if nt_titulo:
                dados["tarefas"].append({
                    "id": str(uuid.uuid4()),
                    "titulo": nt_titulo,
                    "descricao": nt_descricao,
                    "data": str(nt_data),
                    "prioridade": nt_prio,
                    "feita": False,
                    "feita_em": None,
                    "criado_em": datetime.now().isoformat()
                })
                st.session_state["data_nova"] = None
                st.session_state["abrir_form"] = False
                if salvar_dados(dados):
                    st.success("Tarefa adicionada!")
                    st.rerun()
            else:
                st.warning("Digite um título.")

    st.divider()

    # ── Colunas de prioridade ───────────────────────────────────────────────
    pendentes = [t for t in dados.get("tarefas", []) if not t.get("feita")]

    cores_borda = {"bloco-alta": "#e74c3c", "bloco-media": "#f39c12", "bloco-baixa": "#27ae60"}

    def render_coluna(col, label, classe, emoji, prioridade):
        with col:
            cor = cores_borda.get(classe, "#ccc")
            st.markdown(f"""
            <div style="border-top:4px solid {cor};border-radius:10px 10px 0 0;background:white;
                        padding:12px 14px 6px 14px;font-size:1rem;font-weight:700;">
                {emoji} {label}
            </div>
            """, unsafe_allow_html=True)
            bloco = sorted([t for t in pendentes if t.get("prioridade") == prioridade], key=lambda x: x.get("data",""))
            st.markdown('<div style="background:white;padding:0 14px 14px 14px;border-radius:0 0 10px 10px;min-height:200px">', unsafe_allow_html=True)
            if not bloco:
                st.caption("Nenhuma tarefa.")
            for t in bloco:
                editando = st.session_state["editando"] == t["id"]
                with st.container():
                    if editando:
                        nt = st.text_input("Título", value=t["titulo"], key=f"et_{t['id']}")
                        nd = st.text_area("Descrição", value=t.get("descricao",""), key=f"ed_{t['id']}")
                        nd2 = st.date_input("Data", value=date.fromisoformat(t["data"]) if t.get("data") else date.today(), key=f"edt_{t['id']}")
                        np = st.selectbox("Prioridade", ["Alta","Média","Baixa"], index=["Alta","Média","Baixa"].index(t.get("prioridade","Baixa")), key=f"ep_{t['id']}")
                        cs, cc = st.columns(2)
                        with cs:
                            if st.button("💾 Salvar", key=f"sv_{t['id']}"):
                                for tarefa in dados["tarefas"]:
                                    if tarefa["id"] == t["id"]:
                                        tarefa.update({"titulo": nt, "descricao": nd, "data": str(nd2), "prioridade": np})
                                st.session_state["editando"] = None
                                salvar_dados(dados)
                                st.rerun()
                        with cc:
                            if st.button("✕", key=f"cc_{t['id']}"):
                                st.session_state["editando"] = None
                                st.rerun()
                    else:
                        feita = st.checkbox(f"**{t['titulo']}**", value=False, key=f"ck_{t['id']}")
                        if t.get("descricao"):
                            st.caption(t["descricao"])
                        st.caption(f"📅 {t['data']}")
                        if feita:
                            for tarefa in dados["tarefas"]:
                                if tarefa["id"] == t["id"]:
                                    tarefa["feita"] = True
                                    tarefa["feita_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                            salvar_dados(dados)
                            st.rerun()
                        ce, cd = st.columns(2)
                        with ce:
                            if st.button("✏️", key=f"ed2_{t['id']}", use_container_width=True):
                                st.session_state["editando"] = t["id"]
                                st.rerun()
                        with cd:
                            if st.button("🗑️", key=f"dl_{t['id']}", use_container_width=True):
                                dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                                salvar_dados(dados)
                                st.rerun()
                    st.markdown("<hr style='margin:6px 0;border-color:#f0f0f0'>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    col_a, col_m, col_b = st.columns(3)
    render_coluna(col_a, "Alta",  "bloco-alta",  "🔴", "Alta")
    render_coluna(col_m, "Média", "bloco-media", "🟡", "Média")
    render_coluna(col_b, "Baixa", "bloco-baixa", "🟢", "Baixa")

    feitas = sorted([t for t in dados.get("tarefas", []) if t.get("feita")], key=lambda x: x.get("feita_em",""), reverse=True)
    if feitas:
        st.divider()
        with st.expander(f"✅ Feitas ({len(feitas)})"):
            for t in feitas:
                c1, c2 = st.columns([9, 1])
                with c1:
                    st.markdown(f"~~{t['titulo']}~~")
                    st.caption(f"Concluída em {t.get('feita_em','')} · {t.get('prioridade','')}")
                with c2:
                    if st.button("🗑️", key=f"df_{t['id']}"):
                        dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                        salvar_dados(dados)
                        st.rerun()

# ── TAB 2: AVISOS ────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Avisos")
    with st.expander("➕ Novo aviso"):
        texto_aviso = st.text_area("Mensagem", key="av_texto")
        if st.button("Publicar"):
            if texto_aviso:
                dados["avisos"].insert(0, {
                    "id": str(uuid.uuid4()),
                    "texto": texto_aviso,
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                if salvar_dados(dados):
                    st.success("Aviso publicado!")
                    st.rerun()
            else:
                st.warning("Digite uma mensagem.")
    for a in dados.get("avisos", []):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"📢 {a['texto']}")
            st.caption(a["data"])
        with c2:
            if st.button("🗑️", key=f"dav_{a['id']}"):
                dados["avisos"] = [x for x in dados["avisos"] if x["id"] != a["id"]]
                salvar_dados(dados)
                st.rerun()
        st.divider()
