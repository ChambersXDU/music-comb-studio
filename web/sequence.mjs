export function expandPauses(sequence) {
  const tokens = Array.isArray(sequence) ? sequence : sequence.trim().split(/[\s,，;；|]+/).filter(Boolean);
  return tokens.flatMap(token => {
    return ['.', '-', '_', 'R', 'r'].includes(token) ? ['·'] : [token];
  });
}

export function makeTimeline(sequence, slotSeconds = .28) {
  const positions = expandPauses(sequence);
  return {duration: positions.length * slotSeconds,
    events: positions.flatMap((note, index) => note === '·' ? [] : [{note, start: index * slotSeconds}])};
}
