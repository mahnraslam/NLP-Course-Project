import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listDocuments, deleteDocument } from '../api/client'

const S = {
  sidebar: { width: 260, background: '#0f1b2d', borderRight: '1px solid #1e3a5f',
             display: 'flex', flexDirection: 'column', height: '100vh', flexShrink: 0 },
  logo:    { padding: '18px 16px 12px', borderBottom: '1px solid #1e3a5f' },
  logoText:{ fontSize: 18, fontWeight: 700, color: '#60a5fa', letterSpacing: '-0.5px' },
  tagline: { fontSize: 11, color: '#6b7a99', marginTop: 2 },
  section: { padding: '12px 16px 6px', fontSize: 11, fontWeight: 600,
             color: '#6b7a99', letterSpacing: '0.08em', textTransform: 'uppercase' },
  docs:    { flex: 1, overflowY: 'auto', padding: '0 8px' },
  docItem: (active) => ({
    display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px',
    borderRadius: 6, marginBottom: 2, cursor: 'pointer',
    background: active ? '#1e3a5f' : 'transparent',
    border: active ? '1px solid #2563eb' : '1px solid transparent',
    transition: 'all 0.15s',
  }),
  docIcon: { fontSize: 16, flexShrink: 0 },
  docInfo: { flex: 1, minWidth: 0 },
  docName: { fontSize: 12, fontWeight: 500, color: '#e2e8f0',
             whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  docMeta: { fontSize: 10, color: '#6b7a99', marginTop: 1 },
  delBtn:  { background: 'none', border: 'none', cursor: 'pointer',
             color: '#4a5568', fontSize: 14, padding: 2, borderRadius: 3,
             opacity: 0, transition: 'opacity 0.15s' },
  empty:   { padding: 16, fontSize: 12, color: '#4a5568', textAlign: 'center' },
}

export default function Sidebar({ selectedId, onSelect, refreshTrigger }) {
  const [docs,    setDocs]    = useState([])
  const [hoverId, setHoverId] = useState(null)
  const navigate = useNavigate()

  const load = () => listDocuments().then(r => setDocs(r.data)).catch(() => {})

  useEffect(() => { load() }, [refreshTrigger])

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    await deleteDocument(id)
    load()
    if (selectedId === id) navigate('/')
  }

  return (
    <div style={S.sidebar}>
      <div style={S.logo}>
        <div style={S.logoText}>⚙ ConstructOS</div>
        <div style={S.tagline}>AI Construction Intelligence</div>
      </div>

      <div style={S.section}>Documents ({docs.length})</div>

      <div style={S.docs}>
        {docs.length === 0
          ? <div style={S.empty}>No documents yet.<br/>Upload a blueprint to start.</div>
          : docs.map(d => (
            <div key={d.doc_id}
              style={S.docItem(d.doc_id === selectedId)}
              onClick={() => onSelect(d)}
              onMouseEnter={() => setHoverId(d.doc_id)}
              onMouseLeave={() => setHoverId(null)}
            >
              <span style={S.docIcon}>📄</span>
              <div style={S.docInfo}>
                <div style={S.docName}>{d.filename}</div>
                <div style={S.docMeta}>{d.page_count}p · {d.chunk_count} chunks</div>
              </div>
              <button
                style={{ ...S.delBtn, opacity: hoverId === d.doc_id ? 1 : 0 }}
                onClick={(e) => handleDelete(e, d.doc_id)}
                title="Delete"
              >✕</button>
            </div>
          ))
        }
      </div>
    </div>
  )
}
