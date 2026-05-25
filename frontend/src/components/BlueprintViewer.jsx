import { useState } from 'react'

const S = {
  wrap:    { flex: 1, display: 'flex', flexDirection: 'column', height: '100%',
             background: '#0a1628', overflow: 'hidden' },
  toolbar: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
             padding: '10px 16px', borderBottom: '1px solid #1e3a5f', background: '#0f1b2d',
             flexShrink: 0 },
  btn:     (disabled) => ({
    padding: '6px 16px', borderRadius: 6, border: '1px solid #1e3a5f',
    background: disabled ? '#0a1628' : '#1e3a5f',
    color: disabled ? '#374151' : '#e2e8f0', fontSize: 12, fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer', transition: 'all 0.15s',
  }),
  pageInfo:{ fontSize: 13, fontWeight: 600, color: '#94a3b8', minWidth: 120, textAlign: 'center' },
  imgWrap: { flex: 1, overflow: 'auto', display: 'flex', justifyContent: 'center',
             alignItems: 'flex-start', padding: 16 },
  img:     { maxWidth: '100%', borderRadius: 6, border: '1px solid #1e3a5f',
             boxShadow: '0 4px 24px rgba(0,0,0,0.4)' },
  empty:   { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
             justifyContent: 'center', gap: 10, color: '#4a5568' },
  emIcon:  { fontSize: 40 },
  emTitle: { fontSize: 15, fontWeight: 600, color: '#6b7a99' },
  emSub:   { fontSize: 12, color: '#374151', textAlign: 'center', maxWidth: 300 },
  errMsg:  { textAlign: 'center', padding: 32, color: '#f87171', fontSize: 13 },
}

export default function BlueprintViewer({ docId, page = 1, pageCount, onPageChange }) {
  const [imgError, setImgError] = useState(false)

  if (!docId) {
    return (
      <div style={S.empty}>
        <div style={S.emIcon}>📐</div>
        <div style={S.emTitle}>No document selected</div>
        <div style={S.emSub}>Select a document from the sidebar to view its blueprint pages.</div>
      </div>
    )
  }

  // PNG pages served from backend at /pages/{docId}_page_{n}.png
  const imgUrl = `/pages/${docId}_page_${page}.png`
  const maxPage = pageCount || 1

  return (
    <div style={S.wrap}>
      <div style={S.toolbar}>
        <button
          style={S.btn(page <= 1)}
          onClick={() => onPageChange?.(Math.max(1, page - 1))}
          disabled={page <= 1}
        >
          ← Prev
        </button>
        <span style={S.pageInfo}>Page {page} of {maxPage}</span>
        <button
          style={S.btn(page >= maxPage)}
          onClick={() => onPageChange?.(Math.min(maxPage, page + 1))}
          disabled={page >= maxPage}
        >
          Next →
        </button>
      </div>

      <div style={S.imgWrap}>
        {imgError ? (
          <div style={S.errMsg}>
            ⚠ Page image not found.<br />
            This page may not have been rendered during upload.
          </div>
        ) : (
          <img
            src={imgUrl}
            alt={`Blueprint page ${page}`}
            style={S.img}
            onError={() => setImgError(true)}
            onLoad={() => setImgError(false)}
            key={`${docId}_${page}`}
          />
        )}
      </div>
    </div>
  )
}
