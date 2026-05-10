export function usePxChartSettings(chartId: string) {
  const { items, loading, error, fetchAll, fetchById, createItem, updateItem, deleteItem } =
    useCrudForPxWithAuthentication<PxChartSettings>(`api/pxcharts/${chartId}/settings/`)

  const { user } = useAuthentication()

  const defaultSettings = {
    px_chart: chartId,
    use_locks: true,
    ignore_consumable_keys: false,
    show_soft_locks: false,
  }

  const settings: Ref<PxChartSettings> = ref(defaultSettings)

  async function loadChartSettingsForUser() {
    await fetchAll()
    const found = items.value.find(
      (item) => item.px_chart === chartId && item.owner === user.value?.id,
    )
    if (!found) {
      const newSettingsId = await createItem(defaultSettings)
      settings.value = await fetchById(newSettingsId)
    } else {
      settings.value = found
    }
  }

  return {
    items,
    loading,
    error,
    fetchAll,
    fetchById,
    createItem,
    updateItem,
    deleteItem,
    loadChartSettingsForUser,
    settings,
  }
}
