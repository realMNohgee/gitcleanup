# GitCleanup 🧹

**Find and clean up merged branches, stale remote refs, and orphaned objects.** Zero dependencies, pure Python stdlib.

Keep your git repos lean. Scan for branches that have been merged (or are just stale), prune dead remote tracking refs, identify orphaned objects wasting disk space, and get interactive cleanup with intelligent scheduling recommendations. Reports estimated space savings and generates Slack/Discord notifications.

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
| 📢 **Notifications** | Generate cleanup summaries for team channels |

## v2 Features

### Interactive Branch Selection
When running `clean` without `--force`, shows a numbered list and lets you pick which branches to delete by number:
```bash
python3 gitcleanup.py clean
# 1. feature/old-login    age: 45d
# 2. fix/typo             age: 30d
# Delete which? [numbers / all / none] 1
```

### Remote Branch Scanning
Check remote branches too with `--remote`:
```bash
python3 gitcleanup.py scan --remote
```

### Notify Command
Generate a text summary for Slack/Discord copy-paste:
```bash
python3 gitcleanup.py notify
```

### Schedule Command
Get a suggested cleanup schedule based on repo activity patterns:
```bash
python3 gitcleanup.py schedule
# 📅 Suggested Cleanup Schedule
#   Recommended: weekly
#   Reason: many stale branches detected
```

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

# v2: Include remote branches
python3 gitcleanup.py scan --remote

# Preview what would be deleted
python3 gitcleanup.py clean --dry-run

# Delete merged branches (interactive with numbered selection)
python3 gitcleanup.py clean

# Delete merged branches (non-interactive)
python3 gitcleanup.py clean --force

# Prune stale remote refs
python3 gitcleanup.py prune

# Find orphaned objects
python3 gitcleanup.py orphans --verbose

# v2: Generate cleanup notification
python3 gitcleanup.py notify

# v2: Get schedule recommendation
python3 gitcleanup.py schedule

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
| `notify` | Generate cleanup summary for Slack/Discord (v2) |
| `schedule` | Suggest cleanup schedule based on repo activity (v2) |

## Options

| Option | Description |
|---|---|
| `--older-than N` | Only consider branches older than N days (default: 90 for scan) |
| `--dry-run` | Show what would happen without making changes |
| `--force` / `-f` | Skip confirmation prompts |
| `--remote` | Also check remote branches (v2) |
| `--format text\|json` | Output format |
| `--verbose` / `-v` | Show detailed object lists (orphans) |

## License
MIT — see [LICENSE](LICENSE).

---
🧰 **[Tool on Hermtica Marketplace](https://hermtica.com/marketplace)**
