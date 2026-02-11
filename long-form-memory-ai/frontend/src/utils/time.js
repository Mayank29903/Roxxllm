const IST_TIMEZONE = 'Asia/Kolkata'

const IST_DATE_TIME_FORMATTER = new Intl.DateTimeFormat('en-GB', {
  timeZone: IST_TIMEZONE,
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false
})

const IST_TIME_FORMATTER = new Intl.DateTimeFormat('en-GB', {
  timeZone: IST_TIMEZONE,
  hour: '2-digit',
  minute: '2-digit',
  hour12: false
})

const IST_DAY_TOKEN_FORMATTER = new Intl.DateTimeFormat('en-GB', {
  timeZone: IST_TIMEZONE,
  day: '2-digit',
  month: '2-digit',
  year: 'numeric'
})

export const normalizeBackendTimestamp = (value) => {
  if (!value) return null

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value
  }

  const asString = String(value).trim()
  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(asString)
  const safeValue = hasTimezone ? asString : `${asString}Z`
  const parsed = new Date(safeValue)

  if (!Number.isNaN(parsed.getTime())) {
    return parsed
  }

  const fallback = new Date(asString)
  return Number.isNaN(fallback.getTime()) ? null : fallback
}

export const isTodayIST = (timestamp) => {
  const date = normalizeBackendTimestamp(timestamp)
  if (!date) return false

  return (
    IST_DAY_TOKEN_FORMATTER.format(date) ===
    IST_DAY_TOKEN_FORMATTER.format(new Date())
  )
}

export const formatSidebarIST = (timestamp) => {
  const date = normalizeBackendTimestamp(timestamp)
  if (!date) return ''

  if (isTodayIST(date)) {
    return `Today ${IST_TIME_FORMATTER.format(date)} IST`
  }

  return `${IST_DATE_TIME_FORMATTER.format(date).replace(',', '')} IST`
}

export const formatISTDateTime = (timestamp) => {
  const date = normalizeBackendTimestamp(timestamp)
  if (!date) return ''
  return `${IST_DATE_TIME_FORMATTER.format(date).replace(',', '')} IST`
}

export const formatNowISTDateTime = () =>
  `${IST_DATE_TIME_FORMATTER.format(new Date()).replace(',', '')} IST`
