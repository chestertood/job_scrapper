import { useState } from "react";
import Pagination from "./Pagination";

const OFFERS_PAGE_SIZE = 10;

function statusBadgeClass(status) {
  if (status?.includes("หมดอายุ")) return "badge-red";
  if (status?.includes("เปิดรับ")) return "badge-green";
  return "";
}

export default function MyOffers({ data, busy, onRemove }) {
  const [page, setPage] = useState(1);

  // deletable offers first, expired ones after
  const sorted = [...data.offers].sort(
    (a, b) => (b.can_delete ? 1 : 0) - (a.can_delete ? 1 : 0),
  );
  const totalPages = Math.max(1, Math.ceil(sorted.length / OFFERS_PAGE_SIZE));
  const shown = sorted.slice(
    (page - 1) * OFFERS_PAGE_SIZE,
    page * OFFERS_PAGE_SIZE,
  );

  return (
    <div className="my-offers">
      <div className="status">
        {data.remaining === null
          ? ""
          : `นำเสนองานได้อีก ${data.remaining} โพสต์`}
      </div>
      <div className="offers-table-wrap">
        <table className="offers-table">
          <thead>
            <tr>
              <th>ชื่องาน</th>
              <th>สถานะ</th>
              <th>ราคาที่เสนอ</th>
              <th>ระยะเวลา</th>
              <th>ลงประกาศเมื่อ</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {shown.map((o) => (
              <tr key={o.index}>
                <td className="offers-table-title">
                  {o.url ? (
                    <a href={o.url} target="_blank" rel="noreferrer" title={o.title}>
                      {o.title}
                    </a>
                  ) : (
                    o.title
                  )}
                </td>
                <td>
                  <span className={`badge ${statusBadgeClass(o.status)}`}>
                    {o.status}
                  </span>
                </td>
                <td>{o.price} บาท</td>
                <td>{o.days}</td>
                <td>{o.posted}</td>
                <td>
                  {o.can_delete && (
                    <button
                      className="offer-row-remove"
                      disabled={busy === o.index}
                      onClick={() =>
                        confirm(`ลบข้อเสนองาน "${o.title}" จริงๆ?`) &&
                        onRemove(o.index)
                      }
                    >
                      {busy === o.index ? <span className="spinner-sm" /> : "ลบ"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}
