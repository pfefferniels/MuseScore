# MusicXML round trip: report

Work done in a Claude Code cloud session on 1 and 2 November 2026, following `PROMPT.md`. All commits are on the
branch `claude/musicxml-roundtrip-handoff-lem5pj` of `pfefferniels/MuseScore` (see "Deviations from the brief"). The
fix commits touch only `src/` and `fonts/` and can be cherry-picked without the `handoff/` commits.

## Summary

| # | Defect | Status | Commits |
|---|---|---|---|
| 1 | Printed courtesy accidentals dropped at import | fixed | `91cb6879`, `0e8d165a` |
| 2 | Redundant accidentals exported as `cautionary="yes" parentheses="no"` | fixed (behaviour change, see below) | `6f6f33c9` |
| 3 | Melisma end markers lost on export | fixed for single and end syllables | `0f041017` |
| 4 | Cue size lost on export (notes, clefs) | fixed; clefs by a heuristic | `3b27395c`, `68e4e8db`, `69814b49` |
| 5 | `staff-size`/`staff-type` without effect, not exported | fixed, except repro 08 | `712ea6cf`, `b97579b2` |
| 6 | Cue clef at a page start drawn as header clef | not reproduced, no change | none |
| 7 | Tie stop without start | fixed (needs a small engraving change) | `d364e083` |
| 8 | Slashed figured-bass digits shown as "?" | fixed | `42f1ced6` |
| 9 | Printed vertical layout ignored | fixed: all 12 parts have the printed systems and page count | `3f4ac40e`, `c20c6b6f` |
| 10 | Exit crash after conversion | not reproduced on Linux | none |
| – | Converter crashed on every MusicXML export on this branch | fixed (prerequisite) | `f75a44e9` |

`musicxml_tests`: 364 tests before, 383 after, all passing at every commit. `engraving_tests` (900 tests) also pass
after the engraving change in `d364e083`.

## Build and environment

- Linux (Ubuntu 24.04, 4 cores), gcc 14, Qt 6.11.2 installed with aqtinstall (the CI version), Release build with
  `MUSE_ENABLE_UNIT_TESTS=ON`, targets `mscore`, `iex_musicxml_tests` and `engraving_tests`.
- The KDDockWidgets source tarball from the `muse_deps` release has a different SHA-256 than the manifest
  (`4f785d16…` instead of `df1d9fa9…`) and contains an older commit (27aa539). The GitHub archive fallback was blocked
  by the network proxy. I created the tarball with `git archive` from a clone at the pinned commit 662d74a and put it
  into the download cache. Upstream's manifest or release asset seems to be out of step.
- On Linux `mscore` forces the `xcb` platform unless `MU_QT_QPA_PLATFORM` is set (`src/app/main.cpp:108`).
  `run_roundtrip.py` therefore needs `MU_QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORM=offscreen` in its environment.
- **Converter crash (commit `f75a44e9`).** On this branch, `mscore -o out.musicxml in.musicxml` crashed with SIGSEGV in
  `Part::midiPort()` called from `partList()` in the exporter. Only the mscx readers fill the MIDI mapping
  (`read500.cpp:314`), imported scores never get one, and the MusicXML exporter reads it. The fix calls
  `rebuildMidiMapping()` after a reader has imported a score in `NotationProject::doImport`. Without it no round trip
  could be measured. This is a regression on upstream `main`, not in 4.7.4, so it could be proposed upstream as is.
- Code style: `tools/codestyle/tidy_file.sh` was run on every changed C++ file with uncrustify 0.78.1 from Ubuntu.
  That version warns about four options in `uncrustify_muse.cfg`, so it is not the version upstream uses. It
  reformatted one unrelated line in `compatmidirenderinternal.cpp`, which I reverted.
- "Baseline" below means this branch plus `f75a44e9` (built from `da93279b`), because the branch without that fix
  cannot export MusicXML at all.

## Full parts

`pfefferniels/jopa` was available in the session at commit `5f84b0a`. Nothing from it was copied into this
repository. The outputs stayed in the session's scratch directory.

### Pages

`mscore -o <part>.pdf <part>.musicxml`, counted with `pdfinfo`. "Printed" and "4.7.4" are from `PROMPT.md`.

| part | printed | 4.7.4 (macOS) | baseline | spacers only (`3f4ac40e`) | final |
|---|---|---|---|---|---|
| bc | 53 | 55 | 55 | 53 | 53 |
| fl1 | 22 | 22 | 22 | 22 | 22 |
| fl2 | 20 | 20 | 20 | 20 | 20 |
| gamba | 6 | 7 | 6 | 6 | 6 |
| liuto | 2 | 2 | 2 | 2 | 2 |
| ob1 | 20 | 21 | 21 | 20 | 20 |
| ob2 | 18 | 20 | 20 | 19 | 18 |
| va | 22 | 28 | 29 | 25 | 22 |
| vadam1 | 4 | 4 | 4 | 4 | 4 |
| vadam2 | 4 | 5 | 5 | 4 | 4 |
| vn1 | 28 | 29 | 29 | 30 | 28 |
| vn2 | 23 | 26 | 26 | 26 | 23 |

All conversions exited with code 0.

### Checker, lost/gained per category

`run_roundtrip.py --no-render` over the 12 parts. Cells are lost/gained, empty where the category does not occur in
the part. Dynamics are 0/0 in both runs and left out. Tied is left out of the final table because it is 0/0 in every
part (the lone tie stops of defect 7), and break because it is 0/0 in every part (every printed system and page
break comes back).

Baseline:

| part | accidental | barline | break | clef | key | lyric | note | staff-details | tied | transpose | words |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bc | 265/245 | 21/1 | 2/7 | 8/6 | 2/2 | 94/31 | 20/21 | 68/449 | 3/0 |  | 5/5 |
| fl1 | 80/78 | 0/1 | 0/1 | 28/17 | 1/0 | 42/10 | 550/551 |  | 0/0 |  | 8/5 |
| fl2 | 72/71 | 0/1 | 0/2 | 26/15 | 1/0 | 34/7 | 555/558 |  | 0/0 |  | 8/5 |
| gamba | 43/40 | 2/2 | 0/1 | 2/0 | 0/0 | 229/46 | 45/45 | 7/30 | 0/0 |  | 3/3 |
| liuto | 13/11 | 2/0 | 0/1 | 1/0 | 0/0 | 12/6 | 18/116 | 3/0 | 0/0 |  | 2/2 |
| ob1 | 82/78 | 2/2 | 1/1 | 25/15 | 3/3 | 6/3 | 558/560 | 6/36 | 1/0 | 2/1 | 11/7 |
| ob2 | 105/102 | 4/3 | 2/7 | 30/16 | 3/4 | 4/2 | 547/550 | 10/0 | 1/0 | 2/1 | 11/7 |
| va | 89/89 | 0/2 | 6/14 | 42/25 | 2/0 | 0/0 | 644/644 |  | 2/0 |  | 6/4 |
| vadam1 | 32/27 | 1/0 | 0/1 | 1/0 | 0/0 | 120/42 | 18/17 | 2/0 | 0/0 |  | 1/1 |
| vadam2 | 39/35 | 1/0 | 1/2 | 2/1 | 0/0 | 116/40 | 18/17 | 2/0 | 0/0 |  | 1/1 |
| vn1 | 114/108 | 1/1 | 1/12 | 36/22 | 1/0 | 92/34 | 638/638 | 3/0 | 0/0 |  | 8/6 |
| vn2 | 129/123 | 1/2 | 3/13 | 33/18 | 2/0 | 60/20 | 517/517 | 5/0 | 1/0 |  | 10/7 |

Final:

| part | accidental | barline | clef | key | lyric | note | staff-details | transpose | words |
|---|---|---|---|---|---|---|---|---|---|
| bc | 0/1 | 21/1 | 8/6 | 2/2 | 4/5 | 8/9 | 0/0 |  | 5/5 |
| fl1 | 0/0 | 0/1 | 19/8 | 1/0 | 30/9 | 2/3 |  |  | 8/5 |
| fl2 | 0/0 | 0/1 | 18/7 | 1/0 | 28/5 | 2/5 |  |  | 8/5 |
| gamba | 0/0 | 2/2 | 2/0 | 0/0 | 0/0 | 2/2 | 1/1 |  | 3/3 |
| liuto | 0/0 | 2/0 | 1/0 | 0/0 | 0/0 | 0/99 | 0/0 |  | 2/2 |
| ob1 | 0/1 | 2/2 | 18/8 | 3/3 | 2/1 | 6/8 | 0/0 | 2/1 | 11/7 |
| ob2 | 0/1 | 4/3 | 24/10 | 3/4 | 2/1 | 5/8 | 0/0 | 2/1 | 11/7 |
| va | 0/2 | 0/2 | 29/12 | 2/0 | 0/0 | 5/5 |  |  | 6/4 |
| vadam1 | 0/0 | 1/0 | 1/0 | 0/0 | 27/2 | 0/0 | 0/2 |  | 1/1 |
| vadam2 | 0/0 | 1/0 | 2/1 | 0/0 | 27/2 | 0/0 | 0/2 |  | 1/1 |
| vn1 | 0/0 | 1/1 | 26/12 | 1/0 | 0/0 | 4/4 | 0/4 |  | 8/6 |
| vn2 | 0/0 | 1/2 | 27/12 | 2/0 | 0/0 | 1/1 | 0/0 |  | 10/7 |

For gamba, the brief's 4.7.4 numbers were accidental 43/40, lyric 229/46, note 45/45, staff-details 8/31, break 1/2,
words 3/4, barline 2/2. The baseline here matches them closely. The final gamba differences are listed under the
defects below.

## Repros

`run_roundtrip.py` over `repro/*.musicxml`, lost/gained per category.

| repro | baseline | final |
|---|---|---|
| 01-lyric-extend | lyric 8/3 | equal |
| 02-staff-size-cue | note 5/5, staff-details 1/0 | equal |
| 03-accidentals | accidental 5/2 | equal |
| 04-clef-in-multirest | clef 1/1, note 4/4 | clef 1/1 |
| 04b-clef-in-multirest-range | clef 1/1, note 4/4 | clef 1/1 |
| 05-cue-clef-after-barline | clef 1/1, note 3/3 | equal |
| 05b-cue-clef-system-start | clef 1/1, note 3/3 | equal |
| 05c-cue-clef-page-break-defaults | clef 1/1, note 3/3 | equal |
| 06-lone-tie-stop | note 1/1, tied 1/0 | equal |
| 07-figured-bass-slash | equal | equal |
| 08-direction-hidden-staff | staff-details 1/0 | staff-details 1/0 |
| 09-cue-clef-page-break-excerpt | clef 1/1, note 25/25 | equal |
| 10-tuplet-hidden-number-bracket | equal | equal |
| 11-notehead-parentheses | equal | equal |
| 12-alter-without-accidental | accidental 0/1 | accidental 0/1 |
| 13-per-staff-transpose | key 1/0, transpose 2/1 | key 1/0, transpose 2/1 |
| 14-words-hidden-staff-mmrest | (added at the end) | equal, but the words on staff 1 are not drawn |

04/04b are explained under "Other problems found", 08 under defect 5, and 10 to 13 under "Untested items". I looked at
the PNGs of 01, 03, 04 and 09 from the final build, of 02, 06 and 07 from the build of the commit that fixed them,
and of 13 from the baseline. Repros 10 to 13 are new (commit `ea9417c3`).

## Defects

### 1. Printed courtesy accidentals dropped at import: fixed

Cause, as described in the brief, plus two more cases found in the parts:

- `markUserAccidentals()` used one key-based state for all staves of the part, never updated it within the measure,
  and did not visit grace notes.
- Notes sounding at the same moment in different voices: layout gives the accidental to the first voice, so a file
  that prints it on the second voice would get two accidentals if the second one were marked USER.
- Notes tied across the barline: layout always removes an AUTO accidental from a note tied from the same pitch
  (`Chord::cmdUpdateNotes`), so an accidental printed again after the barline was lost. This was the cause of most of
  the remaining bc accidental losses and is fixed in the follow-up commit `0e8d165a`.

Fix: the function now follows the accidental state per staff, in the order layout uses (key signature changes, grace
notes before, the chords of a segment, grace notes after), updates the state after each note, judges the notes of
one moment against the state before that moment, and marks as USER every printed accidental that layout would not
generate itself. Accidentals that layout would generate stay AUTO, so editing and transposing behave as before.

Tests: `courtesyAccidentals` (import, `testCourtesyAccidentals_ref.mscx`), plus `courtesyAccidentalsExport` and
`courtesyAccidentalsRoundTrip` added with defect 2. The test file is repro 03 plus a voice unison bar and a tie across
the barline.

Checker: repro 03 accidental 5/2 → equal. Parts: no accidental is lost any more in any part (gamba 43/40 → 0/0, bc 265/245 → 0/1). Five accidentals are gained in all parts together (bc, ob1, ob2, va): places where MuseScore draws an accidental that the print omits.

Unsure: in the voice-unison case the accidental is drawn and exported on the first voice although the file prints it
on the second. The checker counts per staff, so it does not show this.

### 2. Plain redundant accidentals exported as cautionary: fixed

`writeAccidental()` now writes an unbracketed USER accidental as a plain `<accidental>`. Bracketed and parenthesised
accidentals are unchanged. With defect 1 fixed, re-import marks it USER again, so the round trip is stable
(`courtesyAccidentalsRoundTrip`).

**Upstream may not want this.** A file that uses `cautionary="yes" parentheses="no"` now loses these attributes on a
round trip (`testAccidentals3`, whose input keeps them; the test now compares with a new `testAccidentals3_ref.xml`).
The old output claimed a cautionary accidental that MuseScore does not show as one.

### 3. Melisma end markers lost on export: fixed for single and end syllables

`ExportMusicXml::lyrics()` writes `<extend type="start"/>` and records the end tick of the melisma per track and
verse. A new `melismaExtends()` writes `<lyric number="n"><extend type="continue"/></lyric>` on the following chords
of the same track and `type="stop"` on the chord at the end tick. I checked that the re-import of the new output gives
the same melismas: the `.mscx` of repro 01 imported directly and of its re-exported MusicXML have identical lyric
`ticks_f`.

Tests: `lyricExtensionStartContinueStop` (repro 01) and `lyricExtensionStartContinueStopRoundTrip`. Changed:
`testExtendedLyrics_ref.xml`, `testLyrics1_ref.xml`; `lyricExtension1`/`lyricExtension3` were round-trip tests on
files with bare `<extend/>`. I kept those inputs, which still test the import of the old form, and added
`testLyricExtensions_ref.xml` and `testLyricExtension2_ref.xml`.

Checker: repro 01 lyric 8/3 → equal; gamba lyric 229/46 → 0/0.

Not fixed: the remaining lyric differences (for example fl1, fl2, vadam1, vadam2 in the final table) are `extend` on
syllables with `syllabic` begin or middle. The importer only accepts an extend on single or end syllables
(`MusicXmlParserLyric::parse`), because MuseScore models a melisma on a hyphenated syllable through the hyphen: giving
such a syllable `ticks` would draw an underscore instead of dashes (`Lyrics::isMelisma`, `isEndMelisma`). Writing
start/continue/stop for implicit hyphen melismas on export would be possible but is a different change. Also, the
importer ignores `extend type="stop"`: a melisma always runs to the last note before the next syllable or rest. In
the parts this differs only once (bc, one note without lyric after a stop).

### 4. Cue size lost on export: fixed, clefs by heuristic

Notes (`3b27395c`): `writeType()` now writes `size="cue"` for every small note and `size="grace-cue"` for a small grace
note. The brief's reading of `<cue>` is incomplete: the schema's documentation of `note-type` (`musicxml.xsd`, around
line 5240) says the default size is cue for notes with `<cue>` and grace-cue for notes with both `<grace>` and
`<cue>`. The old output was therefore valid; the new one is explicit and redundant, and readers that take the size
only from `<type size>` (and the checker) now see it.

Rests (`68e4e8db`): `<cue/>` on a rest was ignored at import (unlike notes) and never written at export. Import now
makes such a rest small, and export writes `<cue/>` for a small rest, on the grounds that a rest does not play anyway.
A small rest that was not meant as a cue rest now also gets `<cue/>`.

Clefs (`69814b49`): import never reads `size` on `<clef>`, and there is nothing to store it in: `Clef::isSmall()` is
set by layout (every clef change is drawn small, every header clef full size) and is not saved. Export now writes
`size="cue"` on a clef after the barline when small chords or rests follow it on its staff before the next clef in the
measure. In the parts, all 60 `size="cue"` clefs are after-barline clefs before cue notes, and the two plain
after-barline clefs are not followed by cue notes (counted by a research subagent on the input files). **This is a
heuristic and upstream may prefer a saved clef property**, which would mean a new `Pid`, reading and writing it in
mscx, and setting it at import. In the final run of the parts, 59 of the 60 printed cue clefs come back with
`size="cue"`; in addition, 21 clefs that the end-of-bar problem (see "Other problems found") moves after the barline
in front of cue notes get `size="cue"` although the print has a plain clef there.

Tests: `cueNotes` (now a reference test, new `testCueNotes_ref.xml`, input kept without `size`), `cueRests`, `cueClef`,
`cueClefRoundTrip`; changed `testCueGraceNotes_ref.xml`, `testCueNotes2_ref.xml`.

Checker: repros 05, 05b, 05c, 09 → equal; gamba note 45/45 → 2/2.

Remaining in gamba: two grace cue notes that the parts encode as `<grace/><cue/><type size="cue">` come back as
`size="grace-cue"`. Under the schema (`note-size-type`), `size="cue"` on a grace note means grace size, not reduced
grace size, while MuseScore draws such notes at grace-cue size. If reduced cue grace notes are meant, `grace-cue` is
the matching value in the encoding (8 notes in the parts).

### 5. `staff-size` and `staff-type`: fixed, except repro 08

Cause: `staffDetails()` set `MAG` 1.0 and `LINE_DISTANCE` 0.75 for `<staff-size>75</staff-size>` without `scaling`. In
4.7.4, `Staff::setProperty` had no case for `LINE_DISTANCE`, so the value was dropped and the staff drawn at full size
(checked by a subagent against a v4.7.4 checkout). On this branch the line distance is applied, which gives full-size
notation on closer lines, also wrong. `<staff-type>` was not read. Export only opened `<staff-details>` for mag,
lines, TAB, hidden or line details, so neither a line distance nor a small staff was written.

How I read the spec (`staff-size` in `musicxml.xsd`): both the staff-size value and the `scaling` attribute are
percentages of the work's default scaling; `scaling` is the notation scale. Without `scaling` the spec leaves it open.
I chose: with `staff-type` cue, ossia or editorial, or with a staff-size below 100, the notation scales with the staff
(mag = size/100, line distance 1); a size of 100 or more without `scaling` only spaces the lines (as for tablature,
which MuseScore exports as `<staff-size>150</staff-size>`). The "below 100 without staff-type" rule is needed for the
gamba part's staff 3, which has `<staff-size>75</staff-size>` without a type. **Please confirm that this matches your
intention.**

Fix (`712ea6cf`): cue, ossia and editorial staves become small staves (`Pid::SMALL`), and the size is set through the
staff's user mag divided by `smallStaffMag`, so a 75% cue staff becomes "small staff" with scale 107% in the staff
properties. Export writes `<staff-type>cue</staff-type>` for a small staff and the staff-size with `scaling`. Ossia and
editorial come back as cue.

`b97579b2`: the first staff of a part was never reported hidden, so the cue staff hidden in the first system lost its
`print-object="no"`. Later systems repeated `print-object="no"` for every hidden staff and never wrote
`print-object="yes"`, although the value holds until changed. Hidden staves are now determined at every system start
and `print-object` is written only where a staff is hidden or shown again. Gamba staff-details 7/30 → 1/1.

Tests: `staffSizeCue1` (checks small, mag and line distance), `staffSizeCue2`, `staffSizeCue3`, `hiddenCueStaff`,
`hiddenCueStaffRoundTrip`.

Not fixed: repro 08. The staff with `print-object="no"` carries a words direction, so `Measure::isEmpty` is false and
MuseScore shows the staff, as the brief accepts. Export then has no reason to write `print-object="no"`. Exporting it
anyway would contradict what MuseScore draws; I left it. Remaining staff-details differences in the parts (for example
vn1 0/4, vadam1/2 0/2) are systems in which MuseScore hides an empty cue staff that the print shows, or the reverse;
MuseScore decides visibility by emptiness.

### 6. Cue clef at a page start becomes the header clef: not reproduced

Both the 4.7.4 baseline PNGs (`baseline-4.7.4/05c-…-2.png`, `09-…-2.png`) and this branch draw a plain G2 header clef,
then the key and time signature, then the small G8vb clef, which is the expected result. I looked at the 09 pages of
both. A subagent also checked the full flute I part (4.7.4 PDF and this branch) and bisected the `<defaults>` and
`<print>` variants of 05c without finding a wrong header clef, and the model has the cue clef in the measure's own
clef segment in 05b and 05c alike. My guess is that the previous session misread the small thumbnails. If you saw the
wrong clef in the desktop app, a screenshot and the steps would help. No change, no test.

### 7. Tie stop without start: fixed

Import (`d364e083`): a lone `<tie type="stop"/>`/`<tied type="stop"/>` is kept in `m_unstartedTieNotes` and was
discarded at the end of the part. It now becomes an incoming `PartialTie` on the note. Export writes
`<tie type="stop"/>` for it (`<tied type="stop"/>` was already written for incoming partial ties).

This was not enough on its own, which I verified: an incoming partial tie has a start note only through a jump point,
and `Score::undoRemoveStaleTieJumpPoints` deletes incoming ties without one on every mscx load (with the flag removed
from a saved `.mscx`, the tie is gone after reloading). Playback and MIDI also silenced a note whose tie has no start.
So the commit adds a flag `PartialTie::isStandalone`, saved as `<isStandalone>1</isStandalone>` inside the
`<PartialTie>` in mscx (a file format addition), skipped by the stale-tie cleanup, and treated as "the note sounds" in
`NoteRenderer` and the MIDI renderer. I checked that the MIDI export of repro 06 still contains the A4.

Tests: `tieStopWithoutStart` (round trip), `tieStopWithoutStartKept` (runs the cleanup and checks the tie is kept).
Changed: `importTie1_ref.mscx`, `testBackupRoundingError_ref.mscx`, `testUnterminatedTies_ref.mscx`. All three have tie
stops that the importer cannot match; in `testUnterminatedTies` the bar-9 stop has a start seven bars earlier that the
importer does not connect, and it is now drawn as an incoming tie. Checker: repro 06 → equal.

Upstream will look closely at this one, since it touches engraving, the file format and playback.

### 8. Slashed figured-bass digits: fixed

`fonts/fonts_figuredbass.xml` had `?` for the slashed form of every digit except 5 in both styles (18 entries), and
MScoreBC has no `?` glyph either. Leland has none of the SMuFL figured-bass glyphs and SMuFL has no forward-slashed 6,
so I drew the digit with an overlaid slash at font level: nine composite glyphs U+E216 to U+E21E (slashed 0–4 and
6–9), each the font's own `slash` glyph at x −14 over the digit, exactly like the existing slashed 5 (U+E210). Files:
`fonts_figuredbass.xml`, `mscore-BC.sfd`, and `mscore-BC.ttf` (patched with fontTools; only the nine glyphs and the
tables they need change). The commit message credits the font (Maurizio M. Gavioli, SIL OFL 1.1).

Test: `figuredBassSlashedDigits` imports 1/ to 9/ and checks that the displayed character is not `?`, not the plain
digit, and in the font. It fails without the font change and passes with it (checked). The rendering of repro 07 shows
the slashed 6 and 4.

**Licence question:** the font declares "Reserved Font Name MScoreBC". Under OFL 1.1 a modified version may not use the
reserved name without permission. MuseScore keeps the `.sfd` in its tree as a community-maintained font and has
modified it before (2018), but the point should be raised if this goes upstream. The 12 parts contain no figured bass,
so this affects only the repro.

### 9. Printed vertical layout: fixed for the distances

Design note (written before the implementation, from a research subagent's analysis and my own reading of
`systemlayout.cpp` and `pagelayout.cpp`):

- MuseScore keeps at least `minSystemSpread` (8.5 sp, vertical spread is on by default) between systems and
  `staffLowerBorder` (7 sp) below the last system, and places the first system `staffUpperBorder` (7 sp) below the top
  margin. Many printed system distances are smaller: va 100 of 225, vn2 145 of 233, ob2 116 of 176 are below 8.5 sp.
  A simple model with these minimums predicts exactly the extra pages of the single-staff parts in 4.7.4.
- A FIXED spacer under the last visible staff of a system sets the distance to the next system exactly, skips the
  collision check, and also removes the 7 sp lower border from the page fit check. A FIXED spacer under a staff sets
  the distance to the next visible staff in that system. An UP spacer on staff 0 can push the first system of a page
  down. Spacers on measures inside a multimeasure rest are dropped.
- Options considered: fixed spacers per system (chosen: exact, no engraving change, export then writes the same
  numbers back); global styles from the smallest printed values (fit not guaranteed, not per system); page locks
  (squeeze path unverified, conflicts with imported breaks); up/down spacers (minimums only, cannot reduce a gap).
- Gating: only when both "import layout" and "import breaks" are on, because the distances belong to the printed
  systems.

Implementation (`3f4ac40e`): pass 2 now reads `system-distance` and `top-system-distance` (first part) and
`staff-distance` (all parts) from `<print>`, and records `print-object` changes from `staff-details`. After all parts:
for each printed system, the printed staves are those whose `print-object` state is "yes" and which are shown; a
`staff-distance` becomes a FIXED spacer under the printed staff above, a `system-distance` a FIXED spacer under the last
printed staff of the previous system, and a `top-system-distance` (larger than `staffUpperBorder`, and only where no
frame precedes the system, so in practice from page 2 on) an UP spacer on staff 0. Spacers go into the last measure
of the system that has notes (and staff distances also into the first one), so that multimeasure rests do not drop
them and a printed system that MuseScore has to wrap keeps its distances at both ends. `system-margins` and
`page-layout` in `<print>` are still ignored.

Tests: `systemDistances` (`testSystemDistances_ref.mscx` pins the spacers) and `systemDistancesLayout` (a synthetic
two-page file whose printed distances fit only if they are applied: two pages, every system distance 4 sp, page 2
starting 10 sp below the margin; the baseline needs four pages for it). 33 import references gain spacers, listed
below. `systemDividers` was a round-trip test with layout export; the exported staff distances now come from the
file and drift by 0.01 tenths per round trip (57.53 → 57.54 → 57.53), presumably through the rounded `<millimeters>`
in `<scaling>`. It is now a reference test with layout export (`testSystemDividers_ref.xml`; `musicXmlIoTestRef` got
the same optional `exportLayout` parameter as `musicXmlIoTest`).

With the spacers alone, nine parts had the printed page count, but va had 25 pages (printed 22), vn1 30 (28), vn2 26
(23) and ob2 19 (18). Exported with "all breaks", MuseScore had as many systems as the print in the other parts, but
8 more in va, 11 in vn1, 9 in vn2 and 5 in ob2: its horizontal spacing is wider than the engraver's, so it could not
fit some printed systems on one line and wrapped them, and each extra system cost vertical space the printed page
does not have.

Second commit (`c20c6b6f`), added after your request to preserve the page count: when layout and breaks are imported
and the encoding declares `<supports element="print" attribute="new-system" type="yes"/>` (that is, that it gives
every system break), the measures of each printed system are locked into one system with MuseScore's system locks
(`Score::addSystemLock`, the "keep measures on the same system" feature). Layout then never breaks a locked system
and squeezes it to fit (`HorizontalSpacing::squeezeSystemToFit`: first less padding and stretch, collisions only as
a last resort). The declaration is the gate because without it a `new-system` may stand for several systems (for
example in MuseScore's own export with "manual breaks"). All 12 parts declare it. MuseScore keeps the locks when it
creates multimeasure rests (`EditSystemLocks::updateSystemLocksOnCreateMMRests`), and they are saved in `.mscx`.

Result, with both commits: every part has the printed page count, and the system and page starts are identical to the
print in all 12 parts (2153 systems; checked by exporting with "all breaks" and comparing every `new-system` and
`new-page` with the input). The squeezed systems are dense but legible; I looked at the formerly wrapped systems on
vn1 page 3 and va page 7. The layout also survives a MusicXML round trip: MuseScore's default export ("all breaks"
with layout) declares the breaks complete and writes the distances, and converting that export back to PDF gives
22 pages for va and 28 for vn1 again.

Test for the locks: `systemLocks` (a file with two printed systems of twelve dense bars: with the declaration
MuseScore keeps two systems, without it, it wraps them). 24 import references gain a `<SystemLocks>` block and nothing
else (checked by diffing): `importTie2_ref.mscx`, `importTie3_ref.mscx`, `importTie4_ref.mscx`,
`testArpCrossVoice_ref.mscx`, `testChordSymbols2_ref.mscx`, `testCodaHBox_ref.mscx`, `testDoletOttavas_ref.mscx`,
`testFinaleDynamics_ref.mscx`, `testFinaleSystemObjects_ref.mscx`, `testImportDrums2_ref.mscx`,
`testInferCodaII_ref.mscx`, `testInferSegnoII_ref.mscx`, `testInferredCrescLines_ref.mscx`,
`testInferredCrescLines2_ref.mscx`, `testInferredDynamicsExpression_ref.mscx`, `testInferredTempoText_ref.mscx`,
`testMS3KitAndPerc_ref.mscx`, `testMeasureStyleSlash_ref.mscx`, `testNamedNoteheads_ref.mscx`,
`testPlacementOffsetDefaults_ref.mscx`, `testSibMetronomeMarks_ref.mscx`, `testSibOttavas_ref.mscx`,
`testSibRitLine_ref.mscx`, `testSticking_ref.mscx`.

Not done: page locks. MuseScore also has page locks, which would keep the printed pages even if their systems did not
fit vertically. With the spacers and system locks no page overflows in the 12 parts, so I left them out; they would be
the next step if another file still overflows.

Risks: fixed distances skip collision checks, so lyrics or dynamics that MuseScore draws larger than the print can
collide (I looked at gamba page 3 and saw none). The change applies to every MusicXML file with `<print>` distances
while "import layout" is on (the default), including Finale, Sibelius and Dorico exports, which is why so many
references change. If upstream objects, the same code can move behind its own preference.

Data finding (from the research, not verified by me): in bc (22 systems) and ob2 (23 systems), `staff-layout
number="2"` is given in systems where staff 1 is not printed; the values look like the distance between staves 2 and
3. Under the spec they apply to staff 2, which is the first printed staff, and are ignored. Worth checking in
`compile.py`.

### 10. Exit crash: not reproduced on Linux

96 conversions of the repros (16 files, 3 rounds, MusicXML and PDF) and all conversions of the full parts with the
final build exited with code 0, without `mutex lock failed` or similar messages. I did not look further.

## Updated reference files

Changed reference files, with the commit that changed them:

- `91cb6879` (accidentals): `testBackupRoundingError_ref.mscx`, `testInferCodaII_ref.mscx`,
  `testInferSegnoII_ref.mscx` (printed reminder accidentals now kept), `testCueGraceNotes_ref.mscx`,
  `testCueGraceNotes_ref.xml` (a natural after a grace B♭ is now a normal, needed accidental instead of USER).
- `6f6f33c9`: `testIncompleteTuplet_ref.xml`; new `testAccidentals3_ref.xml` (test changed from round trip to
  reference).
- `0f041017`: `testExtendedLyrics_ref.xml`, `testLyrics1_ref.xml`; new `testLyricExtensions_ref.xml`,
  `testLyricExtension2_ref.xml` (tests changed from round trip to reference).
- `3b27395c`: `testCueGraceNotes_ref.xml`, `testCueNotes2_ref.xml`; new `testCueNotes_ref.xml` (test changed from
  round trip to reference).
- `68e4e8db`: `testCueNotes_ref.xml`, `testCueNotes2_ref.xml`.
- `d364e083`: `importTie1_ref.mscx`, `testBackupRoundingError_ref.mscx`, `testUnterminatedTies_ref.mscx`.
- `3f4ac40e` (spacers only, checked by diffing every file for changes other than spacers and element ids):
  `importTie3_ref.mscx`, `importTie4_ref.mscx`, `testArpCrossVoice_ref.mscx`, `testArpOnRest_ref.mscx`,
  `testBackupRoundingError_ref.mscx`, `testBuzzRoll_ref.mscx`, `testChordSymbols2_ref.mscx`, `testCodaHBox_ref.mscx`,
  `testDoletOttavas_ref.mscx`, `testDuplicateFermataOnGraceNoteAndMainNote_ref.mscx`,
  `testDuplicateFermataOnGraceNote_ref.mscx`, `testDuplicateInstrChange_ref.mscx`, `testFinaleSystemObjects_ref.mscx`,
  `testInferCodaII_ref.mscx`, `testInferSegnoII_ref.mscx`, `testInferredCrescLines2_ref.mscx`,
  `testInferredCrescLines_ref.mscx`, `testInferredFingerings_ref.mscx`, `testInferredTempoText2_ref.mscx`,
  `testMS3KitAndPerc_ref.mscx`, `testMeasureStyleSlash_ref.mscx`, `testNegativeOffset_ref.mscx`,
  `testPartNames_ref.mscx`, `testPlacementDefaults_ref.mscx`, `testPlacementOffsetDefaults_ref.mscx`,
  `testSibMetronomeMarks_ref.mscx`, `testSibOttavas_ref.mscx`, `testSibRitLine_ref.mscx`, `testStaffEmptiness_ref.mscx`,
  `testSystemObjectStaves_ref.mscx`, `testTempoTextSpace1_ref.mscx`, `testTempoTextSpace2_ref.mscx`,
  `testVoltaHiding_ref.mscx`; new `testSystemDividers_ref.xml` (test changed from round trip to reference).
- `0e8d165a`: `testCourtesyAccidentals*` (test file extended).
- `c20c6b6f` (system locks only): the 24 files listed under defect 9.

No input file of an existing test was changed.

## Untested items

Repros 10 to 13 (`repro/`, generated by `tools/make_repros.py`, XSD-valid).

- `<tuplet show-number="none" bracket="no">` (10): kept. The checker does not compare it; I checked the exported
  `<tuplet>` element.
- `<notehead parentheses="yes">` (11): kept, checked in the output.
- `<alter>` without `<accidental>` (12): MuseScore draws the accidental where the key requires one (F♯ in C major) and
  none where it does not (F♯ in G major), and writes the drawn one as `<accidental>` on export, which the checker
  counts as gained. MusicXML leaves the display of a missing `<accidental>` to the reader, so I do not consider this a
  defect.
- Per-staff `<transpose number="n">` (13): MuseScore has one transposition per part (instrument). Import takes one of
  the two, export writes it for the whole part, and the key of staff 2 (`<key number="2">`) is not exported. The notes
  are drawn as written, but a re-import transposes staff 2 like staff 1. This is a limitation of MuseScore's model; I
  did not change it. ob1 and ob2 show it as transpose 2/1 in the tables.

## Lower priority items

- Credits on page 2 and later: not worked on.
- The two defects seen with MuseScore 4.5, recreated by a subagent in scratch copies of the parts with the final
  build:
  - **Clef after the last rest of a multirest: does not reproduce.** In copies of vadam2 (treble-8 clef moved from
    bar 28 to after the rest of bar 27, the end of the 4-bar multirest 24–27) and ob1 (treble clef moved from bar 62 to
    after the rest of bar 61), the following cue is drawn in the new clef with correct pitches. The moved clef is drawn
    after the barline, which is the end-of-bar clef problem below.
  - **Words on a hidden staff 1: reproduces, but only when the direction is in the first bar of a collapsed
    multirest.** In copies of gamba ("19. Arioso", start of a 14-bar multirest) and liuto ("18c. Evangelista", start
    of a 4-bar multirest) the text is missing from the PDF, while the `.mscx` still has the staff text. Outside a
    multirest the text keeps the hidden staff visible, so the text is drawn, but the whole staff 1 is shown in that
    system. Cause: the import maps `print-object="no"` to "hide when empty" for the staff, and
    `Measure::isEmpty()` returns true at once for a multimeasure rest (`src/engraving/dom/measure.cpp:2283`), before
    the check for annotations, so the staff text no longer keeps the staff visible. Minimal repro:
    `repro/14-words-hidden-staff-mmrest.musicxml` (hand-written; with the final build the text on staff 1 is missing,
    and two controls, without multirest or with staff 1 visible, draw it). **Not fixed**: the fix is in engraving
    layout (count the annotations of the multimeasure rest, or of the measures it covers), and I left it for a separate
    change.

## Other problems found (not fixed)

- **Plain clef changes are still lost in several parts** (clef column; for example va 29/12, vn2 27/12, ob2 24/10).
  Part of this is the end-of-bar problem in the next item. I did not find the rest: a minimal file with a clef change
  in the middle of a bar before a rest round-trips correctly. Places to start: va bars 17 and 30 of no. 14 (measure
  indices 111 and 124 in the checker), where cue passages change clef several times within a bar.
- **A clef change at the end of a bar is drawn after the next barline.** `MusicXmlParserPass2::clef()` gives every
  clef that is not at the start of the measure `ClefToBarlinePosition::AFTER` (the `else` branch around
  `importmusicxmlpass2.cpp:6340`), so a clef at the end of a bar is moved after the next barline by layout and exported
  as `after-barline="yes"`. 4.7.4 has the same import code and draws repro 04 the same way. Setting AFTER only when
  `tick == measure->tick()` should fix it, but I have not tested that. This is the main remaining source of clef
  differences in the parts and the reason why repro 04/04b now show `size=cue,after-barline=yes` (the cue clef
  heuristic of defect 4 applies to the moved clef).
- MuseScore fills gaps in voices with rests (liuto note 0/99): the checker counts them as gained notes.
- Jump texts (Da capo, al Fine, tacet) are exported on staff 1 of the part (gamba words 3/3).
- Barline differences in several parts (for example bc 21/1) were not investigated.
- The exported `<millimeters>` is rounded, so positions drift by 0.01 tenths on a round trip (see defect 9).
- Figured bass: MuseScore reads and writes `cross` and `backslash`, while MusicXML uses `plus`, `back-slash` and
  `vertical`, so these standard values are lost on import.
- `<defaults>` `system-distance` and `top-system-distance` are not mapped to styles; this could be a follow-up to
  defect 9.

## Open questions

1. Defect 5: is "staff-size below 100 without staff-type scales the notation" what you want for the gamba's staff 3?
2. Defect 4: is a heuristic for cue clefs acceptable, or should the clef get a saved property?
3. Defect 8: how to handle the Reserved Font Name of MScoreBC upstream.
4. Defect 9: should the spacers and the system locks move behind their own import preference before proposing them
   upstream? Both change every import of a file with printed layout (the locks only where all system breaks are
   declared).
5. The encoding of the 8 grace cue notes (`size="cue"` versus `grace-cue`) and the `staff-layout` numbering in bc and
   ob2.

## Deviations from the brief

- **Branch.** The brief says to push to `musicxml-roundtrip`. This session was set up to develop and push on
  `claude/musicxml-roundtrip-handoff-lem5pj` only, so all commits are there. `musicxml-roundtrip` is unchanged.
- **Trailer.** The commits end with `Assisted-by: Claude Code` without the model identifier, because this session's
  rules forbid model identifiers in commits. `git rebase --exec` or `git filter-repo` can add it if you want it.
- **Extra commits** not in the defect list: `f75a44e9` (converter crash, needed to measure anything), `68e4e8db` (cue
  rests, part of defect 4's checker numbers), `b97579b2` (print-object, part of defect 5) and `0e8d165a` (tied-over
  accidentals, part of defect 1). Defect 4 is split into three commits so that the clef heuristic can be dropped on its
  own.
- I did not run `tools/codestyle/tidy_file.sh` with upstream's uncrustify version (see "Build and environment").
