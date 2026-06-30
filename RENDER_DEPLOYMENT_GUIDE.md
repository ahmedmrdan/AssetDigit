# Deploying Assetdigit CMMS on Render — Complete Guide

## ⚠️ Why your data was disappearing

Render's free web service has a **temporary filesystem**. Every time it restarts
(which happens after ~15 min of inactivity, or on every deploy), any file written
to disk — including your SQLite `cmms.db` — is **wiped**.

The fix: use Render's **free PostgreSQL database** instead, which lives separately
and is never wiped.

---

## Step 1 — Create the PostgreSQL Database

1. Go to your Render Dashboard → click **New +** → **PostgreSQL**
2. Name it: `cmms-database`
3. Region: pick the **same region** you'll use for the web service
4. Plan: **Free**
5. Click **Create Database**
6. Wait ~1 minute. Open the database page and copy the **Internal Database URL**
   (looks like `postgresql://user:pass@host/dbname`)

---

## Step 2 — Push This Code to GitHub

If you haven't already:
```bash
git init
git add .
git commit -m "Assetdigit CMMS - Render ready"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/assetdigit-cmms.git
git push -u origin main
```

---

## Step 3 — Create the Web Service on Render

1. Render Dashboard → **New +** → **Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name:** assetdigit-cmms
   - **Region:** same as your database
   - **Branch:** main
   - **Root Directory:** `cmms` (the folder containing manage.py)
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn cmms.wsgi:application`
   - **Plan:** Free

---

## Step 4 — Add Environment Variables

In the web service → **Environment** tab, add:

| Key | Value |
|---|---|
| `DATABASE_URL` | Paste the **Internal Database URL** from Step 1 |
| `SECRET_KEY` | Any long random string (Render can auto-generate) |
| `PYTHON_VERSION` | `3.11.0` |

---

## Step 5 — Deploy

Click **Create Web Service**. Render will:
1. Install everything in `requirements.txt`
2. Run `build.sh` (this runs migrations + creates your admin user automatically)
3. Start the server with `gunicorn`

This takes 2–5 minutes the first time.

---

## Step 6 — First Login

Once deployed, open your Render URL (e.g. `https://assetdigit-cmms.onrender.com`)

Login: `admin` / `admin123`

**Change this password immediately** from User Management.

---

## ✅ Your Data is Now Permanent

Because data lives in the **PostgreSQL database** (a separate Render service),
it survives:
- Service restarts
- Free tier sleep/wake cycles
- New deployments / code updates

---

## Important Notes

- **Free PostgreSQL databases on Render expire after 90 days** unless upgraded to paid.
  Render will email you before this happens — back up your data (see Backup & Restore
  page in the app) before it expires, or upgrade the database plan (~$7/month).
- **Free web services sleep after 15 min inactivity** and take ~30 seconds to wake up
  on the next visit. This is normal and doesn't affect your data anymore.
- To avoid sleep entirely, upgrade the web service to a paid plan (~$7/month).

---

## Updating Your Code Later

Whenever you want to push new features:
```bash
git add .
git commit -m "describe your change"
git push
```
Render automatically redeploys. Migrations run automatically via `build.sh`.
Your data is never touched by this process.
