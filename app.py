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

    conn.commit()
    conn.close()


criar_banco()


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
        ORDER BY data DESC
        """,
        conn
    )

    conn.close()

    if not df.empty:

        df["data"] = pd.to_datetime(df["data"])

        # Total de SYSVET
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
# MENU LATERAL
# =========================================================

st.sidebar.title("📊 PRODUCT")

pagina = st.sidebar.radio(
    "MENU",
    [
        "📈 Dashboard",
        "📝 Lançar produtividade",
        "👥 Colaboradores",
        "📋 Histórico",
        "📥 Exportar"
    ]
)


# =========================================================
# DASHBOARD
# =========================================================

if pagina == "📈 Dashboard":

    st.title("📊 PRODUCT")

    st.caption(
        "Sistema de Controle de Produtividade"
    )

    df = buscar_produtividade()

    if df.empty:

        st.info(
            "Ainda não existem registros. "
            "Acesse 'Lançar produtividade' para começar."
        )

    else:

        # =================================================
        # FILTROS
        # =================================================

        st.sidebar.markdown("---")
        st.sidebar.subheader("🔎 FILTROS")

        data_min = df["data"].min().date()
        data_max = df["data"].max().date()

        periodo = st.sidebar.date_input(
            "Período",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max
        )

        if isinstance(periodo, tuple) and len(periodo) == 2:

            inicio, fim = periodo

            df_filtrado = df[
                (df["data"].dt.date >= inicio) &
                (df["data"].dt.date <= fim)
            ]

        else:

            df_filtrado = df.copy()

        lista_colaboradores = sorted(
            df_filtrado["colaborador"].unique()
        )

        selecionados = st.sidebar.multiselect(
            "Colaborador",
            lista_colaboradores,
            default=lista_colaboradores
        )

        if selecionados:

            df_filtrado = df_filtrado[
                df_filtrado["colaborador"].isin(selecionados)
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

            st.subheader("🏆 Ranking de produtividade")

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

        # =================================================
        # GRÁFICO POR TIPO
        # =================================================

        with col2:

            st.subheader("📊 Produtividade por tipo")

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
        # EVOLUÇÃO DIÁRIA
        # =================================================

        st.subheader("📈 Evolução da produtividade")

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
        # RANKING DETALHADO
        # =================================================

        st.subheader("🏆 Ranking detalhado")

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
            "⚠️ Cadastre primeiro os colaboradores."
        )

        st.info(
            "Vá até o menu '👥 Colaboradores'."
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
                        f"✅ {nome} cadastrado com sucesso!"
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "⚠️ Esse colaborador já está cadastrado."
                    )

    st.divider()

    st.subheader("Colaboradores cadastrados")

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

        arquivo = "PRODUCT_produtividade.xlsx"

        exportar.to_excel(
            arquivo,
            index=False
        )

        with open(arquivo, "rb") as f:

            st.download_button(
                label="📥 BAIXAR EXCEL",
                data=f,
                file_name="PRODUCT_produtividade.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

