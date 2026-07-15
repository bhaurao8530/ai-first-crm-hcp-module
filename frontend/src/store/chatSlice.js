import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api/api'

export const sendChatMessage = createAsyncThunk(
  'chat/sendChatMessage',
  async ({ sessionId, message, hcpId }) => {
    const res = await api.post('/api/chat/', { session_id: sessionId, message, hcp_id: hcpId })
    return res.data
  }
)

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    sessionId: `session-${Date.now()}`,
    messages: [
      { role: 'assistant', text: "Hi! Tell me about your visit in plain English — e.g. \"Met Dr. Rao today, discussed CardioX trial results, she was positive and wants follow-up data next week.\"" },
    ],
    status: 'idle',
  },
  reducers: {
    addUserMessage(state, action) {
      state.messages.push({ role: 'user', text: action.payload })
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => { state.status = 'loading' })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.messages.push({
          role: 'assistant',
          text: action.payload.reply,
          toolUsed: action.payload.tool_used,
          interaction: action.payload.interaction,
        })
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status = 'failed'
        state.messages.push({ role: 'assistant', text: `Error: ${action.error.message}` })
      })
  },
})

export const { addUserMessage } = chatSlice.actions
export default chatSlice.reducer
