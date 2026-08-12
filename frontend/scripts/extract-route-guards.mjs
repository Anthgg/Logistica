// Extrae del AppRouter cada `path` y las permissions que lo protegen.
// El parser recorre el JSX carácter a carácter para cerrar cada etiqueta
// <Route ...> respetando el anidamiento de llaves de los atributos.
import { readFileSync } from 'node:fs'

export function extractRouteGuards(source) {
  const rows = []
  const stack = []
  let i = 0

  while (i < source.length) {
    const openTag = source.indexOf('<Route', i)
    const closeTag = source.indexOf('</Route>', i)

    if (openTag === -1 && closeTag === -1) break

    if (closeTag !== -1 && (openTag === -1 || closeTag < openTag)) {
      stack.pop()
      i = closeTag + '</Route>'.length
      continue
    }

    // Avanzar hasta el '>' que cierra la etiqueta, ignorando los que estén
    // dentro de llaves (element={<Foo />}) o de cadenas.
    let depth = 0
    let j = openTag + '<Route'.length
    let quote = null
    for (; j < source.length; j += 1) {
      const ch = source[j]
      if (quote) {
        if (ch === quote) quote = null
        continue
      }
      if (ch === '"' || ch === "'" || ch === '`') { quote = ch; continue }
      if (ch === '{') depth += 1
      else if (ch === '}') depth -= 1
      else if (ch === '>' && depth === 0) break
    }

    const tag = source.slice(openTag, j + 1)
    const selfClosing = tag.trimEnd().endsWith('/>')
    const permKeys = [...tag.matchAll(/LOGISTICS_PERMISSIONS\.([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)/g)]
      .map((m) => `${m[1]}.${m[2]}`)
    const literals = [...tag.matchAll(/permission="([^"]+)"/g)].map((m) => `literal:${m[1]}`)
    const own = [...permKeys, ...literals]
    const pathMatch = tag.match(/path="([^"]+)"/)

    if (pathMatch) {
      rows.push({ path: pathMatch[1], guards: [...stack.flat(), ...own] })
    }
    if (!selfClosing) stack.push(own)
    i = j + 1
  }

  return rows
}

if (process.argv[2]) {
  const rows = extractRouteGuards(readFileSync(process.argv[2], 'utf8'))
  process.stdout.write(JSON.stringify(rows, null, 1))
}
