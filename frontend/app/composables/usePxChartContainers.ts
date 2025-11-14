export function usePxChartContainers(chartId: string | number) {
  return useCrudForPxWithAuthentication<PxChartContainer>(`api/pxcharts/${chartId}/pxcontainers/`)
}
