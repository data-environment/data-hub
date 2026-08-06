import streamlit as st


def render_home() -> None:
    st.title("Data Hub")
    st.caption("Central de ferramentas de dados.")

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1, st.container(border=True):
        st.subheader("📚 Wiki")
        st.write(
            "Documentação automática dos DataContracts: fonte, schema, "
            "qualidade, ingestão, distribuição e regras de negócio."
        )
        st.page_link("wiki/screen.py", label="Abrir Wiki", icon="📚")

    with col2, st.container(border=True):
        st.subheader("✅ SmartCheck")
        st.write("Validação de arquivos recebidos contra o contrato de dados.")
        st.page_link("smartcheck/screen.py", label="Abrir SmartCheck", icon="✅")

    with col3, st.container(border=True):
        st.subheader("🗃️ SmartData")
        st.write("Em construção.")
        st.page_link("smartdata/screen.py", label="Abrir SmartData", icon="🗃️")

    with col4, st.container(border=True):
        st.subheader("🔗 Linktree")
        st.write("Em construção.")
        st.page_link("linktree/screen.py", label="Abrir Linktree", icon="🔗")


st.set_page_config(page_title="Data Hub", layout="wide")

home_page = st.Page(
    render_home, title="Início", icon="🏠", url_path="home", default=True
)
wiki_page = st.Page(
    "wiki/screen.py", title="Wiki de Contratos", icon="📚", url_path="wiki"
)
smartcheck_page = st.Page(
    "smartcheck/screen.py", title="SmartCheck", icon="✅", url_path="smartcheck"
)
smartdata_page = st.Page(
    "smartdata/screen.py", title="SmartData", icon="🗃️", url_path="smartdata"
)
linktree_page = st.Page(
    "linktree/screen.py", title="Linktree", icon="🔗", url_path="linktree"
)

pg = st.navigation(
    [home_page, wiki_page, smartcheck_page, smartdata_page, linktree_page]
)
pg.run()
