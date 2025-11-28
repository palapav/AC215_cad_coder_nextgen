import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ModelSelector } from '../components/ModelSelector'

// Mock Select components - Radix UI Select doesn't use native select
let mockOnValueChange: ((value: string) => void) | null = null

vi.mock('../components/ui/select', () => ({
  Select: ({ value, onValueChange, children }: any) => {
    // Store the onValueChange handler so SelectItem can use it
    mockOnValueChange = onValueChange
    return (
      <div data-testid="select" data-value={value}>
        {children}
      </div>
    )
  },
  SelectTrigger: ({ children, className }: any) => (
    <div className={className} data-testid="select-trigger">
      {children}
    </div>
  ),
  SelectValue: ({ placeholder, children }: any) => (
    <div data-testid="select-value">
      {children || placeholder}
    </div>
  ),
  SelectContent: ({ children, className }: any) => (
    <div className={className} data-testid="select-content">
      {children}
    </div>
  ),
  SelectItem: ({ value, children }: any) => {
    const handleClick = () => {
      if (mockOnValueChange) {
        mockOnValueChange(value)
      }
    }
    return (
      <div
        data-testid={`select-item-${value}`}
        onClick={handleClick}
        role="option"
      >
        {children}
      </div>
    )
  },
}))

describe('ModelSelector', () => {
  const mockOnModelChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the model selector', () => {
    render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    expect(screen.getByTestId('select')).toBeInTheDocument()
  })

  it('displays current selected model', () => {
    render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    const select = screen.getByTestId('select')
    expect(select).toHaveAttribute('data-value', 'baseline-llava')
  })

  it('calls onModelChange when model is changed', () => {
    render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    const qwenButton = screen.getByTestId('select-item-qwen3-vl-2b')
    fireEvent.click(qwenButton)
    
    expect(mockOnModelChange).toHaveBeenCalledWith('qwen3-vl-2b')
  })

  it('displays all available models', () => {
    render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    expect(screen.getByTestId('select-item-baseline-llava')).toBeInTheDocument()
    expect(screen.getByTestId('select-item-qwen3-vl-2b')).toBeInTheDocument()
  })

  it('shows model name for baseline-llava', () => {
    render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    const selectValue = screen.getByTestId('select-value')
    expect(selectValue.textContent).toContain('Baseline-LLaVA')
  })

  it('shows model name for qwen3-vl-2b', () => {
    render(
      <ModelSelector
        selectedModel="qwen3-vl-2b"
        onModelChange={mockOnModelChange}
      />
    )
    
    const selectValue = screen.getByTestId('select-value')
    expect(selectValue.textContent).toContain('Qwen3-VL-2B-Instruct')
  })

  it('handles model change to baseline-llava', () => {
    render(
      <ModelSelector
        selectedModel="qwen3-vl-2b"
        onModelChange={mockOnModelChange}
      />
    )
    
    const baselineButton = screen.getByTestId('select-item-baseline-llava')
    fireEvent.click(baselineButton)
    
    expect(mockOnModelChange).toHaveBeenCalledWith('baseline-llava')
  })

  it('handles model change to qwen3-vl-2b', () => {
    render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    const qwenButton = screen.getByTestId('select-item-qwen3-vl-2b')
    fireEvent.click(qwenButton)
    
    expect(mockOnModelChange).toHaveBeenCalledWith('qwen3-vl-2b')
  })

  it('applies correct styling classes', () => {
    const { container } = render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    const selectTrigger = screen.getByTestId('select-trigger')
    expect(selectTrigger).toHaveClass('bg-muted', 'border-border')
  })

  it('renders with correct width', () => {
    const { container } = render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    const wrapper = container.firstChild
    expect(wrapper).toHaveClass('w-64')
  })

  it('handles rapid model changes', () => {
    render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    const qwenButton = screen.getByTestId('select-item-qwen3-vl-2b')
    const baselineButton = screen.getByTestId('select-item-baseline-llava')
    
    fireEvent.click(qwenButton)
    fireEvent.click(baselineButton)
    fireEvent.click(qwenButton)
    
    expect(mockOnModelChange).toHaveBeenCalledTimes(3)
    expect(mockOnModelChange).toHaveBeenLastCalledWith('qwen3-vl-2b')
  })

  it('displays model descriptions in options', () => {
    render(
      <ModelSelector
        selectedModel="baseline-llava"
        onModelChange={mockOnModelChange}
      />
    )
    
    // Check that model options are present
    const baselineOption = screen.getByTestId('select-item-baseline-llava')
    const qwenOption = screen.getByTestId('select-item-qwen3-vl-2b')
    
    expect(baselineOption).toBeInTheDocument()
    expect(qwenOption).toBeInTheDocument()
    expect(baselineOption.textContent).toContain('Baseline-LLaVA')
    expect(qwenOption.textContent).toContain('Qwen3-VL-2B-Instruct')
  })
})
