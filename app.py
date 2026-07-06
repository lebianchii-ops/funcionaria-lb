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
.bloco-header {
    background: white;
    border-radius: 12px 12px 0 0;
    padding: 12px 14px 8px 14px;
    font-size: 1rem;
    font-weight: 700;
    border-top: 4px solid #ccc;
    box-shadow: 0 1px 0 #f0f0f0;
}
.bloco-header-alta  { border-top-color: #e74c3c; }
.bloco-header-media { border-top-color: #f39c12; }
.bloco-header-baixa { border-top-color: #27ae60; }
.bloco-body {
    background: white;
    border-radius: 0 0 12px 12px;
    padding: 8px 14px 14px 14px;
    min-height: 220px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

REPO = "lebianchii-ops/funcionaria-lb"
DATA_FILE = "dados.json"
MES_NOME = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
            "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
MES_ABREV = ["JAN","FEV","MAR","ABR","MAI","JUN","JUL","AGO","SET","OUT","NOV","DEZ"]

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
            e_hoje = d == hoje
            tem = str(d) in datas_tarefas
            td = 'style="padding:3px 2px;white-space:nowrap;text-align:center"'
            if e_hoje:
                linhas += f'<td {td}><div style="background:#c0392b;color:#fff;border-radius:50%;width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:0.78rem;margin:auto">{dia}</div></td>'
            elif tem:
                linhas += (f'<td {td} style="padding:3px 2px;white-space:nowrap;text-align:center;position:relative">'
                           f'<span style="font-size:0.78rem;font-weight:600">{dia}</span>'
                           f'<span style="position:absolute;bottom:1px;left:50%;transform:translateX(-50%);width:4px;height:4px;background:#e74c3c;border-radius:50%;display:block"></span>'
                           f'</td>')
            else:
                linhas += f'<td {td}><span style="font-size:0.78rem;color:#555">{dia}</span></td>'
        linhas += "</tr>"
    cabecalhos = "".join(
        f'<th style="font-size:0.65rem;color:#aaa;font-weight:600;padding:0 4px 6px;white-space:nowrap">{d}</th>'
        for d in ["D","S","T","Q","Q","S","S"])
    return f"""
    <div style="background:white;border-radius:12px;padding:14px 10px;
                box-shadow:0 1px 4px rgba(0,0,0,0.08);font-family:sans-serif;text-align:center;overflow:hidden">
      <div style="font-weight:700;font-size:0.82rem;margin-bottom:10px">{MES_NOME[mes-1].upper()} {ano}</div>
      <table style="width:100%;border-collapse:collapse">
        <tr>{cabecalhos}</tr>{linhas}
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
        cor_borda = {"Alta":"#e74c3c","Média":"#f39c12","Baixa":"#27ae60"}.get(t.get("prioridade"),"#ccc")
        cor_bg    = {"Alta":"#fde8e8","Média":"#fef9e7","Baixa":"#eafaf1"}.get(t.get("prioridade"),"#f5f5f5")
        dot       = {"Alta":"🔴","Média":"🟡","Baixa":"🟢"}.get(t.get("prioridade"),"⚪")
        titulo = t["titulo"][:13]+"…" if len(t["titulo"])>13 else t["titulo"]
        ev_html += (f'<div style="background:{cor_bg};border-left:3px solid {cor_borda};'
                    f'border-radius:4px;padding:3px 6px;margin-top:4px;font-size:0.72rem;font-weight:500">'
                    f'{dot} {titulo}</div>')
    if not ev_html:
        ev_html = '<div style="color:#ccc;font-size:0.7rem;font-style:italic;margin-top:6px">livre</div>'
    return f"""
    <div style="border:{borda};border-radius:10px;padding:10px 8px;
                min-height:140px;background:white;height:100%">
      <div style="font-size:0.6rem;font-weight:700;color:#aaa;letter-spacing:1px;margin-bottom:4px">{nome} {MES_ABREV[dia.month-1]}</div>
      {num}
      {ev_html}
    </div>"""

# ── session state ────────────────────────────────────────────────────────────
for key, val in [("dados", None), ("semana_offset", 0), ("mes_offset", 0),
                 ("editando", None), ("data_nova", None), ("abrir_form", False)]:
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state["dados"] is None:
    st.session_state["dados"] = carregar_dados()

dados = st.session_state["dados"]
for t in dados.get("tarefas", []):
    t.setdefault("feita", False); t.setdefault("feita_em", None)
    t.setdefault("descricao", ""); t.setdefault("prioridade", "Baixa")
    t.setdefault("data", str(date.today()))

# ── cabeçalho ────────────────────────────────────────────────────────────────
st.title("👜 LB Collection — Painel")
tab1, tab2 = st.tabs(["✅ Tarefas", "📢 Avisos"])

# ════════════════════════════════════════════════════════════════════════════
with tab1:
    hoje = date.today()

    # calcular semana e mês exibidos
    sem_off = st.session_state["semana_offset"]
    mes_off = st.session_state["mes_offset"]
    inicio_sem = hoje - timedelta(days=(hoje.weekday()+1) % 7) + timedelta(weeks=sem_off)
    dias_sem = [inicio_sem + timedelta(days=i) for i in range(7)]
    nomes_dia = ["DOM","SEG","TER","QUA","QUI","SEX","SÁB"]

    ano_cal = hoje.year
    mes_cal = hoje.month + mes_off
    while mes_cal > 12: mes_cal -= 12; ano_cal += 1
    while mes_cal < 1:  mes_cal += 12; ano_cal -= 1

    tarefas_ativas = [t for t in dados.get("tarefas",[]) if not t.get("feita")]
    datas_tarefas  = {t.get("data") for t in tarefas_ativas}

    # ── linha de controles ───────────────────────────────────────────────────
    # [‹mes] [›mes] [espaço mini-cal] [‹sem] [label semana] [›sem] [➕nova]
    c = st.columns([1, 1, 4, 1, 5, 1, 2])
    with c[0]:
        if st.button("‹", key="mp", help="Mês anterior"):
            st.session_state["mes_offset"] -= 1; st.rerun()
    with c[1]:
        if st.button("›", key="mn", help="Próximo mês"):
            st.session_state["mes_offset"] += 1; st.rerun()
    with c[3]:
        if st.button("‹", key="sp", help="Semana anterior"):
            st.session_state["semana_offset"] -= 1; st.rerun()
    with c[4]:
        label = (f"{dias_sem[0].day} de {MES_ABREV[dias_sem[0].month-1].lower()}. "
                 f"– {dias_sem[6].day} de {MES_ABREV[dias_sem[6].month-1].lower()}.")
        st.markdown(f"<p style='text-align:center;font-weight:600;margin:6px 0 0'>{label}</p>", unsafe_allow_html=True)
    with c[5]:
        if st.button("›", key="sn", help="Próxima semana"):
            st.session_state["semana_offset"] += 1; st.rerun()
    with c[6]:
        if st.button("➕ Nova tarefa", use_container_width=True):
            st.session_state["data_nova"] = hoje
            st.session_state["abrir_form"] = True

    # ── corpo do calendário ──────────────────────────────────────────────────
    col_mini, col_sem = st.columns([2, 9])

    with col_mini:
        st.markdown(html_mini_cal(ano_cal, mes_cal, hoje, datas_tarefas), unsafe_allow_html=True)

    with col_sem:
        cols_d = st.columns(7)
        for i, (dia, nome) in enumerate(zip(dias_sem, nomes_dia)):
            eventos_dia = [t for t in tarefas_ativas if t.get("data") == str(dia)]
            with cols_d[i]:
                st.markdown(html_dia(dia, nome, eventos_dia, dia == hoje), unsafe_allow_html=True)
                if st.button("＋", key=f"ad{i}", use_container_width=True):
                    st.session_state["data_nova"] = dia
                    st.session_state["abrir_form"] = True
                    st.rerun()

    st.divider()

    # ── formulário nova tarefa ───────────────────────────────────────────────
    data_pre = st.session_state.get("data_nova") or hoje
    with st.expander("➕ Nova tarefa", expanded=st.session_state.get("abrir_form", False)):
        nt_titulo = st.selectbox("Marketplace", ["TK TK - LB Collection","SH - LB Collection",
                                                  "AMZ - LB Collection","ML - LB Collection"], key="nt_t")
        nt_desc   = st.text_area("Descrição", key="nt_d")
        fc1, fc2  = st.columns(2)
        with fc1: nt_data = st.date_input("Data", value=data_pre, key="nt_dt")
        with fc2: nt_prio = st.selectbox("Prioridade", ["Alta","Média","Baixa"], key="nt_p")
        if st.button("Adicionar"):
            if nt_titulo:
                dados["tarefas"].append({
                    "id": str(uuid.uuid4()), "titulo": nt_titulo, "descricao": nt_desc,
                    "data": str(nt_data), "prioridade": nt_prio,
                    "feita": False, "feita_em": None, "criado_em": datetime.now().isoformat()
                })
                st.session_state.update({"data_nova": None, "abrir_form": False})
                if salvar_dados(dados):
                    st.success("Tarefa adicionada!")
                    st.rerun()

    st.divider()

    # ── colunas de prioridade ────────────────────────────────────────────────
    pendentes = [t for t in dados.get("tarefas",[]) if not t.get("feita")]
    COR = {"Alta":"#e74c3c","Média":"#f39c12","Baixa":"#27ae60"}
    EMOJI = {"Alta":"🔴","Média":"🟡","Baixa":"🟢"}

    def render_col(col, prio):
        bloco = sorted([t for t in pendentes if t.get("prioridade")==prio], key=lambda x: x.get("data",""))
        with col:
            st.markdown(f'<div class="bloco-header bloco-header-{prio.lower()}">{EMOJI[prio]} {prio}</div>', unsafe_allow_html=True)
            st.markdown('<div class="bloco-body">', unsafe_allow_html=True)
            if not bloco:
                st.caption("Nenhuma tarefa.")
            for t in bloco:
                ed = st.session_state["editando"] == t["id"]
                with st.container():
                    if ed:
                        nv_t  = st.text_input("Título", value=t["titulo"], key=f"et{t['id']}")
                        nv_d  = st.text_area("Descrição", value=t.get("descricao",""), key=f"ed{t['id']}")
                        nv_dt = st.date_input("Data", value=date.fromisoformat(t["data"]) if t.get("data") else hoje, key=f"edt{t['id']}")
                        nv_p  = st.selectbox("Prioridade", ["Alta","Média","Baixa"],
                                             index=["Alta","Média","Baixa"].index(t.get("prioridade","Baixa")),
                                             key=f"ep{t['id']}")
                        bs, bc = st.columns(2)
                        with bs:
                            if st.button("💾 Salvar", key=f"sv{t['id']}"):
                                for x in dados["tarefas"]:
                                    if x["id"] == t["id"]:
                                        x.update({"titulo":nv_t,"descricao":nv_d,"data":str(nv_dt),"prioridade":nv_p})
                                st.session_state["editando"] = None
                                salvar_dados(dados); st.rerun()
                        with bc:
                            if st.button("✕", key=f"cc{t['id']}"):
                                st.session_state["editando"] = None; st.rerun()
                    else:
                        feita = st.checkbox(f"**{t['titulo']}**", value=False, key=f"ck{t['id']}")
                        if t.get("descricao"): st.caption(t["descricao"])
                        st.caption(f"📅 {t['data']}")
                        if feita:
                            for x in dados["tarefas"]:
                                if x["id"] == t["id"]:
                                    x["feita"] = True; x["feita_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                            salvar_dados(dados); st.rerun()
                        be, bd = st.columns(2)
                        with be:
                            if st.button("✏️", key=f"e2{t['id']}", use_container_width=True):
                                st.session_state["editando"] = t["id"]; st.rerun()
                        with bd:
                            if st.button("🗑️", key=f"dl{t['id']}", use_container_width=True):
                                dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                                salvar_dados(dados); st.rerun()
                    st.markdown("<hr style='margin:5px 0;border-color:#f5f5f5'>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    ca, cm, cb = st.columns(3)
    render_col(ca, "Alta"); render_col(cm, "Média"); render_col(cb, "Baixa")

    # feitas
    feitas = sorted([t for t in dados.get("tarefas",[]) if t.get("feita")],
                    key=lambda x: x.get("feita_em",""), reverse=True)
    if feitas:
        st.divider()
        with st.expander(f"✅ Feitas ({len(feitas)})"):
            for t in feitas:
                c1, c2 = st.columns([9,1])
                with c1:
                    st.markdown(f"~~{t['titulo']}~~")
                    st.caption(f"Concluída em {t.get('feita_em','')} · {t.get('prioridade','')}")
                with c2:
                    if st.button("🗑️", key=f"df{t['id']}"):
                        dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                        salvar_dados(dados); st.rerun()

# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Avisos")
    with st.expander("➕ Novo aviso"):
        av_txt = st.text_area("Mensagem", key="av_t")
        if st.button("Publicar"):
            if av_txt:
                dados["avisos"].insert(0, {"id": str(uuid.uuid4()), "texto": av_txt,
                                           "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                if salvar_dados(dados): st.success("Aviso publicado!"); st.rerun()
            else:
                st.warning("Digite uma mensagem.")
    for a in dados.get("avisos",[]):
        c1, c2 = st.columns([5,1])
        with c1:
            st.markdown(f"📢 {a['texto']}")
            st.caption(a["data"])
        with c2:
            if st.button("🗑️", key=f"dav{a['id']}"):
                dados["avisos"] = [x for x in dados["avisos"] if x["id"] != a["id"]]
                salvar_dados(dados); st.rerun()
        st.divider()
