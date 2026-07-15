import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchHcps, selectHcp } from './store/hcpsSlice'
import LogInteractionScreen from './components/LogInteractionScreen'

export default function App() {
  const dispatch = useDispatch()
  const { list, selectedId, status } = useSelector((s) => s.hcps)

  useEffect(() => {
    dispatch(fetchHcps())
  }, [dispatch])

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Sidebar: HCP list */}
      <aside style={{
        width: 280, borderRight: '1px solid var(--color-border)',
        background: 'var(--color-surface)', padding: '20px 16px', overflowY: 'auto',
      }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 4px' }}>AI-First CRM</h2>
        <p style={{ fontSize: 12, color: 'var(--color-text-muted)', margin: '0 0 20px' }}>
          HCP Module · Log Interaction
        </p>

        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)',
          textTransform: 'uppercase', letterSpacing: 0.4, marginBottom: 8 }}>
          Your HCPs
        </div>

        {status === 'loading' && <p style={{ fontSize: 13 }}>Loading…</p>}

        {list.map((hcp) => (
          <button
            key={hcp.id}
            onClick={() => dispatch(selectHcp(hcp.id))}
            className="btn-ghost"
            style={{
              display: 'block', width: '100%', textAlign: 'left', marginBottom: 8,
              padding: '10px 12px', borderRadius: 10,
              border: hcp.id === selectedId ? '1.5px solid var(--color-primary)' : '1px solid var(--color-border)',
              background: hcp.id === selectedId ? '#eef1ff' : 'white',
            }}
          >
            <div style={{ fontWeight: 600, fontSize: 13 }}>{hcp.name}</div>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              {hcp.specialty} · {hcp.hospital}
            </div>
          </button>
        ))}
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '28px 36px' }}>
        <LogInteractionScreen />
      </main>
    </div>
  )
}
