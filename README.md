# ReadWise — AI-Powered Book Recommendation System

## 📚 About

ReadWise is an intelligent book recommendation system that leverages artificial intelligence and natural language processing to match readers with books based on their current mood, emotional state, and reading preferences. The system uses advanced transformer-based models for sentiment and emotion detection, combined with semantic similarity algorithms to provide personalized recommendations.

### Project Type
**Final Year Project** - A comprehensive full-stack AI/ML application demonstrating advanced backend engineering, machine learning integration, and web technologies.

---

## ✨ Key Features

### 🎯 Core Recommendation Engine
- **Mood-Based Recommendations**: Analyze user emotional state and recommend matching books
- **Sentiment Analysis**: Advanced NLP-powered sentiment detection using transformer models
- **Semantic Similarity**: Find books semantically similar to user preferences using Sentence Transformers
- **Collaborative Filtering**: Recommend books based on similar users' preferences
- **Content-Based Filtering**: Match books by metadata, genre, and themes

### 👤 User Management
- **Google OAuth Integration**: Secure authentication via Google Sign-In
- **User Profiles**: Store reading history, preferences, and mood states
- **Personalization**: Track user interactions to improve recommendations over time
- **Reading History**: Maintain complete history of viewed and rated books

### 🔧 Technical Features
- **REST API**: Comprehensive API for mobile/frontend integration
- **Admin Dashboard**: Django admin for content management
- **Database Management**: Efficient data storage and retrieval
- **Caching Layer**: Redis-based caching for performance optimization
- **Background Tasks**: Celery for async processing

### 📊 Data & ML
- **100K+ Book Dataset**: Comprehensive book catalog with metadata
- **Book Covers**: Visual representation with book cover images
- **ML Models**: Pre-trained transformer models for analysis
- **Data Pipeline**: Automated data processing and validation

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.2
- **API**: Django REST Framework (DRF)
- **Task Queue**: Celery with Redis
- **Database**: SQLite (development), PostgreSQL (production)

### Machine Learning & NLP
- **HuggingFace Transformers**: Pre-trained models for sentiment/emotion analysis
- **Sentence Transformers**: Semantic similarity and embeddings
- **Scikit-learn**: Machine learning utilities and algorithms
- **NumPy/Pandas**: Data processing and analysis

### Authentication & Security
- **OAuth 2.0**: Google Sign-In via django-allauth
- **JWT**: Token-based authentication
- **CORS**: Cross-origin resource sharing

### Deployment
- **Development**: Local Django server
- **Production**: Render / PythonAnywhere
- **Containerization**: Docker-ready configuration

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.9+
- pip or conda
- Virtual environment (venv or conda)
- Git

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/abdulwahabchohann/Readwise.git
cd Readwise
```

#### 2. Create Virtual Environment
```bash
# Using venv
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and fill in your values
```

#### 5. Database Setup
```bash
# Create migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# Load initial data (optional)
python manage.py loaddata initial_data.json
```

#### 6. Run Development Server
```bash
python manage.py runserver
# Server runs at http://localhost:8000
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/readwise_db

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Email Configuration (for notifications)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Redis (for caching & Celery)
REDIS_URL=redis://localhost:6379/0

# ML Model Settings
MODEL_CACHE_DIR=./models
```

---

## 🏗️ Project Structure

```
readwise/
├── accounts/                          # User authentication & profiles
│   ├── models.py                      # User profile models
│   ├── views.py                       # API endpoints
│   ├── serializers.py                 # DRF serializers
│   ├── services/
│   │   ├── sentiment_analysis.py      # Sentiment detection
│   │   ├── mood_recommender.py        # Mood-based recommendations
│   │   ├── dataset_recommender.py     # Content-based recommendations
│   │   ├── recommendation_facade.py   # Unified recommendation logic
│   │   └── cover_utils.py             # Book cover handling
│   ├── management/commands/           # Custom Django commands
│   └── tests.py                       # Unit tests
│
├── readwise/                          # Main Django app config
│   ├── settings.py                    # Django settings
│   ├── urls.py                        # URL routing
│   ├── wsgi.py                        # WSGI config
│   └── celery.py                      # Celery configuration
│
├── data/                              # Dataset files
│   └── books_dataset_*.json           # Book catalog data
│
├── scripts/                           # Utility scripts
│   ├── analyze_books.py               # Book analysis
│   ├── export_books_dataset.py        # Data export
│   └── sentiment_analyzer.py          # Standalone sentiment analysis
│
├── tests/                             # Test suite
│   ├── test_recommendations_flow.py   # E2E tests
│   ├── test_accounts.py               # User tests
│   └── test_sentiment_analyzer.py     # ML model tests
│
├── manage.py                          # Django management script
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── db.sqlite3                         # SQLite database (dev)
└── README.md                          # This file
```

---

## 🚀 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/google/` - Google OAuth login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/user/` - Get current user profile

### Books
- `GET /api/books/` - List all books
- `GET /api/books/{id}/` - Book details
- `GET /api/books/search/?q=query` - Search books

### Recommendations
- `POST /api/recommendations/by-mood/` - Get recommendations by mood
- `POST /api/recommendations/by-sentiment/` - Sentiment-based recommendations
- `GET /api/recommendations/personalized/` - User-personalized recommendations
- `GET /api/recommendations/history/` - User's recommendation history

### User Profile
- `GET /api/profile/` - Get user profile
- `PUT /api/profile/` - Update profile
- `GET /api/profile/reading-history/` - Reading history
- `POST /api/profile/rate-book/` - Rate a book

---

## 🤖 Machine Learning Models

### Sentiment Analysis
- **Model**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Purpose**: Detect text sentiment (positive/negative)
- **Input**: User text, book descriptions
- **Output**: Sentiment score (0-1), label

### Emotion Detection
- **Model**: `j-hartmann/emotion-english-distilroberta-base`
- **Purpose**: Detect 6 emotions (joy, sadness, anger, fear, surprise, neutral)
- **Input**: User text, reviews
- **Output**: Emotion probabilities

### Semantic Similarity
- **Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Purpose**: Calculate semantic similarity between books and user preferences
- **Input**: Book descriptions, user preferences
- **Output**: Similarity scores

---

## 📊 Recommendation Algorithms

### 1. Mood-Based Recommendation
Analyzes user's current mood and emotional state, then matches with books that fit that mood.

### 2. Sentiment Analysis Recommendation
Processes user text input to understand sentiment and recommends books with matching tone.

### 3. Collaborative Filtering
Recommends books based on what similar users have read and rated.

### 4. Content-Based Filtering
Matches users with books based on metadata, genre, themes, and descriptions.

### 5. Hybrid Approach
Combines multiple algorithms for diverse and accurate recommendations.

---

## 📈 Dataset Information

- **Total Books**: 100,000+
- **Data Fields**: Title, Author, Genre, Description, Rating, Cover Image
- **Book Covers**: Visual imagery for each book
- **Metadata**: Genre, publication year, language
- **Reviews**: User ratings and feedback

Dataset file: `data/books_dataset_100k_real_covers.json`

---

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_recommendations_flow.py -v
```

### Run with Coverage
```bash
pytest --cov=accounts --cov=readwise tests/
```

### Test ML Models
```bash
python tests/test_sentiment_analyzer.py
```

---

## 🚀 Deployment

### Development Deployment
```bash
python manage.py runserver 0.0.0.0:8000
```

### Production Deployment (Render)
See `DEPLOYMENT.md` and `TECHNICAL_DEPLOYMENT.md` for detailed instructions.

### Key Deployment Files
- `render.yaml` - Render deployment configuration
- `requirements-pythonanywhere.txt` - PythonAnywhere dependencies
- `DEPLOYMENT.md` - Deployment guide
- `DEPLOYMENT_GUIDE.md` - Detailed deployment instructions

---

## 📋 Important Files

- **QUICKSTART.md** - Quick start guide for rapid setup
- **TECHNICAL_DEPLOYMENT.md** - Technical deployment details
- **DEPLOYMENT.md** - Production deployment instructions
- **RECOMMENDATION_ENGINE_SUMMARY.md** - ML engine documentation
- **requirements.txt** - All Python dependencies

---

## 🔄 Development Workflow

### Start Development
```bash
# Windows
StartDevelopment.bat

# Linux/Mac
./StartDevelopment.sh
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database
python manage.py flush
```

### Custom Management Commands
```bash
# Check recommendation readiness
python manage.py check_recommendation_readiness

# Backfill book covers
python manage.py backfill_book_covers

# Export dataset
python manage.py export_books_dataset
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💻 Author

**Abdul Wahab**
- GitHub: [@abdulwahabchohann](https://github.com/abdulwahabchohann)
- Email: your_email@example.com

---

## 📞 Support & Contact

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact the development team
- Check existing documentation

---

## 🎯 Roadmap

- [ ] Mobile app support (React Native)
- [ ] Advanced recommendation personalization
- [ ] Social features (book clubs, friend recommendations)
- [ ] Multi-language support
- [ ] Enhanced analytics dashboard
- [ ] Recommendation explanation feature

---

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [HuggingFace Transformers](https://huggingface.co/transformers/)
- [Sentence Transformers](https://www.sbert.net/)
- [Google OAuth Documentation](https://developers.google.com/identity)

---

**Last Updated**: May 23, 2026
**Version**: 1.0.0



