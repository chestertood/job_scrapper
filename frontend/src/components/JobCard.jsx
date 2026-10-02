import { useState } from 'react'
import { submitApply } from '../api'
import { jobDate, MIN_SCRIPT_CHARS } from '../utils'
import fastworkLogo from '../assets/fastwork-logo.svg'

export default function JobCard({ job, onRemove, script }) {
  const budget = Number(job.budget) > 0 ? `${job.budget} บาท` : 'ไม่กำหนด'
  const url = `https://jobboard.fastwork.co/jobs/${job.id}`
  const [price, setPrice] = useState(Number(job.budget) > 0 ? job.budget : '')
  const [when, setWhen] = useState('')
  const [accepted, setAccepted] = useState(false)
  const [applyError, setApplyError] = useState(null)
  const [invalid, setInvalid] = useState({ price: false, when: false })

  const priceInvalid = price.toString().trim() === '' || Number(price) <= 0
  const whenInvalid = when.trim() === ''
  const scriptInvalid = script.trim().length < MIN_SCRIPT_CHARS

  const accept = () => {
    if (priceInvalid || whenInvalid || scriptInvalid) {
      setInvalid({ price: priceInvalid, when: whenInvalid })
      if (scriptInvalid) {
        setApplyError(`Application script สั้นไป (ต้องมากกว่า ${MIN_SCRIPT_CHARS} ตัวอักษร) — ไปตั้งค่าที่แท็บ Profile`)
      }
      return
    }
    if (!confirm(`ยืนยันเสนองาน "${job.title}" ราคา ${price} บาท?`)) return
    setAccepted(true)
    setApplyError(null)
    submitApply({ job: url, price, days: when, script })
      .then(() => onRemove(job.id)) // นำเสนอแล้ว — เอาออกจากลิสต์เหมือนกด ✕ ด้วย mechanism เดิม
      .catch(() => setApplyError('เชื่อมต่อ main.py ไม่ได้ — รันมันอยู่ไหม?'))
  }

  return (
    <tr className="job-row">
      <td className="job-logo">
        <img src={fastworkLogo} alt="Fastwork" />
      </td>
      <td className="job-row-title">
        <a href={url} target="_blank" rel="noreferrer" title={job.title}>
          {job.title}
        </a>
      </td>
      <td>
        <span className="badge">{budget}</span>
      </td>
      <td className="job-muted">{job.type}</td>
      <td className="job-muted">{jobDate(job).toISOString().slice(0, 10)}</td>
      <td>
        <input
          type="number"
          min="0"
          className={`offer-price${invalid.price ? ' input-error' : ''}`}
          placeholder="ราคา"
          value={price}
          onChange={(e) => {
            setPrice(e.target.value)
            setInvalid((v) => ({ ...v, price: false }))
          }}
          disabled={accepted}
        />
      </td>
      <td>
        <input
          type="text"
          className={`offer-when${invalid.when ? ' input-error' : ''}`}
          placeholder="วันเวลา"
          value={when}
          onChange={(e) => {
            setWhen(e.target.value)
            setInvalid((v) => ({ ...v, when: false }))
          }}
          disabled={accepted}
        />
      </td>
      <td>
        <button className="offer-accept" onClick={accept} disabled={accepted}>
          {accepted ? '✓ รับแล้ว' : 'Accept'}
        </button>
        {applyError && <div className="offer-error">{applyError}</div>}
      </td>
      <td>
        <button
          className="job-remove"
          title="ลบงานนี้"
          onClick={() => confirm(`ลบงาน "${job.title}" ออกจากลิสต์?`) && onRemove(job.id)}
        >
          ✕
        </button>
      </td>
    </tr>
  )
}
