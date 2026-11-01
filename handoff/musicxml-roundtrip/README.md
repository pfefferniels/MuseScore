# Handoff: MusicXML round trip

Material for fixing MuseScore MusicXML import/export defects found with Niels Pfeffer's encoding of the BA 5037
parts of Bach's St John Passion. The task is in `PROMPT.md`.

- `repro/`: minimal MusicXML 4.0 files, all valid against `src/importexport/musicxml/schema/musicxml.xsd`.
  `tools/make_repros.py` generates 01 to 08 and 04b, 05b. `05c` is `05b` with `new-page` and the `<defaults>` of
  the flute I part. `09` is five bars of the flute I part cut with `tools/excerpt.py` (lyrics, credits and
  identification removed, `<defaults>` reduced to scaling and page layout).
- `baseline-4.7.4/`: output of `tools/run_roundtrip.py` with the MuseScore 4.7.4 release build (macOS):
  re-exported MusicXML, PNG renderings and checker reports.
- `tools/roundtrip_check.py`: semantic comparison of a file with its round trip, per category.
- `tools/run_roundtrip.py`: runs the round trip, the rendering and the check over a set of files.
- The full parts are not here. They are in the private repository `pfefferniels/jopa` (`nba-parts/`, commit
  `5f84b0a`) and must not be published.
