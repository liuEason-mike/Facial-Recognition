import { isArray } from '@ntnyq/utils'
import type { IShortcut, IShortcutValue } from '@/types'

/**
 * Render shortcut value
 * @param value - shortcut value
 * @param list - shortcut list
 * @returns - shortcut name or undefined
 */
export function renderShortcutValue(
  value: IShortcutValue,
  list: IShortcut[] = [],
): string | undefined {
  if (!isArray(list) || !list.length) {
    return
  }
  const matched = list.find(item => item.id === value)
  return matched?.name
}
