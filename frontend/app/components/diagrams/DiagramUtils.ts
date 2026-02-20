function initColorIterator() {
  let idx = 0

  const colors = ['#06b6d4', '#164e63', '#93c5fd', '#1e3a8a', '#d1d5db', '#1f2937']

  const colorIterator = {
    next() {
      const result = { value: colors[idx % colors.length], done: false }
      idx++
      return result
    },
  }
  return colorIterator
}

interface NodeData {
  name: string
  [key: string]: string | number | boolean | undefined
}

export { type NodeData, initColorIterator }
