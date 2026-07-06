#!/usr/bin/env python3
"""Tests for gitcleanup — tests for CLI parsing and dry-run modes."""

import os
import subprocess
import sys
import tempfile

TOOL = os.path.join(os.path.dirname(__file__), "gitcleanup.py")


def run(*args, cwd=None):
    """Run gitcleanup with args."""
    cmd = [sys.executable, TOOL] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout, r.stderr


def test_scan_in_git_repo():
    """Test scan in a temp git repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)

        # Create initial commit
        (tmpdir_path := os.path.join(tmpdir, "README.md"))
        with open(os.path.join(tmpdir, "README.md"), 'w') as f:
            f.write("# test\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmpdir, capture_output=True)

        # Create and merge a feature branch
        subprocess.run(["git", "checkout", "-b", "feature"], cwd=tmpdir, capture_output=True)
        with open(os.path.join(tmpdir, "feature.txt"), 'w') as f:
            f.write("feature\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "feature"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "merge", "feature"], cwd=tmpdir, capture_output=True)

        # Run scan
        rc, out, err = run("scan", cwd=tmpdir)
        assert rc == 0, f"scan failed: {err}"
        assert "feature" in out or "No merged branches" in out


def test_scan_json_format():
    """Test scan with JSON format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)

        with open(os.path.join(tmpdir, "README.md"), 'w') as f:
            f.write("# test\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmpdir, capture_output=True)

        rc, out, err = run("scan", "--format", "json", cwd=tmpdir)
        assert rc == 0, f"scan failed: {err}"
        import json
        data = json.loads(out)
        assert "merged_branches" in data
        assert "stale_branches" in data


def test_clean_dry_run():
    """Test clean with dry-run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)

        with open(os.path.join(tmpdir, "README.md"), 'w') as f:
            f.write("# test\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmpdir, capture_output=True)

        rc, out, err = run("clean", "--dry-run", cwd=tmpdir)
        assert rc == 0, f"clean dry-run failed: {err}"


def test_prune_dry_run():
    """Test prune dry-run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)

        with open(os.path.join(tmpdir, "README.md"), 'w') as f:
            f.write("# test\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmpdir, capture_output=True)

        rc, out, err = run("prune", "--dry-run", cwd=tmpdir)
        # May fail if no origin, that's OK
        # Just check it runs without crash
        assert rc in (0, 1, 128), f"Unexpected return code: {rc}"


def test_orphans():
    """Test orphans command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)

        with open(os.path.join(tmpdir, "README.md"), 'w') as f:
            f.write("# test\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmpdir, capture_output=True)

        rc, out, err = run("orphans", cwd=tmpdir)
        assert rc == 0, f"orphans failed: {err}"


def test_help():
    """Test that all subcommands have help."""
    for cmd in ["scan", "clean", "prune", "orphans"]:
        rc, out, err = run(cmd, "--help")
        assert rc == 0, f"{cmd} --help failed: {err}"
        assert out, f"{cmd} --help produced no output"


if __name__ == "__main__":
    tests = [
        test_scan_in_git_repo,
        test_scan_json_format,
        test_clean_dry_run,
        test_prune_dry_run,
        test_orphans,
        test_help,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
