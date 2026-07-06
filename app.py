import streamlit as st
import json
import requests
import base64
from datetime import datetime, date, timedelta
import uuid

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
.bloco-titulo { font-size: 1rem; font-weight: 700; margin-bottom: 12px; }
.cal-header {
    text-align: center;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    color: #888;
    margin-bottom: 2px;
}
.cal-num { text-align: center; font-size: 1.6rem; font-weight: 700; margin-bottom: 6px; }
.cal-num-hoje {
    background: #c0392b;
    color: white;
    border-radius: 50%;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 6px auto;
    font-size: 1.1rem;
}
.cal-card {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 8px 10px;
    min-height: 130px;
}
.cal-card-hoje { border: 2px solid #c0392b; }
.evento {
    border-radius: 5px;
    padding: 3px 7px;
    margin-bottom: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.evento-alta  { background: #fde8e8; border-left: 3px solid #e74c3c; }
.evento-media { background: #fef9e7; border-left: 3px solid #f39c12; }
.evento-baixa { background: #eafaf1; border-left: 3px solid #27ae60; }
.livre { color: #bbb; font-size: 0.75rem; font-style: italic; }
hr.col-sep { border: none; border-left: 1px solid #eee; height: 100%; }
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

# ── init ────────────────────────────────────────────────────────────────────
if "dados" not in st.session_state:
    st.session_state["dados"] = carregar_dados()
if "semana_offset" not in st.session_state:
    st.session_state["semana_offset"] = 0
if "editando" not in st.session_state:
    st.session_state["editando"] = None

dados = st.session_state["dados"]

# garante campos obrigatórios em tarefas antigas
for t in dados.get("tarefas", []):
    t.setdefault("feita", False)
    t.setdefault("feita_em", None)
    t.setdefault("descricao", "")
    t.setdefault("prioridade", "Baixa")
    t.setdefault("data", str(date.today()))

st.title("👜 LB Collection — Painel")
tab1, tab2, tab3 = st.tabs(["✅ Tarefas", "📅 Calendário", "📢 Avisos"])

# ── TAB 1: TAREFAS ──────────────────────────────────────────────────────────
with tab1:

    # ── Calendário semanal ──────────────────────────────────────────────────
    hoje = date.today()
    offset = st.session_state["semana_offset"]
    inicio = hoje - timedelta(days=hoje.weekday()) + timedelta(weeks=offset)
    dias = [inicio + timedelta(days=i) for i in range(7)]
    nomes = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    mes_nome = ["JAN","FEV","MAR","ABR","MAI","JUN","JUL","AGO","SET","OUT","NOV","DEZ"]

    col_prev, col_titulo, col_next = st.columns([1, 6, 1])
    with col_prev:
        if st.button("‹", use_container_width=True):
            st.session_state["semana_offset"] -= 1
            st.rerun()
    with col_titulo:
        label_inicio = f"{dias[0].day} de {mes_nome[dias[0].month-1].lower()}."
        label_fim    = f"{dias[6].day} de {mes_nome[dias[6].month-1].lower()}."
        st.markdown(f"<div style='text-align:center;font-weight:600;padding-top:6px'>{label_inicio} – {label_fim}</div>", unsafe_allow_html=True)
    with col_next:
        if st.button("›", use_container_width=True):
            st.session_state["semana_offset"] += 1
            st.rerun()

    tarefas_ativas = [t for t in dados.get("tarefas", []) if not t.get("feita")]
    cols_cal = st.columns(7)
    for i, (dia, nome) in enumerate(zip(dias, nomes)):
        with cols_cal[i]:
            e_hoje = dia == hoje
            cls_card = "cal-card cal-card-hoje" if e_hoje else "cal-card"
            num_html = f'<div class="cal-num-hoje">{dia.day}</div>' if e_hoje else f'<div class="cal-num">{dia.day}</div>'
            eventos_dia = [t for t in tarefas_ativas if t.get("data") == str(dia)]
            eventos_html = ""
            for t in eventos_dia:
                cls_ev = {"Alta": "evento-alta", "Média": "evento-media", "Baixa": "evento-baixa"}.get(t.get("prioridade"), "evento-baixa")
                titulo_ev = t["titulo"][:22] + "…" if len(t["titulo"]) > 22 else t["titulo"]
                eventos_html += f'<div class="evento {cls_ev}">{titulo_ev}</div>'
            if not eventos_html:
                eventos_html = '<div class="livre">livre</div>'
            st.markdown(f"""
            <div class="{cls_card}">
                <div class="cal-header">{nome} {mes_nome[dia.month-1]}</div>
                {num_html}
                {eventos_html}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Nova tarefa ─────────────────────────────────────────────────────────
    with st.expander("➕ Nova tarefa"):
        nt_titulo    = st.text_input("Título", key="nt_titulo")
        nt_descricao = st.text_area("Descrição", key="nt_descricao")
        c1, c2 = st.columns(2)
        with c1:
            nt_data = st.date_input("Data", value=date.today(), key="nt_data")
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
                if salvar_dados(dados):
                    st.success("Tarefa adicionada!")
                    st.rerun()
            else:
                st.warning("Digite um título.")

    # ── Colunas de prioridade ───────────────────────────────────────────────
    pendentes = [t for t in dados.get("tarefas", []) if not t.get("feita")]

    def render_coluna(col, label, classe, emoji, prioridade):
        with col:
            st.markdown(f'<div class="bloco {classe}"><div class="bloco-titulo">{emoji} {label}</div></div>', unsafe_allow_html=True)
            bloco = sorted([t for t in pendentes if t.get("prioridade") == prioridade], key=lambda x: x.get("data",""))

            if not bloco:
                st.caption("Nenhuma tarefa.")

            for t in bloco:
                editando_este = st.session_state["editando"] == t["id"]

                with st.container():
                    if editando_este:
                        novo_titulo = st.text_input("Título", value=t["titulo"], key=f"e_titulo_{t['id']}")
                        novo_desc   = st.text_area("Descrição", value=t.get("descricao",""), key=f"e_desc_{t['id']}")
                        novo_data   = st.date_input("Data", value=date.fromisoformat(t["data"]) if t.get("data") else date.today(), key=f"e_data_{t['id']}")
                        novo_prio   = st.selectbox("Prioridade", ["Alta","Média","Baixa"], index=["Alta","Média","Baixa"].index(t.get("prioridade","Baixa")), key=f"e_prio_{t['id']}")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("💾 Salvar", key=f"salvar_{t['id']}"):
                                for tarefa in dados["tarefas"]:
                                    if tarefa["id"] == t["id"]:
                                        tarefa["titulo"]    = novo_titulo
                                        tarefa["descricao"] = novo_desc
                                        tarefa["data"]      = str(novo_data)
                                        tarefa["prioridade"]= novo_prio
                                st.session_state["editando"] = None
                                salvar_dados(dados)
                                st.rerun()
                        with c2:
                            if st.button("✕ Cancelar", key=f"cancel_{t['id']}"):
                                st.session_state["editando"] = None
                                st.rerun()
                    else:
                        feita = st.checkbox(f"**{t['titulo']}**", value=False, key=f"check_{t['id']}")
                        if t.get("descricao"):
                            st.caption(t["descricao"])
                        st.caption(f"📅 {t['data']}")
                        if feita:
                            for tarefa in dados["tarefas"]:
                                if tarefa["id"] == t["id"]:
                                    tarefa["feita"]    = True
                                    tarefa["feita_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                            salvar_dados(dados)
                            st.rerun()
                        ce, cd = st.columns([1, 1])
                        with ce:
                            if st.button("✏️ Editar", key=f"edit_{t['id']}", use_container_width=True):
                                st.session_state["editando"] = t["id"]
                                st.rerun()
                        with cd:
                            if st.button("🗑️ Apagar", key=f"del_{t['id']}", use_container_width=True):
                                dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                                salvar_dados(dados)
                                st.rerun()
                    st.markdown("<hr style='margin:6px 0;border-color:#f0f0f0'>", unsafe_allow_html=True)

    col_a, sep1, col_m, sep2, col_b = st.columns([10, 0.3, 10, 0.3, 10])
    with sep1:
        st.markdown("<div style='border-left:1px solid #e0e0e0;height:100%;min-height:300px'></div>", unsafe_allow_html=True)
    with sep2:
        st.markdown("<div style='border-left:1px solid #e0e0e0;height:100%;min-height:300px'></div>", unsafe_allow_html=True)

    render_coluna(col_a, "Alta",  "bloco-alta",  "🔴", "Alta")
    render_coluna(col_m, "Média", "bloco-media", "🟡", "Média")
    render_coluna(col_b, "Baixa", "bloco-baixa", "🟢", "Baixa")

    # ── Feitas ──────────────────────────────────────────────────────────────
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
                    if st.button("🗑️", key=f"del_f_{t['id']}"):
                        dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                        salvar_dados(dados)
                        st.rerun()

# ── TAB 2: CALENDÁRIO ────────────────────────────────────────────────────────
with tab2:
    st.subheader("Calendário")
    data_sel = st.date_input("Selecionar data", value=date.today(), key="cal_date")
    tarefas_dia = [t for t in dados.get("tarefas", []) if t.get("data") == str(data_sel)]

    if tarefas_dia:
        for t in tarefas_dia:
            cor = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}.get(t.get("prioridade"), "⚪")
            feita_label = " ✅" if t.get("feita") else ""
            st.markdown(f"{cor} **{t['titulo']}**{feita_label}")
            if t.get("descricao"):
                st.caption(t["descricao"])
            if t.get("feita_em"):
                st.caption(f"Concluída em {t['feita_em']}")
            st.divider()
    else:
        st.info("Nenhuma tarefa para esta data.")

# ── TAB 3: AVISOS ────────────────────────────────────────────────────────────
with tab3:
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
            if st.button("🗑️", key=f"del_av_{a['id']}"):
                dados["avisos"] = [x for x in dados["avisos"] if x["id"] != a["id"]]
                salvar_dados(dados)
                st.rerun()
        st.divider()
