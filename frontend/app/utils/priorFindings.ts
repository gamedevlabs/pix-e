export type Paper = {
  id: string
  title: string
  year: number
  citation: string
}

export type Finding = {
  id: string
  paperId: string
  quote: string
  tags: string[]
}
