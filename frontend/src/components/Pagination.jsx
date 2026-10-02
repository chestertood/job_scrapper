// Prev/Next control shared by the job list and the offers list.
export default function Pagination({ page, totalPages, onChange, disabled }) {
  return (
    <div className="pagination">
      <button disabled={disabled || page <= 1} onClick={() => onChange(page - 1)}>
        ← ก่อนหน้า
      </button>
      <span>
        {page} / {totalPages}
      </span>
      <button disabled={disabled || page >= totalPages} onClick={() => onChange(page + 1)}>
        ถัดไป →
      </button>
    </div>
  )
}
