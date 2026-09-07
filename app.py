import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date
import io


# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="PRODUCT",
    page_icon="📊",
    layout="wide"
)

DB = "produtividade.db"
SENHA_PADRAO = "2010"


# =========================================================
# ESTILO
# =========================================================

def aplicar_estilo():

    if st.session_state.get("modo_noturno", False):

        fundo = "#0E1117"
        fundo_card = "#161B22"
        texto = "#FFFFFF"
        texto_secundario = "#AAB4C3"
        borda = "#30363D"

    else:

        fundo = "#F4F7FB"
        fundo_card = "#FFFFFF"
        texto = "#172033"
        texto_secundario = "#667085"
        borda = "#E2E8F0"

    st.markdown(
        f"""
        <style>

        .stApp {{
            background-color: {fundo};
            color: {texto};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {fundo_card};
        }}

        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }}

        .titulo-product {{
            font-size: 42px;
            font-weight: 800;
            color: {texto};
            margin-bottom: 0;
        }}

        .subtitulo-product {{
            font-size: 17px;
            color: {texto_secundario};
            margin-top: 0;
            margin-bottom: 25px;
        }}

        .card {{
            background-color: {fundo_card};
            border: 1px solid {borda};
            border-radius: 16px;
            padding: 18px;
            min-height: 125px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.05);
        }}

        .card-titulo {{
            color: {texto_secundario};
            font-size: 14px;
            font-weight: 600;
        }}

        .card-valor {{
            color: {texto};
            font-size: 30px;
            font-weight: 800;
            margin-top: 8px;
        }}

        .card-icone {{
            font-size: 25px;
        }}

        div[data-testid="stMetric"] {{
            background-color: {fundo_card};
            border: 1px solid {borda};
            padding: 15px;
            border-radius: 15px;
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


def criar_banco():

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS produtividade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            colaborador TEXT NOT NULL,
            sysvet_erro INTEGER DEFAULT 0,
            sysvet_exito INTEGER DEFAULT 0,
            faturado INTEGER DEFAULT 0
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY,
            senha TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        SELECT senha
        FROM configuracoes
        WHERE id = 1
        """
    )

    resultado = cursor.fetchone()

    if resultado is None:

        cursor.execute(
            """
            INSERT INTO configuracoes
            (id, senha)
            VALUES (1, ?)
            """,
            (SENHA_PADRAO,)
        )

    conn.commit()

    conn.close()


criar_banco()


# =========================================================
# SENHA
# =========================================================

def obter_senha():

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

    if resultado:

        return str(resultado[0])

    return SENHA_PADRAO


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
# CONSULTAS
# =========================================================

def buscar_colaboradores():

    conn = conectar()

    df = pd.read_sql_query(
        """
        SELECT id, nome
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
        SELECT
            id,
            data,
            colaborador,
            sysvet_erro,
            sysvet_exito,
            faturado
        FROM produtividade
        ORDER BY data DESC, id DESC
        """,
        conn
    )

    conn.close()

    if not df.empty:

        df["data"] = pd.to_datetime(
            df["data"],
            errors="coerce"
        )

        df["total_sysvet"] = (
            df["sysvet_erro"]
            + df["sysvet_exito"]
        )

        df["produtividade_total"] = (
            df["sysvet_erro"]
            + df["sysvet_exito"]
            + df["faturado"]
        )

        df["taxa_exito"] = df.apply(
            lambda linha:
            (
                linha["sysvet_exito"]
                / linha["total_sysvet"]
                * 100
            )
            if linha["total_sysvet"] > 0
            else 0,
            axis=1
        )

    return df


# =========================================================
# EXCLUSÕES
# =========================================================

def excluir_registro(registro_id):

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


def excluir_por_data(data_excluir):

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


# =========================================================
# SESSÃO
# =========================================================

if "logado" not in st.session_state:

    st.session_state.logado = False


if "modo_noturno" not in st.session_state:

    st.session_state.modo_noturno = False


# =========================================================
# LOGIN
# =========================================================

if not st.session_state.logado:

    aplicar_estilo()

    st.markdown(
        '<div class="titulo-product">📊 PRODUCT</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitulo-product">'
        'Sistema de Controle de Produtividade'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.subheader("🔐 Acesso")

        senha = st.text_input(
            "Digite sua senha",
            type="password",
            key="senha_login"
        )

        entrar = st.button(
            "🔓 ENTRAR",
            use_container_width=True,
            type="primary"
        )

        if entrar:

            if senha == obter_senha():

                st.session_state.logado = True

                st.rerun()

            else:

                st.error("❌ Senha incorreta.")

    st.stop()


# =========================================================
# ESTILO APÓS LOGIN
# =========================================================

aplicar_estilo()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    "## 📊 PRODUCT"
)

st.sidebar.caption(
    "Controle de Produtividade"
)

st.sidebar.divider()


pagina = st.sidebar.radio(
    "MENU",
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


modo_noturno = st.sidebar.toggle(
    "🌙 Modo noturno",
    value=st.session_state.modo_noturno
)


if modo_noturno != st.session_state.modo_noturno:

    st.session_state.modo_noturno = modo_noturno

    st.rerun()


if st.sidebar.button(
    "🚪 Sair",
    use_container_width=True
):

    st.session_state.logado = False

    st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

if pagina == "📈 Dashboard":

    st.markdown(
        '<div class="titulo-product">📊 Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitulo-product">'
        'Visão geral da produtividade'
        '</div>',
        unsafe_allow_html=True
    )

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Nenhum lançamento encontrado."
        )

    else:

        st.subheader("🔎 Filtros")

        col1, col2 = st.columns(2)

        data_min = df["data"].min().date()
        data_max = df["data"].max().date()

        with col1:

            periodo = st.date_input(
                "📅 Período",
                value=(data_min, data_max),
                min_value=data_min,
                max_value=data_max
            )

        with col2:

            colaboradores = sorted(
                df["colaborador"]
                .dropna()
                .unique()
                .tolist()
            )

            colaborador = st.selectbox(
                "👤 Colaborador",
                ["Todos os colaboradores"]
                + colaboradores
            )

        if isinstance(periodo, tuple) and len(periodo) == 2:

            inicio = periodo[0]
            fim = periodo[1]

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


        if colaborador != "Todos os colaboradores":

            df_filtrado = df_filtrado[
                df_filtrado["colaborador"]
                == colaborador
            ]


        st.divider()


        # =================================================
        # CARDS
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

        total = (
            erro
            + exito
            + faturado
        )

        total_sysvet = erro + exito

        taxa = (
            exito / total_sysvet * 100
            if total_sysvet > 0
            else 0
        )


        c1, c2, c3, c4, c5 = st.columns(5)


        with c1:

            st.markdown(
                f"""
                <div class="card">
                    <div class="card-icone">❌</div>
                    <div class="card-titulo">
                        SYSVET ERRO
                    </div>
                    <div class="card-valor">
                        {erro:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


        with c2:

            st.markdown(
                f"""
                <div class="card">
                    <div class="card-icone">✅</div>
                    <div class="card-titulo">
                        SYSVET ÊXITO
                    </div>
                    <div class="card-valor">
                        {exito:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


        with c3:

            st.markdown(
                f"""
                <div class="card">
                    <div class="card-icone">📁</div>
                    <div class="card-titulo">
                        FATURADO
                    </div>
                    <div class="card-valor">
                        {faturado:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


        with c4:

            st.markdown(
                f"""
                <div class="card">
                    <div class="card-icone">📊</div>
                    <div class="card-titulo">
                        PRODUTIVIDADE
                    </div>
                    <div class="card-valor">
                        {total:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


        with c5:

            st.markdown(
                f"""
                <div class="card">
                    <div class="card-icone">🎯</div>
                    <div class="card-titulo">
                        TAXA DE ÊXITO
                    </div>
                    <div class="card-valor">
                        {taxa:.1f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


        st.divider()


        # =================================================
        # RANKING
        # =================================================

        st.subheader(
            "🏆 Ranking de produtividade"
        )

        resumo = (
            df_filtrado
            .groupby("colaborador")
            .agg(
                SYSVET_Erro=(
                    "sysvet_erro",
                    "sum"
                ),
                SYSVET_Exito=(
                    "sysvet_exito",
                    "sum"
                ),
                Faturado=(
                    "faturado",
                    "sum"
                ),
                Total=(
                    "produtividade_total",
                    "sum"
                )
            )
            .reset_index()
            .sort_values(
                "Total",
                ascending=False
            )
        )


        if not resumo.empty:

            fig = px.bar(
                resumo,
                x="colaborador",
                y="Total",
                color="Total",
                text="Total",
                color_continuous_scale="Blues"
            )

            fig.update_traces(
                textposition="outside"
            )

            fig.update_layout(
                template=(
                    "plotly_dark"
                    if st.session_state.modo_noturno
                    else "plotly_white"
                ),
                xaxis_title="Colaborador",
                yaxis_title="Produtividade",
                hovermode="x unified"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # =================================================
        # PRODUTIVIDADE POR TIPO
        # =================================================

        st.subheader(
            "📊 Comparativo por tipo"
        )

        if not resumo.empty:

            composicao = resumo.melt(
                id_vars="colaborador",
                value_vars=[
                    "SYSVET_Erro",
                    "SYSVET_Exito",
                    "Faturado"
                ],
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
                template=(
                    "plotly_dark"
                    if st.session_state.modo_noturno
                    else "plotly_white"
                ),
                xaxis_title="Colaborador",
                yaxis_title="Quantidade"
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
                SYSVET_Erro=(
                    "sysvet_erro",
                    "sum"
                ),
                SYSVET_Exito=(
                    "sysvet_exito",
                    "sum"
                ),
                Faturado=(
                    "faturado",
                    "sum"
                ),
                Total=(
                    "produtividade_total",
                    "sum"
                )
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
                template=(
                    "plotly_dark"
                    if st.session_state.modo_noturno
                    else "plotly_white"
                ),
                xaxis_title="Data",
                yaxis_title="Quantidade"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # =================================================
        # TABELA
        # =================================================

        st.subheader(
            "📋 Detalhamento"
        )

        tabela = df_filtrado[
            [
                "data",
                "colaborador",
                "sysvet_erro",
                "sysvet_exito",
                "faturado",
                "produtividade_total",
                "taxa_exito"
            ]
        ].copy()

        tabela["data"] = (
            tabela["data"]
            .dt.strftime("%d/%m/%Y")
        )

        tabela["taxa_exito"] = (
            tabela["taxa_exito"]
            .round(1)
            .astype(str)
            + "%"
        )

        tabela.columns = [
            "Data",
            "Colaborador",
            "SYSVET Erro",
            "SYSVET Êxito",
            "Faturado",
            "Produtividade Total",
            "Taxa de Êxito"
        ]

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# LANÇAR PRODUTIVIDADE
# =========================================================

elif pagina == "📝 Lançar produtividade":

    st.title(
        "📝 Lançar produtividade"
    )

    st.caption(
        "Registre a produtividade de cada colaborador."
    )

    colaboradores = buscar_colaboradores()

    if colaboradores.empty:

        st.warning(
            "⚠️ Nenhum colaborador cadastrado."
        )

        st.info(
            "Acesse Colaboradores para cadastrar."
        )

    else:

        with st.form(
            "form_lancamento",
            clear_on_submit=True
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
                erro
                + exito
                + faturado
            )

            st.info(
                f"📊 Produtividade total: {total}"
            )

            salvar = st.form_submit_button(
                "💾 SALVAR PRODUTIVIDADE",
                use_container_width=True,
                type="primary"
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
                    "✅ Produtividade registrada!"
                )

                st.rerun()


# =========================================================
# COLABORADORES
# =========================================================

elif pagina == "👥 Colaboradores":

    st.title(
        "👥 Colaboradores"
    )

    st.caption(
        "Cadastre os colaboradores que utilizarão o sistema."
    )

    with st.form(
        "form_colaborador"
    ):

        nome = st.text_input(
            "Nome do colaborador"
        )

        cadastrar = st.form_submit_button(
            "➕ CADASTRAR",
            use_container_width=True,
            type="primary"
        )

        if cadastrar:

            nome_limpo = nome.strip()

            if not nome_limpo:

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
                        (nome_limpo,)
                    )

                    conn.commit()

                    conn.close()

                    st.success(
                        f"✅ {nome_limpo} cadastrado!"
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "⚠️ Esse colaborador já está cadastrado."
                    )


    st.divider()

    lista = buscar_colaboradores()

    if lista.empty:

        st.info(
            "Nenhum colaborador cadastrado."
        )

    else:

        st.dataframe(
            lista,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# HISTÓRICO
# =========================================================

elif pagina == "📋 Histórico":

    st.title(
        "📋 Histórico"
    )

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Nenhum lançamento encontrado."
        )

    else:

        col1, col2 = st.columns(2)

        nomes = sorted(
            df["colaborador"]
            .unique()
            .tolist()
        )

        with col1:

            filtro_colaborador = st.selectbox(
                "👤 Colaborador",
                ["Todos"] + nomes
            )

        with col2:

            filtro_data = st.date_input(
                "📅 Data",
                value=None
            )

        tabela = df.copy()

        if filtro_colaborador != "Todos":

            tabela = tabela[
                tabela["colaborador"]
                == filtro_colaborador
            ]

        if filtro_data is not None:

            tabela = tabela[
                tabela["data"].dt.date
                == filtro_data
            ]

        if tabela.empty:

            st.info(
                "Nenhum registro encontrado para os filtros."
            )

        else:

            tabela_exibicao = tabela[
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

            tabela_exibicao["data"] = (
                tabela_exibicao["data"]
                .dt.strftime("%d/%m/%Y")
            )

            tabela_exibicao["taxa_exito"] = (
                tabela_exibicao["taxa_exito"]
                .round(1)
                .astype(str)
                + "%"
            )

            tabela_exibicao.columns = [
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
                tabela_exibicao,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# GERENCIAR REGISTROS
# =========================================================

elif pagina == "🗑️ Gerenciar registros":

    st.title(
        "🗑️ Gerenciar registros"
    )

    st.warning(
        "⚠️ Atenção: as exclusões são permanentes."
    )

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Não existem registros para excluir."
        )

    else:

        # =================================================
        # EXCLUSÃO POR DATA
        # =================================================

        st.subheader(
            "🗓️ Apagar registros de uma data"
        )

        datas = sorted(
            df["data"]
            .dt.date
            .unique(),
            reverse=True
        )

        data_excluir = st.selectbox(
            "Escolha a data",
            datas,
            format_func=lambda x:
            x.strftime("%d/%m/%Y")
        )

        registros_data = df[
            df["data"].dt.date
            == data_excluir
        ]

        st.info(
            f"Existem {len(registros_data)} "
            f"registro(s) nesta data."
        )

        resumo_data = registros_data[
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

        resumo_data["data"] = (
            resumo_data["data"]
            .dt.strftime("%d/%m/%Y")
        )

        resumo_data.columns = [
            "ID",
            "Data",
            "Colaborador",
            "SYSVET Erro",
            "SYSVET Êxito",
            "Faturado",
            "Produtividade Total"
        ]

        st.dataframe(
            resumo_data,
            use_container_width=True,
            hide_index=True
        )

        confirmar_data = st.checkbox(
            "Confirmo que quero apagar todos os registros desta data."
        )

        if st.button(
            "🗑️ APAGAR TODOS OS REGISTROS DO DIA",
            use_container_width=True,
            type="primary"
        ):

            if confirmar_data:

                quantidade = excluir_por_data(
                    data_excluir
                )

                st.success(
                    f"✅ {quantidade} registro(s) apagado(s)."
                )

                st.rerun()

            else:

                st.error(
                    "Marque a confirmação antes de apagar."
                )


        st.divider()


        # =================================================
        # EXCLUSÃO INDIVIDUAL
        # =================================================

        st.subheader(
            "🗑️ Apagar um lançamento específico"
        )

        df["descricao"] = (
            "ID "
            + df["id"].astype(str)
            + " | "
            + df["data"].dt.strftime("%d/%m/%Y")
            + " | "
            + df["colaborador"]
            + " | Total: "
            + df["produtividade_total"].astype(str)
        )

        registro_id = st.selectbox(
            "Escolha o lançamento",
            df["id"].tolist(),
            format_func=lambda x:
            df.loc[
                df["id"] == x,
                "descricao"
            ].iloc[0]
        )

        confirmar_registro = st.checkbox(
            "Confirmo que quero apagar este lançamento."
        )

        if st.button(
            "🗑️ APAGAR LANÇAMENTO",
            use_container_width=True
        ):

            if confirmar_registro:

                quantidade = excluir_registro(
                    registro_id
                )

                if quantidade > 0:

                    st.success(
                        "✅ Lançamento apagado."
                    )

                else:

                    st.error(
                        "Registro não encontrado."
                    )

                st.rerun()

            else:

                st.error(
                    "Marque a confirmação antes de apagar."
                )


# =========================================================
# CONFIGURAÇÕES
# =========================================================

elif pagina == "⚙️ Configurações":

    st.title(
        "⚙️ Configurações"
    )

    st.subheader(
        "🔐 Alterar senha"
    )

    st.info(
        "A senha inicial do sistema é 2010."
    )

    with st.form(
        "form_senha"
    ):

        senha_atual = st.text_input(
            "Senha atual",
            type="password"
        )

        nova_senha = st.text_input(
            "Nova senha",
            type="password"
        )

        confirmar_senha = st.text_input(
            "Confirmar nova senha",
            type="password"
        )

        alterar = st.form_submit_button(
            "🔒 ALTERAR SENHA",
            use_container_width=True,
            type="primary"
        )

        if alterar:

            if senha_atual != obter_senha():

                st.error(
                    "❌ A senha atual está incorreta."
                )

            elif len(nova_senha) < 4:

                st.error(
                    "❌ A nova senha precisa ter "
                    "pelo menos 4 caracteres."
                )

            elif nova_senha != confirmar_senha:

                st.error(
                    "❌ As senhas não conferem."
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

    st.title(
        "📥 Exportar dados"
    )

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

        arquivo = io.BytesIO()

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
            "✅ Excel preparado com sucesso."
        )

        st.download_button(
            label="📥 BAIXAR EXCEL",
            data=arquivo,
            file_name="PRODUCT_produtividade.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )
