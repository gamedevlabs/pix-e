export function usePxKeyDefinitions() {
  return useCrudForPxWithAuthentication<PxKeyDefinition>('api/pxkeydefinitions/')
}
