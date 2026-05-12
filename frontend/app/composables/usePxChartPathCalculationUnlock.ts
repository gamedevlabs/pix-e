import type { Node } from '@vue-flow/core'
import { pxKeySetDifference, getKeySetFromDefArray } from '#imports'

export function usePxChartPathCalculationUnlock(
  nodes: Ref<Node[]>,
  settings: Ref<PxChartSettings>,
  pxLockDefinitions: Ref<PxLockDefinition[]>,
  pxKeyDefinitions: Ref<PxKeyDefinition[]>,
) {
  const pxLockDefinitionsById: ComputedRef<Record<string, PxLockDefinition>> = computed(() => {
    return pxLockDefinitions.value.reduce((acc, def) => ({ [def.id]: def, ...acc }), {})
  })

  const consumableKeyDefs: ComputedRef<string[]> = computed(() => {
    return pxKeyDefinitions.value.filter((def) => def.consumable).map((def) => def.id)
  })

  const pxKeyDefinitionsById: ComputedRef<Record<string, PxKeyDefinition>> = computed(() => {
    return pxKeyDefinitions.value.reduce((acc, def) => ({ [def.id]: def, ...acc }), {})
  })

  function getKeysInNode(nodeId: string): PxKey[] {
    return nodes.value.find((node) => node.id === nodeId)!.data.keys
  }

  // assumes non-soft gate locks can be unlocked with available keys
  function isSoftUnlock(keys: PxKeySet, locks: PxLock[]) {
    if (!locks || !locks.length) return false

    const softGates: PxLock[] = locks.filter(
      (lock) => pxLockDefinitionsById.value[lock.definition]!.soft_gate,
    )

    return !canUnlock(keys, softGates, false)
  }

  function cartesian(sets: string[][]) {
    if (!sets.length || sets.every((set) => !set.length)) {
      return [[]]
    }

    let prod: string[][] = sets[0]!.map((x) => [x])

    sets.slice(1).forEach((set) => {
      let newProd: string[][] = []
      set.forEach((element) => {
        newProd = newProd.concat(prod.map((p) => p.concat([element])))
      })
      prod = newProd
    })

    return prod
  }

  // removes consumed keys for each valid combination of inventory keyset and unlocking key combination
  function removeConsumed(inventory: PxKeySet[], locks: PxLock[]): PxKeySet[] {
    if (!locks.length) return inventory

    const consumableRequirements = locks
      .flatMap((lock) => new Array(lock.count).fill([lock.definition]))
      .map((lockDefId) => pxLockDefinitionsById.value[lockDefId]!.unlocked_by)
      .filter(
        (requiredKeys) =>
          requiredKeys.filter((keyDef) => pxKeyDefinitionsById.value[keyDef]!.consumable).length,
      )

    if (!consumableRequirements.length) return inventory

    const unlockingKeySets: PxKeySet[] = cartesian(consumableRequirements).map((keys) =>
      getKeySetFromDefArray(keys),
    )

    const updatedInventory: PxKeySet[] = []
    for (const keyset of inventory) {
      for (const unlocking of unlockingKeySets) {
        const canUnlock = Object.entries(unlocking).every(
          ([keyDefId, count]) =>
            // locks can be unlocked if keys are present and, if consumable, present at least as many times as required
            keyset[keyDefId] &&
            (!pxKeyDefinitionsById.value[keyDefId]!.consumable || keyset[keyDefId] >= count),
        )
        if (canUnlock) {
          // if current keyset matches unlocking configuration:
          // add current keyset (minus required consumable keys) to new inventory
          updatedInventory.push(pxKeySetDifference(keyset, unlocking, consumableKeyDefs.value))
        }
      }
    }

    return updatedInventory
  }

  function canUnlock(keysInInventory: PxKeySet, locks: PxLock[], unlockSoftGates: boolean = true) {
    if (!locks.length) {
      return true
    }

    // for set of locks, determine all sets of keys that can unlock them
    const requiredKeysPerLock: string[][] = locks
      .flatMap((lock) => new Array(lock.count).fill([lock.definition]))
      .map((lockDefId) => pxLockDefinitionsById.value[lockDefId]!)
      .map((def) => (def.soft_gate && unlockSoftGates ? [] : def.unlocked_by))
    const unlockingKeySets: PxKeySet[] = cartesian(requiredKeysPerLock).map((keys) =>
      getKeySetFromDefArray(keys),
    )

    // edge is unlockable if any unlocking key set is a subset of the available keys
    const canUnlock = unlockingKeySets.some((unlocking) =>
      Object.entries(unlocking).every(
        ([key, count]) =>
          // locks can be unlocked if keys are present and, if consumable, present at least as many times as required
          keysInInventory[key] &&
          (!pxKeyDefinitionsById.value[key]!.consumable ||
            settings.value.ignore_consumable_keys ||
            keysInInventory[key] >= count),
      ),
    )
    return canUnlock
  }

  return {
    canUnlock,
    removeConsumed,
    isSoftUnlock,
    getKeysInNode,
    pxLockDefinitionsById,
    pxKeyDefinitionsById,
    consumableKeyDefs,
  }
}
