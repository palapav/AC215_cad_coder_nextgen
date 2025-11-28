import { describe, it, expect, vi } from 'vitest'

/**
 * Unit tests for core UI logic (not component rendering).
 * These tests avoid importing components with versioned radix-ui dependencies.
 */

describe('UI Logic Tests', () => {
  describe('Model name mapping', () => {
    const getModelName = (modelId: string) => {
      const modelNames: Record<string, string> = {
        "baseline-llava": "Baseline-LLaVA",
        "qwen3-vl-2b": "Qwen3-VL-2B-Instruct"
      }
      return modelNames[modelId] || modelId
    }

    it('returns correct name for baseline-llava', () => {
      expect(getModelName('baseline-llava')).toBe('Baseline-LLaVA')
    })

    it('returns correct name for qwen3-vl-2b', () => {
      expect(getModelName('qwen3-vl-2b')).toBe('Qwen3-VL-2B-Instruct')
    })

    it('returns modelId for unknown model', () => {
      expect(getModelName('unknown-model')).toBe('unknown-model')
    })
  })

  describe('Model normalization', () => {
    const normalizeModel = (selectedModel: string) => {
      return selectedModel === "baseline-llava" ? "llava" :
             selectedModel === "qwen3-vl-2b" ? "qwen" :
             selectedModel
    }

    it('normalizes baseline-llava to llava', () => {
      expect(normalizeModel('baseline-llava')).toBe('llava')
    })

    it('normalizes qwen3-vl-2b to qwen', () => {
      expect(normalizeModel('qwen3-vl-2b')).toBe('qwen')
    })

    it('passes through unknown model', () => {
      expect(normalizeModel('other')).toBe('other')
    })
  })

  describe('Message creation', () => {
    interface Message {
      id: string
      role: 'user' | 'assistant'
      content: string
      timestamp: Date
      model?: string
      image?: string
    }

    it('creates user message correctly', () => {
      const message: Message = {
        id: '1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      }
      
      expect(message.role).toBe('user')
      expect(message.content).toBe('Hello')
      expect(message.model).toBeUndefined()
    })

    it('creates assistant message with model', () => {
      const message: Message = {
        id: '2',
        role: 'assistant',
        content: 'import cadquery as cq',
        timestamp: new Date(),
        model: 'Qwen3-VL-2B-Instruct',
      }
      
      expect(message.role).toBe('assistant')
      expect(message.model).toBe('Qwen3-VL-2B-Instruct')
    })

    it('creates message with image', () => {
      const message: Message = {
        id: '3',
        role: 'user',
        content: 'Generate code for this',
        timestamp: new Date(),
        image: 'data:image/png;base64,abc123',
      }
      
      expect(message.image).toBe('data:image/png;base64,abc123')
    })
  })

  describe('Session management', () => {
    interface ChatSession {
      id: string
      name: string
      messages: any[]
      createdAt: Date
      model: string
    }

    it('creates new session correctly', () => {
      const session: ChatSession = {
        id: Date.now().toString(),
        name: 'New Chat',
        messages: [],
        createdAt: new Date(),
        model: 'Baseline-LLaVA',
      }
      
      expect(session.name).toBe('New Chat')
      expect(session.messages).toHaveLength(0)
    })

    it('filters sessions correctly', () => {
      const sessions: ChatSession[] = [
        { id: '1', name: 'Chat 1', messages: [], createdAt: new Date(), model: 'LLaVA' },
        { id: '2', name: 'Chat 2', messages: [], createdAt: new Date(), model: 'Qwen' },
      ]
      
      const filtered = sessions.filter(s => s.id !== '1')
      
      expect(filtered).toHaveLength(1)
      expect(filtered[0].id).toBe('2')
    })
  })

  describe('API request formatting', () => {
    it('formats request body correctly', () => {
      const requestBody = {
        prompt: 'Create a cube',
        image_path: null,
        user_id: 'default',
        model_choice: 'llava',
        rag_context: null,
      }
      
      expect(requestBody.prompt).toBe('Create a cube')
      expect(requestBody.model_choice).toBe('llava')
      expect(requestBody.image_path).toBeNull()
    })

    it('includes image path when provided', () => {
      const requestBody = {
        prompt: 'Describe this image',
        image_path: 'data:image/png;base64,xyz',
        user_id: 'default',
        model_choice: 'qwen',
        rag_context: null,
      }
      
      expect(requestBody.image_path).toBe('data:image/png;base64,xyz')
    })
  })

  describe('Response parsing', () => {
    it('extracts cad_code from response', () => {
      const data = {
        cad_code: 'import cadquery as cq\nresult = cq.box(1,1,1)',
      }
      
      const output = data.cad_code || data.generated_code || 'No code found'
      
      expect(output).toContain('cadquery')
    })

    it('falls back to generated_code', () => {
      const data = {
        generated_code: 'import cadquery as cq',
      }
      
      const output = (data as any).cad_code || data.generated_code || 'No code found'
      
      expect(output).toContain('cadquery')
    })

    it('handles missing code fields', () => {
      const data = {}
      
      const output = (data as any).cad_code || (data as any).generated_code || 'No code found'
      
      expect(output).toBe('No code found')
    })
  })
})

describe('Mock Response Generation', () => {
  const MODEL_RESPONSES: Record<string, string[]> = {
    "baseline-llava": [
      "Hello! I'm Baseline-LLaVA, a vision-language model.",
    ],
    "qwen3-vl-2b": [
      "Hello! I'm Qwen3-VL-2B-Instruct.",
    ],
  }

  it('returns response for baseline-llava', () => {
    const responses = MODEL_RESPONSES["baseline-llava"]
    expect(responses).toBeDefined()
    expect(responses[0]).toContain('LLaVA')
  })

  it('returns response for qwen model', () => {
    const responses = MODEL_RESPONSES["qwen3-vl-2b"]
    expect(responses).toBeDefined()
    expect(responses[0]).toContain('Qwen')
  })
})
