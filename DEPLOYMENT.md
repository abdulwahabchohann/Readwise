# ReadWise Deployment Guide

## Project Overview
ReadWise is a Django platform for mood-based book recommendations and Google OAuth login.
It is deployed on Render or PythonAnywhere using environment-driven configuration.

## Render Deployment Steps
1. Push the latest code to GitHub and connect the repository in Render.
2. Create a Web Service and set build command to `pip install -r requirements.txt`.
3. Set start command to `gunicorn readwise.wsgi`.
4. Add required environment variables from the list below.
5. Run migrations and static collection: `python manage.py migrate` and `python manage.py collectstatic --noinput`.
6. Deploy and confirm home, login, and recommendation endpoints are working.

## PythonAnywhere Deployment Steps
1. Create a Python web app with manual configuration.
2. Clone the repository, create a virtual environment, and install dependencies.
3. Configure WSGI to load project path and `readwise.wsgi`.
4. Add required environment variables in the server environment file.
5. Run migrations and static collection.
6. Configure static mapping, reload the app, and verify core pages and auth flow.

## Required Environment Variables
- `SECRET_KEY`
- `DEBUG=False`
- `IS_PRODUCTION=True`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `SITE_BASE_URL`
- `DATABASE_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_BOOKS_API_KEY`

## Google OAuth Setup
1. Open Google Cloud Console and select the correct project.
2. Go to APIs and Services, then Credentials.
3. Open your OAuth Client ID and add redirect URI `https://<domain>/accounts/oauth2callback/`.
4. Save and copy client ID and secret into environment variables.
5. Ensure `GOOGLE_REDIRECT_URI` exactly matches the saved redirect URI.

## Common Errors and Fixes
1. `DisallowedHost`: add the exact deployment domain to `ALLOWED_HOSTS`.
2. CSRF errors: set full HTTPS origin in `CSRF_TRUSTED_ORIGINS`.
3. OAuth mismatch: make redirect URI in Google Console and app settings identical.
