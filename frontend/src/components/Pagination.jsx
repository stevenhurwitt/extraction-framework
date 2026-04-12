export default function Pagination({ offset, limit, total, onChange }) {
  const page = Math.floor(offset / limit);
  const totalPages = Math.ceil(total / limit);
  if (totalPages <= 1) return null;

  return (
    <div className="pagination">
      <button className="btn" disabled={page === 0} onClick={() => onChange((page - 1) * limit)}>
        ← Prev
      </button>
      <span className="btn" style={{ cursor: 'default' }}>
        {page + 1} / {totalPages}
      </span>
      <button className="btn" disabled={page >= totalPages - 1} onClick={() => onChange((page + 1) * limit)}>
        Next →
      </button>
    </div>
  );
}
