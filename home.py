"""
JA Detailing London - public website (single scrolling page).

Sections: Nav · Hero · Highlights · Services · Before & After · Latest Work
(Instagram) · Get a Quote · Contact · Footer · Floating WhatsApp.

No client/business data is ever read here - the only database action is
saving a new website enquiry.
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta

import streamlit as st
import streamlit.components.v1 as components

import services as svc
from auth import is_authenticated
from config import (
    BEFORE_AFTER,
    BUSINESS,
    DEMO_IMAGERY_NOTICE,
    HERO_IMAGE,
    INSTAGRAM_POSTS,
    PREFERRED_TIMES,
    SEO,
    SERVICE_IMAGES,
    SERVICES,
)
from models import EnquiryInput, ValidationError
from styles import PUBLIC_CSS
from utils import (
    esc,
    logo_url,
    quote_whatsapp_message,
    resolve_image,
    responsive_image,
    service_whatsapp_message,
    today_london,
    whatsapp_link,
)

log = logging.getLogger("ja_detailing.public")

try:  # images are served as cacheable files when static serving is enabled (see .streamlit/config.toml)
    STATIC_OK = bool(st.get_option("server.enableStaticServing"))
except Exception:
    STATIC_OK = False

MAX_ENQUIRIES_PER_SESSION = 5
GENERAL_WA_MESSAGE = f"Hello {BUSINESS['name']}, I'd like to enquire about your detailing services."


# ---------------------------------------------------------------------------
# Cached asset helpers (images are optimised once, then reused)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def _logo() -> str | None:
    return logo_url(400, STATIC_OK)


@st.cache_data(show_spinner=False, ttl=3600)
def _img(key: str, group: str, max_width: int = 1000) -> str:
    if group == "service":
        return resolve_image(SERVICE_IMAGES.get(key), max_width, STATIC_OK)
    if group.startswith("ba-"):
        pair = next((p for p in BEFORE_AFTER if p["slug"] == key), None)
        return resolve_image(pair[group[3:]] if pair else None, max_width, STATIC_OK)
    return ""


@st.cache_data(show_spinner=False, ttl=3600)
def _hero() -> tuple[str, str]:
    return responsive_image(HERO_IMAGE, (640, 1024, 1600), STATIC_OK)


def brand_html() -> str:
    """Logo (if present) + business name - used in header and footer."""
    uri = _logo()
    img = f'<img src="{uri}" alt="{esc(BUSINESS["name"])} logo">' if uri else ""
    return (f'{img}<span class="ja-brand-name"><b>JA <em>Detailing</em></b>'
            f'<small>London</small></span>')


def social_icons(include_whatsapp: bool = True) -> str:
    """Round Instagram / Facebook (/ WhatsApp) brand icons."""
    wa = (f'<a class="wa" href="{whatsapp_link(GENERAL_WA_MESSAGE)}" target="_blank" rel="noopener" '
          f'aria-label="WhatsApp" title="WhatsApp"><i class="fa-brands fa-whatsapp" aria-hidden="true"></i></a>'
          if include_whatsapp else "")
    return (f'<div class="soc">'
            f'<a class="ig" href="{BUSINESS["instagram_url"]}" target="_blank" rel="noopener" aria-label="Instagram" '
            f'title="Instagram"><i class="fa-brands fa-instagram" aria-hidden="true"></i></a>'
            f'<a class="fb" href="{BUSINESS["facebook_url"]}" target="_blank" rel="noopener" aria-label="Facebook" '
            f'title="Facebook"><i class="fa-brands fa-facebook-f" aria-hidden="true"></i></a>{wa}</div>')


def section(fn):
    """Render a section; if anything fails, log it and keep the page alive."""
    try:
        fn()
    except Exception as exc:  # pragma: no cover - defensive
        # Let Streamlit's own control-flow signals (rerun/stop) pass through.
        if type(exc).__name__ in {"RerunException", "StopException"}:
            raise
        log.exception("Section %s failed", fn.__name__)


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
def render_seo() -> None:
    """Set <html lang> and meta description (Streamlit has no native API for these)."""
    desc = json.dumps(SEO["description"])
    components.html(
        f"""<script>
        try {{
          const d = window.parent.document;
          d.documentElement.lang = "en-GB";
          let m = d.querySelector('meta[name="description"]');
          if (!m) {{ m = d.createElement('meta'); m.name = 'description'; d.head.appendChild(m); }}
          m.content = {desc};
        }} catch (e) {{}}
        </script>""",
        height=0,
    )


def render_nav() -> None:
    st.html(f"""
    <header class="ja-nav" role="banner">
      <div class="ja-nav-inner">
        <a class="ja-brand" href="#top" aria-label="{esc(BUSINESS['name'])} home">{brand_html()}</a>
        <nav class="ja-links" aria-label="Main">
          <a href="#top">Home</a>
          <a href="#services">Services</a>
          <a href="#before-after">Before &amp; After</a>
          <a href="#latest-work">Our Work</a>
          <a href="#contact">Contact</a>
        </nav>
        <div class="ja-nav-cta">
          <a class="btn btn-ghost btn-sm" href="{whatsapp_link(GENERAL_WA_MESSAGE)}" target="_blank" rel="noopener">
            <i class="fa-brands fa-whatsapp" aria-hidden="true"></i> WhatsApp</a>
          <a class="btn btn-primary btn-sm" href="#get-a-quote">Get a Quote</a>
        </div>
      </div>
    </header>
    """)


def render_hero() -> None:
    hero_logo = _logo()
    logo_block = (f'<img class="ja-hero-logo" src="{hero_logo}" alt="{esc(BUSINESS["name"])} logo">'
                  if hero_logo else "")
    src, srcset = _hero()
    srcset_attr = f'srcset="{srcset}" sizes="100vw"' if srcset else ""
    st.html(f"""
    <section id="top" class="ja-hero">
      <img class="ja-hero-bg" src="{src}" {srcset_attr} alt="{esc(HERO_IMAGE['alt'])}"
           fetchpriority="high" decoding="async" width="1600" height="900">
      <div class="ja-hero-inner">
        <div class="ja-hero-content">
          {logo_block}
          <span class="eyebrow">{esc(BUSINESS['name'])}</span>
          <h1>Premium Car Detailing <span class="hl">Across London &amp; Harlow</span></h1>
          <p class="lead">Meticulous interior and exterior detailing, paint correction and ceramic
          coating - carried out with care for drivers who want their car to look its very best.</p>
          <div class="ja-hero-ctas">
            <a class="btn btn-primary" href="#get-a-quote"><i class="fa-solid fa-file-signature" aria-hidden="true"></i> Get a Quote</a>
            <a class="btn btn-wa" href="{whatsapp_link(GENERAL_WA_MESSAGE)}" target="_blank" rel="noopener">
              <i class="fa-brands fa-whatsapp" aria-hidden="true"></i> WhatsApp Us</a>
          </div>
          <div class="ja-hero-meta">
            <span class="chip"><i class="fa-solid fa-location-dot" aria-hidden="true"></i> {esc(BUSINESS['area'])}</span>
            <span class="chip"><i class="fa-regular fa-clock" aria-hidden="true"></i> Open {esc(BUSINESS['hours_open'])}</span>
          </div>
        </div>
      </div>
    </section>
    <div class="ja-strip">
      <div><i class="fa-solid fa-car" aria-hidden="true"></i><span><b>8 Detailing Services</b>Interior, exterior &amp; paintwork</span></div>
      <div><i class="fa-solid fa-map-location-dot" aria-hidden="true"></i><span><b>London &amp; Harlow</b>And surrounding areas</span></div>
      <div><i class="fa-regular fa-calendar-check" aria-hidden="true"></i><span><b>Monday – Saturday</b>Closed Sundays</span></div>
      <div><i class="fa-brands fa-whatsapp" aria-hidden="true"></i><span><b>Quick Quotes</b>Message us on WhatsApp</span></div>
    </div>
    """)


def render_services() -> None:
    cards = []
    for i, s in enumerate(SERVICES):
        img = SERVICE_IMAGES.get(s["name"], {})
        src = _img(s["name"], "service", 720)
        media = (f'<img src="{src}" alt="{esc(img.get("alt", s["name"]))}" loading="lazy" decoding="async" '
                 f'width="900" height="675">' if src else "")
        cards.append(f"""
        <article class="svc-card" style="animation-delay:{i * 60}ms">
          <div class="svc-media">{media}<span class="svc-icon"><i class="{s['icon']}" aria-hidden="true"></i></span></div>
          <div class="svc-body">
            <h3>{esc(s['name'])}</h3>
            <p>{esc(s['description'])}</p>
            <div class="svc-price">Contact us for a quote</div>
            <div class="svc-actions">
              <a class="btn btn-ghost btn-sm" href="#get-a-quote" aria-label="Get a quote for {esc(s['name'])}">Get a Quote</a>
              <a class="btn btn-wa btn-sm" href="{whatsapp_link(service_whatsapp_message(s['name']))}" target="_blank"
                 rel="noopener" aria-label="Ask about {esc(s['name'])} on WhatsApp"><i class="fa-brands fa-whatsapp" aria-hidden="true"></i></a>
            </div>
          </div>
        </article>""")
    note = ('<div class="demo-note"><i class="fa-regular fa-image" aria-hidden="true"></i>'
            'Illustrative stock photography</div>' if DEMO_IMAGERY_NOTICE else "")
    st.html(f"""
    <section id="services" class="section" aria-labelledby="services-h">
      <div class="section-head">
        <span class="eyebrow">What we do</span>
        <h2 id="services-h">Detailing Services</h2>
        <p>From a refreshed interior to fully corrected and protected paintwork, every service is
        tailored to your vehicle. Tell us about your car and we'll come back with a quote.</p>
        {note}
      </div>
      <div class="svc-grid">{''.join(cards)}</div>
    </section>
    """)


BA_TEMPLATE = """
<!doctype html><html><head><meta charset="utf-8"><style>
  html,body{{margin:0;background:transparent;font-family:Inter,system-ui,sans-serif}}
  .ba{{position:relative;width:100%;height:{h}px;border-radius:16px;overflow:hidden;background:#15181d;
       border:1px solid rgba(255,255,255,.08);user-select:none;touch-action:pan-y}}
  .ba img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;pointer-events:none}}
  .ba .before{{clip-path:inset(0 50% 0 0)}}
  .ba .line{{position:absolute;top:0;bottom:0;left:50%;width:2px;background:#fff;transform:translateX(-1px);
       box-shadow:0 0 12px rgba(0,0,0,.5)}}
  .ba .knob{{position:absolute;top:50%;left:50%;width:44px;height:44px;border-radius:50%;background:#fff;
       transform:translate(-50%,-50%);display:grid;place-items:center;box-shadow:0 6px 20px rgba(0,0,0,.45);
       font-weight:700;color:#0A0B0D;font-size:15px}}
  .tag{{position:absolute;top:12px;padding:5px 11px;border-radius:999px;font-size:11px;letter-spacing:.14em;
       text-transform:uppercase;font-weight:700;background:rgba(10,11,13,.75);color:#fff;border:1px solid rgba(255,255,255,.2)}}
  .tb{{left:12px}} .ta{{right:12px}}
  .demo{{position:absolute;left:12px;bottom:12px;font-size:10.5px;color:#d1d5db;background:rgba(10,11,13,.7);
        padding:4px 9px;border-radius:999px}}
  input{{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:ew-resize;margin:0}}
</style></head><body>
<div class="ba" id="ba">
  <img src="{after}" alt="{after_alt}">
  <img class="before" id="b" src="{before}" alt="{before_alt}">
  <div class="line" id="l"></div><div class="knob" id="k">&#8596;</div>
  <span class="tag tb">Before</span><span class="tag ta">After</span>
  {demo}
  <input type="range" min="0" max="100" value="50" aria-label="Drag to compare before and after: {title}">
</div>
<script>
  const r=document.querySelector('input'),b=document.getElementById('b'),l=document.getElementById('l'),k=document.getElementById('k');
  function u(v){{b.style.clipPath='inset(0 '+(100-v)+'% 0 0)';l.style.left=v+'%';k.style.left=v+'%';}}
  r.addEventListener('input',e=>u(e.target.value));
</script></body></html>
"""


def render_before_after() -> None:
    st.html(f"""
    <section id="before-after" class="section" aria-labelledby="ba-h" style="padding-bottom:0">
      <div class="section-head">
        <span class="eyebrow">Transformations</span>
        <h2 id="ba-h">Before &amp; After</h2>
        <p>Drag the slider to compare. {'These examples use illustrative stock photography - '
        'real JA Detailing transformations are on our Instagram.' if DEMO_IMAGERY_NOTICE else ''}</p>
      </div>
    </section>
    """)
    cols = st.columns(len(BEFORE_AFTER), gap="medium")
    for col, pair in zip(cols, BEFORE_AFTER):
        with col:
            try:
                html_doc = BA_TEMPLATE.format(
                    h=300,
                    before=_img(pair["slug"], "ba-before"),
                    after=_img(pair["slug"], "ba-after"),
                    before_alt=esc(pair["before"]["alt"]),
                    after_alt=esc(pair["after"]["alt"]),
                    title=esc(pair["title"]),
                    demo='<span class="demo">Demo imagery</span>' if DEMO_IMAGERY_NOTICE else "",
                )
                components.html(html_doc, height=304)
            except Exception:
                log.exception("Before/after render failed")
                st.caption("Comparison unavailable.")
            st.html(f'<p class="ba-title">{esc(pair["title"])}</p>')


def render_instagram() -> None:
    st.html(f"""
    <section id="latest-work" class="section" aria-labelledby="work-h" style="padding-bottom:0">
      <div class="section-head center">
        <span class="eyebrow">Instagram</span>
        <h2 id="work-h">See Our Latest Work</h2>
        <p>Recent details straight from our Instagram. Follow
        <a href="{BUSINESS['instagram_url']}" target="_blank" rel="noopener">{esc(BUSINESS['instagram_handle'])}</a>
        for more.</p>
      </div>
    </section>
    """)
    cols = st.columns(len(INSTAGRAM_POSTS), gap="medium")
    for col, post in zip(cols, INSTAGRAM_POSTS):
        with col:
            # The fallback card is ALWAYS shown, so the section still works if the
            # embed is blocked (privacy extensions, Instagram outages, etc.).
            st.html(f"""
            <div class="ig-card">
              <div class="ig-head">
                <span class="ig-avatar"><i class="fa-brands fa-instagram" aria-hidden="true"></i></span>
                <span><b>{esc(BUSINESS['instagram_handle'])}</b><span>{esc(BUSINESS['name'])}</span></span>
              </div>
              <a class="btn btn-ig btn-sm" href="{esc(post['url'])}" target="_blank" rel="noopener">
                <i class="fa-brands fa-instagram" aria-hidden="true"></i> View on Instagram</a>
              <p class="ig-fallback">If the post doesn't load below, tap “View on Instagram”.</p>
            </div>
            """)
            try:
                components.html(
                    f"""<div style="display:flex;justify-content:center;background:transparent">
                    <iframe src="https://www.instagram.com/p/{esc(post['shortcode'])}/embed/captioned/"
                      title="JA Detailing London Instagram post" loading="lazy"
                      style="width:100%;max-width:480px;height:640px;border:0;border-radius:14px;background:#fff"
                      allowtransparency="true" scrolling="no"></iframe></div>""",
                    height=650,
                )
            except Exception:
                log.exception("Instagram embed failed")

    st.html(f"""
    <div class="social-row" style="margin-top:14px">
      <a class="btn btn-ig" href="{BUSINESS['instagram_url']}" target="_blank" rel="noopener"><i class="fa-brands fa-instagram" aria-hidden="true"></i> Instagram</a>
      <a class="btn btn-fb" href="{BUSINESS['facebook_url']}" target="_blank" rel="noopener"><i class="fa-brands fa-facebook-f" aria-hidden="true"></i> Facebook</a>
      <a class="btn btn-wa" href="{whatsapp_link(GENERAL_WA_MESSAGE)}" target="_blank" rel="noopener"><i class="fa-brands fa-whatsapp" aria-hidden="true"></i> WhatsApp</a>
    </div>
    """)


def render_quote() -> None:
    st.html("""
    <section id="get-a-quote" class="section" aria-labelledby="quote-h" style="padding-bottom:0">
      <div class="section-head">
        <span class="eyebrow">Enquiries</span>
        <h2 id="quote-h">Get a Quote</h2>
        <p>Tell us about your vehicle and what you're looking for. It only takes a minute.</p>
      </div>
    </section>
    """)
    left, right = st.columns([5, 7], gap="large")
    with left:
        st.html(f"""
        <div class="quote-panel">
          <h3>How it works</h3>
          <p>Every car is different, so we quote individually rather than using fixed prices.</p>
          <ol class="quote-steps">
            <li><b>1</b><span>Fill in the form with your vehicle and the service you need.</span></li>
            <li><b>2</b><span>Send your enquiry to us on WhatsApp with one tap - it's pre-filled for you.</span></li>
            <li><b>3</b><span>We'll get back to you to confirm your quote and a time that suits you.</span></li>
          </ol>
          <div class="meta"><i class="fa-regular fa-clock" aria-hidden="true"></i><span>Open {esc(BUSINESS['hours_open'])} · {esc(BUSINESS['hours_closed'])}</span></div>
          <div class="meta" style="margin-bottom:22px"><i class="fa-solid fa-location-dot" aria-hidden="true"></i><span>{esc(BUSINESS['area'])}</span></div>
          <a class="btn btn-wa" href="{whatsapp_link(GENERAL_WA_MESSAGE)}" target="_blank" rel="noopener">
            <i class="fa-brands fa-whatsapp" aria-hidden="true"></i> Get a Quote on WhatsApp</a>
        </div>
        """)
    with right:
        render_quote_form()


def render_quote_form() -> None:
    done = st.session_state.get("quote_success")
    if done:
        st.success(f"Thank you, {done['name']} - your enquiry has been received (ref {done['reference']}).")
        st.markdown(
            "For the fastest response, **send your enquiry to us on WhatsApp** - "
            "your details are already filled in, just press send."
        )
        st.link_button("Send enquiry on WhatsApp", done["wa_url"], type="primary",
                       icon=":material/chat:", width="stretch")
        if st.button("Submit another enquiry", width="stretch"):
            del st.session_state["quote_success"]
            st.rerun()
        return

    try:
        services = svc.list_service_names()
    except Exception:
        log.exception("Could not load services list")
        services = [s["name"] for s in SERVICES]
    min_day = today_london()
    default_day = min_day + timedelta(days=1)
    if default_day.weekday() == 6:
        default_day += timedelta(days=1)

    with st.form("quote_form", clear_on_submit=False, border=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Your name *", max_chars=120, autocomplete="name")
        phone = c2.text_input("WhatsApp / phone number *", max_chars=30, placeholder="07123 456789",
                              autocomplete="tel")
        email = st.text_input("Email (optional)", max_chars=160, autocomplete="email")
        c3, c4, c5 = st.columns(3)
        make = c3.text_input("Vehicle make *", max_chars=60, placeholder="e.g. BMW")
        model = c4.text_input("Vehicle model *", max_chars=60, placeholder="e.g. 3 Series")
        reg = c5.text_input("Registration (optional)", max_chars=12, placeholder="AB12 CDE")
        service = st.selectbox("Service required *", services, index=None, placeholder="Choose a service")
        c6, c7 = st.columns(2)
        pdate = c6.date_input("Preferred date *", value=default_day, min_value=min_day,
                              max_value=min_day + timedelta(days=365), format="DD/MM/YYYY",
                              help="We're open Monday to Saturday.")
        ptime = c7.selectbox("Preferred time", PREFERRED_TIMES, index=len(PREFERRED_TIMES) - 1)
        notes = st.text_area("Additional notes", max_chars=1500, height=100,
                             placeholder="Anything we should know - condition, specific concerns, location…")
        submitted = st.form_submit_button("Request my quote", type="primary")

    if submitted:
        count = st.session_state.get("quote_count", 0)
        if count >= MAX_ENQUIRIES_PER_SESSION:
            st.warning("You've sent several enquiries already - please message us on WhatsApp instead.")
            return
        data = EnquiryInput(name=name, phone=phone, email=email, vehicle_make=make, vehicle_model=model,
                            registration=reg, service=service or "", preferred_date=pdate,
                            preferred_time=ptime, notes=notes)
        try:
            enquiry_id = svc.create_enquiry(data)
        except ValidationError as err:
            st.error("Please check the following:\n\n" + "\n".join(f"- {m}" for m in err.errors))
            return
        except Exception:
            # Never expose internal errors to the public - offer WhatsApp instead.
            log.exception("Saving enquiry failed")
            st.error("Sorry, we couldn't save your enquiry just now. Please send it to us on WhatsApp instead.")
            st.link_button("Send enquiry on WhatsApp", whatsapp_link(quote_whatsapp_message(data.__dict__)),
                           type="primary", width="stretch")
            return
        reference = svc.enquiry_code(enquiry_id)
        payload = dict(data.__dict__, reference=reference, registration=reg.upper().strip())
        st.session_state["quote_count"] = count + 1
        st.session_state["quote_success"] = {
            "name": name.strip(),
            "reference": reference,
            "wa_url": whatsapp_link(quote_whatsapp_message(payload)),
        }
        st.rerun()


def render_contact() -> None:
    st.html(f"""
    <section id="contact" class="section" aria-labelledby="contact-h">
      <div class="section-head">
        <span class="eyebrow">Contact</span>
        <h2 id="contact-h">Get In Touch</h2>
        <p>The quickest way to reach us is WhatsApp. We cover {esc(BUSINESS['area'])}.</p>
      </div>
      <div class="contact-grid">
        <a class="contact-card" href="{whatsapp_link(GENERAL_WA_MESSAGE)}" target="_blank" rel="noopener">
          <i class="fa-brands fa-whatsapp" aria-hidden="true"></i><h3>WhatsApp</h3><p>{esc(BUSINESS['whatsapp_display'])}</p></a>
        <div class="contact-card">
          <i class="fa-solid fa-location-dot" aria-hidden="true"></i><h3>Service Area</h3><p>{esc(BUSINESS['area'])}</p></div>
        <div class="contact-card">
          <i class="fa-regular fa-clock" aria-hidden="true"></i><h3>Opening</h3>
          <p>{esc(BUSINESS['hours_open'])}<br><span style="color:var(--muted)">{esc(BUSINESS['hours_closed'])}</span></p></div>
        <div class="contact-card">
          <i class="fa-solid fa-hashtag" aria-hidden="true"></i><h3>Follow Us</h3>
          {social_icons(include_whatsapp=False)}</div>
      </div>
    </section>
    """)


def render_footer() -> None:
    year = today_london().year
    svc_links = "".join(f'<li><a href="#services">{esc(s["name"])}</a></li>' for s in SERVICES)
    st.html(f"""
    <footer class="ja-footer" role="contentinfo">
      <div class="ja-footer-inner">
        <div>
          <a class="ja-brand" href="#top" aria-label="Back to top">{brand_html()}</a>
          <p>{esc(BUSINESS['name'])} provides professional car detailing across London and surrounding
          areas, including Harlow - from interior cleans to paint correction and ceramic coating.</p>
          {social_icons()}
        </div>
        <div><h4>Services</h4><ul>{svc_links}</ul></div>
        <div><h4>Contact</h4><ul>
          <li><a href="{whatsapp_link()}" target="_blank" rel="noopener">WhatsApp {esc(BUSINESS['whatsapp_display'])}</a></li>
          <li><a href="#get-a-quote">Get a Quote</a></li></ul></div>
        <div><h4>Opening</h4><ul>
          <li>{esc(BUSINESS['hours_open'])}</li><li>{esc(BUSINESS['hours_closed'])}</li></ul>
          <h4 style="margin-top:22px">Service Area</h4><p>{esc(BUSINESS['area'])}</p></div>
      </div>
      <div class="ja-copy"><span>© {year} {esc(BUSINESS['name'])}. All rights reserved.</span>
        <span>Car detailing in London &amp; Harlow</span></div>
    </footer>
    <div class="social-float" aria-label="Contact and follow JA Detailing London">
      <a class="sf-ig" href="{BUSINESS['instagram_url']}" target="_blank" rel="noopener" aria-label="Instagram"
         title="Instagram"><i class="fa-brands fa-instagram" aria-hidden="true"></i></a>
      <a class="sf-fb" href="{BUSINESS['facebook_url']}" target="_blank" rel="noopener" aria-label="Facebook"
         title="Facebook"><i class="fa-brands fa-facebook-f" aria-hidden="true"></i></a>
      <a class="sf-wa" href="{whatsapp_link(GENERAL_WA_MESSAGE)}" target="_blank" rel="noopener"
         aria-label="WhatsApp Us" title="WhatsApp Us"><i class="fa-brands fa-whatsapp" aria-hidden="true"></i></a>
    </div>
    """)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
# IMPORTANT: this st.html call must contain ONLY a <style> block - mixing other
# tags in makes Streamlit drop the styles and the site appears unstyled.
st.html(f"<style>{PUBLIC_CSS}</style>")
if is_authenticated():
    # Admin previewing the website: keep the admin sidebar reachable.
    st.html("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],"
            "[data-testid='stHeader']{display:flex !important}</style>")
section(render_seo)
section(render_nav)
section(render_hero)
section(render_services)
section(render_before_after)
section(render_instagram)
section(render_quote)
section(render_contact)
section(render_footer)
