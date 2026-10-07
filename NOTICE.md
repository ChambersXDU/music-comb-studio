# Scope of the software license

The MIT license in `LICENSE` applies to the newly written application code,
scripts, skill instructions, documentation and tests in this repository.

`assets/*.npz` contains reference and derived geometry reconstructed from an
owner-supplied `notext.stl`. Its reported source is Musical Fidget Generator v4
on MakerWorld, design ID 1492688. The reference geometry's origin, file hash and
measurements are recorded in `evidence/provenance.json`. The upstream geometry
license was not independently verified, and the MIT license does not relicense
those assets or confer additional rights to their geometry in generated models.
Retain the applicable upstream authorization when redistributing those assets.

Three.js is distributed under its own MIT license, retained at
`web/vendor/three/LICENSE`. Python dependencies retain their respective licenses.

The repository does not include copyrighted score scans or full song lyrics.
Score-to-sequence skills should keep source links and a record of the requested
excerpt rather than redistribute an entire score.
