import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { updateInteraction, recheckCompliance } from '../store/interactionsSlice'

export default function InteractionHistory({ hcp }) {
  const dispatch = useDispatch()
  const list = useSelector((s) => s.interactions.list)
  const [editingId, setEditingId] = useState(null)
  const [editText, setEditText] = useState('')

  if (!hcp) return null

  const startEdit = (interaction) => {
    setEditingId(interaction.id)
    setEditText(interaction.raw_notes || '')
  }

  const saveEdit = async (id) => {
    await dispatch(updateInteraction({ id, updates: { raw_notes: editText } }))
    setEditingId(null)
  }

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Interaction History</h3>
      {list.length === 0 && (
        <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>No interactions logged yet.</p>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {list.map((it) => (
          <div key={it.id} className="card" style={{ padding: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <span style={{ fontWeight: 700, fontSize: 13 }}>#{it.id} · {it.interaction_type}</span>
                <span style={{ color: 'var(--color-text-muted)', fontSize: 12, marginLeft: 8 }}>
                  {new Date(it.date).toLocaleString()} · via {it.created_via}
                </span>
              </div>
              <span className={`tag ${it.compliance_flag === 'OK' ? 'tag-success' : 'tag-warning'}`}>
                {it.compliance_flag}
              </span>
            </div>

            {editingId === it.id ? (
              <div style={{ marginTop: 10 }}>
                <textarea
                  style={{ width: '100%', minHeight: 80, padding: 10, borderRadius: 8, border: '1px solid var(--color-border)' }}
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                />
                <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                  <button className="btn btn-primary" onClick={() => saveEdit(it.id)}>Save (re-runs AI)</button>
                  <button className="btn btn-ghost" onClick={() => setEditingId(null)}>Cancel</button>
                </div>
              </div>
            ) : (
              <>
                <p style={{ margin: '10px 0 4px', fontSize: 13.5 }}>{it.summary}</p>
                <p style={{ margin: '4px 0', fontSize: 12, color: 'var(--color-text-muted)' }}>
                  Topics: {it.topics_discussed || '—'} · Sentiment: {it.sentiment || '—'}
                </p>
                {it.follow_up_action && (
                  <p style={{ margin: '4px 0', fontSize: 12 }}>📌 Follow-up: {it.follow_up_action}</p>
                )}
                <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
                  <button className="btn btn-ghost" onClick={() => startEdit(it)}>Edit</button>
                  <button className="btn btn-ghost" onClick={() => dispatch(recheckCompliance(it.id))}>
                    Recheck Compliance
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
