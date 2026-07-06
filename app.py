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
CATS      = ["—", "ML - LB Collection", "SH - LB Collection",
             "AMZ - LB Collection", "TK TK - LB Collection"]

# ─── helpers ────────────────────────────────────────────────────────────────

def fmt_data(d_str):
    try:
        return date.fromisoformat(d_str).strftime("%d/%m/%Y")
    except Exception:
        return d_str

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
    content = base64.b64encode(
        json.dumps(data, ensure_ascii=False, indent=2).encode()
    ).decode()
    payload = {
        "message": f"update {datetime.now().strftime('%d/%m %H:%M')}",
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
for t in dados.get("tarefas", []):
    t.setdefault("feita", False)
    t.setdefault("feita_em", None)
    t.setdefault("descricao", "")
    t.setdefault("prioridade", "Baixa")
    t.setdefault("data", str(date.today()))
    t.setdefault("categoria", "—")

# ── dialog nova tarefa (definido uma vez, no nível do script) ─────────────
@st.dialog("Nova Tarefa")
def popup_nova_tarefa(data_inicial):
    titulo    = st.text_input("Título *", placeholder="O que precisa ser feito?")
    categoria = st.selectbox("Categoria / Marketplace", CATS)
    desc      = st.text_area("Descrição (opcional)", height=80)
    c1, c2    = st.columns(2)
    with c1:
        data = st.date_input("Data", value=data_inicial, format="DD/MM/YYYY")
    with c2:
        prio = st.selectbox("Prioridade", PRIOS)
    if st.button("✅ Adicionar tarefa", use_container_width=True, type="primary"):
        if not titulo.strip():
            st.warning("Por favor, preencha o título.")
            return
        dados["tarefas"].append({
            "id":         str(uuid.uuid4()),
            "titulo":     titulo.strip(),
            "categoria":  categoria,
            "descricao":  desc.strip(),
            "data":       str(data),
            "prioridade": prio,
            "feita":      False,
            "feita_em":   None,
            "criado_em":  datetime.now().isoformat(),
        })
        salvar_dados(dados)
        st.rerun()

# ── cabeçalho ────────────────────────────────────────────────────────────────
st.title("👜 LB Collection — Painel")
tab1, tab2 = st.tabs(["✅ Tarefas", "📢 Avisos"])

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

    tarefas_ativas = [t for t in dados.get("tarefas", []) if not t.get("feita")]
    datas_tarefas  = {t.get("data") for t in tarefas_ativas}

    # ── barra de navegação ───────────────────────────────────────────────────
    nav = st.columns([1, 1, 4, 1, 5, 1, 2])
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
    with nav[6]:
        if st.button("➕ Nova tarefa", use_container_width=True):
            popup_nova_tarefa(hoje)

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

    with col_sem:
        cols_d = st.columns(7)
        for i, (dia, nome) in enumerate(zip(dias_sem, nomes_dia)):
            eventos_dia = [t for t in tarefas_ativas if t.get("data") == str(dia)]
            with cols_d[i]:
                st.markdown(html_dia(dia, nome, eventos_dia, dia == hoje),
                            unsafe_allow_html=True)
                if st.button("＋", key=f"ad{i}", use_container_width=True,
                             help=f"Adicionar tarefa em {fmt_data(str(dia))}"):
                    popup_nova_tarefa(dia)

    st.divider()

    # ── colunas de prioridade ────────────────────────────────────────────────
    pendentes = [t for t in dados.get("tarefas", []) if not t.get("feita")]

    def render_col(col, prio):
        bloco = sorted(
            [t for t in pendentes if t.get("prioridade") == prio],
            key=lambda x: x.get("data", "")
        )
        cor = COR[prio]
        with col:
            st.markdown(
                f"<div style='border-top:4px solid {cor};border-radius:8px 8px 0 0;"
                f"background:white;padding:10px 4px 6px;font-weight:700;font-size:0.95rem;"
                f"margin-bottom:-1px'>{EMOJI[prio]} {prio} "
                f"<span style='font-weight:400;font-size:0.8rem;color:#999'>({len(bloco)})</span></div>",
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                if not bloco:
                    st.caption("Nenhuma tarefa.")
                for idx, t in enumerate(bloco):
                    ed = st.session_state["editando"] == t["id"]
                    if ed:
                        nv_t  = st.text_input("Título", value=t["titulo"],  key=f"et{t['id']}")
                        nv_d  = st.text_area("Descrição", value=t.get("descricao", ""), key=f"ed{t['id']}", height=80)
                        nv_cat = st.selectbox("Categoria", CATS,
                                              index=CATS.index(t.get("categoria","—")) if t.get("categoria","—") in CATS else 0,
                                              key=f"ecat{t['id']}")
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
                        bs, bc = st.columns(2)
                        with bs:
                            if st.button("💾 Salvar", key=f"sv{t['id']}", use_container_width=True):
                                for x in dados["tarefas"]:
                                    if x["id"] == t["id"]:
                                        x.update({
                                            "titulo": nv_t.strip(),
                                            "descricao": nv_d.strip(),
                                            "categoria": nv_cat,
                                            "data": str(nv_dt),
                                            "prioridade": nv_p,
                                        })
                                st.session_state["editando"] = None
                                salvar_dados(dados)
                                st.rerun()
                        with bc:
                            if st.button("✕ Cancelar", key=f"cc{t['id']}", use_container_width=True):
                                st.session_state["editando"] = None
                                st.rerun()
                    else:
                        row = st.columns([7, 1, 1])
                        with row[0]:
                            feita = st.checkbox(
                                f"**{t['titulo']}**",
                                value=False, key=f"ck{t['id']}"
                            )
                            cat = t.get("categoria", "—")
                            info = fmt_data(t["data"])
                            if cat and cat != "—":
                                info += f"  ·  {cat}"
                            if t.get("descricao"):
                                st.caption(t["descricao"])
                            st.caption(f"📅 {info}")
                        with row[1]:
                            if st.button("✏️", key=f"e2{t['id']}", use_container_width=True, help="Editar"):
                                st.session_state["editando"] = t["id"]
                                st.rerun()
                        with row[2]:
                            if st.button("🗑️", key=f"dl{t['id']}", use_container_width=True, help="Excluir"):
                                dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                                salvar_dados(dados)
                                st.rerun()
                        if feita:
                            for x in dados["tarefas"]:
                                if x["id"] == t["id"]:
                                    x["feita"]    = True
                                    x["feita_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                            salvar_dados(dados)
                            st.rerun()
                    if idx < len(bloco) - 1:
                        st.markdown("<hr class='task-sep'>", unsafe_allow_html=True)

    ca, cm, cb = st.columns(3)
    render_col(ca, "Alta")
    render_col(cm, "Média")
    render_col(cb, "Baixa")

    # ── feitas ───────────────────────────────────────────────────────────────
    feitas = sorted(
        [t for t in dados.get("tarefas", []) if t.get("feita")],
        key=lambda x: x.get("feita_em", ""), reverse=True
    )
    if feitas:
        st.divider()
        with st.expander(f"✅ Feitas ({len(feitas)})"):
            for t in feitas:
                c1, c2 = st.columns([9, 1])
                with c1:
                    st.markdown(f"~~{t['titulo']}~~")
                    st.caption(f"Concluída em {t.get('feita_em','')} · {t.get('prioridade','')}")
                with c2:
                    if st.button("🗑️", key=f"df{t['id']}", help="Excluir"):
                        dados["tarefas"] = [x for x in dados["tarefas"] if x["id"] != t["id"]]
                        salvar_dados(dados)
                        st.rerun()
                st.markdown("<hr class='task-sep'>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("📢 Avisos")

    with st.form("form_aviso", clear_on_submit=True):
        av_txt = st.text_area("Nova mensagem", placeholder="Digite o aviso para a funcionária...")
        if st.form_submit_button("📢 Publicar aviso", use_container_width=True, type="primary"):
            if av_txt.strip():
                dados["avisos"].insert(0, {
                    "id":    str(uuid.uuid4()),
                    "texto": av_txt.strip(),
                    "data":  datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
                salvar_dados(dados)
                st.success("✅ Aviso publicado!")
                st.rerun()
            else:
                st.warning("Digite uma mensagem antes de publicar.")

    st.divider()

    if not dados.get("avisos"):
        st.info("Nenhum aviso no momento.")

    for a in dados.get("avisos", []):
        c1, c2 = st.columns([10, 1])
        with c1:
            st.markdown(f"**{a['texto']}**")
            st.caption(f"🕐 {a['data']}")
        with c2:
            if st.button("🗑️", key=f"dav{a['id']}", help="Excluir aviso"):
                dados["avisos"] = [x for x in dados["avisos"] if x["id"] != a["id"]]
                salvar_dados(dados)
                st.rerun()
        st.markdown("<hr class='task-sep'>", unsafe_allow_html=True)
