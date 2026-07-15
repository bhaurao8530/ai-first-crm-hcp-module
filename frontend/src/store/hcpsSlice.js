import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api/api'

export const fetchHcps = createAsyncThunk('hcps/fetchHcps', async () => {
  const res = await api.get('/api/hcps/')
  return res.data
})

const hcpsSlice = createSlice({
  name: 'hcps',
  initialState: { list: [], selectedId: null, status: 'idle', error: null },
  reducers: {
    selectHcp(state, action) {
      state.selectedId = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.pending, (state) => { state.status = 'loading' })
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.list = action.payload
        if (!state.selectedId && action.payload.length) {
          state.selectedId = action.payload[0].id
        }
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
  },
})

export const { selectHcp } = hcpsSlice.actions
export default hcpsSlice.reducer
