import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# CSS
# =========================================================

st.markdown("""
<style>

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

.stApp {
    background: #f4f7fb;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}


/* =====================================================
   SIDEBAR
   ===================================================== */

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #0f172a 0%,
        #172554 55%,
        #1e3a8a 100%
    );
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

.sidebar-logo {
    text-align: center;
    padding: 15px 5px 25px 5px;
}

.sidebar-icon {
    font-size: 42px;
}

.sidebar-title {
    font-size: 30px;
    font-weight: 900;
    color: white;
}

.sidebar-subtitle {
    font-size: 12px;
    color: #bfdbfe;
}


/* =====================================================
   LOGIN
   ===================================================== */

.login-container {
    max-width: 430px;
    margin: 90px auto 0 auto;
    background: white;
    padding: 42px;
    border-radius: 24px;
    box-shadow: 0 20px 60px rgba(15,23,42,0.15);
    border: 1px solid #e5e7eb;
}

.login-logo {
    width: 95px;
    height: 95px;
    margin: auto;
    border-radius: 24px;
    background: linear-gradient(
        135deg,
        #2563eb,
        #4f46e5
    );
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 48px;
    box-shadow: 0 10px 25px rgba(37,99,235,0.3);
}

.login-title {
    text-align: center;
    font-size: 34px;
    font-weight: 900;
    color: #1d4ed8;
    margin-top: 18px;
}

.login-subtitle {
    text-align: center;
    color: #64748b;
    font-size: 14px;
    margin-bottom: 28px;
}

.login-footer {
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
    margin-top: 20px;
}


/* =====================================================
   DASHBOARD HEADER
   ===================================================== */

.dashboard-header {
    background: linear-gradient(
        135deg,
        #1d4ed8,
        #4338ca
    );
    padding: 27px 30px;
    border-radius: 20px;
    color: white;
    margin-bottom: 22px;
    box-shadow: 0 10px 30px rgba(37,99,235,0.18);
}

.dashboard-title {
    font-size: 31px;
    font-weight: 900;
}

.dashboard-subtitle {
    font-size: 14px;
    opacity: .9;
    margin-top: 5px;
}


/* =====================================================
   KPI
   ===================================================== */

.kpi-card {
    background: white;
    border-radius: 17px;
    padding: 20px;
    min-height: 130px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 5px 20px rgba(15,23,42,.06);
    position: relative;
    overflow: hidden;
}

.kpi-card:after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 5px;
    background: #2563eb;
}

.kpi-icon {
    font-size: 25px;
}

.kpi-label {
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    margin-top: 8px;
}

.kpi-value {
    color: #0f172a;
    font-size: 28px;
    font-weight: 900;
    margin-top: 4px;
}


/* =====================================================
   SEÇÕES
   ===================================================== */

.section-title {
    font-size: 20px;
    font-weight: 850;
    color: #0f172a;
    margin-top: 25px;
    margin-bottom: 12px;
}


/* =====================================================
   INFO
   ===================================================== */

.info-box {
    background: #eff6ff;
    border-left: 5px solid #2563eb;
    padding: 14px 18px;
    border-radius: 10px;
    color: #1e3a8a;
    margin-bottom: 18px;
}


/* =====================================================
   RANKING
   ===================================================== */

.ranking-card {
    background: white;
    border-radius: 14px;
    padding: 15px 18px;
    margin-bottom: 9px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 3px 12px rgba(15,23,42,.05);
}

.ranking-position {
    font-size: 21px;
    font-weight: 900;
}

.ranking-name {
    font-weight: 750;
    color: #1e293b;
}

.ranking-total {
    float: right;
    color: #2563eb;
    font-weight: 900;
}


/* =====================================================
   BOTÕES
   ===================================================== */

.stButton > button {
    border-radius: 10px;
    font-weight: 700;
    min-height: 42px;
}

.stDownloadButton > button {
    border-radius: 10px;
    font-weight: 700;
}


/* =====================================================
   TABELAS
   ===================================================== */

div[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}


/* =====================================================
   INPUTS
   ===================================================== */

div[data-baseweb="select"] > div {
    border-radius: 10px;
}

input {
    border-radius: 10px !important;
}

</style>
""", unsafe_allow_html=True)


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

def mostrar_login():

    st.markdown(
        '<div class="login-container">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-logo">📊</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-title">PRODUCT</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subtitle">'
        'Sistema de Controle de Produtividade'
        '</div>',
        unsafe_allow_html=True
    )

    senha = st.text_input(
        "🔐 Senha de acesso",
        type="password",
        label_visibility="visible"
    )

    entrar = st.button(
        "🔓 ENTRAR",
        use_container_width=True,
        type="primary"
    )

    if entrar:

        if senha == buscar_senha():

            st.session_state["autenticado"] = True

            st.rerun()

        else:

            st.error(
                "Senha incorreta."
            )

    st.markdown(
        '<div class="login-footer">'
        'PRODUCT • Controle de Produtividade'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


if "autenticado" not in st.session_state:

    st.session_state["autenticado"] = False


if not st.session_state["autenticado"]:

    mostrar_login()

    st.stop()


# =========================================================
# FUNÇÕES
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
            lambda linha:
            (
                linha["sysvet_exito"]
                /
                linha["total_sysvet"]
                *
                100
            )
            if linha["total_sysvet"] > 0
            else 0,
            axis=1
        )

    return df


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    """
    <div class="sidebar-logo">

        <div class="sidebar-icon">
            📊
        </div>

        <div class="sidebar-title">
            PRODUCT
        </div>

        <div class="sidebar-subtitle">
            Controle de Produtividade
        </div>

    </div>
    """,
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

    st.markdown(
        """
        <div class="dashboard-header">

            <div class="dashboard-title">
                📊 Dashboard de Produtividade
            </div>

            <div class="dashboard-subtitle">
                Indicadores de desempenho da equipe
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if df.empty:

        st.info(
            "Nenhum lançamento encontrado."
        )

        st.stop()

    # -----------------------------------------------------
    # FILTROS
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '🔎 Filtros'
        '</div>',
        unsafe_allow_html=True
    )

    f1, f2, f3 = st.columns(
        [2, 2, 1]
    )

    lista_colaboradores = sorted(
        df["colaborador"]
        .dropna()
        .unique()
        .tolist()
    )

    with f1:

        colaborador = st.selectbox(
            "👤 Colaborador",
            ["👥 Todos os colaboradores"]
            + lista_colaboradores
        )

    data_min = df["data"].min().date()

    data_max = df["data"].max().date()

    with f2:

        periodo = st.date_input(
            "📅 Período",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max
        )

    with f3:

        st.write("")

        st.write("")

        if st.button(
            "🔄 Atualizar",
            use_container_width=True
        ):

            st.rerun()

    # -----------------------------------------------------
    # FILTRO DATA
    # -----------------------------------------------------

    if (
        isinstance(periodo, tuple)
        and len(periodo) == 2
    ):

        inicio, fim = periodo

        df_filtrado = df[
            (
                df["data"].dt.date
                >= inicio
            )
            &
            (
                df["data"].dt.date
                <= fim
            )
        ].copy()

    else:

        df_filtrado = df.copy()

    # -----------------------------------------------------
    # FILTRO COLABORADOR
    # -----------------------------------------------------

    if colaborador != "👥 Todos os colaboradores":

        df_filtrado = df_filtrado[
            df_filtrado["colaborador"]
            == colaborador
        ].copy()

    if df_filtrado.empty:

        st.warning(
            "Nenhum registro encontrado para os filtros selecionados."
        )

        st.stop()

    # -----------------------------------------------------
    # INDICADORES
    # -----------------------------------------------------

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

    total = erro + exito + faturado

    taxa = (
        exito / total_sysvet * 100
        if total_sysvet > 0
        else 0
    )

    # -----------------------------------------------------
    # CARDS
    # -----------------------------------------------------

    k1, k2, k3, k4, k5 = st.columns(5)

    cards = [
        ("❌", "SYSVET ERRO", erro),
        ("✅", "SYSVET ÊXITO", exito),
        ("📁", "FATURADO", faturado),
        ("📊", "PRODUTIVIDADE", total),
        ("🎯", "TAXA DE ÊXITO", f"{taxa:.1f}%")
    ]

    colunas = [k1, k2, k3, k4, k5]

    for coluna, card in zip(colunas, cards):

        icone, titulo, valor = card

        with coluna:

            st.markdown(
                f"""
                <div class="kpi-card">

                    <div class="kpi-icon">
                        {icone}
                    </div>

                    <div class="kpi-label">
                        {titulo}
                    </div>

                    <div class="kpi-value">
                        {valor:,}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # IDENTIFICAÇÃO DA VISÃO
    # -----------------------------------------------------

    if colaborador == "👥 Todos os colaboradores":

        texto_visao = (
            "👥 Visualizando a produtividade de toda a equipe."
        )

    else:

        texto_visao = (
            f"👤 Visualizando exclusivamente a produtividade de "
            f"<b>{colaborador}</b>."
        )

    st.markdown(
        f"""
        <div class="info-box">
            {texto_visao}
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # RESUMO
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # RANKING + GRÁFICO
    # -----------------------------------------------------

    esquerda, direita = st.columns(
        [1, 1.6]
    )

    with esquerda:

        st.markdown(
            '<div class="section-title">'
            '🏆 Ranking'
            '</div>',
            unsafe_allow_html=True
        )

        for pos, (_, linha) in enumerate(
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
                        {linha['colaborador']}
                    </span>

                    <span class="ranking-total">
                        {int(linha['Total']):,}
                    </span>

                </div>
                """,
                unsafe_allow_html=True
            )

    with direita:

        st.markdown(
            '<div class="section-title">'
            '📊 Produtividade por colaborador'
            '</div>',
            unsafe_allow_html=True
        )

        grafico = px.bar(
            resumo,
            x="colaborador",
            y="Total",
            color="Total",
            text="Total",
            color_continuous_scale=[
                "#bfdbfe",
                "#2563eb",
                "#1e3a8a"
            ]
        )

        grafico.update_traces(
            textposition="outside"
        )

        grafico.update_layout(
            height=360,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20
            ),
            xaxis_title="",
            yaxis_title="Produtividade",
            coloraxis_showscale=False
        )

        st.plotly_chart(
            grafico,
            use_container_width=True
        )

    # -----------------------------------------------------
    # COMPOSIÇÃO
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '📊 Composição da produtividade'
        '</div>',
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

    grafico_pizza = px.pie(
        composicao,
        names="Tipo",
        values="Quantidade",
        hole=0.58,
        color="Tipo",
        color_discrete_map={
            "SYSVET Erro": "#ef4444",
            "SYSVET Êxito": "#22c55e",
            "Faturado": "#2563eb"
        }
    )

    grafico_pizza.update_layout(
        height=380,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20
        )
    )

    st.plotly_chart(
        grafico_pizza,
        use_container_width=True
    )

    # -----------------------------------------------------
    # EVOLUÇÃO
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '📈 Evolução da produtividade'
        '</div>',
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

    grafico_linha = go.Figure()

    grafico_linha.add_trace(
        go.Scatter(
            x=diario["data"],
            y=diario["Total"],
            name="Produtividade",
            mode="lines+markers",
            line=dict(
                color="#2563eb",
                width=4
            ),
            marker=dict(
                size=8
            )
        )
    )

    grafico_linha.add_trace(
        go.Scatter(
            x=diario["data"],
            y=diario["Faturado"],
            name="Faturado",
            mode="lines+markers",
            line=dict(
                color="#22c55e",
                width=3
            )
        )
    )

    grafico_linha.update_layout(
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
        xaxis_title="Data",
        yaxis_title="Quantidade"
    )

    st.plotly_chart(
        grafico_linha,
        use_container_width=True
    )

    # -----------------------------------------------------
    # TABELA DO COLABORADOR
    # -----------------------------------------------------

    if colaborador != "👥 Todos os colaboradores":

        st.markdown(
            '<div class="section-title">'
            '👤 Detalhamento individual'
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
            "Cadastre primeiro os colaboradores."
        )

    else:

        with st.form(
            "form_lancamento"
        ):

            data_lancamento = st.date_input(
                "📅 Data",
                value=date.today()
            )

            colaborador = st.selectbox(
                "👤 Colaborador",
                colaboradores["nome"].tolist()
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                erro = st.number_input(
                    "❌ SYSVET com erro",
                    min_value=0,
                    value=0,
                    step=1
                )

            with c2:

                exito = st.number_input(
                    "✅ SYSVET com êxito",
                    min_value=0,
                    value=0,
                    step=1
                )

            with c3:

                faturado = st.number_input(
                    "📁 Faturado",
                    min_value=0,
                    value=0,
                    step=1
                )

            total = erro + exito + faturado

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
                    "Produtividade registrada com sucesso!"
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
                        INSERT INTO colaboradores
                        (nome)
                        VALUES (?)
                        """,
                        (nome.strip(),)
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        "Colaborador cadastrado!"
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "Esse colaborador já está cadastrado."
                    )

    st.divider()

    colaboradores = buscar_colaboradores()

    if not colaboradores.empty:

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

    st.title("📋 Histórico")

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Nenhum lançamento encontrado."
        )

    else:

        st.markdown(
            '<div class="section-title">'
            '🗑️ Excluir registros por data'
            '</div>',
            unsafe_allow_html=True
        )

        data_exclusao = st.date_input(
            "📅 Selecione a data",
            value=date.today(),
            key="excluir_data"
        )

        registros = df[
            df["data"].dt.date
            == data_exclusao
        ]

        quantidade = len(registros)

        st.metric(
            "Registros encontrados",
            quantidade
        )

        if quantidade > 0:

            confirmar = st.checkbox(
                "Confirmo que desejo excluir todos os registros desta data."
            )

            if confirmar:

                if st.button(
                    "🗑️ EXCLUIR TODOS DA DATA",
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
                        f"{excluidos} registro(s) excluído(s)."
                    )

                    st.rerun()

        else:

            st.info(
                "Nenhum registro encontrado nessa data."
            )

        st.divider()

        st.markdown(
            '<div class="section-title">'
            '🗑️ Excluir lançamento individual'
            '</div>',
            unsafe_allow_html=True
        )

        id_selecionado = st.selectbox(
            "Selecione o ID do lançamento",
            df["id"].tolist()
        )

        registro = df[
            df["id"] == id_selecionado
        ].iloc[0]

        st.info(
            f"👤 {registro['colaborador']}   |   "
            f"📅 {registro['data'].strftime('%d/%m/%Y')}   |   "
            f"📊 Total: {int(registro['produtividade_total'])}"
        )

        confirmar_individual = st.checkbox(
            "Confirmo a exclusão deste lançamento."
        )

        if confirmar_individual:

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
                    "Lançamento excluído."
                )

                st.rerun()

        st.divider()

        st.markdown(
            '<div class="section-title">'
            '📋 Todos os lançamentos'
            '</div>',
            unsafe_allow_html=True
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

    st.title("📥 Exportar")

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
            "👤 Colaborador",
            ["Todos"] + colaboradores
        )

        if colaborador_exportar != "Todos":

            dados = df[
                df["colaborador"]
                == colaborador_exportar
            ].copy()

        else:

            dados = df.copy()

        exportar = dados.copy()

        exportar["data"] = (
            exportar["data"]
            .dt.strftime("%d/%m/%Y")
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

        exportar["taxa_exito"] = (
            exportar["taxa_exito"]
            .round(1)
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

        # Criar Excel na memória
        arquivo_excel = BytesIO()

        with pd.ExcelWriter(
            arquivo_excel,
            engine="openpyxl"
        ) as writer:

            exportar.to_excel(
                writer,
                index=False,
                sheet_name="Produtividade"
            )

        arquivo_excel.seek(0)

        st.success(
            f"{len(exportar)} registro(s) preparado(s) para exportação."
        )

        st.download_button(
            "📥 BAIXAR EXCEL",
            data=arquivo_excel,
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

    st.markdown(
        """
        <div class="info-box">
            🔐 Aqui você pode alterar a senha utilizada
            para acessar o sistema.
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form(
        "form_senha"
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
                    "A senha atual está incorreta."
                )

            elif not nova_senha:

                st.error(
                    "Digite uma nova senha."
                )

            elif nova_senha != confirmar_senha:

                st.error(
                    "As senhas não são iguais."
                )

            elif len(nova_senha) < 4:

                st.error(
                    "A senha deve possuir pelo menos 4 caracteres."
                )

            else:

                alterar_senha(
                    nova_senha
                )

                st.success(
                    "Senha alterada com sucesso!"
                )


