export function usePxChartEdges(chartId: string | number) {
  return useCrudWithAuthentication<PxChartEdge>(`api/pxcharts/${chartId}/pxedges/`)
}
