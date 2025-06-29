export function usePxChartEdges(chartId: string | number) {
  return useCrud<PxChartEdge>(`api/pxcharts/${chartId}/edges/`)
}
