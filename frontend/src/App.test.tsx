import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import App from './App'

test('başlığı gösterir', () => {
  render(<App />)
  expect(screen.getByRole('heading', { name: 'FlowPilot' })).toBeDefined()
})
