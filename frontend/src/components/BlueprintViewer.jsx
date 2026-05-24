import { useState, useEffect } from 'react'
import { getPageUrl } from '../api/client'

const S = {
  wrap:    { display: 'flex', flexDirection: 'column', height: '100%', background: '#060e1a' },
  toolbar: { display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px',
             background: '#0f1b2d', borderBottom: '1px solid #1e3a5f', flexShrink: 0 },
  title:   { fontSize: 12, fontWeight: 600, color: '#94a3b8', flex: 1 },
  navBtn:  (disabled) => ({
    padding: '5px 12px', background: disabled ? '#1a2744' : '#1e3a5f',
    border: '1px solid #2563eb', borderRadius: 6, color: disabled ? '#374151' : '#e2e8f0',
    cursor: disabled ? 'not-allowed' : 'pointer', fontSize: 13,
  }),
  pageNum: { fontSize: 13, color: '#60a5fa', fontWeight: 700, minWidth: 70, textAlign: 'center' },
  viewer:  { flex: 1, overflowY: 'auto', display: 'flex', alignItems: 'flex-start',
             justifyContent: 'center', padding: 20 },
  img:     { maxWidth: '100%', borderRadius: 6, boxShadow: '0 4px 24px rgba(0,0,0,0.6)',
             border: '1px solid #1e3a5f' },
  empty:   { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
             justifyContent: 'center', gap: 10, color: '#4a5568' },
  emIcon:  { fontSize: 48 },
  emText:  { fontSize: 13, color: '#6b7a99' },
  badge:   { padding: '3px 8px', background: '#1e3a5f', borderRadius: 4,
             fontSize: 11, color: '#60a5fa', border: '1px solid #2563eb' },
}

export default function BlueprintViewer({ docId, page, pageCount, onPageChange }) {
  const [imgSrc,   setImgSrc]   = useState(null)
  const [imgError, setImgError] = useState(false)
  const [loading,  setLoading]  = useState(false)

  useEffect(() => {
    if (!docId) { setImgSrc(null); return }
    setLoading(true)
    setImgError(false)
    const url = getPageUrl(docId, page)
    setImgSrc(url)
  }, [docId, page])

  const canPrev = page > 1
  const canNext = pageCount ? page < pageCount : !imgError

  if (!docId) return (
    <div style={{ ...S.wrap, ...S.empty }}>
      <div style={S.emIcon}>📐</div>
      <div style={S.emText}>Select a document and click a citation page to view here</div>
    </div>
  )

  return (
    <div style={S.wrap}>
      <div style={S.toolbar}>
        <span style={S.title}>Blueprint Viewer</span>
        {imgError && <span style={S.badge}>⚠ Image not available — text-only doc</span>}
        <button style={S.navBtn(!canPrev)} disabled={!canPrev} onClick={() => onPageChange(page - 1)}>◀</button>
        <span style={S.pageNum}>Page {page}{pageCount ? ` / ${pageCount}` : ''}</span>
        <button style={S.navBtn(!canNext)} disabled={!canNext} onClick={() => onPageChange(page + 1)}>▶</button>
      </div>

      <div style={S.viewer}>
        {loading && !imgError && <div style={S.emText}>Loading page…</div>}
        {imgSrc && !imgError && (
          <img
            src={imgSrc}
            alt={`Page ${page}`}
            style={{ ...S.img, display: loading ? 'none' : 'block' }}
            onLoad={() => setLoading(false)}
            onError={() => { setImgError(true); setLoading(false) }}
          />
        )}
        {imgError && (
          <div style={{ ...S.empty, flex: 'none', paddingTop: 60 }}>
            <div style={S.emIcon}>📄</div>
            <div style={S.emText}>No rendered image for page {page}.<br/>
              This may be a text-only document or poppler is not installed.</div>
          </div>
        )}
      </div>
    </div>
  )
}
