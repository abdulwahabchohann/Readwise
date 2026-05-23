import AnimatedSection from '../components/AnimatedSection';
import Container from '../components/Container';
import SectionIntro from '../components/SectionIntro';
import { skillGroups } from '../data/portfolio';

export default function Skills() {
  return (
    <AnimatedSection id="skills" className="section-shell scroll-mt-24">
      <Container>
        <SectionIntro
          eyebrow="Skills"
          title="Tools aligned with backend and AI product delivery"
          description="The emphasis is on shipping working systems, not collecting a broad list of technologies."
        />

        <div className="mt-10 grid gap-4 lg:grid-cols-2 2xl:grid-cols-4">
          {skillGroups.map((group) => (
            <div key={group.title} className="panel p-6">
              <h3 className="text-xl font-semibold text-ink-900 dark:text-white">{group.title}</h3>
              <p className="mt-3 text-sm leading-6 text-ink-600 dark:text-ink-300">{group.detail}</p>
              <div className="mt-5 flex flex-wrap gap-2">
                {group.items.map((item) => (
                  <span key={item} className="pill">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Container>
    </AnimatedSection>
  );
}
