import { describe, it, expect } from 'vitest'
import * as ds from '../src/index'

describe('package scaffold', () => {
  it('exports the Collection type surface (module loads)', () => {
    expect(ds).toBeTypeOf('object')
  })
})
