/**
 * Component tests for ChemicalFamilyBanner.
 *
 * Layer 2 — React component tests with mocked service layer.
 * Tests ADR-007 chemical family expansion disclosure.
 */
import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ChemicalFamilyBanner } from '../ChemicalFamilyBanner'
import type { SearchExpansion } from '../../api/types'

const mockExpansion: SearchExpansion = {
  expanded: true,
  family_name: 'LEAD COMPOUNDS',
  searched_chemicals: ['LEAD', 'LEAD COMPOUNDS', 'LEAD AND LEAD COMPOUNDS'],
  description: 'Includes elemental lead and all lead compound reporting categories',
  nlm_url: 'https://www.atsdr.cdc.gov/toxfaqs/index.asp',
  epa_note:
    'Facilities may report this element and its compounds separately or combined. Results include all related reporting categories.',
}

describe('ChemicalFamilyBanner', () => {
  describe('conditional rendering', () => {
    it('renders nothing when expansion.expanded is false', () => {
      const { container } = render(
        <ChemicalFamilyBanner expansion={{ ...mockExpansion, expanded: false }} />
      )

      expect(container.firstChild).toBeNull()
    })

    it('renders banner when expansion.expanded is true', () => {
      render(<ChemicalFamilyBanner expansion={mockExpansion} />)

      expect(screen.getByTestId('chemical-family-banner')).toBeInTheDocument()
    })
  })

  describe('content display', () => {
    it('shows family name in header', () => {
      render(<ChemicalFamilyBanner expansion={mockExpansion} />)

      expect(screen.getByText(/LEAD COMPOUNDS family/)).toBeInTheDocument()
    })

    it('lists all searched chemicals', () => {
      render(<ChemicalFamilyBanner expansion={mockExpansion} />)

      // Each chemical should be in quotes
      expect(screen.getByText(/"LEAD"/)).toBeInTheDocument()
    })

    it('shows description when provided', () => {
      render(<ChemicalFamilyBanner expansion={mockExpansion} />)

      expect(
        screen.getByText(/Includes elemental lead and all lead compound/)
      ).toBeInTheDocument()
    })

    it('shows NLM link when url provided', () => {
      render(<ChemicalFamilyBanner expansion={mockExpansion} />)

      const link = screen.getByText(/Learn more \(NLM\)/)
      expect(link).toHaveAttribute('href', mockExpansion.nlm_url)
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    })
  })

  describe('exact search callback', () => {
    it('calls onSearchExact when button clicked', () => {
      const onSearchExact = vi.fn()
      render(<ChemicalFamilyBanner expansion={mockExpansion} onSearchExact={onSearchExact} />)

      const button = screen.getByText(/Search exact term only/)
      fireEvent.click(button)

      expect(onSearchExact).toHaveBeenCalledTimes(1)
    })

    it('does not show exact search button when callback not provided', () => {
      render(<ChemicalFamilyBanner expansion={mockExpansion} />)

      expect(screen.queryByText(/Search exact term only/)).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has data-testid for Playwright selection', () => {
      render(<ChemicalFamilyBanner expansion={mockExpansion} />)

      expect(screen.getByTestId('chemical-family-banner')).toBeInTheDocument()
    })

    it('external links have proper security attributes', () => {
      render(<ChemicalFamilyBanner expansion={mockExpansion} />)

      const externalLink = screen.getByText(/Learn more \(NLM\)/)
      expect(externalLink).toHaveAttribute('rel', 'noopener noreferrer')
    })
  })
})
