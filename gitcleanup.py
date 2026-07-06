#!/usr/bin/env python3
"""gitcleanup — Find and clean up stale branches, refs, and orphaned objects. Zero deps."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git(*args, **kwargs) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    cmd = ["git"] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def git_lines(*args) -> list:
    """Run a git command and return stdout lines (stripped, non-empty)."""
    result = git(*args)
    return [l.strip() for l in result.stdout.split('\n') if l.strip()]


def get_current_branch() -> str:
    """Get the name of the current branch."""
    return git_lines("rev-parse", "--abbrev-ref", "HEAD")[0]


def get_default_branch() -> str:
    """Try to determine the default branch (main/master)."""
    # Try common names
    for name in ["main", "master"]:
        r = git("rev-parse", "--verify", f"refs/heads/{name}")
        if r.returncode == 0:
            return name
    # Fallback to remote HEAD
    r = git("remote", "show", "origin")
    if r.returncode == 0:
        for line in r.stdout.split('\n'):
            if "HEAD branch:" in line:
                return line.split(":")[1].strip()
    return "main"


def get_branch_age(branch: str) -> int:
    """Get the age of a branch's last commit in days."""
    r = git("log", "-1", "--format=%ct", branch)
    if r.returncode != 0 or not r.stdout.strip():
        return 0
    try:
        ts = int(r.stdout.strip())
        commit_date = datetime.fromtimestamp(ts, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - commit_date).days
    except (ValueError, TypeError):
        return 0


def get_branch_size(branch: str) -> int:
    """Estimate the size of a branch in bytes (unique objects)."""
    default = get_default_branch()
    r = git("rev-list", "--objects", f"{default}..{branch}")
    if r.returncode != 0 or not r.stdout.strip():
        return 0
    objects = r.stdout.strip().split('\n')
    # Rough estimate: count objects
    return len(objects) * 1024  # rough 1KB per object estimate


def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_scan(args) -> int:
    """Scan for merged branches, stale branches, and orphaned objects."""
    results = {
        "merged_branches": [],
        "stale_branches": [],
        "stale_remote_refs": [],
        "orphaned_objects": 0,
        "disk_space_savings": 0,
    }

    default_branch = get_default_branch()
    current_branch = get_current_branch()

    # Merged branches
    merged = git_lines("branch", "--merged", default_branch)
    for b in merged:
        b_clean = b.lstrip('*').strip()
        if b_clean != default_branch and b_clean != current_branch:
            age = get_branch_age(b_clean)
            size = get_branch_size(b_clean)
            results["merged_branches"].append({
                "branch": b_clean,
                "age_days": age,
                "estimated_size": size,
            })
            results["disk_space_savings"] += size

    # Stale branches (older than threshold)
    all_branches = git_lines("branch", "-a")
    for b in all_branches:
        b_clean = b.lstrip('*').strip()
        if b_clean.startswith("remotes/"):
            continue
        if b_clean == default_branch or b_clean == current_branch:
            continue
        age = get_branch_age(b_clean)
        if args.older_than and age >= args.older_than:
            if b_clean not in [mb["branch"] for mb in results["merged_branches"]]:
                size = get_branch_size(b_clean)
                results["stale_branches"].append({
                    "branch": b_clean,
                    "age_days": age,
                    "estimated_size": size,
                })
                results["disk_space_savings"] += size

    # Stale remote refs
    remote_refs = git_lines("remote", "prune", "--dry-run", "origin")
    results["stale_remote_refs"] = [r.strip() for r in remote_refs if r.strip()]

    # Orphaned objects (unreachable)
    orphaned = git("count-objects", "-v")
    if orphaned.returncode == 0:
        for line in orphaned.stdout.split('\n'):
            if 'prune-packable' in line:
                try:
                    results["orphaned_objects"] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass

    if args.format == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        print("=== gitcleanup scan ===")
        print(f"Default branch: {default_branch}")
        print(f"Current branch: {current_branch}")
        print()

        if results["merged_branches"]:
            print(f"Merged branches ({len(results['merged_branches'])}):")
            for b in results["merged_branches"]:
                print(f"  {b['branch']:<30} age: {b['age_days']}d  size: ~{format_size(b['estimated_size'])}")
        else:
            print("No merged branches found.")

        if results["stale_branches"]:
            print(f"\nStale branches > {args.older_than}d ({len(results['stale_branches'])}):")
            for b in results["stale_branches"]:
                print(f"  {b['branch']:<30} age: {b['age_days']}d  size: ~{format_size(b['estimated_size'])}")

        if results["stale_remote_refs"]:
            print(f"\nStale remote refs ({len(results['stale_remote_refs'])}):")
            for r in results["stale_remote_refs"]:
                print(f"  {r}")

        if results["orphaned_objects"]:
            print(f"\nOrphaned objects: {results['orphaned_objects']} (prune-packable)")

        print(f"\nEstimated disk space savings: {format_size(results['disk_space_savings'])}")

    return 0


def cmd_clean(args) -> int:
    """Delete merged branches."""
    default_branch = get_default_branch()
    current_branch = get_current_branch()

    merged = git_lines("branch", "--merged", default_branch)
    to_delete = []
    for b in merged:
        b_clean = b.lstrip('*').strip()
        if b_clean != default_branch and b_clean != current_branch:
            age = get_branch_age(b_clean)
            if args.older_than is None or age >= args.older_than:
                to_delete.append(b_clean)

    if not to_delete:
        if args.format == "json":
            print(json.dumps({"deleted": [], "note": "No branches to clean"}))
        else:
            print("No merged branches to delete.")
        return 0

    if args.dry_run:
        if args.format == "json":
            print(json.dumps({"dry_run": True, "would_delete": to_delete}))
        else:
            print(f"Would delete {len(to_delete)} merged branches (dry-run):")
            for b in to_delete:
                print(f"  {b}")
        return 0

    if not args.force:
        print(f"About to delete {len(to_delete)} merged branches:")
        for b in to_delete:
            print(f"  {b}")
        response = input("Proceed? [y/N] ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return 0

    deleted = []
    for b in to_delete:
        r = git("branch", "-D", b)
        if r.returncode == 0:
            deleted.append(b)
        else:
            print(f"Failed to delete {b}: {r.stderr.strip()}", file=sys.stderr)

    if args.format == "json":
        print(json.dumps({"deleted": deleted, "count": len(deleted)}))
    else:
        print(f"Deleted {len(deleted)} branches.")
    return 0


def cmd_prune(args) -> int:
    """Prune stale remote tracking refs."""
    if args.dry_run:
        refs = git_lines("remote", "prune", "--dry-run", "origin")
        if args.format == "json":
            print(json.dumps({"dry_run": True, "stale_refs": refs}))
        else:
            if refs:
                print(f"Would prune {len(refs)} stale remote refs (dry-run):")
                for r in refs:
                    print(f"  {r}")
            else:
                print("No stale remote refs to prune.")
        return 0

    r = git("remote", "prune", "origin")
    if args.format == "json":
        print(json.dumps({"status": "ok", "output": r.stdout.strip().split('\n') if r.stdout.strip() else []}))
    else:
        print(r.stdout if r.stdout else "No stale refs to prune.")
    return 0


def cmd_orphans(args) -> int:
    """Find orphaned/unreachable objects."""
    # List unreachable objects
    unreachable = git_lines("fsck", "--unreachable", "--no-reflogs")
    orphan_count = len(unreachable)

    # Count loose objects
    count_r = git("count-objects", "-v")
    loose_count = 0
    size_estimate = 0
    if count_r.returncode == 0:
        for line in count_r.stdout.split('\n'):
            if 'count:' in line:
                try:
                    loose_count = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            if 'size:' in line:
                try:
                    size_estimate = int(line.split(':')[1].strip().replace('KiB', '').strip())
                except (ValueError, IndexError):
                    pass

    if args.format == "json":
        print(json.dumps({
            "unreachable_objects": orphan_count,
            "loose_objects": loose_count,
            "size_kib": size_estimate,
        }))
    else:
        print(f"Unreachable objects: {orphan_count}")
        print(f"Loose objects: {loose_count}")
        print(f"Size: {size_estimate} KiB")
        if args.verbose and unreachable:
            print("\nUnreachable objects:")
            for obj in unreachable[:50]:
                print(f"  {obj}")
            if len(unreachable) > 50:
                print(f"  ... and {len(unreachable) - 50} more")

    return 0


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")

    p = argparse.ArgumentParser(
        description="gitcleanup — Find and clean up stale branches, refs, and orphaned objects")

    sub = p.add_subparsers(dest="cmd", required=True)

    sp_scan = sub.add_parser("scan", parents=[common],
                             help="Scan for merged branches, stale branches, orphaned objects")
    sp_scan.add_argument("--older-than", type=int, default=90,
                         help="Age threshold in days for stale branches (default: 90)")
    sp_scan.add_argument("--dry-run", action="store_true", default=True,
                         help="Dry-run mode (default for scan)")

    sp_clean = sub.add_parser("clean", parents=[common],
                              help="Delete merged branches")
    sp_clean.add_argument("--force", "-f", action="store_true",
                          help="Skip confirmation prompt")
    sp_clean.add_argument("--dry-run", action="store_true",
                          help="Show what would be deleted without deleting")
    sp_clean.add_argument("--older-than", type=int, default=None,
                          help="Only delete branches older than N days")

    sp_prune = sub.add_parser("prune", parents=[common],
                              help="Remove stale remote tracking refs")
    sp_prune.add_argument("--dry-run", action="store_true",
                          help="Show what would be pruned without pruning")

    sp_orphans = sub.add_parser("orphans", parents=[common],
                                help="Find orphaned/unreachable objects")
    sp_orphans.add_argument("--verbose", "-v", action="store_true",
                            help="Show detailed object list")

    args = p.parse_args()

    if args.cmd == "scan":
        return cmd_scan(args)
    elif args.cmd == "clean":
        return cmd_clean(args)
    elif args.cmd == "prune":
        return cmd_prune(args)
    elif args.cmd == "orphans":
        return cmd_orphans(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
