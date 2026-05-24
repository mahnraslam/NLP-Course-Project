import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { listDocuments } from '../api/client'
import Sidebar from '../components/Sidebar'
import ChatPanel from '../components/ChatPanel'
import BlueprintViewer from '../components/BlueprintViewer'
import ConflictList from '../components/ConflictList'

const TAB = { chat: '💬 Chat', viewer: '📐 Blueprint', conflicts: '⚡ Conflicts' }

const S = {
  wrap:    { display: 'flex', height: '100vh', overflow: 'hidden' },
  main:    { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  topbar:  { display: 'flex', alignItems: 'center', gap: 0, padding: '0 16px',
             background: '#0f1b2d', borderBottom: '1px solid #1e3a5f',
             height: 48, flexShrink: 0 },
  backBtn: { background: 'none', border: 'none', color: '#6b7a99', cursor: 'pointer',
             fontSize: 13, padding: '4px 10px 4px 0', marginRight: 8 },
  docName: { fontSize: 13, fontWeight: 600, color: '#94a3b8',
             borderRight: '1px solid #1e3a5f', paddingRight: 16, marginRight: 16,
             maxWidth: 260, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  tabs:    { display: 'flex', gap: 4 },
  tab:     (active) => ({
    padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600,
    cursor: 'pointer', border: 'none',
    background: active ? '#1e3a5f' : 'transparent',
    color: active ? '#60a5fa' : '#6b7a99',
    transition: 'all 0.15s',
  }),
  flex1:   { flex: 1 },
  content: { flex: 1, overflow: 'hidden', display: 'flex' },
  badge:   { padding: '3px 8px', background: '#1a2744', borderRadius: 4,
             fontSize: 11, color: '#6b7a99', marginLeft: 'auto' },
}

export default function ProjectView() {
  const { docId }   = useParams()
  const navigate    = useNavigate()
  const [tab,       setTab]       = useState('chat')
  const [viewPage,  setViewPage]  = useState(1)
  const [doc,       setDoc]       = useState(null)
  const [allDocs,   setAllDocs]   = useState([])
  const [refreshKey,setRefreshKey]= useState(0)

  useEffect(() => {
    listDocuments().then(r => {
      setAllDocs(r.data)
      const found = r.data.find(d => d.doc_id === docId)
      setDoc(found || null)
    }).catch(() => {})
  }, [docId, refreshKey])

  // Called when user clicks a citation page number
  const handleJumpToPage = (pageNum) => {
    setViewPage(pageNum)
    setTab('viewer')
  }

  return (
    <div style={S.wrap}>
      <Sidebar
        selectedId={docId}
        onSelect={d => navigate(`/project/${d.doc_id}`)}
        refreshTrigger={refreshKey}
      />

      <div style={S.main}>
        {/* ── Top bar ── */}
        <div style={S.topbar}>
          <button style={S.backBtn} onClick={() => navigate('/')}>← Back</button>
          <span style={S.docName}>{doc?.filename ?? 'Loading…'}</span>
          <div style={S.tabs}>
            {Object.entries(TAB).map(([key, label]) => (
              <button key={key} style={S.tab(tab === key)} onClick={() => setTab(key)}>
                {label}
              </button>
            ))}
          </div>
          <div style={S.flex1} />
          {doc && (
            <div style={S.badge}>{doc.page_count}p · {doc.chunk_count} chunks</div>
          )}
        </div>

        {/* ── Content ── */}
        <div style={S.content}>
          {tab === 'chat' && (
            <ChatPanel
              docIds={docId ? [docId] : []}
              onJumpToPage={handleJumpToPage}
            />
          )}
          {tab === 'viewer' && (
            <BlueprintViewer
              docId={docId}
              page={viewPage}
              pageCount={doc?.page_count}
              onPageChange={setViewPage}
            />
          )}
          {tab === 'conflicts' && (
            <ConflictList docs={allDocs} />
          )}
        </div>
      </div>
    </div>
  )
}
