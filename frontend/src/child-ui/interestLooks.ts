// Interest keyword -> card emoji and color theme. Same emojis and color groups as the reader themes in ChildApp.
const interestLooks: Record<string, [string, string]> = {
  fish: ['🐟', 'ocean'], ship: ['⛵', 'ocean'], ocean: ['🌊', 'ocean'],
  rocket: ['🚀', 'space'], robot: ['🤖', 'space'], space: ['🪐', 'space'],
  frog: ['🐸', 'nature'], bear: ['🐻', 'nature'], bug: ['🐞', 'nature'], dinosaur: ['🦕', 'nature'],
  unicorn: ['🦄', 'magic'], dragon: ['🐉', 'magic'], bird: ['🐦', 'magic'],
  cat: ['🐱', 'cozy'], dog: ['🐶', 'cozy'],
}

// First keyword found inside the interests ("dinosaurs" contains "dinosaur"). No match: a star and the default card color.
export function lookFor(interests: string[]) {
  const text = interests.join(' ').toLowerCase()
  const key = Object.keys(interestLooks).find((k) => text.includes(k))
  return key ? interestLooks[key] : ['⭐', 'default']
}
