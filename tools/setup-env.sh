#!/usr/bin/env bash
# Install everything the body CAD and the schematic pipeline need, on Ubuntu 24.04.
#
#   sudo bash tools/setup-env.sh          # or as root, e.g. from a cloud environment's setup script
#
# Idempotent: re-running it installs only what is missing. Takes ~3 minutes on
# a fresh machine, most of it KiCad. docs/reference/tooling.md says what each
# piece is for and how to use it.
set -euo pipefail

need_apt=()
have() { dpkg -s "$1" >/dev/null 2>&1; }

# --- body CAD (tools/cad.py): OpenSCAD renders headless through xvfb; gmsh
# meshes the vendor STEP files and needs libxft2; poppler reads datasheets.
for p in openscad xvfb libxft2 poppler-utils python3-yaml python3-pip; do
  have "$p" || need_apt+=("$p")
done

# --- schematics (tools/sch.py): KiCad 9 from the KiCad project's own archive.
# Ubuntu's own kicad is 7.0, whose command line has no ERC and whose file
# format is older than the sheets this repository writes.
if ! kicad-cli version 2>/dev/null | grep -q '^9\.'; then
  if [ ! -f /etc/apt/sources.list.d/kicad-9.list ]; then
    key=$(curl -fsS https://api.launchpad.net/1.0/~kicad/+archive/ubuntu/kicad-9.0-releases \
          | python3 -c "import sys,json;print(json.load(sys.stdin)['signing_key_fingerprint'])")
    curl -fsS "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$key" \
      | gpg --dearmor > /etc/apt/trusted.gpg.d/kicad-9.gpg
    echo "deb https://ppa.launchpadcontent.net/kicad/kicad-9.0-releases/ubuntu noble main" \
      > /etc/apt/sources.list.d/kicad-9.list
  fi
  need_apt+=(kicad kicad-symbols)
fi

if [ ${#need_apt[@]} -gt 0 ]; then
  apt-get update -q
  DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends "${need_apt[@]}"
fi

# KiCad's symbol-library table: without it KiCad's ERC warns on every part
# that its library is "not in the current configuration".
mkdir -p "$HOME/.config/kicad/9.0"
[ -f "$HOME/.config/kicad/9.0/sym-lib-table" ] || \
  cp /usr/share/kicad/template/sym-lib-table "$HOME/.config/kicad/9.0/"

# --- Python packages: Pillow stamps renders; gmsh meshes STEP; manifold3d,
# trimesh and numpy run the clash check.
python3 - <<'EOF' || pip install --break-system-packages -q pillow gmsh manifold3d trimesh numpy
import PIL, gmsh, manifold3d, trimesh, numpy
EOF

echo "setup-env: OpenSCAD $(openscad --version 2>&1 | awk '{print $3}'), KiCad $(kicad-cli version)"
