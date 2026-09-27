"""
All CSS for the app lives here: one stylesheet for the public website, one
for the admin system and one for the login page. Injected with ``st.html``.

THEME
-----
Colours and fonts are CSS variables in ``BASE`` below. To re-colour the whole
site, change ``--accent`` / ``--accent-2`` (and ``primaryColor`` in
.streamlit/config.toml).

Fonts: "Bebas Neue" for headings (bold, automotive) and "Poppins" for body text.
"""

FONT_IMPORTS = """
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Poppins:wght@300;400;500;600;700&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css');
"""

BASE = """
:root {
  /* JA Detailing palette - 70% dark, 20% white/grey, 10% electric blue */
  --bg: #080A0D;          /* deep luxury black */
  --bg-2: #11151A;        /* dark graphite */
  --card: #171C23;        /* card background */
  --card-2: #1C222A;
  --line: #252B33;        /* borders */
  --line-2: #323A45;
  --text: #FFFFFF;
  --muted: #A7ADB7;       /* secondary text */
  --accent: #1677FF;      /* electric blue */
  --accent-2: #3D8BFF;    /* blue hover */
  --accent-glow: rgba(22,119,255,.35);
  --accent-soft: rgba(22,119,255,.10);
  --success: #22C55E;
  --wa: #25D366;
  --ig: radial-gradient(circle at 30% 107%, #fdf497 0%, #fdf497 5%, #fd5949 45%, #d6249f 60%, #285AEB 90%);
  --fb: #1877F2;
  --radius: 12px;
  --shadow: 0 24px 50px -24px rgba(0,0,0,.85);
  --font: 'Poppins', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --display: 'Bebas Neue', 'Poppins', Impact, sans-serif;
}
html, body, [data-testid="stAppViewContainer"], .stApp {
  background: var(--bg) !important;
  color: var(--text);
  font-family: var(--font);
}
a { color: inherit; }
:focus-visible { outline: 2px solid var(--accent-2) !important; outline-offset: 3px; }
"""

PUBLIC_CSS = FONT_IMPORTS + BASE + """
/* ================= Streamlit chrome & layout ================= */
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stStatusWidget"], footer, #MainMenu { display: none !important; }

[data-testid="stMainBlockContainer"], .block-container {
  max-width: 1240px !important;
  padding: 0 24px 40px !important;
}
[data-testid="stVerticalBlock"] { gap: 1rem; }
.stHtml, [data-testid="stHtml"] { width: 100%; }
/* All Streamlit column rows: equal-height columns */
[data-testid="stHorizontalBlock"] { align-items: stretch !important; gap: 24px !important; }

@keyframes rise { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
@keyframes shine { from { background-position: -200% 0; } to { background-position: 200% 0; } }

/* ================= Header ================= */
.ja-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 999;
  background: rgba(8,10,13,.88);
  backdrop-filter: saturate(160%) blur(14px); -webkit-backdrop-filter: saturate(160%) blur(14px);
  border-bottom: 1px solid var(--line);
}
.ja-nav::after { content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent) 20%, var(--accent) 80%, transparent); }
.ja-nav-inner {
  max-width: 1240px; margin: 0 auto; height: 76px; padding: 0 24px;
  display: flex; align-items: center; justify-content: space-between; gap: 20px;
}
.ja-brand { display: flex; align-items: center; gap: 14px; text-decoration: none !important; min-width: 0; }
.ja-brand img { height: 48px; width: auto; object-fit: contain; display: block; border-radius: 4px; }
.ja-brand-name { display: flex; flex-direction: column; line-height: 1; white-space: nowrap; }
.ja-brand-name b { font-family: var(--display); font-weight: 400; font-size: 1.75rem; letter-spacing: .06em; color: #fff; }
.ja-brand-name b em { font-style: normal; color: var(--accent-2); }
.ja-brand-name small { font-size: .62rem; letter-spacing: .42em; color: var(--muted); margin-top: 4px; font-weight: 500; }
.ja-links { display: flex; align-items: center; gap: 30px; }
.ja-links a { text-decoration: none !important; color: #D5D9E0; font-size: .84rem; font-weight: 500;
  letter-spacing: .1em; text-transform: uppercase; position: relative; padding: 6px 0; transition: color .2s; }
.ja-links a::after { content: ""; position: absolute; left: 0; right: 100%; bottom: 0; height: 2px;
  background: var(--accent); transition: right .25s ease; }
.ja-links a:hover { color: #fff; }
.ja-links a:hover::after { right: 0; }
.ja-nav-cta { display: flex; gap: 10px; align-items: center; }

/* ================= Buttons ================= */
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 10px;
  min-height: 50px; padding: 0 26px; border-radius: 8px;
  font-family: var(--font); font-weight: 600; font-size: .86rem; letter-spacing: .08em; text-transform: uppercase;
  text-decoration: none !important; border: 1px solid transparent; white-space: nowrap; cursor: pointer;
  transition: transform .18s ease, box-shadow .2s ease, background .2s ease, border-color .2s ease;
}
.btn:hover { transform: translateY(-2px); }
.btn i { font-size: 1.15em; }
.btn-primary { background: var(--accent); color: #fff !important; box-shadow: 0 12px 30px -12px var(--accent-glow); }
.btn-primary:hover { background: var(--accent-2); box-shadow: 0 16px 36px -10px var(--accent-glow); }
.btn-ghost { background: rgba(255,255,255,.04); color: #fff !important; border-color: var(--line-2); }
.btn-ghost:hover { border-color: var(--accent); background: rgba(22,119,255,.12); }
.btn-wa { background: var(--wa); color: #05260F !important; }
.btn-wa:hover { box-shadow: 0 12px 30px -10px rgba(37,211,102,.6); }
.btn-ig { background: var(--ig); color: #fff !important; }
.btn-fb { background: var(--fb); color: #fff !important; }
.btn-sm { min-height: 42px; padding: 0 18px; font-size: .78rem; }

/* ================= Hero ================= */
.ja-hero {
  position: relative; width: 100vw; margin-left: calc(50% - 50vw);
  min-height: 94vh; display: flex; align-items: center;
  background-size: cover; background-position: center 55%; overflow: hidden;
}
.ja-hero::before {
  content: ""; position: absolute; inset: 0;
  background:
    linear-gradient(90deg, rgba(8,10,13,.96) 0%, rgba(8,10,13,.80) 42%, rgba(8,10,13,.30) 100%),
    radial-gradient(ellipse at 80% 30%, rgba(22,119,255,.18), transparent 60%),
    linear-gradient(0deg, var(--bg) 0%, rgba(8,10,13,0) 28%);
}
.ja-hero-inner { position: relative; max-width: 1240px; width: 100%; margin: 0 auto; padding: 140px 24px 90px; }
.ja-hero-content { max-width: 780px; animation: rise .8s ease both; }
.ja-hero-logo { height: 96px; width: auto; object-fit: contain; margin-bottom: 26px; display: block; border-radius: 6px; }
.eyebrow {
  display: inline-flex; align-items: center; gap: 12px;
  font-size: .76rem; letter-spacing: .3em; text-transform: uppercase; color: var(--accent-2); font-weight: 600;
}
.eyebrow::before { content: ""; width: 30px; height: 2px; background: var(--accent); }
.ja-hero h1 {
  font-family: var(--display); font-weight: 400; text-transform: uppercase;
  font-size: clamp(3rem, 7.2vw, 6.2rem); line-height: .92; letter-spacing: .015em;
  margin: 18px 0 22px; color: #fff; padding: 0;
}
.ja-hero h1 .hl {
  display: block;
  background: linear-gradient(90deg, var(--accent-2) 0%, var(--accent) 40%, #8AB8FF 50%, var(--accent) 60%, var(--accent-2) 100%);
  background-size: 200% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: shine 7s linear infinite;
}
.ja-hero p.lead { font-size: clamp(1rem, 1.5vw, 1.12rem); color: #D5D9E0; line-height: 1.75; max-width: 580px;
  margin: 0 0 32px; font-weight: 300; }
.ja-hero-ctas { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 30px; }
.ja-hero-meta { display: flex; flex-wrap: wrap; gap: 10px; }
.chip {
  display: inline-flex; align-items: center; gap: 9px; padding: 9px 14px; border-radius: 8px;
  font-size: .84rem; color: #E6E9EE; background: rgba(0,0,0,.5); border: 1px solid var(--line-2);
}
.chip i { color: var(--accent-2); }

/* ================= Highlights strip ================= */
.ja-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; background: var(--line);
  border: 1px solid var(--line); border-top: 3px solid var(--accent); border-radius: var(--radius);
  overflow: hidden; margin-top: -46px; position: relative; z-index: 2; box-shadow: var(--shadow); }
.ja-strip > div { background: var(--bg-2); padding: 22px 20px; display: flex; gap: 14px; align-items: center; min-height: 92px; }
.ja-strip i { font-size: 1.15rem; color: #fff; width: 44px; height: 44px; border-radius: 8px; flex: none;
  display: grid; place-items: center; background: var(--accent); box-shadow: 0 10px 24px -10px var(--accent-glow); }
.ja-strip b { display: block; font-size: .95rem; color: #fff; font-weight: 600; }
.ja-strip span { font-size: .8rem; color: var(--muted); }

/* ================= Sections ================= */
.section { padding: 90px 0 24px; scroll-margin-top: 90px; }
.section-head { max-width: 720px; margin-bottom: 38px; }
.section-head.center { margin-left: auto; margin-right: auto; text-align: center; }
.section-head.center .eyebrow::before { display: none; }
.section h2 {
  font-family: var(--display); text-transform: uppercase; font-weight: 400; letter-spacing: .02em;
  font-size: clamp(2.5rem, 5vw, 3.8rem); line-height: 1; margin: 14px 0 18px; color: #fff;
  padding: 0 0 16px; position: relative;
}
.section h2::after { content: ""; position: absolute; left: 0; bottom: 0; width: 70px; height: 4px;
  background: var(--accent); border-radius: 2px; }
.section-head.center h2::after { left: 50%; transform: translateX(-50%); }
.section-head p { color: var(--muted); font-size: 1rem; line-height: 1.75; margin: 0; font-weight: 300; }
.section-head a { color: var(--accent-2); }

/* ================= Service cards ================= */
.svc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 22px; align-items: stretch; }
.svc-card {
  background: var(--card); border: 1px solid var(--line); border-radius: var(--radius);
  overflow: hidden; display: flex; flex-direction: column; height: 100%;
  transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease; animation: rise .7s ease both;
}
.svc-card:hover { transform: translateY(-6px); border-color: rgba(22,119,255,.6);
  box-shadow: 0 26px 50px -24px var(--accent-glow); }
.svc-media { position: relative; aspect-ratio: 4 / 3; overflow: hidden; background: #1B2027; flex: none; }
.svc-media img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .6s ease; }
.svc-card:hover .svc-media img { transform: scale(1.07); }
.svc-media::after { content: ""; position: absolute; inset: 0; background: linear-gradient(0deg, rgba(23,28,35,.95), rgba(23,28,35,0) 55%); }
.svc-icon { position: absolute; left: 18px; bottom: 16px; z-index: 1; width: 44px; height: 44px; border-radius: 8px;
  display: grid; place-items: center; background: var(--accent); color: #fff; box-shadow: 0 10px 24px -8px var(--accent-glow); }
.svc-body { padding: 20px 20px 22px; display: flex; flex-direction: column; flex: 1; }
.svc-body h3 { font-family: var(--display); font-weight: 400; text-transform: uppercase; letter-spacing: .04em;
  font-size: 1.75rem; line-height: 1; margin: 0 0 10px; color: #fff; padding: 0; white-space: nowrap; }
.svc-body p { color: var(--muted); font-size: .88rem; line-height: 1.65; margin: 0 0 16px; flex: 1; font-weight: 300; }
.svc-price { font-size: .72rem; letter-spacing: .16em; text-transform: uppercase; color: var(--accent-2); font-weight: 600; margin-bottom: 14px; }
.svc-actions { display: flex; gap: 8px; margin-top: auto; }
.svc-actions .btn { flex: 1; }
.svc-actions .btn-wa { flex: 0 0 46px; padding: 0; }
.demo-note { display: inline-flex; align-items: center; gap: 8px; font-size: .76rem; color: #8b8b93;
  border: 1px dashed rgba(255,255,255,.16); padding: 6px 12px; border-radius: 6px; margin-top: 20px; }

/* ================= Before & After ================= */
.ba-title { font-family: var(--display); font-size: 1.6rem; letter-spacing: .04em; color: #fff; margin: 2px 0 0; }

/* ================= Instagram ================= */
.ig-card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 18px;
  display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
.ig-head { display: flex; align-items: center; gap: 12px; }
.ig-avatar { width: 46px; height: 46px; border-radius: 50%; display: grid; place-items: center; color: #fff;
  background: var(--ig); font-size: 1.3rem; flex: none; }
.ig-head b { display: block; color: #fff; font-size: .95rem; font-weight: 600; }
.ig-head span { color: var(--muted); font-size: .8rem; }
.ig-fallback { color: var(--muted); font-size: .8rem; margin: 0; width: 100%; }
.social-row { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin-top: 10px; }

/* ================= Round social icons (used in contact, footer, floating) ================= */
.soc { display: flex; gap: 12px; flex-wrap: wrap; }
.soc a { width: 48px; height: 48px; border-radius: 50%; display: grid; place-items: center; flex: none;
  color: #fff !important; font-size: 1.3rem; text-decoration: none !important;
  box-shadow: 0 10px 24px -10px rgba(0,0,0,.8); transition: transform .2s ease, box-shadow .2s ease; }
.soc a:hover { transform: translateY(-3px) scale(1.07); }
.soc .ig, .social-float .sf-ig { background: var(--ig); }
.soc .fb, .social-float .sf-fb { background: var(--fb); }
.soc .wa, .social-float .sf-wa { background: var(--wa); }

/* ================= Quote ================= */
/* Equal-height left panel and form box */
[data-testid="stColumn"]:has(.quote-panel) [data-testid="stVerticalBlock"],
[data-testid="stColumn"]:has(.quote-panel) [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stColumn"]:has(.quote-panel) [data-testid="stElementContainer"],
[data-testid="stColumn"]:has(.quote-panel) [data-testid="stHtml"],
[data-testid="stColumn"]:has(.quote-panel) .stHtml { height: 100%; }
.quote-panel { box-sizing: border-box; height: 100%; display: flex; flex-direction: column;
  background: linear-gradient(165deg, #0E1520 0%, var(--bg-2) 55%); border: 1px solid var(--line);
  border-top: 3px solid var(--accent); border-radius: var(--radius); padding: 32px; }
.quote-panel h3 { font-family: var(--display); font-weight: 400; font-size: 2.1rem; letter-spacing: .03em;
  margin: 0 0 10px; color: #fff; padding: 0; }
.quote-panel p { color: var(--muted); line-height: 1.7; font-weight: 300; }
.quote-panel .meta { display: flex; align-items: center; gap: 10px; margin: 6px 0; color: #D5D9E0; font-size: .92rem; }
.quote-panel .meta i { color: var(--accent-2); width: 18px; text-align: center; }
.quote-panel .btn { align-self: flex-start; margin-top: auto; }
.quote-steps { list-style: none; padding: 0; margin: 20px 0 22px; }
.quote-steps li { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 16px; color: #E6E9EE; font-size: .93rem; line-height: 1.55; }
.quote-steps li b { flex: none; width: 32px; height: 32px; border-radius: 8px; display: grid; place-items: center;
  background: var(--accent); color: #fff; font-size: .85rem; }

[data-testid="stForm"] { background: var(--card); border: 1px solid var(--line) !important;
  border-top: 3px solid var(--accent) !important; border-radius: var(--radius) !important; padding: 28px !important; height: 100%; }
[data-testid="stForm"] label p { color: #E6E9EE !important; font-weight: 500; font-family: var(--font); }
.stTextInput input, .stTextArea textarea, .stDateInput input,
[data-baseweb="select"] > div { background: #0C0F13 !important; border-color: var(--line-2) !important;
  border-radius: 8px !important; min-height: 46px; font-family: var(--font) !important; }
.stTextInput input:focus, .stTextArea textarea:focus { border-color: var(--accent) !important; }
[data-testid="stFormSubmitButton"] button, [data-testid="stBaseButton-primaryFormSubmit"] {
  width: 100%; min-height: 54px; border-radius: 8px !important; background: var(--accent) !important;
  color: #fff !important; border: none !important; box-shadow: 0 12px 30px -12px var(--accent-glow); }
[data-testid="stFormSubmitButton"] button:hover { background: var(--accent-2) !important; }
[data-testid="stFormSubmitButton"] button p { color: #fff !important; font-weight: 600; letter-spacing: .08em;
  text-transform: uppercase; font-family: var(--font); }
[data-testid="stLinkButton"] a { border-radius: 8px !important; min-height: 50px; font-weight: 600; }

/* ================= Contact ================= */
.contact-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; align-items: stretch; }
.contact-card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 26px;
  text-decoration: none !important; display: flex; flex-direction: column; height: 100%; box-sizing: border-box;
  transition: border-color .2s, transform .2s; }
a.contact-card:hover { border-color: var(--accent); transform: translateY(-4px); }
.contact-card > i { font-size: 1.25rem; width: 50px; height: 50px; border-radius: 10px; display: grid; place-items: center;
  background: var(--accent); color: #fff; margin-bottom: 18px; box-shadow: 0 10px 24px -10px var(--accent-glow); }
.contact-card h3 { font-size: .74rem; letter-spacing: .22em; text-transform: uppercase; color: var(--muted);
  margin: 0 0 8px; font-weight: 600; padding: 0; font-family: var(--font); }
.contact-card p { color: #fff; margin: 0; font-size: .98rem; font-weight: 500; line-height: 1.55; }
.contact-card .soc { margin-top: 2px; }

/* ================= Footer ================= */
.ja-footer { width: 100vw; margin-left: calc(50% - 50vw); margin-top: 80px; background: #06080B;
  border-top: 3px solid var(--accent); }
.ja-footer-inner { max-width: 1240px; margin: 0 auto; padding: 64px 24px 34px;
  display: grid; grid-template-columns: 1.5fr 1fr 1fr 1fr; gap: 40px; }
.ja-footer .ja-brand { margin-bottom: 18px; }
.ja-footer h4 { font-family: var(--display); font-weight: 400; font-size: 1.4rem; letter-spacing: .06em;
  color: #fff; margin: 0 0 16px; }
.ja-footer p, .ja-footer li, .ja-footer li a { color: var(--muted); font-size: .9rem; line-height: 1.95;
  text-decoration: none !important; font-weight: 300; }
.ja-footer li a:hover { color: var(--accent-2); }
.ja-footer ul { list-style: none; padding: 0; margin: 0; }
.ja-footer .soc { margin-top: 18px; }
.ja-copy { max-width: 1240px; margin: 0 auto; padding: 22px 24px 30px; border-top: 1px solid var(--line);
  display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; color: #6F7682; font-size: .8rem; }

/* ================= Floating Instagram / Facebook / WhatsApp ================= */
.social-float { position: fixed; right: 22px; bottom: 22px; z-index: 1000;
  display: flex; flex-direction: column; gap: 12px; }
.social-float a { width: 56px; height: 56px; border-radius: 50%; display: grid; place-items: center;
  color: #fff !important; font-size: 1.5rem; text-decoration: none !important;
  box-shadow: 0 12px 28px -8px rgba(0,0,0,.75); transition: transform .2s ease; }
.social-float a:hover { transform: translateY(-3px) scale(1.07); }
.social-float .sf-wa { font-size: 1.8rem; box-shadow: 0 12px 30px -8px rgba(37,211,102,.6); }

/* ================= Tablet ================= */
@media (max-width: 1100px) {
  .svc-grid, .contact-grid { grid-template-columns: repeat(2, 1fr); }
  .ja-strip { grid-template-columns: repeat(2, 1fr); }
  .ja-footer-inner { grid-template-columns: 1fr 1fr; }
  .ja-links { gap: 20px; }
}
/* Header: links move to a scrollable second row */
@media (max-width: 900px) {
  .ja-nav-inner { height: auto; flex-wrap: wrap; padding: 10px 20px 0; row-gap: 6px; }
  .ja-links { order: 3; width: 100%; gap: 22px; overflow-x: auto; padding: 4px 0 10px;
    scrollbar-width: none; -webkit-overflow-scrolling: touch; }
  .ja-links::-webkit-scrollbar { display: none; }
  .ja-links a { font-size: .74rem; flex: none; }
  .ja-nav-cta .btn-ghost { display: none; }
  .ja-hero-inner { padding-top: 150px; }
}
/* ================= Phone ================= */
@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"], .block-container { padding: 0 16px 40px !important; }
  [data-testid="stHorizontalBlock"] { gap: 16px !important; }
  .ja-nav-inner { padding: 8px 16px 0; }
  .ja-brand { gap: 10px; }
  .ja-brand img { height: 40px; }
  .ja-brand-name b { font-size: 1.4rem; }
  .ja-brand-name small { font-size: .55rem; letter-spacing: .32em; }
  .ja-nav-cta .btn { min-height: 38px; padding: 0 12px; font-size: .7rem; }
  .ja-hero { min-height: auto; background-position: 65% center; }
  .ja-hero::before { background: linear-gradient(0deg, rgba(8,10,13,1) 0%, rgba(8,10,13,.82) 50%, rgba(8,10,13,.6) 100%); }
  .ja-hero-inner { padding: 140px 16px 80px; }
  .ja-hero-logo { height: 72px; margin-bottom: 18px; }
  .ja-hero-ctas .btn { flex: 1 1 100%; min-height: 54px; }
  .chip { font-size: .78rem; }
  .svc-grid, .contact-grid, .ja-strip { grid-template-columns: 1fr; }
  .svc-body h3 { white-space: normal; }
  .section { padding-top: 70px; }
  .section h2 { font-size: 2.6rem; }
  .quote-panel { padding: 24px; }
  [data-testid="stForm"] { padding: 20px !important; }
  .ja-footer-inner { grid-template-columns: 1fr; gap: 30px; padding-top: 48px; }
  .ja-copy { padding-bottom: 96px; }
  .social-float { right: 14px; bottom: 16px; gap: 10px; }
  .social-float a { width: 50px; height: 50px; font-size: 1.35rem; }
  .social-float .sf-wa { font-size: 1.6rem; }
}

/* ================= Premium blue refinements ================= */
/* Hero photo is a real image element so it loads first (faster LCP) */
.ja-hero-bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
  object-position: center 55%; z-index: 0; }
.ja-hero::before { z-index: 1; }
.ja-hero-inner { z-index: 2; }
.ja-hero-content { animation: none; }            /* no fade-in on the LCP text */
.ja-hero h1 .hl {
  background: linear-gradient(90deg, #FFFFFF 0%, #BFD6FF 35%, var(--accent-2) 60%, #BFD6FF 80%, #FFFFFF 100%);
  background-size: 200% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
}
.ja-nav { background: rgba(8,10,13,.9); border-bottom: 1px solid var(--line); }
.ja-nav::after { height: 1px; opacity: .8; }

/* Secondary CTA: transparent, white border, blue on hover */
.btn-ghost { background: transparent; color: #fff !important; border: 1px solid rgba(255,255,255,.85); }
.btn-ghost:hover { background: var(--accent-soft); border-color: var(--accent-2); color: #fff !important;
  box-shadow: 0 10px 28px -12px var(--accent-glow); }
.btn-primary { box-shadow: 0 12px 28px -14px var(--accent-glow); }

/* Icon tiles: dark with a blue icon (subtle, not solid blue) */
.ja-strip i, .contact-card > i, .quote-steps li b {
  background: var(--accent-soft); color: var(--accent-2); border: 1px solid rgba(22,119,255,.35); box-shadow: none; }
.svc-icon { background: rgba(8,10,13,.78); color: var(--accent-2); border: 1px solid rgba(22,119,255,.45); box-shadow: none; }
.ja-strip { border-top: 2px solid var(--accent); }
.ja-strip > div { background: var(--bg-2); }

/* Cards */
.svc-card, .contact-card, .ig-card { background: var(--card); border-color: var(--line); }
.svc-card:hover { border-color: rgba(22,119,255,.55); box-shadow: 0 26px 50px -26px var(--accent-glow); }
.svc-price { color: var(--muted); }
.svc-price::before { content: ""; display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); margin-right: 8px; vertical-align: middle; }

/* Every contact card responds to hover (not only WhatsApp) */
.contact-card { transition: border-color .25s ease, transform .25s ease, box-shadow .25s ease; }
.contact-card:hover { border-color: rgba(22,119,255,.6); transform: translateY(-4px);
  box-shadow: 0 22px 44px -24px var(--accent-glow); }
.contact-card:hover > i { background: var(--accent); color: #fff; }
.contact-card h3 { color: var(--muted); }

/* Quote section */
.quote-panel { background: linear-gradient(165deg, #0E1520 0%, var(--bg-2) 60%); border-top: 2px solid var(--accent); }
[data-testid="stForm"] { border-top: 2px solid var(--accent) !important; }
.quote-panel .meta i { color: var(--accent-2); }

/* Footer */
.ja-footer { border-top: 1px solid var(--line); }
.ja-footer::before { content: ""; display: block; height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent); }
.ja-footer h4 { color: #fff; }
.ja-footer li a:hover { color: var(--accent-2); }

/* Headings underline + eyebrow */
.section h2::after { height: 3px; width: 56px; }
.eyebrow { color: var(--accent-2); }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
"""

ADMIN_CSS = FONT_IMPORTS + BASE + """
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container { max-width: 1320px !important; padding-top: 2.2rem !important; }

[data-testid="stSidebar"] { background: #0C0F13 !important; border-right: 1px solid var(--line); }
[data-testid="stSidebarNav"] a { border-radius: 8px; }
[data-testid="stSidebarNav"] a span { font-weight: 500; }
[data-testid="stSidebarNavSeparator"] { border-color: var(--line); }

h1, h2, h3 { color: #fff; }
.adm-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap;
  padding-bottom: 18px; margin-bottom: 8px; border-bottom: 2px solid var(--accent); }
.adm-head h1 { font-family: var(--display); font-weight: 400; letter-spacing: .03em; font-size: 2.8rem;
  margin: 0; padding: 0; line-height: 1; }
.adm-head p { color: var(--muted); margin: 6px 0 0; font-size: .92rem; }
.adm-kicker { font-size: .7rem; letter-spacing: .24em; text-transform: uppercase; color: var(--accent-2); font-weight: 600; }

.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 6px 0 10px; }
.stat { background: var(--card); border: 1px solid var(--line); border-left: 3px solid var(--accent); border-radius: 10px;
  padding: 18px 18px 16px; position: relative; overflow: hidden; }
.stat .lbl { display: flex; align-items: center; gap: 8px; font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
.stat .lbl i { color: var(--accent-2); }
.stat .val { font-family: var(--display); font-size: 2.3rem; font-weight: 400; color: #fff; margin-top: 8px; line-height: 1; letter-spacing: .02em; }
.stat .sub { font-size: .78rem; color: var(--muted); margin-top: 6px; }
.stat.warn .val { color: #FBBF24; }
.stat.good .val { color: #4ADE80; }

.badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: .76rem; font-weight: 600; border: 1px solid; }
.b-paid, .b-completed, .b-converted { color: #4ADE80; border-color: rgba(74,222,128,.35); background: rgba(74,222,128,.08); }
.b-partially-paid, .b-in-progress, .b-contacted { color: #FBBF24; border-color: rgba(251,191,36,.35); background: rgba(251,191,36,.08); }
.b-unpaid, .b-cancelled { color: #F87171; border-color: rgba(248,113,113,.35); background: rgba(248,113,113,.08); }
.b-booked, .b-new { color: #60A5FA; border-color: rgba(96,165,250,.35); background: rgba(96,165,250,.08); }
.b-enquiry, .b-closed { color: #CBD5E1; border-color: rgba(203,213,225,.3); background: rgba(203,213,225,.06); }

.panel { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 18px 20px; }
.kv { display: grid; grid-template-columns: 150px 1fr; gap: 8px 16px; font-size: .9rem; }
.kv span { color: var(--muted); }
.kv b { color: #fff; font-weight: 500; word-break: break-word; }
.empty { text-align: center; padding: 38px 20px; border: 1px dashed var(--line-2); border-radius: 10px; color: var(--muted); }
.empty i { font-size: 1.8rem; display: block; margin-bottom: 10px; color: #6B7280; }

[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--line) !important; border-radius: 10px !important; }
[data-testid="stMetric"] { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--accent) !important; color: #fff !important; border: none !important; }
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover { background: var(--accent-2) !important; }
[data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primaryFormSubmit"] p { color: #fff !important; font-weight: 600; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { padding: 8px 14px; }

@media (max-width: 900px) { .stat-grid { grid-template-columns: repeat(2, 1fr); } .kv { grid-template-columns: 1fr; } }
@media (max-width: 520px) { .stat-grid { grid-template-columns: 1fr; } }
"""

LOGIN_CSS = """
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container { max-width: 460px !important; padding-top: 9vh !important; }
.login-brand { text-align: center; margin-bottom: 22px; }
.login-brand img { height: 84px; width: auto; object-fit: contain; border-radius: 6px; }
.login-brand h1 { font-family: var(--display); font-weight: 400; font-size: 2.4rem; letter-spacing: .03em; margin: 14px 0 4px; padding: 0; }
.login-brand p { color: var(--muted); margin: 0; font-size: .9rem; }
[data-testid="stForm"] { border-top: 3px solid var(--accent) !important; }
"""
