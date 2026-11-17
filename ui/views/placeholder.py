"""Style Mate AI - Editorial Placeholder View
Displays a clean luxury editorial placeholder for pages scheduled for upcoming steps.
"""
import streamlit as st
from ui.components.navigation import navigate_to

def render_placeholder(page_title: str, phase_step: str, description: str):
    """Render a clean luxury placeholder view."""
    st.markdown(
        f"""
        <div class="hero-wrapper" style="padding: 34px 40px; margin-bottom: 24px;">
            <span class="hero-kicker">PHASE 4 · {phase_step}</span>
            <h1 class="hero-title">{page_title}</h1>
            <p class="hero-subtitle">
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="background: #FFFFFF; border: 1px solid #E8E3DA; border-radius: 14px; padding: 42px 36px; text-align: center; max-width: 620px; margin: 40px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.04);">
            <div style="font-family: 'Cinzel', serif; font-size: 1.8rem; margin-bottom: 12px; color: #9A6B43;">✦</div>
            <h3 style="font-family: 'Cinzel', serif; font-size: 1.35rem; margin: 0 0 10px 0; color: #1C1917;">
                View Scheduled for Next Step
            </h3>
            <p style="font-size: 0.88rem; color: #57534E; line-height: 1.55; margin-bottom: 24px;">
                Following the one-view-at-a-time protocol, this view will be built in the next step
                after the editorial homepage review.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("← Return to Homepage", use_container_width=True):
            navigate_to("Home")
