# Release Checklist

- [ ] Version is consistent in package metadata, source, and release notes.
- [ ] Python 3.11, 3.12, and 3.13 jobs pass.
- [ ] Synthetic generated examples are current.
- [ ] Registry and schema parity checks pass.
- [ ] Public-boundary scan passes.
- [ ] No bootstrap payload or one-time workflow remains.
- [ ] Release candidate equals current `main`.
- [ ] Tag points to the audited `main` commit.
- [ ] ZIP, tar.gz, Wheel, SHA-256, and provenance assets are present.
- [ ] Known limitations remain explicit.
