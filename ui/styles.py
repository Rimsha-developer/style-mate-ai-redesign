"""Style Mate AI - Luxury Editorial Styling System
Defines theme tokens, custom CSS, typography, and visual components for high-fashion editorial aesthetic.
Color Palette:
- Ivory Base: #FAF8F5
- Soft Cream Surface: #F7F4EE
- Card Surface: #FFFFFF
- Deep Charcoal: #1C1917
- Soft Charcoal: #57534E
- Muted Taupe: #8C827A
- Warm Chocolate / Bronze Accent: #4A2E18 & #9A6B43
- Subtle Sand Borders: #E8E3DA
"""

LUXURY_CSS = """
<style>
/* ------------------------------------------------------------- */
/* Google Fonts Import: Cinzel & Plus Jakarta Sans               */
/* ------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

:root {
    --bg-ivory: #FAF8F5;
    --card-surface: #FFFFFF;
    --card-surface-alt: #F7F4EE;
    --text-primary: #1C1917;
    --text-secondary: #57534E;
    --text-muted: #8C827A;
    --accent-chocolate: #4A2E18;
    --accent-bronze: #9A6B43;
    --accent-sand: #DCD5C9;
    --border-subtle: #E8E3DA;
    --border-light: #F0ECE4;
    --shadow-soft: 0 4px 20px rgba(28, 25, 23, 0.04);
    --shadow-hover: 0 12px 32px rgba(28, 25, 23, 0.08);
}

/* ------------------------------------------------------------- */
/* Global Reset & Hide Default Sidebar Navigation                */
/* ------------------------------------------------------------- */
[data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-ivory) !important;
}

img {
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
}

.main .block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 4.5rem !important;
    max-width: 1240px !important;
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    color: var(--text-primary) !important;
}

h1, h2, h3, h4, .editorial-heading {
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.04em !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ------------------------------------------------------------- */
/* Top Horizontal Navigation Bar                                 */
/* ------------------------------------------------------------- */
.nav-container {
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 14px;
    margin-bottom: 28px;
}

.nav-brand-title {
    font-family: 'Cinzel', serif;
    font-size: 1.42rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: var(--text-primary);
    text-transform: uppercase;
    display: inline-block;
    padding-top: 6px;
}

/* Custom styling for Streamlit navigation buttons */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--text-secondary) !important;
    padding: 6px 12px !important;
    transition: all 0.25s ease !important;
    box-shadow: none !important;
}

div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
    color: var(--accent-chocolate) !important;
    background: transparent !important;
}

div[data-testid="stHorizontalBlock"] button[kind="primary"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid var(--accent-chocolate) !important;
    border-radius: 0 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--accent-chocolate) !important;
    padding: 6px 12px !important;
    box-shadow: none !important;
}

/* ------------------------------------------------------------- */
/* PRESERVED Hero Section                                        */
/* ------------------------------------------------------------- */
.hero-wrapper {
    background: linear-gradient(135deg, #FAF7F2 0%, #F3EDE2 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 38px 44px;
    margin-bottom: 34px;
    box-shadow: var(--shadow-soft);
    position: relative;
    overflow: hidden;
}

.hero-wrapper::after {
    content: "";
    position: absolute;
    right: -60px;
    top: -60px;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(184, 134, 11, 0.08) 0%, transparent 70%);
    border-radius: 50%;
}

.hero-kicker {
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--accent-bronze);
    margin-bottom: 8px;
    display: inline-block;
}

.hero-title {
    font-family: 'Cinzel', serif;
    font-size: 2.3rem;
    line-height: 1.15;
    margin: 0 0 10px 0;
    color: var(--text-primary);
}

.hero-subtitle {
    font-size: 1.0rem;
    color: var(--text-secondary);
    max-width: 680px;
    margin: 0;
    line-height: 1.55;
    font-weight: 400;
}

/* ------------------------------------------------------------- */
/* Section A: Fashion Editorial Showcase (Magazine Layout)       */
/* ------------------------------------------------------------- */
.showcase-container {
    margin: 36px 0 54px 0;
}

.magazine-frame {
    background: var(--card-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow-soft);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.magazine-frame:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-hover);
}

.magazine-img-tall {
    width: 100%;
    height: 480px;
    object-fit: cover;
    display: block;
    background-color: #EFEBE4;
}

.magazine-img-stacked {
    width: 100%;
    height: 225px;
    object-fit: cover;
    display: block;
    background-color: #EFEBE4;
}

.magazine-caption-box {
    padding: 16px 20px;
    background: var(--card-surface);
}

.caption-tag {
    font-size: 0.68rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--accent-bronze);
    margin-bottom: 4px;
}

.caption-title {
    font-family: 'Cinzel', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 4px 0;
}

.caption-desc {
    font-size: 0.80rem;
    color: var(--text-muted);
    margin: 0;
    line-height: 1.45;
}

/* ------------------------------------------------------------- */
/* Section B: Discover Your Style (Feature Cards)                */
/* ------------------------------------------------------------- */
.feature-card {
    background: var(--card-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow-soft);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    display: flex;
    flex-direction: column;
    height: 100%;
}

.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-hover);
}

.feature-img {
    width: 100%;
    height: 280px;
    object-fit: cover;
    display: block;
    background-color: #EFEBE4;
}

.feature-content {
    padding: 22px 24px;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}

.feature-tag {
    font-size: 0.70rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--accent-bronze);
    margin-bottom: 6px;
}

.feature-title {
    font-family: 'Cinzel', serif;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 10px 0;
}

.feature-text {
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.55;
    margin: 0 0 18px 0;
    flex-grow: 1;
}

/* ------------------------------------------------------------- */
/* Section C: Fashion Inspiration Gallery                        */
/* ------------------------------------------------------------- */
.gallery-card {
    background: var(--card-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    overflow: hidden;
    box-shadow: var(--shadow-soft);
    transition: transform 0.25s ease;
}

.gallery-card:hover {
    transform: translateY(-3px);
}

.gallery-img {
    width: 100%;
    height: 290px;
    object-fit: cover;
    display: block;
    background-color: #EFEBE4;
}

.gallery-caption {
    padding: 12px 14px;
    text-align: center;
}

.gallery-cat {
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--accent-bronze);
    margin-bottom: 2px;
}

.gallery-title {
    font-family: 'Cinzel', serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}

/* ------------------------------------------------------------- */
/* Section D: Brand Statement                                    */
/* ------------------------------------------------------------- */
.statement-box {
    background: linear-gradient(135deg, #FAF8F4 0%, #F5F0E6 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 56px 48px;
    margin: 54px 0 46px 0;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.statement-tag {
    font-size: 0.72rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--accent-bronze);
    margin-bottom: 14px;
}

.statement-quote {
    font-family: 'Cinzel', serif;
    font-size: 1.48rem;
    font-style: italic;
    color: var(--text-primary);
    max-width: 820px;
    margin: 0 auto 16px auto;
    line-height: 1.55;
    font-weight: 400;
}

.statement-author {
    font-size: 0.82rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
}

/* ------------------------------------------------------------- */
/* Section E: Luxury Editorial Footer                            */
/* ------------------------------------------------------------- */
.editorial-footer {
    border-top: 1px solid var(--border-subtle);
    padding: 44px 0 24px 0;
    margin-top: 50px;
    text-align: center;
}

.footer-brand {
    font-family: 'Cinzel', serif;
    font-size: 1.35rem;
    letter-spacing: 0.18em;
    color: var(--text-primary);
    font-weight: 700;
    margin-bottom: 8px;
}

.footer-tagline {
    font-size: 0.85rem;
    color: var(--text-secondary);
    max-width: 520px;
    margin: 0 auto 20px auto;
    line-height: 1.5;
}

.footer-nav {
    display: flex;
    justify-content: center;
    gap: 28px;
    margin-bottom: 24px;
}

.footer-nav-link {
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-secondary);
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s ease;
}

.footer-nav-link:hover {
    color: var(--accent-chocolate);
}

.footer-copy {
    font-size: 0.74rem;
    color: var(--text-muted);
    letter-spacing: 0.05em;
}

/* ------------------------------------------------------------- */
/* Section D: Digital Wardrobe UI Components                     */
/* ------------------------------------------------------------- */
.wardrobe-kpi-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #FFFFFF;
    border: 1px solid var(--border-subtle);
    padding: 6px 16px;
    border-radius: 50px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--accent-chocolate);
    box-shadow: var(--shadow-soft);
}

.wardrobe-item-card {
    background: var(--card-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow-soft);
    transition: transform 0.22s ease, box-shadow 0.22s ease;
    display: flex;
    flex-direction: column;
    margin-bottom: 16px;
}

.wardrobe-item-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-hover);
    border-color: var(--accent-sand);
}

.wardrobe-item-body {
    padding: 16px 18px 14px 18px;
    display: flex;
    flex-direction: column;
}

.wardrobe-slot-kicker {
    font-family: 'Cinzel', serif;
    font-size: 0.68rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--accent-bronze);
    font-weight: 700;
    margin-bottom: 4px;
}

.wardrobe-item-title {
    font-family: 'Cinzel', serif;
    font-size: 1.10rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 10px 0;
}

.wardrobe-pill-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 10px;
}

.wardrobe-meta-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--card-surface-alt);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 3px 10px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-secondary);
}

.wardrobe-color-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    border: 1px solid rgba(0,0,0,0.15);
}

.wardrobe-empty-box {
    background: #FFFFFF;
    border: 1px dashed var(--border-subtle);
    border-radius: 16px;
    padding: 60px 32px;
    text-align: center;
    box-shadow: var(--shadow-soft);
    margin: 24px 0;
}

.wardrobe-detail-box {
    background: #FFFFFF;
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 28px;
    box-shadow: var(--shadow-soft);
    margin-bottom: 24px;
}

/* ------------------------------------------------------------- */
/* High-Contrast Form Controls, Filters & Tabs Styling           */
/* ------------------------------------------------------------- */

/* Text inputs & Search fields */
div[data-testid="stTextInput"] input {
    color: #1C1917 !important;
    background-color: #FFFFFF !important;
    border: 1px solid #D8D2C7 !important;
    border-radius: 6px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.90rem !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #8C827A !important;
}

div[data-testid="stTextInput"] label, 
div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label,
div[data-testid="stMultiSelect"] label {
    color: #1C1917 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
}

/* Selectbox Dropdown controls */
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #D8D2C7 !important;
    border-radius: 6px !important;
    color: #1C1917 !important;
}

div[data-baseweb="select"] * {
    color: #1C1917 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.88rem !important;
}

/* Dropdown popover menu options */
ul[data-baseweb="menu"], div[data-baseweb="popover"] {
    background-color: #FFFFFF !important;
    border: 1px solid #D8D2C7 !important;
    border-radius: 6px !important;
    box-shadow: 0 8px 24px rgba(28, 25, 23, 0.12) !important;
}

li[data-baseweb="menu-item"] {
    color: #1C1917 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.88rem !important;
    background-color: #FFFFFF !important;
}

li[data-baseweb="menu-item"]:hover {
    background-color: #F7F4EE !important;
    color: #4A2E18 !important;
}

/* Radio buttons & filter pills */
div[data-testid="stRadio"] div[role="radiogroup"] {
    gap: 10px !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label {
    background: #FFFFFF !important;
    border: 1px solid #D8D2C7 !important;
    border-radius: 20px !important;
    padding: 6px 16px !important;
    color: #1C1917 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
    border-color: #9A6B43 !important;
    background: #FDFCFB !important;
    color: #4A2E18 !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"],
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background: #4A2E18 !important;
    border-color: #4A2E18 !important;
    color: #FFFFFF !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] *,
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) * {
    color: #FFFFFF !important;
}

/* Tabs styling in AI Studio & everywhere */
div[data-baseweb="tab-list"] {
    background-color: transparent !important;
    border-bottom: 2px solid #E8E3DA !important;
    gap: 16px !important;
    margin-bottom: 24px !important;
}

button[data-baseweb="tab"] {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    border-radius: 0 !important;
    color: #57534E !important;
    font-family: 'Cinzel', serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    padding: 12px 22px !important;
    transition: all 0.2s ease !important;
}

button[data-baseweb="tab"]:hover {
    color: #4A2E18 !important;
    background-color: rgba(154, 107, 67, 0.06) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #4A2E18 !important;
    border-bottom: 3px solid #4A2E18 !important;
    font-weight: 700 !important;
}

button[data-baseweb="tab"][aria-selected="true"] * {
    color: #4A2E18 !important;
}

/* Streamlit Toggle */
div[data-testid="stToggle"] label {
    color: #1C1917 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
</style>
"""

def inject_luxury_styles():
    """Inject the global luxury styling system into the Streamlit session."""
    import streamlit as st
    st.markdown(LUXURY_CSS, unsafe_allow_html=True)
