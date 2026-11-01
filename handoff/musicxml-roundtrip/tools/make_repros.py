"""Write the minimal MusicXML repro files for the MuseScore round-trip handoff."""
import sys
from pathlib import Path

HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="4.0">
  <work><work-title>{title}</work-title></work>
  <part-list>
    <score-part id="P1"><part-name>Test</part-name></score-part>
  </part-list>
  <part id="P1">
"""
TAIL = """  </part>
</score-partwise>
"""


def attributes(clefs, staves=1, fifths=0, extra=""):
    staves_tag = f"<staves>{staves}</staves>" if staves > 1 else ""
    return (f"<attributes><divisions>4</divisions><key><fifths>{fifths}</fifths></key>"
            f"<time><beats>4</beats><beat-type>4</beat-type></time>{staves_tag}{clefs}{extra}</attributes>")


def clef(sign, line, number=None, octave=None, attrs=""):
    num = f' number="{number}"' if number else ""
    oc = f"<clef-octave-change>{octave}</clef-octave-change>" if octave else ""
    return f"<clef{num}{attrs}><sign>{sign}</sign><line>{line}</line>{oc}</clef>"


def note(step, octave, dur=4, typ="quarter", alter=None, acc=None, staff=None, voice=1,
         cue=False, grace=False, lyrics="", notations="", tie=""):
    alter_tag = f"<alter>{alter}</alter>" if alter is not None else ""
    size = ' size="cue"' if cue else ""
    parts = ["<note>",
             '<grace slash="yes"/>' if grace else "",
             "<cue/>" if cue else "",
             f"<pitch><step>{step}</step>{alter_tag}<octave>{octave}</octave></pitch>",
             "" if grace else f"<duration>{dur}</duration>",
             tie,
             f"<voice>{voice}</voice>",
             f"<type{size}>{typ}</type>",
             f"<accidental>{acc}</accidental>" if acc else "",
             f"<staff>{staff}</staff>" if staff else "",
             f"<notations>{notations}</notations>" if notations else "",
             lyrics,
             "</note>"]
    return "".join(parts)


def rest(dur=16, typ="whole", staff=None, voice=1, measure=True, cue=False):
    m = ' measure="yes"' if measure else ""
    size = ' size="cue"' if cue else ""
    st = f"<staff>{staff}</staff>" if staff else ""
    return (f"<note>{'<cue/>' if cue else ''}<rest{m}/><duration>{dur}</duration><voice>{voice}</voice>"
            f"{'' if measure else f'<type{size}>{typ}</type>'}{st}</note>")


def lyric(number, text=None, syllabic="single", extend=None):
    body = f"<syllabic>{syllabic}</syllabic><text>{text}</text>" if text is not None else ""
    ext = f'<extend type="{extend}"/>' if extend else ""
    return f'<lyric number="{number}">{body}{ext}</lyric>'


def measure(number, *content):
    return f'    <measure number="{number}">' + "".join(content) + "</measure>\n"


def backup(d=16):
    return f"<backup><duration>{d}</duration></backup>"


def words(text, staff=None, placement="above"):
    st = f"<staff>{staff}</staff>" if staff else ""
    return (f'<direction placement="{placement}"><direction-type><words>{text}</words></direction-type>'
            f"{st}</direction>")


def score(title, measures):
    return HEAD.format(title=title) + "".join(measures) + TAIL


REPROS = {}

# 1. Melisma: extend start / continue / stop, two verses.
REPROS["01-lyric-extend"] = score("lyric extend start/continue/stop", [
    measure(1, attributes(clef("G", 2)),
            note("C", 5, lyrics=lyric(1, "Ah", extend="start") + lyric(2, "Oh", extend="start")),
            note("D", 5, lyrics=lyric(1, extend="continue") + lyric(2, extend="continue")),
            note("E", 5, lyrics=lyric(1, extend="stop") + lyric(2, extend="stop")),
            note("F", 5, lyrics=lyric(1, "men") + lyric(2, "men"))),
    measure(2, note("G", 5, dur=8, typ="half", lyrics=lyric(1, "so", extend="start")),
            note("F", 5, lyrics=lyric(1, extend="stop")),
            note("E", 5, lyrics=lyric(1, "be"))),
])

# 2. Reduced cue staff (staff-size 75, staff-type cue) and cue notes with lyrics on both staves.
REPROS["02-staff-size-cue"] = score("staff-size and cue notes", [
    measure(1,
            attributes(clef("G", 2, 1, -1) + clef("C", 3, 2), staves=2,
                       extra='<staff-details number="1"><staff-type>cue</staff-type><staff-size>75</staff-size></staff-details>'),
            note("A", 3, cue=True, staff=1, lyrics=lyric(1, "Herr,") + lyric(2, "Lord,")),
            note("B", 3, cue=True, staff=1, lyrics=lyric(1, "un", "begin") + lyric(2, "our", "single")),
            note("C", 4, dur=8, typ="half", cue=True, staff=1, lyrics=lyric(1, "ser", "end") + lyric(2, "Lord")),
            backup(),
            note("A", 3, cue=True, staff=2, voice=5),
            note("B", 3, cue=True, staff=2, voice=5),
            note("C", 4, dur=8, typ="half", staff=2, voice=5)),
])

# 3. Printed courtesy accidentals that MuseScore drops at import (markUserAccidentals), key B flat major.
REPROS["03-accidentals"] = score("courtesy accidentals", [
    # cross-staff: staff 2 has Ab3 before staff 1's courtesy A3 natural
    measure(1, attributes(clef("G", 2, 1) + clef("F", 4, 2), staves=2, fifths=-2),
            note("C", 4, staff=1), note("D", 4, staff=1), note("A", 3, alter=0, acc="natural", staff=1), note("B", 3, alter=-1, staff=1),
            backup(),
            note("A", 3, alter=-1, acc="flat", staff=2, voice=5), note("G", 3, staff=2, voice=5),
            note("F", 3, staff=2, voice=5), note("G", 3, staff=2, voice=5)),
    # same staff: Ab4, courtesy A3 natural, Ab4 flat printed again
    measure(2, note("A", 4, alter=-1, acc="flat", staff=1), note("G", 4, staff=1),
            note("A", 3, alter=0, acc="natural", staff=1), note("A", 4, alter=-1, acc="flat", staff=1),
            backup(), rest(staff=2, voice=5)),
    # grace note with a printed courtesy natural
    measure(3, note("D", 5, alter=0, acc="natural", typ="eighth", staff=1, grace=True), note("C", 5, dur=16, typ="whole", staff=1),
            backup(), rest(staff=2, voice=5)),
    # plain courtesy natural on an ordinary note (re-exported as cautionary="yes")
    measure(4, note("D", 5, alter=0, acc="natural", dur=16, typ="whole", staff=1),
            backup(), rest(staff=2, voice=5)),
])

# 4. Clef change at the end of the last bar of a collapsed multirest; the following bar holds cue notes.
REPROS["04-clef-in-multirest"] = score("clef change inside multirest", [
    measure(1, attributes(clef("G", 2), extra='<measure-style><multiple-rest>3</multiple-rest></measure-style>'), rest()),
    measure(2, rest()),
    measure(3, rest(), "<attributes>" + clef("F", 4) + "</attributes>"),
    measure(4, note("C", 3, cue=True), note("D", 3, cue=True), note("E", 3, cue=True), note("F", 3, cue=True)),
])

# 5. Small cue clef after the barline at the start of a bar that also changes time signature.
REPROS["05-cue-clef-after-barline"] = score("cue clef after barline", [
    measure(1, attributes(clef("G", 2)), note("G", 4, dur=16, typ="whole"),
            '<barline location="right"><bar-style>light-heavy</bar-style></barline>'),
    measure(2, "<attributes><time><beats>3</beats><beat-type>4</beat-type></time></attributes>",
            "<attributes>" + clef("G", 2, octave=-1, attrs=' after-barline="yes" size="cue"') + "</attributes>",
            note("E", 4, cue=True), note("F", 4, cue=True), note("G", 4, cue=True)),
])

# 4b. As 4, but the multirest count also covers the cue bar and the clef sits inside the range.
REPROS["04b-clef-in-multirest-range"] = score("clef change inside multirest range", [
    measure(1, attributes(clef("G", 2), extra='<measure-style><multiple-rest>4</multiple-rest></measure-style>'), rest()),
    measure(2, rest()),
    measure(3, rest(), "<attributes>" + clef("F", 4) + "</attributes>"),
    measure(4, note("C", 3, cue=True), note("D", 3, cue=True), note("E", 3, cue=True), note("F", 3, cue=True)),
    measure(5, note("G", 4, dur=16, typ="whole")),
])

# 5b. As 5, but the bar with the cue clef starts a new system.
REPROS["05b-cue-clef-system-start"] = score("cue clef at system start", [
    measure(1, attributes(clef("G", 2)), note("G", 4, dur=16, typ="whole"),
            '<barline location="right"><bar-style>light-heavy</bar-style></barline>'),
    measure(2, '<print new-system="yes"/>',
            "<attributes><time><beats>3</beats><beat-type>4</beat-type></time></attributes>",
            "<attributes>" + clef("G", 2, octave=-1, attrs=' after-barline="yes" size="cue"') + "</attributes>",
            note("E", 4, cue=True), note("F", 4, cue=True), note("G", 4, cue=True)),
    measure(3, "<attributes>" + clef("G", 2) + "</attributes>", note("G", 4, dur=8, typ="half"), note("A", 4)),
])

# 6. Tie arriving from a bar the part does not print: stop without start.
REPROS["06-lone-tie-stop"] = score("tie stop without start", [
    measure(1, attributes(clef("G", 2)),
            note("A", 4, tie='<tie type="stop"/>', notations='<tied type="stop"/>'),
            note("B", 4), note("C", 5, dur=8, typ="half")),
])

# 7. Figured bass: slashed 6 (suffix slash), plus 4 and raised 3 for contrast.
REPROS["07-figured-bass-slash"] = score("figured bass slashed six", [
    measure(1, attributes(clef("F", 4)),
            "<figured-bass><figure><figure-number>6</figure-number><suffix>slash</suffix></figure></figured-bass>",
            note("D", 3),
            "<figured-bass><figure><figure-number>4</figure-number><suffix>slash</suffix></figure></figured-bass>",
            note("E", 3),
            "<figured-bass><figure><prefix>sharp</prefix><figure-number>6</figure-number></figure></figured-bass>",
            note("F", 3, dur=8, typ="half")),
])

# 8. Direction attached to a staff that is hidden in this system.
REPROS["08-direction-hidden-staff"] = score("direction on hidden staff", [
    measure(1, attributes(clef("G", 2, 1) + clef("C", 3, 2), staves=2,
                          extra='<staff-details number="1" print-object="no"/>'),
            words("Evangelista", staff=1), rest(staff=1), backup(),
            words("Recit.", staff=2), note("C", 4, dur=16, typ="whole", staff=2, voice=5)),
])

# 10. Triplet printed without number and without bracket.
TRIPLET = ("<note><pitch><step>{step}</step><octave>4</octave></pitch><duration>{dur}</duration><voice>1</voice>"
           "<type>eighth</type><time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes>"
           "</time-modification>{notations}</note>")
REPROS["10-tuplet-hidden-number-bracket"] = score("tuplet without number and bracket", [
    measure(1, attributes(clef("G", 2), extra="").replace("<divisions>4</divisions>", "<divisions>6</divisions>"),
            TRIPLET.format(step="C", dur=2, notations='<notations><tuplet type="start" bracket="no" show-number="none"/></notations>'),
            TRIPLET.format(step="D", dur=2, notations=""),
            TRIPLET.format(step="E", dur=2, notations='<notations><tuplet type="stop"/></notations>'),
            "<note><pitch><step>F</step><octave>4</octave></pitch><duration>18</duration><voice>1</voice>"
            "<type>half</type><dot/></note>"),
])

# 11. Notehead in parentheses.
REPROS["11-notehead-parentheses"] = score("notehead parentheses", [
    measure(1, attributes(clef("G", 2)),
            note("C", 5).replace("</type>", '</type><notehead parentheses="yes">normal</notehead>'),
            note("D", 5), note("E", 5, dur=8, typ="half")),
])

# 12. Alterations without <accidental>: one needs a sign by the key (F sharp in C major), one does not.
REPROS["12-alter-without-accidental"] = score("alter without accidental", [
    measure(1, attributes(clef("G", 2)),
            note("F", 4, alter=1), note("G", 4), note("F", 4, alter=1), note("E", 4)),
    measure(2, "<attributes><key><fifths>1</fifths></key></attributes>",
            note("F", 4, alter=1), note("G", 4), note("A", 4), note("B", 4)),
])

# 13. Per-staff transposition: staff 1 an oboe d'amore in A, staff 2 a cue staff at concert pitch.
REPROS["13-per-staff-transpose"] = score("per-staff transpose", [
    measure(1, attributes(clef("G", 2, 1) + clef("G", 2, 2), staves=2,
                          extra='<transpose number="1"><diatonic>-2</diatonic><chromatic>-3</chromatic></transpose>'
                                '<transpose number="2"><diatonic>0</diatonic><chromatic>0</chromatic></transpose>'
                          ).replace("<key><fifths>0</fifths></key>",
                                    '<key number="1"><fifths>3</fifths></key><key number="2"><fifths>0</fifths></key>'),
            note("E", 5, dur=16, typ="whole", staff=1),
            backup(),
            note("C", 5, dur=16, typ="whole", staff=2, voice=5)),
])


def main(outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    for name, xml in REPROS.items():
        (out / f"{name}.musicxml").write_text(xml, encoding="utf-8")
        print(out / f"{name}.musicxml")


main(sys.argv[1])
