import streamlit as st
import json
import requests
import base64
from datetime import datetime, date
import uuid

st.set_page_config(
    page_title="LB Collection — Painel",
    page_icon="👜",
    layout="wide"
)

REPO = "lebianchii-ops/funcionaria-lb"
DATA_FILE = "dados.json"

def get_token():
    return st.secrets["github_token"]

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

st.title("👜 LB Collection — Painel")

tab1, tab2, tab3 = st.tabs(["✅ Tarefas", "📅 Calendário", "📢 Avisos"])

with tab1:
    st.subheader("Tarefas")

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
                    "status": "Pendente",
                    "criado_em": datetime.now().isoformat()
                }
                dados["tarefas"].append(nova)
                if salvar_dados(dados):
                    st.success("Tarefa adicionada!")
                    st.rerun()
            else:
                st.warning("Digite um título para a tarefa.")

    filtro = st.selectbox("Filtrar por status", ["Todas", "Pendente", "Em andamento", "Feita"])

    tarefas = dados.get("tarefas", [])
    if filtro != "Todas":
        tarefas = [t for t in tarefas if t["status"] == filtro]
    tarefas = sorted(tarefas, key=lambda x: x.get("data", ""))

    if not tarefas:
        st.info("Nenhuma tarefa encontrada.")

    for t in tarefas:
        cor = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}.get(t["prioridade"], "⚪")
        status_icone = {"Pendente": "⏳", "Em andamento": "🔄", "Feita": "✅"}.get(t["status"], "")

        with st.container():
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.markdown(f"{cor} **{t['titulo']}** {status_icone}")
                if t.get("descricao"):
                    st.caption(t["descricao"])
                st.caption(f"📅 {t['data']} · {t['prioridade']}")
            with col2:
                opcoes = ["Pendente", "Em andamento", "Feita"]
                idx = opcoes.index(t["status"]) if t["status"] in opcoes else 0
                novo_status = st.selectbox("Status", opcoes, index=idx, key=f"status_{t['id']}", label_visibility="collapsed")
                if novo_status != t["status"]:
                    for tarefa in dados["tarefas"]:
                        if tarefa["id"] == t["id"]:
                            tarefa["status"] = novo_status
                    salvar_dados(dados)
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_{t['id']}"):
                    dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                    salvar_dados(dados)
                    st.rerun()
            st.divider()

with tab2:
    st.subheader("Calendário")
    data_sel = st.date_input("Selecionar data", value=date.today(), key="cal_date")
    tarefas_dia = [t for t in dados.get("tarefas", []) if t.get("data") == str(data_sel)]

    if tarefas_dia:
        for t in tarefas_dia:
            cor = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}.get(t["prioridade"], "⚪")
            status_icone = {"Pendente": "⏳", "Em andamento": "🔄", "Feita": "✅"}.get(t["status"], "")
            st.markdown(f"{cor} **{t['titulo']}** {status_icone}")
            if t.get("descricao"):
                st.caption(t["descricao"])
            st.divider()
    else:
        st.info("Nenhuma tarefa para esta data.")

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
