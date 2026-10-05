import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import Pagination from '../components/Pagination';
import { searchArticles } from '../api';

const LIMIT = 20;

export default function SearchPage() {
  const [params] = useSearchParams();
  const q = params.get('q') ?? '';
  const [offset, setOffset] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!q) return;
    setLoading(true);
    setError(null);
    searchArticles(q, { limit: LIMIT, offset })
      .then(data => { setResult(data); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, [q, offset]);

  return (
    <div className="container">
      {loading && <div className="loading">Searching…</div>}
      {error && <div className="error-msg">{error}</div>}
      {result && !loading && (
        <>
          <div className="search-header">
            {result.total_count.toLocaleString()} results for "<strong>{q}</strong>"
          </div>
          <ul className="result-list">
            {result.articles.map(a => (
              <li key={a.title} className="result-item">
                <Link to={`/article/${encodeURIComponent(a.title)}`}>{a.title}</Link>
                {a.text_length && (
                  <div className="meta">{a.text_length.toLocaleString()} characters</div>
                )}
              </li>
            ))}
          </ul>
          <Pagination
            offset={offset}
            limit={LIMIT}
            total={result.total_count}
            onChange={setOffset}
          />
        </>
      )}
      {result?.articles.length === 0 && !loading && (
        <div className="loading">No articles found for "{q}"</div>
      )}
    </div>
  );
}
