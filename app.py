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
    page_title="PRODUCT | Dashboard Executivo",
    page_icon="📊",
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
# DESIGN SYSTEM & UI PREMIUM (MODO CLARO E NOTURNO)
# =========================================================

if "modo_noturno" not in st.session_state:
    st.session_state.modo_noturno = False

if not st.session_state.modo_noturno:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp { 
        background-color: #f8fafc; 
        color: #0f172a; 
    }
    [data-testid="stSidebar"] { 
        background: linear-gradient(160deg, #0f172a 0%, #1e293b 100%); 
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] * { 
        color: #f1f5f9 !important; 
    }
    h1 { 
        color: #0f172a !important; 
        font-weight: 800; 
        letter-spacing: -0.025em;
    }
    h2, h3 { 
        color: #1e293b !important; 
        font-weight: 700; 
    }
    p, label { 
        color: #334155; 
    }
    /* Estilização moderna dos Cards KPI */
    div[data-testid="stMetric"] { 
        background: #ffffff; 
        padding: 20px; 
        border-radius: 16px; 
        border: 1px solid #e2e8f0; 
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.08);
    }
    div[data-testid="stMetricLabel"] { 
        color: #64748b !important; 
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] { 
        color: #0284c7 !important; 
        font-weight: 800; 
        font-size: 1.8rem;
    }
    .stButton > button, .stDownloadButton > button { 
        border-radius: 12px; 
        font-weight: 600; 
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%);
        box-shadow: 0 6px 15px rgba(2, 132, 199, 0.35);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp { 
        background-color: #030712; 
        color: #f3f4f6; 
    }
    [data-testid="stHeader"] { 
        background-color: #030712; 
    }
    [data-testid="stSidebar"] { 
        background: linear-gradient(160deg, #020617 0%, #0f172a 100%); 
        border-right: 1px solid #1e293b;
    }
    [data-testid="stSidebar"] * { 
        color: #f8fafc !important; 
    }
    h1 { 
        color: #38bdf8 !important; 
        font-weight: 800; 
        letter-spacing: -0.025em;
    }
    h2, h3 { 
        color: #7dd3fc !important; 
        font-weight: 700; 
    }
    p, label { 
        color: #94a3b8 !important; 
    }
    /* Estilização moderna dos Cards KPI (Dark) */
    div[data-testid="stMetric"] { 
        background-color: #0f172a !important; 
        padding: 20px; 
        border-radius: 16px; 
        border: 1px solid #1e293b; 
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricLabel"] { 
        color: #94a3b8 !important; 
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] { 
        color: #38bdf8 !important; 
        font-weight: 800; 
        font-size: 1.8rem;
    }
    .stButton > button { 
        border-radius: 12px; 
        font-weight: 600; 
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); 
        color: white; 
        border: 1px solid #38bdf8;
        box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2);
    }
    .stButton > button:hover { 
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%); 
        color: white; 
    }
    </style>
    """, unsafe_allow_html=True)


# =========================================================
# CONTROLE DE SESSÃO / TELA DE LOGIN
# =========================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "perfil" not in st.session_state:
    st.session_state.perfil = None
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None


if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("<h1 style='text-align: center;'>📊 PRODUCT</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Plataforma Inteligente de Produtividade</p>", unsafe_allow_html=True)
        st.divider()

        tipo_login = st.radio("Entrar como:", ["Administrador", "Colaborador"], horizontal=True)

        if tipo_login == "Administrador":
            senha_adm = st.text_input("Senha do Administrador", type="password", key="senha_adm_input")
            st.markdown("<br>", unsafe_allow_html=True)
            entrar = st.button("🔓 ENTRAR NO SISTEMA", use_container_width=True, type="primary")

            if entrar:
                if senha_adm == buscar_senha():
                    st.session_state.autenticado = True
                    st.session_state.perfil = "admin"
                    st.session_state.usuario_logado = "Administrador"
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta.")
        else:
            df_acessos = buscar_acessos()
            if df_acessos.empty:
                st.warning("⚠️ Nenhum acesso de colaborador cadastrado pelo Administrador.")
            else:
                colab_escolhido = st.selectbox("Selecione seu nome", df_acessos["nome"].tolist())
                senha_colab = st.text_input("Senha de acesso", type="password", key="senha_colab_input")
                st.markdown("<br>", unsafe_allow_html=True)
                entrar_colab = st.button("🔓 ENTRAR NO SISTEMA", use_container_width=True, type="primary")

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
# MENU LATERAL
# =========================================================

st.sidebar.markdown("# 📊 PRODUCT")
st.sidebar.markdown(f"👤 **{st.session_state.usuario_logado}**")
st.sidebar.caption(f"Perfil: {st.session_state.perfil.upper()}")
st.sidebar.divider()

if st.session_state.modo_noturno:
    texto_modo = "☀️ MODO CLARO"
else:
    texto_modo = "🌙 MODO NOTURNO"

if st.sidebar.button(texto_modo, use_container_width=True):
    st.session_state.modo_noturno = not st.session_state.modo_noturno
    st.rerun()

st.sidebar.divider()

if st.session_state.perfil == "admin":
    paginas = [
        "📈 Dashboard",
        "📝 Lançar produtividade",
        "👥 Colaboradores",
        "🔑 Gerenciar Acessos",
        "📋 Histórico",
        "📥 Exportar / Backup",
        "🔐 Alterar senha"
    ]
else:
    paginas = [
        "📝 Lançar produtividade",
        "📋 Histórico"
    ]

pagina = st.sidebar.radio("MENU DE NAVEGAÇÃO", paginas)

st.sidebar.divider()

if st.sidebar.button("🚪 ENCERRAR SESSÃO", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.perfil = None
    st.session_state.usuario_logado = None
    st.rerun()


# =========================================================
# DASHBOARD EXECUTIVO
# =========================================================

if pagina == "📈 Dashboard" and st.session_state.perfil == "admin":
    st.title("📈 Dashboard Executivo")
    st.caption("Visão estratégica e analítica integrada da produtividade da equipe")

    df = buscar_produtividade()

    if df.empty:
        st.info("Ainda não existem registros de produtividade para exibir no dashboard.")
        st.stop()

    st.divider()

    # Filtros do Dashboard em layout limpo
    with st.container():
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        lista_colaboradores = sorted(df["colaborador"].unique().tolist())

        with col_f1:
            colaborador_filtro = st.selectbox("👤 Colaborador", ["Todos os colaboradores"] + lista_colaboradores)

        data_min = df["data"].min().date()
        data_max = df["data"].max().date()

        with col_f2:
            periodo = st.date_input("📅 Período de Análise", value=(data_min, data_max), min_value=data_min, max_value=data_max)

        with col_f3:
            st.write("")
            st.write("")
            if st.button("🔄 Atualizar", use_container_width=True):
                st.rerun()

    if isinstance(periodo, tuple) and len(periodo) == 2:
        inicio, fim = periodo
        df_filtrado = df[(df["data"].dt.date >= inicio) & (df["data"].dt.date <= fim)].copy()
    else:
        df_filtrado = df.copy()

    if colaborador_filtro != "Todos os colaboradores":
        df_filtrado = df_filtrado[df_filtrado["colaborador"] == colaborador_filtro].copy()

    if df_filtrado.empty:
        st.warning("Não existem registros para os filtros selecionados.")
        st.stop()

    # KPIs
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
    c1.metric("❌ SYSVET Erro", f"{erro:,}")
    c2.metric("✅ SYSVET Êxito", f"{exito:,}")
    c3.metric("📁 Faturado", f"{faturado:,}")
    c4.metric("🔍 Auditoria", f"{auditoria:,}")
    c5.metric("📊 Total Geral", f"{produtividade:,}")
    c6.metric("🎯 Taxa Êxito", f"{taxa_media:.1f}%")

    st.divider()

    # Gráficos Linha 1
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("🏆 Ranking de Produtividade")
        resumo_colab = df_filtrado.groupby("colaborador")["produtividade_total"].sum().reset_index()
        resumo_colab = resumo_colab.sort_values("produtividade_total", ascending=True)

        fig_bar = px.bar(
            resumo_colab, 
            x="produtividade_total", 
            y="colaborador", 
            orientation="h",
            text="produtividade_total",
            color="produtividade_total",
            color_continuous_scale="Blues"
        )
        fig_bar.update_traces(textposition="outside", marker_line_width=0, marker_cornerradius=6)
        fig_bar.update_layout(
            xaxis_title="", 
            yaxis_title="", 
            coloraxis_showscale=False, 
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=20, t=10, b=10),
            height=380
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_g2:
        st.subheader("🍩 Distribuição por Categoria")
        df_pizza = pd.DataFrame({
            "Categoria": ["SYSVET Erro", "SYSVET Êxito", "Faturado", "Auditoria"],
            "Quantidade": [erro, exito, faturado, auditoria]
        })
        
        fig_pie = px.pie(
            df_pizza, 
            names="Categoria", 
            values="Quantidade", 
            hole=0.55,
            color="Categoria",
            color_discrete_map={
                "SYSVET Erro": "#ef4444", 
                "SYSVET Êxito": "#22c55e", 
                "Faturado": "#3b82f6",
                "Auditoria": "#a855f7"
            }
        )
        fig_pie.update_traces(textinfo="percent+label", pull=[0.03, 0.03, 0.03, 0.03])
        fig_pie.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            showlegend=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # Gráfico de Linha Estilo Financeiro / Investimento
    st.subheader("📈 Evolução Diária da Produtividade")
    df_tempo = df_filtrado.groupby("data")["produtividade_total"].sum().reset_index()
    df_tempo = df_tempo.sort_values("data")
    df_tempo["data_str"] = df_tempo["data"].dt.strftime("%d/%m/%Y")

    if len(df_tempo) >= 2:
        tendencia_alta = df_tempo["produtividade_total"].iloc[-1] >= df_tempo["produtividade_total"].iloc[0]
    else:
        tendencia_alta = True

    cor_linha = "#10b981" if tendencia_alta else "#ef4444"
    cor_preenchimento = "rgba(16, 185, 129, 0.1)" if tendencia_alta else "rgba(239, 68, 68, 0.1)"

    fig_inv = px.line(
        df_tempo, 
        x="data_str", 
        y="produtividade_total",
        markers=True
    )

    fig_inv.update_traces(
        line=dict(color=cor_linha, width=3.5, shape="spline"),
        marker=dict(size=8, color=cor_linha, line=dict(color="#ffffff", width=2)),
        fill='tozeroy',
        fillcolor=cor_preenchimento
    )

    fig_inv.update_layout(
        xaxis_title="",
        yaxis_title="Volume",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
        height=380,
        hovermode="x unified",
        xaxis=dict(showline=False, gridcolor='rgba(150, 150, 150, 0.1)'),
        yaxis=dict(showline=False, gridcolor='rgba(150, 150, 150, 0.1)')
    )

    st.plotly_chart(fig_inv, use_container_width=True)


# =========================================================
# LANÇAR PRODUTIVIDADE
# =========================================================

elif pagina == "📝 Lançar produtividade":
    st.title("📝 Lançar Produtividade")
    st.caption("Insira os dados referentes às atividades realizadas")

    colaboradores = buscar_colaboradores()

    if colaboradores.empty:
        st.warning("⚠️ Nenhum colaborador cadastrado no sistema.")
    else:
        with st.form("form_produtividade"):
            data_lancamento = st.date_input("📅 Data do Registro", value=date.today())

            if st.session_state.perfil == "admin":
                colaborador = st.selectbox("👤 Colaborador", colaboradores["nome"].tolist())
            else:
                colaborador = st.session_state.usuario_logado
                st.info(f"👤 Lançando em nome de: **{colaborador}**")

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
            st.markdown(f"### 📊 Total calculado: `{total}`")
            st.markdown("<br>", unsafe_allow_html=True)

            salvar = st.form_submit_button("💾 SALVAR REGISTRO", use_container_width=True)

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
                st.success("✅ Produtividade registrada com sucesso!")
                st.rerun()


# =========================================================
# COLABORADORES
# =========================================================

elif pagina == "👥 Colaboradores" and st.session_state.perfil == "admin":
    st.title("👥 Gerenciar Colaboradores")

    with st.form("form_colaborador"):
        st.subheader("➕ Cadastrar Novo Colaborador")
        nome = st.text_input("Nome Completo")
        cadastrar = st.form_submit_button("CADASTRAR", use_container_width=True)

        if cadastrar:
            if not nome.strip():
                st.error("Digite o nome do colaborador.")
            else:
                try:
                    conn = conectar()
                    conn.execute("INSERT INTO colaboradores (nome) VALUES (?)", (nome.strip(),))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {nome} cadastrado com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("⚠️ Esse colaborador já está cadastrado.")

    st.divider()
    st.subheader("📋 Lista de Colaboradores")
    
    colaboradores = buscar_colaboradores()
    if colaboradores.empty:
        st.info("Nenhum colaborador cadastrado.")
    else:
        st.dataframe(colaboradores[["id", "nome"]], use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🗑️ Excluir Colaborador")
        colab_para_excluir = st.selectbox("Selecione para exclusão", colaboradores["nome"].tolist(), key="select_excluir_colab")

        df_prod = buscar_produtividade()
        lancamentos_colab = 0
        if not df_prod.empty:
            lancamentos_colab = len(df_prod[df_prod["colaborador"] == colab_para_excluir])

        if lancamentos_colab > 0:
            st.info(f"ℹ️ Este colaborador possui **{lancamentos_colab} registro(s)** no histórico.")

        confirmar_exclusao = st.checkbox("Confirmo a exclusão deste colaborador.", key="check_excluir_colab")

        if confirmar_exclusao:
            if st.button("🗑️ EXCLUIR SELECIONADO", type="primary", use_container_width=True):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM colaboradores WHERE nome = ?", (colab_para_excluir,))
                cursor.execute("DELETE FROM acessos_colaboradores WHERE nome = ?", (colab_para_excluir,))
                conn.commit()
                conn.close()
                st.success(f"✅ Colaborador removido!")
                st.rerun()


# =========================================================
# GERENCIAR ACESSOS
# =========================================================

elif pagina == "🔑 Gerenciar Acessos" and st.session_state.perfil == "admin":
    st.title("🔑 Acessos dos Colaboradores")

    colaboradores_disp = buscar_colaboradores()

    if colaboradores_disp.empty:
        st.warning("⚠️ Cadastre colaboradores primeiro.")
    else:
        with st.form("form_acesso"):
            colab_nome = st.selectbox("Colaborador", colaboradores_disp["nome"].tolist())
            senha_colab = st.text_input("Senha de Acesso", type="password")
            salvar_acesso = st.form_submit_button("💾 SALVAR ACESSO", use_container_width=True)

            if salvar_acesso:
                if not senha_colab.strip():
                    st.error("A senha não pode estar vazia.")
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
                    st.success(f"✅ Acesso salvo para {colab_nome}!")
                    st.rerun()

    st.divider()
    st.subheader("📋 Acessos Ativos")
    df_acessos = buscar_acessos()
    if not df_acessos.empty:
        df_exibicao = df_acessos.copy()
        df_exibicao["senha"] = "••••••"
        st.dataframe(df_exibicao[["id", "nome", "senha"]], use_container_width=True, hide_index=True)


# =========================================================
# HISTÓRICO
# =========================================================

elif pagina == "📋 Histórico":
    st.title("📋 Histórico de Lançamentos")

    df = buscar_produtividade()

    if st.session_state.perfil == "colaborador":
        df = df[df["colaborador"] == st.session_state.usuario_logado]

    if df.empty:
        st.info("Nenhum lançamento encontrado.")
    else:
        total_lancamentos = len(df)
        soma_prod_hist = int(df["produtividade_total"].sum())
        
        m1, m2 = st.columns(2)
        m1.metric("📦 Total de Registros", f"{total_lancamentos:,}")
        m2.metric("📊 Volume Total", f"{soma_prod_hist:,}")
        st.divider()

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
            "ID", "Data", "Colaborador", "SYSVET Erro", "SYSVET Êxito", "Faturado", "Auditoria", "Total"
        ]

        st.dataframe(visualizar, use_container_width=True, hide_index=True)

        if st.session_state.perfil == "admin":
            st.divider()
            st.subheader("🗑️ Excluir Registros por Data")
            data_exclusao = st.date_input("📅 Data", value=date.today(), key="data_exclusao")

            registros_data = df[df["data"].dt.date == data_exclusao].copy()

            if not registros_data.empty:
                st.warning(f"Existem {len(registros_data)} registro(s) nesta data.")
                confirmar_data = st.checkbox("Confirmo a exclusão de todos os registros desta data.", key="confirmar_exclusao_data")

                if confirmar_data:
                    if st.button("🗑️ EXCLUIR REGISTROS DA DATA", type="primary", use_container_width=True):
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

elif pagina == "📥 Exportar / Backup" and st.session_state.perfil == "admin":
    st.title("📥 Exportação e Backup")

    df = buscar_produtividade()

    if not df.empty:
        st.subheader("📊 Exportar para Excel")
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Produtividade")
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Baixar Planilha Excel (.xlsx)",
            data=processed_data,
            file_name=f"produtividade_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.divider()
    st.subheader("💾 Backup Completo (JSON)")
    json_backup = gerar_backup_json()
    st.download_button(
        label="📥 Baixar Backup do Sistema (.json)",
        data=json_backup,
        file_name=f"backup_sistema_{date.today()}.json",
        mime="application/json",
        use_container_width=True
    )

    st.divider()
    st.subheader("♻️ Restaurar Sistema")
    arquivo_submetido = st.file_uploader("Enviar arquivo de backup (.json)", type=["json"])
    if arquivo_submetido is not None:
        conteudo_json = arquivo_submetido.getvalue().decode("utf-8")
        if st.button("🔄 RESTAURAR DADOS", type="primary", use_container_width=True):
            sucesso, mensagem = restaurar_backup_json(conteudo_json)
            if sucesso:
                st.success(mensagem)
                st.rerun()
            else:
                st.error(mensagem)


# =========================================================
# ALTERAR SENHA
# =========================================================

elif pagina == "🔐 Alterar senha" and st.session_state.perfil == "admin":
    st.title("🔐 Segurança")

    with st.form("form_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirma_senha = st.text_input("Confirmar Nova Senha", type="password")

        atualizar = st.form_submit_button("🔒 ATUALIZAR SENHA", use_container_width=True)

        if atualizar:
            if senha_atual != buscar_senha():
                st.error("❌ Senha atual incorreta.")
            elif not nova_senha.strip():
                st.error("❌ A nova senha não pode estar em branco.")
            elif nova_senha != confirma_senha:
                st.error("❌ As senhas não coincidem.")
            else:
                alterar_senha(nova_senha)
                st.success("✅ Senha alterada com sucesso!")
