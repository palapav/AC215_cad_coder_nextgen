import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChatHistory } from '../components/ChatHistory'
import { Message } from '../components/ChatMessage'

// Mock ChatMessage component
vi.mock('../components/ChatMessage', () => ({
  ChatMessage: ({ message }: any) => (
    <div data-testid={`chat-message-${message.id}`}>
      {message.role}: {message.content}
    </div>
  ),
  Message: {},
}))

// Mock ScrollArea
vi.mock('../components/ui/scroll-area', () => ({
  ScrollArea: ({ children, className }: any) => (
    <div className={className} data-testid="scroll-area">
      {children}
    </div>
  ),
}))

describe('ChatHistory', () => {
  const createMessage = (id: string, role: 'user' | 'assistant', content: string): Message => ({
    id,
    role,
    content,
    timestamp: new Date(),
  })

  beforeEach(() => {
    // Mock scrollIntoView
    Element.prototype.scrollIntoView = vi.fn()
  })

  it('renders empty state when no messages', () => {
    render(<ChatHistory messages={[]} />)
    
    expect(screen.getByText(/Welcome to CAD-Coder AI Model Sandbox/i)).toBeInTheDocument()
    expect(screen.getByText(/Select a model and start chatting/i)).toBeInTheDocument()
  })

  it('renders list of messages', () => {
    const messages = [
      createMessage('1', 'user', 'Hello'),
      createMessage('2', 'assistant', 'Hi there!'),
      createMessage('3', 'user', 'How are you?'),
    ]
    
    render(<ChatHistory messages={messages} />)
    
    expect(screen.getByTestId('chat-message-1')).toBeInTheDocument()
    expect(screen.getByTestId('chat-message-2')).toBeInTheDocument()
    expect(screen.getByTestId('chat-message-3')).toBeInTheDocument()
  })

  it('displays message content correctly', () => {
    const messages = [
      createMessage('1', 'user', 'Create a cube'),
      createMessage('2', 'assistant', 'import cadquery as cq'),
    ]
    
    render(<ChatHistory messages={messages} />)
    
    expect(screen.getByText(/user: Create a cube/i)).toBeInTheDocument()
    expect(screen.getByText(/assistant: import cadquery as cq/i)).toBeInTheDocument()
  })

  it('renders single message', () => {
    const messages = [createMessage('1', 'user', 'Test')]
    
    render(<ChatHistory messages={messages} />)
    
    expect(screen.getByTestId('chat-message-1')).toBeInTheDocument()
    expect(screen.queryByText(/Welcome to CAD-Coder/i)).not.toBeInTheDocument()
  })

  it('renders many messages', () => {
    const messages = Array.from({ length: 20 }, (_, i) =>
      createMessage(
        String(i + 1),
        i % 2 === 0 ? 'user' : 'assistant',
        `Message ${i + 1}`
      )
    )
    
    render(<ChatHistory messages={messages} />)
    
    messages.forEach((msg) => {
      expect(screen.getByTestId(`chat-message-${msg.id}`)).toBeInTheDocument()
    })
  })

  it('scrolls to bottom when messages change', () => {
    const { rerender } = render(<ChatHistory messages={[]} />)
    
    const messages1 = [createMessage('1', 'user', 'First')]
    rerender(<ChatHistory messages={messages1} />)
    
    const messages2 = [
      ...messages1,
      createMessage('2', 'assistant', 'Second'),
    ]
    rerender(<ChatHistory messages={messages2} />)
    
    // scrollIntoView should be called
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
  })

  it('renders messages in correct order', () => {
    const messages = [
      createMessage('1', 'user', 'First'),
      createMessage('2', 'assistant', 'Second'),
      createMessage('3', 'user', 'Third'),
    ]
    
    const { container } = render(<ChatHistory messages={messages} />)
    
    const messageElements = container.querySelectorAll('[data-testid^="chat-message-"]')
    expect(messageElements[0]).toHaveAttribute('data-testid', 'chat-message-1')
    expect(messageElements[1]).toHaveAttribute('data-testid', 'chat-message-2')
    expect(messageElements[2]).toHaveAttribute('data-testid', 'chat-message-3')
  })

  it('handles messages with images', () => {
    const messages: Message[] = [
      {
        id: '1',
        role: 'user',
        content: 'Check this',
        timestamp: new Date(),
        image: 'data:image/png;base64,test',
      },
    ]
    
    render(<ChatHistory messages={messages} />)
    
    expect(screen.getByTestId('chat-message-1')).toBeInTheDocument()
  })

  it('handles messages with model information', () => {
    const messages: Message[] = [
      {
        id: '1',
        role: 'assistant',
        content: 'Response',
        timestamp: new Date(),
        model: 'Baseline-LLaVA',
      },
    ]
    
    render(<ChatHistory messages={messages} />)
    
    expect(screen.getByTestId('chat-message-1')).toBeInTheDocument()
  })
})
