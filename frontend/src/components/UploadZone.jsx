import { useState, useRef } from 'react'
import { uploadDocument } from '../api/client'

const S = {
  zone: (drag) => ({
    border: `2px dashed ${drag ? '#2563eb' : '#1e3a5f'}`,
    borderRadius: 10, padding: '32px 20px', textAlign: 'center',
    background: drag ? '#0d2040' : '#0f1b2d',
    cursor: 'pointer', transition: 'all 0.2s',
  }),
  icon:    { fontSize: 36, marginBottom: 10 },
  title:   { fontSize: 14, fontWeight: 600, color: '#e2e8f0', marginBottom: 4 },
  sub:     { fontSize: 12, color: '#6b7a99' },
  btn:     { marginTop: 14, padding: '8px 20px', background: '#2563eb',
             border: 'none', borderRadius: 6, color: '#fff', fontSize: 13,
             fontWeight: 600, cursor: 'pointer' },
  prog:    { marginTop: 14, fontSize: 12, color: '#60a5fa' },
  error:   { marginTop: 10, fontSize: 12, color: '#f87171' },
  success: { marginTop: 10, fontSize: 12, color: '#34d399' },
}

export default function UploadZone({ onSuccess }) {
  const [drag,    setDrag]    = useState(false)
  const [loading, setLoading] = useState(false)
  const [msg,     setMsg]     = useState(null)
  const [err,     setErr]     = useState(null)
  const inputRef = useRef()

  const upload = async (file) => {
    if (!file || !file.name.endsWith('.pdf')) {
      setErr('Only PDF files are supported.'); return
    }
    setLoading(true); setErr(null); setMsg(null)
    try {
      const res = await uploadDocument(file)
      const d   = res.data
      setMsg(`✓ ${d.filename} — ${d.page_count} pages, ${d.chunk_count} chunks indexed`)
      onSuccess?.()
    } catch (e) {
      setErr(e.response?.data?.detail || 'Upload failed. Check backend is running.')
    } finally { setLoading(false) }
  }

  const onDrop = (e) => { e.preventDefault(); setDrag(false); upload(e.dataTransfer.files[0]) }

  return (
    <div
      style={S.zone(drag)}
      onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      onClick={() => !loading && inputRef.current.click()}
    >
      <div style={S.icon}>📐</div>
      <div style={S.title}>
        {loading ? 'Processing…' : 'Drop a blueprint PDF here'}
      </div>
      <div style={S.sub}>
        {loading
          ? 'Extracting text, running vision analysis, embedding chunks…'
          : 'Blueprints, specs, RFIs, inspection reports — any construction PDF'}
      </div>
      {!loading && <button style={S.btn} onClick={e => { e.stopPropagation(); inputRef.current.click() }}>Browse PDF</button>}
      {msg && <div style={S.success}>{msg}</div>}
      {err && <div style={S.error}>{err}</div>}
      <input ref={inputRef} type="file" accept=".pdf" style={{ display: 'none' }}
             onChange={e => upload(e.target.files[0])} />
    </div>
  )
}
