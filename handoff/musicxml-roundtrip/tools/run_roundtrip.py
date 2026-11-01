"""Round-trip MusicXML files through an mscore binary, render them, and run roundtrip_check on each.

    python3 run_roundtrip.py --mscore PATH --out DIR file.musicxml [...]

For each input writes DIR/<name>.out.musicxml, DIR/<name>-<page>.png and DIR/<name>.check.txt, and prints one
summary line per file. A non-zero mscore exit status is reported even when the output file was written.
"""
import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from roundtrip_check import facts, report


@dataclass(frozen=True)
class Conversion:
    exit_code: int
    output: Path


def convert(mscore: str, source: Path, target: Path, *options: str) -> Conversion:
    completed = subprocess.run([mscore, *options, "-o", str(target), str(source)], capture_output=True, timeout=600)
    return Conversion(completed.returncode, target)


def check(source: Path, out_dir: Path, mscore: str, render: bool) -> str:
    exported = convert(mscore, source, out_dir / f"{source.stem}.out.musicxml")
    if render:
        convert(mscore, source, out_dir / f"{source.stem}.png", "-r", "100", "-T", "20")
    if not exported.output.exists():
        return f"{source.name}: no output (mscore exit {exported.exit_code})"
    lines: list[str] = []
    equal = report(facts(str(source)), facts(str(exported.output)), details=50, out=lines.append)
    (out_dir / f"{source.stem}.check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    status = "equal" if equal else "differs"
    return f"{source.name}: {status} (mscore exit {exported.exit_code})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mscore", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    print("\n".join(check(f, args.out, args.mscore, not args.no_render) for f in args.files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
