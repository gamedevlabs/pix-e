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
  const res = { ...inventory }
  for (const [def, count] of Object.entries(consumed)) {
    if (!res[def] || res[def] < 1) {
      return {}
    } else if (consumableKeyDefs.includes(def)) {
      res[def] -= count
    }
  }
  return res
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
