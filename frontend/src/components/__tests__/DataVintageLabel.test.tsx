/**
 * Component tests for DataVintageLabel.
 *
 * Layer 2 — React component tests with mocked service layer.
 * Tests the component's rendering behavior in isolation.
 */
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DataVintageLabel } from '../DataVintageLabel'

describe('DataVintageLabel', () => {
  describe('rendering', () => {
    it('renders the vintage label when provided', () => {
      render(<DataVintageLabel vintageLabel="EPA TRI 2022" />)

      expect(screen.getByTestId('data-vintage-label')).toHaveTextContent('EPA TRI 2022')
    })

    it('renders loading state when vintageLabel is null', () => {
      render(<DataVintageLabel vintageLabel={null} />)

      expect(screen.getByTestId('data-vintage-label')).toHaveTextContent('TRI: loading…')
    })

    it('has required data-testid attribute (TEST_ID_REGISTRY)', () => {
      render(<DataVintageLabel vintageLabel="Test" />)

      expect(screen.getByTestId('data-vintage-label')).toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('is positioned at bottom-right of viewport', () => {
      render(<DataVintageLabel vintageLabel="Test" />)

      const element = screen.getByTestId('data-vintage-label')
      const style = element.style

      expect(style.position).toBe('absolute')
      expect(style.bottom).toBe('42px')
      expect(style.right).toBe('8px')
    })

    it('has pointer-events disabled (non-interactive overlay)', () => {
      render(<DataVintageLabel vintageLabel="Test" />)

      const element = screen.getByTestId('data-vintage-label')
      expect(element.style.pointerEvents).toBe('none')
    })
  })

  describe('UX Invariant 7 (latest year label)', () => {
    it('displays seed data vintage correctly', () => {
      // Seed data format from TOXMAP_TEST_SEED_DATA.md
      render(<DataVintageLabel vintageLabel="Seed data · 2008–2009" />)

      expect(screen.getByTestId('data-vintage-label')).toHaveTextContent(
        'Seed data · 2008–2009'
      )
    })

    it('displays production vintage format correctly', () => {
      // Production format with EPA freeze date
      render(<DataVintageLabel vintageLabel="EPA TRI 2023 Release (May 2024)" />)

      expect(screen.getByTestId('data-vintage-label')).toHaveTextContent(
        'EPA TRI 2023 Release (May 2024)'
      )
    })
  })
})
