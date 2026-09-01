/**
 * Unit tests for Demographics color utilities.
 *
 * Layer 1 — pure function tests, no I/O.
 */
import { describe, expect, it } from 'vitest'
import {
  DEMOGRAPHIC_COLORS,
  getColorScale,
  getLayerLabel,
  getLegendRanges,
} from './colorUtils'
import type { DemographicLayer } from '../../api/types'

describe('DEMOGRAPHIC_COLORS', () => {
  it('has exactly 8 colors (8-bin scheme)', () => {
    expect(DEMOGRAPHIC_COLORS).toHaveLength(8)
  })

  it('all colors are valid hex codes', () => {
    const hexPattern = /^#[0-9a-f]{6}$/i
    DEMOGRAPHIC_COLORS.forEach((color) => {
      expect(color).toMatch(hexPattern)
    })
  })

  it('starts with light color and ends with dark color', () => {
    // Light colors have higher RGB values, dark colors have lower
    // #f7fcf0 (light) vs #08589e (dark)
    expect(DEMOGRAPHIC_COLORS[0]).toBe('#f7fcf0')
    expect(DEMOGRAPHIC_COLORS[7]).toBe('#08589e')
  })
})

describe('getColorScale', () => {
  const layers: DemographicLayer[] = [
    'pct_under_18',
    'pct_over_65',
    'pct_nonwhite',
    'median_income',
    'cancer_mortality_male_per_100k',
    'cancer_mortality_female_per_100k',
    'heart_disease_mortality_per_100k',
    'total_pop',
  ]

  it('returns the unified color scale for all layers', () => {
    layers.forEach((layer) => {
      expect(getColorScale(layer)).toBe(DEMOGRAPHIC_COLORS)
    })
  })

  it('returns 8 colors for all layers', () => {
    layers.forEach((layer) => {
      expect(getColorScale(layer)).toHaveLength(8)
    })
  })
})

describe('getLegendRanges', () => {
  it('returns 8 ranges for each layer (matches 8-bin colors)', () => {
    const layers: DemographicLayer[] = [
      'pct_under_18',
      'pct_over_65',
      'pct_nonwhite',
      'median_income',
      'cancer_mortality_male_per_100k',
      'cancer_mortality_female_per_100k',
      'heart_disease_mortality_per_100k',
      'total_pop',
    ]

    layers.forEach((layer) => {
      const ranges = getLegendRanges(layer)
      expect(ranges).toHaveLength(8)
    })
  })

  it('income ranges are in currency format', () => {
    const ranges = getLegendRanges('median_income')
    expect(ranges[0]).toContain('$')
    expect(ranges[7]).toContain('$')
  })

  it('percentage layers have % suffix', () => {
    const ranges = getLegendRanges('pct_nonwhite')
    expect(ranges[0]).toContain('%')
    expect(ranges[7]).toContain('%')
  })
})

describe('getLayerLabel', () => {
  it('returns human-readable labels', () => {
    expect(getLayerLabel('pct_under_18')).toBe('% Under 18')
    expect(getLayerLabel('pct_over_65')).toBe('% Over 65')
    expect(getLayerLabel('pct_nonwhite')).toBe('% Non-White')
    expect(getLayerLabel('median_income')).toBe('Median Household Income')
    expect(getLayerLabel('total_pop')).toBe('Total Population')
  })

  it('mortality labels include population context', () => {
    expect(getLayerLabel('cancer_mortality_male_per_100k')).toContain('Cancer')
    expect(getLayerLabel('cancer_mortality_male_per_100k')).toContain('Male')
    expect(getLayerLabel('cancer_mortality_female_per_100k')).toContain('Female')
    expect(getLayerLabel('heart_disease_mortality_per_100k')).toContain('Heart Disease')
  })
})
