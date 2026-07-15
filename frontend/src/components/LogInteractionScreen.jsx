import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { setMode } from '../store/uiSlice'
import { fetchInteractions } from '../store/interactionsSlice'
import InteractionForm from './InteractionForm'
import ChatInterface from './ChatInterface'
import InteractionHistory from './InteractionHistory'

export default function LogInteractionScreen() {
  const dispatch = useDispatch()
  const mode = useSelector((s) => s.ui.mode)
  const selectedId = useSelector((s) => s.hcps.selectedId)
  const hcp = useSelector((s) => s.hcps.list.find((h) => h.id === selectedId))

  useEffect(() => {
    if (selectedId) dispatch(fetchInteractions(selectedId))
  }, [selectedId, dispatch])

  return (
    <div style={{ maxWidth: 860 }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Log Interaction</h1>
        <p style={{ color: 'var(--color-text-muted)', margin: '4px 0 0' }}>
          {hcp ? `Logging for ${hcp.name} · ${hcp.specialty}` : 'Select an HCP to begin'}
        </p>
      </div>

      {/* Mode toggle */}
      <div className="card" style={{ display: 'inline-flex', padding: 4, marginBottom: 20 }}>
        {['form', 'chat'].map((m) => (
          <button
            key={m}
            onClick={() => dispatch(setMode(m))}
            className="btn"
            style={{
              background: mode === m ? 'var(--color-primary)' : 'transparent',
              color: mode === m ? 'white' : 'var(--color-text)',
              padding: '8px 20px',
            }}
          >
            {m === 'form' ? '📝 Structured Form' : '💬 Conversational Chat'}
          </button>
        ))}
      </div>

      <div className="card" style={{ padding: 24, marginBottom: 28 }}>
        {mode === 'form' ? <InteractionForm hcp={hcp} /> : <ChatInterface hcp={hcp} />}
      </div>

      <InteractionHistory hcp={hcp} />
    </div>
  )
}
