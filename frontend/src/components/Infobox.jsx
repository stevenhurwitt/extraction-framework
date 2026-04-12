export default function Infobox({ infobox }) {
  const data = infobox.keyValue?.() ?? {};
  const entries = Object.entries(data).filter(([, v]) => v);
  if (!entries.length) return null;

  return (
    <div className="infobox">
      <div className="infobox-title">{infobox.type?.() ?? 'Infobox'}</div>
      <table>
        <tbody>
          {entries.map(([k, v]) => (
            <tr key={k}>
              <td>{k}</td>
              <td>{String(v)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
