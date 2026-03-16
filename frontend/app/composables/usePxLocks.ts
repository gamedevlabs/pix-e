export function usePxLocks() {
  return useCrudForPxWithAuthentication<PxLock>('pxlocks/')
}
