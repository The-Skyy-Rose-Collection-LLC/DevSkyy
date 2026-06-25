# SKYYROSE-THEME — CLI Harness Design Document

## Phase 1: Analysis

### Theme Dev Loop — Current State

The SkyyRose theme dev loop spans four distinct operations, each with a separate
invocation path:

| Operation | Current path | Pain points |
|-----------|-------------|-------------|
| Deploy | `bash scripts/deploy-theme.sh` or `npm run deploy` | No manifest preview, no --dry-run UX outside npm |
| PHP lint | `cd wordpress-theme/skyyrose-flagship && vendor/bin/phpcs --standard=.phpcs.xml` | Long path, no single-command fix |
| Version bump | Manual edit of 3 files: functions.php, style.css, readme.txt | Error-prone, files can drift |
| Cache flush | `ssh skyyrose.wordpress.com@ssh.wp.com "/usr/local/bin/wp cache flush --path=/srv/htdocs"` | Raw SSH, easy to typo |

**Version drift is the highest-risk gap.** All three files must agree on the
version string, but they're independent. A deploy with a mismatch version shows
the wrong version in WP Admin and the ThemeForest changelog.

**No single verify command.** After deploy, manual `curl` is needed to check
the live site. The deploy script has `verify_live()` but it's internal to bash.

### Template Discovery Gap

`inc/enqueue.php` has a `$template_map` PHP array mapping template filenames
to slugs. No tooling exists to query it programmatically. Agents writing
template-specific CSS/JS rules have to read PHP manually.

### Confirmation Gap

`deploy-theme.sh` has no interactive confirmation step — it just executes. The
only safety is `--dry-run`. The STOP-AND-SHOW protocol in CLAUDE.md plugs this
at the CLI layer.

---

## Phase 2: Architecture

### Design Decisions

**Namespace package.** `cli_anything/` has no `__init__.py`. Uses
`find_namespace_packages(include=["cli_anything.*"])` so multiple cli-anything
harnesses can coexist in the same Python environment.

**Backend orchestration strategy.** The CLI is a thin orchestration layer —
it constructs subprocess argv lists, validates preconditions, and reports
results. It never reimplements deploy logic, PHPCS rules, or WordPress cache
invalidation. The real tools own those semantics.

**Version atomicity.** Three files are written sequentially (not in a true
3-phase commit). Precondition: all three must agree before any write starts.
On partial failure: re-run `version bump --to <old-version>` to restore
consistency. Atomic per-file writes (temp + fsync + os.replace) prevent
torn files.

**STOP-AND-SHOW at the CLI layer.** `build_deploy_manifest()` always returns
a structured dict. `run_deploy(confirmed=False)` raises `DeployNotConfirmedError`
before touching subprocess. The CLI prints the manifest and exits 0 unless
`--confirm` is present. This mirrors the protocol defined in CLAUDE.md.

**REPL default.** `invoke_without_command=True` on the root Click group falls
through to `ctx.invoke(repl)`. The REPL dispatches lines as `cli.main(args, ...)`,
giving full command access without spawning subprocesses.

**Session persistence.** `_locked_save_json` (fcntl.flock + temp + fsync +
os.replace) prevents corruption from concurrent REPL instances. Sessions live
in `~/.cli_anything/skyyrose_theme/sessions/`.

### Module Map

```
skyyrose_theme_cli.py     Click root group, REPL, CliState, emit()
core/version.py           VersionState, read_version(), write_version()
core/template.py          TemplateInfo, TemplateMap, load_templates()
core/deploy.py            DeployManifest, build_deploy_manifest(), run_deploy()
core/verify.py            UrlCheckResult, VerifyReport, verify_live()
core/session.py           Session, _locked_save_json(), CRUD helpers
utils/theme_backend.py    ThemeContext, DoctorReport, run_phpcs(), run_wp_ssh()
utils/php_parser.py       Regex extractors for PHP source text
utils/repl_skin.py        ReplSkin — ANSI rose-gold terminal UI
```

### Exception Hierarchy

```
BackendError
  PHPCSNotFoundError
  PHPNotFoundError
  SSHNotReachableError
  WPCliError

DeployError
  DeployScriptNotFoundError
  DeployNotConfirmedError
  DeployFailedError

VerifyError
  VerifyFailedError

VersionError
  VersionMismatchError

SessionError
  SessionNotFoundError

TemplateError
```

### Known Gaps

1. **wp-cli cache flush not tested offline.** `run_wp_ssh()` requires a live
   SSH connection. Unit tests mock `subprocess.run`. E2E test is gated on
   `SKYYROSE_E2E=1` + SSH reachability.

2. **Version rollback is manual.** If `write_version("1.6.0")` succeeds on
   functions.php but fails on style.css, the user must run
   `version bump --to 1.5.20` to restore consistency. No auto-rollback.

3. **REPL line parsing is naïve split.** `line.split()` doesn't handle quoted
   arguments (e.g., `version bump --to "1.5.21"`). Use `shlex.split()` in a
   future iteration.

4. **No completion.** Tab-completion via `click_completion` or
   `shell_complete` is not wired. Add `COMP_WORDS` integration as Phase 3.

5. **No deploy lock.** Concurrent deploys from two terminals can race.
   A `~/.cli_anything/skyyrose_theme/deploy.lock` file with `fcntl.flock`
   would close this.

### Deploy Prerequisites Checklist

Before `deploy --confirm` is safe to run:

- [ ] `doctor` — all critical checks pass (theme_root, style_css, functions_php, deploy_script)
- [ ] `version current` — all three sources agree
- [ ] SSH key `~/.ssh/skyyrose-deploy` loaded and authorized on `ssh.wp.com`
- [ ] `SKYYROSE_DEPLOY_SCRIPT` points to the real `scripts/deploy-theme.sh`
- [ ] Last `lint php` returned zero violations (or violations are acknowledged)
- [ ] `verify` passes against current production (pre-deploy baseline)
