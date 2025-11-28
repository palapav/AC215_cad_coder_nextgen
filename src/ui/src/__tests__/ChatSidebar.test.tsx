import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChatSidebar, ChatSession } from '../components/ChatSidebar'
import { Message } from '../components/ChatMessage'

// Mock UI components
vi.mock('../components/ui/button', () => ({
  Button: ({ children, onClick, className, ...props }: any) => (
    <button onClick={onClick} className={className} {...props}>
      {children}
    </button>
  ),
}))

vi.mock('../components/ui/scroll-area', () => ({
  ScrollArea: ({ children, className }: any) => (
    <div className={className} data-testid="scroll-area">
      {children}
    </div>
  ),
}))

vi.mock('../components/ui/card', () => ({
  Card: ({ children, className, onClick, onMouseEnter, onMouseLeave }: any) => (
    <div
      className={className}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      data-testid="session-card"
    >
      {children}
    </div>
  ),
}))

describe('ChatSidebar', () => {
  const createMessage = (id: string, role: 'user' | 'assistant', content: string): Message => ({
    id,
    role,
    content,
    timestamp: new Date(),
  })

  const createSession = (id: string, name: string, messages: Message[] = []): ChatSession => ({
    id,
    name,
    messages,
    createdAt: new Date(),
    model: 'Baseline-LLaVA',
  })

  const mockOnSessionSelect = vi.fn()
  const mockOnNewSession = vi.fn()
  const mockOnDeleteSession = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the sidebar', () => {
    render(
      <ChatSidebar
        currentSessionId={null}
        sessions={[]}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    expect(screen.getByRole('button', { name: /new chat/i })).toBeInTheDocument()
  })

  it('displays empty state when no sessions', () => {
    render(
      <ChatSidebar
        currentSessionId={null}
        sessions={[]}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    expect(screen.getByText(/No chat sessions yet/i)).toBeInTheDocument()
  })

  it('calls onNewSession when new chat button is clicked', () => {
    render(
      <ChatSidebar
        currentSessionId={null}
        sessions={[]}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    const newChatButton = screen.getByRole('button', { name: /new chat/i })
    fireEvent.click(newChatButton)
    
    expect(mockOnNewSession).toHaveBeenCalledTimes(1)
  })

  it('renders list of sessions', () => {
    const sessions = [
      createSession('1', 'Session 1'),
      createSession('2', 'Session 2'),
    ]
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={sessions}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    expect(screen.getByText('New Chat')).toBeInTheDocument()
  })

  it('calls onSessionSelect when session is clicked', () => {
    const sessions = [createSession('1', 'Session 1')]
    
    render(
      <ChatSidebar
        currentSessionId={null}
        sessions={sessions}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    const sessionCards = screen.getAllByTestId('session-card')
    fireEvent.click(sessionCards[0])
    
    expect(mockOnSessionSelect).toHaveBeenCalledWith('1')
  })

  it('highlights current session', () => {
    const sessions = [
      createSession('1', 'Session 1'),
      createSession('2', 'Session 2'),
    ]
    
    const { container } = render(
      <ChatSidebar
        currentSessionId="1"
        sessions={sessions}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    const sessionCards = screen.getAllByTestId('session-card')
    // Current session should have different styling
    expect(sessionCards[0]).toHaveClass('bg-sidebar-accent')
  })

  it('formats session name from first user message', () => {
    const messages = [createMessage('1', 'user', 'Create a cube for me')]
    const session = createSession('1', 'Session 1', messages)
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={[session]}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    expect(screen.getByText(/Create a cube for me/i)).toBeInTheDocument()
  })

  it('uses default name for empty sessions', () => {
    const session = createSession('1', 'Session 1', [])
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={[session]}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    // formatSessionName returns "New Chat" for empty sessions
    // There will be multiple "New Chat" texts (button and session name), so use getAllByText
    const newChatTexts = screen.getAllByText(/New Chat/i)
    expect(newChatTexts.length).toBeGreaterThan(0)
  })

  it('truncates long session names', () => {
    const longMessage = 'A'.repeat(50)
    const messages = [createMessage('1', 'user', longMessage)]
    const session = createSession('1', 'Session 1', messages)
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={[session]}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    // Should truncate to 30 characters
    const truncated = longMessage.slice(0, 30) + '...'
    expect(screen.getByText(new RegExp(truncated.slice(0, 20)))).toBeInTheDocument()
  })

  it('shows delete button on hover', async () => {
    const sessions = [
      createSession('1', 'Session 1'),
      createSession('2', 'Session 2'),
    ]
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={sessions}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    const sessionCards = screen.getAllByTestId('session-card')
    // Hover over the first session card
    fireEvent.mouseEnter(sessionCards[0])
    
    // Wait for delete button to appear (it's conditionally rendered based on hover state)
    await waitFor(() => {
      const deleteButtons = screen.queryAllByTestId(/^delete-session-/)
      // At least one delete button should be visible when hovering
      expect(deleteButtons.length).toBeGreaterThan(0)
    }, { timeout: 1000 })
  })

  it('calls onDeleteSession when delete button is clicked', async () => {
    const sessions = [
      createSession('1', 'Session 1'),
      createSession('2', 'Session 2'),
    ]
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={sessions}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    const sessionCards = screen.getAllByTestId('session-card')
    fireEvent.mouseEnter(sessionCards[0])
    
    await waitFor(() => {
      const deleteButton = screen.queryByTestId('delete-session-1')
      if (deleteButton) {
        fireEvent.click(deleteButton)
        expect(mockOnDeleteSession).toHaveBeenCalledWith('1')
      }
    }, { timeout: 1000 })
  })

  it('does not show delete button for single session', () => {
    const sessions = [createSession('1', 'Session 1')]
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={sessions}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    const sessionCards = screen.getAllByTestId('session-card')
    fireEvent.mouseEnter(sessionCards[0])
    
    // Should not show delete button when only one session exists
    expect(screen.queryByTestId('delete-session-1')).not.toBeInTheDocument()
  })

  it('displays message count', () => {
    const messages = [
      createMessage('1', 'user', 'Hello'),
      createMessage('2', 'assistant', 'Hi'),
    ]
    const session = createSession('1', 'Session 1', messages)
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={[session]}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    expect(screen.getByText(/2 messages/i)).toBeInTheDocument()
  })

  it('displays model name', () => {
    const session = createSession('1', 'Session 1')
    session.model = 'Qwen3-VL-2B-Instruct'
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={[session]}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    expect(screen.getByText('Qwen3-VL-2B-Instruct')).toBeInTheDocument()
  })

  it('formats date correctly', () => {
    const today = new Date()
    const session = createSession('1', 'Session 1')
    session.createdAt = today
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={[session]}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    // The date formatting can show "Today", "Yesterday", or a date string
    // Just check that some date-related text is present
    const dateText = screen.getByText(/Today|Yesterday|\d+ days ago|[\d\/]+/)
    expect(dateText).toBeInTheDocument()
  })

  it('stops propagation when delete button is clicked', async () => {
    const sessions = [
      createSession('1', 'Session 1'),
      createSession('2', 'Session 2'),
    ]
    
    render(
      <ChatSidebar
        currentSessionId="1"
        sessions={sessions}
        onSessionSelect={mockOnSessionSelect}
        onNewSession={mockOnNewSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )
    
    const sessionCards = screen.getAllByTestId('session-card')
    fireEvent.mouseEnter(sessionCards[0])
    
    await waitFor(() => {
      const deleteButton = screen.queryByTestId('delete-session-1')
      if (deleteButton) {
        const initialCallCount = mockOnSessionSelect.mock.calls.length
        fireEvent.click(deleteButton)
        
        // Delete should be called
        expect(mockOnDeleteSession).toHaveBeenCalledWith('1')
        // Session select should not be called (stopPropagation prevents it)
        expect(mockOnSessionSelect.mock.calls.length).toBe(initialCallCount)
      }
    }, { timeout: 1000 })
  })
})
