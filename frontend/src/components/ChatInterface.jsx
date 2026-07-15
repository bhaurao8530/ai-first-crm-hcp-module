import React, { useState, useRef, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { sendChatMessage, addUserMessage } from '../store/chatSlice'

export default function ChatInterface({ hcp }) {
  const dispatch = useDispatch()
  const { messages, status, sessionId } = useSelector((s) => s.chat)
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || !hcp) return
    dispatch(addUserMessage(input))
    const msg = input
    setInput('')
    await dispatch(sendChatMessage({ sessionId, message: msg, hcpId: hcp.id }))
  }

  return (
    <div>
      <div style={{
        height: 340, overflowY: 'auto', border: '1px solid var(--color-border)',
        borderRadius: 12, padding: 16, marginBottom: 12, background: '#fafbfc',
      }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
            marginBottom: 10,
          }}>
            <div style={{
              maxWidth: '75%', padding: '10px 14px', borderRadius: 14,
              background: m.role === 'user' ? 'var(--color-primary)' : 'white',
              color: m.role === 'user' ? 'white' : 'var(--color-text)',
              border: m.role === 'user' ? 'none' : '1px solid var(--color-border)',
              fontSize: 13.5,
            }}>
              {m.text}
              {m.toolUsed && m.toolUsed !== 'chitchat' && (
                <div style={{ marginTop: 6 }}>
                  <span className="tag tag-neutral">tool: {m.toolUsed}</span>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} style={{ display: 'flex', gap: 8 }}>
        <input
          style={{ flex: 1, padding: '10px 14px', borderRadius: 10, border: '1px solid var(--color-border)' }}
          placeholder={hcp ? `Message about ${hcp.name}...` : 'Select an HCP first'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={!hcp}
        />
        <button type="submit" className="btn btn-primary" disabled={!hcp || status === 'loading'}>
          {status === 'loading' ? 'Thinking…' : 'Send'}
        </button>
      </form>
      <p style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 8 }}>
        Try: "log a visit with samples dropped", "schedule a follow-up for interaction 3 next Monday",
        "what's Dr. Rao's history", or "recheck compliance on interaction 2".
      </p>
    </div>
  )
}
