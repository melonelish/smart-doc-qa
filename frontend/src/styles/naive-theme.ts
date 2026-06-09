import { darkTheme, lightTheme, type GlobalThemeOverrides } from 'naive-ui'

/* Naive UI 暗色主题覆盖 — 与 CSS 变量保持一致 */
const darkOverrides: GlobalThemeOverrides = {
  common: {
    bodyColor: '#0a0e17',
    cardColor: '#1a1f2e',
    modalColor: '#1a1f2e',
    tableColor: '#1a1f2e',
    inputColor: '#151a28',
    actionColor: '#1a1f2e',
    popoverColor: '#1a1f2e',
    hoverColor: 'rgba(99, 102, 241, 0.1)',
    primaryColor: '#6366f1',
    primaryColorHover: '#818cf8',
    primaryColorPressed: '#4f46e5',
    primaryColorSuppl: '#6366f1',
    infoColor: '#3b82f6',
    successColor: '#10b981',
    warningColor: '#f59e0b',
    errorColor: '#ef4444',
    textColor1: '#f1f5f9',
    textColor2: '#94a3b8',
    textColor3: '#64748b',
    borderColor: '#252b3b',
    dividerColor: '#252b3b',
    placeholderColor: '#64748b',
    borderRadius: '8px',
    fontSize: '13px',
    boxShadow1: '0 1px 3px rgba(0, 0, 0, 0.3)',
    boxShadow2: '0 4px 12px rgba(0, 0, 0, 0.4)',
    boxShadow3: '0 8px 32px rgba(0, 0, 0, 0.5)',
  },
  Button: {
    fontSizeTiny: '10px',
    fontSizeSmall: '11px',
    fontSizeMedium: '12px',
    fontSizeLarge: '14px',
    paddingTiny: '4px 10px',
    paddingSmall: '6px 14px',
    paddingMedium: '8px 18px',
    paddingLarge: '10px 22px',
    borderRadius: '6px',
    textColorPrimary: '#fff',
    colorPrimary: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    colorHoverPrimary: 'linear-gradient(135deg, #818cf8 0%, #a78bfa 100%)',
  },
  Input: {
        border: '1px solid #252b3b',
    borderHover: '1px solid #6366f1',
    borderFocus: '1px solid #6366f1',
    boxShadowFocus: '0 0 0 2px rgba(99, 102, 241, 0.15)',
    fontSizeMedium: '12px',
    heightMedium: '34px',
    textColor: '#f1f5f9',
    placeholderColor: '#64748b',
    color: '#151a28',
    borderRadius: '6px',
  },
  Select: {
    menuColor: '#1a1f2e',
    menuBoxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
    actionColor: '#1a1f2e',
  },
  Modal: {
    color: '#1a1f2e',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
    borderRadius: '12px',
  },
  Tag: {
    borderRadius: '4px',
    fontSizeSmall: '9px',
    heightSmall: '18px',
    padding: '0 6px',
  },
  Card: {
        color: '#1a1f2e',
    borderColor: '#252b3b',
    borderRadius: '16px',
    paddingMedium: '16px',
  },
  Empty: {
    iconSize: '48px',
  },
  Spin: {
    color: '#6366f1',
  },
  Progress: {
        railHeight: '6px',
    colorSuccess: '#10b981',
    colorProcessing: '#3b82f6',
  },
  Tooltip: {
    color: '#1a1f2e',
  },
  Popconfirm: {
    color: '#1a1f2e',
  },
  Notification: {
    color: '#1a1f2e',
  },
  Message: {
    color: '#1a1f2e',
  },
  Drawer: {
    color: '#1a1f2e',
  },
  Switch: {
    railColor: '#252b3b',
    railColorActive: '#6366f1',
  },
}

/* 亮色主题覆盖 */
const lightOverrides: GlobalThemeOverrides = {
  common: {
    bodyColor: '#f8fafc',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    inputColor: '#f1f5f9',
    primaryColor: '#6366f1',
    primaryColorHover: '#818cf8',
    primaryColorPressed: '#4f46e5',
    textColor1: '#0f172a',
    textColor2: '#334155',
    textColor3: '#64748b',
    borderColor: '#e2e8f0',
    dividerColor: '#e2e8f0',
    placeholderColor: '#64748b',
    boxShadow1: '0 1px 3px rgba(0, 0, 0, 0.06)',
    boxShadow2: '0 4px 12px rgba(0, 0, 0, 0.08)',
    boxShadow3: '0 8px 32px rgba(0, 0, 0, 0.1)',
  },
  Button: {
    fontSizeTiny: '10px',
    fontSizeSmall: '11px',
    fontSizeMedium: '12px',
    fontSizeLarge: '14px',
    paddingTiny: '4px 10px',
    paddingSmall: '6px 14px',
    paddingMedium: '8px 18px',
    paddingLarge: '10px 22px',
    borderRadius: '6px',
    textColorPrimary: '#fff',
    colorPrimary: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    colorHoverPrimary: 'linear-gradient(135deg, #818cf8 0%, #a78bfa 100%)',
    colorPressedPrimary: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
  },
  Input: {
    fontSizeMedium: '12px',
    heightMedium: '34px',
    color: '#f1f5f9',
    borderRadius: '6px',
  },
  Tag: {
    borderRadius: '4px',
    fontSizeSmall: '9px',
    heightSmall: '18px',
    padding: '0 6px',
  },
  Card: {
    color: '#ffffff',
    borderColor: '#e2e8f0',
    borderRadius: '16px',
    paddingMedium: '16px',
  },
}

export function getNaiveTheme(theme: 'dark' | 'light') {
  return {
    theme: theme === 'dark' ? darkTheme : lightTheme,
    themeOverrides: theme === 'dark' ? darkOverrides : lightOverrides,
  }
}