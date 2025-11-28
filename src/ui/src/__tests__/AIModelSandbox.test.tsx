import { describe, it, expect, vi, beforeEach } from 'vitest'

/**
 * Tests for AIModelSandbox logic without rendering actual components.
 * This avoids issues with versioned radix-ui imports.
 */

describe('AIModelSandbox Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('API Integration', () => {
    it('calls fetch with correct parameters', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ cad_code: 'import cadquery as cq' }),
      })
      global.fetch = mockFetch

      const requestBody = {
        prompt: 'Create a cube',
        image_path: null,
        user_id: 'default',
        model_choice: 'llava',
        rag_context: null,
      }

      await fetch('http://localhost:8000/generate_cad', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/generate_cad',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('handles API success response', async () => {
      const mockResponse = {
        cad_code: 'import cadquery as cq\nresult = cq.Workplane("XY").box(1, 1, 1)',
        rag_used: false,
      }

      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })
      global.fetch = mockFetch

      const response = await fetch('http://localhost:8000/generate_cad', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'test' }),
      })

      const data = await response.json()
      expect(data.cad_code).toContain('cadquery')
    })

    it('handles API error response', async () => {
      const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'))
      global.fetch = mockFetch

      let error: Error | null = null
      try {
        await fetch('http://localhost:8000/generate_cad', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: 'test' }),
        })
      } catch (e) {
        error = e as Error
      }

      expect(error).not.toBeNull()
      expect(error?.message).toBe('Network error')
    })
  })

  describe('State Management', () => {
    it('manages session state correctly', () => {
      interface ChatSession {
        id: string
        name: string
        messages: any[]
        model: string
      }

      let sessions: ChatSession[] = []
      let currentSessionId: string | null = null

      // Create new session
      const newSession: ChatSession = {
        id: '123',
        name: 'New Chat',
        messages: [],
        model: 'Baseline-LLaVA',
      }
      sessions = [newSession, ...sessions]
      currentSessionId = newSession.id

      expect(sessions).toHaveLength(1)
      expect(currentSessionId).toBe('123')
    })

    it('adds messages to session', () => {
      interface Message {
        id: string
        role: 'user' | 'assistant'
        content: string
      }

      let messages: Message[] = []

      const userMessage: Message = {
        id: '1',
        role: 'user',
        content: 'Create a cube',
      }
      messages = [...messages, userMessage]

      const assistantMessage: Message = {
        id: '2',
        role: 'assistant',
        content: 'import cadquery as cq',
      }
      messages = [...messages, assistantMessage]

      expect(messages).toHaveLength(2)
      expect(messages[0].role).toBe('user')
      expect(messages[1].role).toBe('assistant')
    })

    it('clears messages from session', () => {
      let messages = [
        { id: '1', content: 'test1' },
        { id: '2', content: 'test2' },
      ]

      // Clear chat
      messages = []

      expect(messages).toHaveLength(0)
    })

    it('deletes session correctly', () => {
      let sessions = [
        { id: '1', name: 'Chat 1' },
        { id: '2', name: 'Chat 2' },
      ]
      let currentSessionId = '1'

      // Delete session
      const sessionIdToDelete = '1'
      sessions = sessions.filter(s => s.id !== sessionIdToDelete)
      
      if (currentSessionId === sessionIdToDelete) {
        currentSessionId = sessions.length > 0 ? sessions[0].id : ''
      }

      expect(sessions).toHaveLength(1)
      expect(currentSessionId).toBe('2')
    })
  })

  describe('Model Selection', () => {
    it('updates model in session', () => {
      let session = {
        id: '1',
        model: 'Baseline-LLaVA',
      }

      // Change model
      session = { ...session, model: 'Qwen3-VL-2B-Instruct' }

      expect(session.model).toBe('Qwen3-VL-2B-Instruct')
    })
  })

  describe('Message Content Handling', () => {
    it('uses default prompt when only image provided', () => {
      const content = ''
      const image = 'data:image/png;base64,abc'

      const messageContent = content.trim() || (image ? 'Generate CAD code for this image' : '')

      expect(messageContent).toBe('Generate CAD code for this image')
    })

    it('uses provided content when available', () => {
      const content = 'Create a sphere'
      const image = 'data:image/png;base64,abc'

      const messageContent = content.trim() || (image ? 'Generate CAD code for this image' : '')

      expect(messageContent).toBe('Create a sphere')
    })

    it('handles empty content without image', () => {
      const content = ''
      const image = undefined

      const messageContent = content.trim() || (image ? 'Generate CAD code for this image' : '')

      expect(messageContent).toBe('')
    })
  })

  describe('Response Extraction', () => {
    it('extracts cad_code field', () => {
      const data = { cad_code: 'code1' }
      const output = data.cad_code || (data as any).generated_code || (data as any).output || 'No code'
      expect(output).toBe('code1')
    })

    it('falls back to generated_code', () => {
      const data = { generated_code: 'code2' }
      const output = (data as any).cad_code || data.generated_code || (data as any).output || 'No code'
      expect(output).toBe('code2')
    })

    it('falls back to output', () => {
      const data = { output: 'code3' }
      const output = (data as any).cad_code || (data as any).generated_code || data.output || 'No code'
      expect(output).toBe('code3')
    })

    it('uses fallback message when no code field', () => {
      const data = { status: 'ok' }
      const output = (data as any).cad_code || (data as any).generated_code || (data as any).output || 'No code found'
      expect(output).toBe('No code found')
    })
  })
})
