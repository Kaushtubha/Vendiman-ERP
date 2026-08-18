/**
 * src/main.tsx — Application Entry Point
 *
 * WHY StrictMode: Enables additional development warnings.
 * Identifies side effects, deprecated APIs, unexpected component behaviors.
 * Has NO effect in production builds — zero performance cost in prod.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// WHY non-null assertion on getElementById('root'):
// index.html guarantees #root exists. TypeScript doesn't know this.
// The ! assertion is safe here — if root doesn't exist, React throws
// a clear error immediately.
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
