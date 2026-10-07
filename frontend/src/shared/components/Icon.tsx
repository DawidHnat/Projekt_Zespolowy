import type { CSSProperties } from 'react'

const paths = {
  fleet: (
    <>
      <rect x="3" y="5" width="12" height="12" rx="2" />
      <path d="M15 9h3l3 4v4h-6M3 13h12" />
      <circle cx="7" cy="18" r="2" />
      <circle cx="18" cy="18" r="2" />
    </>
  ),
  history: (
    <>
      <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
      <path d="M3 3v5h5m4-1v5l3 2" />
    </>
  ),
  analytics: (
    <>
      <path d="M4 4v16h16M8 16v-5m5 5V7m5 9v-3" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 4 4" />
    </>
  ),
  arrow: (
    <>
      <path d="M5 12h14m-6-6 6 6-6 6" />
    </>
  ),
  location: (
    <>
      <path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 14 0Z" />
      <circle cx="12" cy="10" r="2" />
    </>
  ),
  refresh: (
    <>
      <path d="M20 7v5h-5M4 17v-5h5m-5 0a8 8 0 0 1 13-6l3 3M4 15l3 3a8 8 0 0 0 13-6" />
    </>
  ),
  check: (
    <>
      <path d="m5 12 4 4L19 6" />
    </>
  ),
  alert: (
    <>
      <path d="m10 4-8 14a2 2 0 0 0 2 3h16a2 2 0 0 0 2-3L14 4a2 2 0 0 0-4 0Z" />
      <path d="M12 9v4m0 3v1" />
    </>
  ),
  edit: (
    <>
      <path d="m15 5 4 4M4 20l5-1L21 7a2.8 2.8 0 0 0-4-4L5 15l-1 5Z" />
    </>
  ),
  distance: (
    <>
      <path d="M5 3 2 21m17-18 3 18M12 4v3m0 4v3m0 4v3" />
    </>
  ),
  chevron: (
    <>
      <path d="m9 5 7 7-7 7" />
    </>
  ),
  close: (
    <>
      <path d="m6 6 12 12M6 18 18 6" />
    </>
  ),
} as const

export type IconName = keyof typeof paths

export function Icon({
  name,
  size = 20,
  style,
}: {
  name: IconName
  size?: number
  style?: CSSProperties
}) {
  return (
    <svg
      width={size}
      height={size}
      style={style}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  )
}
