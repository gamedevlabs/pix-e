export function usePxNodes() {
  return useCrudForPxWithAuthentication<PxNode>('api/pxnodes/')
}
