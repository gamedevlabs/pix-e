export function usePxComponentDefinitions() {
  return useCrudForPxWithAuthentication<PxComponentDefinition>('api/pxcomponentdefinitions/')
}
