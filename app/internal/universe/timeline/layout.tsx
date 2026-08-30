import type { ReactNode } from 'react'

export default function UniverseTimelineLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <div
        role="status"
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 50,
          padding: '0.45rem 0.8rem',
          borderBottom: '1px solid #5b4725',
          background: '#151106',
          color: '#d8b66f',
          fontFamily: 'Lato, sans-serif',
          fontSize: '0.72rem',
          fontWeight: 700,
          letterSpacing: '0.04em',
          textAlign: 'center',
        }}
      >
        Seed-Projektion · nicht kanonisch · KUEPER Knowledge Graph ist noch nicht live angebunden
      </div>
      {children}
    </>
  )
}
