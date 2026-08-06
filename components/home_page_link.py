import streamlit as st

_STYLE = """
<style>
a.home-page-link {
    display: block;
    height: 100%;
    padding: 1rem 1.25rem;
    border: 1px solid rgba(128, 128, 128, 0.3);
    border-radius: 0.5rem;
    text-decoration: none;
    color: inherit;
    transition: border-color 0.15s ease, background-color 0.15s ease;
}
a.home-page-link:hover {
    border-color: rgba(128, 128, 128, 0.6);
    background-color: rgba(128, 128, 128, 0.08);
}
a.home-page-link .home-page-link__title {
    display: block;
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
}
a.home-page-link .home-page-link__subtitle {
    display: block;
    font-size: 0.95rem;
    opacity: 0.75;
    line-height: 1.4;
}
</style>
"""


def home_page_link(icon: str, title: str, subtitle: str, page: str) -> None:
    """Card clicável (ícone + título + subtítulo) que navega para outra página."""
    st.markdown(_STYLE, unsafe_allow_html=True)
    st.markdown(
        f'<a class="home-page-link" href="{page}" target="_self">'
        f'<span class="home-page-link__title">{icon} {title}</span>'
        f'<span class="home-page-link__subtitle">{subtitle}</span>'
        f"</a>",
        unsafe_allow_html=True,
    )
