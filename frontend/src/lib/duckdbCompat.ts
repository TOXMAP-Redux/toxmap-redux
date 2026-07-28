/**
 * Data source routing — the two-mode seam.
 *
 * Dev mode  (VITE_DATA_SOURCE=api):    React → FastAPI (Phases 0–6)
 * Prod mode (VITE_DATA_SOURCE=duckdb): React → DuckDB WASM → Parquet on R2 (Phase 7)
 *
 * All React components call api/ functions, which route through resolveDataSource().
 * Phase 3 implements only dev (api) mode. DuckDB WASM hooks are Phase 7.
 */

export type DataSource = 'api' | 'duckdb'

/** Returns the active data source from VITE_DATA_SOURCE env var. Defaults to 'api'. */
export function resolveDataSource(): DataSource {
  const src = import.meta.env.VITE_DATA_SOURCE
  return src === 'duckdb' ? 'duckdb' : 'api'
}

/** True when DuckDB WASM is the active data source (Phase 7). */
export function isDuckDBMode(): boolean {
  return resolveDataSource() === 'duckdb'
}
