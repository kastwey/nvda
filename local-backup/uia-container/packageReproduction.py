"""Package only reviewed reproduction files and verify their archived hashes."""

import hashlib
import json
from pathlib import Path
import zipfile


def main() -> None:
	root = Path(__file__).resolve().parent
	names = (
		"attachment-readme.md",
		"container-navigation.html",
		"technical-notes.md",
		"earlier-feature-run-excerpt.log",
	)
	manifest = {
		"status": "Clean-build keyboard reproduction and candidate browser validation still pending",
		"files": {
			name: hashlib.sha256((root / name).read_bytes()).hexdigest()
			for name in names
		},
	}
	archivePath = root / "uia-container-reproduction.zip"
	with zipfile.ZipFile(archivePath, "w", compression=zipfile.ZIP_DEFLATED) as archive:
		for name in names:
			archive.write(root / name, arcname=name)
		archive.writestr("sha256-manifest.json", json.dumps(manifest, indent=2) + "\n")
	with zipfile.ZipFile(archivePath) as archive:
		assert archive.testzip() is None
		for name, digest in manifest["files"].items():
			assert hashlib.sha256(archive.read(name)).hexdigest() == digest
	print("ARCHIVE_VERIFIED", archivePath)
	print("MEMBERS", ", ".join(names), "sha256-manifest.json")
	print("ARCHIVE_SHA256", hashlib.sha256(archivePath.read_bytes()).hexdigest())


if __name__ == "__main__":
	main()
