import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SearchBar({ compact = false, initialQuery = '' }) {
  const [q, setQ] = useState(initialQuery);
  const navigate = useNavigate();

  const submit = (e) => {
    e.preventDefault();
    if (q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`);
  };

  if (compact) {
    return (
      <form className="header-search" onSubmit={submit}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search articles…" />
        <button type="submit">Search</button>
      </form>
    );
  }

  return (
    <form className="home-search" onSubmit={submit}>
      <input
        value={q}
        onChange={e => setQ(e.target.value)}
        placeholder="Search Wikipedia articles…"
        autoFocus
      />
      <button type="submit" className="btn btn-primary">Search</button>
    </form>
  );
}
