import { useEffect, useState } from 'react'
import { startLogin } from '../api'
import fastworkLogo from '../assets/fastwork-logo.svg'

const POLL_MS = 2000

// add a real site here once its scraping/apply flow exists — the rest of
// the grid (including the "coming soon" styling) just works
const SITES = [
  { id: 'fastwork', name: 'Fastwork', logo: fastworkLogo, enabled: true },
]

export default function LoginPage({ onRecheck }) {
  const [opened, setOpened] = useState(null) // site id whose login window we opened

  const click = (site) => {
    if (!site.enabled) return
    startLogin(site.id).catch(() => {})
    setOpened(site.id)
  }

  // poll instead of making the user click a button — App unmounts this page
  // as soon as onRecheck() flips fastworkLoggedIn to true, which stops the
  // interval via this cleanup; the backend closes the login window itself
  // once it sees the login succeeded (is_logged_in()'s auto-close)
  useEffect(() => {
    if (!opened) return
    const id = setInterval(onRecheck, POLL_MS)
    return () => clearInterval(id)
  }, [opened, onRecheck])

  return (
    <div className="login-page">
      <h1>เลือกเว็บที่จะเข้าสู่ระบบ</h1>
      <p className="login-page-sub">เชื่อมบัญชีเพื่อเริ่มดึงงานและเสนอราคาอัตโนมัติ</p>
      <div className="login-grid">
        {SITES.map((site) => (
          <button
            key={site.id}
            className={`login-tile${site.enabled ? '' : ' login-tile-disabled'}`}
            onClick={() => click(site)}
            disabled={!site.enabled}
          >
            <img src={site.logo} alt={site.name} />
            <span>{site.name}</span>
            {!site.enabled && <small>เร็วๆนี้</small>}
          </button>
        ))}
      </div>
      {opened && (
        <div className="login-recheck">
          <span className="spinner-sm" />
          <p>login ในหน้าต่างที่เปิดขึ้นให้เสร็จ ระบบจะเข้าให้อัตโนมัติ</p>
        </div>
      )}
    </div>
  )
}
