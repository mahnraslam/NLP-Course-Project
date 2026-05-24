import { useState, useRef, useEffect } from 'react'
import { queryDocuments } from '../api/client'
import CitationCard from './CitationCard'

const S = {
  wrap:    { display: 'flex', flexDirection: 'column', height: '100%', background: '#0a1628' },
  msgs:    { flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: 16 },
  bubble:  (role) => ({
    maxWidth: '85%', alignSelf: role === 'user' ? 'flex-end' : 'flex-start',
    background: role === 'user' ? '#1e3a5f' : '#111e30',
    border: `1px solid ${role === 'user' ? '#2563eb' : '#1e3a5f'}`,
    borderRadius: role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
    padding: '10px 14px',
  }),
  role:    (role) => ({ fontSize: 11, fontWeight: 700, marginBottom: 5,
                        color: role === 'user' ? '#60a5fa' : '#34d399' }),
  text:    { fontSize: 13, color: '#e2e8f0', lineHeight: 1.7, whiteSpace: 'pre-wrap' },
  cits:    { marginTop: 10 },
  citHdr:  { fontSize: 11, color: '#6b7a99', fontWeight: 600, marginBottom: 4,
             textTransform: 'uppercase', letterSpacing: '0.05em' },
  typing:  { display: 'flex', gap: 4, alignItems: 'center', padding: '10px 14px',
             background: '#111e30', borderRadius: 12, alignSelf: 'flex-start', border: '1px solid #1e3a5f' },
  dot:     (i) => ({ width: 7, height: 7, borderRadius: '50%', background: '#2563eb',
                     animation: `bounce 1s ease-in-out ${i * 0.15}s infinite` }),
  inputRow:{ display: 'flex', gap: 8, padding: '12px 16px',
             borderTop: '1px solid #1e3a5f', background: '#0f1b2d' },
  input:   { flex: 1, background: '#111e30', border: '1px solid #1e3a5f', borderRadius: 8,
             padding: '10px 14px', color: '#e2e8f0', fontSize: 13, outline: 'none',
             transition: 'border-color 0.2s' },
  send:    { padding: '10px 20px', background: '#2563eb', border: 'none', borderRadius: 8,
             color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer',
             transition: 'background 0.15s' },
  empty:   { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
             justifyContent: 'center', gap: 10, color: '#4a5568' },
  emIcon:  { fontSize: 40 },
  emTitle: { fontSize: 15, fontWeight: 600, color: '#6b7a99' },
  emSub:   { fontSize: 12, color: '#374151', textAlign: 'center', maxWidth: 300 },
  suggestions: { display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8, justifyContent: 'center' },
  sug:     { padding: '6px 12px', background: '#111e30', border: '1px solid #1e3a5f',
             borderRadius: 20, fontSize: 11, color: '#60a5fa', cursor: 'pointer' },
}

const SUGGESTIONS = [
  'What is the slab thickness?',
  'What concrete grade is specified?',
  'What rebar sizes are used in columns?',
  'What are the foundation dimensions?',
  'Are there any fire rating requirements?',
]

export default function ChatPanel({ docIds, onJumpToPage }) {
  const [messages, setMessages] = useState([])
  const [input,    setInput]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const bottomRef = useRef()

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  const send = async (text) => {
    const q = (text || input).trim()
    if (!q) return
    setInput('')
    setMessages(m => [...m, { role: 'user', text: q }])
    setLoading(true)
    try {
      const res = await queryDocuments(q, docIds?.length ? docIds : null)
      setMessages(m => [...m, { role: 'ai', text: res.data.answer, citations: res.data.citations }])
    } catch (e) {
      setMessages(m => [...m, { role: 'ai', text: '⚠ Error: ' + (e.response?.data?.detail || e.message), citations: [] }])
    } finally { setLoading(false) }
  }

  return (
    <div style={S.wrap}>
      <style>{`@keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-5px)} }`}</style>

      <div style={S.msgs}>
        {messages.length === 0 ? (
          <div style={S.empty}>
            <div style={S.emIcon}>🏗</div>
            <div style={S.emTitle}>Ask about your blueprints</div>
            <div style={S.emSub}>Ask any technical question about uploaded documents. Answers come with page citations.</div>
            <div style={S.suggestions}>
              {SUGGESTIONS.map(s => (
                <div key={s} style={S.sug} onClick={() => send(s)}>{s}</div>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} style={S.bubble(m.role)}>
              <div style={S.role(m.role)}>{m.role === 'user' ? '👤 You' : '⚙ ConstructOS'}</div>
              <div style={S.text}>{m.text}</div>
              {m.citations?.length > 0 && (
                <div style={S.cits}>
                  <div style={S.citHdr}>📎 Sources ({m.citations.length})</div>
                  {m.citations.map((c, j) => (
                    <CitationCard key={j} citation={c} onJumpToPage={onJumpToPage} />
                  ))}
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div style={S.typing}>
            {[0,1,2].map(i => <div key={i} style={S.dot(i)} />)}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={S.inputRow}>
        <input
          style={S.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask a technical question about the blueprints…"
        />
        <button style={S.send} onClick={() => send()} disabled={loading}>
          {loading ? '…' : 'Ask'}
        </button>
      </div>
    </div>
  )
}
