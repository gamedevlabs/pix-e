export function usePxLockDefinitions() {
  return useCrudForPxWithAuthentication<PxLockDefinition>('api/pxlockdefinitions/')
}
