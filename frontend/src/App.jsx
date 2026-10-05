import { Routes, Route, useNavigate } from 'react-router-dom';
import SearchBar from './components/SearchBar';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import ArticlePage from './pages/ArticlePage';

export default function App() {
  const navigate = useNavigate();
  return (
    <>
      <header className="site-header">
        <div className="logo" style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
          Wiki<span>pedia</span>
        </div>
        <SearchBar compact />
      </header>
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/article/:title" element={<ArticlePage />} />
        </Routes>
      </main>
    </>
  );
}
