import ParameterType from './ParameterType.js'

export default class GeneratedExpression {
  constructor(
    private readonly expressionTemplate: string,
    public readonly parameterTypes: readonly ParameterType<unknown>[]
  ) {}

  get source() {
    return format(this.expressionTemplate, ...this.parameterTypes.map((t) => t.name || ''))
  }

  /**
   * Returns an array of parameter names to use in generated function/method signatures
   *
   * @returns {ReadonlyArray.<String>}
   */
  get parameterNames(): readonly string[] {
    const usageByTypeName: { [key: string]: number } = {}
    return this.parameterTypes.map((t) => getParameterName(t.name || '', usageByTypeName))
  }
}

function getParameterName(typeName: string, usageByTypeName: { [key: string]: number }) {
  let count = usageByTypeName[typeName]
  count = count ? count + 1 : 1
  usageByTypeName[typeName] = count

  return count === 1 ? typeName : `${typeName}${count}`
}

function format(pattern: string, ...args: readonly string[]): string {
  return pattern.replace(/{(\d+)}/g, (match, number) => args[number])
}
