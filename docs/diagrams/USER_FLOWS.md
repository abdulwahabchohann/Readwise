# User Journey & Feature Flows

## Complete User Journey

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        READWISE USER JOURNEY                            │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   NEW VISITOR    │
└────────┬─────────┘
         │
         ▼
    ┌────────────────────┐
    │ Landing Page       │
    │ • Feature overview │
    │ • Sign up CTA      │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ Sign Up / Login    │
    │ • Email/Password   │
    │ • Google OAuth     │
    └────────┬───────────┘
             │
             ├─ Already Registered ──┐
             │                       │
             └─ New User ────┐       │
                             │       │
                             ▼       ▼
                    ┌─────────────────────┐
                    │ User Profile Setup  │
                    │ • Select genres     │
                    │ • Choose interests  │
                    │ • Set preferences   │
                    └────────┬────────────┘
                             │
                             ▼
    ┌────────────────────────────────────────┐
    │        MAIN DASHBOARD                  │
    │                                        │
    │  ┌──────────────────────────────────┐ │
    │  │ Personalized Recommendations     │ │
    │  │ • Based on mood                  │ │
    │  │ • Based on preferences           │ │
    │  │ • Trending books                 │ │
    │  └──────────────────────────────────┘ │
    │                                        │
    │  ┌──────────────────────────────────┐ │
    │  │ Book Discovery                   │ │
    │  │ • Search                         │ │
    │  │ • Browse by genre                │ │
    │  │ • Filter & sort                  │ │
    │  └──────────────────────────────────┘ │
    │                                        │
    │  ┌──────────────────────────────────┐ │
    │  │ Quick Mood Search                │ │
    │  │ • Enter current mood/text        │ │
    │  │ • Get instant recommendations    │ │
    │  └──────────────────────────────────┘ │
    └────────┬───────────────────┬──────────┘
             │                   │
             ├─ Select Book      ├─ Enter Mood
             │                   │
             ▼                   ▼
    ┌─────────────────┐  ┌──────────────────┐
    │ Book Detail     │  │ Mood Analysis    │
    │ • Description   │  │ • Process input  │
    │ • Reviews       │  │ • Detect emotion │
    │ • Rating        │  │ • Get recs       │
    │ • Add to list   │  └────────┬─────────┘
    │ • Rate/Review   │           │
    └────────┬────────┘           │
             │                    │
             └────────┬───────────┘
                      │
                      ▼
    ┌────────────────────────────────┐
    │ Recommendation Results         │
    │ • Ranked by relevance         │
    │ • Score explanation           │
    │ • Add to reading list         │
    │ • Rate recommendation         │
    └────────┬─────────────────────┘
             │
             ▼
    ┌────────────────────────────────┐
    │ My Reading List                │
    │ • Books to read               │
    │ • Currently reading           │
    │ • Completed books             │
    │ • Want to read               │
    └────────┬─────────────────────┘
             │
             ▼
    ┌────────────────────────────────┐
    │ Profile & History              │
    │ • Reading history             │
    │ • Stats & achievements        │
    │ • My ratings & reviews        │
    │ • Preferences                 │
    └────────────────────────────────┘
```

## Mood-Based Recommendation Flow

```
START: User selects "Get Recommendations by Mood"
│
├─ Input Options:
│  ├─ Quick Selection (Buttons)
│  │  ├─ 😊 Happy
│  │  ├─ 😢 Sad
│  │  ├─ 😤 Angry
│  │  ├─ 😴 Calm
│  │  └─ 🤔 Thoughtful
│  │
│  └─ Text Input
│     • "I'm feeling..."
│     • Enter any mood description
│
│  User selects mood: "Happy and adventurous"
│  │
│  ▼
│  ┌─────────────────────────────┐
│  │ Processing...               │
│  │ • Analyzing mood           │
│  │ • Searching database       │
│  │ • Running ML models        │
│  │ • Ranking results          │
│  └──────────┬──────────────────┘
│             │
│             ▼
│  ┌─────────────────────────────────────┐
│  │ Recommendations Generated           │
│  │                                     │
│  │ Book 1: "Sherlock Holmes" - 95%    │
│  │ Book 2: "The Odyssey" - 92%        │
│  │ Book 3: "Adventure Time" - 89%     │
│  │ ...                                 │
│  └──────────┬──────────────────────────┘
│             │
│             ├─ User clicks on Book 1
│             │  │
│             │  ▼
│             │  ┌───────────────────────┐
│             │  │ Book Details Show    │
│             │  │ • Full description   │
│             │  │ • Cover image        │
│             │  │ • Reviews            │
│             │  │ • Add to list/Rate   │
│             │  └───────────────────────┘
│             │
│             └─ User rates recommendation
│                │
│                ▼
│             ┌──────────────────┐
│             │ Rating Saved     │
│             │ Feedback used    │
│             │ to improve recs  │
│             └──────────────────┘
│
END: Recommendation complete
```

## Sentiment Analysis Feature Flow

```
User Action: "Tell me a book for this feeling"
│
├─ User enters text:
│  "I'm feeling inspired but a bit lonely,
│   want something uplifting with depth"
│
│  ▼
│  ┌──────────────────────────────────┐
│  │ NLP Processing                   │
│  │ Step 1: Tokenization            │
│  │ Step 2: Sentiment Analysis      │
│  │ Step 3: Emotion Detection       │
│  │ Step 4: Embedding Creation      │
│  └────────────┬─────────────────────┘
│               │
│               ▼
│  ┌──────────────────────────────────┐
│  │ Analysis Results                 │
│  │                                  │
│  │ Sentiment: Positive + Neutral   │
│  │ Emotions Detected:              │
│  │  • Hope (0.85)                 │
│  │  • Loneliness (0.72)           │
│  │  • Inspiration (0.90)          │
│  │  • Melancholy (0.65)           │
│  └────────────┬─────────────────────┘
│               │
│               ▼
│  ┌──────────────────────────────────┐
│  │ Book Matching                    │
│  │ Find books matching:             │
│  │ • Inspirational tone            │
│  │ • Emotional depth               │
│  │ • Uplifting narrative           │
│  │ • Personal growth themes        │
│  └────────────┬─────────────────────┘
│               │
│               ▼
│  ┌──────────────────────────────────┐
│  │ Recommendations                  │
│  │                                  │
│  │ 1. "The Boy Who Harnessed Wind" │
│  │    Score: 0.94                  │
│  │    Reason: Inspirational story  │
│  │             of personal triumph │
│  │                                  │
│  │ 2. "Man's Search for Meaning"   │
│  │    Score: 0.91                  │
│  │    Reason: Deep, uplifting     │
│  │             philosophical work  │
│  │                                  │
│  │ 3. "The Midnight Library"       │
│  │    Score: 0.88                  │
│  │    Reason: Explores life paths, │
│  │             hopeful ending      │
│  └──────────────────────────────────┘
│
END: User reviews recommendations
```

## Reading List Management Flow

```
Dashboard
│
├─ User clicks "My Reading Lists"
│  │
│  ▼
│  ┌────────────────────────────────┐
│  │ Reading Lists View             │
│  │                                │
│  │ ✓ To Read (15 books)          │
│  │ ◐ Currently Reading (2 books) │
│  │ ✓ Completed (47 books)        │
│  │ ♥ Favorites (8 books)         │
│  │ + Create New List             │
│  └────────┬───────────────────────┘
│           │
│           ├─ Click "To Read"
│           │  │
│           │  ▼
│           │  ┌──────────────────────┐
│           │  │ To Read List         │
│           │  │ (15 books sorted)   │
│           │  │                      │
│           │  │ 1. Book Title A     │
│           │  │    [Mark Reading]   │
│           │  │    [Remove]         │
│           │  │                      │
│           │  │ 2. Book Title B     │
│           │  │    [Mark Reading]   │
│           │  │    [Remove]         │
│           │  │                      │
│           │  │ ... (13 more)       │
│           │  └──────────────────────┘
│           │
│           └─ Click "Completed"
│              │
│              ▼
│              ┌──────────────────────┐
│              │ Completed Books      │
│              │ (47 books)          │
│              │ Sorted by date      │
│              │ Filters: Genre,     │
│              │ Rating, Author      │
│              └──────────────────────┘
```

---

**Last Updated**: May 23, 2026
