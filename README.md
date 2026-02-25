# Lightweight Challenge Hosting Platform

This is a small multi-user challenge hosting platform built with **Flask** and **SQLite**. It is designed for running timed challenges from a single laptop that is exposed to participants via **ngrok**.

## Key Features

- User registration with name + email (no passwords)
- Client-side identity caching (browser storage) with a minimal server-side session
- Content list with lock/unlock state and per-content time limits
- Single attempt per user per content (enforced by the backend)
- Server-side timing and scoring (frontend timers are only for display)
- Leaderboard with cumulative scores across all contents
- Simple admin panel for:
  - Logging in with a hardcoded username/password
  - Creating content modules (title, time limit, lock/unlock)
  - Viewing attempts and leaderboard

## Setup instructions

### 1. Install dependencies

From the project root:

**Windows (PowerShell or CMD):**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create the database

**First time (new database):**
```bash
python -c "from app import app; from models import db; app.app_context().push(); db.create_all(); print('Database created.')"
```

**If you already had the app running before (existing database):**  
Add the new chapter/panel columns:
```bash
python migrate_add_chapter_fields.py
```

### 3. Run the server

```bash
python app.py
```

- App runs at **http://127.0.0.1:5000** (or `0.0.0.0:5000` for LAN/ngrok).
- Override with env vars: `FLASK_RUN_HOST`, `FLASK_RUN_PORT`, `FLASK_DEBUG`.

## Exposing via ngrok

With the server running:

```bash
ngrok http 5000
```

Use the HTTPS URL printed by ngrok as the public URL for participants.

## Admin Credentials

Default admin credentials (can be overridden via environment variables):

- Username: `admin` (`ADMIN_USERNAME`)
- Password: `changeme` (`ADMIN_PASSWORD`)

## Chapter structure (overview)

- **Chapters 1–6** appear on the dashboard and unlock by time (admin sets unlock time / is_unlocked).
- **Chapters 7 and 8** are hidden until a player **completes Chapter 6**. Then a narrative reveal runs (“You thought the story ended. It didn’t.”) and chapters 7 & 8 unlock. Access to 7/8 is validated on the backend; direct URLs are blocked until then.

---

## Adding comic strip chapters (6–8 pages per chapter)

Each chapter can be a **comic** with **6–8 panels (pages)**. Panels are image URLs (e.g. from Cloudinary or any CDN). You add them via the Admin panel when creating or editing content.

### Step 1: Log in as admin

1. Open **http://127.0.0.1:5000/admin**
2. Log in (default: `admin` / `changeme`)

### Step 2: Create a chapter

1. Click **Create Content**
2. Fill in:
   - **Title** – e.g. `Chapter 1: The Crime`
   - **Time limit (seconds)** – e.g. `600` (10 minutes)
   - **Chapter number** – `1` through `8` (must match the story order)
   - **Unlock time** – leave empty, or use ISO datetime (e.g. `2025-03-01T00:00:00`) for scheduled unlock
   - **Unlocked** – check this if the chapter should be playable now (for chapters 1–6)
   - **Requires Ch.6 completion** – check **only for Chapter 7 and Chapter 8**
   - **Panels JSON** – see Step 3 below

### Step 3: Add 6–8 panel URLs (comic pages)

In **Panels JSON**, use this format (one URL per panel; **6–8 panels per chapter**):

```json
{
  "chapter": 1,
  "panels": [
    "https://res.cloudinary.com/YOUR_CLOUD/image/upload/v123/ch1_page1.png",
    "https://res.cloudinary.com/YOUR_CLOUD/image/upload/v123/ch1_page2.png",
    "https://res.cloudinary.com/YOUR_CLOUD/image/upload/v123/ch1_page3.png",
    "https://res.cloudinary.com/YOUR_CLOUD/image/upload/v123/ch1_page4.png",
    "https://res.cloudinary.com/YOUR_CLOUD/image/upload/v123/ch1_page5.png",
    "https://res.cloudinary.com/YOUR_CLOUD/image/upload/v123/ch1_page6.png"
  ]
}
```

- Use **6, 7, or 8** URLs in the `"panels"` array (one per page).
- Order matters: first URL = page 1, second = page 2, etc.
- You can use **Cloudinary** or any public image URL (HTTPS recommended).
- Keep the JSON on one line or paste it as-is; the app parses it and shows a slideshow + zoom viewer.

**Example with 8 panels (Chapter 2):**
```json
{"chapter": 2, "panels": ["https://example.com/c2-1.png", "https://example.com/c2-2.png", "https://example.com/c2-3.png", "https://example.com/c2-4.png", "https://example.com/c2-5.png", "https://example.com/c2-6.png", "https://example.com/c2-7.png", "https://example.com/c2-8.png"]}
```

### Step 4: Repeat for all 8 chapters

| Chapter | Chapter number | Unlocked | Requires Ch.6 completion | Panels JSON |
|--------|----------------|----------|--------------------------|-------------|
| 1      | 1              | ✓        | —                        | 6–8 URLs    |
| 2      | 2              | ✓        | —                        | 6–8 URLs    |
| 3      | 3              | ✓        | —                        | 6–8 URLs    |
| 4      | 4              | ✓        | —                        | 6–8 URLs    |
| 5      | 5              | ✓        | —                        | 6–8 URLs    |
| 6      | 6              | ✓        | —                        | 6–8 URLs    |
| 7      | 7              | —        | ✓                        | 6–8 URLs    |
| 8      | 8              | —        | ✓                        | 6–8 URLs    |

Chapters 7 and 8 stay hidden until a player completes Chapter 6; then they appear with the narrative reveal.

### Step 5: Upload panel images (e.g. Cloudinary)

1. Create a Cloudinary account (or use another CDN).
2. Upload each page image (e.g. `ch1_page1.png` … `ch1_page6.png`).
3. Copy the **secure URL** for each image.
4. Paste those URLs into the `"panels"` array in **Panels JSON** for that chapter.

Using **compressed** images (e.g. WebP or optimized PNG) is recommended for faster loading; the app lazy-loads and preloads the next panel.

---

## Database migration (existing databases only)

If you already had a `contents` table before the chapter/panels feature, add the new columns once:

```bash
python migrate_add_chapter_fields.py
```

Then create your 8 chapters in Admin → Create Content as in the table above, with **Panels JSON** for each comic chapter (6–8 URLs per chapter).

