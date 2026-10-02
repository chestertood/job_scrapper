import JobCard from './JobCard'
import Pagination from './Pagination'

const TABS = [
  { id: 'today', label: 'วันนี้' },
  { id: 'yesterday', label: 'เมื่อวาน' },
  { id: 'all', label: 'ทั้งหมด' },
  { id: 'AI_job', label: 'งาน AI' },
]

export default function JobListTab({ jobs, filter, onFilterChange, page, totalPages, loading, error, onPageChange, onRemove, script }) {
  return (
    <>
      <div className="chips">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`chip${filter === t.id ? ' chip-active' : ''}`}
            onClick={() => onFilterChange(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className={`status${error ? ' status-error' : ''}`}>
        {loading ? 'กำลังโหลด...' : error ? `ผิดพลาด: ${error}` : `${jobs.length} งาน · หน้า ${page}/${totalPages}`}
      </div>
      <div className="job-table-wrap">
        {!loading && !error && jobs.length === 0 ? (
          <div className="empty">
            <span className="empty-icon">🔍</span>
            ไม่พบงานในช่วงนี้ ลองเปลี่ยนตัวกรองดู
          </div>
        ) : (
          <table className="job-table">
            <thead>
              <tr>
                <th>เว็บ</th>
                <th>ชื่องาน</th>
                <th>งบประมาณ</th>
                <th>ประเภท</th>
                <th>วันที่</th>
                <th>ราคาที่เสนอ</th>
                <th>วันเวลา</th>
                <th></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <JobCard key={j.id} job={j} onRemove={onRemove} script={script} />
              ))}
            </tbody>
          </table>
        )}
      </div>
      <Pagination page={page} totalPages={totalPages} onChange={onPageChange} disabled={loading} />
    </>
  )
}
