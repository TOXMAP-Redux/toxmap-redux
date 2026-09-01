/**
 * Unit tests for formatLbs utility.
 *
 * Layer 1 — pure function tests, no I/O.
 * Covers UX Invariant 8: comma-formatted release quantities.
 */
import { describe, expect, it } from 'vitest'
import { formatLbs, formatNumber } from './formatLbs'

describe('formatLbs', () => {
  describe('comma formatting (UX Invariant 8)', () => {
    it('formats four-digit numbers with comma', () => {
      expect(formatLbs(8205)).toBe('8,205 lbs')
    })

    it('formats five-digit numbers with comma', () => {
      expect(formatLbs(12485)).toBe('12,485 lbs')
    })

    it('formats six-digit numbers with commas', () => {
      expect(formatLbs(100000)).toBe('100,000 lbs')
    })

    it('formats seven-digit numbers with commas', () => {
      expect(formatLbs(1234567)).toBe('1,234,567 lbs')
    })

    it('formats numbers under 1000 without comma', () => {
      expect(formatLbs(999)).toBe('999 lbs')
    })

    it('formats zero correctly', () => {
      expect(formatLbs(0)).toBe('0 lbs')
    })
  })

  describe('null/undefined handling', () => {
    it('returns dash for null', () => {
      expect(formatLbs(null)).toBe('—')
    })

    it('returns dash for undefined', () => {
      expect(formatLbs(undefined)).toBe('—')
    })
  })

  describe('rounding (7.UX.7)', () => {
    it('rounds decimals to nearest whole number', () => {
      expect(formatLbs(8205.5)).toBe('8,206 lbs')
    })

    it('rounds down when fraction < 0.5', () => {
      expect(formatLbs(8205.4)).toBe('8,205 lbs')
    })

    it('rounds small decimals to zero', () => {
      expect(formatLbs(0.001)).toBe('0 lbs')
    })

    it('rounds 0.5 up to 1', () => {
      expect(formatLbs(0.5)).toBe('1 lbs')
    })

    it('rounds large numbers with decimals', () => {
      // Brandon Shores test case: 5,609,480.2 → 5,609,480
      expect(formatLbs(5609480.2)).toBe('5,609,480 lbs')
    })
  })

  describe('seed data regression', () => {
    // T-01: Bethlehem Steel copper release
    it('T-01 copper release: 8,205 lbs', () => {
      expect(formatLbs(8205)).toBe('8,205 lbs')
    })

    // T-01 total: 12,485 lbs
    it('T-01 total release: 12,485 lbs', () => {
      expect(formatLbs(12485)).toBe('12,485 lbs')
    })
  })
})

describe('formatNumber', () => {
  describe('comma formatting', () => {
    it('formats four-digit numbers with comma', () => {
      expect(formatNumber(8205)).toBe('8,205')
    })

    it('formats five-digit numbers with comma', () => {
      expect(formatNumber(12485)).toBe('12,485')
    })

    it('formats six-digit numbers with commas', () => {
      expect(formatNumber(100000)).toBe('100,000')
    })

    it('formats numbers under 1000 without comma', () => {
      expect(formatNumber(999)).toBe('999')
    })

    it('formats zero correctly', () => {
      expect(formatNumber(0)).toBe('0')
    })
  })

  describe('null/undefined handling', () => {
    it('returns dash for null', () => {
      expect(formatNumber(null)).toBe('—')
    })

    it('returns dash for undefined', () => {
      expect(formatNumber(undefined)).toBe('—')
    })
  })

  describe('rounding (7.UX.7)', () => {
    it('rounds decimals to nearest whole number', () => {
      expect(formatNumber(8205.5)).toBe('8,206')
    })

    it('rounds down when fraction < 0.5', () => {
      expect(formatNumber(8205.4)).toBe('8,205')
    })

    it('rounds large numbers with decimals', () => {
      // Discrepancy test case: 5,703.74 → 5,704
      expect(formatNumber(5703.74)).toBe('5,704')
    })
  })
})
