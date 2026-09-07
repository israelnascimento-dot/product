import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date

# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="PRODUCT",
    page_icon="📊",
    layout="wide"
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

    # Tabela de colaboradores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    # Tabela de produtividade
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

    # Tabela de configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY,
            senha TEXT NOT NULL
        )
    """)

    # Cria senha inicial somente se ainda não existir
    cursor.execute(
        "SELECT COUNT(*) FROM configuracoes"
    )

    existe_senha = cursor.fetchone()[0]

    if existe_senha == 0:

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

    st.title("📊 PRODUCT")

    st.subheader(
        "🔐 Acesso ao Sistema"
    )

    st.write(
        "Digite sua senha para acessar o sistema."
    )

    senha = st.text_input(
        "🔑 Senha",
        type="password"
    )

    entrar = st.button(
        "🔓 ENTRAR",
        use_container_width=True
    )

    if entrar:

        senha_correta = buscar_senha()

        if senha == senha_correta:

            st.session_state["autenticado"] = True

            st.rerun()

        else:

            st.error(
                "❌ Senha incorreta."
            )


# =========================================================
# CONTROLE DE LOGIN
# =========================================================

if "autenticado" not in st.session_state:

    st.session_state["autenticado"] = False


if not st.session_state["autenticado"]:

    tela_login()

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

        # Total SYSVET
        df["total_sysvet"] = (
            df["sysvet_erro"] +
            df["sysvet_exito"]
        )

        # Produtividade total
        df["produtividade_total"] = (
            df["sysvet_erro"] +
            df["sysvet_exito"] +
            df["faturado"]
        )

        # Taxa de êxito
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
# MENU
# =========================================================

st.sidebar.title("📊 PRODUCT")

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


# =========================================================
# SAIR
# =========================================================

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

    st.title("📊 Dashboard")

    st.caption(
        "Sistema de Controle de Produtividade"
    )

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Ainda não existem registros."
        )

    else:

        # =================================================
        # FILTROS
        # =================================================

        st.sidebar.markdown("---")

        st.sidebar.subheader(
            "🔎 FILTROS"
        )

        # -------------------------------------------------
        # COLABORADOR
        # -------------------------------------------------

        colaboradores = sorted(
            df["colaborador"]
            .dropna()
            .unique()
            .tolist()
        )

        opcao_colaborador = [
            "👥 TODOS OS COLABORADORES"
        ] + colaboradores

        colaborador_selecionado = st.sidebar.selectbox(
            "👤 Selecione o colaborador",
            opcao_colaborador
        )

        # -------------------------------------------------
        # DATA
        # -------------------------------------------------

        data_min = df["data"].min().date()

        data_max = df["data"].max().date()

        periodo = st.sidebar.date_input(
            "📅 Período",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max
        )

        # -------------------------------------------------
        # FILTRO DE DATA
        # -------------------------------------------------

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

        # -------------------------------------------------
        # FILTRO DE COLABORADOR
        # -------------------------------------------------

        if (
            colaborador_selecionado
            != "👥 TODOS OS COLABORADORES"
        ):

            df_filtrado = df_filtrado[
                df_filtrado["colaborador"]
                == colaborador_selecionado
            ].copy()

            st.success(
                f"👤 Visualizando produtividade de: "
                f"**{colaborador_selecionado}**"
            )

        else:

            st.info(
                "👥 Visualizando produtividade de "
                "**todos os colaboradores**."
            )

        # =================================================
        # SEM RESULTADOS
        # =================================================

        if df_filtrado.empty:

            st.warning(
                "⚠️ Não existem registros para os "
                "filtros selecionados."
            )

            st.stop()

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

        if total_sysvet > 0:

            taxa_exito = (
                exito /
                total_sysvet *
                100
            )

        else:

            taxa_exito = 0

        # =================================================
        # CARDS
        # =================================================

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "❌ SYSVET ERRO",
            f"{erro:,}"
        )

        col2.metric(
            "✅ SYSVET ÊXITO",
            f"{exito:,}"
        )

        col3.metric(
            "📁 FATURADO",
            f"{faturado:,}"
        )

        col4.metric(
            "📊 PRODUTIVIDADE",
            f"{produtividade_total:,}"
        )

        col5.metric(
            "🎯 TAXA DE ÊXITO",
            f"{taxa_exito:.1f}%"
        )

        st.divider()

        # =================================================
        # RESUMO POR COLABORADOR
        # =================================================

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

        # =================================================
        # RANKING
        # =================================================

        st.subheader(
            "🏆 Produtividade por colaborador"
        )

        ranking = resumo.copy()

        ranking.insert(
            0,
            "Posição",
            range(
                1,
                len(ranking) + 1
            )
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

        st.dataframe(
            ranking,
            use_container_width=True,
            hide_index=True
        )

        # =================================================
        # GRÁFICOS
        # =================================================

        col1, col2 = st.columns(2)

        with col1:

            st.subheader(
                "🏆 Ranking de produtividade"
            )

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
                xaxis_title="Colaborador",
                yaxis_title="Produtividade"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:

            st.subheader(
                "📊 Produtividade por tipo"
            )

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
            yaxis_title="Quantidade"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # =================================================
        # DETALHAMENTO DO COLABORADOR
        # =================================================

        if (
            colaborador_selecionado
            != "👥 TODOS OS COLABORADORES"
        ):

            st.divider()

            st.subheader(
                f"👤 Detalhamento — "
                f"{colaborador_selecionado}"
            )

            detalhes = df_filtrado[
                [
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
                "Colaborador",
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

    st.title(
        "📝 Lançar produtividade"
    )

    colaboradores = buscar_colaboradores()

    if colaboradores.empty:

        st.warning(
            "⚠️ Cadastre primeiro os colaboradores."
        )

    else:

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
                f"📊 Produtividade total: "
                f"**{total}**"
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
                    "✅ Produtividade registrada!"
                )

                st.rerun()


# =========================================================
# COLABORADORES
# =========================================================

elif pagina == "👥 Colaboradores":

    st.title(
        "👥 Cadastro de colaboradores"
    )

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
                        f"✅ {nome} cadastrado!"
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

    st.title(
        "📋 Histórico de produtividade"
    )

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
            "🗑️ Excluir registros por data"
        )

        data_exclusao = st.date_input(
            "📅 Selecione a data",
            value=date.today(),
            key="data_exclusao"
        )

        registros_data = df[
            df["data"].dt.date
            == data_exclusao
        ]

        quantidade = len(
            registros_data
        )

        st.metric(
            "📋 Registros encontrados",
            quantidade
        )

        if quantidade > 0:

            confirmar_data = st.checkbox(
                "⚠️ Confirmo que desejo excluir "
                "TODOS os registros desta data.",
                key="confirmar_data"
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
        # EXCLUSÃO INDIVIDUAL
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
            f"📊 Total: "
            f"{registro['produtividade_total']}"
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

    st.title(
        "📥 Exportar dados"
    )

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Nenhum dado disponível."
        )

    else:

        exportar = df.copy()

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
            "✅ Excel pronto!"
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

    st.title(
        "🔐 Alterar senha"
    )

    st.info(
        "Aqui você pode alterar a senha utilizada "
        "para entrar no PRODUCT."
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

            senha_correta = buscar_senha()

            if senha_atual != senha_correta:

                st.error(
                    "❌ A senha atual está incorreta."
                )

            elif not nova_senha:

                st.error(
                    "❌ Digite uma nova senha."
                )

            elif nova_senha != confirmar_senha:

                st.error(
                    "❌ As novas senhas não são iguais."
                )

            elif len(nova_senha) < 4:

                st.error(
                    "❌ A senha deve ter pelo menos "
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
                    "A próxima vez que entrar no "
                    "sistema, utilize a nova senha."
                )

