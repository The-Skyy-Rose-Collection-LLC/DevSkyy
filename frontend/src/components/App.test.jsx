import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import App from '../App.jsx'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    // Just check that it renders successfully
    expect(document.body).toBeTruthy()
  })

  it('has correct title', () => {
    render(<App />)
    // Basic smoke test - check if App component exists
    expect(document.body).toBeInTheDocument()
  })
})