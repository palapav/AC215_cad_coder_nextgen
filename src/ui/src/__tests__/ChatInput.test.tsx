import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChatInput } from '../components/ChatInput'

// Mock ImageWithFallback
vi.mock('../components/figma/ImageWithFallback', () => ({
  ImageWithFallback: ({ src, alt }: any) => (
    <img src={src} alt={alt} data-testid="preview-image" />
  ),
}))

// Mock UI components
vi.mock('../components/ui/button', () => ({
  Button: ({ children, onClick, disabled, type, ...props }: any) => (
    <button
      onClick={onClick}
      disabled={disabled}
      type={type}
      {...props}
    >
      {children}
    </button>
  ),
}))

vi.mock('../components/ui/textarea', () => ({
  Textarea: ({ value, onChange, onKeyDown, placeholder, disabled, className }: any) => (
    <textarea
      value={value}
      onChange={onChange}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      disabled={disabled}
      className={className}
      data-testid="textarea"
    />
  ),
}))

describe('ChatInput', () => {
  const mockOnSendMessage = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the input form', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    expect(screen.getByTestId('textarea')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('allows typing in the textarea', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    const textarea = screen.getByTestId('textarea')
    
    fireEvent.change(textarea, { target: { value: 'Hello, world!' } })
    
    expect(textarea).toHaveValue('Hello, world!')
  })

  it('sends message when form is submitted', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    const textarea = screen.getByTestId('textarea')
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message', undefined)
  })

  it('sends message when Enter is pressed (without Shift)', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    const textarea = screen.getByTestId('textarea')
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message', undefined)
  })

  it('does not send message when Shift+Enter is pressed', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    const textarea = screen.getByTestId('textarea')
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    
    expect(mockOnSendMessage).not.toHaveBeenCalled()
  })

  it('clears input after sending message', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    const textarea = screen.getByTestId('textarea')
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    expect(textarea).toHaveValue('')
  })

  it('handles image selection', async () => {
    const file = new File(['test'], 'test.png', { type: 'image/png' })
    const reader = {
      readAsDataURL: vi.fn(),
      onload: null as any,
      result: 'data:image/png;base64,test',
    }
    
    vi.spyOn(global, 'FileReader').mockImplementation(() => reader as any)

    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    
    const fileInput = screen.getByRole('textbox').closest('form')?.querySelector('input[type="file"]') as HTMLInputElement
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })
    
    fireEvent.change(fileInput)
    
    // Simulate FileReader onload
    reader.onload({ target: { result: 'data:image/png;base64,test' } })
    
    await waitFor(() => {
      expect(reader.readAsDataURL).toHaveBeenCalledWith(file)
    })
  })

  it('displays selected image preview', async () => {
    const file = new File(['test'], 'test.png', { type: 'image/png' })
    const reader = {
      readAsDataURL: vi.fn(),
      onload: null as any,
      result: 'data:image/png;base64,test',
    }
    
    vi.spyOn(global, 'FileReader').mockImplementation(() => reader as any)

    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    
    const fileInput = screen.getByRole('textbox').closest('form')?.querySelector('input[type="file"]') as HTMLInputElement
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })
    
    fireEvent.change(fileInput)
    reader.onload({ target: { result: 'data:image/png;base64,test' } })
    
    await waitFor(() => {
      expect(screen.getByTestId('preview-image')).toBeInTheDocument()
    })
  })

  it('removes selected image', async () => {
    const file = new File(['test'], 'test.png', { type: 'image/png' })
    const reader = {
      readAsDataURL: vi.fn(),
      onload: null as any,
      result: 'data:image/png;base64,test',
    }
    
    vi.spyOn(global, 'FileReader').mockImplementation(() => reader as any)

    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    
    const fileInput = screen.getByRole('textbox').closest('form')?.querySelector('input[type="file"]') as HTMLInputElement
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })
    
    fireEvent.change(fileInput)
    reader.onload({ target: { result: 'data:image/png;base64,test' } })
    
    await waitFor(() => {
      expect(screen.getByTestId('preview-image')).toBeInTheDocument()
    })
    
    const removeButton = screen.getByRole('button', { name: /remove/i })
    fireEvent.click(removeButton)
    
    await waitFor(() => {
      expect(screen.queryByTestId('preview-image')).not.toBeInTheDocument()
    })
  })

  it('sends message with image when image is selected', async () => {
    const file = new File(['test'], 'test.png', { type: 'image/png' })
    const reader = {
      readAsDataURL: vi.fn(),
      onload: null as any,
      result: 'data:image/png;base64,test',
    }
    
    vi.spyOn(global, 'FileReader').mockImplementation(() => reader as any)

    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    
    const fileInput = screen.getByRole('textbox').closest('form')?.querySelector('input[type="file"]') as HTMLInputElement
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })
    
    fireEvent.change(fileInput)
    reader.onload({ target: { result: 'data:image/png;base64,test' } })
    
    await waitFor(() => {
      expect(screen.getByTestId('preview-image')).toBeInTheDocument()
    })
    
    const sendButton = screen.getByRole('button', { name: /send/i })
    fireEvent.click(sendButton)
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('', 'data:image/png;base64,test')
  })

  it('disables input when disabled prop is true', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} disabled={true} />)
    const textarea = screen.getByTestId('textarea')
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    expect(textarea).toBeDisabled()
    expect(sendButton).toBeDisabled()
  })

  it('does not send empty message without image', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    const textarea = screen.getByTestId('textarea')
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(textarea, { target: { value: '   ' } })
    fireEvent.click(sendButton)
    
    expect(mockOnSendMessage).not.toHaveBeenCalled()
  })

  it('trims whitespace from message before sending', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    const textarea = screen.getByTestId('textarea')
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(textarea, { target: { value: '  Test message  ' } })
    fireEvent.click(sendButton)
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message', undefined)
  })

  it('rejects non-image files', async () => {
    const file = new File(['test'], 'test.txt', { type: 'text/plain' })
    const reader = {
      readAsDataURL: vi.fn(),
      onload: null as any,
    }
    
    vi.spyOn(global, 'FileReader').mockImplementation(() => reader as any)

    render(<ChatInput onSendMessage={mockOnSendMessage} />)
    
    const fileInput = screen.getByRole('textbox').closest('form')?.querySelector('input[type="file"]') as HTMLInputElement
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })
    
    fireEvent.change(fileInput)
    
    // FileReader should not be called for non-image files
    expect(reader.readAsDataURL).not.toHaveBeenCalled()
  })
})
