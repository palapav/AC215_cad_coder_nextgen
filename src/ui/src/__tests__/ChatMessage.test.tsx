import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChatMessage, Message } from '../components/ChatMessage'

// Mock ImageWithFallback
vi.mock('../components/figma/ImageWithFallback', () => ({
  ImageWithFallback: ({ src, alt, className }: any) => (
    <img src={src} alt={alt} className={className} data-testid="message-image" />
  ),
}))

// Mock UI components
vi.mock('../components/ui/avatar', () => ({
  Avatar: ({ children, className }: any) => (
    <div className={className} data-testid="avatar">
      {children}
    </div>
  ),
  AvatarFallback: ({ children, className }: any) => (
    <div className={className}>{children}</div>
  ),
}))

vi.mock('../components/ui/card', () => ({
  Card: ({ children, className }: any) => (
    <div className={className} data-testid="message-card">
      {children}
    </div>
  ),
}))

describe('ChatMessage', () => {
  const createMessage = (overrides: Partial<Message> = {}): Message => ({
    id: '1',
    role: 'user',
    content: 'Test message',
    timestamp: new Date(),
    ...overrides,
  })

  it('renders user message correctly', () => {
    const message = createMessage({ role: 'user', content: 'Hello, world!' })
    render(<ChatMessage message={message} />)
    
    expect(screen.getByText('Hello, world!')).toBeInTheDocument()
    expect(screen.getByTestId('message-card')).toBeInTheDocument()
  })

  it('renders assistant message correctly', () => {
    const message = createMessage({
      role: 'assistant',
      content: 'This is a response',
    })
    render(<ChatMessage message={message} />)
    
    expect(screen.getByText('This is a response')).toBeInTheDocument()
    expect(screen.getByTestId('avatar')).toBeInTheDocument()
  })

  it('displays image when message has image', () => {
    const message = createMessage({
      role: 'user',
      content: 'Check this out',
      image: 'data:image/png;base64,test123',
    })
    render(<ChatMessage message={message} />)
    
    expect(screen.getByTestId('message-image')).toBeInTheDocument()
    expect(screen.getByTestId('message-image')).toHaveAttribute(
      'src',
      'data:image/png;base64,test123'
    )
  })

  it('displays model name for assistant messages', () => {
    const message = createMessage({
      role: 'assistant',
      content: 'Response',
      model: 'Baseline-LLaVA',
    })
    render(<ChatMessage message={message} />)
    
    expect(screen.getByText('Baseline-LLaVA')).toBeInTheDocument()
  })

  it('does not display model name for user messages', () => {
    const message = createMessage({
      role: 'user',
      content: 'User message',
      model: 'Baseline-LLaVA',
    })
    render(<ChatMessage message={message} />)
    
    expect(screen.queryByText('Baseline-LLaVA')).not.toBeInTheDocument()
  })

  it('handles multiline content correctly', () => {
    const multilineContent = 'Line 1\nLine 2\nLine 3'
    const message = createMessage({
      role: 'user',
      content: multilineContent,
    })
    const { container } = render(<ChatMessage message={message} />)
    
    // Check that the content is rendered (may be split across lines)
    const contentElement = container.querySelector('.whitespace-pre-wrap')
    expect(contentElement).toBeInTheDocument()
    expect(contentElement?.textContent).toBe(multilineContent)
  })

  it('renders message with both image and text', () => {
    const message = createMessage({
      role: 'user',
      content: 'Look at this image',
      image: 'data:image/png;base64,test',
    })
    render(<ChatMessage message={message} />)
    
    expect(screen.getByTestId('message-image')).toBeInTheDocument()
    expect(screen.getByText('Look at this image')).toBeInTheDocument()
  })

  it('applies correct styling for user messages', () => {
    const message = createMessage({ role: 'user' })
    const { container } = render(<ChatMessage message={message} />)
    
    const messageContainer = container.firstChild
    expect(messageContainer).toHaveClass('justify-end')
  })

  it('applies correct styling for assistant messages', () => {
    const message = createMessage({ role: 'assistant' })
    const { container } = render(<ChatMessage message={message} />)
    
    const messageContainer = container.firstChild
    expect(messageContainer).toHaveClass('justify-start')
  })

  it('renders empty content gracefully', () => {
    const message = createMessage({ content: '' })
    render(<ChatMessage message={message} />)
    
    const card = screen.getByTestId('message-card')
    expect(card).toBeInTheDocument()
  })

  it('handles long content correctly', () => {
    const longContent = 'A'.repeat(1000)
    const message = createMessage({ content: longContent })
    render(<ChatMessage message={message} />)
    
    expect(screen.getByText(longContent)).toBeInTheDocument()
  })
})
