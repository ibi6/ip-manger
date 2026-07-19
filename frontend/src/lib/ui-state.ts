export function adminRouteAllowed(role: string | null | undefined): boolean {
  return role === 'admin'
}

interface AddressSelectionCandidate {
  id: number
  status: string
  is_network_or_broadcast: boolean
}

export function releasableAddressIds(rows: AddressSelectionCandidate[]): number[] {
  return rows
    .filter(
      (row) =>
        !row.is_network_or_broadcast &&
        (row.status === 'allocated' || row.status === 'reserved' || row.status === 'disabled'),
    )
    .map((row) => row.id)
}

export function selectionState(
  selectedIds: number[],
  availableIds: number[],
): { checked: boolean; indeterminate: boolean } {
  if (availableIds.length === 0) return { checked: false, indeterminate: false }

  const selected = new Set(selectedIds)
  const selectedCount = availableIds.filter((id) => selected.has(id)).length
  return {
    checked: selectedCount === availableIds.length,
    indeterminate: selectedCount > 0 && selectedCount < availableIds.length,
  }
}
