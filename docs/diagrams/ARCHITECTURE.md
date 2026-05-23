# ReadWise Architecture Diagram

## System Architecture Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                           │
├──────────────────────────────────────────────────────────────────────────┤
│  Web Browser (React/Vue)          │      Mobile App (React Native)      │
│  ├─ Dashboard                     │      ├─ Book Discovery             │
│  ├─ Recommendation Page           │      ├─ Mood Input                 │
│  ├─ Profile Management            │      ├─ Recommendations            │
│  └─ Admin Panel                   │      └─ Profile                    │
└────────────────────┬──────────────────────────┬─────────────────────────┘
                     │ HTTPS/REST API          │
        ┌────────────▼──────────────────────────▼──────────────┐
        │          DJANGO REST FRAMEWORK (DRF)                 │
        │                                                      │
        │  ┌──────────────┬──────────────┬───────────────┐    │
        │  │ Auth         │ Books        │ Recommendations│   │
        │  │ Endpoints    │ Endpoints    │ Endpoints     │    │
        │  └──────────────┴──────────────┴───────────────┘    │
        └────┬───────────────────────────┬───────────────────┘
             │                           │
   ┌─────────▼──────────┐   ┌───────────▼─────────────┐
   │  SERVICE LAYER     │   │   ML/AI PIPELINE        │
   │                    │   │                         │
   │ ├─ Auth Service    │   │ ├─ Sentiment Analysis  │
   │ ├─ Book Service    │   │ ├─ Emotion Detection   │
   │ ├─ Rec Service     │   │ ├─ Semantic Similarity │
   │ └─ User Service    │   │ └─ Embeddings          │
   └─────────┬──────────┘   └───────────┬─────────────┘
             │                          │
        ┌────▼──────────────────────────▼─────┐
        │      DATA LAYER & CACHING            │
        │                                      │
        │  ┌────────────────────────────────┐ │
        │  │  PostgreSQL Database           │ │
        │  │  ├─ Users Table               │ │
        │  │  ├─ Books Table              │ │
        │  │  ├─ Recommendations Table    │ │
        │  │  └─ Ratings Table            │ │
        │  └────────────────────────────────┘ │
        │                                      │
        │  ┌────────────────────────────────┐ │
        │  │  Redis Cache                   │ │
        │  │  ├─ User Sessions             │ │
        │  │  ├─ Book Cache                │ │
        │  │  └─ Recommendation Cache      │ │
        │  └────────────────────────────────┘ │
        └─────────────────────────────────────┘
                          │
        ┌─────────────────▼──────────────────┐
        │    ASYNC TASK PROCESSING            │
        │          (Celery + Redis)           │
        │                                     │
        │  ├─ Background Jobs                │
        │  ├─ Model Training                 │
        │  ├─ Data Processing                │
        │  └─ Email Notifications            │
        └─────────────────────────────────────┘
```

## Database Schema

```
┌─────────────────────┐
│       USER          │
├─────────────────────┤
│ id (PK)             │
│ username            │
│ email               │
│ password_hash       │
│ google_id           │
│ created_at          │
│ updated_at          │
└─────────────────────┘
         │ 1:N
         │
         └─────────────────────────┐
                                   │
┌─────────────────────┐   ┌────────▼──────────┐
│       BOOK          │   │ READING_HISTORY   │
├─────────────────────┤   ├────────┬──────────┤
│ id (PK)             │   │ id (PK)│
│ title               │   │ user_id(FK)
│ author              │   │ book_id(FK)
│ description         │   │ status
│ genre               │   │ rating
│ rating              │   │ date_added
│ cover_image         │   │ date_completed
│ isbn                │   └────────────────────┘
│ created_at          │
└─────────────────────┘
         │ 1:N
         │
         └─────────────────────────┐
                                   │
                    ┌──────────────▼──────────────┐
                    │ RECOMMENDATION             │
                    ├────────────────────────────┤
                    │ id (PK)                    │
                    │ user_id (FK)              │
                    │ book_id (FK)              │
                    │ algorithm_type            │
                    │ score                     │
                    │ reason                    │
                    │ created_at                │
                    └────────────────────────────┘
```

## Recommendation Algorithm Flow

```
User Input
    │
    ├─────────────────────────────────────┐
    │                                     │
    ▼                                     ▼
Text Input                          Mood Selection
"I'm feeling                         Happy / Sad /
 contemplative"                      Excited / Calm
    │                                     │
    └──────────────────┬──────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ NLP Processing       │
            │                      │
            │ • Tokenization       │
            │ • Embedding          │
            │ • Sentiment Analysis │
            └──────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    Sentiment      Emotion        Mood
    Scores         Scores         Analysis
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ Book Matching        │
            │                      │
            │ • Semantic Search    │
            │ • Similarity Score   │
            │ • Ranking            │
            └──────────────────────┘
                       │
        ┌──────────────┼──────────────────┐
        │              │                  │
        ▼              ▼                  ▼
    Content-Based  Collaborative  Personalized
    Filtering      Filtering      Filtering
        │              │                  │
        └──────────────┼──────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ Result Aggregation   │
            │ & Ranking            │
            └──────────────────────┘
                       │
                       ▼
            Top 10 Book Recommendations
            (Sorted by Score)
```

## API Response Flow

```
Client Request
    │
    ├─ GET /api/recommendations/by-mood/
    │  payload: { mood: "happy", limit: 10 }
    │
    ▼
┌──────────────────────────────────────┐
│ Django View Layer                    │
│ • Validate request                   │
│ • Check authentication               │
│ • Parse parameters                   │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ Business Logic Layer                 │
│ • Call recommendation service        │
│ • Run ML pipeline                    │
│ • Score & rank results               │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ Data Layer                           │
│ • Query database                     │
│ • Apply filters                      │
│ • Cache results                      │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ Response Serialization               │
│ • Format as JSON                     │
│ • Include metadata                   │
│ • Add pagination                     │
└──────────────────────────────────────┘
    │
    ▼
HTTP 200 Response
{
  "recommendations": [
    {
      "id": 1,
      "title": "...",
      "score": 0.95,
      ...
    }
  ],
  "count": 10,
  "total_available": 45
}
```

## ML Model Pipeline

```
Input Text/Mood
    │
    ▼
┌─────────────────────────────────────────┐
│  TOKENIZATION & PREPROCESSING           │
│  • Remove special chars                 │
│  • Convert to lowercase                 │
│  • Tokenize into words                  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  EMBEDDING GENERATION                   │
│  Model: Sentence Transformers           │
│  Output: 384-dimensional vector         │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  SENTIMENT ANALYSIS                     │
│  Model: DistilBERT (SST-2)             │
│  Output: Positive/Negative Score        │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  EMOTION DETECTION                      │
│  Model: RoBERTa (6-class)              │
│  Output: Joy, Sadness, Anger, ...       │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  SEMANTIC SIMILARITY MATCHING            │
│  • Compute cosine similarity            │
│  • Against all books embeddings         │
│  • Rank by similarity score             │
└─────────────────────────────────────────┘
    │
    ▼
Recommendation Results
(Ranked by relevance score)
```

---

**Last Updated**: May 23, 2026
