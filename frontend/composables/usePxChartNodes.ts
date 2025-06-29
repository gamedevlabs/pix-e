export function usePxChartNodes(chartId: string | number) {
  return useCrud<PxChartNode>(`api/pxcharts/${chartId}/nodes/`)
}