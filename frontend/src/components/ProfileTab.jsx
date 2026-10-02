import MyOffers from './MyOffers'
import { MIN_SCRIPT_CHARS } from '../utils'

// data/error/busy live in App (not here) so switching tabs away and back
// doesn't remount this and refetch — only first load and explicit refresh do

export default function ProfileTab({ script, saveScript, data, error, busy, onRemove }) {
  // gate the whole tab behind one loading screen, but only for the very
  // first load (data/error both still null) — never on tab re-visits
  if (!data && !error) {
    return (
      <div className="profile-loading">
        <div className="spinner" />
        <div>กำลังโหลดโปรไฟล์...</div>
      </div>
    )
  }

  const chars = script.trim().length
  const charsOk = chars >= MIN_SCRIPT_CHARS

  return (
    <div className="profile">
      <div className="profile-col">
        <div className="profile-head">
          <div className="avatar">👤</div>
          <div>
            <div className="profile-name">Freelancer</div>
            <div className="profile-sub">Tracking jobs since {new Date().toISOString().slice(0, 10)}</div>
          </div>
        </div>

        <div className="script-box">
          <label htmlFor="apply-script">Application script</label>
          <p className="script-hint">Text sent when auto-applying to a job.</p>
          <textarea
            id="apply-script"
            rows={8}
            value={script}
            onChange={(e) => saveScript(e.target.value)}
            placeholder="สวัสดีครับ สนใจงานนี้ พร้อมเริ่มงานได้ทันที..."
          />
          <p className={`script-wordcount${charsOk ? '' : ' script-wordcount-warn'}`}>
            {chars} / {MIN_SCRIPT_CHARS} ตัวอักษร
            {!charsOk && ` — ต้องมากกว่า ${MIN_SCRIPT_CHARS} ตัวอักษร`}
          </p>
        </div>
      </div>

      <div className="my-offers-col">
        {error ? <div className="offer-error">{error}</div> : <MyOffers data={data} busy={busy} onRemove={onRemove} />}
      </div>
    </div>
  )
}
