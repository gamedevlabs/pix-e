export function usePxNodes() {
  return useCrudForPxWithAuthentication<PxNode>('pxnodes/')
}
