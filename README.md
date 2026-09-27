# JA Detailing London — Website + Admin Management System

A premium public website and a private business dashboard in one Streamlit app.

* **Public site** (`/`): hero, 8 services, before & after sliders, Instagram posts, a quote form that saves the enquiry and opens a pre-filled WhatsApp message, contact details, footer and a floating WhatsApp button.
* **Admin system** (`/admin`, login required): dashboard, website enquiries, clients, jobs, payments, PDF receipts (`JA-2026-0001`…), revenue reports and settings/backups.

---

## 1. Project structure

```
JA Detail/
├── streamlit_app.py        # Entry point + routing (public vs admin)
├── config.py               # Business info, services, ALL image paths, Instagram posts
├── styles.py               # All CSS (public site, admin, login)
├── database.py             # SQLite connection, schema, transactions
├── models.py               # Status lists, dataclasses, ValidationError
├── services.py             # Business logic: clients, jobs, payments, receipts, reports
├── auth.py                 # Admin login (hashed password from secrets, lockout, timeout)
├── utils.py                # Money, dates, validation, WhatsApp links, image loading
├── ui.py                   # Admin UI components (cards, badges, panels)
├── receipt_pdf.py          # PDF receipt generator
├── requirements.txt
├── public/home.py          # The public website
├── pages/                  # Admin pages (only registered after login)
│   ├── admin_login.py  dashboard.py  enquiries.py  clients.py
│   ├── jobs.py  payments.py  receipts.py  reports.py  settings.py
├── images/
│   ├── logo.png            # ← your existing logo goes here
│   ├── hero/  services/  before_after/  gallery/
│   └── README.txt          # exact file names for your own photos
├── data/database.db        # created automatically on first run
├── tools/hash_password.py  # generates the admin password hash
├── tests/test_core.py      # tests for the database/business logic
├── .streamlit/config.toml  # dark theme, hides error details from visitors
├── .streamlit/secrets.toml.example
└── .vscode/launch.json     # "Run JA Detailing" button in VS Code
```

---

## 2. Setup (Windows / macOS / Linux)

Requires **Python 3.10+**.

1. Open the `JA Detail` folder in VS Code (**File → Open Folder**).
2. **Put your logo in place:** copy it to `images/logo.png`. (The app still runs without it and shows a text wordmark instead.)
3. Open a terminal in VS Code (**Terminal → New Terminal**) and create a virtual environment:

   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. **Set up admin login:**

   ```bash
   python tools/hash_password.py
   ```

   Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, then paste in your username and the generated hash:

   ```toml
   ADMIN_USERNAME = "your-username"
   ADMIN_PASSWORD_HASH = "pbkdf2_sha256$390000$....."
   ```

   `secrets.toml` is git-ignored, so never commit or share it.

## 3. Run locally

```bash
streamlit run streamlit_app.py
```

* Website: http://localhost:8501
* Admin: http://localhost:8501/admin

In VS Code you can also press **F5** (or use Run and Debug → "Run JA Detailing (Streamlit)").

Run the logic tests with `python tests/test_core.py`.

---

## 4. Replacing the demo images with real JA Detailing photos

The service, hero and before/after photos are **free Unsplash stock images** ([license](https://unsplash.com/license)). They are labelled on the site as illustrative and are **not** presented as JA Detailing's work.

To use your own photos, drop files with the names listed in `images/README.txt` into the matching folder (for example `images/services/ceramic-coating.jpg`). They are picked up automatically and resized for the web. When every demo photo has been replaced, set `DEMO_IMAGERY_NOTICE = False` in `config.py`.

All image settings live in one place: `SERVICE_IMAGES`, `HERO_IMAGE` and `BEFORE_AFTER` in `config.py`.

---

## 5. How things work

| Feature | Details |
|---|---|
| **Quote form** | Validates input (Sundays blocked, phone format, required fields), saves an enquiry, then shows a **Send enquiry on WhatsApp** button with every detail pre-filled for +44 7493 164083. No SMS is sent or claimed. |
| **Instagram** | The two posts are embedded (not downloaded). A "View on Instagram" card is always shown, so the section still works if an embed is blocked. |
| **Enquiries** | Show up in Admin → Enquiries. You can reply on WhatsApp or **convert** an enquiry into a client plus a job. |
| **Jobs** | Total = price + extra − discount. Outstanding = Total − Received. Payment status (Paid / Partially Paid / Unpaid) is calculated from recorded payments, so it can't drift out of sync. Received can't exceed the total. |
| **Receipts** | Numbered `JA-YEAR-0001` sequentially and uniquely (safe even with two people clicking at once). Each receipt stores a snapshot of the figures when it was issued. PDF download for sending or printing. No VAT is shown. |
| **Revenue** | Counts jobs that are Booked, In Progress or Completed, in the month of the job date. Enquiry and Cancelled jobs are excluded. |
| **Money** | Stored as whole pence to avoid rounding errors. |
| **Empty database** | The app starts empty, with no fake clients or revenue. Every page shows a friendly empty state. |

### Security
* Admin pages are **not registered at all** for logged-out visitors, and each page also checks the login itself.
* Passwords are compared as PBKDF2-SHA256 hashes, in constant time. After 5 failed attempts, login locks for 5 minutes. Sessions expire after 8 hours.
* Every SQL query is parameterised. User text is HTML-escaped before it is displayed.
* Visitors never see error details (`showErrorDetails = "none"`). Errors are logged on the server instead.

---

## 6. Deploying to Streamlit Community Cloud

1. Push the project to a **private** GitHub repository. `secrets.toml` and the database are git-ignored.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app**, pick the repository, and set the main file to `streamlit_app.py`.
3. Under **Advanced settings → Secrets**, paste the contents of your `secrets.toml`.
4. Deploy.

> ⚠️ **Important about data on Streamlit Cloud:** its file system is *temporary*. The SQLite file in `data/` can be wiped when the app restarts or redeploys. That is fine for a demo, but **for real business use**, either
> * download regular backups (Admin → Settings → Data & backup), or preferably
> * move to a hosted PostgreSQL database (e.g. Supabase or Neon). The data layer is built for this: only `database.py` needs to change (switch `sqlite3` to `psycopg`, change `?` placeholders to `%s`, and translate the schema). Put the connection string in secrets.
>
> Other options that keep a persistent disk: a small VPS, Railway or Render with a volume, running the same `streamlit run` command.

### Custom domain / SEO
The page title is set to *"JA Detailing London | Premium Car Detailing in London & Harlow"*, and a meta description is added at runtime. Streamlit Community Cloud doesn't support custom domains directly. For a custom domain and the best search visibility, host on a VPS/Render behind your own domain.

---

## 7. Placeholders / information still needed from JA Detailing
* Real work photos (see `images/README.txt`)
* Prices, if they ever want them shown (currently "Contact us for a quote")
* VAT number, only if VAT registered (receipts currently show no tax details)
* Any reviews, certifications or guarantees. Nothing like this was invented.
