#!/usr/bin/env bash
# Install everything the body CAD, the schematics, the layout and the sims need.
# Written for Ubuntu 24.04; on another distribution it installs what it can and
# says what it could not. Versions: tools/toolchain.yaml, tools/requirements.txt.
#
#   sudo bash tools/setup-env.sh          # or as root, e.g. from a cloud environment's setup script
#
# Idempotent: re-running it installs only what is missing. Takes ~3 minutes on
# a fresh machine, most of it KiCad. docs/reference/tooling.md says what each
# piece is for and how to use it.
set -euo pipefail

# The versions the committed outputs were made with: tools/toolchain.yaml (issue #9, G7).
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
pin() { awk -v k="$1:" '$1 == k {print $2}' "$here/toolchain.yaml"; }
KICAD_MIN=$(pin kicad_min); NGSPICE_MAJOR=$(pin ngspice_major); OPENSCAD_WANT=$(pin openscad)
# ver_ge A B: version A >= B
ver_ge() { [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -1)" = "$2" ]; }
. /etc/os-release
warn=()

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

# --- circuit simulation (tools/sim.py): ngspice from the distribution's archive
# (Ubuntu 24.04's is the 42 every results.yaml records; tools/toolchain.yaml). Raw
# decks through subprocess; not PySpice (hardware/module/pitch-stage/sim/README.md says why).
have ngspice || need_apt+=(ngspice)

# --- schematics (tools/sch.py): KiCad 9 from the KiCad project's own archive.
# Ubuntu's own kicad is 7.0, whose command line has no ERC and whose file
# format is older than the sheets this repository writes.
# The archive is a Launchpad PPA built for UBUNTU: on Debian (trixie ships 9.0.2) or
# any other distribution it is the wrong source, so it is never added there.
kicad_now=$(kicad-cli version 2>/dev/null || true)
if [ "$ID" != ubuntu ] && ! printf '%s' "$kicad_now" | grep -q '^9\.'; then
  echo "setup-env: $PRETTY_NAME - no KiCad 9 found, and the KiCad PPA is Ubuntu's. Install KiCad >= $KICAD_MIN" \
       "from your distribution (Debian: trixie's 9.0.x, or backports) or the Flatpak (org.kicad.KiCad), then re-run." >&2
elif [ "$ID" = ubuntu ] && printf '%s' "$kicad_now" | grep -q '^9\.' && ! ver_ge "$kicad_now" "$KICAD_MIN"; then
  need_apt+=(kicad kicad-symbols kicad-footprints)        # an older 9.x: upgrade from the archive
elif ! printf '%s' "$kicad_now" | grep -q '^9\.'; then
  if [ ! -f /etc/apt/sources.list.d/kicad-9.list ]; then
    key=$(curl -fsS https://api.launchpad.net/1.0/~kicad/+archive/ubuntu/kicad-9.0-releases \
          | python3 -c "import sys,json;print(json.load(sys.stdin)['signing_key_fingerprint'])")
    curl -fsS "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$key" \
      | gpg --dearmor > /etc/apt/trusted.gpg.d/kicad-9.gpg
    echo "deb https://ppa.launchpadcontent.net/kicad/kicad-9.0-releases/ubuntu ${VERSION_CODENAME:-noble} main" \
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
# are the key boards'; the rest the main board's (2026-09-30); the 2x10 header the
# module jack board's (2026-10-02); the 2x5 the iso board's (2026-10-03); the 1x10
# header and the 1x4 (the wire pads) the right-hand key board's Matrix parts (2026-10-03).
models=/usr/share/kicad/3dmodels
for m in Capacitor_SMD.3dshapes/C_0805_2012Metric.step \
         Resistor_SMD.3dshapes/R_0805_2012Metric.step \
         Resistor_SMD.3dshapes/R_0603_1608Metric.step \
         Package_SO.3dshapes/SOIC-16_3.9x9.9mm_P1.27mm.step \
         Capacitor_SMD.3dshapes/C_1206_3216Metric.step \
         Capacitor_SMD.3dshapes/CP_Elec_10x10.step \
         Capacitor_SMD.3dshapes/CP_Elec_6.3x5.8.step \
         Capacitor_SMD.3dshapes/CP_Elec_6.3x7.7.step \
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
         Package_TO_SOT_SMD.3dshapes/SOT-23.step \
         Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x05_P2.54mm_Vertical.step \
         Connector_PinHeader_2.54mm.3dshapes/PinHeader_2x10_P2.54mm_Vertical.step \
         Connector_PinHeader_2.54mm.3dshapes/PinHeader_2x05_P2.54mm_Vertical.step \
         Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x10_P2.54mm_Vertical.step \
         Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x04_P2.54mm_Vertical.step \
         Converter_DCDC.3dshapes/Converter_DCDC_RECOM_R-78E-0.5_THT.step; do
  if [ ! -s "$models/$m" ]; then
    mkdir -p "$models/$(dirname "$m")"
    curl -fsSL -o "$models/$m.part" "https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/9.0.0/$m"
    mv "$models/$m.part" "$models/$m"
  fi
done
# The PJ398SM's model is not in kicad-packages3D at any tag (MANIFEST row
# THONKICONN-PJ398SM-BADPIXEL-3D, checked 2026-09-29), so the banked community model
# goes in under the name KiCad's footprint gives it (module-jack, 2026-10-02).
pj=Connector_Audio.3dshapes/Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical.step
if [ ! -s "$models/$pj" ]; then
  mkdir -p "$models/$(dirname "$pj")"
  cp "$(dirname "$0")/../datasheets/connectors/THONKICONN-PJ398SM-BADPIXEL-3D.step" "$models/$pj"
fi

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
# cadquery-ocp (OpenCASCADE's binding) for tools/lib-models.py. Versions pinned in
# tools/requirements.txt (issue #9, G7); bpy apart, because Blender 5's wheels exist for
# Python 3.11 only, so its failure is a warning rather than the end of the script.
grep -v '^bpy' "$here/requirements.txt" > /tmp/woody-requirements.txt
pip install --break-system-packages -q -r /tmp/woody-requirements.txt
pip install --break-system-packages -q "$(awk '/^bpy/ {print $1}' "$here/requirements.txt")" \
  || warn+=("bpy did not install for $(python3 --version) - tools/render-module.py (the module's photographs) will not run")

# --- what is installed, against what the outputs were made with (tools/toolchain.yaml)
kicad_now=$(kicad-cli version 2>/dev/null || echo none)
ng_now=$(ngspice -v 2>&1 | sed -n 's/.*ngspice-\([0-9.]*\).*/\1/p' | head -1)
scad_now=$(openscad --version 2>&1 | awk '{print $3}')
{ [ "$kicad_now" != none ] && ver_ge "$kicad_now" "$KICAD_MIN"; } || warn+=("KiCad $kicad_now is below $KICAD_MIN, which made the fab outputs")
[ "${ng_now%%.*}" = "$NGSPICE_MAJOR" ] || warn+=("ngspice $ng_now; every results.yaml was made with $NGSPICE_MAJOR - a re-run may move numbers")
[ "$scad_now" = "$OPENSCAD_WANT" ] || warn+=("OpenSCAD $scad_now; the renders were made with $OPENSCAD_WANT")
command -v java >/dev/null || warn+=("no Java, so no Freerouting: only 'route: freerouting' needs it, and no board uses it now (the main board routes astar)")
echo "setup-env: $PRETTY_NAME | OpenSCAD $scad_now | KiCad $kicad_now | ngspice $ng_now"
for w in "${warn[@]}"; do echo "setup-env: WARNING: $w" >&2; done
