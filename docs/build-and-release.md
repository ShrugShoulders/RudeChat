# Build and release

This page covers how RudeChat gets packaged and shipped. It reads the build files as they are on the `RudeChat4.2` branch. Where the files disagree with each other or don't say enough to decide, the page says so. For running the app from source, see [development.md](development.md).

## Build files at a glance

| File | Role |
| --- | --- |
| [`setup.py`](../setup.py) | setuptools script. Also configures py2app, but only when it runs on macOS. |
| [`pyproject.toml`](../pyproject.toml) | setuptools metadata, package data and the `rudechat` script. |
| [`requirements.txt`](../requirements.txt) | Runtime dependencies, plus `pyinstaller`. |
| [`Manifest.in`](../Manifest.in) | Include rules for source distributions. See the filename note below. |
| [`RudeChat.spec`](../RudeChat.spec) | PyInstaller spec file. Nothing in the repo calls it. |
| [`macBuild.sh`](../macBuild.sh) | Two-line helper that runs py2app and zips the result. |
| [`.github/workflows/build-installers.yml`](../.github/workflows/build-installers.yml) | CI that builds every installer. |
| [`RudeUpdate.py`](../RudeUpdate.py) | A manual upgrade script for pip installs. See [RudeUpdate.py](#rudeupdatepy). |

## Build targets

### pip install (from source)

The README gives this for Linux:

```sh
pip install -r requirements.txt .
```

After it finishes, `rudechat` starts the app. Two files define that command and they don't agree:

- `pyproject.toml` sets `rudechat = "rudechat4.__main__:__main__"` under `[project.scripts]`. That function exists in [`__main__.py`](../src/rudechat4/__main__.py).
- `setup.py` sets `rudechat=rudechat4.__main__:__main__` under `console_scripts`.

`setup.py` also passes `scripts=["src/rudechat4/__main__.py"]`, which installs a second script literally named `__main__.py` into the environment's `bin` folder.

Packaging differences worth knowing:

- `pyproject.toml` lists `packages = ["rudechat4"]` only. `setup.py` uses `find_namespace_packages(where='src')`. Which list setuptools ends up using when both exist isn't something the files settle. The `package-data` globs in `pyproject.toml` (`GUI/*`, `Client/*`, `Components/*`, `Util/*`, `Resources/*/*` and so on) cover the subfolders either way.
- `pyproject.toml` has no `dependencies` field. `setup.py` has `install_requires`. The README tells you to install `requirements.txt` first, which sidesteps the question.
- `requirements.txt` includes `pyinstaller`, which is a build tool. A plain developer install pulls it in too. This is here for GitHub Workflows to build with.
- On macOS, `shared_imports.py` imports `objc`. Neither dependency list names a package that provides it (`pyobjc-core` does, which is outside knowledge, not something in this repo). The py2app build probably brings it in, but I couldn't verify that from the files.

### macOS app with py2app

From the README:

```sh
pip3 install -r requirements.txt
python3 setup.py py2app
```

[`macBuild.sh`](../macBuild.sh) does the same build and then runs `zip -yr dist/RudeChat.app.zip dist/RudeChat.app`. Because the zip command gets a path that starts with `dist/`, the archive stores that `dist/` prefix. The script assumes py2app writes `dist/RudeChat.app`. I didn't build it, so I can't confirm the name.

What `setup.py` configures for py2app:

- Entry script: `src/rudechat4/__main__.py`.
- Icon: `Resources/Icons/rude.icns`.
- Excludes `rubicon` and `setuptools`.
- Bundle ID `io.github.ShrugShoulders.rudechat`, with `CFBundleVersion` and `CFBundleShortVersionString` both set from `VERSION` (`4.2.0`).
- `isMac()` gates the `app`, `options` and `setup_requires` arguments, so on macOS even a plain `pip install .` asks for py2app through `setup_requires`. That's an inference from reading `setup.py`, not something I ran.

The README says the app isn't signed and that you may have to authorize it. Nothing in the repo signs or notarizes it.

### PyInstaller (CI builds)

CI doesn't use `RudeChat.spec`. Every job in the workflow writes a small launcher and calls PyInstaller with flags:

1. A one-line Python command writes `ci_entry.py`. The file calls `runpy.run_module("rudechat4", run_name="__main__")`, with the strings spelled out through `chr()` calls. It runs `rudechat4/__main__.py` as the main module.
2. PyInstaller runs with `--noconfirm --windowed --name rudechat --paths=src --collect-submodules=rudechat4`.
3. `--add-data` copies `src/rudechat4/Resources` and `src/rudechat4/DefaultConfig` into the bundle under `rudechat4/`.
4. The icon comes from `Resources/Icons`, and it varies by target: `rude.icns` on macOS, `rude.ico` on Windows, `rude_icon_round.png` on Linux.

Each job runs `pip install -r requirements.txt pyinstaller` and then `pip install .` before PyInstaller. Which copy of `rudechat4` PyInstaller bundles, the one in `src` (from `--paths=src`) or the installed one, isn't stated in the workflow. They should be identical.

### PyInstaller (local, with RudeChat.spec)

[`RudeChat.spec`](../RudeChat.spec) is an older, hand-written alternative. It differs from the CI flags:

- It names the output `rudechat4`, not `rudechat`.
- It always uses `rude.ico` as the icon, which suits Windows only.
- It adds each `Resources` subfolder to `datas` one by one. If you add a new subfolder under `Resources`, add it here too.
- It also copies the `.py` files of `Client`, `GUI`, `Util` and `Components` in as data.
- It has no macOS `BUNDLE` step, so on a Mac it produces a plain folder, not a `.app`.

Nothing in the README, `macBuild.sh` or the workflow mentions it. The command would be `pyinstaller RudeChat.spec`.

### Linux, Windows and macOS installers from CI

The workflow in [`build-installers.yml`](../.github/workflows/build-installers.yml) is named "Build Cross-Platform Installers". It has four jobs:

| Job | Runs on | Python | Output |
| --- | --- | --- | --- |
| `build-standard` (matrix: macOS, Windows, Debian/Ubuntu) | `macos-latest`, `windows-latest`, `ubuntu-latest` | 3.12 from `actions/setup-python` | `.dmg`, Windows installer, `.deb` |
| `build-fedora-rpm` | `ubuntu-latest` with a `fedora:latest` container | Fedora's `python3` | `.rpm` |
| `build-arch-pkg` | `ubuntu-latest` with an `archlinux:latest` container | Arch's `python`, in a venv at `/opt/venv` | `.pkg.tar.zst` |
| `build-musl-alpine` | `ubuntu-latest` with an `alpine:latest` container | Alpine's `python3`, in a venv with system site packages | `.tar.gz` |

How each package is made:

- **macOS `.dmg`:** `hdiutil create` wraps `dist/rudechat.app` into `release/rudechat-macOS.dmg`. No signing step.
- **Windows:** the job writes an Inno Setup script (`installer.iss`) and runs `iscc`. The script installs to `{autopf}\rudechat`, adds Start menu and desktop icons, and writes `release/rudechat-Windows-Setup.exe`. The workflow doesn't install Inno Setup, so it relies on `iscc` being on the runner already. I can't verify that from the repo.
- **Debian `.deb`:** `dpkg-deb --build` packs the PyInstaller output into `/opt/rudechat`, links it as `/usr/local/bin/rudechat`, and adds a `.desktop` file and a 256 pixel icon. The control file declares `Architecture: amd64`, no dependencies, and `Maintainer: Your Name <you@example.com>`, which is a placeholder.
- **Fedora `.rpm`:** the job writes a spec file by hand, with `%global debug_package %{nil}` and stripping disabled, and runs `rpmbuild -bb`. It copies `~/rpmbuild/RPMS/x86_64/*.rpm` to `release/rudechat-Fedora-x86_64.rpm`.
- **Arch package:** the job creates a `builder` user, writes a `PKGBUILD` and runs `makepkg -f`. The result is `release/rudechat-Arch-x86_64.pkg.tar.zst`.
- **Alpine musl tarball:** Alpine installs PyQt6 from its own packages (`py3-qt6`, plus `py3-requests`, `py3-tzlocal`, `py3-regex`, `py3-aiofiles`). Pip adds `irctokens`, `emoji`, `pyinstaller` and `pytz`, and installs RudeChat with `--no-deps`. The output is `release/rudechat-Linux-musl-x86_64.tar.gz`, which holds `dist/rudechat`.

On Linux runners the standard job first installs `libegl1`, `libxkbcommon-x11-0`, `libxcb-cursor0`, `libdbus-1-3` and `libasound2-dev`. The Fedora and Arch jobs install the matching packages for their distros.

## What triggers CI

The `on:` block has two triggers:

- A push of a tag that matches `v*`.
- `workflow_dispatch`, which means a manual run from the Actions tab.

Pushes to branches and pull requests don't trigger a build.

## Artifacts

Every job uploads its `release/` output with `actions/upload-artifact@v4`:

| Artifact name | File inside |
| --- | --- |
| `installer-macos` | `rudechat-macOS.dmg` |
| `installer-windows` | `rudechat-Windows-Setup.exe` |
| `installer-debian-ubuntu` | `rudechat-Linux-amd64.deb` |
| `installer-fedora-rpm` | `rudechat-Fedora-x86_64.rpm` |
| `installer-arch-pkg` | `rudechat-Arch-x86_64.pkg.tar.zst` |
| `installer-linux-musl` | `rudechat-Linux-musl-x86_64.tar.gz` |

The workflow has no step that creates a GitHub Release or attaches files to one. Someone has to download the artifacts from the workflow run and publish them by hand.

## Where versions are set

Nothing derives one version from another. The values below were read from the files.

| Where | Value | What it controls |
| --- | --- | --- |
| `pyproject.toml`, line 7 | `4.2.0` | Package metadata |
| `setup.py`, line 12 (`VERSION`) | `4.2.0` | py2app bundle version fields only |
| `src/rudechat4/__main__.py`, line 105 | `4.2.0` | `app.setApplicationVersion(...)`, which Qt reports as the app version |
| `src/rudechat4/rude_client.py`, lines 1149, 1153 and 1162 | `RudeChat4.2.0` | Replies to CTCP `VERSION`, the cow greeting and `FINGER` |
| `.github/workflows/build-installers.yml`, lines 72, 110, 150, 158, 162 and 237 | `4.2.0` | Inno Setup `AppVersion`, `.deb` control, `.rpm` spec and tarball name, `PKGBUILD` `pkgver` |

## RudeUpdate.py

[`RudeUpdate.py`](../RudeUpdate.py) is a standalone script for people who installed with `pip` and want a newer version without losing settings. Nothing in the repo runs it: the workflow, `setup.py` and the README don't mention it. You run it by hand with `python RudeUpdate.py`. Ignore this as it is not updated at all to the newer verions of RudeChat.
