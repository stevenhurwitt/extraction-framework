import wtf from 'wtf_wikipedia';
import Infobox from './Infobox';

export default function ArticleRenderer({ title, wikitext }) {
  const doc = wtf(wikitext);
  const infoboxes = doc.infoboxes();
  const sections = doc.sections();

  return (
    <div className="article-layout">
      <div className="article-content">
        <h1>{title}</h1>
        {sections.map((section, i) => {
          const depth = section.depth?.() ?? 0;
          const heading = section.title?.();
          const paragraphs = section.paragraphs?.() ?? [];

          const HeadingTag = depth === 0 ? null : depth === 1 ? 'h2' : 'h3';

          return (
            <div key={i}>
              {HeadingTag && heading && <HeadingTag>{heading}</HeadingTag>}
              {paragraphs.map((para, j) => {
                const text = para.text?.();
                return text ? <p key={j}>{text}</p> : null;
              })}
            </div>
          );
        })}
      </div>

      {infoboxes.length > 0 && (
        <aside>
          {infoboxes.map((box, i) => (
            <Infobox key={i} infobox={box} />
          ))}
        </aside>
      )}
    </div>
  );
}
