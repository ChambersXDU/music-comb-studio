import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parent.parent / 'skills/music-comb-score/scripts/make_sequence.py'
spec = importlib.util.spec_from_file_location('score_sequence', path)
sequence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sequence)


class ScoreSkillTests(unittest.TestCase):
    def test_uniform_transpose_and_enharmonics(self):
        events = [{'pitch': p} for p in ['F4', 'A4', 'F4', 'Bb4', 'A4', 'Bb4', 'C5', 'A4']]
        plan, audit = sequence.convert({'events': events}, transpose=-5)
        self.assertEqual(plan['notes'], 'C1 E1 C1 F1 E1 F1 G1 E1')
        self.assertEqual(sequence.midi('E#4'), sequence.midi('F4'))
        self.assertEqual(sequence.midi('Cb4'), sequence.midi('B3'))
        self.assertEqual(audit['count'], 8)

    def test_ties_rearticulations_and_rests(self):
        events = [{'pitch': 'C4'}, {'pitch': 'C4', 'tie_to_previous': True},
                  {'pitch': 'C4'}, {'pitch': None}] + [{'pitch': 'D4'}] * 6
        plan, audit = sequence.convert({'events': events}, rests_as_blanks=False)
        self.assertEqual(len(plan['notes'].split()), 8)
        self.assertEqual(plan['notes'].split()[:2], ['C1', 'C1'])
        self.assertEqual(audit['alignment'][1]['tooth'], 1)
        plan, _ = sequence.convert({'events': events}, rests_as_blanks=True)
        self.assertEqual(plan['notes'].split()[2], '·')

    def test_rests_are_kept_by_default(self):
        events = [{'pitch': 'C4'}] * 4 + [{'pitch': None}] + [{'pitch': 'D4'}] * 4
        plan, audit = sequence.convert({'events': events})
        self.assertEqual(plan['notes'], 'C1 C1 C1 C1 · D1 D1 D1 D1')
        self.assertEqual(audit['alignment'][4]['tooth'], 5)

    def test_invalid_tie_range_and_count(self):
        cases = [
            [{'pitch': 'C4', 'tie_to_previous': True}] * 8,
            [{'pitch': 'C4'}, {'pitch': None}, {'pitch': 'C4', 'tie_to_previous': True}] * 3,
            [{'pitch': 'C4'}, {'pitch': 'D4', 'tie_to_previous': True}] * 4,
            [{'pitch': 'D5'}] * 8,
            [{'pitch': 'C4'}] * 7,
            [{'pitch': 'C4'}] * 34,
        ]
        for events in cases:
            with self.subTest(events=events), self.assertRaises(ValueError):
                sequence.convert({'events': events})
