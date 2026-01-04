export function usePxCharts() {
  return useCrudForPxWithAuthentication<PxChart>('api/pxcharts/')
}
