import axios from 'axios'
const BASE = import.meta.env.VITE_API_URL || ''
const api  = axios.create({ baseURL: BASE })

export const uploadDocument  = (file) => { const f = new FormData(); f.append('file', file); return api.post('/api/documents/upload', f) }
export const listDocuments   = ()     => api.get('/api/documents/')
export const deleteDocument  = (id)   => api.delete(`/api/documents/${id}`)
export const getPageUrl      = (docId, page) => `${BASE}/pages/${docId}_page_${page}.png`
export const queryDocuments  = (question, doc_ids=null, top_k=5) => api.post('/api/query/', { question, doc_ids, top_k })
export const detectConflicts = (doc_id_a, doc_id_b, filename_a='', filename_b='') =>
  api.post('/api/conflicts/detect', { doc_id_a, doc_id_b, filename_a, filename_b })
