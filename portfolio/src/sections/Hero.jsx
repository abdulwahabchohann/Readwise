import { motion } from 'framer-motion';
import Container from '../components/Container';
import { profile, project } from '../data/portfolio';

const heroTags = ['Python', 'Django', 'DRF', 'Sentence Transformers', 'FAISS', 'Celery'];

export default function Hero() {
  return (
    <section className="relative overflow-hidden pb-14 pt-8 sm:pb-18 sm:pt-12">
      <Container>
        <div className="grid items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <motion.div
            className="order-2 lg:order-1"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="inline-flex items-center rounded-full border border-accent-200 bg-accent-50 px-3 py-1 text-sm font-medium text-accent-800 dark:border-accent-800 dark:bg-accent-950/40 dark:text-accent-200">
              {profile.availability}
            </div>
            <h1 className="mt-6 max-w-3xl font-display text-5xl leading-[1.02] text-ink-900 sm:text-6xl dark:text-white">
              {profile.title}
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-ink-600 dark:text-ink-300">
              {profile.impactStatement}
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <a
                href="#project"
                className="inline-flex items-center justify-center rounded-full bg-ink-900 px-6 py-3 text-sm font-semibold text-white transition hover:bg-ink-700 dark:bg-white dark:text-ink-900 dark:hover:bg-ink-100"
              >
                View Project
              </a>
              <a
                href="#contact"
                className="inline-flex items-center justify-center rounded-full border border-ink-300 px-6 py-3 text-sm font-semibold text-ink-800 transition hover:border-accent-300 hover:text-accent-700 dark:border-ink-700 dark:text-ink-100 dark:hover:border-accent-500 dark:hover:text-accent-200"
              >
                Contact
              </a>
            </div>
            <p className="mt-5 text-sm text-ink-500 dark:text-ink-400">{profile.location}</p>
            <div className="mt-8 flex flex-wrap gap-2">
              {heroTags.map((tag) => (
                <span key={tag} className="pill">
                  {tag}
                </span>
              ))}
            </div>
          </motion.div>

          <motion.div
            className="order-1 lg:order-2"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.62, delay: 0.06, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="panel mx-auto max-w-md overflow-hidden p-4 sm:p-5">
              <img
                src="/assets/profile-portrait.svg"
                alt="Portrait illustration for Abdul Wahab"
                width="640"
                height="760"
                className="h-auto w-full rounded-[1.6rem] border border-ink-200 bg-ink-50 object-cover dark:border-ink-700 dark:bg-ink-900"
              />
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="panel p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-500 dark:text-ink-400">
                  Core build
                </p>
                <p className="mt-2 text-sm leading-6 text-ink-700 dark:text-ink-200">{project.alias}: Django, FAISS, Celery, and NLP-backed recommendations.</p>
              </div>
              <div className="panel p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-500 dark:text-ink-400">
                  Hiring fit
                </p>
                <p className="mt-2 text-sm leading-6 text-ink-700 dark:text-ink-200">Best aligned with backend-heavy AI product teams and applied Generative AI engineering roles.</p>
              </div>
            </div>
          </motion.div>
        </div>
      </Container>
    </section>
  );
}
