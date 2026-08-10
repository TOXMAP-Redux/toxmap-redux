/**
 * Demographic layer color utilities.
 * Used by both InlineLegend and MapContainer for consistent colors.
 */
import type { DemographicLayer } from '../../api/types'

/** Color scales matching TOXMAP_DEVELOPMENT_ROADMAP §5.2.1 specification */
export const COLOR_SCALES = {
  // Percentage fields (pct_under_18, pct_over_65, pct_nonwhite): sequential blue
  percentage: ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
  // Income fields (median_income): sequential green
  income: ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c'],
  // Mortality fields (cancer_mortality_*): sequential red
  mortality: ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
  // Total population: sequential purple
  population: ['#f2f0f7', '#cbc9e2', '#9e9ac8', '#756bb1', '#54278f'],
} as const

/** Map layer type to its color scale */
export function getColorScale(layer: DemographicLayer): readonly string[] {
  switch (layer) {
    case 'pct_under_18':
    case 'pct_over_65':
    case 'pct_nonwhite':
      return COLOR_SCALES.percentage
    case 'median_income':
      return COLOR_SCALES.income
    case 'cancer_mortality_male_per_100k':
    case 'cancer_mortality_female_per_100k':
    case 'heart_disease_mortality_per_100k':
      return COLOR_SCALES.mortality
    case 'total_pop':
      return COLOR_SCALES.population
    default:
      return COLOR_SCALES.percentage
  }
}

/** Approximate data ranges for legend labels (derived from typical Census/mortality data) */
export function getLegendRanges(layer: DemographicLayer): string[] {
  switch (layer) {
    case 'pct_under_18':
      // US county range typically 15-30%, bins centered around national avg ~22%
      return ['0-18%', '18-21%', '21-24%', '24-27%', '27%+']
    case 'pct_over_65':
      // US county range typically 10-25%, bins centered around national avg ~16%
      return ['0-12%', '12-15%', '15-18%', '18-22%', '22%+']
    case 'pct_nonwhite':
      return ['0-10%', '10-25%', '25-40%', '40-60%', '60%+']
    case 'median_income':
      return ['<$30k', '$30-45k', '$45-60k', '$60-80k', '$80k+']
    case 'cancer_mortality_male_per_100k':
    case 'cancer_mortality_female_per_100k':
      return ['<100', '100-150', '150-200', '200-250', '250+']
    case 'heart_disease_mortality_per_100k':
      return ['<100', '100-150', '150-200', '200-300', '300+']
    case 'total_pop':
      return ['<10k', '10-50k', '50-100k', '100-500k', '500k+']
    default:
      return ['Low', 'Med-Low', 'Medium', 'Med-High', 'High']
  }
}

/** Human-readable label for the layer type */
export function getLayerLabel(layer: DemographicLayer): string {
  switch (layer) {
    case 'pct_under_18':
      return '% Under 18'
    case 'pct_over_65':
      return '% Over 65'
    case 'pct_nonwhite':
      return '% Non-White'
    case 'median_income':
      return 'Median Household Income'
    case 'cancer_mortality_male_per_100k':
      return 'Cancer Mortality (Male)'
    case 'cancer_mortality_female_per_100k':
      return 'Cancer Mortality (Female)'
    case 'heart_disease_mortality_per_100k':
      return 'Heart Disease Mortality'
    case 'total_pop':
      return 'Total Population'
  }
}
