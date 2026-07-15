import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { createInteraction } from '../store/interactionsSlice'

const TYPES = ['Visit', 'Call', 'Email', 'Conference']
const CHANNELS = ['In-person', 'Phone', 'Video', 'Email']

export default function InteractionForm({ hcp }) {
  const dispatch = useDispatch()
  const submitStatus = useSelector((s) => s.interactions.submitStatus)
  const [form, setForm] = useState({
    interaction_type: 'Visit',
    channel: 'In-person',
    raw_notes: '',
  })
  const [lastResult, setLastResult] = useState(null)

  const update = (key, val) => setForm((f) => ({ ...f, [key]: val }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!hcp) return
    const action = await dispatch(createInteraction({ hcp_id: hcp.id, ...form }))
    if (action.payload) {
      setLastResult(action.payload)
      setForm({ interaction_type: 'Visit', channel: 'In-person', raw_notes: '' })
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
        <div style={{ flex: 1 }}>
          <label style={labelStyle}>Interaction Type</label>
          <select style={inputStyle} value={form.interaction_type}
            onChange={(e) => update('interaction_type', e.target.value)}>
            {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div style={{ flex: 1 }}>
          <label style={labelStyle}>Channel</label>
          <select style={inputStyle} value={form.channel}
            onChange={(e) => update('channel', e.target.value)}>
            {CHANNELS.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      <label style={labelStyle}>Interaction Notes</label>
      <textarea
        style={{ ...inputStyle, minHeight: 120, resize: 'vertical' }}
        placeholder="Describe what happened — topics discussed, products mentioned, samples dropped, HCP's reaction, any follow-up needed..."
        value={form.raw_notes}
        onChange={(e) => update('raw_notes', e.target.value)}
        required
      />
      <p style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 6 }}>
        The LLM (Groq · gemma2-9b-it) will auto-summarize this, extract topics/products/sentiment,
        and run a compliance check when you submit.
      </p>

      <button type="submit" className="btn btn-primary" disabled={!hcp || submitStatus === 'loading'}>
        {submitStatus === 'loading' ? 'Logging with AI…' : 'Log Interaction'}
      </button>

      {lastResult && (
        <div className="card" style={{ marginTop: 20, padding: 16, background: '#fafbff' }}>
          <div style={{ fontWeight: 700, marginBottom: 6 }}>✅ Logged &amp; Summarized by AI</div>
          <p style={{ margin: '4px 0' }}><strong>Summary:</strong> {lastResult.summary}</p>
          <p style={{ margin: '4px 0' }}><strong>Sentiment:</strong> {lastResult.sentiment}</p>
          <p style={{ margin: '4px 0' }}><strong>Topics:</strong> {lastResult.topics_discussed || '—'}</p>
          <p style={{ margin: '4px 0' }}>
            <strong>Compliance:</strong>{' '}
            <span className={`tag ${lastResult.compliance_flag === 'OK' ? 'tag-success' : 'tag-warning'}`}>
              {lastResult.compliance_flag}
            </span>
          </p>
        </div>
      )}
    </form>
  )
}

const labelStyle = { display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--color-text-muted)' }
const inputStyle = {
  width: '100%', padding: '10px 12px', borderRadius: 10,
  border: '1px solid var(--color-border)', marginBottom: 16, background: 'white',
}
