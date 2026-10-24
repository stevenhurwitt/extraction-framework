function collectFields(node, out = []) {
  for (const part of node.has_parts ?? []) {
    if (part.type === 'field' && part.value) {
      out.push([part.name, part.value]);
    } else if (part.type === 'section') {
      collectFields(part, out);
    }
  }
  return out;
}

function findImage(node) {
  for (const part of node.has_parts ?? []) {
    if (part.type === 'image' && part.images?.length) {
      return part.images[0].content_url;
    }
    if (part.type === 'section') {
      const found = findImage(part);
      if (found) return found;
    }
  }
  return null;
}

export default function Infobox({ infobox }) {
  const entries = collectFields(infobox);
  const image = findImage(infobox);
  if (!entries.length && !image) return null;

  return (
    <div className="infobox">
      <div className="infobox-title">{infobox.name ?? 'Infobox'}</div>
      {image && <img src={image} alt={infobox.name ?? ''} style={{ maxWidth: '100%' }} />}
      <table>
        <tbody>
          {entries.map(([k, v], i) => (
            <tr key={`${k}-${i}`}>
              <td>{k}</td>
              <td>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
