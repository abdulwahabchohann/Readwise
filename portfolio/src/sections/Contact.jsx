import AnimatedSection from '../components/AnimatedSection';
import Container from '../components/Container';
import SectionIntro from '../components/SectionIntro';
import { contactLinks, profile } from '../data/portfolio';

export default function Contact() {
  return (
    <AnimatedSection id="contact" className="section-shell scroll-mt-24">
      <Container>
        <div className="panel p-6 sm:p-8">
          <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <SectionIntro
                eyebrow="Contact"
                title="Open to Generative AI / Backend Engineering roles"
                description="If your team needs someone who can connect AI functionality to reliable backend systems, I’m available for conversations."
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              {contactLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  target={link.href.startsWith('mailto:') ? undefined : '_blank'}
                  rel={link.href.startsWith('mailto:') ? undefined : 'noreferrer'}
                  className="rounded-3xl border border-ink-200 bg-white p-5 transition hover:border-accent-300 hover:-translate-y-0.5 dark:border-ink-700 dark:bg-ink-800 dark:hover:border-accent-500"
                >
                  <p className="eyebrow">{link.label}</p>
                  <p className="mt-3 break-all text-sm font-medium leading-6 text-ink-800 dark:text-ink-100">{link.value}</p>
                </a>
              ))}
            </div>
          </div>

          <div className="mt-10 flex flex-col gap-3 border-t border-ink-200 pt-6 text-sm text-ink-500 dark:border-ink-700 dark:text-ink-400 sm:flex-row sm:items-center sm:justify-between">
            <p>{profile.name}</p>
            <p>Designed for recruiter clarity, backend credibility, and fast portfolio scanning.</p>
          </div>
        </div>
      </Container>
    </AnimatedSection>
  );
}
