/**
 * Hook: debounced chemical name autocomplete (story 3.2.4).
 * Calls GET /api/v1/chemicals/search?q= on each keystroke (300ms debounce).
 */
import { useEffect, useRef, useState } from 'react'
import { searchChemicals } from '../api/chemicals'
import type { Chemical } from '../api/types'

export interface UseChemicalAutocompleteResult {
  suggestions: Chemical[]
  loading: boolean
}

/**
 * Returns autocomplete suggestions for the given query string.
 * Empty array when query < 2 chars or on error.
 */
export function useChemicalAutocomplete(query: string): UseChemicalAutocompleteResult {
  const [suggestions, setSuggestions] = useState<Chemical[]>([])
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const latestQuery = useRef(query)
  latestQuery.current = query

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (query.length < 2) {
      setSuggestions([])
      setLoading(false)
      return
    }

    setLoading(true)
    debounceRef.current = setTimeout(() => {
      const q = latestQuery.current
      searchChemicals(q)
        .then((results) => {
          if (latestQuery.current === q) setSuggestions(results)
        })
        .catch(() => {
          if (latestQuery.current === q) setSuggestions([])
        })
        .finally(() => {
          if (latestQuery.current === q) setLoading(false)
        })
    }, 300)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query])

  return { suggestions, loading }
}
