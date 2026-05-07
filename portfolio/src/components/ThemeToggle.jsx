const iconClassName = 'h-4 w-4';

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={iconClassName}>
      <circle cx="12" cy="12" r="4" />
      <path strokeLinecap="round" d="M12 2v2.5M12 19.5V22M4.93 4.93l1.77 1.77M17.3 17.3l1.77 1.77M2 12h2.5M19.5 12H22M4.93 19.07l1.77-1.77M17.3 6.7l1.77-1.77" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={iconClassName}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z"
      />
    </svg>
  );
}

export default function ThemeToggle({ theme, onToggle }) {
  const nextTheme = theme === 'dark' ? 'light' : 'dark';

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={`Switch to ${nextTheme} mode`}
      className="inline-flex items-center gap-2 rounded-full border border-ink-200 bg-white/90 px-3 py-2 text-sm font-medium text-ink-700 transition hover:border-accent-300 hover:text-accent-700 dark:border-ink-700 dark:bg-ink-800/90 dark:text-ink-200 dark:hover:border-accent-500 dark:hover:text-accent-300"
    >
      {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
      <span>{nextTheme === 'dark' ? 'Dark mode' : 'Light mode'}</span>
    </button>
  );
}
