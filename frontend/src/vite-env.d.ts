/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_DATA_SOURCE: string
  readonly VITE_MAPLIBRE_STYLE: string
  readonly VITE_R2_BASE_URL: string
  // VITE_NOMINATIM_UA removed — geocoding uses Photon (ADR-006)
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
