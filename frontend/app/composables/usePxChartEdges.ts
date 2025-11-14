export function usePxChartEdges(chartId: string | number) {
  return useCrudForPxWithAuthentication<PxChartEdge>(`api/pxcharts/${chartId}/pxedges/`)
}
