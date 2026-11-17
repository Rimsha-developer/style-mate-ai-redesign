"""Style Mate AI - Luxury Editorial Homepage View
Transforms the homepage into a high-fashion, truly UNISEX editorial magazine experience.
Preserves the exact Editorial Hero section, with an asymmetric unisex magazine showcase,
balanced editorial feature columns, an 8-look unisex fashion gallery, brand philosophy, and luxury footer.
"""
import streamlit as st
from ui.components.navigation import navigate_to

# ---------------------------------------------------------------------------
# High-Resolution Fashion Editorial Imagery (100% Verified, Non-Repetitive)
# Balanced representation of Men's, Women's, and Unisex Contemporary Fashion
# ---------------------------------------------------------------------------

# Section A: Showcase
IMG_SHOWCASE_MEN_TALL = "https://images.unsplash.com/photo-1617137984095-74e4e5e3613f?auto=format&fit=crop&w=1000&q=80"  # Men's structured tailored overcoat
IMG_SHOWCASE_WOMEN_STACKED = "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?auto=format&fit=crop&w=1000&q=80"  # Women's timeless camel trench
IMG_SHOWCASE_DETAIL_STACKED = "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=1000&q=80"  # Artisanal footwear & leather

# Section B: Discover Your Style (3 Features)
IMG_FEAT_MEN_SUIT = "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=800&q=80"  # Men's tailored navy suit / AI analysis
IMG_FEAT_WARDROBE_UNISEX = "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?auto=format&fit=crop&w=800&q=80"  # Capsule wardrobe rack
IMG_FEAT_WOMEN_ENSEMBLE = "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=800&q=80"  # Women's tailored ensemble / outfit inspiration

# Section C: Fashion Inspiration Gallery (8 Balanced Categories)
IMG_GAL_MEN_FORMAL = "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?auto=format&fit=crop&w=800&q=80"  # 1. Men's Formal Wear
IMG_GAL_WOMEN_FORMAL = "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=800&q=80"  # 2. Women's Formal Wear
IMG_GAL_MEN_CASUAL = "https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=800&q=80"  # 3. Men's Casual Wear
IMG_GAL_WOMEN_CASUAL = "https://images.unsplash.com/photo-1554412933-514a83d2f3c8?auto=format&fit=crop&w=800&q=80"  # 4. Women's Casual Wear
IMG_GAL_MEN_STREET = "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?auto=format&fit=crop&w=800&q=80"  # 5. Men's Streetwear
IMG_GAL_WOMEN_STREET = "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=800&q=80"  # 6. Women's Streetwear
IMG_GAL_UNISEX_MINIMAL = "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=800&q=80"  # 7. Unisex Minimalist Fashion
IMG_GAL_SHOES_ACCESSORIES = "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=800&q=80"  # 8. Shoes and Accessories


def render_home():
    """Render the luxury unisex fashion editorial homepage."""
    # -------------------------------------------------------------
    # 1. PRESERVED EXISTING EDITORIAL HERO SECTION (EXACT UNTOUCHED)
    # -------------------------------------------------------------
    st.markdown(
        """
        <div class="hero-wrapper">
            <span class="hero-kicker">AUTONOMOUS FASHION INTELLIGENCE</span>
            <h1 class="hero-title">Elevate Your Aesthetic with Editorial Precision</h1>
            <p class="hero-subtitle">
                Style Mate AI harmonizes deep neural computer vision with color theory and occasion-aware
                heuristics. Decompose complex silhouettes, curate a responsive digital wardrobe, and generate
                effortlessly balanced Western ensembles in milliseconds.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------------------------------------------------
    # 2. SECTION A: FASHION EDITORIAL SHOWCASE (Asymmetric Magazine Layout)
    # -------------------------------------------------------------
    st.markdown(
        """
        <div style="margin: 44px 0 18px 0;">
            <div class="caption-tag">COLLECTION DISCOURSE</div>
            <h2 style="font-family: 'Cinzel', serif; font-size: 1.85rem; color: #1C1917; margin: 4px 0 6px 0;">
                The Architectural Form
            </h2>
            <p style="font-size: 0.92rem; color: #57534E; margin: 0 0 20px 0; max-width: 620px;">
                An editorial contemplation on proportion, tactile materiality, and tonal depth across contemporary
                men's and women's Western tailoring.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_tall, col_stacked = st.columns([1.15, 1.0], gap="large")

    with col_tall:
        st.markdown(
            f"""
            <div class="magazine-frame">
                <img src="{IMG_SHOWCASE_MEN_TALL}" alt="Men's Tailored Overcoat" class="magazine-img-tall" />
                <div class="magazine-caption-box">
                    <div class="caption-tag">EDITORIAL VOL. IV · MENSWEAR</div>
                    <div class="caption-title">The Structured Navy Suit & Architectural Form</div>
                    <p class="caption-desc">
                        Sharply sculpted tailoring with a crisp white shirt and classic pocket square. A disciplined composition in deep navy,
                        stone, and minimal architectural form.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_stacked:
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; gap: 20px; height: 100%;">
                <div class="magazine-frame">
                    <img src="{IMG_SHOWCASE_WOMEN_STACKED}" alt="Women's Camel Trench" class="magazine-img-stacked" />
                    <div class="magazine-caption-box" style="padding: 14px 18px;">
                        <div class="caption-tag">CHROMA STUDY · WOMENSWEAR</div>
                        <div class="caption-title" style="font-size: 0.95rem;">Camel Drape & Warm Tonalities</div>
                        <p class="caption-desc" style="font-size: 0.78rem;">
                            Soft-focus camel gabardine paired with fine gauge cream knitwear.
                        </p>
                    </div>
                </div>
                <div class="magazine-frame">
                    <img src="{IMG_SHOWCASE_DETAIL_STACKED}" alt="Artisanal Footwear" class="magazine-img-stacked" />
                    <div class="magazine-caption-box" style="padding: 14px 18px;">
                        <div class="caption-tag">MATERIALITY · ACCESSORIES</div>
                        <div class="caption-title" style="font-size: 0.95rem;">Artisanal Leather & Clean Lines</div>
                        <p class="caption-desc" style="font-size: 0.78rem;">
                            Hand-finished calfskin footwear, minimalist hardware, and tactile suedes.
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # -------------------------------------------------------------
    # 3. SECTION B: DISCOVER YOUR STYLE (3 Editorial Feature Stories)
    # -------------------------------------------------------------
    st.markdown(
        """
        <div style="margin: 64px 0 24px 0; text-align: center;">
            <div class="caption-tag" style="letter-spacing: 0.22em;">INTELLIGENT EXPERIENCES</div>
            <h2 style="font-family: 'Cinzel', serif; font-size: 2.05rem; color: #1C1917; margin: 6px 0 10px 0;">
                Discover Your Signature Style
            </h2>
            <p style="font-size: 0.94rem; color: #57534E; margin: 0 auto; max-width: 600px; line-height: 1.55;">
                Three harmonized modules tailored for men and women, connecting deep neural recognition to deliberate wardrobe curation.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    f1, f2, f3 = st.columns(3, gap="medium")

    with f1:
        st.markdown(
            f"""
            <div class="feature-card">
                <img src="{IMG_FEAT_MEN_SUIT}" alt="AI Fashion Analysis" class="feature-img" />
                <div class="feature-content">
                    <div class="feature-tag">01 / NEURAL VISION</div>
                    <div class="feature-title">AI Fashion Analysis</div>
                    <p class="feature-text">
                        Instant silhouette classification across 18 Western apparel archetypes with dominant HSV
                        palette extraction and occasion etiquette detection for men and women.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Explore Studio →", key="btn_disc_studio", use_container_width=True):
            navigate_to("AI Studio")

    with f2:
        st.markdown(
            f"""
            <div class="feature-card">
                <img src="{IMG_FEAT_WARDROBE_UNISEX}" alt="Digital Wardrobe" class="feature-img" />
                <div class="feature-content">
                    <div class="feature-tag">02 / CAPSULE CURATION</div>
                    <div class="feature-title">Digital Wardrobe</div>
                    <p class="feature-text">
                        Curate your personal collection into modular slots: Tops, Bottoms, Dresses, Outerwear,
                        Shoes, and Bags with intelligent wear-frequency logging.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Explore Wardrobe →", key="btn_disc_wardrobe", use_container_width=True):
            navigate_to("My Wardrobe")

    with f3:
        st.markdown(
            f"""
            <div class="feature-card">
                <img src="{IMG_FEAT_WOMEN_ENSEMBLE}" alt="Outfit Inspiration" class="feature-img" />
                <div class="feature-content">
                    <div class="feature-tag">03 / HARMONY HEURISTICS</div>
                    <div class="feature-title">Outfit Inspiration</div>
                    <p class="feature-text">
                        Autonomous ensemble compositions calibrated with circular hue distance formulas, neutral
                        palette anchors, and occasion compatibility matrices.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Discover Outfits →", key="btn_disc_outfits", use_container_width=True):
            navigate_to("Outfit Ideas")

    # -------------------------------------------------------------
    # 4. SECTION C: FASHION INSPIRATION GALLERY (8 Balanced Categories)
    # -------------------------------------------------------------
    st.markdown(
        """
        <div style="margin: 64px 0 22px 0;">
            <div class="caption-tag">MOODBOARD ARCHIVE</div>
            <h2 style="font-family: 'Cinzel', serif; font-size: 1.85rem; color: #1C1917; margin: 4px 0 6px 0;">
                Curated Fashion Inspiration
            </h2>
            <p style="font-size: 0.92rem; color: #57534E; margin: 0 0 24px 0; max-width: 640px;">
                A comprehensive visual compendium of Western aesthetics across men's and women's formal, casual,
                streetwear, and minimalist styling.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Row 1: Formal & Casual (Men + Women)
    r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4, gap="medium")

    with r1_col1:
        st.markdown(
            f"""
            <div class="gallery-card">
                <img src="{IMG_GAL_MEN_FORMAL}" alt="Men's Formal Wear" class="gallery-img" />
                <div class="gallery-caption">
                    <div class="gallery-cat">FORMAL · MEN</div>
                    <div class="gallery-title">Bespoke Tailoring & Silk Ties</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with r1_col2:
        st.markdown(
            f"""
            <div class="gallery-card">
                <img src="{IMG_GAL_WOMEN_FORMAL}" alt="Women's Formal Wear" class="gallery-img" />
                <div class="gallery-caption">
                    <div class="gallery-cat">FORMAL · WOMEN</div>
                    <div class="gallery-title">Architectural Evening Silhouettes</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with r1_col3:
        st.markdown(
            f"""
            <div class="gallery-card">
                <img src="{IMG_GAL_MEN_CASUAL}" alt="Men's Casual Wear" class="gallery-img" />
                <div class="gallery-caption">
                    <div class="gallery-cat">CASUAL · MEN</div>
                    <div class="gallery-title">Overshirts & Selvedge Denim</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with r1_col4:
        st.markdown(
            f"""
            <div class="gallery-card">
                <img src="{IMG_GAL_WOMEN_CASUAL}" alt="Women's Casual Wear" class="gallery-img" />
                <div class="gallery-caption">
                    <div class="gallery-cat">CASUAL · WOMEN</div>
                    <div class="gallery-title">Cashmere Knitwear & Tonal Denim</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div style="height: 18px;"></div>', unsafe_allow_html=True)

    # Row 2: Streetwear, Minimalist & Footwear (Men + Women + Unisex)
    r2_col1, r2_col2, r2_col3, r2_col4 = st.columns(4, gap="medium")

    with r2_col1:
        st.markdown(
            f"""
            <div class="gallery-card">
                <img src="{IMG_GAL_MEN_STREET}" alt="Men's Streetwear" class="gallery-img" />
                <div class="gallery-caption">
                    <div class="gallery-cat">STREETWEAR · MEN</div>
                    <div class="gallery-title">Layered Outerwear & Low-Tops</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with r2_col2:
        st.markdown(
            f"""
            <div class="gallery-card">
                <img src="{IMG_GAL_WOMEN_STREET}" alt="Women's Streetwear" class="gallery-img" />
                <div class="gallery-caption">
                    <div class="gallery-cat">STREETWEAR · WOMEN</div>
                    <div class="gallery-title">Statement Bombers & High-Tops</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with r2_col3:
        st.markdown(
            f"""
            <div class="gallery-card">
                <img src="{IMG_GAL_UNISEX_MINIMAL}" alt="Unisex Minimalist Fashion" class="gallery-img" />
                <div class="gallery-caption">
                    <div class="gallery-cat">MINIMALIST · UNISEX</div>
                    <div class="gallery-title">Monochrome Neutral Layering</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with r2_col4:
        st.markdown(
            f"""
            <div class="gallery-card">
                <img src="{IMG_GAL_SHOES_ACCESSORIES}" alt="Shoes and Accessories" class="gallery-img" />
                <div class="gallery-caption">
                    <div class="gallery-cat">FOOTWEAR · ACCESSORIES</div>
                    <div class="gallery-title">Artisanal Leather & Clean Sneaker Design</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # -------------------------------------------------------------
    # 5. SECTION D: BRAND STATEMENT
    # -------------------------------------------------------------
    st.markdown(
        """
        <div class="statement-box">
            <div class="statement-tag">THE PHILOSOPHY</div>
            <div class="statement-quote">
                &ldquo;We believe personal style is an architectural dialogue between form, palette, and intention.
                Style Mate AI transforms computational vision into an intuitive extension of your aesthetic discernment &mdash;
                crafted for all silhouettes and discerning tastes.&rdquo;
            </div>
            <div class="statement-author">
                STYLE MATE AI &nbsp;·&nbsp; UNISEX FASHION INTELLIGENCE
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------------------------------------------------
    # 6. SECTION E: LUXURY EDITORIAL FOOTER
    # -------------------------------------------------------------
    st.markdown(
        """
        <div class="editorial-footer">
            <div class="footer-brand">STYLE MATE AI</div>
            <div class="footer-tagline">
                Autonomous Western Fashion Intelligence for Men & Women · Capsule Wardrobe Curation.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Footer navigation buttons in horizontal row
    fc1, fc2, fc3, fc4, fc5 = st.columns([1.5, 1, 1, 1, 1.5])
    with fc2:
        if st.button("AI Studio", key="foot_nav_studio", use_container_width=True):
            navigate_to("AI Studio")
    with fc3:
        if st.button("My Wardrobe", key="foot_nav_wardrobe", use_container_width=True):
            navigate_to("My Wardrobe")
    with fc4:
        if st.button("Outfit Ideas", key="foot_nav_outfits", use_container_width=True):
            navigate_to("Outfit Ideas")

    st.markdown(
        """
        <div style="text-align: center; margin-top: 18px; margin-bottom: 10px;">
            <span class="footer-copy">© 2026 Style Mate AI · All rights reserved. High-Fashion Editorial System.</span>
        </div>
        """,
        unsafe_allow_html=True
    )
