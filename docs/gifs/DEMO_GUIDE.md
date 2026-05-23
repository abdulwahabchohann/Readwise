# Demo GIFs & Video Guide

## Demo 1: Mood-Based Recommendation

**File**: `mood-recommendation-demo.gif`
**Duration**: 15 seconds
**Steps to Record**:

1. **Seconds 0-2**: Show dashboard with mood selection buttons
   - Display the "How are you feeling?" section
   - Show mood options: Happy, Sad, Calm, Excited, etc.

2. **Seconds 2-4**: User clicks "😊 Happy" button
   - Button highlights/animates
   - Show loading spinner

3. **Seconds 4-8**: Processing animation
   - Show "Analyzing your mood..." message
   - Display progress bar (0-100%)
   - Show ML model indicators

4. **Seconds 8-15**: Recommendations appear with animation
   - Cards slide in from bottom
   - Each card shows: Book cover, title, rating, match score
   - Scroll through first 3-4 recommendations

**Loop**: Yes - replay from step 1

---

## Demo 2: Sentiment Analysis Feature

**File**: `sentiment-demo.gif`
**Duration**: 12 seconds
**Steps to Record**:

1. **Seconds 0-2**: Show text input box
   - Focus on the "Tell me your mood..." input field
   - Show placeholder text

2. **Seconds 2-5**: Type text slowly
   - "I'm feeling inspired but a bit lonely"
   - Show cursor typing character by character

3. **Seconds 5-7**: Processing
   - Show sentiment indicators appearing
   - Display emotion detection badges (Hope, Loneliness, etc.)
   - Show percentage scores

4. **Seconds 7-12**: Results slide in
   - Matched books appear with scores
   - Show "Why this recommendation" section
   - Highlight similarity match

**Loop**: Yes

---

## Demo 3: Complete User Journey

**File**: `complete-flow-demo.gif`
**Duration**: 30-45 seconds
**Steps to Record**:

1. **0-5 sec**: User signs in
   - Show login page
   - Enter credentials or click "Google Login"
   - See dashboard load

2. **5-10 sec**: Browse dashboard
   - Show personalized recommendations
   - Show trending section
   - Scroll down to see more

3. **10-15 sec**: User enters mood
   - Click on mood input
   - Type: "Happy and adventurous"
   - Click "Get Recommendations"

4. **15-20 sec**: Recommendations loading
   - Show loading animation
   - Recommendations appear one by one

5. **20-30 sec**: User interacts with book
   - Click on a book card
   - Show book detail page
   - Click "Add to List"
   - See success message

6. **30-45 sec**: View reading list
   - Navigate to "My Lists"
   - Show the added book in reading list
   - Show stats update

---

## Demo 4: API Response Visualization

**File**: `api-response-demo.gif`
**Duration**: 10 seconds
**Steps to Record**:

1. **0-2 sec**: Show API request in terminal/REST client
   ```
   POST /api/recommendations/by-mood/
   Content: {"mood": "happy", "limit": 10}
   ```

2. **2-5 sec**: Show request being sent
   - Network activity indicator
   - Loading spinner

3. **5-10 sec**: Show JSON response
   - Response data appears line by line
   - Highlight important fields (id, title, score)
   - Show formatted JSON with syntax highlighting

---

## How to Record GIFs

### Tools to Use:
- **Windows**: ScreenToGif, Gifski, or LICEcap
- **Mac**: Kap, GIPHY Capture, or QuickTime
- **Linux**: SimpleScreenRecorder + ffmpeg

### Recording Tips:

1. **Screen Setup**:
   - Use 1280x720 or 1920x1080 resolution
   - Close unnecessary windows
   - Ensure clean background

2. **Recording**:
   - Move slowly and deliberately
   - Pause between major steps
   - Avoid jerky movements
   - Use smooth scrolling

3. **GIF Optimization**:
   - Keep duration under 30 seconds
   - File size under 5MB
   - Frame rate: 10-15 fps (smoother than 60)
   - Optimize colors if needed

4. **Quality Settings**:
   - Use full color (256 colors minimum)
   - Keep aspect ratio
   - Avoid compression artifacts

### Example FFmpeg Command:
```bash
# Convert MP4 to GIF
ffmpeg -i video.mp4 -vf "fps=10,scale=1280:720" output.gif

# Optimize GIF size
ffmpeg -i output.gif -vf "fps=10" -loop 0 optimized.gif
```

---

## Demo Video Script

### Full Product Demo (2-3 minutes)

**Scene 1: Introduction (30 seconds)**
```
[Show title card]
"ReadWise - AI-Powered Book Recommendations"

[Show app logo/branding]
"Discover your next favorite book based on your mood"

[Show key features bullets]
- Mood-based recommendations
- Sentiment analysis
- Smart filtering
- Personal reading lists
```

**Scene 2: Sign Up Flow (1 minute)**
```
[Show landing page]
"Start by signing up..."

[Click signup button]
[Fill in credentials or use Google OAuth]
[Verify email]

"Welcome to ReadWise!"
```

**Scene 3: Dashboard Tour (1 minute)**
```
[Show main dashboard]
"Your personalized dashboard shows..."

[Point to sections]
- Recommended for you
- Quick mood search
- Trending books
- Reading lists

[Show sorting/filtering options]
```

**Scene 4: Get Recommendations (1 minute)**
```
[Show mood input]
"Tell us how you're feeling..."

[Enter text or select mood]
"I'm feeling inspired and adventurous"

[Show processing]
"ReadWise analyzes your mood..."

[Show recommendations appear]
"Here are books perfect for your mood!"

[Highlight match scores and reasons]
```

**Scene 5: Book Details (45 seconds)**
```
[Click on recommended book]
[Show book details page]

[Point out]
- Book cover and description
- Reader reviews
- Why it matches your mood
- Add to reading list option
```

**Scene 6: Reading List Management (45 seconds)**
```
[Go to "My Lists"]
[Show reading lists]

[Show different lists]
- To Read (15 books)
- Currently Reading (2 books)
- Completed (47 books)

[Show statistics]
- Books read this year: 47
- Pages read: 12,345
- Average rating given: 4.3
```

**Outro (30 seconds)**
```
[Show summary of features]
"ReadWise makes reading personal"

[Call to action]
"Start discovering your next favorite book"

[Show download/access links]
```

---

## Video Recording Checklist

- [ ] App is responsive and runs smoothly
- [ ] No error messages visible
- [ ] Data is realistic (not placeholder)
- [ ] Smooth transitions between screens
- [ ] Voice-over is clear (if adding audio)
- [ ] Video resolution is 1080p minimum
- [ ] Video framerate is 30fps
- [ ] Total file size under 100MB
- [ ] Video is in MP4 format
- [ ] Subtitles added (optional but recommended)

---

## File Naming & Placement

```
docs/gifs/
├── mood-recommendation-demo.gif
├── sentiment-demo.gif
├── complete-flow-demo.gif
└── api-response-demo.gif

docs/videos/
├── complete-flow-demo.mp4
├── setup-guide.mp4
└── api-usage.mp4
```

---

## Updating README with Media

After recording, update [../../README.md](../../README.md):

```markdown
### Demo GIFs

#### Mood-Based Recommendation
![Mood Recommendation Demo](docs/gifs/mood-recommendation-demo.gif)

#### Sentiment Analysis
![Sentiment Analysis Demo](docs/gifs/sentiment-demo.gif)

### Demo Videos

#### Complete User Journey
[Watch the complete flow demo](docs/videos/complete-flow-demo.mp4)

#### Setup Guide
[Watch the installation guide](docs/videos/setup-guide.mp4)
```

---

**Last Updated**: May 23, 2026
