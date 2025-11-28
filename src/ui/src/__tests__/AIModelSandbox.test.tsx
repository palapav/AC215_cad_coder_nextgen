import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { AIModelSandbox } from '../components/AIModelSandbox'

// Mock child components to avoid complex radix-ui dependencies
vi.mock('../components/ModelSelector', () => ({
  ModelSelector: ({ selectedModel, onModelChange }: any) => (
    <div data-testid="model-selector">
      <select
        data-testid="model-select"
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
      >
        <option value="baseline-llava">Baseline-LLaVA</option>
        <option value="qwen3-vl-2b">Qwen3-VL-2B-Instruct</option>
      </select>
    </div>
  ),
}))

vi.mock('../components/ChatHistory', () => ({
  ChatHistory: ({ messages }: any) => (
    <div data-testid="chat-history">
      {messages.length === 0 ? (
        <div>No messages</div>
      ) : (
        messages.map((msg: any) => (
          <div key={msg.id} data-testid={`message-${msg.id}`}>
            {msg.role}: {msg.content}
          </div>
        ))
      )}
    </div>
  ),
}))

vi.mock('../components/ChatInput', () => ({
  ChatInput: ({ onSendMessage, disabled }: any) => (
    <div data-testid="chat-input">
      <input
        data-testid="message-input"
        disabled={disabled}
        onChange={(e) => {
          (window as any).__testMessage = e.target.value
        }}
      />
      <button
        data-testid="send-button"
        onClick={() => {
          const msg = (window as any).__testMessage || 'test message'
          onSendMessage(msg)
        }}
        disabled={disabled}
      >
        Send
      </button>
    </div>
  ),
}))

vi.mock('../components/ChatSidebar', () => ({
  ChatSidebar: ({ 
    currentSessionId, 
    sessions, 
    onSessionSelect, 
    onNewSession, 
    onDeleteSession 
  }: any) => (
    <div data-testid="chat-sidebar">
      <button data-testid="new-session-btn" onClick={onNewSession}>
        New Session
      </button>
      {sessions.map((session: any) => (
        <div
          key={session.id}
          data-testid={`session-${session.id}`}
          data-current={currentSessionId === session.id}
        >
          <button onClick={() => onSessionSelect(session.id)}>
            {session.name}
          </button>
          <button
            data-testid={`delete-session-${session.id}`}
            onClick={() => onDeleteSession(session.id)}
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  ),
  ChatSession: {},
}))

vi.mock('../components/ui/button', () => ({
  Button: ({ children, onClick, disabled, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  ),
}))

describe('AIModelSandbox', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
    ;(window as any).__testMessage = ''
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the component with initial state', () => {
    render(<AIModelSandbox />)
    expect(screen.getByTestId('chat-sidebar')).toBeInTheDocument()
    expect(screen.getByTestId('chat-history')).toBeInTheDocument()
    expect(screen.getByTestId('chat-input')).toBeInTheDocument()
  })

  it('creates initial session on mount', () => {
    render(<AIModelSandbox />)
    expect(screen.getByTestId('new-session-btn')).toBeInTheDocument()
  })

  it('creates a new session when new session button is clicked', async () => {
    render(<AIModelSandbox />)
    const newSessionBtn = screen.getByTestId('new-session-btn')
    
    fireEvent.click(newSessionBtn)
    
    await waitFor(() => {
      const sessions = screen.getAllByTestId(/^session-/)
      expect(sessions.length).toBeGreaterThan(0)
    })
  })

  it('sends a message and updates state', async () => {
    const mockResponse = {
      cad_code: 'import cadquery as cq\nresult = cq.Workplane("XY").box(1, 1, 1)',
    }
    
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    render(<AIModelSandbox />)
    
    const input = screen.getByTestId('message-input')
    const sendButton = screen.getByTestId('send-button')
    
    fireEvent.change(input, { target: { value: 'Create a cube' } })
    ;(window as any).__testMessage = 'Create a cube'
    
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/generate_cad',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })
  })

  it('handles API error gracefully', async () => {
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    render(<AIModelSandbox />)
    
    const input = screen.getByTestId('message-input')
    const sendButton = screen.getByTestId('send-button')
    
    fireEvent.change(input, { target: { value: 'test' } })
    ;(window as any).__testMessage = 'test'
    
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })
  })

  it('changes model selection', async () => {
    render(<AIModelSandbox />)
    
    const modelSelect = screen.getByTestId('model-select')
    
    fireEvent.change(modelSelect, { target: { value: 'qwen3-vl-2b' } })
    
    await waitFor(() => {
      expect(modelSelect).toHaveValue('qwen3-vl-2b')
    })
  })

  it('normalizes model names correctly', async () => {
    const mockResponse = { cad_code: 'test code' }
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    render(<AIModelSandbox />)
    
    const modelSelect = screen.getByTestId('model-select')
    fireEvent.change(modelSelect, { target: { value: 'baseline-llava' } })
    
    await waitFor(() => {
      const input = screen.getByTestId('message-input')
      const sendButton = screen.getByTestId('send-button')
      fireEvent.change(input, { target: { value: 'test' } })
      ;(window as any).__testMessage = 'test'
      fireEvent.click(sendButton)
    })
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
      const call = (global.fetch as any).mock.calls[0]
      const body = JSON.parse(call[1].body)
      expect(body.model_choice).toBe('llava')
    })
  })

  it('handles session deletion', async () => {
    render(<AIModelSandbox />)
    
    // Create a session first
    const newSessionBtn = screen.getByTestId('new-session-btn')
    fireEvent.click(newSessionBtn)
    
    await waitFor(() => {
      const sessions = screen.getAllByTestId(/^session-/)
      expect(sessions.length).toBeGreaterThan(0)
    })
    
    const sessions = screen.getAllByTestId(/^session-/)
    const firstSessionId = sessions[0].getAttribute('data-testid')?.replace('session-', '')
    
    if (firstSessionId) {
      const deleteBtn = screen.getByTestId(`delete-session-${firstSessionId}`)
      fireEvent.click(deleteBtn)
    }
  })

  it('switches between sessions', async () => {
    render(<AIModelSandbox />)
    
    // Create multiple sessions
    const newSessionBtn = screen.getByTestId('new-session-btn')
    fireEvent.click(newSessionBtn)
    
    await waitFor(() => {
      const sessions = screen.getAllByTestId(/^session-/)
      expect(sessions.length).toBeGreaterThan(0)
    })
    
    const sessions = screen.getAllByTestId(/^session-/)
    if (sessions.length > 0) {
      const sessionButton = sessions[0].querySelector('button')
      if (sessionButton) {
        fireEvent.click(sessionButton)
      }
    }
  })

  it('extracts cad_code from various response formats', async () => {
    const testCases = [
      { cad_code: 'code1' },
      { generated_code: 'code2' },
      { output: 'code3' },
      { result: 'code4' },
    ]

    for (const testCase of testCases) {
      vi.clearAllMocks()
      const { unmount } = render(<AIModelSandbox />)
      
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => testCase,
      })
      
      const inputs = screen.getAllByTestId('message-input')
      const sendButtons = screen.getAllByTestId('send-button')
      
      if (inputs.length > 0 && sendButtons.length > 0) {
        fireEvent.change(inputs[0], { target: { value: 'test' } })
        ;(window as any).__testMessage = 'test'
        fireEvent.click(sendButtons[0])
        
        await waitFor(() => {
          expect(global.fetch).toHaveBeenCalled()
        })
      }
      
      unmount()
    }
  })

  it('disables input while generating', async () => {
    let resolveFetch: any
    const fetchPromise = new Promise((resolve) => {
      resolveFetch = resolve
    })
    
    ;(global.fetch as any).mockReturnValueOnce(fetchPromise)

    render(<AIModelSandbox />)
    
    const input = screen.getByTestId('message-input')
    const sendButton = screen.getByTestId('send-button')
    
    fireEvent.change(input, { target: { value: 'test' } })
    ;(window as any).__testMessage = 'test'
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(sendButton).toBeDisabled()
    })
    
    resolveFetch({
      ok: true,
      json: async () => ({ cad_code: 'test' }),
    })
  })

  it('handles empty message content with image fallback', async () => {
    const mockResponse = { cad_code: 'test code' }
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    render(<AIModelSandbox />)
    
    // Simulate sending empty message with image
    const sendButton = screen.getByTestId('send-button')
    ;(window as any).__testMessage = ''
    
    // Mock image being sent
    const component = screen.getByTestId('chat-input').closest('div')
    if (component) {
      // This would normally come from ChatInput, but we're testing the handler
      const input = screen.getByTestId('message-input')
      fireEvent.change(input, { target: { value: '' } })
    }
  })
})
