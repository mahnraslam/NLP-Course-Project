import { useState } from 'react'

const S = {
  card: (score) => ({
    background: '#111e30',
    borderLeft: `3px solid ${score > 0.7 ? '#2563eb' : score > 0.4 ? '#7c3aed' : '#374151'}`,
    borderRadius: '0 6px 6px 0', padding: '8px 12px', margin: '6px 0',
    cursor: 'pointer', transition: 'background 0.15s',
  }),
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 },
  file:   { fontSize: 12, fontWeight: 600, color: '#60a5fa' },
  page:   { fontSize: 11, color: '#93c5fd', background: '#1e3a5f',
            padding: '2px 7px', borderRadius: 10, cursor: 'pointer',
            border: '1px solid #2563eb', fontWeight: 600 },
  score:  { fontSize: 10, color: '#6b7a99' },
  quote:  { fontSize: 11, color: '#94a3b8', fontStyle: 'italic', lineHeight: 1.5,
            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
            overflow: 'hidden' },
  hint:   { fontSize: 10, color: '#4a5568', marginTop: 4 },

  // Inline thumbnail
  thumbWrap: {
    marginTop: 8, borderRadius: 4, overflow: 'hidden',
    border: '1px solid #1e3a5f', background: '#0a1628',
    position: 'relative',
  },
  thumb: {
    width: '100%', display: 'block', maxHeight: 180,
    objectFit: 'contain', background: '#0a1628',
  },
  thumbBadge: {
    position: 'absolute', top: 4, right: 4,
    background: 'rgba(15,27,45,0.85)', borderRadius: 4,
    padding: '2px 6px', fontSize: 10, color: '#60a5fa',
    fontWeight: 600,
  },
  thumbToggle: {
    marginTop: 5, fontSize: 10, color: '#2563eb', cursor: 'pointer',
    textDecoration: 'underline', background: 'none', border: 'none',
    padding: 0,
  },
}

export default function CitationCard({ citation, onJumpToPage }) {
  const { filename, page_num, chunk_text, relevance_score, image_url } = citation
  const score = relevance_score ?? 0
  const [showThumb, setShowThumb] = useState(false)
  const [thumbError, setThumbError] = useState(false)

  const handleJump = (e) => {
    e.stopPropagation()
    onJumpToPage?.(page_num)
  }

  const toggleThumb = (e) => {
    e.stopPropagation()
    setShowThumb(v => !v)
  }

  return (
    <div style={S.card(score)} onClick={handleJump}>
      <div style={S.header}>
        <span style={S.file}>📄 {filename}</span>
        <span style={S.page} title="Click to jump to this page in blueprint viewer">
          Page {page_num}
        </span>
      </div>

      <div style={S.quote}>
        &ldquo;{chunk_text?.slice(0, 180)}{chunk_text?.length > 180 ? '…' : ''}&rdquo;
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 4 }}>
        <div style={S.hint}>
          Relevance: {(score * 100).toFixed(0)}% · Click to view in blueprint →
        </div>
        {image_url && !thumbError && (
          <button style={S.thumbToggle} onClick={toggleThumb}>
            {showThumb ? 'Hide preview' : '🖼 Preview page'}
          </button>
        )}
      </div>

      {/* Inline page image preview */}
      {showThumb && image_url && !thumbError && (
        <div style={S.thumbWrap}>
          <img
            src={image_url}
            alt={`Page ${page_num} preview`}
            style={S.thumb}
            onError={() => { setThumbError(true); setShowThumb(false) }}
          />
          <div style={S.thumbBadge}>Page {page_num}</div>
        </div>
      )}
    </div>
  )
} 