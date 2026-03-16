export function usePxKeys() {
  return useCrudForPxWithAuthentication<PxKey>('pxkeys/')
}
