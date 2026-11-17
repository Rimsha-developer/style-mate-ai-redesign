"""Style Mate AI - Application Entry Point
Editorial Western Fashion Recognition & Wardrobe Intelligence System.
"""
import streamlit as st
from ui.styles import inject_luxury_styles
from ui.components.navigation import render_navigation
from ui.views.home import render_home
from ui.views.ai_studio import render_ai_studio
from ui.views.wardrobe_view import render_wardrobe_view
from ui.views.master_catalog_view import render_master_catalog_view
from ui.views.outfit_ideas_view import render_outfit_ideas_view

# -------------------------------------------------------------
# Page Configuration
# -------------------------------------------------------------
st.set_page_config(
    page_title="Style Mate AI · Editorial Fashion Intelligence",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# Global Luxury Styling
# -------------------------------------------------------------
inject_luxury_styles()

# -------------------------------------------------------------
# Sidebar Navigation Router
# -------------------------------------------------------------
active_page = render_navigation()

# -------------------------------------------------------------
# View Dispatcher
# -------------------------------------------------------------
if active_page == "Home":
    render_home()
elif active_page == "AI Studio":
    render_ai_studio()
elif active_page == "My Wardrobe":
    render_wardrobe_view()
elif active_page == "Fashion Catalog":
    render_master_catalog_view()
elif active_page == "Outfit Ideas":
    render_outfit_ideas_view()
