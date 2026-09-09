import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date
from io import BytesIO
import json

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="PRODUCT | Enterprise Workspace",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "produtividade.db"


# =========================================================
# BANCO DE DADOS (CRIAÇÃO DO ZERO / MIGRAÇÃO AUTOMÁTICA)
# =========================================================

def conectar():
    return sqlite3.connect(DB)


def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtividade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            colaborador TEXT NOT NULL,
            sysvet_erro INTEGER DEFAULT 0,
            sysvet_exito INTEGER DEFAULT 0,
            faturado INTEGER DEFAULT 0,
            auditoria INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY,
            senha TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acessos_colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)

    try:
        cursor.execute("ALTER TABLE produtividade ADD COLUMN auditoria INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT COUNT(*) FROM configuracoes")
    quantidade = cursor.fetchone()[0]

    if quantidade == 0:
        cursor.execute(
            "INSERT INTO configuracoes (id, senha) VALUES (1, ?)",
            ("2010",)
        )

    conn.commit()
    conn.close()


criar_banco()


# =========================================================
# FUNÇÕES DE APOIO E DADOS
# =========================================================

def buscar_senha():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT senha FROM configuracoes WHERE id = 1")
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return resultado[0]
    return "2010"


def alterar_senha(nova_senha):
    conn = conectar()
    conn.execute("UPDATE configuracoes SET senha = ? WHERE id = 1", (nova_senha,))
    conn.commit()
    conn.close()


def buscar_colaboradores():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM colaboradores ORDER BY nome", conn)
    conn.close()
    return df


def buscar_acessos():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM acessos_colaboradores ORDER BY nome", conn)
    conn.close()
    return df


def buscar_produtividade():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM produtividade ORDER BY data DESC, id DESC", conn)
    conn.close()

    if not df.empty:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df["sysvet_erro"] = pd.to_numeric(df["sysvet_erro"], errors="coerce").fillna(0).astype(int)
        df["sysvet_exito"] = pd.to_numeric(df["sysvet_exito"], errors="coerce").fillna(0).astype(int)
        df["faturado"] = pd.to_numeric(df["faturado"], errors="coerce").fillna(0).astype(int)
        
        if "auditoria" not in df.columns:
            df["auditoria"] = 0
        else:
            df["auditoria"] = pd.to_numeric(df["auditoria"], errors="coerce").fillna(0).astype(int)
        
        df["total_sysvet"] = df["sysvet_erro"] + df["sysvet_exito"]
        df["produtividade_total"] = df["sysvet_erro"] + df["sysvet_exito"] + df["faturado"] + df["auditoria"]
        
        df["taxa_exito"] = df.apply(
            lambda linha: (linha["sysvet_exito"] / linha["total_sysvet"] * 100) if linha["total_sysvet"] > 0 else 0,
            axis=1
        )
    return df


def gerar_backup_json():
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM colaboradores")
    cols = [desc[0] for desc in cursor.description]
    colaboradores = [dict(zip(cols, row)) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM produtividade")
    cols = [desc[0] for desc in cursor.description]
    produtividade = [dict(zip(cols, row)) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM acessos_colaboradores")
    cols = [desc[0] for desc in cursor.description]
    acessos = [dict(zip(cols, row)) for row in cursor.fetchall()]

    conn.close()

    dados_backup = {
        "colaboradores": colaboradores,
        "produtividade": produtividade,
        "acessos_colaboradores": acessos
    }
    return json.dumps(dados_backup, ensure_ascii=False, indent=4)


def restaurar_backup_json(json_str):
    try:
        dados = json.loads(json_str)
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM colaboradores")
        cursor.execute("DELETE FROM produtividade")
        cursor.execute("DELETE FROM acessos_colaboradores")

        for item in dados.get("colaboradores", []):
            cursor.execute("INSERT INTO colaboradores (id, nome) VALUES (?, ?)", (item.get("id"), item.get("nome")))

        for item in dados.get("produtividade", []):
            auditoria_val = item.get("auditoria", 0)
            if auditoria_val is None:
                auditoria_val = 0

            cursor.execute("""
                INSERT INTO produtividade (id, data, colaborador, sysvet_erro, sysvet_exito, faturado, auditoria)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("id"), 
                item.get("data"), 
                item.get("colaborador"), 
                item.get("sysvet_erro"), 
                item.get("sysvet_exito"), 
                item.get("faturado"),
                auditoria_val
            ))

        for item in dados.get("acessos_colaboradores", []):
            cursor.execute("INSERT INTO acessos_colaboradores (id, nome, senha) VALUES (?, ?, ?)", (item.get("id"), item.get("nome"), item.get("senha")))

        conn.commit()
        conn.close()
        return True, "Backup restaurado com sucesso!"
    except Exception as e:
        return False, f"Erro ao restaurar backup: {str(e)}"


# =========================================================
# DESIGN SYSTEM EXCLUSIVO (UI / UX + BACKGROUND PREMIUM MESH)
# =========================================================

if "modo_noturno" not in st.session_state:
    st.session_state.modo_noturno = True  # Padrão Dark Mode corporativo tecnológico

if not st.session_state.modo_noturno:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Background Light Customizado com Textura Mesh e Grid */
    .stApp { 
        background-color: #f8fafc;
        background-image: 
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.06) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(14, 165, 233, 0.05) 0px, transparent 50%),
            linear-gradient(to right, rgba(226, 232, 240, 0.3) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(226, 232, 240, 0.3) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 100% 100%, 32px 32px, 32px 32px;
        color: #0f172a; 
    }
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%); 
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] * { 
        color: #1e293b !important; 
    }
    h1 { 
        color: #0f172a !important; 
        font-weight: 800; 
        letter-spacing: -0.03em;
    }
    h2, h3 { 
        color: #1e293b !important; 
        font-weight: 700; 
        letter-spacing: -0.02em;
    }
    p, label { 
        color: #475569 !important; 
    }
    
    /* Cards Modernos Estilo Vercel/Notion com Efeito Glass */
    div[data-testid="stMetric"] { 
        background: rgba(255, 255, 255, 0.85); 
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 22px; 
        border-radius: 16px; 
        border: 1px solid rgba(226, 232, 240, 0.8); 
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }
    div[data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 35px -10px rgba(99, 102, 241, 0.15);
        border-color: #cbd5e1;
    }
    div[data-testid="stMetricLabel"] { 
        color: #64748b !important; 
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    div[data-testid="stMetricValue"] { 
        color: #0f172a !important; 
        font-weight: 800; 
        font-size: 1.85rem;
    }
    
    /* Botões Dinâmicos e Elegantes */
    .stButton > button, .stDownloadButton > button { 
        border-radius: 12px; 
        font-weight: 600; 
        background: #0f172a;
        color: white;
        border: 1px solid #1e293b;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: #1e293b;
        border-color: #334155;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.2);
        color: white;
    }
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        border: none !important;
    }
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Background Dark Deep Tech com Glow e Mesh Neomórfico */
    .stApp { 
        background-color: #030712;
        background-image: 
            radial-gradient(at 10% 10%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
            radial-gradient(at 90% 10%, rgba(14, 165, 233, 0.12) 0px, transparent 50%),
            radial-gradient(at 50% 90%, rgba(168, 85, 247, 0.10) 0px, transparent 50%),
            linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 100% 100%, 40px 40px, 40px 40px;
        color: #f8fafc; 
    }
    [data-testid="stHeader"] { 
        background-color: transparent; 
    }
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #020617 0%, #030712 100%); 
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    [data-testid="stSidebar"] * { 
        color: #f8fafc !important; 
    }
    h1 { 
        color: #ffffff !important; 
        font-weight: 800; 
        letter-spacing: -0.03em;
    }
    h2, h3 { 
        color: #f1f5f9 !important; 
        font-weight: 700; 
        letter-spacing: -0.02em;
    }
    p, label { 
        color: #94a3b8 !important; 
    }
    
    /* Cards (Dark Glassmorphism Premium) */
    div[data-testid="stMetric"] { 
        background: rgba(15, 23, 42, 0.75) !important; 
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        padding: 22px; 
        border-radius: 16px; 
        border: 1px solid rgba(255, 255, 255, 0.08); 
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7);
        position: relative;
        overflow: hidden;
    }
    div[data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #818cf8 0%, #6366f1 100%);
    }
    div[data-testid="stMetricLabel"] { 
        color: #94a3b8 !important; 
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    div[data-testid="stMetricValue"] { 
        color: #f8fafc !important; 
        font-weight: 800; 
        font-size: 1.85rem;
    }
    
    .stButton > button { 
        border-radius: 12px; 
        font-weight: 600; 
        background: rgba(30, 41, 59, 0.8); 
        backdrop-filter: blur(8px);
        color: #f8fafc; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        transition: all 0.2s ease;
    }
    .stButton > button:hover { 
        background: rgba(51, 65, 85, 0.9); 
        border-color: rgba(255, 255, 255, 0.2);
        color: #ffffff; 
    }
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        border: none !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)


# =========================================================
# CONTROLE DE SESSÃO / TELA DE LOGIN PREMIUM
# =========================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "perfil" not in st.session_state:
    st.session_state.perfil = None
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None


if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.3, 1])

    with col2:
        st.markdown("<h1 style='text-align: center; font-size: 2.5rem;'>⚡ PRODUCT</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.05rem;'>Workspace Corporativo de Alta Performance</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        tipo_login = st.radio("Acessar como:", ["Administrador", "Colaborador"], horizontal=True)

        if tipo_login == "Administrador":
            senha_adm = st.text_input("Senha Master do Administrador", type="password", key="senha_adm_input")
            st.markdown("<br>", unsafe_allow_html=True)
            entrar = st.button("🔐 AUTENTICAR NO SISTEMA", use_container_width=True)

            if entrar:
                if senha_adm == buscar_senha():
                    st.session_state.autenticado = True
                    st.session_state.perfil = "admin"
                    st.session_state.usuario_logado = "Administrador Master"
                    st.rerun()
                else:
                    st.error("❌ Senha master incorreta.")
        else:
            df_acessos = buscar_acessos()
            if df_acessos.empty:
                st.warning("⚠️ Nenhum acesso de colaborador configurado pelo Administrador.")
            else:
                colab_escolhido = st.selectbox("Selecione seu perfil", df_acessos["nome"].tolist())
                senha_colab = st.text_input("Senha de acesso pessoal", type="password", key="senha_colab_input")
                st.markdown("<br>", unsafe_allow_html=True)
                entrar_colab = st.button("🔐 AUTENTICAR NO SISTEMA", use_container_width=True)

                if entrar_colab:
                    senha_correta = df_acessos[df_acessos["nome"] == colab_escolhido]["senha"].values[0]
                    if senha_colab == senha_correta:
                        st.session_state.autenticado = True
                        st.session_state.perfil = "colaborador"
                        st.session_state.usuario_logado = colab_escolhido
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta.")

    st.stop()


# =========================================================
# MENU LATERAL REFINADO
# =========================================================

st.sidebar.markdown("## ⚡ PRODUCT")
st.sidebar.markdown(f"""
<div style="background: rgba(255,255,255,0.04); padding: 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 15px;">
    <p style="margin:0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Sessão Ativa</p>
    <p style="margin:4px 0 0 0; font-weight: 700; font-size: 0.95rem;">👤 {st.session_state.usuario_logado}</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.modo_noturno:
    texto_modo = "☀️ Alternar Modo Claro"
else:
    texto_modo = "🌙 Alternar Modo Noturno"

if st.sidebar.button(texto_modo, use_container_width=True):
    st.session_state.modo_noturno = not st.session_state.modo_noturno
    st.rerun()

st.sidebar.markdown("<br>", unsafe_allow_html=True)

if st.session_state.perfil == "admin":
    paginas = [
        "📊 Dashboard Executivo",
        "📝 Lançar Produtividade",
        "👥 Gerenciar Colaboradores",
        "🔑 Configurar Acessos",
        "📋 Histórico Geral",
        "📥 Backup & Exportação",
        "🔐 Segurança / Senha"
    ]
else:
    paginas = [
        "📝 Lançar Produtividade",
        "📋 Histórico Geral"
    ]

pagina = st.sidebar.radio("NAVEGAÇÃO PRINCIPAL", paginas)

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)

if st.sidebar.button("🚪 ENCERRAR SESSÃO", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.perfil = None
    st.session_state.usuario_logado = None
    st.rerun()


# =========================================================
# DASHBOARD EXECUTIVO
# =========================================================

if pagina == "📊 Dashboard Executivo" and st.session_state.perfil == "admin":
    st.title("📊 Dashboard Executivo")
    st.caption("Central de inteligência analítica e acompanhamento de métricas de produtividade")

    df = buscar_produtividade()

    if df.empty:
        st.info("Ainda não existem registros de produtividade para renderizar o painel.")
        st.stop()

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container():
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        lista_colaboradores = sorted(df["colaborador"].unique().tolist())

        with col_f1:
            colaborador_filtro = st.selectbox("👤 Filtrar por Colaborador", ["Todos os colaboradores"] + lista_colaboradores)

        data_min = df["data"].min().date()
        data_max = df["data"].max().date()

        with col_f2:
            periodo = st.date_input("📅 Janela Temporal", value=(data_min, data_max), min_value=data_min, max_value=data_max)

        with col_f3:
            st.write("")
            st.write("")
            if st.button("🔄 Sincronizar", use_container_width=True):
                st.rerun()

    if isinstance(periodo, tuple) and len(periodo) == 2:
        inicio, fim = periodo
        df_filtrado = df[(df["data"].dt.date >= inicio) & (df["data"].dt.date <= fim)].copy()
    else:
        df_filtrado = df.copy()

    if colaborador_filtro != "Todos os colaboradores":
        df_filtrado = df_filtrado[df_filtrado["colaborador"] == colaborador_filtro].copy()

    if df_filtrado.empty:
        st.warning("Não há dados consolidados para os parâmetros selecionados.")
        st.stop()

    erro = int(df_filtrado["sysvet_erro"].sum())
    exito = int(df_filtrado["sysvet_exito"].sum())
    faturado = int(df_filtrado["faturado"].sum())
    auditoria = int(df_filtrado["auditoria"].sum())
    total_sysvet = erro + exito
    produtividade = erro + exito + faturado + auditoria
    taxa_media = (exito / total_sysvet * 100) if total_sysvet > 0 else 0

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📌 Indicadores Chave de Desempenho (KPIs)")
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("❌ Erro SYSVET", f"{erro:,}")
    c2.metric("✅ Êxito SYSVET", f"{exito:,}")
    c3.metric("📁 Faturado", f"{faturado:,}")
    c4.metric("🔍 Auditoria", f"{auditoria:,}")
    c5.metric("📊 Volume Total", f"{produtividade:,}")
    c6.metric("🎯 Taxa Êxito", f"{taxa_media:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("🏆 Ranking de Produtividade por Colaborador")
        resumo_colab = df_filtrado.groupby("colaborador")["produtividade_total"].sum().reset_index()
        resumo_colab = resumo_colab.sort_values("produtividade_total", ascending=True)

        fig_bar = px.bar(
            resumo_colab, 
            x="produtividade_total", 
            y="colaborador", 
            orientation="h",
            text="produtividade_total",
            color="produtividade_total",
            color_continuous_scale="Viridis"
        )
        fig_bar.update_traces(textposition="outside", marker_line_width=0, marker_cornerradius=8)
        fig_bar.update_layout(
            xaxis_title="", 
            yaxis_title="", 
            coloraxis_showscale=False, 
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=30, t=10, b=10),
            height=380,
            font=dict(family="Plus Jakarta Sans", color="#94a3b8" if st.session_state.modo_noturno else "#475569")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_g2:
        st.subheader("🍩 Distribuição Percentual por Categoria")
        df_pizza = pd.DataFrame({
            "Categoria": ["SYSVET Erro", "SYSVET Êxito", "Faturado", "Auditoria"],
            "Quantidade": [erro, exito, faturado, auditoria]
        })
        
        fig_pie = px.pie(
            df_pizza, 
            names="Categoria", 
            values="Quantidade", 
            hole=0.6,
            color="Categoria",
            color_discrete_map={
                "SYSVET Erro": "#f43f5e", 
                "SYSVET Êxito": "#10b981", 
                "Faturado": "#3b82f6",
                "Auditoria": "#8b5cf6"
            }
        )
        fig_pie.update_traces(textinfo="percent+label", pull=[0.02, 0.02, 0.02, 0.02])
        fig_pie.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            showlegend=False,
            font=dict(family="Plus Jakarta Sans", color="#94a3b8" if st.session_state.modo_noturno else "#475569")
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("📈 Linha do Tempo de Produtividade Consolidada")
    df_tempo = df_filtrado.groupby("data")["produtividade_total"].sum().reset_index()
    df_tempo = df_tempo.sort_values("data")
    df_tempo["data_str"] = df_tempo["data"].dt.strftime("%d/%m/%Y")

    fig_inv = px.line(
        df_tempo, 
        x="data_str", 
        y="produtividade_total",
        markers=True
    )

    fig_inv.update_traces(
        line=dict(color="#6366f1", width=3.5, shape="spline"),
        marker=dict(size=8, color="#6366f1", line=dict(color="#ffffff", width=2)),
        fill='tozeroy',
        fillcolor='rgba(99, 102, 241, 0.15)'
    )

    fig_inv.update_layout(
        xaxis_title="",
        yaxis_title="Volume Diário",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
        height=380,
        hovermode="x unified",
        xaxis=dict(showline=False, gridcolor='rgba(128, 128, 128, 0.08)' if st.session_state.modo_noturno else 'rgba(128, 128, 128, 0.15)'),
        yaxis=dict(showline=False, gridcolor='rgba(128, 128, 128, 0.08)' if st.session_state.modo_noturno else 'rgba(128, 128, 128, 0.15)'),
        font=dict(family="Plus Jakarta Sans", color="#94a3b8" if st.session_state.modo_noturno else "#475569")
    )

    st.plotly_chart(fig_inv, use_container_width=True)


# =========================================================
# LANÇAR PRODUTIVIDADE
# =========================================================

elif pagina == "📝 Lançar Produtividade":
    st.title("📝 Lançar Produtividade")
    st.caption("Preencha os indicadores correspondentes às entregas diárias")

    colaboradores = buscar_colaboradores()

    if colaboradores.empty:
        st.warning("⚠️ Cadastre colaboradores antes de realizar lançamentos.")
    else:
        with st.form("form_produtividade"):
            data_lancamento = st.date_input("📅 Data de Referência", value=date.today())

            if st.session_state.perfil == "admin":
                colaborador = st.selectbox("👤 Colaborador Responsável", colaboradores["nome"].tolist())
            else:
                colaborador = st.session_state.usuario_logado
                st.info(f"👤 Registrando atividade em nome de: **{colaborador}**")

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                erro = st.number_input("❌ SYSVET Erro", min_value=0, value=0, step=1)
            with col2:
                exito = st.number_input("✅ SYSVET Êxito", min_value=0, value=0, step=1)
            with col3:
                faturado = st.number_input("📁 Faturado", min_value=0, value=0, step=1)
            with col4:
                auditoria = st.number_input("🔍 Auditoria", min_value=0, value=0, step=1)

            total = erro + exito + faturado + auditoria
            st.markdown(f"### 📊 Total computado do lançamento: `{total}`")
            st.markdown("<br>", unsafe_allow_html=True)

            salvar = st.form_submit_button("💾 SALVAR REGISTRO OFICIAL", use_container_width=True)

            if salvar:
                conn = conectar()
                conn.execute(
                    """
                    INSERT INTO produtividade (data, colaborador, sysvet_erro, sysvet_exito, faturado, auditoria)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (str(data_lancamento), colaborador, int(erro), int(exito), int(faturado), int(auditoria))
                )
                conn.commit()
                conn.close()
                st.success("✅ Atividade registrada e salva no banco de dados com sucesso!")
                st.rerun()


# =========================================================
# COLABORADORES
# =========================================================

elif pagina == "👥 Gerenciar Colaboradores" and st.session_state.perfil == "admin":
    st.title("👥 Gestão de Colaboradores")

    with st.form("form_colaborador"):
        st.subheader("➕ Adicionar Novo Membro")
        nome = st.text_input("Nome Completo do Colaborador")
        cadastrar = st.form_submit_button("CADASTRAR NOVO MEMBRO", use_container_width=True)

        if cadastrar:
            if not nome.strip():
                st.error("Informe o nome do colaborador.")
            else:
                try:
                    conn = conectar()
                    conn.execute("INSERT INTO colaboradores (nome) VALUES (?)", (nome.strip(),))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {nome} cadastrado com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("⚠️ Este colaborador já se encontra cadastrado no sistema.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Equipe Cadastrada")
    
    colaboradores = buscar_colaboradores()
    if colaboradores.empty:
        st.info("Nenhum colaborador registrado.")
    else:
        st.dataframe(colaboradores[["id", "nome"]], use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🗑️ Remover Colaborador")
        colab_para_excluir = st.selectbox("Selecione o membro para exclusão", colaboradores["nome"].tolist(), key="select_excluir_colab")

        df_prod = buscar_produtividade()
        lancamentos_colab = 0
        if not df_prod.empty:
            lancamentos_colab = len(df_prod[df_prod["colaborador"] == colab_para_excluir])

        if lancamentos_colab > 0:
            st.info(f"ℹ️ Este colaborador possui **{lancamentos_colab} registro(s)** históricos associados.")

        confirmar_exclusao = st.checkbox("Confirmo a exclusão permanente deste colaborador e seus acessos.", key="check_excluir_colab")

        if confirmar_exclusao:
            if st.button("🗑️ EXCLUIR DEFINITIVAMENTE", use_container_width=True):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM colaboradores WHERE nome = ?", (colab_para_excluir,))
                cursor.execute("DELETE FROM acessos_colaboradores WHERE nome = ?", (colab_para_excluir,))
                conn.commit()
                conn.close()
                st.success("✅ Colaborador e registros de acesso removidos com sucesso!")
                st.rerun()


# =========================================================
# GERENCIAR ACESSOS
# =========================================================

elif pagina == "🔑 Configurar Acessos" and st.session_state.perfil == "admin":
    st.title("🔑 Controle de Acessos Individuais")

    colaboradores_disp = buscar_colaboradores()

    if colaboradores_disp.empty:
        st.warning("⚠️ Cadastre colaboradores na aba anterior para gerenciar acessos.")
    else:
        with st.form("form_acesso"):
            colab_nome = st.selectbox("Colaborador", colaboradores_disp["nome"].tolist())
            senha_colab = st.text_input("Definir Senha de Acesso", type="password")
            salvar_acesso = st.form_submit_button("💾 SALVAR CREDENCIAIS DE ACESSO", use_container_width=True)

            if salvar_acesso:
                if not senha_colab.strip():
                    st.error("A senha não pode estar em branco.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM acessos_colaboradores WHERE nome = ?", (colab_nome,))
                    existe = cursor.fetchone()

                    if existe:
                        cursor.execute("UPDATE acessos_colaboradores SET senha = ? WHERE nome = ?", (senha_colab.strip(), colab_nome))
                    else:
                        cursor.execute("INSERT INTO acessos_colaboradores (nome, senha) VALUES (?, ?)", (colab_nome, senha_colab.strip()))

                    conn.commit()
                    conn.close()
                    st.success(f"✅ Credenciais salvas para {colab_nome}!")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Status de Acessos Configurados")
    df_acessos = buscar_acessos()
    if not df_acessos.empty:
        df_exibicao = df_acessos.copy()
        df_exibicao["senha"] = "••••••"
        st.dataframe(df_exibicao[["id", "nome", "senha"]], use_container_width=True, hide_index=True)


# =========================================================
# HISTÓRICO
# =========================================================

elif pagina == "📋 Histórico Geral":
    st.title("📋 Histórico Geral de Entregas")

    df = buscar_produtividade()

    if st.session_state.perfil == "colaborador":
        df = df[df["colaborador"] == st.session_state.usuario_logado]

    if df.empty:
        st.info("Nenhum lançamento registrado no momento.")
    else:
        total_lancamentos = len(df)
        soma_prod_hist = int(df["produtividade_total"].sum())
        
        m1, m2 = st.columns(2)
        m1.metric("📦 Total de Registros", f"{total_lancamentos:,}")
        m2.metric("📊 Volume Acumulado", f"{soma_prod_hist:,}")
        st.markdown("<br>", unsafe_allow_html=True)

        visualizar = df[
            [
                "id",
                "data",
                "colaborador",
                "sysvet_erro",
                "sysvet_exito",
                "faturado",
                "auditoria",
                "produtividade_total"
            ]
        ].copy()

        visualizar["data"] = visualizar["data"].dt.strftime("%d/%m/%Y")
        visualizar.columns = [
            "ID", "Data", "Colaborador", "SYSVET Erro", "SYSVET Êxito", "Faturado", "Auditoria", "Total Geral"
        ]

        st.dataframe(visualizar, use_container_width=True, hide_index=True)

        if st.session_state.perfil == "admin":
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🗑️ Auditoria: Excluir Lançamentos por Data")
            data_exclusao = st.date_input("📅 Data Alvo para Limpeza", value=date.today(), key="data_exclusao")

            registros_data = df[df["data"].dt.date == data_exclusao].copy()

            if not registros_data.empty:
                st.warning(f"Atenção: Existem {len(registros_data)} registro(s) associados a esta data.")
                confirmar_data = st.checkbox("Confirmo a exclusão definitiva de todos os registros desta data específica.", key="confirmar_exclusao_data")

                if confirmar_data:
                    if st.button("🗑️ EXECUTAR REMOÇÃO DOS REGISTROS", use_container_width=True):
                        conn = conectar()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM produtividade WHERE data = ?", (str(data_exclusao),))
                        conn.commit()
                        conn.close()
                        st.success("✅ Registros excluídos com sucesso.")
                        st.rerun()


# =========================================================
# EXPORTAR / BACKUP
# =========================================================

elif pagina == "📥 Backup & Exportação" and st.session_state.perfil == "admin":
    st.title("📥 Backup & Exportação de Dados")

    df = buscar_produtividade()

    if not df.empty:
        st.subheader("📊 Exportar Relatório em Planilha Excel")
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Produtividade")
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Baixar Planilha Consolidada (.xlsx)",
            data=processed_data,
            file_name=f"produtividade_enterprise_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💾 Backup Completo do Workspace (JSON)")
    json_backup = gerar_backup_json()
    st.download_button(
        label="📥 Baixar Arquivo de Backup do Sistema (.json)",
        data=json_backup,
        file_name=f"backup_enterprise_{date.today()}.json",
        mime="application/json",
        use_container_width=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("♻️ Restaurar Estado do Sistema via Backup")
    arquivo_submetido = st.file_uploader("Enviar arquivo JSON de backup válido", type=["json"])
    if arquivo_submetido is not None:
        conteudo_json = arquivo_submetido.getvalue().decode("utf-8")
        if st.button("🔄 EXECUTAR RESTAURAÇÃO COMPLETA", use_container_width=True):
            sucesso, mensagem = restaurar_backup_json(conteudo_json)
            if sucesso:
                st.success(mensagem)
                st.rerun()
            else:
                st.error(mensagem)


# =========================================================
# ALTERAR SENHA
# =========================================================

elif pagina == "🔐 Segurança / Senha" and st.session_state.perfil == "admin":
    st.title("🔐 Configurações de Segurança")

    with st.form("form_senha"):
        senha_atual = st.text_input("Senha Master Atual", type="password")
        nova_senha = st.text_input("Nova Senha Master", type="password")
        confirma_senha = st.text_input("Confirme a Nova Senha Master", type="password")

        atualizar = st.form_submit_button("🔒 ATUALIZAR CREDENCIAIS DE SEGURANÇA", use_container_width=True)

        if atualizar:
            if senha_atual != buscar_senha():
                st.error("❌ A senha master atual informada está incorreta.")
            elif not nova_senha.strip():
                st.error("❌ A nova senha não pode ser vazia.")
            elif nova_senha != confirma_senha:
                st.error("❌ As novas senhas não coincidem.")
            else:
                alterar_senha(nova_senha)
                st.success("✅ Senha master atualizada com sucesso!")
