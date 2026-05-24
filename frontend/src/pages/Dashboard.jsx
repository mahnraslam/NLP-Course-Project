import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import UploadZone from '../components/UploadZone'

const S = {
  wrap:    { display: 'flex', height: '100vh', overflow: 'hidden' },
  main:    { flex: 1, display: 'flex', flexDirection: 'column',
             background: '#0a1628', overflowY: 'auto' },
  hero:    { padding: '40px 48px 24px', borderBottom: '1px solid #1e3a5f' },
  title:   { fontSize: 28, fontWeight: 800, color: '#e2e8f0', marginBottom: 6,
             letterSpacing: '-0.5px' },
  sub:     { fontSize: 14, color: '#6b7a99', maxWidth: 500, lineHeight: 1.6 },
  body:    { padding: '32px 48px', maxWidth: 700 },
  secTitle:{ fontSize: 13, fontWeight: 700, color: '#6b7a99', marginBottom: 16,
             textTransform: 'uppercase', letterSpacing: '0.08em' },
  features:{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 28 },
  feat:    { background: '#111e30', border: '1px solid #1e3a5f', borderRadius: 8, padding: 16 },
  fIcon:   { fontSize: 22, marginBottom: 8 },
  fTitle:  { fontSize: 13, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 },
  fSub:    { fontSize: 11, color: '#6b7a99', lineHeight: 1.5 },
}

const FEATURES = [
  { icon: '🔍', title: 'Blueprint Q&A', desc: 'Ask technical questions. Get cited answers from exact document pages.' },
  { icon: '⚡', title: 'Conflict Detection', desc: 'Find contradictions between specs and drawings across 10 construction topics.' },
  { icon: '📐', title: 'Blueprint Viewer', desc: 'Click a citation to jump directly to that page in the drawing.' },
  { icon: '🧠', title: 'Vision Analysis', desc: 'Drawing-heavy pages are analysed visually — not just text extraction.' },
]

export default function Dashboard() {
  const [refreshKey, setRefreshKey] = useState(0)
  const navigate    = useNavigate()

  return (
    <div style={S.wrap}>
      <Sidebar
        selectedId={null}
        onSelect={d => navigate(`/project/${d.doc_id}`)}
        refreshTrigger={refreshKey}
      />
      <div style={S.main}>
        <div style={S.hero}>
          <div style={S.title}>⚙ ConstructOS</div>
          <div style={S.sub}>
            AI-powered construction document intelligence. Upload blueprints, specs, or RFIs
            and ask technical questions — with page-level citations.
          </div>
        </div>
        <div style={S.body}>
          <div style={S.secTitle}>Upload a Document</div>
          <UploadZone onSuccess={() => setRefreshKey(k => k + 1)} />
          <div style={S.features}>
            {FEATURES.map(f => (
              <div key={f.title} style={S.feat}>
                <div style={S.fIcon}>{f.icon}</div>
                <div style={S.fTitle}>{f.title}</div>
                <div style={S.fSub}>{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
