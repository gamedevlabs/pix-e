export function usePxLocks(chartId: string | number) {
  return useCrudForPxWithAuthentication<PxLock>(`api/pxcharts/${chartId}/pxlocks/`)
}
