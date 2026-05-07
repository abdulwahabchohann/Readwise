export default function SectionIntro({ eyebrow, title, description, className = '' }) {
  return (
    <div className={className}>
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="section-title mt-4">{title}</h2>
      {description ? <p className="body-copy mt-4 max-w-3xl">{description}</p> : null}
    </div>
  );
}
