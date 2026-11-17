"""Style Mate AI - Horizontal Top Navigation Component
Implements a minimalist, high-end editorial top navigation bar:
STYLE MATE AI | Home | AI Studio | My Wardrobe | Outfit Ideas
"""
import streamlit as st

NAV_PAGES = ["Home", "AI Studio", "My Wardrobe", "Fashion Catalog", "Outfit Ideas"]

def render_navigation() -> str:
    """Render the top horizontal navigation bar and return the active page key."""
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Home"

    current = st.session_state["current_page"]

    col_brand, col_nav = st.columns([1.0, 3.0], gap="medium")

    with col_brand:
        st.markdown(
            """
            <div style="padding: 2px 0;">
                <span class="nav-brand-title">STYLE MATE AI</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_nav:
        n1, n2, n3, n4, n5 = st.columns([1, 1, 1.1, 1, 1.1], gap="small")
        
        with n1:
            if st.button("Home", key="top_nav_home", type="primary" if current == "Home" else "secondary", use_container_width=True):
                if current != "Home":
                    navigate_to("Home")
        with n2:
            if st.button("AI Studio", key="top_nav_studio", type="primary" if current == "AI Studio" else "secondary", use_container_width=True):
                if current != "AI Studio":
                    navigate_to("AI Studio")
        with n3:
            if st.button("My Wardrobe", key="top_nav_wardrobe", type="primary" if current == "My Wardrobe" else "secondary", use_container_width=True):
                if current != "My Wardrobe":
                    navigate_to("My Wardrobe")
        with n4:
            if st.button("Catalog", key="top_nav_catalog", type="primary" if current == "Fashion Catalog" else "secondary", use_container_width=True):
                if current != "Fashion Catalog":
                    navigate_to("Fashion Catalog")
        with n5:
            if st.button("Outfit Ideas", key="top_nav_outfits", type="primary" if current == "Outfit Ideas" else "secondary", use_container_width=True):
                if current != "Outfit Ideas":
                    navigate_to("Outfit Ideas")

    st.markdown('<div class="nav-container"></div>', unsafe_allow_html=True)
    return st.session_state["current_page"]

def navigate_to(page_key: str):
    """Programmatically navigate to a page."""
    st.session_state["current_page"] = page_key
    st.rerun()
