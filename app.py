import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date
import hashlib
import io

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
# CSS - VISUAL MODERNO
# =========================================================

def aplicar_estilo(modo_escuro=False):

    if modo_escuro:

        fundo = "#0E1117"
        card = "#161B22"
        texto = "#FFFFFF"
        texto_sec = "#A8B3C2"
        borda = "#30363D"
        sidebar = "#0B0F14"

    else:

        fundo = "#F4F7FB"
        card = "#FFFFFF"
        texto = "#172033"
        texto_sec = "#667085"
        borda = "#E4E7EC"
        sidebar = "#FFFFFF"

    st.markdown(
        f"""
        <style>

        .stApp {{
            background-color: {fundo};
            color: {texto};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {sidebar};
            border-right: 1px solid {borda};
        }}

        section[data-testid="stSidebar"] * {{
            color: {texto} !important;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: {texto} !important;
        }}

        p, label {{
            color: {texto} !important;
        }}

        .metric-card {{
            background: {card};
            border: 1px solid {borda};
            border-radius: 16px;
            padding: 20px;
            min-height: 130px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        }}

        .metric-title {{
            font-size: 14px;
            color: {texto_sec};
            margin-bottom: 8px;
        }}

        .metric-value {{
            font-size: 30px;
            font-weight: 700;
            color: {texto};
        }}

        .metric-icon {{
            font-size: 24px;
            margin-bottom: 8px;
        }}

        .dashboard-header {{
            background: linear-gradient(
                135deg,
                #2563EB,
                #4F46E5
            );
            padding: 28px;
            border-radius: 20px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 8px 25px rgba(37,99,235,0.25);
        }}

        .dashboard-header h1 {{
            color: white !important;
            margin-bottom: 5px;
        }}

        .dashboard-header p {{
            color: #E0E7FF !important;
        }}

        .section-card {{
            background: {card};
            border: 1px solid {borda};
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
        }}

        div[data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
        }}

        .login-box {{
            max-width: 450px;
            margin: 80px auto;
            background: {card};
            border: 1px solid {borda};
            border-radius: 20px;
            padding: 35px;
            box-shadow: 0 10px 35px rgba(0,0,0,0.10);
        }}

        .logo {{
            text-align: center;
            font-size: 48px;
            margin-bottom: 5px;
        }}

        .logo-title {{
            text-align: center;
            font-size: 32px;
            font-weight: 800;
            color: {texto};
        }}

        .logo-subtitle {{
            text-align: center;
            color: {texto_sec};
            margin-bottom: 25px;
        }}

        .stButton > button {{
            border-radius: 10px;
            font-weight: 600;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# BANCO DE DADOS
# =========================================================

def conectar():
    return sqlite3.connect(DB)


def hash_senha(senha):
    return hashlib.sha256(
        senha.encode("utf-8")
    ).hexdigest()


def criar_banco():

    conn = conectar()
    cursor = conn.cursor()

    # Colaboradores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    # Produtividade
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

    # Configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            senha TEXT NOT NULL
        )
    """)

    # Senha inicial
    cursor.execute("""
        SELECT senha
        FROM configuracoes
        WHERE id = 1
    """)

    resultado = cursor.fetchone()

    if resultado is None:

        cursor.execute(
            """
            INSERT INTO configuracoes (id, senha)
            VALUES (1, ?)
            """,
            (hash_senha("2010"),)
        )

    conn.commit()
    conn.close()


criar_banco()


# =========================================================
# FUNÇÕES DE SENHA
# =========================================================

def verificar_senha(senha):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT senha
        FROM configuracoes
        WHERE id = 1
        """
    )

    resultado = cursor.fetchone()

    conn.close()

    if resultado is None:
        return False

    return hash_senha(senha) == resultado[0]


def alterar_senha(nova_senha):

    conn = conectar()

    conn.execute(
        """
        UPDATE configuracoes
        SET senha = ?
        WHERE id = 1
        """,
        (hash_senha(nova_senha),)
    )

    conn.commit()
    conn.close()


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


def excluir_registros_data(data_excluir):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM produtividade
        WHERE data = ?
        """,
        (str(data_excluir),)
    )

    quantidade = cursor.rowcount

    conn.commit()
    conn.close()

    return quantidade


def excluir_registro_id(registro_id):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM produtividade
        WHERE id = ?
        """,
        (int(registro_id),)
    )

    quantidade = cursor.rowcount

    conn.commit()
    conn.close()

    return quantidade


# =========================================================
# SESSÃO
# =========================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "modo_escuro" not in st.session_state:
    st.session_state.modo_escuro = False


# =========================================================
# ESTILO
# =========================================================

aplicar_estilo(
    st.session_state.modo_escuro
)


# =========================================================
# TELA DE LOGIN
# =========================================================

if not st.session_state.autenticado:

    st.markdown(
        '<div class="login-box">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="logo">📊</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="logo-title">PRODUCT</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="logo-subtitle">'
        'Sistema de Controle de Produtividade'
        '</div>',
        unsafe_allow_html=True
    )

    senha = st.text_input(
        "🔐 Senha de acesso",
        type="password",
        placeholder="Digite sua senha"
    )

    entrar = st.button(
        "🔓 ENTRAR",
        use_container_width=True
    )

    if entrar:

        if verificar_senha(senha):

            st.session_state.autenticado = True

            st.rerun()

        else:

            st.error(
                "❌ Senha incorreta."
            )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    st.stop()


# =========================================================
# MENU LATERAL
# =========================================================

st.sidebar.markdown(
    """
    <div style="
        text-align:center;
        padding:10px 0 20px 0;
    ">
        <div style="font-size:42px;">📊</div>
        <div style="
            font-size:26px;
            font-weight:800;
        ">
            PRODUCT
        </div>
        <div style="
            font-size:12px;
            color:#667085;
        ">
            Controle de Produtividade
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.divider()

pagina = st.sidebar.radio(
    "MENU PRINCIPAL",
    [
        "📈 Dashboard",
        "📝 Lançar produtividade",
        "👥 Colaboradores",
        "📋 Histórico",
        "🗑️ Gerenciar registros",
        "⚙️ Configurações",
        "📥 Exportar"
    ]
)

st.sidebar.divider()

modo = st.sidebar.toggle(
    "🌙 Modo noturno",
    value=st.session_state.modo_escuro
)

if modo != st.session_state.modo_escuro:

    st.session_state.modo_escuro = modo

    st.rerun()


if st.sidebar.button(
    "🚪 Sair",
    use_container_width=True
):

    st.session_state.autenticado = False

    st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

if pagina == "📈 Dashboard":

    df = buscar_produtividade()

    st.markdown(
        """
        <div class="dashboard-header">
            <h1>📊 Dashboard de Produtividade</h1>
            <p>
                Acompanhe o desempenho da equipe
                de forma rápida e visual.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if df.empty:

        st.info(
            "Ainda não existem registros de produtividade."
        )

    else:

        # =================================================
        # FILTROS
        # =================================================

        st.subheader("🔎 Filtros")

        f1, f2, f3 = st.columns(3)

        data_min = df["data"].min().date()
        data_max = df["data"].max().date()

        with f1:

            periodo = st.date_input(
                "📅 Período",
                value=(data_min, data_max),
                min_value=data_min,
                max_value=data_max
            )

        with f2:

            colaboradores = sorted(
                df["colaborador"].unique().tolist()
            )

            colaborador_filtro = st.selectbox(
                "👤 Colaborador",
                ["Todos os colaboradores"] + colaboradores
            )

        with f3:

            tipos = st.multiselect(
                "📊 Indicadores",
                [
                    "SYSVET Erro",
                    "SYSVET Êxito",
                    "Faturado"
                ],
                default=[
                    "SYSVET Erro",
                    "SYSVET Êxito",
                    "Faturado"
                ]
            )

        # =================================================
        # FILTRO DE DATA
        # =================================================

        if (
            isinstance(periodo, tuple)
            and len(periodo) == 2
        ):

            inicio, fim = periodo

            df_filtrado = df[
                (df["data"].dt.date >= inicio) &
                (df["data"].dt.date <= fim)
            ].copy()

        else:

            df_filtrado = df.copy()

        # =================================================
        # FILTRO COLABORADOR
        # =================================================

        if colaborador_filtro != "Todos os colaboradores":

            df_filtrado = df_filtrado[
                df_filtrado["colaborador"]
                == colaborador_filtro
            ]

        # =================================================
        # INDICADORES
        # =================================================

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

        produtividade_total = (
            erro +
            exito +
            faturado
        )

        taxa_exito = (
            exito / total_sysvet * 100
            if total_sysvet > 0
            else 0
        )

        st.divider()

        # =================================================
        # CARDS
        # =================================================

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">❌</div>
                    <div class="metric-title">
                        SYSVET ERRO
                    </div>
                    <div class="metric-value">
                        {erro:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">✅</div>
                    <div class="metric-title">
                        SYSVET ÊXITO
                    </div>
                    <div class="metric-value">
                        {exito:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">📁</div>
                    <div class="metric-title">
                        FATURADO
                    </div>
                    <div class="metric-value">
                        {faturado:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c4:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">📊</div>
                    <div class="metric-title">
                        PRODUTIVIDADE
                    </div>
                    <div class="metric-value">
                        {produtividade_total:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c5:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">🎯</div>
                    <div class="metric-title">
                        TAXA DE ÊXITO
                    </div>
                    <div class="metric-value">
                        {taxa_exito:.1f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # =================================================
        # AVISO DO FILTRO
        # =================================================

        if colaborador_filtro != "Todos os colaboradores":

            st.info(
                f"👤 Visualizando exclusivamente a produtividade de: "
                f"**{colaborador_filtro}**"
            )

        # =================================================
        # RANKING
        # =================================================

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

        col1, col2 = st.columns(2)

        # =================================================
        # GRÁFICO RANKING
        # =================================================

        with col1:

            st.subheader("🏆 Ranking")

            if not resumo.empty:

                fig = px.bar(
                    resumo,
                    x="colaborador",
                    y="Total",
                    color="Total",
                    text="Total",
                    color_continuous_scale=[
                        "#60A5FA",
                        "#2563EB",
                        "#1D4ED8"
                    ]
                )

                fig.update_traces(
                    textposition="outside"
                )

                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Produtividade",
                    template=(
                        "plotly_dark"
                        if st.session_state.modo_escuro
                        else "plotly_white"
                    ),
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        # =================================================
        # COMPOSIÇÃO
        # =================================================

        with col2:

            st.subheader("📊 Por tipo")

            if not resumo.empty and tipos:

                mapa = {
                    "SYSVET Erro": "SYSVET_Erro",
                    "SYSVET Êxito": "SYSVET_Exito",
                    "Faturado": "Faturado"
                }

                colunas = [
                    mapa[x]
                    for x in tipos
                ]

                composicao = resumo.melt(
                    id_vars="colaborador",
                    value_vars=colunas,
                    var_name="Tipo",
                    value_name="Quantidade"
                )

                fig = px.bar(
                    composicao,
                    x="colaborador",
                    y="Quantidade",
                    color="Tipo",
                    barmode="group",
                    text="Quantidade"
                )

                fig.update_traces(
                    textposition="outside"
                )

                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Quantidade",
                    template=(
                        "plotly_dark"
                        if st.session_state.modo_escuro
                        else "plotly_white"
                    ),
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        # =================================================
        # EVOLUÇÃO
        # =================================================

        st.subheader(
            "📈 Evolução da produtividade"
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

        if not diario.empty:

            fig = px.line(
                diario,
                x="data",
                y=[
                    "SYSVET_Erro",
                    "SYSVET_Exito",
                    "Faturado",
                    "Total"
                ],
                markers=True
            )

            fig.update_layout(
                xaxis_title="Data",
                yaxis_title="Quantidade",
                template=(
                    "plotly_dark"
                    if st.session_state.modo_escuro
                    else "plotly_white"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =================================================
        # RANKING DETALHADO
        # =================================================

        st.subheader(
            "🏆 Ranking detalhado"
        )

        if not resumo.empty:

            ranking = resumo.copy()

            ranking.insert(
                0,
                "Posição",
                range(1, len(ranking) + 1)
            )

            ranking["Taxa de Êxito"] = ranking.apply(
                lambda x:
                (
                    x["SYSVET_Exito"] /
                    (
                        x["SYSVET_Erro"] +
                        x["SYSVET_Exito"]
                    ) * 100
                )
                if (
                    x["SYSVET_Erro"] +
                    x["SYSVET_Exito"]
                ) > 0
                else 0,
                axis=1
            )

            ranking["Taxa de Êxito"] = (
                ranking["Taxa de Êxito"]
                .round(1)
                .astype(str)
                + "%"
            )

            ranking.columns = [
                "Posição",
                "Colaborador",
                "SYSVET Erro",
                "SYSVET Êxito",
                "Faturado",
                "Total",
                "Taxa de Êxito"
            ]

            st.dataframe(
                ranking,
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
            "Cadastre os colaboradores primeiro."
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

    st.title("👥 Cadastro de colaboradores")

    with st.form("form_colaborador"):

        nome = st.text_input(
            "Nome do colaborador",
            placeholder="Digite o nome"
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
                        f"✅ {nome} cadastrado com sucesso!"
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "⚠️ Esse colaborador já está cadastrado."
                    )

    st.divider()

    st.subheader(
        "👥 Colaboradores cadastrados"
    )

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
# GERENCIAR REGISTROS
# =========================================================

elif pagina == "🗑️ Gerenciar registros":

    st.title("🗑️ Gerenciar registros")

    st.warning(
        "⚠️ Atenção: registros excluídos não poderão "
        "ser recuperados pelo aplicativo."
    )

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Não existem registros para excluir."
        )

    else:

        # =================================================
        # EXCLUIR POR DATA
        # =================================================

        st.subheader(
            "📅 Excluir todos os registros de um dia"
        )

        datas_disponiveis = sorted(
            df["data"].dt.date.unique(),
            reverse=True
        )

        data_excluir = st.selectbox(
            "Selecione a data",
            datas_disponiveis,
            format_func=lambda x:
            x.strftime("%d/%m/%Y")
        )

        quantidade_data = len(
            df[
                df["data"].dt.date == data_excluir
            ]
        )

        st.info(
            f"Existem **{quantidade_data} lançamento(s)** "
            f"para o dia "
            f"**{data_excluir.strftime('%d/%m/%Y')}**."
        )

        confirmar_data = st.checkbox(
            "Confirmo que quero excluir TODOS os registros desta data."
        )

        if st.button(
            "🗑️ EXCLUIR TODOS OS REGISTROS DO DIA",
            type="secondary",
            use_container_width=True
        ):

            if not confirmar_data:

                st.error(
                    "Marque a confirmação antes de excluir."
                )

            else:

                quantidade = excluir_registros_data(
                    data_excluir
                )

                st.success(
                    f"✅ {quantidade} registro(s) "
                    f"excluído(s) com sucesso."
                )

                st.rerun()

        st.divider()

        # =================================================
        # EXCLUIR REGISTRO INDIVIDUAL
        # =================================================

        st.subheader(
            "🗑️ Excluir lançamento individual"
        )

        registros = df.copy()

        registros["descricao"] = (
            "ID "
            + registros["id"].astype(str)
            + " | "
            + registros["data"]
            .dt.strftime("%d/%m/%Y")
            + " | "
            + registros["colaborador"]
            + " | Total: "
            + registros["produtividade_total"]
            .astype(str)
        )

        registro_selecionado = st.selectbox(
            "Selecione o lançamento",
            registros["id"].tolist(),
            format_func=lambda x:
            registros.loc[
                registros["id"] == x,
                "descricao"
            ].iloc[0]
        )

        confirmar_individual = st.checkbox(
            "Confirmo que quero excluir este lançamento."
        )

        if st.button(
            "🗑️ EXCLUIR LANÇAMENTO SELECIONADO",
            type="secondary",
            use_container_width=True
        ):

            if not confirmar_individual:

                st.error(
                    "Marque a confirmação antes de excluir."
                )

            else:

                quantidade = excluir_registro_id(
                    registro_selecionado
                )

                if quantidade > 0:

                    st.success(
                        "✅ Lançamento excluído com sucesso."
                    )

                else:

                    st.error(
                        "❌ Não foi possível encontrar o lançamento."
                    )

                st.rerun()


# =========================================================
# CONFIGURAÇÕES
# =========================================================

elif pagina == "⚙️ Configurações":

    st.title("⚙️ Configurações")

    st.subheader(
        "🔐 Alterar senha de acesso"
    )

    st.info(
        "A senha atual não será exibida."
    )

    with st.form("form_alterar_senha"):

        senha_atual = st.text_input(
            "🔐 Senha atual",
            type="password"
        )

        nova_senha = st.text_input(
            "🔑 Nova senha",
            type="password"
        )

        confirmar_senha = st.text_input(
            "🔑 Confirmar nova senha",
            type="password"
        )

        alterar = st.form_submit_button(
            "🔒 ALTERAR SENHA",
            use_container_width=True
        )

        if alterar:

            if not senha_atual:

                st.error(
                    "Informe a senha atual."
                )

            elif not verificar_senha(senha_atual):

                st.error(
                    "❌ A senha atual está incorreta."
                )

            elif not nova_senha:

                st.error(
                    "Informe uma nova senha."
                )

            elif len(nova_senha) < 4:

                st.error(
                    "A nova senha deve ter pelo menos 4 caracteres."
                )

            elif nova_senha != confirmar_senha:

                st.error(
                    "As novas senhas não são iguais."
                )

            else:

                alterar_senha(
                    nova_senha
                )

                st.success(
                    "✅ Senha alterada com sucesso!"
                )


# =========================================================
# EXPORTAR
# =========================================================

elif pagina == "📥 Exportar":

    st.title("📥 Exportar dados")

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Nenhum dado disponível para exportação."
        )

    else:

        exportar = df.copy()

        exportar["data"] = (
            exportar["data"]
            .dt.strftime("%d/%m/%Y")
        )

        exportar["taxa_exito"] = (
            exportar["taxa_exito"]
            .round(1)
            .astype(str)
            + "%"
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

        buffer = io.BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:

            exportar.to_excel(
                writer,
                index=False,
                sheet_name="Produtividade"
            )

        buffer.seek(0)

        st.success(
            "✅ Arquivo pronto para download."
        )

        st.download_button(
            label="📥 BAIXAR EXCEL",
            data=buffer,
            file_name="PRODUCT_produtividade.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )
