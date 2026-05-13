export function usePxKeys() {
  return useCrudForPxWithAuthentication<PxKey>('api/pxkeys/')
}
