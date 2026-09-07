import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date
from io import BytesIO


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

    cursor.execute(
        "SELECT COUNT(*) FROM configuracoes"
    )

    quantidade = cursor.fetchone()[0]

    if quantidade == 0:

        cursor.execute(
            """
            INSERT INTO configuracoes
            (id, senha)
            VALUES (1, ?)
            """,
            ("2010",)
        )

    conn.commit()
    conn.close()


criar_banco()


# =========================================================
# FUNÇÕES
# =========================================================

def buscar_senha():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT senha
        FROM configuracoes
        WHERE id = 1
    """)

    resultado = cursor.fetchone()

    conn.close()

    if resultado:
        return resultado[0]

    return "2010"


def alterar_senha(nova_senha):

    conn = conectar()

    conn.execute(
        """
        UPDATE configuracoes
        SET senha = ?
        WHERE id = 1
        """,
        (nova_senha,)
    )

    conn.commit()
    conn.close()


def buscar_colaboradores():

    conn = conectar()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM colaboradores
        ORDER BY nome
        """,
        conn
    )

    conn.close()

    return df


def buscar_produtividade():

    conn = conectar()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM produtividade
        ORDER BY data DESC, id DESC
        """,
        conn
    )

    conn.close()

    if not df.empty:

        df["data"] = pd.to_datetime(df["data"])

        df["total_sysvet"] = (
            df["sysvet_erro"] +
            df["sysvet_exito"]
        )

        df["produtividade_total"] = (
            df["sysvet_erro"] +
            df["sysvet_exito"] +
            df["faturado"]
        )

        df["taxa_exito"] = df.apply(
            lambda linha:
            (
                linha["sysvet_exito"] /
                linha["total_sysvet"] *
                100
            )
            if linha["total_sysvet"] > 0
            else 0,
            axis=1
        )

    return df


# =========================================================
# MODO VISUAL
# =========================================================

if "modo_noturno" not in st.session_state:
    st.session_state.modo_noturno = False


# =========================================================
# CSS
# =========================================================

if not st.session_state.modo_noturno:

    st.markdown("""
    <style>

    .stApp {
        background-color: #f4f7fb;
        color: #172033;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #0f172a 0%,
            #173b8f 100%
        );
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    h1 {
        color: #173b8f !important;
        font-weight: 800;
    }

    h2, h3 {
        color: #1e3a8a !important;
    }

    p, label {
        color: #263247;
    }

    div[data-testid="stMetric"] {
        background: white;
        padding: 18px;
        border-radius: 15px;
        border: 1px solid #e1e7ef;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
    }

    div[data-testid="stMetricValue"] {
        color: #173b8f !important;
        font-weight: 800;
    }

    div[data-baseweb="input"] {
        background-color: white !important;
        border-radius: 10px;
    }

    div[data-baseweb="input"] input {
        color: #172033 !important;
        background-color: white !important;
    }

    div[data-baseweb="select"] > div {
        background-color: white !important;
        color: #172033 !important;
    }

    div[data-baseweb="select"] span {
        color: #172033 !important;
    }

    div[data-testid="stNumberInput"] input {
        color: #172033 !important;
        background-color: white !important;
    }

    div[data-testid="stDateInput"] input {
        color: #172033 !important;
        background-color: white !important;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
    }

    .stDownloadButton > button {
        border-radius: 10px;
        font-weight: 700;
    }

    </style>
    """, unsafe_allow_html=True)


else:

    st.markdown("""
    <style>

    .stApp {
        background-color: #0b1120;
        color: #e5e7eb;
    }

    [data-testid="stHeader"] {
        background-color: #0b1120;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #020617 0%,
            #111827 100%
        );
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    h1 {
        color: #60a5fa !important;
        font-weight: 800;
    }

    h2, h3 {
        color: #93c5fd !important;
    }

    p, label {
        color: #cbd5e1 !important;
    }

    div[data-testid="stMetric"] {
        background-color: #111827 !important;
        padding: 18px;
        border-radius: 15px;
        border: 1px solid #263244;
        box-shadow: 0 5px 20px rgba(0,0,0,0.35);
    }

    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #60a5fa !important;
        font-weight: 800;
    }

    div[data-baseweb="input"] {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="input"] input {
        color: #ffffff !important;
        background-color: #1e293b !important;
        caret-color: #60a5fa !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        color: #ffffff !important;
    }

    div[data-baseweb="select"] span {
        color: #ffffff !important;
    }

    div[data-baseweb="select"] input {
        color: #ffffff !important;
    }

    ul[data-baseweb="menu"] {
        background-color: #1e293b !important;
    }

    li[data-baseweb="option"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }

    li[data-baseweb="option"]:hover {
        background-color: #334155 !important;
    }

    div[data-testid="stNumberInput"] input {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    div[data-testid="stDateInput"] input {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    div[data-testid="stTextInput"] input {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    input[type="password"] {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    div[data-testid="stCheckbox"] label {
        color: #e5e7eb !important;
    }

    div[data-testid="stRadio"] label {
        color: #e5e7eb !important;
    }

    div[data-baseweb="tag"] {
        background-color: #2563eb !important;
    }

    div[data-baseweb="tag"] span {
        color: white !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #334155;
        border-radius: 12px;
    }

    div[data-testid="stAlert"] {
        background-color: #172033 !important;
        color: #e5e7eb !important;
        border-radius: 12px;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
        background-color: #1e40af;
        color: white;
        border: 1px solid #3b82f6;
    }

    .stButton > button:hover {
        background-color: #2563eb;
        color: white;
    }

    .stDownloadButton > button {
        border-radius: 10px;
        font-weight: 700;
        background-color: #1e40af;
        color: white;
    }

    hr {
        border-color: #334155 !important;
    }

    </style>
    """, unsafe_allow_html=True)


# =========================================================
# LOGIN
# =========================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False


if not st.session_state.autenticado:

    st.title("📊 PRODUCT")

    st.caption(
        "Sistema de Controle de Produtividade"
    )

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.subheader("🔐 Acesso ao sistema")

        senha = st.text_input(
            "Senha de acesso",
            type="password",
            key="senha_login"
        )

        entrar = st.button(
            "🔓 ENTRAR",
            use_container_width=True,
            type="primary"
        )

        if entrar:

            if senha == buscar_senha():

                st.session_state.autenticado = True

                st.rerun()

            else:

                st.error(
                    "❌ Senha incorreta."
                )

    st.stop()


# =========================================================
# MENU LATERAL
# =========================================================

st.sidebar.markdown("# 📊 PRODUCT")

st.sidebar.caption(
    "Sistema de Controle de Produtividade"
)

st.sidebar.divider()


# =========================================================
# MODO NOTURNO
# =========================================================

if st.session_state.modo_noturno:

    texto_modo = "☀️ MODO CLARO"

else:

    texto_modo = "🌙 MODO NOTURNO"


if st.sidebar.button(
    texto_modo,
    use_container_width=True
):

    st.session_state.modo_noturno = (
        not st.session_state.modo_noturno
    )

    st.rerun()


st.sidebar.divider()


pagina = st.sidebar.radio(
    "MENU",
    [
        "📈 Dashboard",
        "📝 Lançar produtividade",
        "👥 Colaboradores",
        "📋 Histórico",
        "📥 Exportar",
        "🔐 Alterar senha"
    ]
)


st.sidebar.divider()


if st.sidebar.button(
    "🚪 SAIR",
    use_container_width=True
):

    st.session_state.autenticado = False

    st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

if pagina == "📈 Dashboard":

    st.title("📊 Dashboard")

    st.caption(
        "Visão geral da produtividade da equipe"
    )

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Ainda não existem registros."
        )

        st.stop()

    st.divider()

    st.subheader("🔎 Filtros")

    col1, col2, col3 = st.columns(3)

    lista_colaboradores = sorted(
        df["colaborador"]
        .unique()
        .tolist()
    )

    with col1:

        colaborador = st.selectbox(
            "👤 Colaborador",
            ["Todos os colaboradores"]
            +
            lista_colaboradores
        )

    data_min = df["data"].min().date()
    data_max = df["data"].max().date()

    with col2:

        periodo = st.date_input(
            "📅 Período",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max
        )

    with col3:

        st.write("")

        if st.button(
            "🔄 Atualizar",
            use_container_width=True
        ):

            st.rerun()

    if (
        isinstance(periodo, tuple)
        and len(periodo) == 2
    ):

        inicio, fim = periodo

        df_filtrado = df[
            (df["data"].dt.date >= inicio)
            &
            (df["data"].dt.date <= fim)
        ].copy()

    else:

        df_filtrado = df.copy()

    if colaborador != "Todos os colaboradores":

        df_filtrado = df_filtrado[
            df_filtrado["colaborador"] == colaborador
        ].copy()

    if df_filtrado.empty:

        st.warning(
            "Não existem registros para os filtros selecionados."
        )

        st.stop()

    erro = int(
        df_filtrado["sysvet_erro"].sum()
    )

    exito = int(
        df_filtrado["sysvet_exito"].sum()
    )

    faturado = int(
        df_filtrado["faturado"].sum()
    )

    total_sysvet = erro + exito

    produtividade = (
        erro +
        exito +
        faturado
    )

    taxa = (
        exito /
        total_sysvet *
        100
        if total_sysvet > 0
        else 0
    )

    st.subheader("📌 Indicadores")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "❌ SYSVET ERRO",
        f"{erro:,}"
    )

    c2.metric(
        "✅ SYSVET ÊXITO",
        f"{exito:,}"
    )

    c3.metric(
        "📁 FATURADO",
        f"{faturado:,}"
    )

    c4.metric(
        "📊 PRODUTIVIDADE",
        f"{produtividade:,}"
    )

    c5.metric(
        "🎯 TAXA DE ÊXITO",
        f"{taxa:.1f}%"
    )

    st.divider()

    if colaborador == "Todos os colaboradores":

        st.success(
            "👥 Visualizando toda a equipe."
        )

    else:

        st.success(
            f"👤 Visualizando somente: {colaborador}"
        )

    resumo = (
        df_filtrado
        .groupby("colaborador")
        .agg(
            SYSVET_Erro=("sysvet_erro", "sum"),
            SYSVET_Exito=("sysvet_exito", "sum"),
            Faturado=("faturado", "sum"),
            Total=("produtividade_total", "sum")
        )
        .reset_index()
        .sort_values(
            "Total",
            ascending=False
        )
    )

    st.subheader(
        "🏆 Ranking de produtividade"
    )

    grafico = px.bar(
        resumo,
        x="colaborador",
        y="Total",
        color="Total",
        text="Total",
        color_continuous_scale="Blues"
    )

    grafico.update_traces(
        textposition="outside"
    )

    grafico.update_layout(
        height=430,
        xaxis_title="Colaborador",
        yaxis_title="Produtividade",
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(
        grafico,
        use_container_width=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📊 Composição")

        composicao = pd.DataFrame({
            "Tipo": [
                "SYSVET Erro",
                "SYSVET Êxito",
                "Faturado"
            ],
            "Quantidade": [
                erro,
                exito,
                faturado
            ]
        })

        pizza = px.pie(
            composicao,
            names="Tipo",
            values="Quantidade",
            hole=0.55,
            color="Tipo",
            color_discrete_map={
                "SYSVET Erro": "#ef4444",
                "SYSVET Êxito": "#22c55e",
                "Faturado": "#2563eb"
            }
        )

        pizza.update_layout(
            height=400,
            paper_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(
            pizza,
            use_container_width=True
        )

    with col2:

        st.subheader("📈 Evolução")

        diario = (
            df_filtrado
            .groupby("data")
            .agg(
                Produtividade=(
                    "produtividade_total",
                    "sum"
                ),
                Faturado=(
                    "faturado",
                    "sum"
                )
            )
            .reset_index()
        )

        linha = px.line(
            diario,
            x="data",
            y=[
                "Produtividade",
                "Faturado"
            ],
            markers=True
        )

        linha.update_layout(
            height=400,
            xaxis_title="Data",
            yaxis_title="Quantidade",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(
            linha,
            use_container_width=True
        )

    if colaborador != "Todos os colaboradores":

        st.divider()

        st.subheader(
            f"👤 Detalhamento de {colaborador}"
        )

        detalhes = df_filtrado[
            [
                "data",
                "sysvet_erro",
                "sysvet_exito",
                "faturado",
                "total_sysvet",
                "produtividade_total",
                "taxa_exito"
            ]
        ].copy()

        detalhes["data"] = (
            detalhes["data"]
            .dt.strftime("%d/%m/%Y")
        )

        detalhes["taxa_exito"] = (
            detalhes["taxa_exito"]
            .round(1)
            .astype(str)
            +
            "%"
        )

        detalhes.columns = [
            "Data",
            "SYSVET Erro",
            "SYSVET Êxito",
            "Faturado",
            "Total SYSVET",
            "Produtividade Total",
            "Taxa de Êxito"
        ]

        st.dataframe(
            detalhes,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# LANÇAR PRODUTIVIDADE
# =========================================================

elif pagina == "📝 Lançar produtividade":

    st.title("📝 Lançar produtividade")

    colaboradores = buscar_colaboradores()

    if colaboradores.empty:

        st.warning(
            "⚠️ Nenhum colaborador cadastrado."
        )

        st.info(
            "Acesse o menu Colaboradores."
        )

    else:

        with st.form("form_produtividade"):

            data_lancamento = st.date_input(
                "📅 Data",
                value=date.today()
            )

            colaborador = st.selectbox(
                "👤 Colaborador",
                colaboradores["nome"].tolist()
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                erro = st.number_input(
                    "❌ SYSVET com erro",
                    min_value=0,
                    value=0,
                    step=1
                )

            with col2:

                exito = st.number_input(
                    "✅ SYSVET com êxito",
                    min_value=0,
                    value=0,
                    step=1
                )

            with col3:

                faturado = st.number_input(
                    "📁 Faturado",
                    min_value=0,
                    value=0,
                    step=1
                )

            total = (
                erro +
                exito +
                faturado
            )

            st.info(
                f"📊 Produtividade total: {total}"
            )

            salvar = st.form_submit_button(
                "💾 SALVAR PRODUTIVIDADE",
                use_container_width=True
            )

            if salvar:

                conn = conectar()

                conn.execute(
                    """
                    INSERT INTO produtividade
                    (
                        data,
                        colaborador,
                        sysvet_erro,
                        sysvet_exito,
                        faturado
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(data_lancamento),
                        colaborador,
                        int(erro),
                        int(exito),
                        int(faturado)
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    "✅ Produtividade registrada com sucesso!"
                )

                st.rerun()


# =========================================================
# COLABORADORES
# =========================================================

elif pagina == "👥 Colaboradores":

    st.title("👥 Colaboradores")

    with st.form("form_colaborador"):

        nome = st.text_input(
            "Nome do colaborador"
        )

        cadastrar = st.form_submit_button(
            "➕ CADASTRAR COLABORADOR",
            use_container_width=True
        )

        if cadastrar:

            if not nome.strip():

                st.error(
                    "Digite o nome do colaborador."
                )

            else:

                try:

                    conn = conectar()

                    conn.execute(
                        """
                        INSERT INTO colaboradores
                        (nome)
                        VALUES (?)
                        """,
                        (nome.strip(),)
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        f"✅ {nome} cadastrado com sucesso!"
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "⚠️ Esse colaborador já está cadastrado."
                    )

    st.divider()

    colaboradores = buscar_colaboradores()

    if colaboradores.empty:

        st.info(
            "Nenhum colaborador cadastrado."
        )

    else:

        st.dataframe(
            colaboradores[
                ["id", "nome"]
            ],
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# HISTÓRICO
# =========================================================

elif pagina == "📋 Histórico":

    st.title("📋 Histórico de produtividade")

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Nenhum lançamento encontrado."
        )

    else:

        # =================================================
        # EXCLUSÃO POR DATA
        # =================================================

        st.subheader(
            "🗑️ Excluir registros de uma data"
        )

        st.warning(
            "⚠️ Atenção: esta função excluirá TODOS os "
            "lançamentos da data selecionada."
        )

        data_exclusao = st.date_input(
            "📅 Selecione a data que deseja excluir",
            value=date.today(),
            key="data_exclusao"
        )

        registros_data = df[
            df["data"].dt.date == data_exclusao
        ].copy()

        if registros_data.empty:

            st.info(
                "Nenhum registro encontrado nessa data."
            )

        else:

            total_data = int(
                registros_data["produtividade_total"].sum()
            )

            st.error(
                f"Existem {len(registros_data)} lançamento(s) "
                f"nessa data, totalizando {total_data} "
                "de produtividade."
            )

            visualizar = registros_data[
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

            visualizar["data"] = (
                visualizar["data"]
                .dt.strftime("%d/%m/%Y")
            )

            visualizar.columns = [
                "ID",
                "Data",
                "Colaborador",
                "SYSVET Erro",
                "SYSVET Êxito",
                "Faturado",
                "Produtividade Total"
            ]

            st.dataframe(
                visualizar,
                use_container_width=True,
                hide_index=True
            )

            confirmar_data = st.checkbox(
                "✅ Confirmo que quero excluir TODOS os registros desta data.",
                key="confirmar_exclusao_data"
            )

            if confirmar_data:

                if st.button(
                    "🗑️ EXCLUIR TODOS OS REGISTROS DESTA DATA",
                    type="primary",
                    use_container_width=True,
                    key="botao_excluir_data"
                ):

                    conn = conectar()

                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        DELETE FROM produtividade
                        WHERE data = ?
                        """,
                        (str(data_exclusao),)
                    )

                    quantidade_excluida = cursor.rowcount

                    conn.commit()
                    conn.close()

                    st.success(
                        f"✅ {quantidade_excluida} registro(s) "
                        "foram excluídos com sucesso."
                    )

                    st.rerun()

        st.divider()

        # =================================================
        # EXCLUSÃO INDIVIDUAL
        # =================================================

        st.subheader(
            "🗑️ Excluir lançamento individual"
        )

        ids = df["id"].tolist()

        id_escolhido = st.selectbox(
            "Selecione o ID do lançamento",
            ids,
            key="id_exclusao"
        )

        registro = df[
            df["id"] == id_escolhido
        ].iloc[0]

        st.info(
            f"👤 {registro['colaborador']} | "
            f"📅 {registro['data'].strftime('%d/%m/%Y')} | "
            f"📊 Produtividade: "
            f"{int(registro['produtividade_total'])}"
        )

        confirmar_individual = st.checkbox(
            "✅ Confirmo a exclusão deste lançamento.",
            key="confirmar_exclusao_individual"
        )

        if confirmar_individual:

            if st.button(
                "🗑️ EXCLUIR LANÇAMENTO",
                type="primary",
                use_container_width=True,
                key="botao_excluir_individual"
            ):

                conn = conectar()

                conn.execute(
                    """
                    DELETE FROM produtividade
                    WHERE id = ?
                    """,
                    (int(id_escolhido),)
                )

                conn.commit()
                conn.close()

                st.success(
                    "✅ Lançamento excluído com sucesso."
                )

                st.rerun()

        st.divider()

        # =================================================
        # HISTÓRICO COMPLETO
        # =================================================

        st.subheader(
            "📋 Todos os lançamentos"
        )

        historico = df[
            [
                "id",
                "data",
                "colaborador",
                "sysvet_erro",
                "sysvet_exito",
                "faturado",
                "total_sysvet",
                "produtividade_total",
                "taxa_exito"
            ]
        ].copy()

        historico["data"] = (
            historico["data"]
            .dt.strftime("%d/%m/%Y")
        )

        historico["taxa_exito"] = (
            historico["taxa_exito"]
            .round(1)
            .astype(str)
            +
            "%"
        )

        historico.columns = [
            "ID",
            "Data",
            "Colaborador",
            "SYSVET Erro",
            "SYSVET Êxito",
            "Faturado",
            "Total SYSVET",
            "Produtividade Total",
            "Taxa de Êxito"
        ]

        st.dataframe(
            historico,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# EXPORTAR
# =========================================================

elif pagina == "📥 Exportar":

    st.title("📥 Exportar dados")

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Nenhum dado disponível."
        )

    else:

        colaboradores = sorted(
            df["colaborador"]
            .unique()
            .tolist()
        )

        colaborador_exportar = st.selectbox(
            "👤 Escolha o colaborador",
            [
                "Todos os colaboradores"
            ]
            +
            colaboradores
        )

        if colaborador_exportar == "Todos os colaboradores":

            dados = df.copy()

        else:

            dados = df[
                df["colaborador"] == colaborador_exportar
            ].copy()

        exportar = dados.copy()

        exportar["data"] = (
            exportar["data"]
            .dt.strftime("%d/%m/%Y")
        )

        exportar["taxa_exito"] = (
            exportar["taxa_exito"]
            .round(1)
        )

        exportar = exportar[
            [
                "id",
                "data",
                "colaborador",
                "sysvet_erro",
                "sysvet_exito",
                "faturado",
                "total_sysvet",
                "produtividade_total",
                "taxa_exito"
            ]
        ]

        exportar.columns = [
            "ID",
            "Data",
            "Colaborador",
            "SYSVET Erro",
            "SYSVET Êxito",
            "Faturado",
            "Total SYSVET",
            "Produtividade Total",
            "Taxa de Êxito"
        ]

        arquivo = BytesIO()

        with pd.ExcelWriter(
            arquivo,
            engine="openpyxl"
        ) as writer:

            exportar.to_excel(
                writer,
                index=False,
                sheet_name="Produtividade"
            )

        arquivo.seek(0)

        st.success(
            f"✅ {len(exportar)} registro(s) "
            "pronto(s) para exportação."
        )

        st.download_button(
            label="📥 BAIXAR EXCEL",
            data=arquivo,
            file_name="PRODUCT_produtividade.xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True
        )


# =========================================================
# ALTERAR SENHA
# =========================================================

elif pagina == "🔐 Alterar senha":

    st.title("🔐 Alterar senha")

    st.info(
        "Altere a senha utilizada para entrar no sistema."
    )

    with st.form("form_alterar_senha"):

        senha_atual = st.text_input(
            "🔑 Senha atual",
            type="password"
        )

        nova_senha = st.text_input(
            "🆕 Nova senha",
            type="password"
        )

        confirmar_senha = st.text_input(
            "🔁 Confirmar nova senha",
            type="password"
        )

        alterar = st.form_submit_button(
            "🔐 ALTERAR SENHA",
            use_container_width=True
        )

        if alterar:

            if senha_atual != buscar_senha():

                st.error(
                    "❌ A senha atual está incorreta."
                )

            elif not nova_senha:

                st.error(
                    "❌ Digite uma nova senha."
                )

            elif nova_senha != confirmar_senha:

                st.error(
                    "❌ As senhas não são iguais."
                )

            elif len(nova_senha) < 4:

                st.error(
                    "❌ A senha deve ter pelo menos 4 caracteres."
                )

            else:

                alterar_senha(nova_senha)

                st.success(
                    "✅ Senha alterada com sucesso!"
                )
