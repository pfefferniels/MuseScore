"""Semantic comparison of a MusicXML file with its MuseScore round trip.

    python3 roundtrip_check.py in.musicxml out.musicxml [--details N]

Compares per (part, measure index, staff) the multisets of musical facts listed in FACTS and prints a loss/gain
table per category. Byte identity is not the target: MuseScore rewrites identification, defaults, positions and
element order. The normalisations below remove differences that carry no musical meaning.
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import accumulate
from typing import Callable, Iterator


@dataclass(frozen=True, order=True)
class Fact:
    category: str
    part: int
    measure: int
    staff: str
    value: str


def text_of(el: ET.Element | None, path: str, default: str = "") -> str:
    return default if el is None else (el.findtext(path) or default).strip()


def staff_of(el: ET.Element) -> str:
    return text_of(el, "staff", "1")


def attrs(el: ET.Element | None, *names: str) -> str:
    if el is None:
        return ""
    return ",".join(f"{n}={el.get(n)}" for n in names if el.get(n) is not None)


def pitch(note: ET.Element) -> str:
    if note.find("rest") is not None:
        return "rest"
    alter = text_of(note, "pitch/alter", "0")
    return text_of(note, "pitch/step") + ("" if alter == "0" else f"[{alter}]") + text_of(note, "pitch/octave")


def note_value(note: ET.Element, divisions: int) -> str:
    type_el = note.find("type")
    flags = [
        "cue" if note.find("cue") is not None else "",
        "grace" if note.find("grace") is not None else "",
        "chord" if note.find("chord") is not None else "",
        "size=" + type_el.get("size") if type_el is not None and type_el.get("size") else "",
        "tie=" + "+".join(sorted(t.get("type") for t in note.findall("tie"))) if note.find("tie") is not None else "",
    ]
    duration = Fraction(int(text_of(note, "duration", "0")), divisions)
    dots = len(note.findall("dot"))
    return f"{pitch(note)}:{text_of(note, 'type', '-')}{'.' * dots}/{duration} {' '.join(f for f in flags if f)}".strip()


def is_filler_rest(note: ET.Element) -> bool:
    """Whole-measure rests MuseScore adds to otherwise empty staves or voices, and unprinted rests that carry nothing
    but time, which are the same as a <forward> (MuseScore fills holes in a voice with them)."""
    rest = note.find("rest")
    if rest is None:
        return False
    whole_measure = rest.get("measure") == "yes" and note.find("cue") is None
    only_time = (note.get("print-object") == "no" and note.find("lyric") is None and note.find("notations") is None
                 and note.find("time-modification") is None)
    return whole_measure or only_time


def note_facts(note: ET.Element, divisions: int) -> Iterator[tuple[str, str]]:
    yield "note", note_value(note, divisions)
    accidental = note.find("accidental")
    if accidental is not None:
        yield "accidental", f"{pitch(note)} {accidental.text} {attrs(accidental, 'cautionary', 'editorial', 'parentheses', 'bracket', 'size')}"
    for tied in note.findall("notations/tied"):
        yield "tied", f"{pitch(note)} {tied.get('type')}"
    for lyric in note.findall("lyric"):
        extend = lyric.find("extend")
        ext = "" if extend is None else f" extend={extend.get('type', 'none')}"
        yield "lyric", f"{lyric.get('number', '1')} {text_of(lyric, 'syllabic')} {''.join(t.text or '' for t in lyric.findall('text'))}{ext}"


def transpose_value(transpose: ET.Element | None) -> str:
    if transpose is None:
        return "0/0/"
    return f"{text_of(transpose, 'diatonic', '0')}/{text_of(transpose, 'chromatic', '0')}/{text_of(transpose, 'octave-change')}"


def transpose_facts(attributes: ET.Element, staves: int) -> Iterator[tuple[str, str, str]]:
    """One transposition per staff. A transpose without number applies to all staves; with numbers, a staff left
    out has none."""
    transposes = attributes.findall("transpose")
    if not transposes:
        return
    common = next((t for t in transposes if t.get("number") is None), None)
    for staff in map(str, range(1, staves + 1)):
        own = next((t for t in transposes if t.get("number") == staff), common)
        yield staff, "transpose", transpose_value(own)


def attribute_facts(attributes: ET.Element, staves: int) -> Iterator[tuple[str, str, str]]:
    for clef in attributes.findall("clef"):
        value = f"{text_of(clef, 'sign')}{text_of(clef, 'line')}{text_of(clef, 'clef-octave-change')} {attrs(clef, 'size', 'after-barline')}"
        yield clef.get("number", "1"), "clef", value.strip()
    for key in attributes.findall("key"):
        yield key.get("number", "all"), "key", text_of(key, "fifths")
    for details in attributes.findall("staff-details"):
        value = f"{text_of(details, 'staff-type')} size={text_of(details, 'staff-size')} {attrs(details, 'print-object')}"
        yield details.get("number", "1"), "staff-details", value
    yield from transpose_facts(attributes, staves)


JUMP_SOUNDS = ("segno", "coda", "dalsegno", "dacapo", "fine", "tocoda")


def sound_facts(sound: ET.Element | None) -> Iterator[tuple[str, str]]:
    """Jumps and markers of a <sound>; the values are ids that only have to match within a file."""
    for name in JUMP_SOUNDS:
        if sound is not None and sound.get(name) is not None:
            yield "jump", f"sound {name}"


def direction_facts(direction: ET.Element) -> Iterator[tuple[str, str]]:
    for words in direction.findall("direction-type/words"):
        yield "words", (words.text or "").strip()
    for dynamics in direction.findall("direction-type/dynamics"):
        yield "dynamics", " ".join(child.tag for child in dynamics)
    for sign in ("segno", "coda"):
        for _ in direction.findall(f"direction-type/{sign}"):
            yield "jump", sign
    yield from sound_facts(direction.find("sound"))


def child_times(measure: ET.Element) -> list[int]:
    """Time of each child of the measure, in divisions, following note durations, backup and forward. A chord note
    starts with the note before it."""
    times, t, onset = [], 0, 0
    for child in measure:
        is_chord_note = child.tag == "note" and child.find("chord") is not None
        times.append(onset if is_chord_note else t)
        if child.tag == "note" and not is_chord_note or child.tag == "forward":
            onset = t
            t += int(text_of(child, "duration", "0"))
        elif child.tag == "backup":
            t -= int(text_of(child, "duration", "0"))
    return times


def measure_length(measure: ET.Element, times: list[int]) -> int:
    """The furthest time a note or forward of the measure reaches, in divisions."""
    ends = [t + int(text_of(c, "duration", "0")) for t, c in zip(times, measure)
            if c.tag == "forward" or c.tag == "note" and c.find("chord") is None]
    return max(ends, default=0)


def is_trailing(measure: ET.Element, index: int) -> bool:
    """No note or forward in any voice starts at or after the element, so it takes effect where the next measure
    starts. A note of another voice that follows after a backup but starts earlier does not count."""
    children, times = list(measure), child_times(measure)
    return not any(c.tag in ("note", "forward") and times[i] >= times[index]
                   for i, c in enumerate(children) if i > index)


@dataclass
class PartState:
    """Number of staves and print-object state of each staff, carried from measure to measure."""
    staves: int = 1
    printed: dict[str, bool] = field(default_factory=dict)

    def update(self, attributes: ET.Element) -> None:
        self.staves = int(text_of(attributes, "staves", str(self.staves)))
        for details in attributes.findall("staff-details"):
            if details.get("print-object") is not None:
                self.printed[details.get("number", "1")] = details.get("print-object") != "no"


def direction_staff(measure: ET.Element, direction: ET.Element, state: PartState) -> str:
    """Staff of a direction. Text on a staff that is not printed and has no notes in the measure is drawn on the
    nearest printed staff of the part, so it is counted there."""
    staff = staff_of(direction)
    has_notes = any(staff_of(n) == staff and n.find("rest") is None for n in measure.findall("note"))
    if state.printed.get(staff, True) or has_notes:
        return staff
    below = range(int(staff) + 1, state.staves + 1)
    above = range(int(staff) - 1, 0, -1)
    return next((str(s) for s in [*below, *above] if state.printed.get(str(s), True)), staff)


def measure_facts(part_index: int, measure_index: int, measure: ET.Element, divisions: int,
                  state: PartState) -> Iterator[Fact]:
    def fact(category: str, staff: str, value: str, index: int = measure_index) -> Fact:
        return Fact(category, part_index, index, staff, value)

    times = child_times(measure)
    yield fact("measure-len", "all", str(Fraction(measure_length(measure, times), divisions)))
    barlines = set()
    for position, child in enumerate(measure):
        if child.tag == "note" and not is_filler_rest(child):
            onset = f" @{Fraction(times[position], divisions)}"
            yield from (fact(c, staff_of(child), v + (onset if c == "note" else "")) for c, v in note_facts(child, divisions))
        elif child.tag == "attributes":
            state.update(child)
            index = measure_index + is_trailing(measure, position)
            yield from (fact(c, staff, v, index) for staff, c, v in attribute_facts(child, state.staves))
        elif child.tag == "direction":
            yield from (fact(c, direction_staff(measure, child, state), v) for c, v in direction_facts(child))
        elif child.tag == "figured-bass":
            figures = " ".join(f"{text_of(f, 'prefix')}{text_of(f, 'figure-number')}{text_of(f, 'suffix')}" for f in child.findall("figure"))
            yield fact("figured-bass", "1", figures)
        elif child.tag == "barline":
            # a barline belongs to the measure of the part, some files repeat it after each staff
            value = f"{child.get('location', 'right')} {text_of(child, 'bar-style')}"
            if value not in barlines:
                barlines.add(value)
                yield fact("barline", "all", value)
        elif child.tag == "sound":
            yield from (fact(c, "all", v) for c, v in sound_facts(child))
        elif child.tag == "print":
            breaks = attrs(child, "new-system", "new-page")
            if breaks:
                yield fact("break", "all", breaks)


def divisions_per_measure(measures: list[ET.Element]) -> list[int]:
    """Divisions in force in each measure (a change in a measure applies from that measure on)."""
    def step(current: int, measure: ET.Element) -> int:
        return int(text_of(measure, "attributes/divisions", str(current)))
    return list(accumulate(measures, step, initial=1))[1:]


def facts(path: str) -> Counter:
    root = ET.parse(path).getroot()
    result: Counter = Counter()
    for p, part in enumerate(root.findall("part")):
        state = PartState()
        measures = part.findall("measure")
        for m, (measure, divisions) in enumerate(zip(measures, divisions_per_measure(measures))):
            result.update(measure_facts(p, m, measure, divisions, state))
    return result


def report(before: Counter, after: Counter, details: int, out: Callable[[str], None] = print) -> bool:
    lost, gained = before - after, after - before
    categories = sorted({f.category for f in before | after})
    out(f"{'category':<14}{'in':>8}{'out':>8}{'lost':>8}{'gained':>8}")
    for c in categories:
        count = lambda counter: sum(n for f, n in counter.items() if f.category == c)
        out(f"{c:<14}{count(before):>8}{count(after):>8}{count(lost):>8}{count(gained):>8}")
    for label, diff in (("lost", lost), ("gained", gained)):
        for f in sorted(diff)[:details]:
            out(f"  {label}: {f.category} part {f.part} measure-index {f.measure} staff {f.staff}: {f.value}")
    return not lost and not gained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--details", type=int, default=20, help="examples to print per direction")
    args = parser.parse_args()
    return 0 if report(facts(args.before), facts(args.after), args.details) else 1


if __name__ == "__main__":
    sys.exit(main())
