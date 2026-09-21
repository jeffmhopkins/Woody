# P6 — headless environment, install path, reproducibility

**Slice:** getting the KiCad toolchain running in this container and keeping it
reproducible.
**Subject:** `docs/reference/pcb-pipeline.md` (Proposed 2026-09-21, nothing built).
**Method:** cold. Prior review directories not read. Everything below was tested
in the live session where a `[test]` marker says so; `[source]` is KiCad's own
source at a named branch; `[from memory]` is unverified and flagged as such.

**Environment of record:** Ubuntu 24.04.4 noble, x86_64, kernel 6.18.44 `[test:
/etc/os-release, uname -a]`. Outbound HTTPS via agent proxy at
`http://127.0.0.1:36327`.

---

## 1. Verdict on each gotcha

| # | Claim in the plan | Verdict | Evidence |
|---|---|---|---|
| 1 | `pcbnew` lands at `/usr/lib/python3/dist-packages/pcbnew.py` + `_pcbnew.so` | **Correct** | `[test]` |
| 2 | "use system `python3`, or `--system-site-packages`, or `PYTHONPATH=…`" | **Wrong here — all three fail** | `[test]` |
| 3 | "library tables do not exist until a GUI has run once" | **Wrong** | `[source]` |
| 4 | "copy the stock ones from `/usr/share/kicad/template/`" | Path **right**, owning package **wrong**, and the copy is **unnecessary** | `[test]` + `[source]` |
| 5 | (slice question) is `KICAD9_FOOTPRINT_DIR`/`_SYMBOL_DIR` a cleaner way? | **No** — they are substituted *inside* the table, not a replacement for it | `[test]` |
| 6 | "`HOME` must be writable" | **Half right** — what must be writable is the config dir, and it is relocatable without touching `HOME` | `[source]` |
| 7 | "`kicad-cli pcb render` needs OpenGL; xvfb + `LIBGL_ALWAYS_SOFTWARE=1`" | **Wrong for KiCad 9** — CPU raytracer into a RAM buffer, no GL context | `[source]` |
| 8 | "Everything else — DRC, gerbers, drill, STEP, SVG — is genuinely headless" | **Correct**, and `render` belongs in this list too | `[source]` |
| 9 | "Ubuntu noble's stock archive has KiCad 7 only" | **Correct** — 7.0.11+dfsg-1build4 | `[test]` |
| 10 | "KiCad 7 has no `kicad-cli pcb drc`" | **Correct** | `[test]` |
| 11 | "needs `*.kicad.org` or `ppa.launchpadcontent.net` allowlisted … this is the one hard network requirement" | **Understated** — it is at least two hosts, and the package names change | `[test]` |
| 12 | Package set `kicad`, `kicad-libraries`, `kicad-footprints`, `kicad-symbols`, `kicad-packages3d` | **Correct for the stock archive, wrong for the PPA** | `[test]` |
| 13 | Freerouting "depending on version" wants GL | **Not verified** — GitHub API access to `freerouting/freerouting` is denied in this session | `[from memory]` |

### 1.1 `pcbnew` install path — correct, but the Python advice is not

The path is right. From the stock `kicad` deb, without installing it `[test]`:

```
$ dpkg-deb -c kicad_7.0.11+dfsg-1build4_amd64.deb | grep -iE "pcbnew\.py|_pcbnew|dist-packages"
-rw-r--r-- ./usr/lib/python3/dist-packages/pcbnew.py
lrwxrwxrwx ./usr/lib/python3/dist-packages/_pcbnew.so -> ../../../bin/_pcbnew.kiface
-rw-r--r-- ./usr/lib/kicad/_pcbnew.kiface            (35 MB)
```

The remedy is wrong in this container. `python3` on `PATH` is **not** noble's
system interpreter `[test]`:

```
$ which -a python3
/usr/local/bin/python3
/usr/bin/python3
$ python3 -V
Python 3.11.15
$ ls /usr/bin/python3.*
python3.10  python3.11  python3.12  python3.13
```

(A `deadsnakes` PPA is configured in `/etc/apt/sources.list.d/` `[test]`, which is
where the extra interpreters come from.)

And the extension module is hard-linked against 3.12 `[test]`:

```
$ readelf -d usr/lib/kicad/_pcbnew.kiface | grep -i python
 (NEEDED)  Shared library: [libpython3.12.so.1.0]
```

So:

- **"use system `python3`"** → picks 3.11, `import pcbnew` fails.
- **`python3 -m venv --system-site-packages`** → a 3.11 venv, same failure.
- **`PYTHONPATH=/usr/lib/python3/dist-packages`** → does nothing useful, and is
  the worst of the three, because `/usr/lib/python3/dist-packages` is **already**
  on `sys.path` for *both* interpreters (Debian patch) `[test]`:

  ```
  $ /usr/bin/python3.12 -c "import sys;print([p for p in sys.path if 'dist' in p])"
  ['/usr/local/lib/python3.12/dist-packages', '/usr/lib/python3/dist-packages']
  $ python3 -c "import sys;print(sys.version.split()[0],[p for p in sys.path if 'dist' in p])"
  3.11.15 ['/usr/local/lib/python3.11/dist-packages', '/usr/lib/python3/dist-packages']
  ```

  `pcbnew.py` is therefore *found* under 3.11 and then dies on the `_pcbnew`
  import with an ELF/ABI error — a confusing failure, not a clean `ModuleNotFoundError`.

**Correct instruction:** name the interpreter explicitly. Every pipeline script
that touches `pcbnew` must run under `/usr/bin/python3.12`, and any venv must be
`/usr/bin/python3.12 -m venv --system-site-packages`. The KiCad 9/10 PPA builds
for noble link the same 3.12 `[from memory]`, so this does not change with the
version bump — but it *would* change on a distro bump, which is one more thing
to pin.

### 1.2 The library tables — the mechanism in the plan is not the real one

The plan says the tables are written by the GUI on first launch and must be
copied by hand. They are not. `FP_LIB_TABLE::LoadGlobalTable()` does it itself,
in library code that `kicad-cli` and `pcbnew` both reach `[source: gitlab.com
kicad/code/kicad ref=9.0, common/fp_lib_table.cpp:622]`:

```cpp
bool FP_LIB_TABLE::LoadGlobalTable( FP_LIB_TABLE& aTable )
{
    wxFileName fn = GetGlobalTableFileName();
    if( !fn.FileExists() )
    {
        if( !wxFileName::DirExists( fn.GetPath() )
            && !wxFileName::Mkdir( fn.GetPath(), 0x777, wxPATH_MKDIR_FULL ) )
            THROW_IO_ERROR( ... "Cannot create global library table path '%s'." );

        SEARCH_STACK ss;  SystemDirsAppend( &ss );
        std::optional<wxString> v = ENV_VAR::GetVersionedEnvVarValue( envVars, wxT("TEMPLATE_DIR") );
        if( v && !v->IsEmpty() ) ss.AddPaths( *v, 0 );
        wxString fileName = ss.FindValidPath( FILEEXT::FootprintLibraryTableFileName );

        // The fallback is to create an empty global footprint table ...
        if( fileName.IsEmpty() || !::wxCopyFile( fileName, fn.GetFullPath(), false ) )
        {
            FP_LIB_TABLE emptyTable;
            emptyTable.Save( fn.GetFullPath() );
        }
    }
    aTable.Load( fn.GetFullPath() );
```

Three things follow, and they matter more than the gotcha as written:

1. **The copy is automatic**, sourced from `${KICAD9_TEMPLATE_DIR}`, whose
   default is `PATHS::GetStockTemplatesPath()` `[source: common/settings/common_settings.cpp,
   COMMON_SETTINGS::InitializeEnvironment]` — `/usr/share/kicad/template` on a
   Debian install. A `setup.sh` `cp` is redundant.
2. **The dangerous case is silent, not loud.** If the template is not found,
   the fallback writes an **empty** table and carries on. Nothing errors. Every
   footprint then fails to resolve, with a message pointing at the footprint,
   not at the missing library package. That is the gotcha worth writing down.
3. **The real `HOME` requirement** is the `Mkdir` above: the config directory's
   parent must be creatable, or you get a thrown `IO_ERROR`. See §1.4.

### 1.3 `/usr/share/kicad/template/` — right path, wrong package

`kicad-templates` does **not** ship the global tables `[test]`. It ships page-layout
worksheets and per-project starter templates:

```
$ dpkg-deb -c kicad-templates_7.0.9-1_all.deb | grep -iE "lib-table"
./usr/share/kicad/template/Arduino_Mega/fp-lib-table      (161 bytes — project-local)
./usr/share/kicad/template/Arduino_Micro/fp-lib-table
...
```

The global tables come from the *library* packages `[test]`:

```
$ dpkg-deb -c kicad-footprints_7.0.11-1_all.deb | grep "share/kicad/template"
-rw-r--r-- 21405 ./usr/share/kicad/template/fp-lib-table
$ dpkg-deb -c kicad-symbols_7.0.11-1_all.deb | grep "share/kicad/template"
-rw-r--r-- 32629 ./usr/share/kicad/template/sym-lib-table
```

So the `setup.sh` failure mode is *not* "forgot to copy the tables" — it is
"installed `kicad` and `kicad-templates` but not `kicad-footprints`", which
lands you in the silent-empty-table case of §1.2.

### 1.4 `HOME` — and the better knob

`kicad-cli`/`pcbnew` need a writable **config** directory, not a writable `HOME`
as such. KiCad 9 resolves it as `[source: common/paths.cpp,
PATHS::CalculateUserSettingsPath]`:

```cpp
if( aUseEnv && wxGetEnv( wxT( "KICAD_CONFIG_HOME" ), &envstr ) && !envstr.IsEmpty() )
    cfgpath.AssignDir( envstr );
else
{
    cfgpath.AssignDir( KIPLATFORM::ENV::GetUserConfigPath() );   // XDG → $HOME/.config
    cfgpath.AppendDir( TO_STR( KICAD_CONFIG_DIR ) );             // "kicad"
}
if( aIncludeVer ) cfgpath.AppendDir( GetMajorMinorVersion() );   // "9.0"
```

Note the asymmetry, which is easy to get wrong: with `KICAD_CONFIG_HOME` set,
the `kicad` path component is **not** appended. So

- default: `$HOME/.config/kicad/9.0/fp-lib-table` (the plan's path — correct)
- `KICAD_CONFIG_HOME=/work/kicfg`: `/work/kicfg/9.0/fp-lib-table`

Two sibling knobs exist and are worth setting in a build: `KICAD_CACHE_HOME`
`[source: PATHS::GetUserCachePath]` and `KICAD_DOCUMENTS_HOME`
`[source: paths.cpp:46]`. All three are plain `wxGetEnv` reads.

**Recommendation:** set `KICAD_CONFIG_HOME` and `KICAD_CACHE_HOME` to paths
under the build tree rather than relying on `HOME`. It makes the config state a
build artifact you can delete and recreate, which is exactly what a
"re-runnable forever" pipeline wants, and it removes a whole class of "it worked
on my machine because my `HOME` had a stale table in it".

### 1.5 `KICAD9_FOOTPRINT_DIR` is not an alternative to the table

The slice asked whether the env vars are a cleaner path than the lib tables.
They are not — they are *consumed by* the table `[test]`:

```
$ tar -xO ./usr/share/kicad/template/fp-lib-table | head -2
(fp_lib_table
  (lib (name Audio_Module)(type Kicad)(uri ${KICAD7_FOOTPRINT_DIR}/Audio_Module.pretty) ...
$ ... | grep -oE '\$\{[A-Z0-9_]+\}' | sort -u
${KICAD7_FOOTPRINT_DIR}
```

Same for `${KICAD7_SYMBOL_DIR}` in `sym-lib-table` `[test]`. Set the env var with
no table and no library is declared at all. The env var's use is to *redirect* an
existing table at a pinned library checkout — which is a real and useful thing
to do (see §3.2), just not the thing the plan needed.

The name is built at runtime from the running major version `[source:
common/env_vars.cpp]`:

```cpp
wxString ENV_VAR::GetVersionedEnvVarName( const wxString& aBaseName )
{
    int version = 0;
    std::tie(version, std::ignore, std::ignore) = GetMajorMinorPatchTuple();
    return wxString::Format( "KICAD%d_%s", version, aBaseName );
}
```

KiCad 7 → `KICAD7_*`, 9 → `KICAD9_*`, 10 → `KICAD10_*`. This is a pinning hazard
in its own right: see §3.2.

### 1.6 `pcb render` does not need OpenGL

`kicad-cli pcb render` in KiCad 9 runs `RENDER_3D_RAYTRACE_RAM` — a CPU
raytracer that writes into a heap buffer, with no canvas and no GL context
`[source: pcbnew/pcbnew_jobs_handler.cpp, JobExportRender]`:

```cpp
wxSize     windowSize( aRenderJob->m_width, aRenderJob->m_height );
TRACK_BALL camera( 2 * RANGE_SCALE_3D );
RENDER_3D_RAYTRACE_RAM raytrace( boardAdapter, camera );
raytrace.SetCurWindowSize( windowSize );
for( bool first = true; raytrace.Redraw( false, m_reporter, m_reporter ); first = false ) { ... }
uint8_t* rgbaBuffer = raytrace.GetBuffer();
```

`3d-viewer/3d_rendering/raytracing/render_3d_raytrace_ram.h` contains no GL
reference at all `[test: grep -c "GL\|gl\." → 0]`. The `_RAM` variant exists
precisely so the CLI does not need a context.

`xvfb-run -a` around it is harmless but it is cargo cult, and it costs
credibility on the rest of the list. **It also hides the real cost:** software
raytracing a board at default quality is CPU-minutes, not seconds `[from memory]`,
which matters far more for a bounded session than the display does.

`xvfb` itself does work here and is already installed `[test]`:

```
$ xvfb-run -a sh -c 'echo DISPLAY=$DISPLAY'
DISPLAY=:99
```

Keep `xvfb` in the stack for Freerouting (unverified, §1.8) — not for `render`.

### 1.7 KiCad 7 in noble, and `pcb drc`

Both correct `[test]`:

```
$ apt-cache policy kicad
kicad:
  Candidate: 7.0.11+dfsg-1build4
     500 http://archive.ubuntu.com/ubuntu noble/universe amd64 Packages
```

And the KiCad 7 `kicad-cli` binary contains none of the DRC job's strings
`[test: strings on ./usr/bin/kicad-cli from the deb]`:

| probe | count |
|---|---|
| `severity-error` | 0 |
| `exit-code-violations` | 0 |
| `schematic-parity` | 0 |
| `pcb drc` | 0 |
| `pcb render` | 0 |
| `drill-origin` | 1 |

So KiCad 7 can plot gerbers and drill but cannot run the verify stage. The plan's
conclusion stands.

### 1.8 Freerouting — not verified

`https://api.github.com/repos/freerouting/freerouting/releases` returns 403
("GitHub access to this repository is not enabled for this session") and the
`add_repo` call to enable it was denied `[test]`. Java 21 is present
(`openjdk 21.0.10`) `[test]`. Whether Freerouting 2.x needs a display is
**unverified**; treat the plan's `xvfb-run` there as an untested assumption and
prove it in `pcb/smoke/` as the plan already intends. `-Djava.awt.headless=true`
is the cheaper thing to try first `[from memory]`.

---

## 2. Install recipe

Tested as far as this environment allows. The KiCad 9 steps cannot be executed
here (blocked host, §2.1) — they are marked as such, and everything *around*
them was verified.

### 2.1 Network: it is two blocked hosts, not one

The plan names `*.kicad.org` or `ppa.launchpadcontent.net`. Measured, through
the agent proxy `[test: curl -o /dev/null -w %{http_code}]`:

| host | code | note |
|---|---|---|
| `archive.ubuntu.com` | 200 | KiCad 7 only |
| `launchpad.net` | 200 | PPA metadata pages readable |
| `keyserver.ubuntu.com` | 200 | signing key fetchable |
| `api.launchpad.net` | **000** | CONNECT 403 |
| `ppa.launchpadcontent.net` | **000** | CONNECT 403 |
| `downloads.kicad.org` | **000** | CONNECT 403 |
| `kicad.org` | **000** | CONNECT 403 (proxy log) |
| `github.com` / `gitlab.com` / `pypi.org` | reachable | |

`add-apt-repository ppa:kicad/kicad-9.0-releases` will fail **even if
`ppa.launchpadcontent.net` is allowlisted**, because it resolves the PPA through
`launchpadlib` against `api.launchpad.net` `[test]`:

```
$ grep -n "service_root" /usr/lib/python3/dist-packages/softwareproperties/ppa.py
112:                                  service_root='production',
$ grep -n LPNET_SERVICE_ROOT /usr/lib/python3/dist-packages/launchpadlib/uris.py
37:LPNET_SERVICE_ROOT = "https://api.launchpad.net/"
```

**The allowlist ask should therefore be: `ppa.launchpadcontent.net` (mandatory),
and either `api.launchpad.net` or nothing — write the source file by hand.**
Writing it by hand is better: it is one fewer host, and it is the version-pinned
form anyway.

### 2.2 The apt source, written by hand

Verified from the PPA page `[test: launchpad.net/~kicad/+archive/ubuntu/kicad-9.0-releases]`.
Signing key fingerprint, read off that page:
`FDA854F61C4D0D9572BB95E5245D5502FAD7A805`.

```sh
# 1. key — keyserver.ubuntu.com is reachable [test]
install -d -m 0755 /etc/apt/keyrings
curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0xFDA854F61C4D0D9572BB95E5245D5502FAD7A805" \
  | gpg --dearmor -o /etc/apt/keyrings/kicad.gpg
# verify it is the key you think it is, do not skip this:
gpg --show-keys --with-fingerprint /etc/apt/keyrings/kicad.gpg   # expect FDA8 54F6 1C4D 0D95 72BB  95E5 245D 5502 FAD7 A805

# 2. source
cat > /etc/apt/sources.list.d/kicad.sources <<'EOF'
Types: deb
URIs: https://ppa.launchpadcontent.net/kicad/kicad-9.0-releases/ubuntu/
Suites: noble
Components: main
Signed-By: /etc/apt/keyrings/kicad.gpg
EOF

# 3. pin — see §3.1; without this the "9.0" you install drifts
cat > /etc/apt/preferences.d/kicad.pref <<'EOF'
Package: kicad kicad-library-*
Pin: version 9.0.9~ubuntu24.04.1
Pin-Priority: 1001
EOF

apt-get update
```

### 2.3 The packages — the names are different in the PPA

This is the concrete error in the plan's package list. The PPA does **not** ship
`kicad-libraries`/`kicad-footprints`/`kicad-symbols`/`kicad-packages3d`. Read off
the PPA's noble package listing `[test]`:

| stock archive (KiCad 7) | KiCad PPA (9.0.9~ubuntu24.04.1) |
|---|---|
| `kicad` | `kicad` |
| `kicad-libraries` | `kicad-library-all` |
| `kicad-footprints` | `kicad-library-footprints` |
| `kicad-symbols` | `kicad-library-symbols` |
| `kicad-templates` | `kicad-library-templates` |
| `kicad-packages3d` | `kicad-library-packages3d` |
| `kicad-demos` | — |
| — | `kicad-doc` |

A `setup.sh` written against the stock names will `apt-get install` its way to
`E: Unable to locate package kicad-footprints` after the PPA is added. Given
§1.2/§1.3, *that specific failure* — footprints package absent — is the one that
degrades to a silently empty library table.

**Install:**

```sh
apt-get install -y --no-install-recommends \
    kicad kicad-library-symbols kicad-library-footprints kicad-library-templates \
    xvfb
# kicad-library-packages3d ONLY if STEP-with-components or render is wanted — see §4
```

`kicad-library-all` is a metapackage; naming the three real ones is better
because it makes the `packages3d` omission deliberate and visible.

### 2.4 Environment

```sh
export KICAD_CONFIG_HOME="$PWD/pcb/.kicad-config"   # → .../9.0/fp-lib-table [source §1.4]
export KICAD_CACHE_HOME="$PWD/pcb/.kicad-cache"
export PCB_PYTHON=/usr/bin/python3.12               # NOT `python3` — §1.1
# do NOT set PYTHONPATH; dist-packages is already on 3.12's sys.path [test]
```

and a guard at the top of `setup.sh` that actually catches the §1.1 and §1.2
failures instead of discovering them at stage 2:

```sh
"$PCB_PYTHON" - <<'EOF'
import sys, pcbnew, os
print("pcbnew", pcbnew.GetBuildVersion(), "under", sys.version.split()[0])
EOF
test -s /usr/share/kicad/template/fp-lib-table  || { echo "no stock fp-lib-table: kicad-library-footprints missing"; exit 1; }
test -s /usr/share/kicad/template/sym-lib-table || { echo "no stock sym-lib-table: kicad-library-symbols missing";   exit 1; }
```

The two `test -s` lines are the important ones. They convert the silent
empty-table path of §1.2 into a failure at install time.

### 2.5 What could not be tested

- No KiCad 9 was installed: `ppa.launchpadcontent.net` is 403 `[test]`, and the
  disk is not a safe place to try (§4.3). Everything in §2.2–§2.4 that concerns
  KiCad 9 rests on `[source]` reading of the 9.0 branch and `[test]` on the
  KiCad 7 debs, not on a running KiCad 9.
- Whether the PPA's `kicad` deb links `libpython3.12` — `[from memory]`, though
  it must, since noble's `python3` is 3.12.

---

## 3. Reproducibility gaps the plan does not address, ranked

The plan says the pipeline is "re-runnable forever". Four things break that, in
descending order of how expensive they are to discover late.

### 3.1 Nothing pins KiCad, and the PPA is a moving target — HIGH

`ppa:kicad/kicad-9.0-releases` is a *series*, not a version. Its current noble
build is `9.0.9~ubuntu24.04.1` `[test]`; the Docker Hub tag history for the same
upstream shows that series walking 9.0.0 (2025-02-22) → 9.0.9 (2026-05-03) `[test:
hub.docker.com/v2/repositories/kicad/kicad/tags]`. `apt-get install kicad` from
that source gives you a different KiCad in six months.

Worse, there is now a `kicad-10.0-releases` PPA carrying `10.0.6~ubuntu24.04.1`
for noble `[test]`. The plan's stack table says "KiCad 9" — as of today that is
already one major behind, which means the plan is choosing an old version
without saying it is choosing.

**Fix:** pin the exact version in `apt/preferences.d` (§2.2) *and* record it as a
tracked figure. Launchpad removes superseded binaries from a PPA's published
archive after a while `[from memory — not verifiable here, the host is blocked]`,
so a version pin is necessary but not sufficient; see §4.2 for the durable
answer.

### 3.2 A KiCad major bump renames every env var and rewrites the board file — HIGH

Two separate mechanisms, both invisible until they bite.

**Env vars.** `KICAD<major>_FOOTPRINT_DIR` is generated from the running version
`[source §1.5]`. A `fp-lib-table` checked into the repo under KiCad 9 contains
`${KICAD9_FOOTPRINT_DIR}` in every row. Run KiCad 10 against it and every one of
those substitutions is undefined — and the failure presents as "footprint not
found", not as "your table is for the wrong major".

**Board file format.** KiCad rewrites `.kicad_pcb` to the running version's
format on save. `[source: pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.h at each
release branch]`:

| branch | `SEXPR_BOARD_FILE_VERSION` |
|---|---|
| 8.0 | `20240108` |
| 9.0 | `20241229` |
| 10.0 | `20260206` |
| master | `20260901` |

KiCad 7's own binary carries the warning string for this `[test: strings on
_pcbnew.kiface]`: *"This file was created by an older version of KiCad. It will
be converted to the new format when saved."*

This is a real hazard for this repo specifically, because the pipeline **writes**
the board every run — `route.py` imports the SES, `pour.py` fills zones and
saves. So a `.kicad_pcb` in git is not an inert artifact; it is a file whose
on-disk format is a function of whichever KiCad the last run happened to have.
One run under a bumped KiCad produces a whole-file diff and a board the previous
KiCad can no longer open. That is the project's named failure mode — a value
changes and the derived thing follows silently — expressed in a file format.

**Fix:** pin the major explicitly, put `kicad_version` in `config/figures.yaml`
with its `forbidden` list, and have `verify.py` assert the board's `(version …)`
token matches the pinned KiCad before it does anything else. That last check is
three lines and it is the only one that catches the bump on the run that causes
it.

### 3.3 Gerber and drill output is not byte-reproducible — MEDIUM

Two identical runs will **not** produce identical files. KiCad stamps the
generation time into both formats `[test: strings on
usr/lib/kicad/_pcbnew.kiface from the stock deb]`:

```
G04 Created by KiCad (%s) date %s*        <- every gerber
; DRILL file {%s} date %s                 <- every Excellon drill file
%%%%CreationDate: %s                      <- PostScript plotter
/CreationDate (%s)                        <- PDF plotter
```

And there is no opt-out: `SOURCE_DATE_EPOCH` appears **zero** times in either
`kicad-cli` or `_pcbnew.kiface` `[test: strings … | grep -c SOURCE_DATE_EPOCH → 0]`.

Consequences the plan should state:

- `fab/<board>/*.gbr` cannot be committed and diffed usefully; every re-export is
  a diff on every file.
- "re-runnable forever" cannot mean "produces the same bytes". It can only mean
  "produces the same geometry".
- A zip of gerbers has no stable checksum, so you cannot prove the zip you sent
  the fab is the zip the pipeline produces today.

**Fix:** a `tools/normalize-gerbers.py` that strips the two date lines before
hashing/committing, and make the pipeline's re-runnability claim about the
*normalized* output. Then a `MANIFEST.csv` with SHA-256 over the normalized set
— which is exactly the mechanism `datasheets/` already uses and the one rule in
this repo that demonstrably works.

### 3.4 Python interpreter drift — MEDIUM

`python3` here is 3.11.15 from `/usr/local/bin`, while the distro's is 3.12 and
`pcbnew` is bound to 3.12 (§1.1). Nothing in the plan pins an interpreter. A
`requirements.txt` for SKiDL/kiutils/PySpice resolved under 3.11 and a `pcbnew`
that only loads under 3.12 is two Pythons in one pipeline, which is a drift
source the moment anyone adds a dependency that both stages import.

**Fix:** one interpreter, named. `/usr/bin/python3.12 -m venv --system-site-packages
pcb/.venv`, a hash-pinned `requirements.txt` (`pip install --require-hashes`),
and a `setup.sh` assertion that `sys.version_info[:2] == (3, 12)`.

---

## 4. Container vs `setup.sh`

**Recommendation: a `Dockerfile` is the right artifact to commit; `setup.sh` is
the right thing to run today. Write the `Dockerfile` first and generate
`setup.sh` from it, not the reverse.**

The reasoning is not about convenience. §3.1 and §3.2 are unfixable by a shell
script: a script says "install kicad", and what that means changes under it. An
image digest does not change. `kicad/kicad:9.0.9` pins to
`sha256:cef4a572df1465b98fa63cdac88780e0f8d39f03c5493434802bcd92f62123fb` `[test:
hub.docker.com tags API]`, and that is the only artifact in this whole discussion
that satisfies "re-runnable forever" literally.

### 4.1 But it does not work in this session

Docker CLI 29.3.1 is installed, `dockerd` is present, and the daemon **does**
start `[test]`:

```
$ dockerd --iptables=false --bridge=none
... msg="Daemon has completed initialization"
... msg="API listen on /var/run/docker.sock"
$ docker info | grep -E "Server Version|Storage Driver|Cgroup Version"
 Server Version: 29.3.1
 Storage Driver: overlayfs
 Cgroup Version: 1
```

Pulls fail. Registry manifests are reachable; the **blob CDNs are 403** `[test]`:

```
$ docker pull hello-world
failed to copy: ... Get "https://production.cloudfront.docker.com/registry-v2/...": Forbidden

$ curl -H "Authorization: Bearer $TOK" https://ghcr.io/v2/inti-cmnb/kicad9_auto/manifests/latest
HTTP 200                                        # manifest fine
$ curl -L ... https://ghcr.io/v2/inti-cmnb/kicad9_auto/blobs/sha256:f3ad29...
curl: (56) CONNECT tunnel failed, response 403   # redirected to pkg-containers.githubusercontent.com
```

| host | result |
|---|---|
| `registry-1.docker.io` | 404 (reachable) |
| `auth.docker.io` | token issued |
| `hub.docker.com` | 200 |
| `ghcr.io/v2/` | 401 (reachable) |
| `registry.gitlab.com/v2/` | 401 (reachable) |
| `production.cloudfront.docker.com` | **403** |
| `pkg-containers.githubusercontent.com` | **403** |

So "just use a container" needs an allowlist change too — a *different* one from
the PPA ask, and the plan's network section names neither. If an allowlist
request is going to be made anyway, `production.cloudfront.docker.com` buys more
than `ppa.launchpadcontent.net` does, because it also pins.

### 4.2 The option that needs no allowlist at all

Bank the `.deb` files the way `datasheets/` banks documents: one `MANIFEST.csv`
row per file with a SHA-256, fetched once from wherever they can be fetched, and
`tools/verify-debs.py` before any install. This is the project's own rule 3
applied to the toolchain, it is immune to both the PPA rolling and the archive
dropping superseded binaries, and it works behind the current policy once the
files are in hand.

Cost: roughly 120–200 MiB of `.deb` for a KiCad 9 install without 3D models
(extrapolated from the measured KiCad 7 closure, §4.3) — too much for git
proper, fine for LFS or an out-of-tree bank with the manifest in git.

### 4.3 Disk

Measured, stock-archive KiCad 7 (the PPA cannot be measured from here) `[test:
apt-get install -s kicad → 46 packages, summed Size/Installed-Size from
apt-cache show]`:

| set | download | installed |
|---|---|---|
| `kicad` + full dependency closure (46 pkgs, incl. symbols, footprints, templates, demos, OCCT, wx) | **113.3 MiB** | **695.2 MiB** |
| `kicad-packages3d` alone (**not** in the above closure) | **404.5 MiB** | **5 575 MiB (5.44 GiB)** |

Per-package `[test]`:

| package | download | installed |
|---|---|---|
| `kicad` | 34.4 MiB | 142.8 MiB |
| `kicad-footprints` | 21.6 MiB | 143.8 MiB |
| `kicad-symbols` | 2.3 MiB | 166.9 MiB |
| `kicad-templates` | 1.0 MiB | 2.6 MiB |
| `kicad-demos` | 3.2 MiB | 26.1 MiB |
| `kicad-libraries` (metapackage) | 0.03 MiB | 0.1 MiB |
| **`kicad-packages3d`** | **404.5 MiB** | **5 575.5 MiB** |

Container images, compressed, for comparison `[test: hub.docker.com]`:

| tag | compressed |
|---|---|
| `kicad/kicad:9.0.9` | 454 MiB |
| `kicad/kicad:9.0.9-full` (with 3D) | 1 060 MiB |
| `kicad/kicad:10.0.5` | 771 MiB |

**Does the pipeline need `kicad-packages3d`?** Partly, and the plan's own stated
purpose is the expensive half.

- Gerbers, drill, DRC, SVG: **no**.
- `pcb render`: yes.
- `pcb export step`: **yes, as the plan uses it.** The STEP exporter resolves
  each footprint's 3D model file unless `--board-only` is passed `[source:
  pcbnew/exporters/step/exporter_step.cpp:327,369]`. The plan's reason for STEP
  is "mechanical fit against the panel and enclosure", which is exactly the case
  that needs component bodies — a board-only STEP is an outline and holes.

So the honest statement is: **the fab deliverable costs 695 MiB; the mechanical
check costs 6.3 GiB.** Split them. Run gerbers/drill/DRC in the small install
every time; run STEP/render as a separate, occasional stage — ideally in the
`-full` container, which is 1 060 MiB compressed rather than 6.3 GiB unpacked.

**On the "fixed per-session allowance":** there is no quota. `/` is a single
252 GiB ext4 shared with everything else in the session `[test: findmnt -no
SOURCE,FSTYPE,SIZE,AVAIL /` → `/dev/vda ext4 252G`]. Free space moved as follows
**during this review**, with no action of mine beyond downloading ~60 MiB of debs
`[test: repeated df -h /]`:

```
17:02   7.9G avail     (79% used)
17:08   3.4G avail     (91% used)   <- tool output failed with ENOSPC here
17:34  19.0G avail     (52% used)
17:46  23.0G avail     (40% used)
```

The 3.4 GiB point is below what `kicad-packages3d` needs to unpack. **You cannot
plan a 5.4 GiB install against a figure that moved 15 GiB in half an hour.**
Anything that needs the 3D models must check free space immediately before
unpacking and fail with a clear message, not discover it mid-`dpkg`.

---

## 5. Summary of defects filed

| id | node | defect | severity |
|---|---|---|---|
| P6-1 | `setup.sh` / python | `python3` is 3.11; `_pcbnew.so` needs `libpython3.12`. All three remedies in the plan fail. Must name `/usr/bin/python3.12`. | **blocking** |
| P6-2 | `setup.sh` / apt | PPA package names are `kicad-library-*`, not `kicad-footprints`/`kicad-symbols`/`kicad-packages3d`. Install will fail on the names the plan implies. | **blocking** |
| P6-3 | network | `add-apt-repository` also needs `api.launchpad.net` (blocked). Allowlist ask is incomplete; write the `.sources` file by hand instead. | high |
| P6-4 | `setup.sh` / lib tables | The GUI-writes-the-tables premise is wrong. The real hazard is the silent empty-table fallback when `kicad-library-footprints` is absent; add the two `test -s` guards. | high |
| P6-5 | version pinning | Nothing pins KiCad. PPA series rolls (9.0.0 → 9.0.9 observed); KiCad 10.0.6 is now the noble PPA current. | high |
| P6-6 | `.kicad_pcb` in git | Board format version changes per major (8.0 `20240108`, 9.0 `20241229`, 10.0 `20260206`) and the pipeline saves the board every run. Needs a `(version …)` assertion in `verify.py`. | high |
| P6-7 | `fab/**` | Gerber and Excellon output carries a generation timestamp; no `SOURCE_DATE_EPOCH` support. "Re-runnable" cannot mean byte-identical without a normalizer. | medium |
| P6-8 | `pcb render` | Does not need OpenGL in KiCad 9 (`RENDER_3D_RAYTRACE_RAM`). The `xvfb`/`LIBGL_ALWAYS_SOFTWARE` advice is cargo cult and hides the real cost (CPU time). | medium |
| P6-9 | disk | `kicad-packages3d` is 5.44 GiB installed and is needed for the plan's stated STEP purpose. Free space on `/` moved 3.4→23 GiB during this review; there is no per-session quota to plan against. | medium |
| P6-10 | `/usr/share/kicad/template/` | Tables ship in `kicad-footprints`/`kicad-symbols`, not `kicad-templates`. Cosmetic on its own, load-bearing via P6-4. | low |
| P6-11 | Freerouting | GL requirement unverified — GitHub API access denied this session. Flag as untested in the plan rather than asserting it. | low |

## 6. What I could not check

- Any KiCad 9 or 10 binary. `ppa.launchpadcontent.net` and `downloads.kicad.org`
  are 403; container blobs are 403. All KiCad 9 statements above are `[source]`
  from the 9.0 branch on gitlab.com or `[test]` on the KiCad 7 debs, and are
  labelled as such.
- Freerouting (§1.8).
- Whether Launchpad drops superseded PPA binaries (§3.1) — the host is blocked.
