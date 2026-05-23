# ReadWise - Technical Deployment Guide for Production

## 🚀 QUICK START: Deploy to Production in 45 Minutes

### Option A: Deploy to PythonAnywhere (RECOMMENDED - Best Value) ⭐

#### Step 1: Create Account
1. Go to https://www.pythonanywhere.com
2. Sign up (use FREE tier to start)
3. Complete setup wizard

#### Step 2: Upload Code
```bash
# In PythonAnywhere Web Console:
git clone https://github.com/YOUR_USERNAME/readwise.git
cd readwise
```

#### Step 3: Create Virtual Environment
```bash
mkvirtualenv readwise --python=/usr/bin/python3.10
pip install -r requirements.txt
```

#### Step 4: Configure Web App
1. PythonAnywhere Dashboard → Web → Add a new web app
2. Select "Manual configuration" → Python 3.10
3. Set WSGI file: `/home/YOUR_USERNAME/readwise/readwise/wsgi.py`
4. Source code path: `/home/YOUR_USERNAME/readwise`

#### Step 5: Update WSGI Configuration File
Edit the WSGI file shown on the Web tab:
```python
import os
import sys

path = '/home/YOUR_USERNAME/readwise'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'readwise.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### Step 6: Set Environment Variables
In PythonAnywhere Web app settings, set:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourname.pythonanywhere.com
IS_PRODUCTION=True
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
SENDGRID_API_KEY=SG.your-key
SENDGRID_FROM_EMAIL=noreply@readwise.app
```

#### Step 7: Reload & Deploy
1. Click "Reload Web App" button
2. Visit your site: https://yourname.pythonanywhere.com
3. Test functionality

**Cost**: FREE (tier) → $5/month when you have users  
**Uptime**: 99.9%  
**Domain**: https://yourname.pythonanywhere.com
**Best for**: Getting started with zero budget

---

### Option B: Deploy to Render.com (If you prefer AWS infrastructure)

#### Step 1: Prepare Repository
```bash
# On your local machine
git init
git add .
git commit -m "Initial commit: ReadWise production ready"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/readwise.git
git push -u origin main
```

#### Step 2: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Name: `readwise`
6. Region: `Ohio` (US East)

#### Step 3: Configure Build Settings
```
Build Command: pip install -r requirements.txt && python manage.py collectstatic --noinput

Start Command: gunicorn readwise.wsgi:application --bind 0.0.0.0:$PORT
```

#### Step 4: Add Environment Variables
(Same as PythonAnywhere above)

#### Step 5: Deploy
```bash
git push origin main
# Render auto-deploys! Check dashboard for status
```

**Cost**: FREE (tier with spin-down) → $7/month hosting + $7/month database = $14/month when paid  
**Uptime**: 99.99% (paid) but free tier spins down  
**Domain**: https://readwise-prod.onrender.com
**Best for**: Production apps that need high availability

---

## 💳 PAYMENT PROCESSING (Stripe Integration)

### Step 1: Install Stripe Package
```bash
pip install stripe django-stripe-payments
```

### Step 2: Update requirements.txt (Add these lines)
```
stripe>=5.0.0
stripe-payments>=0.2.0
```

### Step 3: Create Subscription Model
Create `accounts/models.py` additions:

```python
from django.db import models
from django.contrib.auth.models import User
import stripe

class Subscription(models.Model):
    TIER_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='free')
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    monthly_recommendations = models.IntegerField(default=3)
    used_recommendations = models.IntegerField(default=0)
    reset_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_recommendations_left(self):
        return self.used_recommendations < self.monthly_recommendations

    def is_premium(self):
        return self.tier == 'premium'
```

### Step 4: Create Payment Views
```python
# accounts/views.py - Add these

from django.views.decorators.http import require_POST
from django.http import JsonResponse
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

@require_POST
def create_subscription(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    # Create Stripe customer
    customer = stripe.Customer.create(
        email=user.email,
        metadata={'user_id': user.id}
    )
    
    # Create subscription
    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[{'price': 'price_1A2B3C4D5E6F7G'}],  # Your Premium plan price ID
    )
    
    # Save to database
    user_subscription = Subscription.objects.get_or_create(user=user)[0]
    user_subscription.tier = 'premium'
    user_subscription.stripe_customer_id = customer.id
    user_subscription.stripe_subscription_id = subscription.id
    user_subscription.monthly_recommendations = float('inf')  # Unlimited
    user_subscription.save()
    
    return JsonResponse({'success': True, 'subscription_id': subscription.id})


@require_POST
def webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    
    if event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        user_sub = Subscription.objects.filter(
            stripe_subscription_id=subscription.id
        ).first()
        if user_sub:
            user_sub.tier = 'free'
            user_sub.save()
    
    return JsonResponse({'status': 'success'})
```

### Step 5: Create Checkout Page
```html
<!-- accounts/templates/checkout.html -->
<form id="payment-form">
  {% csrf_token %}
  <script
    src="https://js.stripe.com/v3/"
    data-api-key="{{ stripe_public_key }}"
  ></script>
  
  <div id="card-element"></div>
  <button type="submit" id="submit">Subscribe for $9.99/month</button>
</form>

<script>
const stripe = Stripe(document.querySelector('[data-api-key]').dataset.apiKey);
const elements = stripe.elements();
const cardElement = elements.create('card');
cardElement.mount('#card-element');

document.getElementById('payment-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const {token} = await stripe.createToken(cardElement);
  
  fetch('/accounts/subscribe/', {
    method: 'POST',
    body: JSON.stringify({token: token.id}),
    headers: {'Content-Type': 'application/json'}
  });
});
</script>
```

### Step 6: Add URLs
```python
# accounts/urls.py - Add these patterns
urlpatterns += [
    path('subscribe/', views.create_subscription, name='subscribe'),
    path('webhook/stripe/', views.webhook, name='stripe-webhook'),
]
```

---

## 📧 EMAIL SERVICE SETUP (SendGrid)

### Step 1: Create SendGrid Account
- Go to https://sendgrid.com
- Sign up (free: 40K emails/month)
- Generate API key

### Step 2: Install Package
```bash
pip install sendgrid django-anymail
```

### Step 3: Configure Settings
```python
# readwise/settings.py

EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'

ANYMAIL = {
    'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
}

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@readwise.app')
```

### Step 4: Send Welcome Email
```python
from django.core.mail import send_mail

def send_welcome_email(user):
    send_mail(
        subject='Welcome to ReadWise!',
        message=f'Hi {user.first_name}, start discovering books based on your mood!',
        from_email='noreply@readwise.app',
        recipient_list=[user.email],
    )
```

---

## 📊 ANALYTICS SETUP (Google Analytics 4)

### Step 1: Create GA4 Property
- Go to https://analytics.google.com
- Create new property for ReadWise
- Get Measurement ID: `G-XXXXXXXXXX`

### Step 2: Add to Base Template
```html
<!-- templates/base.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Step 3: Track Events
```python
# accounts/views.py
def recommendations(request):
    # Track conversion
    ga_event = {
        'event': 'get_recommendations',
        'mood': mood,
        'result_count': 3,
    }
    # Send to GA via JavaScript event
```

---

## 🔐 SECURITY CHECKLIST

Before production deployment:

```bash
# 1. Check for hardcoded secrets
grep -r "password" . --include="*.py"
grep -r "SECRET" . --include="*.py"

# 2. Security check
python manage.py check --deploy

# 3. Update security headers
# In readwise/settings.py:
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

---

## 🔧 DATABASE MIGRATION GUIDE

### Initial Production Setup
```bash
# Render/PythonAnywhere provides database
# Run migrations on deployment:
python manage.py migrate

# Create superuser for admin
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### Backup Strategy
```bash
# Weekly backups (set up via Render dashboard)
# Or manual:
python manage.py dumpdata > backup.json

# Restore if needed:
python manage.py loaddata backup.json
```

---

## 📋 PRE-LAUNCH CHECKLIST

- [ ] Domain name registered (readwise.app or similar)
- [ ] SSL certificate (auto via Render)
- [ ] Environment variables all set
- [ ] Database migrations tested
- [ ] Stripe account active
- [ ] SendGrid account active
- [ ] Google Analytics installed
- [ ] Privacy policy page created
- [ ] Terms of service page created
- [ ] GDPR compliance reviewed
- [ ] Payment processing tested (test card: 4242 4242 4242 4242)
- [ ] Email sending tested
- [ ] Error logging set up (e.g., Sentry)

---

## 🔍 MONITORING & MAINTENANCE

### Essential Monitoring Tools (Free tier):
- **Uptime**: UptimeRobot (monitors your site 24/7)
- **Error tracking**: Sentry (Django integration)
- **Performance**: NewRelic Free Tier

### Setup Sentry for Error Tracking
```python
# pip install sentry-sdk
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)
```

---

## 💰 PRODUCTION COSTS BREAKDOWN

### Bare Minimum Setup (PythonAnywhere FREE):
```
PythonAnywhere hosting:    $0/month (FREE tier)
Domain name:               $0/month (use pythonanywhere.com subdomain)
Stripe fees:               2.2% + $0.30 per transaction
SendGrid:                  FREE (40K/month)
Google Analytics:          FREE
Total fixed:               $0/month

+ Variable costs:
- 50 premium users × $9.99 = $499.50 gross
- Stripe fee (2.2% + $0.30): ~$11/month
- = $488.50 net profit
- Breakeven: 3-5 premium users
```

### When You Hit $500/month Revenue (PythonAnywhere PAID):
```
PythonAnywhere hosting:    $5/month
Domain name:               $12/year ($1/month)
Stripe fees:               2.2% + $0.30 per transaction (auto)
SendGrid:                  FREE (or $10-20 if beyond 40K/month)
Total fixed:               $6/month

= Still only 1% of revenue! Easy to sustain.
```

### Scaling Budget (10K users/month, need PythonAnywhere Pro):
```
PythonAnywhere Pro:        $50/month (for better resources)
Domain:                    $12/year
Email volume:              $20/month (beyond free tier)
Analytics:                 FREE
Support staff:             $500/month (1 person)
Marketing:                 $200-1000/month
Total:                     $770-1,560/month

= Still very profitable at 8K-10K users with premium + affiliate
```

---

## ✅ RECOMMENDED DEPLOYMENT SEQUENCE

1. **Day 1**: Deploy to Render.com (30 min)
2. **Day 2**: Set up Stripe payments (2 hours)
3. **Day 3**: Add email notifications (1 hour)
4. **Day 4**: Install analytics (30 min)
5. **Day 5**: Set up affiliate links (1 hour)
6. **Day 6**: Security audit & hardening (2 hours)
7. **Day 7**: Launch to public! 🎉

**Total time: ~10 hours of work**

---

## 🚨 TROUBLESHOOTING

### Deployment Won't Start
```bash
# Check logs
render logs  # Render dashboard
# Common issue: Missing environment variable
# Solution: Add in Render dashboard
```

### Stripe Not Working
```bash
# Test webhook
curl -X POST http://localhost:8000/webhook/stripe/ \
  -d 'payload=...'
# Check Stripe Dashboard for webhook logs
```

### Email Not Sending
```bash
# Check SendGrid API key
python -c "import sendgrid; print('OK')"
# Send test email
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])
```

---

## 📞 SUPPORT RESOURCES

- **Render Docs**: https://render.com/docs
- **Stripe API**: https://stripe.com/docs/api
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/
- **SendGrid**: https://docs.sendgrid.com/

---

**Ready to launch? Start with Option A (Render) - it's the fastest path to revenue!**
