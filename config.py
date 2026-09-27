"""
Central configuration for JA Detailing London.

EVERYTHING that describes the business, the services and the imagery lives
here, so nothing is hard-coded across multiple files.

HOW TO SWAP IN REAL JA DETAILING PHOTOS
---------------------------------------
Every image entry has a ``local`` path and a ``url`` (demo stock fallback).
If the ``local`` file exists it is used automatically; otherwise the demo
stock photo is shown. So to use your own photo, simply drop it into the
folder with the file name shown below, e.g.:

    images/services/interior-detailing.jpg

No code changes needed. Once real work photos are in place, set
``DEMO_IMAGERY_NOTICE`` below to False to hide the "demo imagery" labels.

Demo images are free-to-use photos from Unsplash (https://unsplash.com/license).
They are NOT JA Detailing's own work and are clearly labelled as such.
"""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
DATA_DIR = BASE_DIR / "data"

# ---------------------------------------------------------------------------
# Business information (supplied by the client - do not invent extra facts)
# ---------------------------------------------------------------------------
BUSINESS = {
    "name": "JA Detailing London",
    "short_name": "JA Detailing",
    "area": "London & surrounding areas, including Harlow",
    "area_short": "London & Harlow",
    "hours_open": "Monday – Saturday",
    "hours_closed": "Closed Sunday",
    "whatsapp_display": "+44 7493 164083",
    "whatsapp_number": "447493164083",  # international format, no "+" (for wa.me)
    "instagram_url": "https://www.instagram.com/jadetailing.london/",
    "instagram_handle": "@jadetailing.london",
    "facebook_url": "https://www.facebook.com/1240265762493106/",
}

WHATSAPP_URL = f"https://wa.me/{BUSINESS['whatsapp_number']}"

# Logo: images/logo.png (or logo.png in the main folder if uploaded without folders)
LOGO_PATH = IMAGES_DIR / "logo.png" if (IMAGES_DIR / "logo.png").is_file() else BASE_DIR / "logo.png"

SEO = {
    "title": "JA Detailing London | Premium Car Detailing in London & Harlow",
    "description": (
        "JA Detailing London offers professional car detailing services across "
        "London and Harlow - interior and exterior detailing, paint correction, "
        "ceramic coating, machine polishing and full car detailing. Get a quote today."
    ),
}

# Set to False once all demo photos have been replaced with real JA Detailing work.
DEMO_IMAGERY_NOTICE = True


def _unsplash(photo_id: str, width: int = 1200) -> str:
    """Build an optimised Unsplash CDN URL (auto WebP/AVIF, resized, compressed)."""
    return (
        f"https://images.unsplash.com/photo-{photo_id}"
        f"?auto=format&fit=crop&w={width}&q=70"
    )


# ---------------------------------------------------------------------------
# Services (single source of truth for names, copy and images)
# Prices are intentionally NOT listed - the business has not supplied them.
# ---------------------------------------------------------------------------
SERVICES = [
    {
        "name": "Interior Detailing",
        "slug": "interior-detailing",
        "icon": "fa-solid fa-couch",
        "description": (
            "Thorough cleaning of seats, carpets, dashboard, trims and glass - "
            "leaving your cabin fresh, clean and cared for."
        ),
    },
    {
        "name": "Exterior Detailing",
        "slug": "exterior-detailing",
        "icon": "fa-solid fa-car-side",
        "description": (
            "Safe, careful exterior wash and decontamination that lifts road grime "
            "and restores a clean, glossy finish."
        ),
    },
    {
        "name": "Paint Correction",
        "slug": "paint-correction",
        "icon": "fa-solid fa-wand-magic-sparkles",
        "description": (
            "Reduces swirl marks, light scratches and dullness to bring back "
            "clarity and depth to your paintwork."
        ),
    },
    {
        "name": "Ceramic Coating",
        "slug": "ceramic-coating",
        "icon": "fa-solid fa-shield-halved",
        "description": (
            "A protective coating applied to prepared paintwork for a deep gloss "
            "and easier ongoing maintenance."
        ),
    },
    {
        "name": "Deep Cleaning",
        "slug": "deep-cleaning",
        "icon": "fa-solid fa-spray-can-sparkles",
        "description": (
            "An intensive clean for vehicles that need extra attention - reaching "
            "the areas a standard wash misses."
        ),
    },
    {
        "name": "Wheel Detailing",
        "slug": "wheel-detailing",
        "icon": "fa-solid fa-circle-dot",
        "description": (
            "Detailed cleaning of wheels, tyres and arches to remove brake dust and "
            "grime for a sharp, finished look."
        ),
    },
    {
        "name": "Machine Polishing",
        "slug": "machine-polishing",
        "icon": "fa-solid fa-gears",
        "description": (
            "Professional machine polishing to enhance gloss and refine the finish "
            "of your vehicle's paintwork."
        ),
    },
    {
        "name": "Full Car Detailing",
        "slug": "full-car-detailing",
        "icon": "fa-solid fa-star",
        "description": (
            "Our complete inside-and-out treatment for a vehicle that looks and "
            "feels its absolute best."
        ),
    },
]

SERVICE_NAMES = [s["name"] for s in SERVICES]

# ---------------------------------------------------------------------------
# Image configuration - replace demo photos by adding the ``local`` files.
# ---------------------------------------------------------------------------
HERO_IMAGE = {
    "local": IMAGES_DIR / "hero" / "hero.jpg",
    "url": _unsplash("1520340356584-f9917d1eea6f", 1800),
    "alt": "Black performance car photographed in dramatic studio lighting",
}

SERVICE_IMAGES = {
    "Interior Detailing": {
        "local": IMAGES_DIR / "services" / "interior-detailing.jpg",
        "url": _unsplash("1605437241278-c1806d14a4d9"),
        "alt": "Clean black leather car interior with dashboard and steering wheel",
    },
    "Exterior Detailing": {
        "local": IMAGES_DIR / "services" / "exterior-detailing.jpg",
        "url": _unsplash("1633014041037-f5446fb4ce99"),
        "alt": "Grey car covered in snow foam during an exterior detailing wash",
    },
    "Paint Correction": {
        "local": IMAGES_DIR / "services" / "paint-correction.jpg",
        "url": _unsplash("1632823469901-5d2cfff5ba50"),
        "alt": "Detailer using a machine to correct vehicle paintwork",
    },
    "Ceramic Coating": {
        "local": IMAGES_DIR / "services" / "ceramic-coating.jpg",
        "url": _unsplash("1761934658331-2e00b20dc6c6"),
        "alt": "Microfibre cloth resting on glossy red coated paintwork",
    },
    "Deep Cleaning": {
        "local": IMAGES_DIR / "services" / "deep-cleaning.jpg",
        "url": _unsplash("1771491237218-cbd4a707497e"),
        "alt": "Detailer deep cleaning the dashboard of a car",
    },
    "Wheel Detailing": {
        "local": IMAGES_DIR / "services" / "wheel-detailing.jpg",
        "url": _unsplash("1708805282683-50a060eba80f"),
        "alt": "Gloved hand cleaning a car tyre and alloy wheel with a brush",
    },
    "Machine Polishing": {
        "local": IMAGES_DIR / "services" / "machine-polishing.jpg",
        "url": _unsplash("1620584898989-d39f7f9ed1b7"),
        "alt": "Professional dual-action polishing machine ready for use",
    },
    "Full Car Detailing": {
        "local": IMAGES_DIR / "services" / "full-car-detailing.jpg",
        "url": _unsplash("1607860108855-64acf2078ed9"),
        "alt": "Black coupe being rinsed during a full car detail",
    },
}

# Before & After pairs. Replace with real JA Detailing transformations by adding
# images/before_after/<slug>-before.jpg and <slug>-after.jpg
BEFORE_AFTER = [
    {
        "title": "Wheel Transformation",
        "slug": "wheels",
        "before": {
            "local": IMAGES_DIR / "before_after" / "wheels-before.jpg",
            "url": _unsplash("1565689876697-e467b6c54da2", 1000),
            "alt": "Wheel covered in cleaning foam before detailing",
        },
        "after": {
            "local": IMAGES_DIR / "before_after" / "wheels-after.jpg",
            "url": _unsplash("1708805283017-c662be2c7a44", 1000),
            "alt": "Clean, freshly detailed tyre and wheel",
        },
    },
    {
        "title": "Exterior Finish",
        "slug": "exterior",
        "before": {
            "local": IMAGES_DIR / "before_after" / "exterior-before.jpg",
            "url": _unsplash("1608506375591-b90e1f955e4b", 1000),
            "alt": "Sports car covered in wash foam before finishing",
        },
        "after": {
            "local": IMAGES_DIR / "before_after" / "exterior-after.jpg",
            "url": _unsplash("1607860115477-7b3700e055b6", 1000),
            "alt": "Glossy black coupe after exterior detailing",
        },
    },
    {
        "title": "Interior Refresh",
        "slug": "interior",
        "before": {
            "local": IMAGES_DIR / "before_after" / "interior-before.jpg",
            "url": _unsplash("1708805282695-ef186db20192", 1000),
            "alt": "Car interior being worked on during a detail",
        },
        "after": {
            "local": IMAGES_DIR / "before_after" / "interior-after.jpg",
            "url": _unsplash("1605437241278-c1806d14a4d9", 1000),
            "alt": "Clean, detailed car interior",
        },
    },
]

# ---------------------------------------------------------------------------
# Instagram posts supplied by JA Detailing (embedded, never downloaded)
# ---------------------------------------------------------------------------
INSTAGRAM_POSTS = [
    {"url": "https://www.instagram.com/p/DdvcCo5A_ee/", "shortcode": "DdvcCo5A_ee"},
    {"url": "https://www.instagram.com/p/Ddtr_UMRq2V/", "shortcode": "Ddtr_UMRq2V"},
]

# ---------------------------------------------------------------------------
# Quote form options
# ---------------------------------------------------------------------------
PREFERRED_TIMES = ["Morning", "Midday", "Afternoon", "Any time / flexible"]
