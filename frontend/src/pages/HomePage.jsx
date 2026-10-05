import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import { getStats, getRandomArticle } from '../api';

export default function HomePage() {
  const [stats, setStats] = useState(null);
  const [loadingRandom, setLoadingRandom] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
  }, []);

  const handleRandom = async () => {
    setLoadingRandom(true);
    try {
      const article = await getRandomArticle();
      navigate(`/article/${encodeURIComponent(article.title)}`);
    } catch {
      setLoadingRandom(false);
    }
  };

  return (
    <>
      <div className="home-hero">
        <h1>Wiki<span>pedia</span> Explorer</h1>
        <p>Browse {stats ? stats.total_articles.toLocaleString() : '…'} articles from the local database</p>
        <SearchBar />
        <button className="btn" onClick={handleRandom} disabled={loadingRandom}>
          {loadingRandom ? 'Loading…' : '🎲 Random Article'}
        </button>
      </div>

      {stats && (
        <div className="container">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="value">{stats.total_articles.toLocaleString()}</div>
              <div className="label">Total Articles</div>
            </div>
            <div className="stat-card">
              <div className="value">{Math.round(stats.avg_text_length).toLocaleString()}</div>
              <div className="label">Avg. Length (chars)</div>
            </div>
            <div className="stat-card">
              <div className="value">{stats.max_text_length.toLocaleString()}</div>
              <div className="label">Longest Article</div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
