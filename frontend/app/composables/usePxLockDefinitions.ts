export function usePxLockDefinitions() {
  return useCrudForPxWithAuthentication<PxLockDefinition>('pxlockdefinitions/')
}
