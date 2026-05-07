# ReadWise Deployment Guide

## Project Overview
ReadWise is a Django app for mood-based book recommendations with Google OAuth login.
It supports deployment on Render and PythonAnywhere using environment-based configuration.

## Render Deployment Steps
1. Push your latest code to GitHub and connect the repository in Render.
2. Create a new Web Service (or Blueprint), set build command to `pip install -r requirements.txt`.
3. Set start command to `gunicorn readwise.wsgi`.
4. Add all required environment variables from the list below.
5. Run `python manage.py migrate` and `python manage.py collectstatic --noinput`.
6. Deploy and verify `/`, `/login/`, and recommendation endpoints.

## PythonAnywhere Deployment Steps
1. Create a Python web app (manual config, supported Python version).
2. Clone repository, create virtual environment, install dependencies.
3. Configure WSGI file to load project path and `readwise.wsgi`.
4. Add environment variables in your PythonAnywhere environment file.
5. Run `python manage.py migrate` and `python manage.py collectstatic --noinput`.
6. Configure static files mapping, reload web app, then validate login and recommendations.

## Required Environment Variables
- `SECRET_KEY`
- `DEBUG=False`
- `IS_PRODUCTION=True`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `SITE_BASE_URL`
- `DATABASE_URL` (Render/Postgres) or SQLite path (PythonAnywhere)
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_BOOKS_API_KEY`

## Google OAuth Setup
1. Open Google Cloud Console and select the correct project.
2. Go to APIs & Services -> Credentials -> OAuth 2.0 Client ID.
3. Add authorized redirect URI: `https://<your-domain>/accounts/oauth2callback/`.
4. Copy client ID and secret into environment variables.
5. Ensure `GOOGLE_REDIRECT_URI` exactly matches the registered URI.

## Common Errors and Fixes
1. `DisallowedHost`: add your exact domain to `ALLOWED_HOSTS`.
2. CSRF verification failed: set full `https://` origin in `CSRF_TRUSTED_ORIGINS`.
3. OAuth redirect mismatch: make Google Console redirect URI and `GOOGLE_REDIRECT_URI` identical.
