# MusicXML round-trip fixes in MuseScore: task for a Claude Code cloud session

You are working in Niels Pfeffer's fork of MuseScore Studio (`pfefferniels/MuseScore`), branch
`musicxml-roundtrip`. Everything this task needs is in `handoff/musicxml-roundtrip/`. Read this file completely
before you start, then `AI_POLICY.md` at the repository root.

## Background

Niels has encoded the printed performance parts of Bach's St John Passion (Bärenreiter BA 5037) as MusicXML 4.0:
12 parts, XSD-valid, with the printed page and system breaks, per-system distances, cue notes with lyrics, reduced
cue staves, per-staff keys and figured bass. Opening these files in MuseScore 4.7.4 and exporting them again loses
information, and some of it is already lost or misdrawn at import. A previous session reproduced each reported
defect with a minimal file, traced several of them to the code, and recorded a baseline with the 4.7.4 release
build. Your job is to fix the defects in the source, with tests.

## Goal

1. Each fixed defect: `tools/roundtrip_check.py` reports no loss or gain for its repro file, the rendering is
   correct, and a unit test in `src/importexport/musicxml/tests` covers it.
2. One commit per defect, each one self-contained so that it could later be proposed upstream on its own.
3. A report, `handoff/musicxml-roundtrip/REPORT.md`, as described at the end.

**Not a goal: byte-identical output.** MuseScore rewrites `<identification>` and `<defaults>`, positions, element
order and divisions on every export, and fills empty staves with whole-measure rests. The checker normalises these.
Do not spend time on them.

## Build and test

- Build MuseScore on Linux following `buildscripts/ci/linux/setup.sh` and `build.sh` (or the developer docs these
  scripts point to). You need the command-line converter, `mscore -o out.musicxml in.musicxml`, which runs headless
  with `QT_QPA_PLATFORM=offscreen`.
- Unit tests: `MUE_BUILD_IMPORTEXPORT_TESTS` (default on) builds `musicxml_tests`; see
  `buildscripts/ci/linux/build_utest.sh` and `runutests.sh`. Follow the existing patterns in
  `src/importexport/musicxml/tests/musicxml_tests.cpp`: `musicXmlIoTest` (import, export, compare with the same
  file), `musicXmlIoTestRef` (compare with `<name>_ref.xml`) and `musicXmlImportTestRef` (compare with
  `<name>_ref.mscx`). Test data goes to `src/importexport/musicxml/tests/data/`.
- Run the whole `musicxml_tests` suite before every commit. Changing export output will alter existing reference
  files (for example `testExtendedLyrics_ref.xml`). Update a reference file only where the new output is the
  intended one, and list every updated reference file in the report.
- Run the repro set with your build, then compare against the 4.7.4 baseline:

  ```
  python3 handoff/musicxml-roundtrip/tools/run_roundtrip.py --mscore <build>/mscore \
      --out /tmp/rt handoff/musicxml-roundtrip/repro/*.musicxml
  ```

  It writes `<name>.out.musicxml`, `<name>-<page>.png` and `<name>.check.txt` per file. Look at the PNGs: several
  defects concern rendering only.

## The full parts (private)

The 12 parts are in Niels' private repository `pfefferniels/jopa`, folder `nba-parts/`, at commit `5f84b0a` (the
version the baseline numbers below refer to). Clone it outside this repository, for example
`git clone https://github.com/pfefferniels/jopa /tmp/jopa`. The files are a transcription for private research
and include a copyrighted English underlay. Never copy them, or excerpts longer than a few bars, into this fork,
which is public, and never commit them anywhere. If you cannot clone the repository, say so in the report and
work with the repros only.

With the parts available:

- At the start, and again when you finish, run `tools/run_roundtrip.py --no-render` over all 12 parts and count
  the pages of `mscore -o <part>.pdf <part>.musicxml` (for example with `pdfinfo`). Put both tables in the report.
- The smallest multi-staff cases are `liuto-liuto.musicxml` (2 staves, 24 bars), `gamba-viola-da-gamba.musicxml`
  (3 staves including a reduced vocal cue staff, 119 bars) and the two `vadam` parts. `bc-continuo.musicxml` has a
  reduced vocal staff, a hidden staff and tremolos. `ob1` and `ob2` have per-staff keys and transposing staves.
- For gamba, 4.7.4 gives this checker table (in, out, lost, gained): accidental 239/236/43/40,
  lyric 965/782/229/46, note 2455/2455/45/45, staff-details 9/32/8/31, break 35/36/1/2, words 36/37/3/4,
  barline 6/6/2/2. Clefs, keys, ties and dynamics are equal.

## Defects

The order is the suggested priority. "Cause" is marked as verified when the previous session read the code and the
repro confirmed it, and as suspected otherwise. Check every suspected cause before acting on it.

### 1. Printed courtesy accidentals are dropped at import

Repro `03-accidentals.musicxml`, baseline `baseline-4.7.4/03-accidentals-1.png`. In the parts this drops printed
accidentals (viola da gamba part, 51st measure, bar 32: A3 natural and the second A♭4 flat; 92nd measure, bar 17:
natural on a grace E4).

Cause (verified): `markUserAccidentals()` in `src/importexport/musicxml/internal/import/importmusicxmlpass2.cpp`
(around line 2552) marks an accidental as `AccidentalRole::USER` only if it is redundant with respect to the
key signature. Everything else keeps role AUTO, and layout then removes AUTO accidentals it considers unnecessary.
Three defects:

- `accTmp` and `currAcc` are shared by all staves of the part. An A♭3 on staff 2 prevents a courtesy A3 natural on
  staff 1 from being marked (repro bar 1).
- `currAcc` is initialised from the key and never updated within the measure, so an accidental that repeats an
  earlier alteration in the same measure is not recognised as redundant (repro bar 2, second A♭4).
- Only the chords in segments are visited, so grace notes are never checked (repro bar 3).

Expected: every `<accidental>` in the input is displayed after import and present after export.

### 2. Plain redundant accidentals come back as `cautionary="yes" parentheses="no"`

Repro `03-accidentals.musicxml` bar 4. In the gamba part there were 40 such cases.

Cause (verified): `writeAccidental()` in `export/exportmusicxml.cpp` (around line 2860) writes every unbracketed
USER accidental with `cautionary="yes" parentheses="no"`. Proposed fix: write a plain `<accidental>` for an
unbracketed USER accidental. Once defect 1 is fixed, re-import marks it USER again because it is redundant. This
changes long-standing export behaviour, so keep it in its own commit and say in the report that upstream may not
want it.

### 3. Melisma end markers are lost on export

Repro `01-lyric-extend.musicxml`. In the gamba part, 183 `<lyric><extend type="stop"/></lyric>` were dropped and
the 46 `<extend type="start"/>` came back as `<extend/>`. No sung syllable is lost. The peer report counted these
as lost syllables, which is incorrect.

Cause (verified): `ExportMusicXml::lyrics()` in `export/exportmusicxml.cpp` (around line 6091) writes `<extend/>`
when `l->ticks()` is non-zero and nothing on the following notes. Import and rendering are correct (the melisma
line ends at the right note). Proposed fix: write `type="start"`, and on the notes covered by the melisma write
`<lyric number="n"><extend type="continue"/></lyric>`, with `type="stop"` on the last note. The figured-bass export
in the same file already does start/continue/stop and may be a model. Check that import of the new output gives the
same melisma.

### 4. Cue size is lost on export: notes and clefs

Repro `02-staff-size-cue.musicxml` (notes), `05-cue-clef-after-barline.musicxml` (clef).

Cause (verified for notes): `writeType()` in `export/exportmusicxml.cpp` (around line 4220) omits
`size="cue"` for cue notes because it is "implicit". The MusicXML 4.0 definition of `<cue>` only says that the note
does not play, and the size is given by `<type size="cue">`. Write `size="cue"` for every small note. For
`<clef size="cue">` the cause is not yet traced: find where clef size is read at import (around line 6204 of
`importmusicxmlpass2.cpp`) and written at export.

### 5. `<staff-size>` and `<staff-type>cue</staff-type>` have no effect and are not exported

Repro `02-staff-size-cue.musicxml`: staff 1 has `<staff-type>cue</staff-type><staff-size>75</staff-size>` and is
drawn at full size. Export writes no `<staff-details>` at all (also not `print-object="no"`, repro
`08-direction-hidden-staff.musicxml`).

Cause (partly verified): `staffDetails()` in `importmusicxmlpass2.cpp` (around line 3214) reads `staff-size` with
`scaling` defaulting to 100, so it sets `MAG` 1.0 and `LINE_DISTANCE` 0.75. Even so, the staff shows no reduced
line distance, so something later probably overrides or ignores the staff type values. Find out what. `staff-type`
is not handled. The exporter (around line 8131) writes `staff-size` only when line distance or mag differ from 1.
Per the MusicXML 4.0 schema (`src/importexport/musicxml/schema/musicxml.xsd`, type `staff-size`), a cue staff
scales its notation. A reasonable reading: with `staff-type` cue (or ossia, editorial) and no `scaling`, scale the
notation by the staff size (mag 0.75, line distance 1.0). State in the report how you read the spec.

### 6. Small cue clef at the start of a page becomes the system's header clef

Repros `05c-cue-clef-page-break-defaults.musicxml` (synthetic) and `09-cue-clef-page-break-excerpt.musicxml`
(five bars from the flute I part, lyrics removed). A bar starting a new page has `<clef after-barline="yes"
size="cue">` G8vb in a second `<attributes>`. Expected: the system starts with the normal G2 clef, then the small
G8vb clef after the time signature. 4.7.4 draws a G8vb header clef instead (see the `-2.png` baselines).

What is known: the defect appears only with a page break and a `<defaults>` block (scaling and page layout).
Without `<defaults>` (`05b`, and the same file without its defaults) the clef is placed correctly. Without the
`<print>` it is also correct. The `<direction>`, the time change, the cue rest, the key signature and a second
voice were ruled out. Cause not traced. Start at the clef handling around lines 6204 and 6312 of
`importmusicxmlpass2.cpp` and at what `<defaults>` switches on (layout import, spatium). Repros `05` and `05b` must
stay correct.

### 7. A tie stop without a start is not drawn and not exported

Repro `06-lone-tie-stop.musicxml`. The parts need this where a tie arrives from a bar the part does not print.
MuseScore 4.5 and later have incoming partial ties (`src/engraving/dom/partialtie.h`). Suspected fix: create an
incoming partial tie for a lone `<tie type="stop"/>` or `<tied type="stop"/>`, and export it again as
`<tied type="stop"/>`.

### 8. Slashed figured-bass digits display as "?"

Repro `07-figured-bass-slash.musicxml`. The round trip itself is lossless.

Cause (verified): in `fonts/fonts_figuredbass.xml` the MScoreBC font has `?` in `<slashed>` and
`<slashedHistoric>` for nine digits, 6 among them. Look up the SMuFL figured-bass glyphs for raised digits (for
example the "6 raised" glyph) in the SMuFL specification and use them, or draw the digit with an overlaid slash.
Credit the source of any glyph mapping you use in the commit message.

### 9. Printed vertical layout is ignored, so systems spill onto extra pages

The parts give every system its distances in `<print>`: `<system-layout>` with `<system-distance>`,
`<top-system-distance>` and `<system-margins>`, and `<staff-layout><staff-distance>`. The Viola part has 225
`system-distance` values. With 4.7.4 the page counts grow: ob1 20→21, ob2 18→20, gamba 6→7, vadam2 4→5, va 22→28,
vn1 28→29, vn2 23→26, bc 53→55.

Cause (verified): pass 2 skips `page-layout`, `system-layout` and `staff-layout` inside `<print>`
(`importmusicxmlpass2.cpp` around line 2905), and pass 1 skips `system-margins` and `top-system-distance` in
`<defaults>` (`importmusicxmlpass1.cpp` around line 2003). Proposed fix: when layout import is enabled, map each
system's distances to MuseScore's model, for example fixed spacers, so that the printed systems fit the printed
pages. Larger than the others: write a short design note in the report before you implement it. Build a synthetic
test with several pages of systems and explicit distances, and compare the page counts of the full parts with the
table above.

### 10. Exit crash after conversion

On macOS, 4.7.4 aborts at exit with `libc++abi: terminating due to uncaught exception of type
std::__1::system_error: mutex lock failed: Invalid argument` (exit code 134) after writing a complete file, in 14 of
16 conversions of the repro files in one test run. Check whether your Linux build of the current branch shows it. If it does, find
the cause. `main` already contains upstream PR #34733 ("write-deadlock"), which may be related. If you cannot
reproduce it on Linux, say so and leave it.

### Lower priority, only after 1 to 9

- Credits with `page="2"` and higher are ignored. A centred page-level credit on page 1 lands on top of the title in
  the title frame. One option is to map running heads that repeat on every page to header and footer styles.
- Two defects seen with MuseScore 4.5 that the minimal repros did not reproduce in 4.7.4. Recreate each in a copy of
  the full part and check the PDF:
  - A clef change after the last rest of a collapsed `<multiple-rest>`: the following cue was drawn in the old
    clef. Original places: `vadam2-viola-d-amore-II.musicxml`, first system of PDF page 1 (no. 18c, cue clef
    treble-8 at the end of a 4-bar rest), and `ob1-oboe-I.musicxml`, first system of PDF page 9 (no. 21f,
    bars 58 to 61, treble clef at the end of the rest). The current files have the clef at the start of the next
    measure. Move it into an `<attributes>` after the last rest of the last measure the multirest covers.
  - A words direction attached to staff 1 where staff 1 has `<staff-details print-object="no">` in that system
    was missing from the PDF (gamba and liuto, probably gamba PDF page 1). Move a words direction from staff 2 to
    staff 1 in such a system.
  If either still fails, write a minimal repro and treat it like the defects above.
- Untested so far: `<tuplet show-number="none" bracket="no">`, `<notehead parentheses="yes">`, an `<alter>` without
  `<accidental>`, and survival of per-staff `<transpose number="n">` on export. Write a repro for each, run it and
  record the result in the report. Fix only what is clearly a defect.

### Not defects, or out of scope

- Whole-measure rests added to empty staves, reordering, rewritten identification and defaults (normalised by the
  checker).
- A clef at the end of a bar comes back at the start of the next bar. This is equivalent, and the checker treats it
  as equal. The peer report of a clef dropped inside a multirest did not reproduce in `04` and `04b`.
- A direction on a staff with `print-object="no"` is kept and drawn (`08`). Elements of a hidden staff are not drawn
  by design.
- Centring a words direction on the system: MuseScore has no such placement.
- A multirest whose last bar holds cue notes is drawn as n−1 bars of rest plus the cue bar. MusicXML cannot say
  otherwise.

## Rules

- Do not open pull requests, issues or comments in `musescore/MuseScore` or any other upstream space. Niels reviews
  everything first (`AI_POLICY.md`, section 2).
- Commits: subject in the imperative, at most 60 characters, no trailing period. A body only when it adds something
  the diff does not show. End each commit with the trailer the repository asks for:
  `Assisted-by: Claude Code (claude-opus-5-5)`. Do not use `Co-authored-by`.
- Keep `handoff/` changes in separate commits from the fixes, so that the fix commits can be cherry-picked onto
  upstream `main` without them.
- Follow the code style of the surrounding file and run `tools/codestyle/tidy_file.sh` on changed C++ files.
  Comments short and sparse. They say why, never what changed or what the code used to do.
- Touch only what a defect needs. If you notice other problems, list them in the report instead of fixing them.
- Push to `origin` (the fork) on the `musicxml-roundtrip` branch as you go, so that the work survives the session.

## Report

`handoff/musicxml-roundtrip/REPORT.md`, written for Niels in plain, factual prose. For each defect: fixed, partly
fixed or not fixed, the cause as you found it, the commit, the test, the checker output before and after, and
anything you are unsure about. Then the updated reference files, the results for the untested items, and the open
questions. Claim only what you have checked.
