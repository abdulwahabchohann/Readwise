import { useEffect, useState } from 'react';
import Container from './components/Container';
import ThemeToggle from './components/ThemeToggle';
import { profile } from './data/portfolio';
import About from './sections/About';
import Contact from './sections/Contact';
import FeaturedProject from './sections/FeaturedProject';
import Hero from './sections/Hero';
import Skills from './sections/Skills';
import Timeline from './sections/Timeline';

const navItems = [
  { label: 'About', href: '#about' },
  { label: 'Project', href: '#project' },
  { label: 'Skills', href: '#skills' },
  { label: 'Timeline', href: '#timeline' },
  { label: 'Contact', href: '#contact' },
];

function getInitialTheme() {
  const stored = localStorage.getItem('portfolio-theme');
  if (stored === 'light' || stored === 'dark') {
    return stored;
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export default function App() {
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('portfolio-theme', theme);
  }, [theme]);

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-ink-200/70 bg-ink-50/85 backdrop-blur-md dark:border-ink-800 dark:bg-ink-900/80">
        <Container className="flex items-center justify-between gap-4 py-4">
          <a href="#top" className="min-w-0">
            <p className="truncate text-sm font-semibold uppercase tracking-[0.2em] text-ink-500 dark:text-ink-400">
              {profile.name}
            </p>
            <p className="truncate text-sm text-ink-700 dark:text-ink-200">Generative AI Engineer</p>
          </a>

          <div className="hidden items-center gap-6 lg:flex">
            <nav className="flex items-center gap-6 text-sm text-ink-600 dark:text-ink-300">
              {navItems.map((item) => (
                <a key={item.label} href={item.href} className="transition hover:text-accent-700 dark:hover:text-accent-300">
                  {item.label}
                </a>
              ))}
            </nav>
            <ThemeToggle theme={theme} onToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
          </div>

          <div className="lg:hidden">
            <ThemeToggle theme={theme} onToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
          </div>
        </Container>
      </header>

      <main id="top">
        <Hero />
        <About />
        <FeaturedProject />
        <Skills />
        <Timeline />
        <Contact />
      </main>
    </div>
  );
}
