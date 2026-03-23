import { create } from 'zustand'

interface Note {
  pitch: number
  start: number
  duration: number
  velocity?: number
}

interface TranscriptionData {
  notes: Note[]
  time_signature: string
  key_signature: string
  tempo: number
  instrument_type: string
}

interface Transcription {
  id: number
  title: string
  instrument_type: string
  status: string
  notation_data: TranscriptionData | null
  created_at: string
  duration: number
}

interface TranscriptionState {
  currentTranscription: Transcription | null
  transcriptions: Transcription[]
  
  setCurrentTranscription: (transcription: Transcription | null) => void
  setTranscriptions: (transcriptions: Transcription[]) => void
  addTranscription: (transcription: Transcription) => void
  updateTranscription: (id: number, updates: Partial<Transcription>) => void
  removeTranscription: (id: number) => void
}

export const useTranscriptionStore = create<TranscriptionState>((set) => ({
  currentTranscription: null,
  transcriptions: [],
  
  setCurrentTranscription: (transcription) => set({ currentTranscription: transcription }),
  
  setTranscriptions: (transcriptions) => set({ transcriptions }),
  
  addTranscription: (transcription) => set((state) => ({
    transcriptions: [transcription, ...state.transcriptions]
  })),
  
  updateTranscription: (id, updates) => set((state) => ({
    transcriptions: state.transcriptions.map(t => 
      t.id === id ? { ...t, ...updates } : t
    ),
    currentTranscription: state.currentTranscription?.id === id 
      ? { ...state.currentTranscription, ...updates }
      : state.currentTranscription
  })),
  
  removeTranscription: (id) => set((state) => ({
    transcriptions: state.transcriptions.filter(t => t.id !== id),
    currentTranscription: state.currentTranscription?.id === id 
      ? null 
      : state.currentTranscription
  }))
}))
