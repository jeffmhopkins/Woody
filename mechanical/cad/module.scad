// =====================================================================
// WOODY - EURORACK MODULE (10HP A-100 panel, two boards; ADR 0023, 0024)
//
// DO NOT PUT NUMBERS HERE. Dimensions come from generated/module-params.scad,
// which tools/cad.py writes from config/module.yaml - each value there carries
// its source and a status (settled / nominal / tbd), and the NE8FAV's numbers
// are copied from config/body.yaml by reference, never restated. This file
// holds GEOMETRY. The few literal numbers below are drawing conventions
// (colours, a nudge, a picture's margin) and are named as such.
//
//   part = "assembly"      the module, 3D (default)
//   part = "panel"         the panel as it is cut, 2D (DXF)
//   part = "jack_board"    the jack board's outline, 2D (DXF)
//   part = "main_board"    the main board's outline, 2D (DXF)
//   part = "drc"           the design-rule report, echo only
//   part = "pcb_geom"      where every board-mounted thing is, echo only
//   part = "art"           the printed graphics' zones and what stands on the face, echo only
//
// FRAME (config/module.yaml): x across the panel from its left edge, y up
// from its bottom edge, both seen from the front; z out of the panel toward
// the player, 0 on the panel's FRONT face. "Depth" below is distance behind
// the panel's REAR face, z = -panel_t - depth.
//
// Render with `python3 tools/cad.py build`, never by hand into renders/.
// =====================================================================

include <generated/module-params.scad>

part = "assembly";
explode = 0;          // mm between the layers in the exploded view
highlight = [];       // solid ids drawn bright yellow, the rest faded
ghost_panel = false;  // draw the panel translucent
show_rails = true;    // the case's rails, translucent
show_plugs = false;   // the NE8MX and patch plugs, for pictures only
vendor = true;        // banked vendor meshes where one exists; false = the envelopes the clash check uses
cut = "none";         // "x2d": a section DRAWING through x = cut_at, laid as (depth, y)
cut_at = -1;          // < 0: through the panel's centre (the NE8FAV's axis)
only = "";            // tools/cad.py clash: draw just this solid
list_solids = false;  // tools/cad.py clash: echo every solid's id
figure = false;       // set true by a figure that includes this file

$fn = 48;
EPS = 0.01;           // drawing convention: coplanar-face nudge

// ---------------------------------------------------------------- frame ----
W = panel_w;
H = panel_h;
T = panel_t;
cx = W / 2;
function zd(d) = -T - d;                   // z of a plane `d` behind the rear face

// THE STACK, front to back (ADR 0023 point 2). The jack's body stands on the
// panel's rear face and on the jack board's front face, so it sets that
// board's depth; the NE8FAV's flange stands on the rear face and its PCB face
// on the main board, so it sets that one's.
jb_d = jack_body_d;                        // jack board front face, behind the rear face
jb_z1 = zd(jb_d);                          // ...its z
jb_z0 = jb_z1 - boards_t;                  // its rear face
mb_d = ethercon_pcb_setback;
mb_z1 = zd(mb_d);                          // main board front face
mb_z0 = mb_z1 - boards_t;                  // main board rear face
so_l = jb_z0 - mb_z1;                      // MECH-STANDOFF-MOD, derived (never a config value)

// ---------------------------------------------------------- panel parts ----
ec = [cx, layout_ec_y];
fl = [ethercon_flange_w, ethercon_flange_h];
pots = [for (i = [0 : 2]) [cx + (i - 1) * layout_pot_pitch, layout_pot_y]];
jack_rows = len(layout_jacks);
jacks = [for (r = [0 : jack_rows - 1], c = [0 : 1])
         [layout_jacks[r][c], [cx + (c - 0.5) * layout_jack_pitch_x, layout_jack_y0 - r * layout_jack_pitch_y]]];
// THE BOTTOM ROW IS THE NE8FAV (ADR 0024 point 11): its cable drops below
// every control. The toggle's row is above it, and the LED is in that row, in
// the strip beside the toggle that the jack board's leg stands behind.
tog = [cx, layout_toggle_y];
led = [layout_led_side == "left" ? (ec[0] - fl[0] / 2) / 2 : (W + ec[0] + fl[0] / 2) / 2, tog[1]];
// Neutrik's two screws: diagonally opposite, upper left and lower right seen
// from the front (config/body.yaml ethercon.hole_dx/dy's source).
ec_holes = [ec + [-ethercon_hole_dx, ethercon_hole_dy] / 2, ec + [ethercon_hole_dx, -ethercon_hole_dy] / 2];
mount_x = [panel_hole_x0, panel_hole_x0 + panel_hole_n_hp * panel_hp];
mounts = [for (x = mount_x, y = panel_hole_y) [x, y]];
clear_top = panel_hole_y[1] - panel_washer_od / 2;       // the clear height's top, under the washers
clear_bot = panel_hole_y[0] + panel_washer_od / 2;
title_band = [1, clear_top - layout_label_band, W - 1, clear_top];   // x0 y0 x1 y1

// Toggle: the lever throws toward layout.toggle_on for ON (ADR 0024 point 12:
// across the panel, the owner's instruction of 2026-09-30), so its sweep lies
// in the panel plane along that axis. Everything that turns with the switch -
// the D-flat, the sweep, the body's terminal field and its lugs - is derived
// from tog_on; nothing below names x or y for the toggle.
lev_len = toggle_lever[0];
lev_d = toggle_lever[1];
lev_ang = toggle_lever[2];
tog_sweep = lev_len * sin(lev_ang) + lev_d / 2;     // along the throw, each way
tog_on = layout_toggle_on == "right" ? [1, 0] : layout_toggle_on == "left" ? [-1, 0]
       : layout_toggle_on == "up" ? [0, 1] : layout_toggle_on == "down" ? [0, -1] : undef;
assert(tog_on != undef, str("layout.toggle_on must be right, left, up or down, not ", layout_toggle_on));
function tog_xy(along, across) = tog_on[0] != 0 ? [along, across] : [across, along];   // [along the throw, across it] -> [x, y]
// NKK's terminal field (toggle.body[1]) lies along the throw, its width across.
tog_body = tog_xy(toggle_body[1], toggle_body[0]);
// The flat is on the OFF side: the M2011 is ON with the lever away from it
// (NKK p.5's positions against p.7's D4 front view; config layout.toggle_on).
tog_flat_rot = atan2(-tog_on[1], -tog_on[0]) - 90;  // dhole2d draws the flat at +y
// The lever's sweep on the face, and the nut's across it.
tog_sweep_r = ["r", tog - tog_xy(tog_sweep, toggle_nut_d / 2), tog + tog_xy(tog_sweep, toggle_nut_d / 2)];
tog_proud = toggle_bushing_l - T;          // bushing stood in front of the panel

// LED: lens tip led_proud in front of the face; its lead spacer (MECH-LED-BEZEL-MOD)
// stands on the jack board and stops the flange's underside.
led_fu = led_proud - led_l;                // z of the flange's underside
led_spacer_l = led_fu - jb_z1;             // derived

// Power header J-PWR-EURO on the main board's rear face, long axis along y.
pw = power_at;
pw_seat = mb_z0 - power_floor;             // where the seated socket's face stops
pw_top = pw_seat - power_socket_h;         // the socket's back (with strain relief)
rib_back = pw_top - 2 * power_ribbon_t;    // the ribbon folded over it, double at the fold
depth_max_rear = -rib_back - T;            // the deepest thing, behind the rear face

// ---------------------------------------------------------------- boards ----
b_x0 = boards_side_margin;
b_x1 = W - boards_side_margin;
b_y0 = rail_band;
b_y1 = H - rail_band;
notch = [ec[0] - fl[0] / 2 - boards_ec_clear, ec[0] + fl[0] / 2 + boards_ec_clear, ec[1] + fl[1] / 2 + boards_ec_clear];  // x0 x1 top; open to the bottom edge
// ...and above it, narrower, the step SW-POWER's body passes through: its body
// is deeper than the jack board's depth (ADR 0023). [x0, x1, y0, top]; y0 is
// the notch's top, so the two are one cut-out.
tnotch = [tog[0] - tog_body[0] / 2 - boards_toggle_clear, tog[0] + tog_body[0] / 2 + boards_toggle_clear,
          notch[2], max(notch[2], tog[1] + tog_body[1] / 2 + boards_toggle_clear)];
notch_top = tnotch[3];
// THE UMBILICAL'S DROP ZONE (ADR 0024 point 11), on the panel's face: the
// mated NE8MX's grip, and the strip its width that the plug and its cable
// hang in, from the axis down past the panel's bottom edge. How far in front
// of the panel the plug stands, and how the cable bends, are below.
drop_zone = [["NE8MX grip", ["c", ec, ethercon_cable_d / 2]],
             ["NE8MX cable drop", ["r", [ec[0] - ethercon_cable_d / 2, -H], [ec[0] + ethercon_cable_d / 2, ec[1]]]]];
plug_reach = ethercon_plug_l_min - ethercon_pcb_setback - T;   // the plug's back, in front of the panel's FRONT face, at least
umb_bend_r = ethercon_umb_bend_k * ethercon_umb_od;
// The tallest thing on the face (the knob, unless the toggle's lever is longer).
front = max(knob_gap + knob_h, tog_proud + lev_len * cos(lev_ang), ethercon_tab_front - T, led_proud, jack_bushing_l - T);
b2b_w = (b2b_rows - 1) * b2b_pitch;
b2b_l = (b2b_pins - 1) * b2b_pitch;
b2b_pin_l = b2b_protrude + boards_t + so_l + boards_t + b2b_tail;   // J-B2B-MOD's pins, derived
// U-ISO (ADR 0027) on the main board's rear face; its pins' tails out of the front face.
iso_tail = iso_pin_l - boards_t;           // derived: the pins stand this far out of the front face
iso_rect = rect_c(iso_at, iso_body[0], iso_body[1]);
iso_filter_env = [for (f = iso_filter) [f[5], f[2] == "can" ? ["c", [f[0], f[1]], f[3] / 2] : rect_c([f[0], f[1]], f[3], f[3])]];

// --------------------------------------------------------------- colours ----
C_ALU = [0.80, 0.81, 0.83];
C_PCB = [0.12, 0.42, 0.22];
C_PCB2 = [0.10, 0.30, 0.45];
C_BLACK = [0.12, 0.12, 0.13];
C_KNOB = [0.18, 0.18, 0.19];
C_METAL = [0.72, 0.72, 0.70];
C_BRASS = [0.78, 0.66, 0.35];
C_NYLON = [0.25, 0.25, 0.25];
C_LED = [0.35, 0.85, 0.35, 0.85];
C_RIB = [0.62, 0.62, 0.66];
C_RED = [0.85, 0.15, 0.12];
C_CAP = [0.12, 0.20, 0.55];
C_TRIM = [0.20, 0.35, 0.75];
C_RAIL = [0.55, 0.56, 0.60];
C_EC = [0.16, 0.16, 0.17];

// ----------------------------------------------------------------- solids ----
// Every solid goes through P() WITH A NAME, like the body's: the clash check
// pulls each one out on its own, and highlights and sections keep colour.
function id_match(h, id) = h == id || (h[len(h) - 1] == "*" && len(id) >= len(h) - 1
    && (len(h) == 1 || [for (i = [0 : len(h) - 2]) id[i]] == [for (i = [0 : len(h) - 2]) h[i]]));
module P(c, see = false, id = "") {
    assert(id != "", "every solid needs an id - the clash check cannot see an unnamed one");
    if (list_solids) echo("SOLID", id);
    hl = len(highlight) > 0;
    cc = hl && len([for (h = highlight) if (id_match(h, id)) 1]) > 0 ? [1.0, 0.85, 0.0]
       : hl ? [c[0], c[1], c[2], 0.18]
       : see ? [c[0], c[1], c[2], 0.3] : c;
    if (only == "" || only == id) color(cc)
        if (cut == "none") children();
        else section_2d() translate([0, 0, -cut_x()]) rotate([0, -90, 0]) children();
}
function cut_x() = cut_at < 0 ? cx : cut_at;
// The section in the plane (see woody_body.scad: a thin slab first, so a part
// that misses the plane is empty rather than a projection() warning).
module section_2d() {
    projection() intersection() {
        children();
        translate([-1e4, -1e4, -0.01]) cube([2e4, 2e4, 0.02]);
    }
}
// The exploded view pulls layers apart along z: the panel and what is on its
// face forward, the main board and what is behind it back.
function ex(layer) = explode * layer;

// ================================================================ 2D ======

module slot2d(p, r, travel) { hull() for (s = [-1, 1]) translate(p + [s * travel / 2, 0]) circle(r = r); }
module dhole2d(d, flat) {   // round with one flat, the flat up (+y): `flat` across from the flat to the far arc
    intersection() { circle(d = d); translate([-d / 2, -d / 2]) square([d, flat]); }
}

module panel_2d() {
    difference() {
        square([W, H]);
        for (m = mounts) slot2d(m, panel_hole_d / 2, panel_slot_travel);
        for (j = jacks) translate(j[1]) circle(d = jack_hole_d);
        for (p = pots) translate(p) circle(d = pot_hole_d);
        translate(led) circle(d = led_hole_d);
        translate(tog) rotate(tog_flat_rot) dhole2d(toggle_hole_d, toggle_flat);
        translate(ec) circle(d = ethercon_bore_d + ethercon_bore_clear);
        for (h = ec_holes) translate(h) circle(d = ethercon_hole_d);
        // No PUSH-tab slot: the tab stands ethercon.tab_back in front of the
        // flange face, clear of any panel up to the NE8FAV's panel_max (ADR 0024).
        if (ethercon_push_slot)
            translate([ec[0] - ethercon_tab_w / 2, ec[1] + ethercon_tab_bottom]) square([ethercon_tab_w, ethercon_tab_top - ethercon_tab_bottom]);
    }
}

module standoff_holes_2d() { for (s = standoff_at) translate(s) circle(d = standoff_hole_d); }
module jack_board_2d() {
    difference() {
        translate([b_x0, b_y0]) square([b_x1 - b_x0, b_y1 - b_y0]);
        translate([notch[0], b_y0 - 1]) square([notch[1] - notch[0], notch[2] - b_y0 + 1]);
        translate([tnotch[0], tnotch[2] - EPS]) square([tnotch[1] - tnotch[0], tnotch[3] - tnotch[2] + EPS]);
        standoff_holes_2d();
    }
}
module main_board_2d() {
    difference() {
        translate([b_x0, b_y0]) square([b_x1 - b_x0, b_y1 - b_y0]);
        standoff_holes_2d();
    }
}

// ================================================================ 3D ======

module slab(z0, z1) { translate([0, 0, min(z0, z1)]) linear_extrude(abs(z1 - z0)) children(); }
module box(x0, y0, z0, x1, y1, z1) { translate([min(x0, x1), min(y0, y1), min(z0, z1)]) cube([abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)]); }
module cyl(p, d, z0, z1, fn = 48) { translate([p[0], p[1], min(z0, z1)]) cylinder(d = d, h = abs(z1 - z0), $fn = fn); }

module panel_3d() {
    translate([0, 0, ex(2)]) {
        P(C_ALU, ghost_panel, "panel") slab(-T, 0) panel_2d();
        // The four M3 x 6 and their washers (MECH-PANEL-SCREW-MOD), at the
        // slots' centres. Only the heads: the shanks go into the rail.
        for (i = [0 : len(mounts) - 1]) {
            P(C_METAL, false, str("panel washer ", i + 1)) cyl(mounts[i], panel_washer_od, 0, panel_washer_t);
            P(C_METAL, false, str("panel screw ", i + 1)) cyl(mounts[i], m3_head_d, panel_washer_t, panel_washer_t + m3_head_k);
        }
        // Neutrik's A-screws into the flange, heads on the face.
        for (i = [0 : 1]) P(C_BLACK, false, str("etherCON screw ", i + 1)) cyl(ec_holes[i], ethercon_screw_head_d, 0, ethercon_screw_head_h);
        // Panel nuts: jacks and toggle.
        // Nuts are envelopes round the bushing: bored to the panel hole, so a nut and its bushing never read as a clash.
        for (j = jacks) P(C_METAL, false, str("nut ", j[0])) difference() { cyl(j[1], jack_nut_d, 0, jack_nut_h, 6); cyl(j[1], jack_hole_d, -1, jack_nut_h + 1); }
        P(C_METAL, false, "nut SW-POWER") difference() { cyl(tog, toggle_nut_d, 0, toggle_nut_h, 6); cyl(tog, toggle_hole_d, -1, toggle_nut_h + 1); }
    }
}

// -- the jack board and what it carries (layer 0) --
// PJ398SM ON ITS SIDE (ADR 0024): pins across the panel, the sleeve (pin 1)
// toward the panel's nearer side edge. Along a 13 mm column the footprint's
// pin line (fp_u below) does not fit; across, it does.
function jsgn(p) = p[0] < cx ? 1 : -1;     // +1: the pin-3 side (the body's top) points +x
function ju(p, u) = p[0] + jsgn(p) * u;    // x of a point `u` along the pin line
fp_u = [min(-jack_body_down, jack_pins[2] - jack_pads[2][1] / 2), max(jack_body_up, jack_pins[0] + jack_pads[0][1] / 2)];
fp_a = max(jack_body_w, jack_pads[0][0], jack_pads[1][0], jack_pads[2][0]) / 2;
function jack_body_rect(p) = ["r", [min(ju(p, -jack_body_down), ju(p, jack_body_up)), p[1] - jack_body_w / 2],
                                  [max(ju(p, -jack_body_down), ju(p, jack_body_up)), p[1] + jack_body_w / 2]];
function jack_fp_rect(p) = ["r", [min(ju(p, fp_u[0]), ju(p, fp_u[1])), p[1] - fp_a], [max(ju(p, fp_u[0]), ju(p, fp_u[1])), p[1] + fp_a]];
module jack_env(p) {
    // Body on the panel's rear face and the board's front; bushing through the panel.
    let(r = jack_body_rect(p)) box(r[1][0], r[1][1], jb_z1, r[2][0], r[2][1], zd(0));
    cyl(p, 6.0 - 0.02, zd(0), zd(0) + jack_bushing_l);      // the D6 bushing (drawing, [ds]); a nudge under the hole
}
module jack_3d(j) {
    p = j[1];
    P(C_BLACK, false, j[0]) {
        // The STEP has its sleeve toward +y; turn it to point outward.
        if (vendor) translate([p[0], p[1], jb_z1]) rotate([0, 0, jsgn(p) > 0 ? 90 : -90]) import("vendor/pj398sm.stl");
        else jack_env(p);
    }
    P(C_METAL, false, str(j[0], " tails"))
        box(ju(p, jack_pins[2]) - jsgn(p) * 0.8, p[1] - 0.8, jb_z0, ju(p, jack_pins[0]) + jsgn(p) * 0.8, p[1] + 0.8, jb_z1 - jack_tails);
}
module pot_env(p) {
    // R0904N, pins down: body on the board's front face, shaft up through the panel.
    box(p[0] - pot_body[2] / 2, p[1] + pot_body[0], jb_z1, p[0] + pot_body[2] / 2, p[1] + pot_body[1], jb_z1 + pot_body[3]);
    cyl(p, pot_shaft_d, jb_z1 + pot_body[3], jb_z1 + pot_shaft_top);
}
module pot_3d(name, p) {
    P(C_METAL, false, name) {
        if (vendor) translate([p[0], p[1], jb_z1]) rotate([0, 0, 90]) import("vendor/r0904n.stl");
        else pot_env(p);
    }
    P(C_METAL, false, str(name, " legs"))
        box(p[0] - pot_body[2] / 2, p[1] + pot_body[0], jb_z0, p[0] + pot_body[2] / 2, p[1] + pot_body[1], jb_z1 - pot_legs);
}
module knob_3d(name, p) {
    // Thonk 1900h (T18): 12 at the base, 16 tall. Its bore takes the shaft.
    translate([0, 0, ex(3)]) P(C_KNOB, false, str("knob ", name)) difference() {
        union() {
            cyl(p, knob_d, knob_gap, knob_gap + knob_h * 0.35);
            translate([p[0], p[1], knob_gap + knob_h * 0.35]) cylinder(d1 = knob_d * 0.85, d2 = knob_d * 0.75, h = knob_h * 0.65);
        }
        cyl(p, pot_shaft_d + 0.02, knob_gap - 1, jb_z1 + pot_shaft_top);
    }
}
module led_3d() {
    P(C_LED, false, "LED-PANEL") {
        cyl(led, led_flange_d, led_fu, led_fu + led_flange_t);
        cyl(led, led_lens_d, led_fu + led_flange_t, led_proud - led_lens_d / 2);
        translate([led[0], led[1], led_proud - led_lens_d / 2]) sphere(d = led_lens_d);
    }
    P(C_NYLON, false, "LED spacer") cyl(led, led_spacer_d, jb_z1, led_fu);
    P(C_METAL, false, "LED-PANEL leads")
        box(led[0] - led_pitch / 2 - 0.3, led[1] - 0.3, jb_z0, led[0] + led_pitch / 2 + 0.3, led[1] + 0.3, jb_z0 - 1.5);
}
module jack_board_3d() {
    P(C_PCB, false, "jack board") slab(jb_z0, jb_z1) jack_board_2d();
    for (j = jacks) jack_3d(j);
    for (i = [0 : 2]) { pot_3d(layout_pots[i], pots[i]); knob_3d(layout_pots[i], pots[i]); }
    led_3d();
    // Standoff screws' heads on the jack board's front face.
    for (i = [0 : len(standoff_at) - 1])
        P(C_METAL, false, str("standoff screw front ", i + 1)) cyl(standoff_at[i], m3_head_d, jb_z1, jb_z1 + m3_head_k);
    // J-B2B-MOD's posts out of the jack board's front face, for the fillet.
    P(C_BRASS, false, "J-B2B-MOD posts front") b2b_pins(jb_z1, jb_z1 + b2b_protrude);
}
module b2b_pins(z0, z1) {
    for (r = [0 : b2b_rows - 1], k = [0 : b2b_pins - 1])
        translate([b2b_at[0] - b2b_w / 2 + r * b2b_pitch - 0.32, b2b_at[1] - b2b_l / 2 + k * b2b_pitch - 0.32, min(z0, z1)])
            cube([0.64, 0.64, abs(z1 - z0)]);
}

// -- between the boards (layer -1) --
module between_3d() {
    translate([0, 0, ex(-1)]) {
        for (i = [0 : len(standoff_at) - 1])
            P(C_NYLON, false, str("standoff ", i + 1)) translate([standoff_at[i][0], standoff_at[i][1], mb_z1])
                difference() { cylinder(d = standoff_af / cos(30), h = so_l, $fn = 6); translate([0, 0, -1]) cylinder(d = standoff_hole_d - 0.7, h = so_l + 2); }
        P(C_BLACK, false, "J-B2B-MOD") box(b2b_at[0] - b2b_w / 2 - 1.27, b2b_at[1] - b2b_l / 2 - 1.27, mb_z1,
                                          b2b_at[0] + b2b_w / 2 + 1.27, b2b_at[1] + b2b_l / 2 + 1.27, mb_z1 + b2b_insulator_h);
        P(C_BRASS, false, "J-B2B-MOD pins") b2b_pins(mb_z1 + b2b_insulator_h, jb_z0);
    }
}

// -- the main board and what it carries (layer -2) --
module ec_env() {
    // NE8FAV (ADR 0021/0023): the 25 x 25 body from the flange face to the PCB
    // face, the nose in the bore, the PUSH tab's stem inside the bore's circle
    // and its plate in front of the panel, the two locating nubs below.
    box(ec[0] - fl[0] / 2, ec[1] - fl[1] / 2, mb_z1, ec[0] + fl[0] / 2, ec[1] + fl[1] / 2, zd(0));
    cyl(ec, ethercon_bore_d - 0.4, zd(0), zd(0) + ethercon_nose_l);
    intersection() {   // the stem: inside the nose's circle, where the STEP has it
        box(ec[0] - ethercon_tab_w / 4, ec[1] + ethercon_tab_bottom, zd(0), ec[0] + ethercon_tab_w / 4, ec[1] + ethercon_tab_bottom + 1, zd(0) + ethercon_tab_back);
        cyl(ec, ethercon_bore_d - 0.4, zd(0) - 1, zd(0) + ethercon_tab_back + 1);
    }
    box(ec[0] - ethercon_tab_w / 2, ec[1] + ethercon_tab_bottom, zd(0) + ethercon_tab_back, ec[0] + ethercon_tab_w / 2, ec[1] + ethercon_tab_top, zd(0) + ethercon_tab_front);
    box(ec[0] - ethercon_pegs[0], ec[1] - fl[1] / 2 - ethercon_peg_below, zd(ethercon_pegs[2]), ec[0] + ethercon_pegs[0], ec[1] - fl[1] / 2 + EPS, zd(ethercon_pegs[1]));
}
module main_board_3d() {
    translate([0, 0, ex(-2)]) {
        P(C_PCB2, false, "main board") slab(mb_z0, mb_z1) main_board_2d();
        P(C_EC, false, "J-UMBILICAL") {
            if (vendor) translate([ec[0], ec[1], zd(0)]) import("vendor/ne8fav.stl");
            else ec_env();
        }
        P(C_METAL, false, "J-UMBILICAL tails") box(ec[0] - 9.28, ec[1] - 11.0, mb_z0, ec[0] + 9.28, ec[1] + 12.35, zd(ethercon_pcb_setback + ethercon_tails));
        P(C_BRASS, false, "J-B2B-MOD tails") b2b_pins(mb_z0, mb_z0 - b2b_tail);
        for (i = [0 : len(standoff_at) - 1])
            P(C_METAL, false, str("standoff screw rear ", i + 1)) cyl(standoff_at[i], m3_head_d, mb_z0, mb_z0 - m3_head_k);
        // J-PWR-EURO: the shroud, its cavity open to the rear.
        P(C_BLACK, false, "J-PWR-EURO") difference() {
            box(pw[0] - power_w / 2, pw[1] - power_l / 2, mb_z0, pw[0] + power_w / 2, pw[1] + power_l / 2, mb_z0 - power_h);
            box(pw[0] - power_socket_w / 2 - 0.1, pw[1] - power_socket_l / 2 - 0.1, pw_seat, pw[0] + power_socket_w / 2 + 0.1, pw[1] + power_socket_l / 2 + 0.1, mb_z0 - power_h - 1);
        }
        // Tall parts: envelopes for the depth and clash checks, not placements.
        for (i = [0 : len(tall_at) - 1]) let(t = tall_at[i]) {
            if (t[2] == "cap") P(C_CAP, false, str("tall cap ", i + 1)) cyl([t[0], t[1]], tall_cap_d, mb_z0, mb_z0 - tall_cap_h);
            else P(C_TRIM, false, str("tall trimmer ", i + 1)) box(t[0] - tall_trim[0] / 2, t[1] - tall_trim[1] / 2, mb_z0, t[0] + tall_trim[0] / 2, t[1] + tall_trim[1] / 2, mb_z0 - tall_trim[2]);
        }
        // U-ISO, RECOM RP20-2412SAW (ADR 0027): the body on the rear face, the pins' tails out of the front.
        P(C_METAL, false, "U-ISO") box(iso_at[0] - iso_body[0] / 2, iso_at[1] - iso_body[1] / 2, mb_z0,
                                       iso_at[0] + iso_body[0] / 2, iso_at[1] + iso_body[1] / 2, mb_z0 - iso_body[2]);
        P(C_BRASS, false, "U-ISO tails") for (q = iso_pins) cyl(iso_at + q, iso_pin_d, mb_z1, mb_z1 + iso_tail, 16);
        for (f = iso_filter)
            if (f[2] == "can") P(C_CAP, false, f[5]) cyl([f[0], f[1]], f[3], mb_z0, mb_z0 - f[4]);
            else P(C_BLACK, false, f[5]) box(f[0] - f[3] / 2, f[1] - f[3] / 2, mb_z0, f[0] + f[3] / 2, f[1] + f[3] / 2, mb_z0 - f[4]);
    }
}
// The toggle is panel-mounted and wired (ADR 0023): body on the panel's rear
// face, through the step at the top of the jack board's notch; lever thrown to
// ON (layout.toggle_on), its terminal field along the throw.
module toggle_3d() {
    P(C_METAL, false, "SW-POWER") {
        box(tog[0] - tog_body[0] / 2, tog[1] - tog_body[1] / 2, zd(toggle_body[2]), tog[0] + tog_body[0] / 2, tog[1] + tog_body[1] / 2, zd(0));
        // The keyed bushing: the D-hole's shape less a nudge (NKK's D4 flat is what stops it turning).
        translate([tog[0], tog[1], zd(0)]) linear_extrude(toggle_bushing_l) offset(delta = -0.05) rotate(tog_flat_rot) dhole2d(toggle_hole_d, toggle_flat);
        translate([tog[0], tog[1], zd(0) + toggle_bushing_l]) rotate(a = lev_ang, v = [-tog_on[1], tog_on[0], 0]) cylinder(d = lev_d, h = lev_len);
    }
    li = tog_xy(1, 0.5);    // the lugs inside the body's outline: 1 along the throw, 0.5 across
    P(C_METAL, false, "SW-POWER lugs") box(tog[0] - tog_body[0] / 2 + li[0], tog[1] - tog_body[1] / 2 + li[1], zd(toggle_body[2]), tog[0] + tog_body[0] / 2 - li[0], tog[1] + tog_body[1] / 2 - li[1], zd(toggle_body[2] + toggle_lugs));
}
// The mated IDC socket and its ribbon, folded over the strain relief and down
// toward the bus board (red stripe, -12 V, at the bottom).
module power_plug_3d() {
    translate([0, 0, ex(-3)]) {
        P(C_BLACK, false, "power socket") box(pw[0] - power_socket_w / 2, pw[1] - power_socket_l / 2, pw_seat, pw[0] + power_socket_w / 2, pw[1] + power_socket_l / 2, pw_top);
        P(C_RIB, false, "power ribbon") box(pw[0] + power_socket_w / 2 - power_ribbon_w, -power_drop, pw_top, pw[0] + power_socket_w / 2, pw[1] + power_socket_l / 2, rib_back);
        P(C_RED, false, "power ribbon stripe") box(pw[0] + power_socket_w / 2 - 1.27, -power_drop, rib_back - EPS * 5, pw[0] + power_socket_w / 2, pw[1] + power_socket_l / 2, rib_back - EPS);
    }
}
module rails_3d() {
    for (r = [[0, rail_band], [H - rail_band, H]])
        P(C_RAIL, true, r[0] == 0 ? "rail bottom" : "rail top") box(-6, r[0], zd(rail_depth), W + 6, r[1], zd(0));
}
module plugs_3d() {
    for (j = jacks) P(C_BLACK, false, str("patch plug ", j[0])) cyl(j[1], jack_plug_d, jack_nut_h + 0.5, jack_nut_h + 25);
    P(C_EC, false, "NE8MX") cyl(ec, ethercon_cable_d, ethercon_tab_front - T + 0.5, 40);
}

module assembly() {
    jack_board_3d();
    between_3d();
    main_board_3d();
    toggle_3d();
    power_plug_3d();
    if (show_plugs) plugs_3d();
    if (show_rails) rails_3d();
    panel_3d();         // last: a see-through part drawn first hides what is behind it
}

// =============================================================== DRC ======
// Arithmetic checks on the parameters, one line each, in the body's format:
//   ECHO: "DRC", "PASS"|"FAIL"|"NOTE"|"INFO", "<rule>", <measured>, "<why>"
module drc(ok, rule, v, why) { echo("DRC", ok == undef ? "NOTE" : ok ? "PASS" : "FAIL", rule, v, why); }

// 2D shapes on the panel's face: ["c", [x, y], r] or ["r", [x0, y0], [x1, y1]].
function dist_pr(p, a, b) = sqrt(pow(max(a[0] - p[0], 0, p[0] - b[0]), 2) + pow(max(a[1] - p[1], 0, p[1] - b[1]), 2));
function gap2(A, B) =
    A[0] == "c" && B[0] == "c" ? norm(A[1] - B[1]) - A[2] - B[2]
  : A[0] == "c" && B[0] == "r" ? dist_pr(A[1], B[1], B[2]) - A[2]
  : A[0] == "r" && B[0] == "c" ? gap2(B, A)
  : max(A[1][0] - B[2][0], B[1][0] - A[2][0], A[1][1] - B[2][1], B[1][1] - A[2][1]);
function edge_gap(A) = A[0] == "c" ? min(A[1][0] - A[2], W - A[1][0] - A[2], A[1][1] - A[2], H - A[1][1] - A[2])
                                   : min(A[1][0], W - A[2][0], A[1][1], H - A[2][1]);
function minv(v) = min([for (x = v) x]);
// [min gap, [name a, name b]] over pairs drawn from two named lists.
function worst(L, M, same = false) =
    let(g = [for (i = [0 : len(L) - 1], j = [0 : len(M) - 1]) if (!same || j > i) [gap2(L[i][1], M[j][1]), L[i][0], M[j][0]]],
        m = minv([for (x = g) x[0]]))
    [for (x = g) if (x[0] == m) x][0];
function rect_c(p, w, h) = ["r", p - [w, h] / 2, p + [w, h] / 2];

// The panel's cuts, for webs. A slot is its hull's rectangle and two circles.
// [name, shape, group]: cuts in one group are one part's own pattern.
cuts_own = concat([for (j = jacks) [j[0], ["c", j[1], jack_hole_d / 2], ""]],
                  [for (i = [0 : 2]) [layout_pots[i], ["c", pots[i], pot_hole_d / 2], ""]],
                  [["LED-PANEL", ["c", led, led_hole_d / 2], ""], ["SW-POWER", ["c", tog, toggle_hole_d / 2], ""],
                   ["J-UMBILICAL bore", ["c", ec, (ethercon_bore_d + ethercon_bore_clear) / 2], "ec"]],
                  [for (h = ec_holes) ["J-UMBILICAL screw", ["c", h, ethercon_hole_d / 2], "ec"]]);
cuts_mount = [for (m = mounts) ["mount slot", rect_c(m, panel_slot_travel + panel_hole_d, panel_hole_d)]];

// What stands on the panel's face, for spacing.
knobs_max = [for (i = [0 : 2]) [str("knob ", layout_pots[i]), ["c", pots[i], knob_d_max / 2]]];
knobs = [for (i = [0 : 2]) [str("knob ", layout_pots[i]), ["c", pots[i], knob_d / 2]]];
plugs = [for (j = jacks) [str("plug ", j[0]), ["c", j[1], jack_plug_d / 2]]];
ne8mx = [["NE8MX", ["c", ec, ethercon_cable_d / 2]]];
face_other = concat(
    [["PUSH tab", ["r", ec + [-ethercon_tab_w / 2, ethercon_tab_bottom], ec + [ethercon_tab_w / 2, ethercon_tab_top]]],
     ["SW-POWER sweep", tog_sweep_r],
     ["LED-PANEL", ["c", led, led_lens_d / 2]]],
    [for (h = ec_holes) ["A-screw head", ["c", h, ethercon_screw_head_d / 2]]]);
washers = [for (m = mounts) ["panel washer", rect_c(m, panel_slot_travel + panel_washer_od, panel_washer_od)]];

// LEGEND ZONES (ADR 0024), derived from what is around them: the title band
// under the top washers; a band under each knob down to the first row's plug
// grips; beside each jack on the panel's outer side; between the LED and the
// toggle; the strip right of the flange; right of the toggle.
jl = jacks[0][1][0] - jack_plug_d / 2;     // the left column's plug edge
jr = jacks[1][1][0] + jack_plug_d / 2;
legend = concat(
    [["title", ["r", [title_band[0], title_band[1]], [title_band[2], title_band[3]]], ""]],
    [for (i = [0 : 2]) [str(layout_pots[i], " legend"),
        ["r", [pots[i][0] - (layout_pot_pitch - legend_sep()) / 2, layout_jack_y0 + jack_plug_d / 2 + 0.5],
              [pots[i][0] + (layout_pot_pitch - legend_sep()) / 2, layout_pot_y - knob_d_max / 2 - 0.5]], ""]],
    [for (j = jacks) [str(j[0], " legend"),
        j[1][0] < cx ? ["r", [1, j[1][1] - rules_legend_h / 2], [jl - 0.5, j[1][1] + rules_legend_h / 2]]
                     : ["r", [jr + 0.5, j[1][1] - rules_legend_h / 2], [W - 1, j[1][1] + rules_legend_h / 2]], "jack"]],
    [["LED-PANEL legend", ["r", [led[0] + led_hole_d / 2 + 1, led[1] - rules_legend_h / 2], [tog_sweep_r[1][0] - 1, led[1] + rules_legend_h / 2]], ""],
     ["J-UMBILICAL legend", ["r", [ec[0] + ethercon_cable_d / 2 + 0.5, ec_holes[1][1] + ethercon_screw_head_d / 2 + 0.5], [W - 1, ec[1] + fl[1] / 2]], ""],
     ["SW-POWER legend", ["r", [tog_sweep_r[2][0] + 1, tog[1] - rules_legend_h / 2], [W - 1, tog[1] + rules_legend_h / 2]], ""]]);
function legend_sep() = 1;     // drawing convention: 0.5 either side between neighbouring legend bands

// THE PRINTED GRAPHICS' ZONES (ADR 0026), derived like the legend zones.
// Three grey ISLANDS - A the breath knobs, B the six outputs, C power and the
// umbilical - with black gutters between them; a HEADER pill over A under the
// title band; the NAME between the two top panel screws' washers, above the
// title band (which carries the maker line - the owner, 2026-09-30); the
// OFFSET knob's two end marks. Each jack's label is a pill in its own legend
// zone, so it needs no zone of its own.
// tools/panel-art.py reads these from panel-art.echo and sets the text in
// them; nothing it draws may leave its zone.
art_in = art_island_r / 2;                         // a pill this far inside an island's edge
knob_top = layout_pot_y + knob_d_max / 2;
jack_grip_top = layout_jack_y0 + jack_plug_d / 2;
jack_nut_bot = jacks[len(jacks) - 1][1][1] - jack_nut_d / 2;
// Gutter A|B: centred between the first row's nuts and the pot legend bands' foot.
gut_ab = (layout_jack_y0 + jack_nut_d / 2 + legend[1][1][1][1]) / 2;
// Gutter B|C: centred between the last row's nuts and the top of the toggle row.
row_top = max(tog_sweep_r[2][1], tog[1] + toggle_nut_d / 2, legend[len(legend) - 1][1][2][1], led[1] + led_hole_d / 2);
gut_bc = (jack_nut_bot + row_top) / 2;
hdr_a = ["r", [art_frame, (knob_top + title_band[1] - art_header_h) / 2], [W - art_frame, (knob_top + title_band[1] + art_header_h) / 2]];
islands = [["island A", ["r", [art_frame, gut_ab + art_island_gap / 2], [W - art_frame, hdr_a[1][1] - art_island_gap / 2]], "island"],
           ["island B", ["r", [art_frame, gut_bc + art_island_gap / 2], [W - art_frame, gut_ab - art_island_gap / 2]], "island"],
           ["island C", ["r", [art_frame, clear_bot + art_frame], [W - art_frame, gut_bc - art_island_gap / 2]], "island"]];
mark_r = knob_d_max / 2 + art_mark_gap + art_mark_size / 2;
mark_at = [for (s = [-1, 1]) pots[1] + mark_r * [s * sin(art_mark_angle), cos(art_mark_angle)]];
art_zones = concat(islands,
    [["header breath", hdr_a, "header"],
     // the name: between the top washers' reach (a washer anywhere along its slot), 0.5 clear, from the
     // title band's top to art.frame under the panel's top edge
     ["name", ["r", [mounts[1][0] + (panel_slot_travel + panel_washer_od) / 2 + 0.5, clear_top],
                    [mounts[3][0] - (panel_slot_travel + panel_washer_od) / 2 - 0.5, H - art_frame]], "text"],
     ["scale OFFSET-", rect_c(mark_at[0], art_mark_size, art_mark_size), "mark"],
     ["scale OFFSET+", rect_c(mark_at[1], art_mark_size, art_mark_size), "mark"]]);

module drc_report() {
    echo("DRC", "INFO", "tbd parameters in play", len(module_tbd_params), module_tbd_params);
    echo("DRC", "INFO", "panel", [W, H, T], "mm: width, height, thickness (A-100, 10HP) - panel-width, panel-height-budget");

    // ---- the panel: layout on the face
    kk = worst(knobs_max, knobs_max, true);
    drc(kk[0] >= rules_knob_gap_min - 1e-6, "knob to knob at the 14 mm budget", kk[0],
        str("mm between knob skirts at KNOB-BREATH's maximum diameter (", kk[1], " / ", kk[2], "); ADR 0004 wants ", rules_knob_gap_min));
    kc = worst(knobs, knobs, true);
    drc(kc[0] >= rules_knob_gap_min, "knob to knob, the chosen knob", kc[0], "mm between the Thonk 1900h's 12 mm skirts (KNOB-BREATH, proposed)");
    ke = minv([for (k = knobs_max) edge_gap(k[1])]);
    drc(ke >= rules_knob_edge_min, "knob inside the panel's side edges", ke, "mm, a 14 mm knob to the nearest panel edge");
    pp = worst(plugs, plugs, true);
    drc(pp[0] >= rules_plug_gap_min, "jack to jack: plug grip to plug grip", pp[0], str("mm (", pp[1], " / ", pp[2], "); ", layout_jack_pitch_y, " down a column, ", layout_jack_pitch_x, " across"));
    pk = worst(plugs, knobs_max);
    drc(pk[0] >= rules_plug_gap_min, "plug grip to knob", pk[0], str("mm (", pk[1], " / ", pk[2], ")"));
    po = worst(concat(plugs, knobs_max), concat(ne8mx, face_other));
    drc(po[0] >= rules_front_clear, "plugs and knobs clear of the NE8MX, the PUSH tab, the toggle, the LED and the A-screws", po[0], str("mm (", po[1], " / ", po[2], ")"));
    oo = worst(face_other, face_other, true);
    drc(oo[0] >= rules_front_clear, "face parts clear of each other", oo[0], str("mm (", oo[1], " / ", oo[2], ")"));
    on = worst(ne8mx, [for (f = face_other) if (f[0] == "SW-POWER sweep" || f[0] == "LED-PANEL") f]);
    drc(on[0] >= rules_front_clear, "NE8MX clear of the toggle's sweep and the LED", on[0], str("mm (", on[2], "); it covers its own tab and screws by design"));
    // THE OWNER'S RULE (2026-09-30, ADR 0024 point 11): "Power switch should not
    // be underneath the connector." Nothing the player must reach - the toggle,
    // the knobs, the jacks' plug grips, the LED - in the NE8MX's grip or the
    // strip its plug and cable hang in, by a plug grip's clearance.
    controls = concat(knobs_max, plugs,
                      [["SW-POWER sweep", tog_sweep_r],
                       ["SW-POWER nut", ["c", tog, toggle_nut_d / 2]],
                       ["LED-PANEL", ["c", led, led_hole_d / 2]]]);
    dz = worst(controls, drop_zone);
    drc(dz[0] >= rules_plug_gap_min, "no panel control under the umbilical: clear of the NE8MX's grip and its cable's drop zone", dz[0],
        str("mm (", dz[1], " / ", dz[2], "); the zone is the NE8MX's ", ethercon_cable_d, " grip and a strip that wide from the axis down past the panel's bottom edge"));
    drc(plug_reach >= front, "the umbilical's plug stands proud of every control", [plug_reach, front],
        "mm in front of the panel's front face: the NE8MX's back at least (its short length, fully home to the NE8FAV's PCB face), against the tallest thing on the face - so no control gets out from under the cable by being taller, and the drop zone holds at every height");
    echo("DRC", "INFO", "the umbilical's bend", [umb_bend_r, plug_reach + umb_bend_r - ethercon_umb_od / 2, ec[1] - umb_bend_r],
         "mm: the cable's bend radius (tbd: umb_bend_k x umb_od); how far in front of the panel its hanging run stands, at least; and how far above the panel's bottom edge the bend has turned it straight down");
    fw = worst(concat(plugs, knobs_max, ne8mx, face_other, [["title band", ["r", [title_band[0], title_band[1]], [title_band[2], title_band[3]]]]]), washers);
    drc(fw[0] >= 0, "everything on the face clear of the panel screws' washers", fw[0],
        str("mm (", fw[1], "); a washer anywhere along its slot, panel_washer_od - the clear height panel-height-budget derives"));
    drc(title_band[1] >= pots[0][1] + knob_d_max / 2, "title band above the knobs", title_band[1] - pots[0][1] - knob_d_max / 2, "mm, the band's foot above a 14 mm knob's top");

    // ---- the panel: webs
    // Pairs inside one part's own pattern (the NE8FAV's bore and screws) are Neutrik's, not the layout's.
    wo_other = [for (i = [0 : len(cuts_own) - 1], j = [i + 1 : 1 : len(cuts_own) - 1])
                if (cuts_own[i][2] == "" || cuts_own[i][2] != cuts_own[j][2])
                [gap2(cuts_own[i][1], cuts_own[j][1]), cuts_own[i][0], cuts_own[j][0]]];
    wm = minv([for (x = wo_other) x[0]]);
    wmn = [for (x = wo_other) if (x[0] == wm) x][0];
    drc(wm >= rules_web_min, "panel web between two parts' cuts", wm, str("mm of aluminium (", wmn[1], " / ", wmn[2], ")"));
    we = minv([for (c = cuts_own) edge_gap(c[1])]);
    drc(we >= rules_web_min, "panel web from a cut to the panel's edge", we, "mm (the standard mounting slots excepted)");
    wms = worst(cuts_own, cuts_mount);
    drc(wms[0] >= rules_web_min, "panel web from a cut to a mounting slot", wms[0], str("mm (", wms[1], ")"));
    ecw = min(norm(ec_holes[0] - ec) - (ethercon_bore_d + ethercon_bore_clear) / 2 - ethercon_hole_d / 2, 1e9);
    echo("DRC", "INFO", "NE8FAV cut-out's own web, bore to screw hole", ecw, "mm - Neutrik's pattern (ST-NE8FAV), not a layout choice");
    drc(undef, "mounting slots", [mount_x, panel_hole_y, panel_hole_d, panel_slot_travel],
        "mm: slot centres x, y; width; centre travel - Doepfer's holes, slotted as the banked fabricated panel is");

    // ---- the parts in the panel
    drc(T <= ethercon_panel_max, "panel within the NE8FAV's maximum", ethercon_panel_max - T, "mm to spare");
    drc(T <= toggle_panel_max, "panel within the toggle's maximum", toggle_panel_max - T, "mm to spare (NKK, standard hardware)");
    drc(ethercon_tab_back > T && !ethercon_push_slot, "PUSH tab clear of the panel - no slot",
        ethercon_tab_back - T, "mm between the panel's front face and the tab's plate (ADR 0024); the stem passes inside the bore");
    drc(ethercon_tab_bottom < (ethercon_bore_d + ethercon_bore_clear) / 2, "PUSH tab's stem rises inside the bore",
        (ethercon_bore_d + ethercon_bore_clear) / 2 - ethercon_tab_bottom, "mm, the tab's foot inside the bore's edge; the STEP has nothing of the NE8FAV outside a 22 circle within 3.8 of the flange face (ethercon.tab_back)");
    drc(jack_bushing_l - T >= jack_nut_h, "jack bushing leaves thread for its nut", jack_bushing_l - T - jack_nut_h, "mm past the nut");
    drc(tog_proud >= toggle_nut_h, "toggle bushing leaves thread for its nut", tog_proud - toggle_nut_h, "mm past the nut");
    pot_gap = jb_d - pot_body[3];
    drc(pot_gap >= 0, "pot bracket behind the panel", pot_gap, "mm between the R0904N's bracket and the panel's rear face (it has no bushing: the board locates it)");
    shaft_proud = jb_z1 + pot_shaft_top;
    drc(undef, "pot shaft stands in front of the panel", shaft_proud,
        str("mm; the knob's bore must be at least ", shaft_proud - knob_gap, " deep for it to sit knob.gap off the face - read it off the knob at the first fit"));
    drc(led_spacer_l > 0, "LED lead spacer length (derived)", led_spacer_l,
        "mm, the jack board's front face to the LED flange's underside - MECH-LED-BEZEL-MOD's length");

    // ---- the stack
    echo("DRC", "INFO", "stack depths behind the panel's rear face", [jb_d, jb_d + boards_t, mb_d, mb_d + boards_t],
         "mm: jack board front and rear, main board front and rear - set by the PJ398SM's body and the NE8FAV's setback");
    drc(so_l > 0, "standoff length (derived)", so_l, "mm between the boards = the NE8FAV's setback less the jack's body and the jack board (MECH-STANDOFF-MOD)");
    face = standoff_stock_l - so_l;
    drc(abs(face) > standoff_tol ? (face > 0) : true, "standoff faced from stock", [standoff_stock_l, face],
        str("mm: the stock length, and what comes off it (a stock part is +/-", standoff_tol, "; face it and measure it, as the key boards' spacer)"));
    drc(undef, "J-B2B-MOD pin length (derived)", b2b_pin_l,
        str("mm = ", b2b_protrude, " proud of the jack board + ", boards_t, " + the gap + ", boards_t, " + ", b2b_tail, " out of the main board"));

    // ---- the boards
    drc(b_y0 >= rail_band && b_y1 <= H - rail_band, "boards inside the rail band", [b_y0, b_y1], "mm, the boards' bottom and top edges (rail.band is tbd)");
    drc(b_x0 >= 0 && b_x1 <= W, "boards inside the panel's width", [b_x0, W - b_x1], "mm inside each side edge");
    echo("DRC", "INFO", "board outlines", [[b_x0, b_y0, b_x1, b_y1], notch, tnotch], "mm: [x0, y0, x1, y1] of both; the jack board's notch [x0, x1, top], open to its bottom edge, and its step for SW-POWER [x0, x1, y0, top] above it");
    legw = [notch[0] - b_x0, b_x1 - notch[1]];
    echo("DRC", "INFO", "jack board legs beside the notch", legw, "mm wide, left and right");
    drc(notch[0] <= ec[0] - fl[0] / 2 - boards_ec_clear + 1e-6 && notch[2] >= ec[1] + fl[1] / 2 + boards_ec_clear - 1e-6,
        "jack board notch clear of the NE8FAV's body", boards_ec_clear, "mm each side and above");
    tn = min(tog[0] - tog_body[0] / 2 - tnotch[0], tnotch[1] - tog[0] - tog_body[0] / 2, tnotch[3] - tog[1] - tog_body[1] / 2);
    drc(tn >= boards_toggle_clear - 1e-6 && tog[1] - tog_body[1] / 2 >= ec[1] + fl[1] / 2 + boards_part_clear,
        "jack board notch clear of SW-POWER's body", [tn, tog[1] - tog_body[1] / 2 - ec[1] - fl[1] / 2],
        "mm: the least of each side and above; and the toggle's body above the NE8FAV's body, behind the panel");
    // Behind the panel, inside the rail's depth: nothing may reach into the band.
    behind = concat([for (j = jacks) [j[0], j[1][1] - jack_body_w / 2, j[1][1] + jack_body_w / 2]],
                    [for (i = [0 : 2]) [layout_pots[i], pots[i][1] + pot_body[0], pots[i][1] + pot_body[1]]],
                    [["SW-POWER", tog[1] - tog_body[1] / 2, tog[1] + tog_body[1] / 2],
                     ["J-UMBILICAL", ec[1] - fl[1] / 2 - ethercon_peg_below, ec[1] + fl[1] / 2],
                     ["LED spacer", led[1] - led_spacer_d / 2, led[1] + led_spacer_d / 2]],
                    [for (s = standoff_at) ["standoff screw head", s[1] - m3_head_d / 2, s[1] + m3_head_d / 2]]);
    rb = [for (b = behind) [min(b[1] - rail_band, H - rail_band - b[2]), b[0]]];
    rbm = minv([for (r = rb) r[0]]);
    drc(rbm >= 0, "parts behind the panel clear of the rail band", rbm, str("mm (", [for (r = rb) if (r[0] == rbm) r[1]][0], "); rail.band is tbd"));
    tl = zd(toggle_body[2] + toggle_lugs) - mb_z1;
    drc(tl >= 0, "toggle's lugs in front of the main board", tl, "mm between the lugs' ends and the main board's front face - room for the wires' bends");
    // Standoffs: in a leg or above the pots, clear of everything on each face.
    sp = [for (s = standoff_at) [s, ["r", s - [standoff_af / cos(30), standoff_af] / 2, s + [standoff_af / cos(30), standoff_af] / 2]]];
    jb_face = concat([for (j = jacks) [j[0], jack_body_rect(j[1])]],
                     [for (i = [0 : 2]) [layout_pots[i], ["r", pots[i] + [-pot_body[2] / 2, pot_body[0]], pots[i] + [pot_body[2] / 2, pot_body[1]]]]],
                     [["LED spacer", ["c", led, led_spacer_d / 2]],
                      ["J-B2B-MOD", rect_c(b2b_at, b2b_w + 2.54, b2b_l + 2.54)]]);
    heads = [for (s = standoff_at) ["standoff screw head", ["c", s, m3_head_d / 2]]];
    hf = worst(heads, jb_face);
    drc(hf[0] >= boards_part_clear, "standoff screw heads clear of the jack board's front-face parts", hf[0], str("mm (", hf[2], ")"));
    j_edge = minv([for (s = standoff_at) min(s[0] - b_x0, b_x1 - s[0], s[1] - b_y0, b_y1 - s[1],
                      (s[1] < notch[2] && s[0] > notch[0] - m3_head_d && s[0] < notch[1] + m3_head_d) ? min(abs(s[0] - notch[0]), abs(notch[1] - s[0])) : 1e9,
                      (s[1] < tnotch[3] + m3_head_d && s[1] > tnotch[2] && s[0] > tnotch[0] - m3_head_d && s[0] < tnotch[1] + m3_head_d) ? min(abs(s[0] - tnotch[0]), abs(tnotch[1] - s[0]), abs(s[1] - tnotch[3])) : 1e9) - m3_head_d / 2]);
    drc(j_edge >= boards_copper_edge, "standoff screw heads inside the boards' edges and the notch", j_edge, "mm, a head's edge to the nearest board edge");
    mb_rear = concat([["J-PWR-EURO", rect_c(pw, power_w, power_l)],
                      ["J-UMBILICAL tails", ["r", ec + [-9.28, -11.0], ec + [9.28, 12.35]]],
                      ["J-B2B-MOD tails", rect_c(b2b_at, b2b_w + 2.54, b2b_l + 2.54)]],
                     [for (i = [0 : len(tall_at) - 1]) let(t = tall_at[i]) [str("tall ", t[2], " ", i + 1),
                        t[2] == "cap" ? ["c", [t[0], t[1]], tall_cap_d / 2] : rect_c([t[0], t[1]], tall_trim[0], tall_trim[1])]],
                     [["U-ISO", iso_rect]], iso_filter_env);
    ie = min(iso_rect[1][0] - b_x0, b_x1 - iso_rect[2][0], iso_rect[1][1] - b_y0, b_y1 - iso_rect[2][1]);
    drc(ie >= 0, "U-ISO on the main board", ie, "mm, its body's edge inside the board's nearest edge");
    hr = worst(heads, mb_rear);
    drc(hr[0] >= boards_part_clear, "standoff screw heads clear of the main board's rear-face parts", hr[0], str("mm (", hr[2], ")"));
    rr = worst(mb_rear, mb_rear, true);
    drc(rr[0] >= boards_part_clear, "main board rear-face parts clear of each other", rr[0], str("mm (", rr[1], " / ", rr[2], ")"));
    mb_front = [["J-UMBILICAL body", ["r", ec - fl / 2, ec + fl / 2]], ["J-B2B-MOD", rect_c(b2b_at, b2b_w + 2.54, b2b_l + 2.54)]];
    sf = worst([for (s = sp) ["standoff", s[1]]], mb_front);
    drc(sf[0] >= boards_part_clear, "standoffs clear of the NE8FAV and J-B2B-MOD between the boards", sf[0], str("mm (", sf[2], ")"));
    jfp = [for (j = jacks) [str(j[0], " footprint"), jack_fp_rect(j[1])]];
    bj = worst([["J-B2B-MOD pads", rect_c(b2b_at, b2b_w + b2b_pad_d, b2b_l + b2b_pad_d)]], jfp);
    drc(bj[0] >= boards_part_clear, "J-B2B-MOD's pads clear of the jacks' footprints", bj[0], str("mm (", bj[2], "), between the two jack columns"));
    jj = worst(jfp, jfp, true);
    drc(jj[0] >= boards_part_clear, "jack footprints clear of each other", jj[0],
        str("mm (", jj[1], " / ", jj[2], "): body and pads, ", fp_u[1] - fp_u[0], " along the pin line, which lies across the panel"));
    drc(fp_u[1] - fp_u[0] + boards_part_clear > layout_jack_pitch_y, "why the jacks lie on their sides", [fp_u[1] - fp_u[0], layout_jack_pitch_y],
        "mm: a PJ398SM's footprint along its pin line, against the column's pitch - pins down the column would put one jack's sleeve pad on the next one's tip pad");
    jpe = min([for (j = jacks) let(r = jack_fp_rect(j[1])) min(r[1][0] - b_x0, b_x1 - r[2][0])]);
    drc(jpe >= boards_copper_edge, "jack pads inside the board's side edges", jpe, "mm, a sleeve pad's edge to the board's edge");
    nb = min([for (j = jacks) j[1][1] - fp_a]) - notch_top;
    drc(nb >= boards_copper_edge, "lowest jacks above the notch", nb, "mm, the lowest footprint's edge to the notch's top edge (its step for SW-POWER)");
    ln = min(led[0] - led_spacer_d / 2 - b_x0, notch[0] - led[0] - led_spacer_d / 2, tnotch[0] - led[0] - led_spacer_d / 2);
    drc(ln >= boards_copper_edge, "LED spacer on the jack board's leg", ln, "mm, the spacer's edge to the leg's edges (the LED's leads are soldered in the leg)");

    // ---- depth
    ds = [["the mated power socket with its ribbon folded over it", depth_max_rear],
          ["J-PWR-EURO shroud", mb_d + boards_t + power_h],
          ["tallest bulk cap (tbd height)", mb_d + boards_t + tall_cap_h],
          ["trimmer", mb_d + boards_t + tall_trim[2]],
          ["NE8FAV tails", mb_d + ethercon_tails],
          ["U-ISO", mb_d + boards_t + iso_body[2]]];
    dmax = max([for (d = ds) d[1]]);
    // Not a rule since 2026-09-30 - the owner: "Don't worry about module depth." Reported, not judged.
    echo("DRC", "INFO", "depth behind the panel, against the Intellijel Palette", [dmax, case_depth_max - dmax],
        str("mm behind the rear face, and to spare (", [for (d = ds) if (d[1] == dmax) d[0]][0], "); from the FRONT face ", dmax + T,
            " - not a rule: the owner, 2026-09-30, 'Don't worry about module depth'"));
    echo("DRC", "INFO", "depths of the deep things", ds, "mm behind the rear face");
    echo("DRC", "INFO", "tallest thing in front of the panel", front, "mm from the front face (the knob, unless the toggle's lever is longer)");

    // ---- legend zones
    for (l = legend) {
        g = worst([l], concat(plugs, knobs_max, ne8mx, face_other, washers));
        w = l[1][2][0] - l[1][1][0];
        h = l[1][2][1] - l[1][1][1];
        drc(g[0] >= 0 && h >= rules_legend_h - 1e-6 && (l[2] != "jack" || w >= rules_legend_w),
            str("legend zone: ", l[0]), [w, h, g[0]], str("mm wide, high, and clear of the nearest face part (", g[2], ")"));
    }

    // ---- the printed graphics' zones (ADR 0026)
    // Islands are surfaces - they run under nuts, and the ink pulls back from
    // every hole (tools/panel-art.py) - so they are checked for their gutters,
    // for holding their controls' legends and for staying off the washers.
    for (i = [0 : len(islands) - 2])
        drc(islands[i][1][1][1] - islands[i + 1][1][2][1] >= art_island_gap - 1e-6, str("art: gutter ", islands[i][0], " / ", islands[i + 1][0]),
            islands[i][1][1][1] - islands[i + 1][1][2][1], "mm of black frame between the two islands");
    iw = worst(islands, washers);
    drc(iw[0] >= 0, "art: islands clear of the panel screws' washers", iw[0], "mm, a washer anywhere along its slot");
    // Held = the zone's full height and its centre inside the island; a pot's
    // band is wider than its label, and the tool checks the ink itself.
    inside = function(r, R) r[1][1] >= R[1][1] - 1e-6 && r[2][1] <= R[2][1] + 1e-6
                            && (r[1][0] + r[2][0]) / 2 > R[1][0] && (r[1][0] + r[2][0]) / 2 < R[2][0];
    held = [for (l = legend) if (l[0] != "title") len([for (s = islands) if (inside(l[1], s[1])) 1]) > 0];
    drc(len([for (h = held) if (!h) 1]) == 0, "art: every control's legend zone inside one island", len([for (h = held) if (h) 1]),
        str("of ", len(held), " legend zones, by height and centre (the title is on the frame)"));
    ab = [islands[0][1][1][1] - legend[1][1][1][1], islands[1][1][2][1] - (layout_jack_y0 + jack_nut_d / 2)];
    drc(ab[0] <= 1e-6 && ab[1] >= 0, "art: gutter A|B between the first row's nuts and the pot legends", ab,
        "mm: island A's foot below the pot legend bands' foot (<= 0), island B's top above the first row's nuts (jack.nut_d is tbd)");
    for (z = [for (a = art_zones) if (a[2] != "island") a]) {
        w = z[1][2][0] - z[1][1][0];
        h = z[1][2][1] - z[1][1][1];
        others = concat(plugs, knobs_max, ne8mx, face_other, washers, [for (l = legend) [l[0], l[1]]],
                        [for (a = art_zones) if (a[2] != "island" && a[0] != z[0]) [a[0], a[1]]]);
        g = worst([z], others);
        need_h = z[2] == "header" ? art_header_h : z[2] == "mark" ? art_mark_size : rules_legend_h;
        drc(g[0] >= 0 && h >= need_h - 1e-6 && edge_gap(z[1]) >= art_frame - 1e-6, str("art zone: ", z[0]), [w, h, g[0]],
            str("mm wide, high, and clear of the nearest face part or zone (", g[2], ")"));
    }
}

// The printed graphics' geometry, for tools/panel-art.py and the Blender
// scene (ADR 0026) - every zone's POSITION, not only its size, and what
// stands on the face:
//   ECHO: "PANEL", "size", W, H, T
//   ECHO: "PANEL", "zone", name, x0, y0, x1, y1, kind     kind: title legend jack island header text mark
//   ECHO: "PANEL", "keepout", name, "c", x, y, r  |  "r", x0, y0, x1, y1
//   ECHO: "PANEL", "part", name, x, y, ...                where each part sits, for the scene
module panel_art() {
    echo("PANEL", "size", W, H, T);
    for (l = legend) echo("PANEL", "zone", l[0], l[1][1][0], l[1][1][1], l[1][2][0], l[1][2][1], l[0] == "title" ? "title" : l[2] == "jack" ? "jack" : "legend");
    for (a = art_zones) echo("PANEL", "zone", a[0], a[1][1][0], a[1][1][1], a[1][2][0], a[1][2][1], a[2]);
    kc = concat(knobs_max, plugs, ne8mx, face_other, washers, drop_zone,
                [for (j = jacks) [str("nut ", j[0]), ["c", j[1], jack_nut_d / 2]]],
                [["nut SW-POWER", ["c", tog, toggle_nut_d / 2]]]);
    for (k = kc) if (k[1][0] == "c") echo("PANEL", "keepout", k[0], "c", k[1][1][0], k[1][1][1], k[1][2]);
                 else echo("PANEL", "keepout", k[0], "r", k[1][1][0], k[1][1][1], k[1][2][0], k[1][2][1]);
    for (i = [0 : 2]) echo("PANEL", "part", layout_pots[i], pots[i][0], pots[i][1], "pot", pot_shaft_d, knob_d, knob_h, knob_gap);
    for (j = jacks) echo("PANEL", "part", j[0], j[1][0], j[1][1], "jack", jack_hole_d, jack_nut_d, jack_nut_h, jack_bushing_l - T);
    echo("PANEL", "part", "LED-PANEL", led[0], led[1], "led", led_lens_d, led_proud);
    echo("PANEL", "part", "SW-POWER", tog[0], tog[1], "toggle", tog_on[0], tog_on[1], lev_len, lev_d, lev_ang, tog_proud, toggle_nut_d, toggle_nut_h);
    echo("PANEL", "part", "J-UMBILICAL", ec[0], ec[1], "ethercon", ethercon_cable_d, plug_reach);
    for (i = [0 : 1]) echo("PANEL", "part", str("A-screw ", i + 1), ec_holes[i][0], ec_holes[i][1], "screw", ethercon_screw_head_d, ethercon_screw_head_h);
    for (i = [0 : len(mounts) - 1]) echo("PANEL", "part", str("panel screw ", i + 1), mounts[i][0], mounts[i][1], "mount", m3_head_d, m3_head_k, panel_washer_od, panel_washer_t);
    echo("PANEL", "part", "mark OFFSET-", mark_at[0][0], mark_at[0][1], "mark", -1);
    echo("PANEL", "part", "mark OFFSET+", mark_at[1][0], mark_at[1][1], "mark", 1);
}

// Where everything board-mounted is, for the layout - the body's pcb-geometry
// family: ECHO: "PCB", <board>, <kind>, <name>, x, y, ... in the panel frame
// (seen from the front, mm); KiCad's view of either board from the panel is
// this with y negated.
module pcb_geometry() {
    for (b = [["module-jack", b_x0, b_y0, b_x1, b_y1], ["module-main", b_x0, b_y0, b_x1, b_y1]])
        echo("PCB", b[0], "board", "outline", b[1], b[2], b[3], b[4]);
    echo("PCB", "module-jack", "cutout", "notch", notch[0], b_y0, notch[1], notch[2], "open to the bottom edge; the NE8FAV's body passes");
    echo("PCB", "module-jack", "cutout", "notch step", tnotch[0], tnotch[2], tnotch[1], tnotch[3], "on the notch's top edge, one cut-out with it; SW-POWER's body passes");
    echo("PCB", "module-jack", "board", "thickness", boards_t, "depth", jb_d, "side", "jacks, pots, LED on the front (toward the panel)");
    echo("PCB", "module-main", "board", "thickness", boards_t, "depth", mb_d, "side", "NE8FAV and J-B2B-MOD's insulator on the front; power header, trimmers, bulk caps on the rear");
    for (j = jacks) echo("PCB", "module-jack", "jack", j[0], j[1][0], j[1][1], jsgn(j[1]) > 0 ? 180 : 0,
                         "PJ398SM on its side: the angle (deg, from +x) from the barrel to the sleeve pad; pins 3, 2, 1 at this many mm along it", [-jack_pins[0], -jack_pins[1], -jack_pins[2]]);
    for (i = [0 : 2]) echo("PCB", "module-jack", "pot", layout_pots[i], pots[i][0], pots[i][1], 0, "R0904N, pins down at dy", pot_pins[0], "pitch", pot_pins[1]);
    echo("PCB", "module-jack", "led", "LED-PANEL", led[0], led[1], 0, "leads along x, pitch", led_pitch, "spacer", led_spacer_l);
    for (i = [0 : len(standoff_at) - 1]) {
        echo("PCB", "module-jack", "standoff", str("MECH-STANDOFF-MOD ", i + 1), standoff_at[i][0], standoff_at[i][1], standoff_hole_d, m3_head_d, so_l);
        echo("PCB", "module-main", "standoff", str("MECH-STANDOFF-MOD ", i + 1), standoff_at[i][0], standoff_at[i][1], standoff_hole_d, m3_head_d, so_l);
    }
    for (b = ["module-jack", "module-main"])
        echo("PCB", b, "connector", "J-B2B-MOD", b2b_at[0], b2b_at[1], 0, b2b_rows, b2b_pins, b2b_pitch, "long axis along y, pin 1 at the top left");
    echo("PCB", "module-main", "connector", "J-UMBILICAL", ec[0], ec[1], 0, "NE8FAV, latch up");
    echo("PCB", "module-main", "connector", "J-PWR-EURO", pw[0], pw[1], 0, "rear face, long axis along y, pin 1 (-12 V) at the bottom");
    for (i = [0 : len(tall_at) - 1]) echo("PCB", "module-main", "tall", tall_at[i][2], tall_at[i][0], tall_at[i][1], "rear face, an envelope - the layout places these");
    echo("PCB", "module-main", "tall", "U-ISO", iso_at[0], iso_at[1], "rear face, RP20-2412SAW body", iso_body, "; pins' tails out of the front face", iso_tail);
    for (f = iso_filter) echo("PCB", "module-main", "tall", f[5], f[0], f[1], "rear face, an envelope - the layout places these");
    echo("PCB", "module-main", "panel", "SW-POWER", tog[0], tog[1], str("panel-mounted, wired; lever ON ", layout_toggle_on, ", lugs in a line along the throw; lugs end"), zd(toggle_body[2] + toggle_lugs) - mb_z1, "in front of the main board");
    // Keep-outs: what each face must leave clear, and the height it allows.
    for (j = jacks) echo("PCB", "module-jack", "keepout", str("barrel ", j[0]), j[1][0], j[1][1], 3.0, "d, no copper under the barrel (Thonk's PJ398SM note)");
    for (b = ["module-jack", "module-main"]) for (s = standoff_at)
        echo("PCB", b, "keepout", "standoff head", s[0], s[1], m3_head_d + 2 * boards_part_clear, "d, no parts or copper");
    echo("PCB", "module-main", "keepout", "front: under the jack board", b_x0, b_y0, b_x1, b_y1, so_l - pot_legs + boards_t - boards_part_clear,
         "max part height on the front face where the pots' legs are; ", so_l - (jack_tails - boards_t) - boards_part_clear, " under a jack's tails");
    echo("PCB", "module-jack", "keepout", "rear: toward the main board", b_x0, b_y0, b_x1, b_y1, so_l - boards_part_clear, "max part height on the rear face, less whatever the main board puts under it");
    echo("PCB", "module-main", "keepout", "front: SW-POWER wiring", tog[0] - tog_body[0] / 2, tog[1] - tog_body[1] / 2, tog[0] + tog_body[0] / 2, tog[1] + tog_body[1] / 2,
         zd(toggle_body[2] + toggle_lugs) - mb_z1, "the lugs' ends above the front face");
    echo("PCB", "module-main", "keepout", "rear: ribbon fold", pw[0] + power_socket_w / 2 - power_ribbon_w, b_y0, pw[0] + power_socket_w / 2, pw[1] + power_socket_l / 2,
         mb_z0 - pw_top, "max part height on the rear face under the ribbon (the socket's back)");
}

// ============================================================== figure ====
// Legend zones, for the panel drawing.
module legend_2d() { for (l = legend) translate(l[1][1]) square(l[1][2] - l[1][1]); }

if (!figure) {
    if (part == "assembly") assembly();
    else if (part == "panel") panel_2d();
    else if (part == "jack_board") jack_board_2d();
    else if (part == "main_board") main_board_2d();
    else if (part == "drc") drc_report();
    else if (part == "pcb_geom") pcb_geometry();
    else if (part == "art") panel_art();
    else assert(false, str("unknown part ", part));
}
