import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

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
# CSS - VISUAL MODERNO / POWER BI
# =========================================================

st.markdown("""
<style>

    /* Fundo principal */
    .stApp {
        background-color: #f4f7fb;
    }

    /* Remove espaço superior */
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #111827 0%,
            #172554 100%
        );
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Logo */
    .product-logo {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0;
    }

    .product-subtitle {
        color: #93c5fd;
        font-size: 13px;
        margin-bottom: 25px;
    }

    /* Cabeçalho */
    .dashboard-header {
        background: linear-gradient(
            135deg,
            #1d4ed8,
            #4f46e5
        );
        padding: 24px 28px;
        border-radius: 18px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.18);
    }

    .dashboard-title {
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 3px;
    }

    .dashboard-subtitle {
        font-size: 14px;
        opacity: 0.88;
    }

    /* Cards KPI */
    .kpi-card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        min-height: 135px;
        box-shadow: 0 5px 20px rgba(15, 23, 42, 0.07);
        border: 1px solid #e5e7eb;
        position: relative;
        overflow: hidden;
    }

    .kpi-card:after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: #2563eb;
    }

    .kpi-icon {
        font-size: 25px;
        margin-bottom: 8px;
    }

    .kpi-label {
        color: #64748b;
        font-size: 13px;
        font-weight: 600;
    }

    .kpi-value {
        color: #0f172a;
        font-size: 29px;
        font-weight: 800;
        margin-top: 5px;
    }

    /* Seções */
    .section-title {
        font-size: 19px;
        font-weight: 750;
        color: #0f172a;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    /* Cards de ranking */
    .ranking-card {
        background: white;
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 9px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.05);
    }

    .ranking-position {
        font-size: 21px;
        font-weight: 800;
    }

    .ranking-name {
        font-weight: 700;
        color: #1e293b;
    }

    .ranking-total {
        font-weight: 800;
        color: #2563eb;
    }

    /* Informação */
    .info-box {
        background: #eff6ff;
        border-left: 5px solid #2563eb;
        padding: 14px 18px;
        border-radius: 10px;
        color: #1e3a8a;
        margin-bottom: 18px;
    }

    /* Login */
    .login-box {
        max-width: 430px;
        margin: 80px auto;
        background: white;
        padding: 35px;
        border-radius: 22px;
        box-shadow: 0 15px 50px rgba(15, 23, 42, 0.12);
    }

    /* Botões */
    .stButton > button {
        border-radius: 10px;
        font-weight: 650;
    }

    /* Métricas nativas */
    div[data-testid="stMetric"] {
        background: white;
        padding: 15px;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.05);
    }

    /* Tabelas */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# BANCO
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

    existe = cursor.fetchone()[0]

    if existe == 0:

        cursor.execute(
            """
            INSERT INTO configuracoes (id, senha)
            VALUES (1, ?)
            """,
            ("2010",)
        )

    conn.commit()
    conn.close()


criar_banco()


# =========================================================
# SENHA
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


# =========================================================
# LOGIN
# =========================================================

def tela_login():

    st.markdown("""
    <div class="login-box">

        <div style="
            text-align:center;
            font-size:48px;
        ">
            📊
        </div>

        <div style="
            text-align:center;
            font-size:32px;
            font-weight:800;
            color:#1d4ed8;
        ">
            PRODUCT
        </div>

        <div style="
            text-align:center;
            color:#64748b;
            margin-bottom:25px;
        ">
            Sistema de Controle de Produtividade
        </div>

    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        senha = st.text_input(
            "🔐 Senha de acesso",
            type="password"
        )

        entrar = st.button(
            "🔓 ENTRAR NO PRODUCT",
            use_container_width=True,
            type="primary"
        )

        if entrar:

            if senha == buscar_senha():

                st.session_state["autenticado"] = True

                st.rerun()

            else:

                st.error(
                    "❌ Senha incorreta."
                )


if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False


if not st.session_state["autenticado"]:

    tela_login()
    st.stop()


# =========================================================
# FUNÇÕES DE DADOS
# =========================================================

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

        df["data"] = pd.to_datetime(
            df["data"]
        )

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
            lambda x:
            (
                x["sysvet_exito"] /
                x["total_sysvet"] * 100
            )
            if x["total_sysvet"] > 0
            else 0,
            axis=1
        )

    return df


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    '<div class="product-logo">📊 PRODUCT</div>',
    unsafe_allow_html=True
)

st.sidebar.markdown(
    '<div class="product-subtitle">'
    'Controle de Produtividade'
    '</div>',
    unsafe_allow_html=True
)

st.sidebar.divider()

pagina = st.sidebar.radio(
    "NAVEGAÇÃO",
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

st.sidebar.caption(
    "Sistema PRODUCT"
)

if st.sidebar.button(
    "🚪 SAIR",
    use_container_width=True
):

    st.session_state["autenticado"] = False
    st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

if pagina == "📈 Dashboard":

    df = buscar_produtividade()

    st.markdown("""
    <div class="dashboard-header">

        <div class="dashboard-title">
            📊 Dashboard de Produtividade
        </div>

        <div class="dashboard-subtitle">
            Acompanhamento de desempenho individual e da equipe
        </div>

    </div>
    """, unsafe_allow_html=True)

    if df.empty:

        st.info(
            "Ainda não existem registros de produtividade."
        )

        st.stop()

    # =====================================================
    # FILTROS
    # =====================================================

    st.markdown(
        '<div class="section-title">🔎 Filtros do Dashboard</div>',
        unsafe_allow_html=True
    )

    filtro1, filtro2, filtro3 = st.columns(
        [2, 2, 1]
    )

    colaboradores = sorted(
        df["colaborador"]
        .dropna()
        .unique()
        .tolist()
    )

    with filtro1:

        colaborador_selecionado = st.selectbox(
            "👤 Colaborador",
            ["👥 Todos"] + colaboradores
        )

    data_min = df["data"].min().date()
    data_max = df["data"].max().date()

    with filtro2:

        periodo = st.date_input(
            "📅 Período",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max
        )

    with filtro3:

        st.write("")
        st.write("")

        limpar = st.button(
            "🔄 Atualizar",
            use_container_width=True
        )

        if limpar:
            st.rerun()

    # =====================================================
    # FILTRO DATA
    # =====================================================

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

    # =====================================================
    # FILTRO COLABORADOR
    # =====================================================

    if colaborador_selecionado != "👥 Todos":

        df_filtrado = df_filtrado[
            df_filtrado["colaborador"]
            == colaborador_selecionado
        ].copy()

    # =====================================================
    # RESULTADO
    # =====================================================

    if df_filtrado.empty:

        st.warning(
            "⚠️ Não existem registros para os filtros selecionados."
        )

        st.stop()

    # =====================================================
    # TÍTULO DA VISÃO
    # =====================================================

    if colaborador_selecionado == "👥 Todos":

        st.markdown(
            """
            <div class="info-box">
                👥 <b>Visão geral da equipe</b><br>
                Os indicadores abaixo representam todos os colaboradores selecionados.
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="info-box">
                👤 <b>Visualizando:</b> {colaborador_selecionado}<br>
                Os indicadores abaixo representam somente este colaborador.
            </div>
            """,
            unsafe_allow_html=True
        )

    # =====================================================
    # KPIs
    # =====================================================

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
        exito / total_sysvet * 100
        if total_sysvet > 0
        else 0
    )

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">❌</div>
                <div class="kpi-label">SYSVET ERRO</div>
                <div class="kpi-value">{erro:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with k2:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">✅</div>
                <div class="kpi-label">SYSVET ÊXITO</div>
                <div class="kpi-value">{exito:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with k3:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">📁</div>
                <div class="kpi-label">FATURADO</div>
                <div class="kpi-value">{faturado:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with k4:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">📊</div>
                <div class="kpi-label">PRODUTIVIDADE TOTAL</div>
                <div class="kpi-value">{produtividade:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with k5:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-icon">🎯</div>
                <div class="kpi-label">TAXA DE ÊXITO</div>
                <div class="kpi-value">{taxa:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    # =====================================================
    # RESUMO POR COLABORADOR
    # =====================================================

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

    # =====================================================
    # RANKING VISUAL + COMPOSIÇÃO
    # =====================================================

    col_rank, col_comp = st.columns(
        [1, 1.5]
    )

    with col_rank:

        st.markdown(
            '<div class="section-title">🏆 Ranking</div>',
            unsafe_allow_html=True
        )

        for pos, (_, row) in enumerate(
            resumo.iterrows(),
            start=1
        ):

            if pos == 1:
                medalha = "🥇"

            elif pos == 2:
                medalha = "🥈"

            elif pos == 3:
                medalha = "🥉"

            else:
                medalha = f"{pos}º"

            st.markdown(
                f"""
                <div class="ranking-card">

                    <span class="ranking-position">
                        {medalha}
                    </span>

                    &nbsp;&nbsp;

                    <span class="ranking-name">
                        {row['colaborador']}
                    </span>

                    <span style="float:right"
                          class="ranking-total">
                        {int(row['Total']):,}
                    </span>

                </div>
                """,
                unsafe_allow_html=True
            )

    with col_comp:

        st.markdown(
            '<div class="section-title">📊 Composição da produtividade</div>',
            unsafe_allow_html=True
        )

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

        fig = px.pie(
            composicao,
            names="Tipo",
            values="Quantidade",
            hole=0.58,
            color="Tipo",
            color_discrete_map={
                "SYSVET Erro": "#ef4444",
                "SYSVET Êxito": "#22c55e",
                "Faturado": "#3b82f6"
            }
        )

        fig.update_layout(
            height=350,
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10
            ),
            legend=dict(
                orientation="h",
                y=-0.08
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =====================================================
    # EVOLUÇÃO DIÁRIA
    # =====================================================

    st.markdown(
        '<div class="section-title">📈 Evolução da produtividade</div>',
        unsafe_allow_html=True
    )

    diario = (
        df_filtrado
        .groupby("data")
        .agg(
            SYSVET_Erro=("sysvet_erro", "sum"),
            SYSVET_Exito=("sysvet_exito", "sum"),
            Faturado=("faturado", "sum"),
            Total=("produtividade_total", "sum")
        )
        .reset_index()
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=diario["data"],
            y=diario["Total"],
            mode="lines+markers",
            name="Produtividade",
            line=dict(
                color="#2563eb",
                width=4
            ),
            marker=dict(
                size=8
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=diario["data"],
            y=diario["Faturado"],
            mode="lines+markers",
            name="Faturado",
            line=dict(
                color="#22c55e",
                width=3
            )
        )
    )

    fig.update_layout(
        height=420,
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20
        ),
        xaxis=dict(
            title="Data",
            showgrid=False
        ),
        yaxis=dict(
            title="Quantidade",
            gridcolor="#e5e7eb"
        ),
        legend=dict(
            orientation="h",
            y=1.08,
            x=0
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # DETALHAMENTO INDIVIDUAL
    # =====================================================

    if colaborador_selecionado != "👥 Todos":

        st.markdown(
            '<div class="section-title">'
            '👤 Detalhamento do colaborador'
            '</div>',
            unsafe_allow_html=True
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
            + "%"
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
            "⚠️ Cadastre primeiro os colaboradores."
        )

        st.info(
            "Acesse o menu 👥 Colaboradores."
        )

    else:

        st.markdown(
            '<div class="info-box">'
            'Preencha os dados abaixo para registrar '
            'a produtividade do colaborador.'
            '</div>',
            unsafe_allow_html=True
        )

        with st.form(
            "form_produtividade"
        ):

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
                f"📊 Produtividade total: **{total}**"
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

    with st.form(
        "form_colaborador"
    ):

        nome = st.text_input(
            "Nome do colaborador"
        )

        adicionar = st.form_submit_button(
            "➕ CADASTRAR COLABORADOR",
            use_container_width=True
        )

        if adicionar:

            if not nome.strip():

                st.error(
                    "Digite o nome do colaborador."
                )

            else:

                try:

                    conn = conectar()

                    conn.execute(
                        """
                        INSERT INTO colaboradores (nome)
                        VALUES (?)
                        """,
                        (nome.strip(),)
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        f"✅ {nome.strip()} cadastrado!"
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
        # EXCLUIR POR DATA
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '🗑️ Excluir registros por data'
            '</div>',
            unsafe_allow_html=True
        )

        data_exclusao = st.date_input(
            "📅 Selecione a data",
            value=date.today(),
            key="data_exclusao"
        )

        registros_data = df[
            df["data"].dt.date == data_exclusao
        ]

        quantidade = len(
            registros_data
        )

        st.metric(
            "Registros encontrados",
            quantidade
        )

        if quantidade > 0:

            confirmar_data = st.checkbox(
                "⚠️ Confirmo que desejo excluir "
                "TODOS os registros desta data."
            )

            if confirmar_data:

                if st.button(
                    "🗑️ EXCLUIR TODOS OS REGISTROS DA DATA",
                    type="primary",
                    use_container_width=True
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

                    excluidos = cursor.rowcount

                    conn.commit()
                    conn.close()

                    st.success(
                        f"✅ {excluidos} registro(s) excluído(s)."
                    )

                    st.rerun()

        else:

            st.info(
                "Nenhum registro encontrado nessa data."
            )

        st.divider()

        # =================================================
        # EXCLUIR INDIVIDUAL
        # =================================================

        st.subheader(
            "🗑️ Excluir lançamento individual"
        )

        ids = df["id"].tolist()

        id_selecionado = st.selectbox(
            "Selecione o ID",
            ids
        )

        registro = df[
            df["id"] == id_selecionado
        ].iloc[0]

        st.info(
            f"👤 {registro['colaborador']} | "
            f"📅 {registro['data'].strftime('%d/%m/%Y')} | "
            f"📊 Total: {registro['produtividade_total']}"
        )

        confirmar = st.checkbox(
            "Confirmo que desejo excluir este lançamento."
        )

        if confirmar:

            if st.button(
                "🗑️ EXCLUIR LANÇAMENTO",
                type="primary",
                use_container_width=True
            ):

                conn = conectar()

                conn.execute(
                    """
                    DELETE FROM produtividade
                    WHERE id = ?
                    """,
                    (int(id_selecionado),)
                )

                conn.commit()
                conn.close()

                st.success(
                    "✅ Lançamento excluído!"
                )

                st.rerun()

        st.divider()

        # =================================================
        # HISTÓRICO COMPLETO
        # =================================================

        st.subheader(
            "📋 Histórico completo"
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
            + "%"
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

        st.subheader(
            "📊 Exportação para Excel"
        )

        # Filtro de colaborador
        colaboradores = sorted(
            df["colaborador"]
            .unique()
            .tolist()
        )

        colaborador_exportar = st.selectbox(
            "👤 Colaborador",
            ["Todos"] + colaboradores
        )

        if colaborador_exportar != "Todos":

            dados_exportar = df[
                df["colaborador"]
                == colaborador_exportar
            ].copy()

        else:

            dados_exportar = df.copy()

        exportar = dados_exportar.copy()

        exportar["data"] = (
            exportar["data"]
            .dt.strftime("%d/%m/%Y")
        )

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

        arquivo = (
            "PRODUCT_produtividade.xlsx"
        )

        exportar.to_excel(
            arquivo,
            index=False
        )

        st.success(
            f"✅ {len(exportar)} registro(s) "
            "pronto(s) para exportação."
        )

        with open(
            arquivo,
            "rb"
        ) as f:

            st.download_button(
                label="📥 BAIXAR EXCEL",
                data=f,
                file_name=arquivo,
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

    st.markdown(
        """
        <div class="info-box">
            🔐 Utilize esta área para alterar a senha
            de acesso ao sistema PRODUCT.
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form(
        "form_alterar_senha"
    ):

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
                    "❌ A senha deve possuir pelo menos "
                    "4 caracteres."
                )

            else:

                alterar_senha(
                    nova_senha
                )

                st.success(
                    "✅ Senha alterada com sucesso!"
                )

                st.info(
                    "A nova senha será utilizada no próximo acesso."
                )


