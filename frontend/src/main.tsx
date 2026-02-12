import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { identifyUser } from './posthog'

// Identify test user for analytics
identifyUser('3d4df718-47c3-4903-b09e-711090412204', {
  name: 'Demo User',
  role: 'Sales Manager',
  organization: 'Sanitär-Heinze'
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
