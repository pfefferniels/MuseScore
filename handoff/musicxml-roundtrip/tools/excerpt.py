"""Cut measures [a, b) of the first part into a new file; keeps divisions/key/clef/time in the first kept measure."""
import copy, sys, xml.etree.ElementTree as ET
src, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
drop_lyrics = "--no-lyrics" in sys.argv
tree = ET.parse(src); root = tree.getroot()
for c in root.findall("credit"): root.remove(c)
part = root.find("part"); ms = list(part.findall("measure"))
state = {}
for m in ms[:a]:
    for at in m.findall("attributes"):
        for ch in at:
            state[(ch.tag, ch.get("number"))] = ch
for m in ms[:a] + ms[b:]: part.remove(m)
first = ms[a]
at = first.find("attributes")
if at is None:
    at = ET.Element("attributes"); first.insert(1 if first.find("print") is not None else 0, at)
order = ["divisions", "key", "time", "staves", "clef", "staff-details", "transpose"]
present = {(ch.tag, ch.get("number")) for ch in at}
for (tag, num), el in state.items():
    if tag in order and (tag, num) not in present:
        at.append(copy.deepcopy(el))
at[:] = sorted(at, key=lambda e: order.index(e.tag) if e.tag in order else 99)
if drop_lyrics:
    for n in root.iter("note"):
        for l in n.findall("lyric"): n.remove(l)
tree.write(out, encoding="UTF-8", xml_declaration=True)
