;(function () {
  try {
    var stored = window.localStorage.getItem('netledger_theme')
    var preference = stored === 'light' || stored === 'dark' ? stored : 'system'
    var systemDark =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches
    var resolved = preference === 'system' ? (systemDark ? 'dark' : 'light') : preference
    document.documentElement.dataset.theme = resolved
    document.documentElement.style.colorScheme = resolved
  } catch {
    document.documentElement.dataset.theme = 'light'
    document.documentElement.style.colorScheme = 'light'
  }
})()
