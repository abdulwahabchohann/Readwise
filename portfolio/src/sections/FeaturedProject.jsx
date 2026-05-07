import AnimatedSection from '../components/AnimatedSection';
import Container from '../components/Container';
import SectionIntro from '../components/SectionIntro';
import { profile, project } from '../data/portfolio';

function Arrow() {
  return (
    <svg className="h-5 w-5 text-ink-400 dark:text-ink-500" viewBox="0 0 20 20" fill="none">
      <path d="M4 10h12M11 5l5 5-5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function FeaturedProject() {
  return (
    <AnimatedSection id="project" className="section-shell scroll-mt-24">
      <Container>
        <div className="panel overflow-hidden">
          <div className="grid gap-0 xl:grid-cols-[0.96fr_1.04fr]">
            <div className="border-b border-ink-200/80 p-6 sm:p-8 xl:border-b-0 xl:border-r dark:border-ink-700/80">
              <SectionIntro
                eyebrow={project.eyebrow}
                title={project.name}
                description={project.summary}
              />

              <div className="mt-8 space-y-5">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">Problem</p>
                  <p className="mt-3 text-base leading-7 text-ink-700 dark:text-ink-200">{project.problem}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">Solution</p>
                  <p className="mt-3 text-base leading-7 text-ink-700 dark:text-ink-200">{project.solution}</p>
                </div>
              </div>

              <div className="mt-8 overflow-hidden rounded-[1.75rem] border border-ink-200 bg-ink-50 dark:border-ink-700 dark:bg-ink-900">
                <img
                  src="/assets/readwise-illustration.png"
                  alt="Illustration for the AI Book Recommendation System"
                  width="1152"
                  height="768"
                  className="h-auto w-full object-cover"
                />
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <a
                  href={profile.repo}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center justify-center rounded-full bg-ink-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-ink-700 dark:bg-white dark:text-ink-900 dark:hover:bg-ink-100"
                >
                  View Source
                </a>
                <span className="inline-flex items-center rounded-full border border-ink-200 px-4 py-3 text-sm font-medium text-ink-600 dark:border-ink-700 dark:text-ink-300">
                  Deployment: {project.deployment.join(' / ')}
                </span>
              </div>
            </div>

            <div className="p-6 sm:p-8">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">Technical Architecture</p>
                <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center">
                  {project.architecture.map((node, index) => (
                    <div key={node} className="flex items-center gap-3">
                      <div className="rounded-2xl border border-ink-200 bg-white px-4 py-3 text-sm font-semibold text-ink-800 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100">
                        {node}
                      </div>
                      {index < project.architecture.length - 1 ? <Arrow /> : null}
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-10">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">Key Features</p>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  {project.features.map((feature) => (
                    <div key={feature.title} className="rounded-3xl border border-ink-200 bg-white p-5 dark:border-ink-700 dark:bg-ink-800">
                      <h3 className="text-lg font-semibold text-ink-900 dark:text-white">{feature.title}</h3>
                      <p className="mt-3 text-sm leading-6 text-ink-600 dark:text-ink-300">{feature.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-10 grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">Engineering Decisions</p>
                  <div className="mt-4 space-y-4">
                    {project.decisions.map((decision) => (
                      <div key={decision.title} className="rounded-3xl border border-ink-200 bg-white p-5 dark:border-ink-700 dark:bg-ink-800">
                        <h3 className="text-base font-semibold text-ink-900 dark:text-white">{decision.title}</h3>
                        <p className="mt-2 text-sm leading-6 text-ink-600 dark:text-ink-300">{decision.description}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-500 dark:text-ink-400">Tech Stack</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {project.stack.map((item) => (
                      <span key={item} className="pill">
                        {item}
                      </span>
                    ))}
                  </div>

                  <div className="mt-8 rounded-3xl border border-accent-200 bg-accent-50 p-5 dark:border-accent-900 dark:bg-accent-950/30">
                    <p className="text-sm font-semibold uppercase tracking-[0.18em] text-accent-800 dark:text-accent-200">Real-world value</p>
                    <p className="mt-3 text-sm leading-6 text-ink-700 dark:text-ink-200">
                      This project demonstrates the ability to turn NLP and retrieval into a real product surface: authenticated user flows, external integrations, async backend processing, and a reusable API layer.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </AnimatedSection>
  );
}
