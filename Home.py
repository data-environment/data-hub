import streamlit as st

from components.home_page_link import home_page_link


def render_home() -> None:
    st.title("Data Hub")
    st.caption("Sua central de ferramentas de dados.")

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        home_page_link(
            icon="📚",
            title="Wiki",
            subtitle="Documentação de contratos, processos e pipelines.",
            page="wiki",
        )

    with col2:
        home_page_link(
            icon="✅",
            title="SmartCheck",
            subtitle="Validação de arquivos recebidos contra o contrato de dados.",
            page="smartcheck",
        )

    with col3:
        home_page_link(
            icon="🗃️",
            title="SmartData",
            subtitle="Consulte o banco de dados.",
            page="smartdata",
        )

    with col4:
        home_page_link(
            icon="🔗",
            title="Linktree",
            subtitle="Acesso fácil a links úteis relacionados.",
            page="linktree",
        )


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
