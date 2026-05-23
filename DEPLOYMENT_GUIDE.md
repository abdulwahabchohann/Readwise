# READWISE Deployment Guide

This document provides step-by-step instructions for deploying ReadWise to different platforms.

---

## Table of Contents
1. [Pre-Deployment Requirements](#pre-deployment-requirements)
2. [Local Testing](#local-testing)
3. [Deployment Options](#deployment-options)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Requirements

### System Requirements
- Python 3.10+
- 500 MB disk space minimum
- 2 GB RAM recommended
- Internet connection (for downloading dependencies and ML models)

### Files Required
- `books_dataset_100k_real_covers.json` (48.62 MB)
- `db.sqlite3` (448 KB)
- All Python source files
- Static files (CSS, images, JS)

### Dependencies
```bash
pip install -r requirements.txt
```

---

## Local Testing

### 1. Run Deployment Tests
```bash
cd /path/to/final-year-project
source venv/bin/activate
python DEPLOYMENT_TESTS.py
```

**Expected Output:**
```
STATUS: ✅ DEPLOYMENT READY
✅ Passed: 7/7
```

### 2. Test Recommendation Engine
```bash
python manage.py runserver
```

Visit: `http://localhost:8000/recommendations/`

Test with sample prompts:
- "I'm feeling happy"
- "Stressed and anxious"
- "Sad and need comfort"

---

## Deployment Options

### Option 1: PythonAnywhere (Recommended for Beginners)

#### Steps:
1. Create PythonAnywhere account (pythonanywhere.com)
2. Upload project files
3. Create Python web app
4. Configure virtual environment
5. Set environment variables

#### Configuration:
```python
# In /var/www/[username]_pythonanywhere_com_wsgi.py
import os
import sys
path = '/home/[username]/mysite'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'readwise.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### After Deployment:
- Navigate to Web tab
- Set Python version to 3.x
- Set WSGI configuration file
- Add static files mapping: `/static/` -> `/home/[username]/mysite/staticfiles/`
- Reload web app

### Option 2: Heroku

#### Prerequisites:
```bash
# Install Heroku CLI
brew install heroku/brew/heroku
heroku login
```

#### Steps:
```bash
# Create Heroku app
heroku create readwise-app

# Set environment variables
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=[generate-random-key]
heroku config:set ALLOWED_HOSTS=readwise-app.herokuapp.com

# Add Procfile
echo "web: gunicorn readwise.wsgi" > Procfile

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Collect static files
heroku run python manage.py collectstatic --noinput
```

### Option 3: Docker (Production)

#### Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run server
CMD ["gunicorn", "readwise.wsgi:application", "--bind", "0.0.0.0:8000"]
```

#### Deploy:
```bash
docker build -t readwise .
docker run -p 8000:8000 readwise
```

### Option 4: DigitalOcean / AWS / Google Cloud

#### Basic Steps:
1. Create Ubuntu server (18.04+)
2. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3.10 python3.10-venv nginx
   ```

3. Clone repository:
   ```bash
   git clone [your-repo-url] /var/www/readwise
   cd /var/www/readwise
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

6. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

7. Create systemd service:
   ```bash
   sudo nano /etc/systemd/system/readwise.service
   ```

   Content:
   ```ini
   [Unit]
   Description=ReadWise Application
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/readwise
   ExecStart=/var/www/readwise/venv/bin/gunicorn \
       --bind 0.0.0.0:8000 \
       --workers 4 \
       readwise.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

8. Start service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start readwise
   sudo systemctl enable readwise
   ```

9. Configure Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/readwise
   ```

   Content:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location /static/ {
           alias /var/www/readwise/staticfiles/;
       }

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

10. Enable site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/readwise /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

---

## Post-Deployment Verification

### 1. Health Check
```bash
# Test home page
curl https://your-domain.com/

# Test recommendations page
curl https://your-domain.com/recommendations/
```

### 2. Run Deployment Tests
```bash
python DEPLOYMENT_TESTS.py
```

### 3. Test Functionality
1. Visit: `https://your-domain.com/recommendations/`
2. Enter a mood: "I'm feeling happy"
3. Click "Get Recommendations"
4. Verify results display with book covers

### 4. Check Logs
```bash
# PythonAnywhere
tail -f /var/log/[username].pythonanywhere.com.log

# Self-hosted
journalctl -u readwise -f

# Docker
docker logs -f [container-id]
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'django'"

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "No such table: accounts_book"

**Solution:**
```bash
python manage.py migrate
```

### Issue: "Static files not loading"

**Solution:**
```bash
python manage.py collectstatic --noinput
```

### Issue: "DEBUG = True in production"

**Solution:**
Set environment variable:
```bash
export DEBUG=False
```

Or in settings.py:
```python
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
```

### Issue: "Slow performance on first request"

**Reason:** ML models loading for first time

**Solution:** Models cache after first load

---

## Monitoring & Maintenance

### Regular Tasks
- Weekly: Check error logs
- Monthly: Update dependencies
- Quarterly: Update dataset
- Annually: Security audit

### Backup Strategy
```bash
# Daily backup
0 0 * * * /home/backup_db.sh

# Database backup script
#!/bin/bash
cp /path/to/db.sqlite3 /backups/db_$(date +%Y%m%d).sqlite3
```

### Updates & Patches
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Deploy changes
git pull origin main
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart readwise
```

---

## Performance Optimization (Production)

### 1. Enable Caching
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 2. CDN Setup
- Upload static files to CloudFront/CloudFlare
- Update STATIC_URL to CDN URL

### 3. Database Optimization
```sql
-- Create indexes for faster queries
CREATE INDEX idx_book_title ON accounts_book(title);
CREATE INDEX idx_book_isbn ON accounts_book(isbn_13);
```

### 4. Load Balancing
- Deploy multiple app instances
- Use Nginx for load balancing
- Configure sticky sessions if needed

---

## Support & Rollback

### Need to Rollback?
```bash
# Revert to previous version
git revert [commit-hash]

# Or reset to previous tag
git checkout [tag-name]

# Restore database from backup
cp /backups/db_latest.sqlite3 db.sqlite3

# Restart service
systemctl restart readwise
```

---

**Deployment Status:** ✅ Ready for Production

For questions or issues, refer to DEPLOYMENT_READY_REPORT.md
