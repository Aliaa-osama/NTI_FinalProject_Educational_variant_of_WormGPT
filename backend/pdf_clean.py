from pathlib import Path
import shutil
import sys
import pikepdf
from pikepdf import PdfError, PasswordError
from pypdf import PdfReader

# --------- CONFIG ---------
INPUT_DIR = Path("./documents")            # your original PDFs
OUTPUT_DIR = Path("./documents_cleaned")   # cleaned copies here
LINEARIZE = True                           # optimize for fast web view
# --------------------------

def validate_with_pypdf(pdf_path: Path) -> tuple[bool, str]:
    """Quick sanity check with pypdf (catches common structure issues)."""
    try:
        # strict=False makes pypdf attempt to be tolerant
        r = PdfReader(str(pdf_path), strict=False)
        _ = len(r.pages)  # force page tree traversal
        _ = r.metadata    # force metadata read
        return True, "ok"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def repair_one(src: Path, dst: Path) -> tuple[bool, str]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        with pikepdf.open(str(src)) as pdf:
            # Save repaired/normalized copy
            pdf.save(str(dst), linearize=LINEARIZE)
        # Optional: validate the cleaned file with pypdf
        ok, msg = validate_with_pypdf(dst)
        if not ok:
            return False, f"pypdf-validate-failed: {msg}"
        return True, "repaired"
    except PasswordError:
        return False, "encrypted/password-required"
    except PdfError as e:
        return False, f"pikepdf-error: {e}"
    except Exception as e:
        return False, f"unexpected: {type(e).__name__}: {e}"

def main():
    if not INPUT_DIR.exists():
        print(f"[!] INPUT_DIR not found: {INPUT_DIR.resolve()}")
        sys.exit(1)

    # Fresh output folder (safe: we won’t delete existing if it contains anything else)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = list(INPUT_DIR.rglob("*.pdf"))
    if not pdfs:
        print(f"[!] No PDFs found under {INPUT_DIR}")
        sys.exit(1)

    print(f"[*] Found {len(pdfs)} PDFs under {INPUT_DIR}")
    successes = 0
    skipped = 0
    failures = 0

    for i, src in enumerate(pdfs, 1):
        rel = src.relative_to(INPUT_DIR)
        dst = OUTPUT_DIR / rel
        print(f"[{i}/{len(pdfs)}] {rel} -> {dst.relative_to(OUTPUT_DIR)}", end=" ... ")
        ok, msg = repair_one(src, dst)
        if ok:
            print("OK")
            successes += 1
        else:
            print(f"SKIP ({msg})")
            # If encrypted or unrecoverable, you can still copy the original over (optional):
            # dst.parent.mkdir(parents=True, exist_ok=True)
            # shutil.copy2(src, dst)
            if "encrypted" in msg:
                skipped += 1
            else:
                failures += 1

    print("\n=== Summary ===")
    print(f"Repaired: {successes}")
    print(f"Skipped (encrypted): {skipped}")
    print(f"Failed (corrupt/unhandled): {failures}")
    print(f"Cleaned folder: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
