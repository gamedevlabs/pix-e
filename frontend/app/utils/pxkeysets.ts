// PxKeySet type and associated logic
// used in path calculation in PxChart

export type PxKeySet = Record<string, number>

export function getKeySetFromDefArray(keys: string[]): PxKeySet {
  if (!keys || !keys.length) return {}

  const keyset: PxKeySet = {}
  for (const key of keys) {
    if (!keyset[key]) keyset[key] = 0
    keyset[key] += 1
  }
  return keyset
}

// assumes the input is a single assignment,
// i.e. each definition can only appear once
export function getKeySetFromKeyAssignment(keys: PxKey[]): PxKeySet {
  if (!keys || !keys.length) return {}

  const keyset: PxKeySet = {}
  for (const key of keys) {
    keyset[key.definition] = key.count
  }
  return keyset
}

export function pxKeySetDifference(
  inventory: PxKeySet,
  consumed: PxKeySet,
  consumableKeyDefs: string[],
): PxKeySet {
  const diff = { ...inventory }
  for (const [def, count] of Object.entries(consumed)) {
    if (!diff[def] || diff[def] < 1) {
      return {}
    } else if (consumableKeyDefs.includes(def)) {
      diff[def] -= count
    }
  }
  const filteredDiff: PxKeySet = {}
  for (const [def, count] of Object.entries(diff)) {
    if (count) filteredDiff[def] = count
  }

  return filteredDiff
}

export function mergePxKeySets(keyset1: PxKeySet, keyset2: PxKeySet) {
  const res = { ...keyset1 }
  for (const [def, count] of Object.entries(keyset2)) {
    if (!res[def]) {
      res[def] = count
    } else {
      res[def] += count
    }
  }
  return res
}

export function pxKeySetsAreEqual(keyset1: PxKeySet, keyset2: PxKeySet) {
  for (const [def, count] of Object.entries(keyset1)) {
    if (!keyset2[def] || keyset2[def] != count) {
      return false
    }
  }
  for (const [def, count] of Object.entries(keyset2)) {
    if (!keyset1[def] || keyset1[def] != count) {
      return false
    }
  }
  return true
}

export function pxKeyInventoriesAreEqual(inv1: PxKeySet[], inv2: PxKeySet[]) {
  if (inv1.length !== inv2.length) return false

  for (const keyset of inv1) {
    if (inv2.every((keyset2) => !pxKeySetsAreEqual(keyset, keyset2))) {
      return false
    }
  }
  for (const keyset of inv2) {
    if (inv1.every((keyset1) => !pxKeySetsAreEqual(keyset, keyset1))) {
      return false
    }
  }
  return true
}

export function filterPxKeySet(keyset: PxKeySet, remainingDefs: PxKeyDefinition[]) {
  const remainingDefIds = remainingDefs.map((def) => def.id)
  const filtered: PxKeySet = {}
  for (const [def, count] of Object.entries(keyset)) {
    if (remainingDefIds.includes(def)) {
      filtered[def] = count
    }
  }
  return filtered
}
