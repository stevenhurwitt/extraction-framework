import Infobox from './Infobox';

function renderParts(parts = [], depth = 1) {
  return parts.map((part, i) => {
    if (part.type === 'section') {
      return <Section key={i} section={part} depth={depth + 1} />;
    }
    if (part.type === 'paragraph' && part.value) {
      return <p key={i}>{part.value}</p>;
    }
    if (part.type === 'list' && part.has_parts?.length) {
      return (
        <ul key={i}>
          {part.has_parts.map((item, j) =>
            item.value ? <li key={j}>{item.value}</li> : null
          )}
        </ul>
      );
    }
    return null;
  });
}

function Section({ section, depth = 1 }) {
  const HeadingTag = depth === 1 ? 'h2' : 'h3';
  return (
    <div>
      {section.name && <HeadingTag>{section.name}</HeadingTag>}
      {renderParts(section.has_parts, depth)}
    </div>
  );
}

export default function ArticleRenderer({ article }) {
  const sections = (article.sections ?? []).filter(s => s.type === 'section');
  const infoboxes = (article.infoboxes ?? []).filter(b => b.type === 'infobox');

  return (
    <div className="article-layout">
      <div className="article-content">
        <h1>{article.title}</h1>
        {article.description && <p className="meta">{article.description}</p>}
        {sections.length > 0
          ? sections.map((section, i) => <Section key={i} section={section} />)
          : article.text && <p>{article.text}</p>}
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
