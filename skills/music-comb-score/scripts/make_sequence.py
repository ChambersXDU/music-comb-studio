#!/usr/bin/env python3
"""Convert already transcribed, simplified score events to a music comb plan."""
import argparse
import json
import re
import sys
from pathlib import Path

LABELS = ['F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B', 'C1', 'Db1', 'D1',
          'Eb1', 'E1', 'F1', 'Gb1', 'G1', 'Ab1', 'A1', 'Bb1', 'B1', 'C2']
NATURAL = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def midi(pitch):
    if not isinstance(pitch, str):
        raise ValueError('pitch must be a scientific pitch such as F4, or null for a rest')
    match = re.fullmatch(r'([A-Ga-g])([#b♯♭]?)(-?\d+)', pitch)
    if not match:
        raise ValueError(f'Invalid scientific pitch: {pitch}')
    letter, accidental, octave = match.groups()
    value = (int(octave) + 1) * 12 + NATURAL[letter.upper()]
    value += 1 if accidental in ['#', '♯'] else -1 if accidental in ['b', '♭'] else 0
    if not 0 <= value <= 127:
        raise ValueError(f'Pitch outside MIDI range: {pitch}')
    return value


def convert(document, transpose=0, octave_shift=0, rests_as_blanks=True):
    events = document.get('events')
    if not isinstance(events, list) or not events:
        raise ValueError('events must be a non-empty list of simplified score events')
    sequence, alignment = [], []
    previous_pitch = None
    last_note_index = None
    shift = transpose + 12 * octave_shift
    for index, event in enumerate(events):
        if not isinstance(event, dict) or 'pitch' not in event:
            raise ValueError(f'Event {index + 1} requires pitch')
        pitch = event['pitch']
        tie = event.get('tie_to_previous', False)
        if not isinstance(tie, bool):
            raise ValueError(f'Event {index + 1}: tie_to_previous must be boolean')
        row = {'event': index + 1, 'pitch': pitch, 'lyric': event.get('lyric', '')}
        if pitch is None:
            if tie:
                raise ValueError(f'Event {index + 1}: a rest cannot be tied')
            if rests_as_blanks:
                sequence.append('·')
                row.update(tooth=len(sequence), note='·', action='rest_as_blank')
            else:
                row['action'] = 'rest_not_a_tooth'
            previous_pitch = None
            last_note_index = None
        else:
            value = midi(pitch)
            if tie:
                if previous_pitch != value or last_note_index is None:
                    raise ValueError(f'Event {index + 1}: tie must continue the immediately preceding pitch')
                row.update(tooth=last_note_index, note=sequence[last_note_index - 1], action='tie_continuation')
            else:
                target = value + shift
                if not 53 <= target <= 72:
                    raise ValueError(f'Event {index + 1} ({pitch}) maps outside F3–C5; choose a consistent transpose/octave shift or another excerpt')
                sequence.append(LABELS[target - 53])
                last_note_index = len(sequence)
                row.update(tooth=last_note_index, note=sequence[-1], action='note')
            previous_pitch = value
        alignment.append(row)
    if not 8 <= len(sequence) <= 33:
        raise ValueError(f'Comb requires 8–33 positions; got {len(sequence)}. Do not silently truncate or pad.')
    plan = {'notes': ' '.join(sequence), 'offsets': [], 'extension': 0, 'layers': []}
    audit = {'source': document.get('source'), 'original_key': document.get('original_key'),
             'target_key': document.get('target_key'), 'transpose_semitones': transpose,
             'octave_shift': octave_shift, 'rests_as_blanks': rests_as_blanks,
             'simplifications': document.get('simplifications', []), 'alignment': alignment,
             'sequence': sequence, 'count': len(sequence)}
    return plan, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='Output plan JSON path')
    parser.add_argument('--transpose', type=int, default=0, help='Uniform semitone shift')
    parser.add_argument('--octave-shift', type=int, default=0)
    rests = parser.add_mutually_exclusive_group()
    rests.add_argument('--rests-as-blanks', action='store_true', help='Keep rests as blank positions (default)')
    rests.add_argument('--omit-rests', action='store_true', help='Explicitly omit rest positions')
    args = parser.parse_args()
    try:
        document = json.loads(args.input.read_text(encoding='utf-8'))
        plan, audit = convert(document, args.transpose, args.octave_shift, not args.omit_rests)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
        args.out.with_suffix('.score.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
        print(plan['notes'])
        print(f"{audit['count']} positions; plan: {args.out}; audit: {args.out.with_suffix('.score.json')}")
    except (ValueError, TypeError, OSError, AttributeError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
