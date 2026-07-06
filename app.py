import streamlit as st
import json
import requests
import base64
from datetime import datetime, date, timedelta
import uuid

st.set_page_config(
    page_title="LB Collection — Painel",
    page_icon="👜",
    layout="wide"
)

REPO = "lebianchii-ops/funcionaria-lb"
DATA_FILE = "dados.json"

def get_token():
    token = st.secrets["github_token"]
    return ''.join(c for c in token if ord(c) < 128).strip()

def carregar_dados():
    token = get_token()
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/{REPO}/contents/{DATA_FILE}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()
        data = json.loads(base64.b64decode(content["content"]).decode())
        st.session_state["sha"] = content["sha"]
        return data
    return {"tarefas": [], "avisos": []}

def salvar_dados(data):
    token = get_token()
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/{REPO}/contents/{DATA_FILE}"
    content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
    payload = {
        "message": f"dados atualizados {datetime.now().strftime('%d/%m %H:%M')}",
        "content": content,
    }
    sha = st.session_state.get("sha")
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload)
    if r.status_code in [200, 201]:
        st.session_state["sha"] = r.json()["content"]["sha"]
        return True
    return False

if "dados" not in st.session_state:
    st.session_state["dados"] = carregar_dados()

dados = st.session_state["dados"]

# garante que tarefas antigas sem campo "feita" funcionem
for t in dados.get("tarefas", []):
    t.setdefault("feita", False)
    t.setdefault("feita_em", None)

st.title("👜 LB Collection — Painel")

tab1, tab2, tab3 = st.tabs(["✅ Tarefas", "📅 Calendário", "📢 Avisos"])

# ── TAB 1: TAREFAS ──────────────────────────────────────────────────────────
with tab1:

    # Calendário semanal no topo
    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())  # segunda-feira
    dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]
    nomes_dia = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    tarefas_ativas = [t for t in dados.get("tarefas", []) if not t.get("feita")]

    st.markdown("#### 📅 Semana atual")
    cols_cal = st.columns(7)
    for i, (dia, nome) in enumerate(zip(dias_semana, nomes_dia)):
        with cols_cal[i]:
            is_hoje = dia == hoje
            cabecalho = f"**{'🔵 ' if is_hoje else ''}{nome}**"
            st.markdown(cabecalho)
            st.markdown(f"**{dia.day}**")
            tarefas_dia = [t for t in tarefas_ativas if t.get("data") == str(dia)]
            if tarefas_dia:
                for t in tarefas_dia:
                    cor = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}.get(t.get("prioridade"), "⚪")
                    st.markdown(f"{cor} {t['titulo']}")
            else:
                st.caption("livre")

    st.divider()

    # Nova tarefa
    with st.expander("➕ Nova tarefa"):
        titulo = st.text_input("Título")
        descricao = st.text_area("Descrição")
        col1, col2 = st.columns(2)
        with col1:
            data_tarefa = st.date_input("Data", value=date.today())
        with col2:
            prioridade = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"])

        if st.button("Adicionar"):
            if titulo:
                nova = {
                    "id": str(uuid.uuid4()),
                    "titulo": titulo,
                    "descricao": descricao,
                    "data": str(data_tarefa),
                    "prioridade": prioridade,
                    "feita": False,
                    "feita_em": None,
                    "criado_em": datetime.now().isoformat()
                }
                dados["tarefas"].append(nova)
                if salvar_dados(dados):
                    st.success("Tarefa adicionada!")
                    st.rerun()
            else:
                st.warning("Digite um título para a tarefa.")

    # Blocos de prioridade lado a lado
    def render_bloco(col, label, emoji, bloco):
        with col:
            st.markdown(f"### {emoji} {label}")
            if not bloco:
                st.caption("Nenhuma tarefa.")
            for t in bloco:
                c1, c2 = st.columns([7, 1])
                with c1:
                    feita = st.checkbox(
                        f"**{t['titulo']}**",
                        value=False,
                        key=f"check_{t['id']}"
                    )
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
                with c2:
                    if st.button("🗑️", key=f"del_{t['id']}"):
                        dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                        salvar_dados(dados)
                        st.rerun()

    pendentes = [t for t in dados.get("tarefas", []) if not t.get("feita")]
    col_a, col_m, col_b = st.columns(3)
    render_bloco(col_a, "Alta",  "🔴", sorted([t for t in pendentes if t.get("prioridade") == "Alta"],  key=lambda x: x.get("data", "")))
    render_bloco(col_m, "Média", "🟡", sorted([t for t in pendentes if t.get("prioridade") == "Média"], key=lambda x: x.get("data", "")))
    render_bloco(col_b, "Baixa", "🟢", sorted([t for t in pendentes if t.get("prioridade") == "Baixa"], key=lambda x: x.get("data", "")))

    # Feitas
    feitas = sorted([t for t in dados.get("tarefas", []) if t.get("feita")], key=lambda x: x.get("feita_em", ""), reverse=True)
    if feitas:
        st.divider()
        with st.expander(f"✅ Feitas ({len(feitas)})"):
            for t in feitas:
                c1, c2 = st.columns([8, 1])
                with c1:
                    st.markdown(f"~~{t['titulo']}~~")
                    st.caption(f"Concluída em {t.get('feita_em', '')} · {t.get('prioridade', '')}")
                with c2:
                    if st.button("🗑️", key=f"del_feita_{t['id']}"):
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
        texto_aviso = st.text_area("Mensagem")
        if st.button("Publicar"):
            if texto_aviso:
                aviso = {
                    "id": str(uuid.uuid4()),
                    "texto": texto_aviso,
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                dados["avisos"].insert(0, aviso)
                if salvar_dados(dados):
                    st.success("Aviso publicado!")
                    st.rerun()
            else:
                st.warning("Digite uma mensagem.")

    for a in dados.get("avisos", []):
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"📢 {a['texto']}")
                st.caption(a["data"])
            with col2:
                if st.button("🗑️", key=f"del_aviso_{a['id']}"):
                    dados["avisos"] = [x for x in dados["avisos"] if x["id"] != a["id"]]
                    salvar_dados(dados)
                    st.rerun()
            st.divider()
