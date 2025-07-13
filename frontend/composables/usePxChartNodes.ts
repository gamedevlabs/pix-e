export function usePxChartNodes(chartId: string | number) {
  return useCrudWithAuthentication<PxChartNode>(`api/pxcharts/${chartId}/pxnodes/`)
}
