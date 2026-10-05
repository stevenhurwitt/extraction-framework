import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import ArticleRenderer from '../components/ArticleRenderer';
import { getArticle } from '../api';

export default function ArticlePage() {
  const { title } = useParams();
  const decodedTitle = decodeURIComponent(title);
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setArticle(null);
    getArticle(decodedTitle)
      .then(data => { setArticle(data); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, [decodedTitle]);

  if (loading) return <div className="loading">Loading article…</div>;
  if (error) return (
    <div className="container">
      <div className="error-msg">{error}</div>
      <Link to="/">← Back to home</Link>
    </div>
  );

  return (
    <div className="container">
      {article?.text
        ? <ArticleRenderer title={article.title} wikitext={article.text} />
        : <div className="loading">Article has no content.</div>
      }
    </div>
  );
}
