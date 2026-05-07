import AnimatedSection from '../components/AnimatedSection';
import Container from '../components/Container';
import SectionIntro from '../components/SectionIntro';
import { timeline } from '../data/portfolio';

export default function Timeline() {
  return (
    <AnimatedSection id="timeline" className="section-shell scroll-mt-24">
      <Container>
        <SectionIntro
          eyebrow="Experience Timeline"
          title="Progression toward applied Generative AI engineering"
          description="A concise view of the technical path behind the current portfolio focus."
        />

        <div className="mt-10 rounded-[2rem] border border-ink-200 bg-white/85 p-6 shadow-panel backdrop-blur-sm dark:border-ink-700 dark:bg-ink-800/80">
          <div className="relative">
            <div className="absolute left-[15px] top-2 hidden h-[calc(100%-1rem)] w-px bg-ink-200 dark:bg-ink-700 sm:block" />
            <div className="space-y-6">
              {timeline.map((item) => (
                <div key={item.stage} className="relative grid gap-3 sm:grid-cols-[32px_1fr] sm:gap-6">
                  <div className="hidden sm:flex">
                    <span className="mt-1 h-8 w-8 rounded-full border border-accent-200 bg-accent-50 dark:border-accent-800 dark:bg-accent-950/30" />
                  </div>
                  <div className="rounded-3xl border border-ink-200 p-5 dark:border-ink-700">
                    <h3 className="text-lg font-semibold text-ink-900 dark:text-white">{item.stage}</h3>
                    <p className="mt-2 text-sm leading-6 text-ink-600 dark:text-ink-300">{item.summary}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Container>
    </AnimatedSection>
  );
}
