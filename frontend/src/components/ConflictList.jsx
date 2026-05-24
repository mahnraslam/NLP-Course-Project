import { useState } from 'react'
import { detectConflicts, listDocuments } from '../api/client'

const SEVERITY_COLOR = { high: '#ef4444', medium: '#f59e0b', low: '#6b7280' }
const SEVERITY_BG    = { high: '#1a0a0a', medium: '#1a1200', low: '#111827' }

const S = {
  wrap:    { padding: 16, height: '100%', overflowY: 'auto' },
  header:  { marginBottom: 16 },
  title:   { fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 },
  sub:     { fontSize: 12, color: '#6b7a99' },
  row:     { display: 'flex', gap: 10, marginBottom: 16, alignItems: 'flex-end' },
  sel:     { flex: 1, background: '#111e30', border: '1px solid #1e3a5f', borderRadius: 6,
             padding: '8px 12px', color: '#e2e8f0', fontSize: 12 },
  btn:     (loading) => ({
    padding: '9px 18px', background: loading ? '#374151' : '#dc2626',
    border: 'none', borderRadius: 6, color: '#fff', fontSize: 13,
    fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
  }),
  noConf:  { padding: '32px 0', textAlign: 'center', color: '#374151', fontSize: 13 },
  badge:   (sev) => ({
    display: 'inline-block', padding: '2px 8px', borderRadius: 10, fontSize: 10,
    fontWeight: 700, background: SEVERITY_BG[sev], color: SEVERITY_COLOR[sev],
    border: `1px solid ${SEVERITY_COLOR[sev]}`, textTransform: 'uppercase',
  }),
  card:    (sev) => ({
    background: SEVERITY_BG[sev], borderLeft: `3px solid ${SEVERITY_COLOR[sev]}`,
    borderRadius: '0 8px 8px 0', padding: 14, marginBottom: 12,
  }),
  cardTop: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 },
  topic:   { fontSize: 11, color: '#94a3b8', fontWeight: 600, flex: 1,
             textTransform: 'uppercase', letterSpacing: '0.05em' },
  desc:    { fontSize: 13, color: '#e2e8f0', marginBottom: 10, lineHeight: 1.6 },
  quotes:  { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 },
  qBox:    { background: '#0a1628', borderRadius: 6, padding: '8px 10px' },
  qLabel:  { fontSize: 10, fontWeight: 700, color: '#6b7a99', marginBottom: 4,
             textTransform: 'uppercase', letterSpacing: '0.05em' },
  qText:   { fontSize: 11, color: '#94a3b8', fontStyle: 'italic', lineHeight: 1.5 },
  qPage:   { fontSize: 10, color: '#4a5568', marginTop: 4 },
  summary: { padding: '10px 14px', background: '#111e30', borderRadius: 6,
             marginBottom: 16, fontSize: 12, color: '#94a3b8',
             border: '1px solid #1e3a5f' },
}

export default function ConflictList({ docs }) {
  const [selA,      setSelA]      = useState('')
  const [selB,      setSelB]      = useState('')
  const [conflicts, setConflicts] = useState(null)
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState(null)

  const run = async () => {
    if (!selA || !selB || selA === selB) {
      setError('Please select two different documents.'); return
    }
    setLoading(true); setError(null); setConflicts(null)
    const docA = docs.find(d => d.doc_id === selA)
    const docB = docs.find(d => d.doc_id === selB)
    try {
      const res = await detectConflicts(selA, selB, docA?.filename || '', docB?.filename || '')
      setConflicts(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Conflict detection failed.')
    } finally { setLoading(false) }
  }

  return (
    <div style={S.wrap}>
      <div style={S.header}>
        <div style={S.title}>⚡ Conflict Detection</div>
        <div style={S.sub}>Select two documents to check for contradictions across 10 construction topics.</div>
      </div>

      <div style={S.row}>
        <select style={S.sel} value={selA} onChange={e => setSelA(e.target.value)}>
          <option value="">— Document A —</option>
          {docs.map(d => <option key={d.doc_id} value={d.doc_id}>{d.filename}</option>)}
        </select>
        <select style={S.sel} value={selB} onChange={e => setSelB(e.target.value)}>
          <option value="">— Document B —</option>
          {docs.map(d => <option key={d.doc_id} value={d.doc_id}>{d.filename}</option>)}
        </select>
        <button style={S.btn(loading)} onClick={run} disabled={loading}>
          {loading ? 'Checking…' : '⚡ Detect'}
        </button>
      </div>

      {error && <div style={{ ...S.summary, borderColor: '#ef4444', color: '#f87171' }}>{error}</div>}

      {loading && (
        <div style={S.summary}>
          Checking 10 construction topics (slab, rebar, columns, walls, levels…). Max 10 LLM calls.
        </div>
      )}

      {conflicts && (
        <>
          <div style={S.summary}>
            {conflicts.total === 0
              ? '✓ No contradictions found across all 10 checked topics.'
              : `⚠ Found ${conflicts.total} conflict${conflicts.total > 1 ? 's' : ''} between the two documents.`
            }
          </div>
          {conflicts.conflicts.map((c, i) => (
            <div key={i} style={S.card(c.severity)}>
              <div style={S.cardTop}>
                <span style={S.badge(c.severity)}>{c.severity}</span>
                <span style={S.topic}>{c.topic}</span>
              </div>
              <div style={S.desc}>{c.description}</div>
              <div style={S.quotes}>
                <div style={S.qBox}>
                  <div style={S.qLabel}>Doc A — {c.filename_a}</div>
                  <div style={S.qText}>"{c.quote_a}"</div>
                  <div style={S.qPage}>Page {c.page_a}</div>
                </div>
                <div style={S.qBox}>
                  <div style={S.qLabel}>Doc B — {c.filename_b}</div>
                  <div style={S.qText}>"{c.quote_b}"</div>
                  <div style={S.qPage}>Page {c.page_b}</div>
                </div>
              </div>
            </div>
          ))}
        </>
      )}

      {conflicts?.total === 0 && (
        <div style={S.noConf}>✓ No contradictions found.<br/>These documents appear consistent on checked topics.</div>
      )}
    </div>
  )
}
