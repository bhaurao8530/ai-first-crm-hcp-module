import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api/api'

export const fetchInteractions = createAsyncThunk(
  'interactions/fetchInteractions',
  async (hcpId) => {
    const res = await api.get('/api/interactions/', { params: hcpId ? { hcp_id: hcpId } : {} })
    return res.data
  }
)

export const createInteraction = createAsyncThunk(
  'interactions/createInteraction',
  async (payload) => {
    const res = await api.post('/api/interactions/', payload)
    return res.data
  }
)

export const updateInteraction = createAsyncThunk(
  'interactions/updateInteraction',
  async ({ id, updates }) => {
    const res = await api.put(`/api/interactions/${id}`, updates)
    return res.data
  }
)

export const recheckCompliance = createAsyncThunk(
  'interactions/recheckCompliance',
  async (id) => {
    const res = await api.post(`/api/interactions/${id}/compliance-check`)
    return res.data
  }
)

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: { list: [], status: 'idle', submitStatus: 'idle', error: null },
  reducers: {
    upsertLocal(state, action) {
      const idx = state.list.findIndex((i) => i.id === action.payload.id)
      if (idx >= 0) state.list[idx] = action.payload
      else state.list.unshift(action.payload)
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => { state.status = 'loading' })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.list = action.payload
      })
      .addCase(createInteraction.pending, (state) => { state.submitStatus = 'loading' })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.submitStatus = 'succeeded'
        state.list.unshift(action.payload)
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.submitStatus = 'failed'
        state.error = action.error.message
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        const idx = state.list.findIndex((i) => i.id === action.payload.id)
        if (idx >= 0) state.list[idx] = action.payload
      })
      .addCase(recheckCompliance.fulfilled, (state, action) => {
        const idx = state.list.findIndex((i) => i.id === action.payload.id)
        if (idx >= 0) state.list[idx] = action.payload
      })
  },
})

export const { upsertLocal } = interactionsSlice.actions
export default interactionsSlice.reducer
