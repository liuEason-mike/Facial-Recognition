/**
 * 字典值
 */
export type IShortcutValue = number | string

/**
 * 字典项
 */
export interface IShortcut<T extends IShortcutValue = IShortcutValue> {
  /**
   * 字典值
   */
  id: T
  /**
   * 文字
   */
  name: string
}
