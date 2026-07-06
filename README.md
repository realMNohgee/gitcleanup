# GitCleanup 🧹

**Find and clean up merged branches, stale remote refs, and orphaned objects.** Zero dependencies, pure Python stdlib.

Keep your git repos lean. Scan for branches that have been merged (or are just stale), prune dead remote tracking refs, and identify orphaned objects wasting disk space. Reports estimated space savings.

> Part of the **Trust & Reliability Layer for Agentic AI**

## Why it exists

Every active repo accumulates cruft — merged feature branches nobody remembers to delete, stale references to long-gone remote branches, unreachable objects bloating the object store. GitCleanup provides a single tool to scan, report, and clean all of these with one command.

## One tool, many domains

| Domain | What GitCleanup does |
|---|---|
| 🧹 **Repo Hygiene** | Scan and clean merged/stale branches |
| 💾 **Disk Space** | Find orphaned objects and estimate savings |
| 🔗 **Remote Sync** | Prune stale remote tracking refs |
| ⏱️ **Age-Based** | Filter branches by age (`--older-than`) |
| 🤖 **Automation** | JSON output for scripts and CI |

## Install
```bash
git clone git@github.com:realMNohgee/gitcleanup.git
cd gitcleanup
python3 gitcleanup.py --help
```

## Quick start
```bash
# Scan your repo for cleanup opportunities
python3 gitcleanup.py scan

# Show branches older than 60 days
python3 gitcleanup.py scan --older-than 60

# Preview what would be deleted
python3 gitcleanup.py clean --dry-run

# Delete merged branches (interactive)
python3 gitcleanup.py clean

# Delete merged branches (non-interactive)
python3 gitcleanup.py clean --force

# Prune stale remote refs
python3 gitcleanup.py prune

# Find orphaned objects
python3 gitcleanup.py orphans --verbose

# JSON output for automation
python3 gitcleanup.py scan --format json
```

## Commands

| Command | Description |
|---|---|
| `scan` | Scan for merged branches, stale branches, orphaned objects |
| `clean` | Delete merged branches (interactive or `--force`) |
| `prune` | Remove stale remote tracking refs (`git remote prune`) |
| `orphans` | Find orphaned/unreachable objects |

## Options

| Option | Description |
|---|---|
| `--older-than N` | Only consider branches older than N days (default: 90 for scan) |
| `--dry-run` | Show what would happen without making changes |
| `--force` / `-f` | Skip confirmation prompts |
| `--format text\|json` | Output format |
| `--verbose` / `-v` | Show detailed object lists (orphans) |

## License
MIT — see [LICENSE](LICENSE).

---
🧰 **[Tool on Hermtica Marketplace](https://hermtica.com/marketplace)**
