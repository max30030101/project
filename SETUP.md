# FITNESS ZONE: setup and launch guide

## Part 1. Run it on your computer with VS Code

1. **Install** Python 3.10 or newer (python.org; on Windows tick "Add Python to PATH"), VS Code, and the VS Code *Python* extension.
2. **Unzip** `fitness-zone.zip`. In VS Code choose **File > Open Folder** and open the `fitness-zone` folder.
3. **Open a terminal** in VS Code (Terminal > New Terminal) and run these in order.

   Windows (PowerShell):
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt and `venv\Scripts\activate.bat`.

   macOS / Linux:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Create the database and load demo data** (same terminal):
   ```bash
   python manage.py makemigrations accounts shop workouts
   python manage.py migrate
   python manage.py seed_demo
   python manage.py createsuperuser
   ```
5. **Start the site:** `python manage.py runserver`, then open http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/ (log in with the superuser you created)
   - Or press **F5** in VS Code and pick "Django: run FITNESS ZONE" to run with the debugger.
6. **Try it:** register an account (the welcome email prints in the terminal), generate a workout plan, favourite products, add to cart, check out, then see the order in the admin panel.

Stop the server with Ctrl+C. Next time, just activate the venv and run `python manage.py runserver`.

## Part 2. Put it live (Render.com, recommended)

The project ships with `render.yaml`, `build.sh`, `Procfile` and a PostgreSQL setup, so Render can create everything for you.

1. Create a free account at github.com and a new empty repository. In the VS Code terminal:
   ```bash
   git init
   git add .
   git commit -m "FITNESS ZONE"
   git branch -M main
   git remote add origin https://github.com/<your-username>/fitness-zone.git
   git push -u origin main
   ```
   (Run your local steps once first; this also commits the generated `migrations/` folders. That is good practice, so keep them in Git.)
2. Create an account at render.com, choose **New > Blueprint**, connect your GitHub repo and select it. Render reads `render.yaml`.
3. When asked, set `DJANGO_SUPERUSER_PASSWORD` (your admin password) and `DJANGO_SUPERUSER_EMAIL`.
4. Click **Apply**. The first build takes a few minutes. Your site goes live at `https://fitness-zone.onrender.com` (or the URL Render shows).
5. Sign in at `/admin/` with username `admin` and the password you set. Add your real products, images and categories.
6. **Real welcome emails:** in the Render dashboard open the service > Environment and add `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS=1`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (for Gmail, use an app password) and `DEFAULT_FROM_EMAIL`.
7. **Custom domain:** Render dashboard > Settings > Custom Domains. Then add the domain to `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` (with `https://`), and set `SITE_URL`.

Good to know before launch:
- **Uploaded product images** are stored on the server's disk, which free hosting wipes on redeploy. For a real store, attach a persistent disk (set `MEDIA_ROOT` to its path and `SERVE_MEDIA=1`) or move to cloud storage such as S3. Check Render's current free-tier limits (sleeping services, database retention) before relying on it for customers.
- Change `SEED_DEMO` to `0` after the first deploy if you don't want demo products re-added.
- Always keep `DJANGO_DEBUG=0` in production.

### Other hosts
Any host that runs Python works: set the environment variables from `.env.example`, use `bash build.sh` as the build step and `gunicorn fitnesszone.wsgi:application` as the start command. On PythonAnywhere, use their Django guide, point the WSGI file at `fitnesszone.wsgi`, and map `/static/` to `staticfiles/` and `/media/` to `media/`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `no such table` | Run `makemigrations accounts shop workouts`, then `migrate` |
| Shop is empty | Run `python manage.py seed_demo` |
| Workout plan has no exercises | Same: `seed_demo` loads the exercise library |
| Static files missing in production | Check the build log ran `collectstatic`; keep `DJANGO_DEBUG=0` |
| `DisallowedHost` | Add your domain to `DJANGO_ALLOWED_HOSTS` |
| CSRF verification failed on a live site | Add `https://your-domain` to `CSRF_TRUSTED_ORIGINS` |

## Changing the website name

The name lives in one place: `SITE_NAME` in `fitnesszone/settings.py` (or the `SITE_NAME` environment variable on your host).
Change it once and the header logo, page titles, footer, welcome email and admin panel all update.
The last word of the name is shown in the accent colour. The internal `fitnesszone/` folder name does not need to change.
