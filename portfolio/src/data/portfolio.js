export const profile = {
  name: 'Abdul Wahab',
  title: 'Generative AI Engineer building production-ready AI systems',
  impactStatement:
    'I build backend-first AI products that combine semantic search, asynchronous processing, and dependable APIs so models become usable software.',
  availability: 'Open to Generative AI / Backend Engineering roles',
  location: 'Based in Pakistan, open to remote and on-site teams',
  email: '12345678+abdulwahabchohann@users.noreply.github.com',
  github: 'https://github.com/abdulwahabchohann',
  linkedin: 'https://pk.linkedin.com/in/abdul-wahab-951100272/',
  repo: 'https://github.com/abdulwahabchohann/Readwise',
};

export const aboutPoints = [
  'My focus is building AI systems that hold up beyond notebooks. I work across the full delivery path: preparing data, selecting retrieval and ranking strategies, exposing the system through Django APIs, and making the stack practical to deploy.',
  'The strongest example is my AI Book Recommendation System, where semantic retrieval, sentiment-aware ranking, background processing, and external book data are combined into a usable product instead of a one-off model demo.',
];

export const project = {
  eyebrow: 'Featured Project',
  name: 'AI Book Recommendation System',
  alias: 'ReadWise',
  summary:
    'A Django-based recommendation platform that turns vague user intent into relevant book suggestions through semantic retrieval, sentiment-aware ranking, and API-first backend design.',
  problem:
    'Book discovery often breaks down when users know the mood or theme they want but cannot describe exact titles, authors, or genres. Keyword search alone misses that intent.',
  solution:
    'I built an AI recommendation workflow that converts user input into embeddings, retrieves semantically similar books with FAISS, adjusts ordering with sentiment signals, and exposes the system through authenticated Django and DRF endpoints.',
  features: [
    {
      title: 'Semantic retrieval with FAISS',
      description:
        'Sentence-transformer embeddings allow recommendations to match meaning rather than exact keywords.',
    },
    {
      title: 'Sentiment-aware ranking',
      description:
        'Recommendations are re-ordered to better reflect how the user feels, improving relevance for mood-driven discovery.',
    },
    {
      title: 'Asynchronous processing with Celery',
      description:
        'Background jobs keep enrichment and heavier recommendation tasks off the request path for more reliable response times.',
    },
    {
      title: 'REST API with Django REST Framework',
      description:
        'The system is exposed as reusable endpoints so the recommendation engine can support web UI and future clients.',
    },
    {
      title: 'Google Books API integration',
      description:
        'External metadata broadens discovery and fills gaps where local catalog data is incomplete.',
    },
    {
      title: 'Authentication and user flows',
      description:
        'User auth, profile handling, and protected endpoints make the product practical as an end-to-end application.',
    },
  ],
  decisions: [
    {
      title: 'Vector retrieval over keyword-only search',
      description:
        'FAISS and sentence embeddings were a better fit for subjective prompts where the user intent is semantic, not literal.',
    },
    {
      title: 'API-first backend boundary',
      description:
        'Using DRF keeps the recommendation engine reusable and easier to extend into other interfaces or services.',
    },
    {
      title: 'Async worker layer for non-trivial jobs',
      description:
        'Celery reduces coupling between user-facing latency and downstream processing, which matters as recommendation logic grows.',
    },
    {
      title: 'Low-ops deployment path',
      description:
        'SQLite plus PythonAnywhere or Render kept the system deployable while still demonstrating practical backend architecture decisions.',
    },
  ],
  architecture: ['Client', 'Django REST API', 'Celery Workers', 'FAISS + SQLite + External APIs'],
  stack: [
    'Python',
    'Django',
    'Django REST Framework',
    'Celery',
    'Transformers',
    'Sentence Transformers',
    'FAISS',
    'SQLite',
  ],
  deployment: ['PythonAnywhere', 'Render'],
};

export const skillGroups = [
  {
    title: 'Backend',
    items: ['Django', 'Django REST Framework'],
    detail: 'Building authenticated APIs, service layers, and production-minded application flows.',
  },
  {
    title: 'AI / ML',
    items: ['Transformers', 'Sentence Transformers', 'FAISS'],
    detail: 'Applying NLP models and vector search to recommendation and retrieval problems.',
  },
  {
    title: 'Data',
    items: ['Pandas', 'NumPy'],
    detail: 'Preparing, cleaning, and structuring data for recommendation and model workflows.',
  },
  {
    title: 'Tools',
    items: ['Git', 'Docker', 'Celery'],
    detail: 'Version control, basic containerization, and background execution for reliable delivery.',
  },
];

export const timeline = [
  {
    stage: 'Foundations',
    summary: 'Built Python fundamentals through scripting, debugging, and structured problem solving.',
  },
  {
    stage: 'Django / DRF',
    summary: 'Moved into backend engineering with web apps, authentication flows, and REST APIs.',
  },
  {
    stage: 'ML / NLP',
    summary: 'Applied transformer-based NLP and text similarity techniques to practical recommendation use cases.',
  },
  {
    stage: 'AI Book Recommendation System',
    summary: 'Combined Django, FAISS, async workers, and external APIs into a complete AI-backed application.',
  },
  {
    stage: 'Exploring LLM apps',
    summary: 'Expanding into LLM-driven products while keeping the same focus on system reliability and backend execution.',
  },
];

export const contactLinks = [
  {
    label: 'Email',
    value: profile.email,
    href: `mailto:${profile.email}`,
  },
  {
    label: 'GitHub',
    value: 'github.com/abdulwahabchohann',
    href: profile.github,
  },
  {
    label: 'LinkedIn',
    value: 'pk.linkedin.com/in/abdul-wahab-951100272',
    href: profile.linkedin,
  },
];
