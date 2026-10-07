import assert from 'node:assert/strict';
import {expandPauses, makeTimeline} from '../web/sequence.mjs';

assert.deepEqual(expandPauses('C1 · E1 R'), ['C1', '·', 'E1', '·']);
const timeline = makeTimeline('C1 · E1 · G1');
assert.deepEqual(timeline.events.map(e => e.note), ['C1', 'E1', 'G1']);
timeline.events.forEach((event, i) => assert.ok(Math.abs(event.start - [0, .56, 1.12][i]) < 1e-9));
assert.ok(Math.abs(timeline.duration - 1.4) < 1e-9);
assert.deepEqual(makeTimeline(['·', '·']).events, []);
console.log('Pause expansion and playback timing passed.');
