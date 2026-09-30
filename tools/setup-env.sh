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

# --- what this script itself uses before anything else: curl and gpg fetch the
# KiCad archive's key, and neither is in a minimal Ubuntu image.
boot=()
for p in curl gnupg ca-certificates; do
  have "$p" || boot+=("$p")
done
if [ ${#boot[@]} -gt 0 ]; then
  apt-get update -q
  DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends "${boot[@]}"
fi

# --- body CAD (tools/cad.py): OpenSCAD renders headless through xvfb; gmsh
# meshes the vendor STEP files and needs libxft2; poppler reads datasheets.
for p in openscad xvfb libxft2 poppler-utils librsvg2-bin python3-yaml python3-pip; do
  have "$p" || need_apt+=("$p")
done

# --- circuit simulation (tools/sim.py): ngspice 42 from the Ubuntu archive. Raw
# decks through subprocess; not PySpice (hardware/module/pitch-stage/sim/README.md says why).
have ngspice || need_apt+=(ngspice)

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
  need_apt+=(kicad kicad-symbols kicad-footprints)
fi

# The footprint library, whenever the KiCad 9 archive is configured.
[ -f /etc/apt/sources.list.d/kicad-9.list ] && ! have kicad-footprints && need_apt+=(kicad-footprints)

if [ ${#need_apt[@]} -gt 0 ]; then
  apt-get update -q
  DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends "${need_apt[@]}"
fi

# KiCad's library tables: without them KiCad's ERC and DRC warn on every part
# that its library is "not in the current configuration". KiCad itself may
# have written an EMPTY table on first run, so replace one that lists nothing.
mkdir -p "$HOME/.config/kicad/9.0"
for t in sym-lib-table fp-lib-table; do
  if ! grep -q "(lib (name" "$HOME/.config/kicad/9.0/$t" 2>/dev/null; then
    cp "/usr/share/kicad/template/$t" "$HOME/.config/kicad/9.0/$t"
  fi
done

# --- 3D models for tools/pcb.py render. kicad-packages3d is 3 GB, so only the ones
# the boards' footprints name, from KiCad's own library at the release tag. Without
# them kicad-cli renders the parts as nothing, exits 0 and says nothing; pcb.py render
# now refuses instead. Add a line here when a board names a new one (the refusal lists
# it). The KS-33's model is banked in datasheets/; the woody footprints' drawn
# models are in hardware/lib/woody.3dshapes (tools/lib-models.py). The first three
# are the key boards'; the rest the main board's (2026-09-30).
models=/usr/share/kicad/3dmodels
for m in Capacitor_SMD.3dshapes/C_0805_2012Metric.step \
         Resistor_SMD.3dshapes/R_0805_2012Metric.step \
         Package_SO.3dshapes/SOIC-16_3.9x9.9mm_P1.27mm.step \
         Capacitor_SMD.3dshapes/C_1206_3216Metric.step \
         Capacitor_SMD.3dshapes/CP_Elec_10x10.step \
         Capacitor_SMD.3dshapes/CP_Elec_6.3x5.8.step \
         Resistor_SMD.3dshapes/R_1206_3216Metric.step \
         Inductor_SMD.3dshapes/L_0805_2012Metric.step \
         Inductor_SMD.3dshapes/L_Sunlord_SWPA6028S.step \
         Diode_SMD.3dshapes/D_SMA.step \
         Diode_SMD.3dshapes/D_SMC.step \
         Diode_SMD.3dshapes/D_SOD-123.step \
         Diode_SMD.3dshapes/D_SOD-323.step \
         Package_SO.3dshapes/SOIC-8_3.9x4.9mm_P1.27mm.step \
         Package_SO.3dshapes/SOIC-14_3.9x8.7mm_P1.27mm.step \
         Package_TO_SOT_SMD.3dshapes/SOT-23-5.step \
         Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x05_P2.54mm_Vertical.step \
         Converter_DCDC.3dshapes/Converter_DCDC_RECOM_R-78E-0.5_THT.step; do
  if [ ! -s "$models/$m" ]; then
    mkdir -p "$models/$(dirname "$m")"
    curl -fsSL -o "$models/$m.part" "https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/9.0.0/$m"
    mv "$models/$m.part" "$models/$m"
  fi
done

# --- Freerouting for tools/pcb.py's `route: freerouting` (the main board;
# tools/pcb_freeroute.py). v2.1.0 is the last release that runs on Java 21; its
# SHA-256 is checked there.
fr="$HOME/.cache/woody/freerouting-2.1.0.jar"
if [ ! -s "$fr" ]; then
  mkdir -p "$(dirname "$fr")"
  curl -fsSL -o "$fr.part" "https://github.com/freerouting/freerouting/releases/download/v2.1.0/freerouting-2.1.0.jar"
  mv "$fr.part" "$fr"
fi

# --- Python packages: Pillow stamps renders; gmsh meshes STEP; manifold3d,
# trimesh and numpy run the clash check; fontTools, shapely and ezdxf set the
# module's panel artwork (tools/panel-art.py, with librsvg2-bin's rsvg-convert);
# bpy - Blender as a Python module - renders its photographs (tools/render-module.py).
python3 - <<'EOF' || pip install --break-system-packages -q pillow gmsh manifold3d trimesh numpy shapely fonttools ezdxf
import PIL, gmsh, manifold3d, trimesh, numpy, shapely, fontTools, ezdxf
EOF
# OpenCASCADE's Python binding: tools/lib-models.py draws the woody footprints' 3D models.
python3 -c "import OCP" 2>/dev/null || pip install --break-system-packages -q cadquery-ocp
python3 -c "import bpy" 2>/dev/null || pip install --break-system-packages -q bpy

echo "setup-env: OpenSCAD $(openscad --version 2>&1 | awk '{print $3}'), KiCad $(kicad-cli version)"
