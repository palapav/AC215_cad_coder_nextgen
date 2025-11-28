import { describe, it, expect, vi } from 'vitest'

// Mock the AIModelSandbox component to avoid import issues with versioned radix-ui
vi.mock('../components/AIModelSandbox', () => ({
  AIModelSandbox: () => <div data-testid="sandbox">CAD-Coder Sandbox</div>
}))

describe('App', () => {
  it('renders the main component', async () => {
    const { default: App } = await import('../App')
    const { render, screen } = await import('@testing-library/react')
    
    render(<App />)
    expect(screen.getByTestId('sandbox')).toBeInTheDocument()
  })
})
