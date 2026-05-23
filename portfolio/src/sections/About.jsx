import AnimatedSection from '../components/AnimatedSection';
import Container from '../components/Container';
import SectionIntro from '../components/SectionIntro';
import { aboutPoints } from '../data/portfolio';

const workflow = [
  {
    title: 'Data',
    description: 'Curate and prepare book metadata and user inputs so downstream recommendations are usable.',
  },
  {
    title: 'Modeling',
    description: 'Apply embeddings, ranking logic, and NLP components where they improve relevance.',
  },
  {
    title: 'API',
    description: 'Expose the system through Django and DRF so the model can serve real interfaces.',
  },
  {
    title: 'Deployment',
    description: 'Keep the architecture practical enough to ship on PythonAnywhere or Render.',
  },
];

export default function About() {
  return (
    <AnimatedSection id="about" className="section-shell scroll-mt-24">
      <Container>
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <SectionIntro
            eyebrow="About"
            title="Engineering focus over self-description"
            description="I am most effective on projects where machine learning needs real backend structure around it: data preparation, API boundaries, async processing, and deployment decisions that make the product stable to use."
          />
          <div className="space-y-5">
            {aboutPoints.map((point) => (
              <div key={point} className="panel p-6">
                <p className="body-copy">{point}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {workflow.map((item) => (
            <div key={item.title} className="panel p-5">
              <p className="eyebrow">{item.title}</p>
              <h3 className="mt-3 text-lg font-semibold text-ink-900 dark:text-white">{item.title} to delivery</h3>
              <p className="mt-3 text-sm leading-6 text-ink-600 dark:text-ink-300">{item.description}</p>
            </div>
          ))}
        </div>
      </Container>
    </AnimatedSection>
  );
}
