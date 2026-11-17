# Style Mate AI · Editorial Fashion Intelligence

**Style Mate AI** is a luxury editorial fashion recognition and wardrobe intelligence platform. It combines deep learning computer vision (CNN + KNN ensemble and MediaPipe pose estimation) with a curated, high-resolution master fashion catalog and a personalized digital wardrobe.

---

## 🌟 Key Architecture & Features

### 1. Unified Master HD Fashion Catalog (746 Products)
- **100% Genuine High-Resolution Imagery**:
  - **720 Original Dataset Products**: 100% verified authentic HD assets (`1080×1440` to `1476×1968` px sourced directly from Myntra master CDN, and `900×1200` px from dataset parquets). Zero artificial upscaling.
  - **26 Curated Luxury Brand Products**: Curated editorial fashion pieces with verified brand names, prices, and dimensions.
- **7-Category Fashion Taxonomy**:
  - **Tops**: Shirts, T-shirts, Tops, Blouses, Kurtas, Sweatshirts, Sweaters, Hoodies
  - **Bottoms**: Trousers, Jeans, Shorts, Track Pants, Skirts
  - **Dresses**: Dresses, Gowns, Jumpsuits
  - **Outerwear**: Jackets, Coats, Blazers, Cardigans
  - **Shoes**: Casual Shoes, Sports Shoes, Formal Shoes, Heels, Flats, Sneakers, Sandals, Boots
  - **Bags**: Handbags, Backpacks, Tote Bags, Clutches
  - **Accessories**: Watches, Belts, Sunglasses, Jewellery, Scarves, Hats
- **Multi-Attribute Filter Engine**: Instant search by brand/title/color, category/subcategory selectors, gender filters, occasion filters, and HD toggles.
- **Product Inspector**: Detail modal with image zoom, product attributes, direct product link, and **Similar Styles** carousel.

### 2. AI Fashion Studio (Recognition & Pose Analysis)
- **Single Garment Classification**: Predicts garment type, dominant HSV color, circular hue, color hex/RGB values, and occasion heuristics.
- **Full-Body Pose Analysis**: MediaPipe pose detection automatically identifies body landmarks and extracts upper/lower garment crops for independent classification.
- **AI Recommendations Synergy**: Bridges predicted classes directly to matching HD products in the catalog with direct "Add to Wardrobe" actions.
- **Transparent Fallbacks**: Explains the 18 trained garment classes and suggests alternatives for untrained items.

### 3. Personal Digital Wardrobe (Strict Isolation)
- User wardrobe items remain strictly segregated from catalog and dataset products.
- Supports garment inspection, editing, slot assignment (`top`, `bottom`, `outer`, `dress`, `shoes`, `bag`, `accessory`), and deletion.

### 4. Admin Product Management System
- **Secure Authentication**: Configured via environment variables (`STYLEMATE_ADMIN_PASSWORD`) or Streamlit secrets (`.streamlit/secrets.toml`). Zero hardcoded credentials in application source code. Denies access by default if unconfigured.
- **Single Product Upload**: Uploads custom garments with PIL format validation and automatic slot determination.
- **Bulk CSV Import**: Import batches of products with column validation and a downloadable template.
- **Product Management Table**: Searchable, paginated table with inline editing and delete confirmation safety gates.

---

## 🤖 AI Model Specifications & Audit

The underlying AI engine utilizes an unmodified CNN feature extractor coupled with a K-Nearest Neighbors (KNN) classifier and scaler:
- **Trained Model Files (100% Byte-for-Byte Identical to Original)**:
  - `models/stylemate_model.keras` (`23,546,950` bytes, sha256: `5132a4a1...`)
  - `models/knn.pkl` (`85,900,200` bytes, sha256: `fe0de781...`)
  - `models/scaler.pkl` (`31,335` bytes, sha256: `d02f5f7e...`)
  - `models/labels.json` (`1,183` bytes, sha256: `68336cda...`)
- **Compatibility Adapter**: Uses a non-invasive in-memory monkey-patch for Keras deserialization; **zero model weights were altered**.
- **Empirical Audit (180 samples across 18 classes)**:
  - **Top-1 Accuracy**: **85.56%**
  - **Top-3 Accuracy**: **98.89%**
  - **Slot Accuracy**: **97.22%**
  - **Mean Confidence**: **0.798**
- **18 Trained Classes**: `Tshirts`, `Shirts`, `Tops`, `Sweatshirts`, `Sweaters`, `Jackets`, `Kurtas`, `Jeans`, `Trousers`, `Track Pants`, `Shorts`, `Dresses`, `Casual Shoes`, `Sports Shoes`, `Formal Shoes`, `Heels`, `Flats`, `Handbags`.
- **Known Model Limitations**: The model was not trained on accessories (watches, sunglasses, belts, jewellery). The UI reports this transparently to the user.

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- macOS, Linux, or Windows with Python 3.9+ installed.

### 2. Environment Setup
```bash
cd /Users/aen./Downloads/Friend_file/stylemate_redesign

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (if setting up fresh)
pip install -r requirements.txt
```

### 3. Configure Admin Password (Optional)
To enable the Admin Portal, set the environment variable:
```bash
export STYLEMATE_ADMIN_PASSWORD="YourSecurePasswordHere"
```
Or add to `.streamlit/secrets.toml`:
```toml
admin_password = "YourSecurePasswordHere"
```
*(If unset, the application runs normally, but the Admin portal safely denies login with a configuration prompt).*

### 4. Launch Application
```bash
streamlit run app.py --server.port 8502 --server.headless true
```
Open your browser to: **`http://localhost:8502`**

---

## 📂 Project Structure

```text
stylemate_redesign/
├── app.py                         # Application entrypoint & view dispatcher
├── engine.py                      # Original core AI engine (with runtime Keras patch)
├── requirements.txt               # Dependencies
├── catalog/                       # Master catalog & image datasets
│   ├── catalog.csv                # Original 720 product IDs & metadata
│   ├── catalog_index.csv          # Pre-computed slot/color index
│   ├── master_products.json       # Unified 746-product master database
│   ├── images/                    # Preserved original 60x80 thumbnail assets
│   ├── images_hd/                 # Genuine 1080x1440 & 900x1200 HD images (720 items)
│   └── images_custom/             # User & Admin uploaded product assets
├── curated_catalog/               # 26 Curated Luxury Brand Collection
│   ├── curated_products.json      # Verified metadata & prices
│   └── images/                    # High-resolution product images
├── models/                        # Unmodified AI model weights
│   ├── stylemate_model.keras
│   ├── knn.pkl
│   ├── scaler.pkl
│   └── labels.json
├── services/                      # Decoupled service layer
│   ├── ai_service.py              # AI inference & wardrobe adapter
│   ├── master_catalog_service.py  # Master catalog query & Admin CRUD
│   ├── curated_catalog_service.py # Curated brand queries
│   └── recommendation_service.py  # AI ↔ HD Catalog recommendation bridge
└── ui/                            # Editorial presentation layer
    ├── styles.py                  # Luxury editorial typography & design system
    ├── components/
    │   └── navigation.py          # Top horizontal navigation bar
    └── views/
        ├── home.py                # Luxury editorial homepage
        ├── ai_studio.py           # Single & multi-garment AI Studio
        ├── wardrobe_view.py       # Personal Digital Wardrobe
        ├── master_catalog_view.py # Master HD Catalog browser & inspector
        ├── curated_brands_view.py # Curated Brand Collection
        ├── admin_product_view.py  # Auth-gated Admin portal
        └── placeholder.py         # Outfit Ideas generator placeholder
```
