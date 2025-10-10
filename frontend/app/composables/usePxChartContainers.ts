export function usePxChartContainers(chartId: string | number) {
  return useCrudWithAuthentication<PxChartContainer>(`api/pxcharts/${chartId}/pxcontainers/`)
}
