import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date
from io import BytesIO
import json

# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="PRODUCT",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "produtividade.db"


# =========================================================
# BANCO DE DADOS
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
            faturado INTEGER DEFAULT 0
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
        df["data"] = pd.to_datetime(df["data"])
        df["total_sysvet"] = df["sysvet_erro"] + df["sysvet_exito"]
        df["produtividade_total"] = df["sysvet_erro"] + df["sysvet_exito"] + df["faturado"]
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
            cursor.execute("""
                INSERT INTO produtividade (id, data, colaborador, sysvet_erro, sysvet_exito, faturado)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item.get("id"), item.get("data"), item.get("colaborador"), item.get("sysvet_erro"), item.get("sysvet_exito"), item.get("faturado")))

        for item in dados.get("acessos_colaboradores", []):
            cursor.execute("INSERT INTO acessos_colaboradores (id, nome, senha) VALUES (?, ?, ?)", (item.get("id"), item.get("nome"), item.get("senha")))

        conn.commit()
        conn.close()
        return True, "Backup restaurado com sucesso!"
    except Exception as e:
        return False, f"Erro ao restaurar backup: {str(e)}"


# =========================================================
# MODO VISUAL E CSS
# =========================================================

if "modo_noturno" not in st.session_state:
    st.session_state.modo_noturno = False

if not st.session_state.modo_noturno:
    st.markdown("""
    <style>
    .stApp { background-color: #f4f7fb; color: #172033; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #173b8f 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    h1 { color: #173b8f !important; font-weight: 800; }
    h2, h3 { color: #1e3a8a !important; }
    p, label { color: #263247; }
    div[data-testid="stMetric"] { background: white; padding: 18px; border-radius: 15px; border: 1px solid #e1e7ef; box-shadow: 0 4px 15px rgba(0,0,0,0.06); }
    div[data-testid="stMetricLabel"] { color: #64748b !important; }
    div[data-testid="stMetricValue"] { color: #173b8f !important; font-weight: 800; }
    .stButton > button, .stDownloadButton > button { border-radius: 10px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e5e7eb; }
    [data-testid="stHeader"] { background-color: #0b1120; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #020617 0%, #111827 100%); }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
    h1 { color: #60a5fa !important; font-weight: 800; }
    h2, h3 { color: #93c5fd !important; }
    p, label { color: #cbd5e1 !important; }
    div[data-testid="stMetric"] { background-color: #111827 !important; padding: 18px; border-radius: 15px; border: 1px solid #263244; box-shadow: 0 5px 20px rgba(0,0,0,0.35); }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
    div[data-testid="stMetricValue"] { color: #60a5fa !important; font-weight: 800; }
    .stButton > button { border-radius: 10px; font-weight: 700; background-color: #1e40af; color: white; border: 1px solid #3b82f6; }
    .stButton > button:hover { background-color: #2563eb; color: white; }
    </style>
    """, unsafe_allow_html=True)


# =========================================================
# CONTROLE DE SESSÃO / LOGIN
# =========================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "perfil" not in st.session_state:
    st.session_state.perfil = None
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None


if not st.session_state.autenticado:
    st.title("📊 PRODUCT")
    st.caption("Sistema de Controle de Produtividade")
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("🔐 Acesso ao sistema")
        
        tipo_login = st.radio("Entrar como:", ["Administrador", "Colaborador"])

        if tipo_login == "Administrador":
            senha_adm = st.text_input("Senha do Administrador", type="password", key="senha_adm_input")
            entrar = st.button("🔓 ENTRAR COMO ADMIN", use_container_width=True, type="primary")

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
                st.warning("⚠️ Nenhum acesso de colaborador cadastrado pelo Administrador ainda.")
            else:
                colab_escolhido = st.selectbox("Selecione seu nome", df_acessos["nome"].tolist())
                senha_colab = st.text_input("Senha de acesso", type="password", key="senha_colab_input")
                entrar_colab = st.button("🔓 ENTRAR COMO COLABORADOR", use_container_width=True, type="primary")

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
st.sidebar.caption(f"Logado como: **{st.session_state.usuario_logado}** ({st.session_state.perfil.upper()})")
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

pagina = st.sidebar.radio("MENU", paginas)

st.sidebar.divider()

if st.sidebar.button("🚪 SAIR", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.perfil = None
    st.session_state.usuario_logado = None
    st.rerun()


# =========================================================
# DASHBOARD POR MEIO DE CADASTRO (Somente Admin)
# =========================================================

if pagina == "📈 Dashboard" and st.session_state.perfil == "admin":
    st.title("📈 Dashboard por Meio de Cadastro")
    st.caption("Acompanhamento detalhado segmentado por tipo de lançamento (SYSVET Erro, Êxito e Faturamento)")

    df = buscar_produtividade()

    if df.empty:
        st.info("Ainda não existem registros de produtividade para exibir no dashboard.")
        st.stop()

    st.divider()

    # Filtros do Dashboard
    with st.container():
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        lista_colaboradores = sorted(df["colaborador"].unique().tolist())

        with col_f1:
            colaborador_filtro = st.selectbox("👤 Filtrar por Colaborador", ["Todos os colaboradores"] + lista_colaboradores)

        data_min = df["data"].min().date()
        data_max = df["data"].max().date()

        with col_f2:
            periodo = st.date_input("📅 Intervalo de Datas", value=(data_min, data_max), min_value=data_min, max_value=data_max)

        with col_f3:
            st.write("")
            st.write("")
            if st.button("🔄 Atualizar", use_container_width=True):
                st.rerun()

    # Aplicação dos Filtros
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

    # Cálculos dos KPIs
    erro = int(df_filtrado["sysvet_erro"].sum())
    exito = int(df_filtrado["sysvet_exito"].sum())
    faturado = int(df_filtrado["faturado"].sum())
    total_sysvet = erro + exito
    produtividade = erro + exito + faturado
    taxa_media = (exito / total_sysvet * 100) if total_sysvet > 0 else 0

    st.markdown("### 📌 Indicadores Gerais por Meio")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("❌ SYSVET Erro", f"{erro:,}")
    c2.metric("✅ SYSVET Êxito", f"{exito:,}")
    c3.metric("📁 Faturado", f"{faturado:,}")
    c4.metric("📊 Total Geral", f"{produtividade:,}")
    c5.metric("🎯 Taxa de Êxito", f"{taxa_media:.1f}%")

    st.divider()

    # Transformação dos dados para formato longo (cada linha representa um meio de cadastro)
    df_melted = df_filtrado.melt(
        id_vars=["id", "data", "colaborador"],
        value_vars=["sysvet_erro", "sysvet_exito", "faturado"],
        var_name="Meio de Cadastro",
        value_name="Quantidade"
    )

    # Renomeando de forma elegante para exibição
    mapa_nomes = {
        "sysvet_erro": "SYSVET Erro",
        "sysvet_exito": "SYSVET Êxito",
        "faturado": "Faturado"
    }
    df_melted["Meio de Cadastro"] = df_melted["Meio de Cadastro"].map(mapa_nomes)

    # Gráficos da Linha 1
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📊 Volume Total por Meio de Cadastro")
        resumo_meios = df_melted.groupby("Meio de Cadastro")["Quantidade"].sum().reset_index()

        fig_bar_meio = px.bar(
            resumo_meios,
            x="Meio de Cadastro",
            y="Quantidade",
            text="Quantidade",
            color="Meio de Cadastro",
            color_discrete_map={"SYSVET Erro": "#ef4444", "SYSVET Êxito": "#22c55e", "Faturado": "#3b82f6"}
        )
        fig_bar_meio.update_traces(textposition="outside")
        fig_bar_meio.update_layout(
            xaxis_title="",
            yaxis_title="Quantidade Total",
            coloraxis_showscale=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            showlegend=False
        )
        st.plotly_chart(fig_bar_meio, use_container_width=True)

    with col_g2:
        st.subheader("👥 Produtividade por Colaborador e Meio")
        fig_group_bar = px.bar(
            df_melted,
            x="colaborador",
            y="Quantidade",
            color="Meio de Cadastro",
            barmode="group",
            color_discrete_map={"SYSVET Erro": "#ef4444", "SYSVET Êxito": "#22c55e", "Faturado": "#3b82f6"}
        )
        fig_group_bar.update_layout(
            xaxis_title="Colaborador",
            yaxis_title="Quantidade",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            legend_title="Meio de Cadastro"
        )
        st.plotly_chart(fig_group_bar, use_container_width=True)

    st.divider()

    # Gráfico de Linha Temporal Separado por Meio (Linha 2)
    st.subheader("📈 Evolução Diária Dividida por Meio de Cadastro")
    df_tempo_meio = df_melted.groupby(["data", "Meio de Cadastro"])["Quantidade"].sum().reset_index()
    df_tempo_meio = df_tempo_meio.sort_values("data")
    df_tempo_meio["data_str"] = df_tempo_meio["data"].dt.strftime("%d/%m/%Y")

    fig_line_meio = px.line(
        df_tempo_meio,
        x="data_str",
        y="Quantidade",
        color="Meio de Cadastro",
        markers=True,
        color_discrete_map={"SYSVET Erro": "#ef4444", "SYSVET Êxito": "#22c55e", "Faturado": "#3b82f6"}
    )
    fig_line_meio.update_layout(
        xaxis_title="Data",
        yaxis_title="Quantidade",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
        height=380,
        legend_title="Meio de Cadastro"
    )
    st.plotly_chart(fig_line_meio, use_container_width=True)


# =========================================================
# LANÇAR PRODUTIVIDADE
# =========================================================

elif pagina == "📝 Lançar produtividade":
    st.title("📝 Lançar produtividade")

    colaboradores = buscar_colaboradores()

    if colaboradores.empty:
        st.warning("⚠️ Nenhum colaborador cadastrado.")
        st.info("O Administrador precisa cadastrar colaboradores no menu correspondente.")
    else:
        with st.form("form_produtividade"):
            data_lancamento = st.date_input("📅 Data", value=date.today())

            if st.session_state.perfil == "admin":
                colaborador = st.selectbox("👤 Colaborador", colaboradores["nome"].tolist())
            else:
                colaborador = st.session_state.usuario_logado
                st.info(f"👤 Lançando em nome de: **{colaborador}**")

            col1, col2, col3 = st.columns(3)
            with col1:
                erro = st.number_input("❌ SYSVET com erro", min_value=0, value=0, step=1)
            with col2:
                exito = st.number_input("✅ SYSVET com êxito", min_value=0, value=0, step=1)
            with col3:
                faturado = st.number_input("📁 Faturado", min_value=0, value=0, step=1)

            total = erro + exito + faturado
            st.info(f"📊 Produtividade total: {total}")

            salvar = st.form_submit_button("💾 SALVAR PRODUTIVIDADE", use_container_width=True)

            if salvar:
                conn = conectar()
                conn.execute(
                    """
                    INSERT INTO produtividade (data, colaborador, sysvet_erro, sysvet_exito, faturado)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (str(data_lancamento), colaborador, int(erro), int(exito), int(faturado))
                )
                conn.commit()
                conn.close()
                st.success("✅ Produtividade registrada com sucesso!")
                st.rerun()


# =========================================================
# COLABORADORES (Somente Admin)
# =========================================================

elif pagina == "👥 Colaboradores" and st.session_state.perfil == "admin":
    st.title("👥 Colaboradores")

    with st.form("form_colaborador"):
        nome = st.text_input("Nome do colaborador")
        cadastrar = st.form_submit_button("➕ CADASTRAR COLABORADOR", use_container_width=True)

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
    colaboradores = buscar_colaboradores()
    if colaboradores.empty:
        st.info("Nenhum colaborador cadastrado.")
    else:
        st.dataframe(colaboradores[["id", "nome"]], use_container_width=True, hide_index=True)


# =========================================================
# GERENCIAR ACESSOS DE COLABORADORES (Somente Admin)
# =========================================================

elif pagina == "🔑 Gerenciar Acessos" and st.session_state.perfil == "admin":
    st.title("🔑 Gerenciar Acessos dos Colaboradores")
    st.caption("Cadastre a senha para que seus colaboradores possam entrar e registrar a própria produtividade.")

    colaboradores_disp = buscar_colaboradores()

    if colaboradores_disp.empty:
        st.warning("⚠️ Cadastre colaboradores primeiro no menu 'Colaboradores'.")
    else:
        with st.form("form_acesso"):
            colab_nome = st.selectbox("Selecione o Colaborador", colaboradores_disp["nome"].tolist())
            senha_colab = st.text_input("Senha de acesso para este colaborador", type="password")
            salvar_acesso = st.form_submit_button("💾 SALVAR/ATUALIZAR ACESSO", use_container_width=True)

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
                    st.success(f"✅ Acesso configurado com sucesso para {colab_nome}!")
                    st.rerun()

    st.divider()
    st.subheader("📋 Acessos Cadastrados")
    df_acessos = buscar_acessos()
    if df_acessos.empty:
        st.info("Nenhum acesso configurado.")
    else:
        df_exibicao = df_acessos.copy()
        df_exibicao["senha"] = "••••••"
        st.dataframe(df_exibicao[["id", "nome", "senha"]], use_container_width=True, hide_index=True)


# =========================================================
# HISTÓRICO
# =========================================================

elif pagina == "📋 Histórico":
    st.title("📋 Histórico de produtividade")

    df = buscar_produtividade()

    if st.session_state.perfil == "colaborador":
        df = df[df["colaborador"] == st.session_state.usuario_logado]

    if df.empty:
        st.info("Nenhum lançamento encontrado.")
    else:
        visualizar = df[
            [
                "id",
                "data",
                "colaborador",
                "sysvet_erro",
                "sysvet_exito",
                "faturado",
                "produtividade_total"
            ]
        ].copy()

        visualizar["data"] = visualizar["data"].dt.strftime("%d/%m/%Y")
        visualizar.columns = [
            "ID",
            "Data",
            "Colaborador",
            "SYSVET Erro",
            "SYSVET Êxito",
            "Faturado",
            "Produtividade Total"
        ]

        st.dataframe(visualizar, use_container_width=True, hide_index=True)

        if st.session_state.perfil == "admin":
            st.divider()
            st.subheader("🗑️ Excluir registros de uma data")
            st.warning("⚠️ Atenção: esta função excluirá TODOS os lançamentos da data selecionada.")

            data_exclusao = st.date_input("📅 Selecione a data que deseja excluir", value=date.today(), key="data_exclusao")

            registros_data = df[df["data"].dt.date == data_exclusao].copy()

            if not registros_data.empty:
                total_data = int(registros_data["produtividade_total"].sum())
                st.error(f"Existem {len(registros_data)} lançamento(s) nessa data, totalizando {total_data} de produtividade.")

                confirmar_data = st.checkbox("✅ Confirmo que quero excluir TODOS os registros desta data.", key="confirmar_exclusao_data")

                if confirmar_data:
                    if st.button("🗑️ EXCLUIR TODOS OS REGISTROS DESTA DATA", type="primary", use_container_width=True, key="botao_excluir_data"):
                        conn = conectar()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM produtividade WHERE data = ?", (str(data_exclusao),))
                        quantidade_excluida = cursor.rowcount
                        conn.commit()
                        conn.close()
                        st.success(f"✅ {quantidade_excluida} registro(s) foram excluídos com sucesso.")
                        st.rerun()


# =========================================================
# EXPORTAR / BACKUP (Somente Admin)
# =========================================================

elif pagina == "📥 Exportar / Backup" and st.session_state.perfil == "admin":
    st.title("📥 Exportar Dados e Backup do Sistema")
    st.caption("Evite perder seus dados caso o servidor reinicie: faça download do backup regularmente.")

    df = buscar_produtividade()

    if not df.empty:
        st.subheader("📊 Exportar para Excel (.xlsx)")
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Produtividade")
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Baixar Relatório em Excel",
            data=processed_data,
            file_name=f"produtividade_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.divider()
    st.subheader("💾 Backup Completo do Sistema (JSON)")
    st.write("Baixe um arquivo de segurança contendo todos os cadastros, senhas e lançamentos.")

    json_backup = gerar_backup_json()
    st.download_button(
        label="📥 Baixar Arquivo de Backup (.json)",
        data=json_backup,
        file_name=f"backup_sistema_{date.today()}.json",
        mime="application/json",
        use_container_width=True
    )

    st.divider()
    st.subheader("♻️ Restaurar Sistema via Backup")
    st.write("Caso o aplicativo tenha reiniciado do zero, envie o arquivo JSON de backup gerado anteriormente para recuperar todos os seus dados instantaneamente.")

    arquivo_submetido = st.file_uploader("Enviar arquivo de backup (.json)", type=["json"])
    if arquivo_submetido is not None:
        conteudo_json = arquivo_submetido.getvalue().decode("utf-8")
        if st.button("🔄 RESTAURAR DADOS AGORA", type="primary", use_container_width=True):
            sucesso, mensagem = restaurar_backup_json(conteudo_json)
            if sucesso:
                st.success(mensagem)
                st.rerun()
            else:
                st.error(mensagem)


# =========================================================
# ALTERAR SENHA (Somente Admin)
# =========================================================

elif pagina == "🔐 Alterar senha" and st.session_state.perfil == "admin":
    st.title("🔐 Alterar senha do Administrador")

    with st.form("form_senha"):
        senha_atual = st.text_input("Senha atual", type="password")
        nova_senha = st.text_input("Nova senha", type="password")
        confirma_senha = st.text_input("Confirme a nova senha", type="password")

        atualizar = st.form_submit_button("🔒 ALTERAR SENHA", use_container_width=True)

        if atualizar:
            if senha_atual != buscar_senha():
                st.error("❌ Senha atual incorreta.")
            elif not nova_senha.strip():
                st.error("❌ A nova senha não pode estar em branco.")
            elif nova_senha != confirma_senha:
                st.error("❌ As senhas novas não coincidem.")
            else:
                alterar_senha(nova_senha)
                st.success("✅ Senha alterada com sucesso!")
