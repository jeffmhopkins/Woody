// =====================================================================
// WOODY - EURORACK MODULE (10HP A-100 panel, three boards; ADR 0023, 0024)
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
//   part = "iso_board"     the iso board's outline, 2D (DXF)
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
pso_l = zd(0) - mb_z1;                     // MECH-PANEL-STANDOFF-MOD: the panel's rear face to the main board, derived

// ---------------------------------------------------------- panel parts ----
ec = [cx, layout_ec_y];
fl = [ethercon_flange_w, ethercon_flange_h];
pots = [for (i = [0 : 2]) [cx + (i - 1) * layout_pot_pitch, layout_pot_y]];
jack_rows = len(layout_jacks);
jacks = [for (r = [0 : jack_rows - 1], c = [0 : 1])
         [layout_jacks[r][c], [cx + (c - 0.5) * layout_jack_pitch_x, layout_jack_y0 - r * layout_jack_pitch_y]]];
// THE BOTTOM ROW IS THE NE8FAV (ADR 0024 point 11): its cable drops below
// every control. The toggle's row is above it, and the LED is in that row, in
// the strip beside the toggle: a panel-mount indicator in its own housing,
// wired to a header on the main board (point 16).
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

// LED (ADR 0024 point 16): LED-PANEL, a Dialight 605 panel-mount indicator -
// its chrome head on the face, its M5 housing through the panel and held by
// its nut behind - with its leads cut short and soldered to CBL-LED-PANEL, a
// two-wire lead that turns down and plugs into J-LED-PANEL, a JST B2B-XH-A on
// the main board's front face below it. What stands behind the panel, and
// where the wires run, is derived and DRC'd.
led_back = -led_body_l;                    // z of the housing's back (the head's shoulder is the front face)
led_tail_z = led_back - led_tail_l;        // z of the sleeved joints' end
led_tail_room = led_tail_z - mb_z1;        // derived: air between them and the main board's front face
hdr = led - [0, led_header_below];         // J-LED-PANEL, on the main board's front face
hdr_top = mb_z1 + led_header[2];           // the mated XHP-2's top, where the wires leave it
hdr_room = zd(0) - hdr_top;                // derived: from there to the panel's rear face
hdr_rect = ["r", hdr - [led_header[0], led_header[1]] / 2, hdr + [led_header[0], led_header[1]] / 2];
lead_w = 2 * led_wire_d;                   // the lead's two wires side by side
// The lead's path, centre line: out of the tail, down toward the header and
// forward into the gap, then down into the housing (a polyline; the clash
// check sees it as hulled spheres).
lead_path = [[led[0], led[1], led_tail_z + lead_w / 2], [led[0], led[1] - led_tail_d / 2 - lead_w, led_tail_z + lead_w / 2],
             [led[0], hdr[1] + led_header[1] / 2 + lead_w, hdr_top + 2 * lead_w], [led[0], hdr[1], hdr_top + 2 * lead_w]];
function plen(q, i = 0) = i >= len(q) - 1 ? 0 : norm(q[i + 1] - q[i]) + plen(q, i + 1);
lead_run = led_tail_l + plen(lead_path) + 2 * lead_w;     // the lead as laid, joint to crimp
lead_spare = led_cable_l - lead_run;

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
// THE JACK BOARD IS A PLAIN RECTANGLE (ADR 0024 point 15, the owner,
// 2026-10-01): full width, from just below the bottom jack row's footprints
// to the top edge the main board shares. SW-POWER's body and the NE8FAV are
// below it; nothing passes through it.
jb_y0 = boards_jack_y0;
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
// A trimmer's envelope [x, y, height]: a 3296 (trim) or TRIM-RESP's 3224W (trim_smd).
function trim_sz(t) = t[2] == "trim_smd" ? tall_trim_smd : tall_trim;
iso_tail = iso_pin_l - boards_t;           // derived: the pins stand this far out of the front face
iso_rect = rect_c(iso_at, iso_body[0], iso_body[1]);
// A toroid's envelope on the board: its terminals' cross, turned by f[8]
// degrees - the square that holds the terminals' outer corners, or the body,
// whichever is wider: [x, y, "toroid", span, height, refdes, body d, terminal w, rot].
function toroid_half(f) = max(f[6] / 2, let(a = f[8], t = [f[3] / 2, f[7] / 2])
    max([for (q = [[t[0], t[1]], [t[0], -t[1]], [t[1], t[0]], [-t[1], t[0]]]) abs(q[0] * cos(a) - q[1] * sin(a))]));
iso_filter_env = [for (f = iso_filter) [f[5], f[2] == "can" ? ["c", [f[0], f[1]], f[3] / 2]
                                          : f[2] == "toroid" ? rect_c([f[0], f[1]], 2 * toroid_half(f), 2 * toroid_half(f))
                                          : rect_c([f[0], f[1]], f[3], f[3])]];
// THE ISO BOARD (ADR 0023 point 2, amended 2026-10-03): U-ISO and its filter on a
// third board, BEHIND the main board, on the stock spacers uncut. Its outline is
// derived: the boards' side edges; its bottom edge boards.part_clear above the
// NE8FAV's tails (the same 12.35 the tails' envelope below uses); a notch at its
// lower right that J-PWR-EURO and its mated socket stand in; its top a leaf.
ib_gap = standoff_stock_l;                 // main board rear face to iso board front face
ib_z1 = mb_z0 - ib_gap;                    // iso board front face (toward the main board)
ib_z0 = ib_z1 - boards_t;                  // its rear face, where U-ISO and its filter stand
ib_y0 = ec[1] + 12.35 + boards_part_clear;
// the notch: J-PWR-EURO's body, its footprint's courtyard round it (0.5, as the layout draws it) and boards.part_clear
ib_notch = [pw[0] - power_w / 2 - 0.5 - boards_part_clear, pw[1] + power_l / 2 + 0.5 + boards_part_clear];
ib_poly = [[b_x0, ib_y0], [ib_notch[0], ib_y0], ib_notch, [b_x1, ib_notch[1]], [b_x1, iso_board_y1], [b_x0, iso_board_y1]];
ib_rects = [["r", [b_x0, ib_y0], [ib_notch[0], iso_board_y1]], ["r", [b_x0, ib_notch[1]], [b_x1, iso_board_y1]]];   // the L as two rectangles
function in_rect(A, R) = A[0] == "c" ? min(A[1][0] - A[2] - R[1][0], R[2][0] - A[1][0] - A[2], A[1][1] - A[2] - R[1][1], R[2][1] - A[1][1] - A[2])
                                     : min(A[1][0] - R[1][0], R[2][0] - A[2][0], A[1][1] - R[1][1], R[2][1] - A[2][1]);
function in_ib(A) = max([for (R = ib_rects) in_rect(A, R)]);   // how far inside the iso board's outline (< 0: out)
// J-B2B-ISO: 2 x b2b_iso.pins, long axis along x; insulator on the main board's rear face.
b2bi_l = (b2b_iso_pins - 1) * b2b_pitch;   // along x
b2bi_w = (b2b_iso_rows - 1) * b2b_pitch;   // along y
b2bi_rect = rect_c(b2b_iso_at, b2bi_l + 2.54, b2bi_w + 2.54);
b2bi_pin_l = b2b_tail + boards_t + ib_gap + boards_t + b2b_protrude;   // J-B2B-ISO's pins, derived
// The power ribbon's fold over the socket: the region behind the main board's rear face it lies in, and how far back it starts.
fold = [pw[0] + power_socket_w / 2 - power_ribbon_w, b_y0, pw[0] + power_socket_w / 2, pw[1] + power_socket_l / 2];
fold_h = mb_z0 - pw_top;

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
        // The panel standoffs' self-clinching studs (point 15): a plain hole; the head fills its displacement.
        for (s = panel_standoff_at) translate(s) circle(d = panel_standoff_stud_hole_d);
        translate(tog) rotate(tog_flat_rot) dhole2d(toggle_hole_d, toggle_flat);
        translate(ec) circle(d = ethercon_bore_d + ethercon_bore_clear);
        for (h = ec_holes) translate(h) circle(d = ethercon_hole_d);
        // No PUSH-tab slot: the tab stands ethercon.tab_back in front of the
        // flange face, clear of any panel up to the NE8FAV's panel_max (ADR 0024).
        if (ethercon_push_slot)
            translate([ec[0] - ethercon_tab_w / 2, ec[1] + ethercon_tab_bottom]) square([ethercon_tab_w, ethercon_tab_top - ethercon_tab_bottom]);
    }
}

module standoff_holes_2d(set) { for (s = set) translate(s) circle(d = standoff_hole_d); }
module jack_board_2d() {
    difference() {
        translate([b_x0, jb_y0]) square([b_x1 - b_x0, b_y1 - jb_y0]);
        standoff_holes_2d(standoff_at);
    }
}
module main_board_2d() {
    difference() {
        translate([b_x0, b_y0]) square([b_x1 - b_x0, b_y1 - b_y0]);
        standoff_holes_2d(standoff_at);
        standoff_holes_2d(panel_standoff_at);
        standoff_holes_2d(iso_board_standoff_at);
    }
}
module iso_board_2d() {
    difference() {
        polygon(ib_poly);
        standoff_holes_2d(iso_board_standoff_at);
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
        // The panel standoffs' studs: the head flush in the front face (drawn a hair proud, so it shows), the
        // shank behind the rear face, inside its spacer.
        for (i = [0 : len(panel_standoff_at) - 1])
            P(C_METAL, false, str("panel stud ", i + 1)) {
                cyl(panel_standoff_at[i], panel_standoff_stud_head_d, 0, 5 * EPS);
                cyl(panel_standoff_at[i], 3.0 - 0.02, -T + EPS, -panel_standoff_stud_l);   // the M3 shank (a nudge under the thread)
            }
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
// LED-PANEL, panel-mounted (ADR 0024 point 16): the chrome head on the face
// with the LED recessed in it, the housing through the panel, its nut and
// lock washer on the rear face, and the housing's back. Then CBL-LED-PANEL:
// the cut leads' sleeved joints and the lead, down into J-LED-PANEL's
// housing on the main board (drawn with the main board's layer).
module led_3d() {
    P(C_METAL, false, "LED-PANEL") difference() {
        union() {
            cyl(led, led_bezel_d, 0, led_proud);
            cyl(led, led_thread_d - 0.1, led_back, 0);
        }
        cyl(led, led_bezel_d - 1.3, led_proud - 0.8, led_proud + 1);
    }
    P(C_LED, false, "LED-PANEL lens") cyl(led, led_bezel_d - 1.3, led_proud - 0.8, led_proud - 0.3);
    P(C_METAL, false, "LED-PANEL nut") translate([led[0], led[1], zd(0) - led_nut_h]) difference() {
        cylinder(d = led_nut_d, h = led_nut_h, $fn = 6);
        translate([0, 0, -1]) cylinder(d = led_thread_d, h = led_nut_h + 2);
    }
    translate([0, 0, ex(-2)]) P(C_RED, false, "CBL-LED-PANEL") {
        cyl(led, led_tail_d, led_tail_z, led_back);
        for (i = [0 : len(lead_path) - 2]) hull() for (q = [lead_path[i], lead_path[i + 1]]) translate(q) sphere(d = lead_w, $fn = 16);
        cyl([led[0], hdr[1]], lead_w, hdr_top, hdr_top + 2 * lead_w);
    }
}
module jack_board_3d() {
    P(C_PCB, false, "jack board") slab(jb_z0, jb_z1) jack_board_2d();
    for (j = jacks) jack_3d(j);
    for (i = [0 : 2]) { pot_3d(layout_pots[i], pots[i]); knob_3d(layout_pots[i], pots[i]); }
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
        // The main board's two low mounting points: a spacer from the panel's rear face, on its stud.
        for (i = [0 : len(panel_standoff_at) - 1])
            P(C_METAL, false, str("panel standoff ", i + 1)) translate([panel_standoff_at[i][0], panel_standoff_at[i][1], mb_z1])
                difference() { cylinder(d = standoff_af / cos(30), h = pso_l, $fn = 6); translate([0, 0, -1]) cylinder(d = standoff_hole_d - 0.2, h = pso_l + 2); }
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
        for (i = [0 : len(panel_standoff_at) - 1])
            P(C_METAL, false, str("panel standoff screw rear ", i + 1)) cyl(panel_standoff_at[i], m3_head_d, mb_z0, mb_z0 - m3_head_k);
        // J-LED-PANEL, the JST B2B-XH-A with the lead's XHP-2 mated, on the front face; its pins' tails on the rear.
        P(C_NYLON, false, "J-LED-PANEL") box(hdr_rect[1][0], hdr_rect[1][1], mb_z1, hdr_rect[2][0], hdr_rect[2][1], hdr_top);
        P(C_BRASS, false, "J-LED-PANEL tails") for (i = [-0.5, 0.5]) cyl(hdr + [i * led_header_pitch, 0], 1.0, mb_z0 - 1.5, mb_z0, 12);
        // J-PWR-EURO: the shroud, its cavity open to the rear.
        P(C_BLACK, false, "J-PWR-EURO") difference() {
            box(pw[0] - power_w / 2, pw[1] - power_l / 2, mb_z0, pw[0] + power_w / 2, pw[1] + power_l / 2, mb_z0 - power_h);
            box(pw[0] - power_socket_w / 2 - 0.1, pw[1] - power_socket_l / 2 - 0.1, pw_seat, pw[0] + power_socket_w / 2 + 0.1, pw[1] + power_socket_l / 2 + 0.1, mb_z0 - power_h - 1);
        }
        // Tall parts: envelopes for the depth and clash checks, not placements.
        for (i = [0 : len(tall_at) - 1]) let(t = tall_at[i]) {
            if (t[2] == "cap") P(C_CAP, false, str("tall cap ", i + 1)) cyl([t[0], t[1]], tall_cap_d, mb_z0, mb_z0 - tall_cap_h);
            else let(sz = trim_sz(t)) P(C_TRIM, false, str("tall trimmer ", i + 1)) box(t[0] - sz[0] / 2, t[1] - sz[1] / 2, mb_z0, t[0] + sz[0] / 2, t[1] + sz[1] / 2, mb_z0 - sz[2]);
        }
        // J-B2B-ISO (ADR 0023, amended 2026-10-03): the insulator on the rear face, the tails out of the front.
        P(C_BLACK, false, "J-B2B-ISO") box(b2bi_rect[1][0], b2bi_rect[1][1], mb_z0, b2bi_rect[2][0], b2bi_rect[2][1], mb_z0 - b2b_insulator_h);
        P(C_BRASS, false, "J-B2B-ISO tails") b2bi_pins(mb_z1, mb_z1 + b2b_tail);
        for (i = [0 : len(iso_board_standoff_at) - 1])
            P(C_METAL, false, str("iso standoff screw front ", i + 1)) cyl(iso_board_standoff_at[i], m3_head_d, mb_z1, mb_z1 + m3_head_k);
    }
}
module b2bi_pins(z0, z1) {
    for (r = [0 : b2b_iso_rows - 1], k = [0 : b2b_iso_pins - 1])
        translate([b2b_iso_at[0] - b2bi_l / 2 + k * b2b_pitch - 0.32, b2b_iso_at[1] - b2bi_w / 2 + r * b2b_pitch - 0.32, min(z0, z1)])
            cube([0.64, 0.64, abs(z1 - z0)]);
}

// -- the iso board and what it carries (layer -2.5; ADR 0023 point 2, amended 2026-10-03) --
// U-ISO, RECOM RPA20-2412SAW (ADR 0027), and its filter on the iso board's REAR
// face; U-ISO's pins' tails out of its front face, into the gap; the spacers
// from the main board's rear face; J-B2B-ISO's posts through it.
module iso_board_3d() {
    translate([0, 0, ex(-2.5)]) {
        P(C_PCB2, false, "iso board") slab(ib_z0, ib_z1) iso_board_2d();
        P(C_METAL, false, "U-ISO") box(iso_at[0] - iso_body[0] / 2, iso_at[1] - iso_body[1] / 2, ib_z0,
                                       iso_at[0] + iso_body[0] / 2, iso_at[1] + iso_body[1] / 2, ib_z0 - iso_body[2]);
        P(C_BRASS, false, "U-ISO tails") for (q = iso_pins) cyl(iso_at + q, iso_pin_d, ib_z1, ib_z1 + iso_tail, 16);
        for (f = iso_filter)
            if (f[2] == "can") P(C_CAP, false, f[5]) cyl([f[0], f[1]], f[3], ib_z0, ib_z0 - f[4]);
            // a toroid: the body, and its four terminals on a cross at the board (2 tall, an estimate - the drawing does not dimension it)
            else if (f[2] == "toroid") P(C_BLACK, false, f[5]) union() {
                cyl([f[0], f[1]], f[6], ib_z0, ib_z0 - f[4]);
                translate([f[0], f[1], ib_z0 - 2]) rotate(f[8]) for (r = [0, 90]) rotate(r) translate([-f[3] / 2, -f[7] / 2, 0]) cube([f[3], f[7], 2]);
            }
            else P(C_BLACK, false, f[5]) box(f[0] - f[3] / 2, f[1] - f[3] / 2, ib_z0, f[0] + f[3] / 2, f[1] + f[3] / 2, ib_z0 - f[4]);
        for (i = [0 : len(iso_board_standoff_at) - 1]) {
            P(C_METAL, false, str("iso standoff ", i + 1)) translate([iso_board_standoff_at[i][0], iso_board_standoff_at[i][1], ib_z1])
                difference() { cylinder(d = standoff_af / cos(30), h = ib_gap, $fn = 6); translate([0, 0, -1]) cylinder(d = standoff_hole_d - 0.2, h = ib_gap + 2); }
            P(C_METAL, false, str("iso standoff screw rear ", i + 1)) cyl(iso_board_standoff_at[i], m3_head_d, ib_z0, ib_z0 - m3_head_k);
        }
        // in the gap, and out of the iso board's rear for the fillet (through the board is its own hole)
        P(C_BRASS, false, "J-B2B-ISO pins") b2bi_pins(mb_z0 - b2b_insulator_h, ib_z1);
        P(C_BRASS, false, "J-B2B-ISO posts rear") b2bi_pins(ib_z0, ib_z0 - b2b_protrude);
    }
}
// The toggle is panel-mounted and wired (ADR 0023): body on the panel's rear
// face, below the jack board's bottom edge; lever thrown to
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
    iso_board_3d();
    toggle_3d();
    led_3d();
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
                  [for (h = ec_holes) ["J-UMBILICAL screw", ["c", h, ethercon_hole_d / 2], "ec"]],
                  [for (s = panel_standoff_at) ["panel stud", ["c", s, panel_standoff_stud_hole_d / 2], ""]]);
cuts_mount = [for (m = mounts) ["mount slot", rect_c(m, panel_slot_travel + panel_hole_d, panel_hole_d)]];

// What stands on the panel's face, for spacing.
knobs_max = [for (i = [0 : 2]) [str("knob ", layout_pots[i]), ["c", pots[i], knob_d_max / 2]]];
knobs = [for (i = [0 : 2]) [str("knob ", layout_pots[i]), ["c", pots[i], knob_d / 2]]];
plugs = [for (j = jacks) [str("plug ", j[0]), ["c", j[1], jack_plug_d / 2]]];
ne8mx = [["NE8MX", ["c", ec, ethercon_cable_d / 2]]];
face_other = concat(
    [["PUSH tab", ["r", ec + [-ethercon_tab_w / 2, ethercon_tab_bottom], ec + [ethercon_tab_w / 2, ethercon_tab_top]]],
     ["SW-POWER sweep", tog_sweep_r],
     ["LED-PANEL", ["c", led, led_bezel_d / 2]]],
    [for (h = ec_holes) ["A-screw head", ["c", h, ethercon_screw_head_d / 2]]],
    [for (s = panel_standoff_at) ["panel stud head", ["c", s, panel_standoff_stud_head_d / 2]]]);
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
    [["LED-PANEL legend", ["r", [led[0] + led_bezel_d / 2 + 0.5, led[1] - rules_legend_h / 2], [tog_sweep_r[1][0] - 1, led[1] + rules_legend_h / 2]], ""],
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
row_top = max(tog_sweep_r[2][1], tog[1] + toggle_nut_d / 2, legend[len(legend) - 1][1][2][1], led[1] + led_bezel_d / 2);
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
                       ["LED-PANEL", ["c", led, led_bezel_d / 2]]]);
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
    drc(T <= led_panel_max, "panel within LED-PANEL's maximum", led_panel_max - T, "mm to spare (Dialight 605, its nut and lock washer)");
    ps_edge = minv([for (q = panel_standoff_at) min(q[0], W - q[0], q[1], H - q[1])]);
    drc(T >= panel_standoff_stud_sheet_min && ps_edge >= panel_standoff_stud_edge_min, "panel studs: sheet and edge distance (PEM)", [T, ps_edge],
        str("mm: the panel against the stud's ", panel_standoff_stud_sheet_min, " minimum sheet; each stud's centre to the nearest panel edge against PEM's ", panel_standoff_stud_edge_min));

    // ---- the stack
    echo("DRC", "INFO", "stack depths behind the panel's rear face", [jb_d, jb_d + boards_t, mb_d, mb_d + boards_t],
         "mm: jack board front and rear, main board front and rear - set by the PJ398SM's body and the NE8FAV's setback");
    drc(so_l > 0, "standoff length (derived)", so_l, "mm between the boards = the NE8FAV's setback less the jack's body and the jack board (MECH-STANDOFF-MOD)");
    face = standoff_stock_l - so_l;
    drc(abs(face) > standoff_tol ? (face > 0) : true, "standoff faced from stock", [standoff_stock_l, face],
        str("mm: the stock length, and what comes off it (a stock part is +/-", standoff_tol, "; face it and measure it, as the key boards' spacer)"));
    pface = panel_standoff_stock_l - pso_l;
    drc(pso_l > 0 && (abs(pface) > standoff_tol ? (pface > 0) : true), "panel standoff length (derived), faced from stock", [pso_l, panel_standoff_stock_l, pface],
        "mm: the panel's rear face to the main board's front face = the NE8FAV's setback (MECH-PANEL-STANDOFF-MOD); the stock length (tbd); what comes off it. The NE8FAV fixes that gap, so the spacer must match it, not set it");
    echo("DRC", "INFO", "panel stud in its spacer", [panel_standoff_stud_l - T, pso_l - (panel_standoff_stud_l - T)],
         "mm: the stud's shank behind the panel's rear face (its length code taken from the flush head, PEM FH), and what is left of the spacer's length for the main board's screw");
    drc(undef, "J-B2B-MOD pin length (derived)", b2b_pin_l,
        str("mm = ", b2b_protrude, " proud of the jack board + ", boards_t, " + the gap + ", boards_t, " + ", b2b_tail, " out of the main board"));
    drc(undef, "J-B2B-ISO pin length (derived)", b2bi_pin_l,
        str("mm = ", b2b_tail, " out of the main board's front + ", boards_t, " + the gap (the stock spacer, ", ib_gap, ") + ", boards_t, " + ", b2b_protrude,
            " out of the iso board's rear; the insulator on the main board's rear face"));

    // ---- the boards
    drc(b_y0 >= rail_band && b_y1 <= H - rail_band, "boards inside the rail band", [b_y0, b_y1], "mm, the boards' bottom and top edges (rail.band is tbd)");
    drc(b_x0 >= 0 && b_x1 <= W, "boards inside the panel's width", [b_x0, W - b_x1], "mm inside each side edge");
    echo("DRC", "INFO", "board outlines", [[b_x0, jb_y0, b_x1, b_y1], [b_x0, b_y0, b_x1, b_y1]],
         "mm: [x0, y0, x1, y1] of the jack board, a plain rectangle (ADR 0024 point 15), and of the main board");
    // The jack board ends just below the bottom jack row and above everything in the toggle's row.
    jfp_bot = min([for (j = jacks) j[1][1] - fp_a]);
    tog_top = tog[1] + tog_body[1] / 2;
    drc(jfp_bot - jb_y0 >= boards_copper_edge - 1e-6 && jb_y0 - tog_top >= boards_toggle_clear - 1e-6 && jb_y0 >= ec[1] + fl[1] / 2 + boards_part_clear,
        "jack board bottom edge", [jb_y0, jfp_bot - jb_y0, jb_y0 - tog_top, jb_y0 - ec[1] - fl[1] / 2],
        str("mm: the edge (boards.jack_y0); the bottom jack row's footprints above it (boards.copper_edge ", boards_copper_edge, "); it above SW-POWER's body (boards.toggle_clear ",
            boards_toggle_clear, ") and above the NE8FAV's body - nothing passes through the board"));
    drc(tog[1] - tog_body[1] / 2 >= ec[1] + fl[1] / 2 + boards_part_clear, "SW-POWER's body above the NE8FAV's", tog[1] - tog_body[1] / 2 - ec[1] - fl[1] / 2,
        "mm between the two bodies, behind the panel");
    // Behind the panel, inside the rail's depth: nothing may reach into the band.
    behind = concat([for (j = jacks) [j[0], j[1][1] - jack_body_w / 2, j[1][1] + jack_body_w / 2]],
                    [for (i = [0 : 2]) [layout_pots[i], pots[i][1] + pot_body[0], pots[i][1] + pot_body[1]]],
                    [["SW-POWER", tog[1] - tog_body[1] / 2, tog[1] + tog_body[1] / 2],
                     ["J-UMBILICAL", ec[1] - fl[1] / 2 - ethercon_peg_below, ec[1] + fl[1] / 2],
                     ["LED-PANEL nut", led[1] - led_nut_d / 2, led[1] + led_nut_d / 2],
                     ["J-LED-PANEL", hdr_rect[1][1], hdr_rect[2][1]]],
                    [for (s = standoff_at) ["standoff screw head", s[1] - m3_head_d / 2, s[1] + m3_head_d / 2]],
                    [for (s = panel_standoff_at) ["panel standoff", s[1] - standoff_af / cos(30) / 2, s[1] + standoff_af / cos(30) / 2]]);
    rb = [for (b = behind) [min(b[1] - rail_band, H - rail_band - b[2]), b[0]]];
    rbm = minv([for (r = rb) r[0]]);
    drc(rbm >= 0, "parts behind the panel clear of the rail band", rbm, str("mm (", [for (r = rb) if (r[0] == rbm) r[1]][0], "); rail.band is tbd"));
    tl = zd(toggle_body[2] + toggle_lugs) - mb_z1;
    // SW-POWER is fitted with ONE nut, on the front: its body bears on the
    // panel's rear face, as modelled. NKK's D4 hardware has a second hex nut
    // [ds NKK-SERIES-M-TOGGLE.pdf p.7]; it is NOT fitted behind the panel,
    // where it would move the body back by toggle.nut_h.
    drc(tl >= 0 && tl - toggle_nut_h >= 0, "toggle's lugs in front of the main board", [tl, tl - toggle_nut_h],
        "mm between the lugs' ends and the main board's front face - room for the wires' bends - with the body on the panel's rear face (ONE nut, on the front: fit it so); and if the D4 kit's second nut were fitted behind the panel, toggle.nut_h less (do not)");
    // Standoffs: two between the boards above the pots, two from the panel to
    // the main board low down (ADR 0024 point 15), clear of everything on each face.
    sp = [for (s = standoff_at) [s, ["r", s - [standoff_af / cos(30), standoff_af] / 2, s + [standoff_af / cos(30), standoff_af] / 2]]];
    psp = [for (s = panel_standoff_at) [s, ["c", s, standoff_af / cos(30) / 2]]];
    jb_face = concat([for (j = jacks) [j[0], jack_body_rect(j[1])]],
                     [for (i = [0 : 2]) [layout_pots[i], ["r", pots[i] + [-pot_body[2] / 2, pot_body[0]], pots[i] + [pot_body[2] / 2, pot_body[1]]]]],
                     [["J-B2B-MOD", rect_c(b2b_at, b2b_w + 2.54, b2b_l + 2.54)]]);
    heads = [for (s = standoff_at) ["standoff screw head", ["c", s, m3_head_d / 2]]];
    rheads = concat(heads, [for (s = panel_standoff_at) ["panel standoff screw head", ["c", s, m3_head_d / 2]]]);
    hf = worst(heads, jb_face);
    drc(hf[0] >= boards_part_clear, "standoff screw heads clear of the jack board's front-face parts", hf[0], str("mm (", hf[2], ")"));
    j_edge = minv([for (s = standoff_at) min(s[0] - b_x0, b_x1 - s[0], s[1] - jb_y0, b_y1 - s[1]) - m3_head_d / 2]);
    m_edge = minv([for (s = panel_standoff_at) min(s[0] - b_x0, b_x1 - s[0], s[1] - b_y0, b_y1 - s[1]) - m3_head_d / 2]);
    drc(min(j_edge, m_edge) >= boards_copper_edge, "standoff screw heads inside the boards' edges", [j_edge, m_edge],
        "mm, a head's edge to the nearest board edge: the standoffs between the boards (on the jack board), the panel standoffs (on the main board)");
    mb_tall = concat([["J-PWR-EURO", rect_c(pw, power_w, power_l)]],
                     [for (i = [0 : len(tall_at) - 1]) let(t = tall_at[i]) [str("tall ", t[2], " ", i + 1),
                        t[2] == "cap" ? ["c", [t[0], t[1]], tall_cap_d / 2] : rect_c([t[0], t[1]], trim_sz(t)[0], trim_sz(t)[1])]]);
    ib_spacers = [for (i = [0 : len(iso_board_standoff_at) - 1]) [str("iso standoff ", i + 1), ["c", iso_board_standoff_at[i], standoff_af / cos(30) / 2]]];
    mb_rear = concat(mb_tall,
                     [["J-UMBILICAL tails", ["r", ec + [-9.28, -11.0], ec + [9.28, 12.35]]],
                      ["J-B2B-MOD tails", rect_c(b2b_at, b2b_w + 2.54, b2b_l + 2.54)],
                      ["J-LED-PANEL tails", rect_c(hdr, led_header_pitch + 1.7, 2.0)],
                      ["J-B2B-ISO", b2bi_rect]], ib_spacers);

    // ---- the iso board (ADR 0023 point 2, amended 2026-10-03)
    ib_parts = concat([["U-ISO", iso_rect]], iso_filter_env);
    ibe = [for (e = ib_parts) [e[0], in_ib(e[1])]];
    drc(min([for (e = ibe) e[1]]) >= boards_copper_edge - 1e-6, "U-ISO and its filter on the iso board", ibe,
        "mm, each envelope's edge inside the iso board's outline, against boards.copper_edge (L-CM-ISO's turned 45 degrees: config/module.yaml iso.filter)");
    ib_rear = concat(ib_parts, [for (s = iso_board_standoff_at) ["iso standoff screw head", ["c", s, m3_head_d / 2]]],
                     [["J-B2B-ISO posts", rect_c(b2b_iso_at, b2bi_l + b2b_pad_d, b2bi_w + b2b_pad_d)]]);
    ibr = worst(ib_rear, ib_rear, true);
    drc(ibr[0] >= boards_part_clear, "iso board rear-face parts clear of each other", ibr[0], str("mm (", ibr[1], " / ", ibr[2], ")"));
    ibh = minv([for (s = iso_board_standoff_at) in_ib(["c", s, m3_head_d / 2])]);
    drc(ibh >= boards_copper_edge, "iso standoff screw heads inside the iso board's edges", ibh, "mm, a head's edge to the nearest edge of the iso board");
    ibp = in_ib(rect_c(b2b_iso_at, b2bi_l + b2b_pad_d, b2bi_w + b2b_pad_d));
    drc(ibp >= boards_copper_edge, "J-B2B-ISO's pads inside the iso board", ibp, "mm, the pads' edge to the iso board's nearest edge");
    drc(iso_tail + iso_board_under_h + boards_part_clear <= ib_gap, "iso board gap", [ib_gap, iso_tail, iso_board_under_h],
        str("mm: the gap (the stock spacer, uncut), U-ISO's tails out of the iso board's front, and the most a main board rear-face part may stand under it (iso_board.under_h) - tails + parts + boards.part_clear inside the gap"));
    drc(ib_gap > b2b_insulator_h + boards_part_clear, "J-B2B-ISO's insulator in the gap", ib_gap - b2b_insulator_h, "mm from its top to the iso board's front face");
    // Nothing on the main board's rear face that stands taller than under_h may be under the iso board.
    mt = [for (t = concat(mb_tall, [["J-UMBILICAL tails", ["r", ec + [-9.28, -11.0], ec + [9.28, 12.35]]]])) [t[0], -in_ib(t[1])]];
    drc(min([for (t = mt) t[1]]) >= boards_part_clear, "main board's tall rear-face parts clear of the iso board", mt,
        "mm in plan from each (J-PWR-EURO, the bulk caps, the trimmers, the NE8FAV's tails) to the iso board's outline");
    // The power ribbon folds over the socket, behind the main board: where the iso board is under it, its parts must stay below the fold.
    ib_fold = [for (e = concat(ib_parts, [["J-B2B-ISO posts", rect_c(b2b_iso_at, b2bi_l, b2bi_w)]]))
               if (gap2(e[1], ["r", [fold[0], fold[1]], [fold[2], fold[3]]]) < 0) e[0]];
    ib_fold_h = max(concat([0], [for (e = ib_parts) if (gap2(e[1], ["r", [fold[0], fold[1]], [fold[2], fold[3]]]) < 0)
                                   let(f = [for (g = iso_filter) if (g[5] == e[0]) g]) len(f) ? f[0][4] : iso_body[2]],
                           [for (x = ib_fold) if (x == "J-B2B-ISO posts") b2b_protrude]));
    drc(ib_gap + boards_t + ib_fold_h + boards_part_clear <= fold_h, "iso board under the power ribbon's fold", [ib_fold, ib_gap + boards_t + ib_fold_h, fold_h],
        "mm: the iso board's parts under the fold in plan, how far back the tallest of them reaches from the main board's rear face, and where the fold starts");
    hr = worst(rheads, mb_rear);
    drc(hr[0] >= boards_part_clear, "standoff screw heads clear of the main board's rear-face parts", hr[0], str("mm (", hr[2], ")"));
    rr = worst(mb_rear, mb_rear, true);
    drc(rr[0] >= boards_part_clear, "main board rear-face parts clear of each other", rr[0], str("mm (", rr[1], " / ", rr[2], ")"));
    // Every trimmer is adjusted from BEHIND with the module out of the rack:
    // its slot faces away from the board, and nothing but the power ribbon
    // is behind the rear face. A screwdriver's shaft goes straight in, so a
    // TALLER part beside it must stand off by the shaft's radius - checked
    // against each trimmer's centre (the slot is inside the body), and the
    // ribbon's fold must not be over it.
    let(tr = [for (i = [0 : len(tall_at) - 1]) let(t = tall_at[i]) if (t[2] != "cap") [i, t]],
        // the iso board's parts stand behind the iso board: taller, from the main board's rear face, by the gap and the board
        hts = concat([for (i = [0 : len(tall_at) - 1]) let(t = tall_at[i]) t[2] == "cap" ? tall_cap_h : trim_sz(t)[2]],
                     [ib_gap + boards_t + iso_body[2]], [for (f = iso_filter) ib_gap + boards_t + f[4]], [ib_gap + boards_t, ib_gap + boards_t]),
        envs = concat([for (i = [0 : len(tall_at) - 1]) let(t = tall_at[i]) t[2] == "cap" ? ["c", [t[0], t[1]], tall_cap_d / 2] : rect_c([t[0], t[1]], trim_sz(t)[0], trim_sz(t)[1])],
                      [iso_rect], [for (e = iso_filter_env) e[1]], ib_rects),
        acc = [for (q = tr) let(t = q[1], h = trim_sz(t)[2],
                   d = min(concat([for (k = [0 : len(envs) - 1]) if (k != q[0] && hts[k] > h) gap2(["c", [t[0], t[1]], 0], envs[k])], [1e9])),
                   under = t[0] > fold[0] && t[0] < fold[2] && t[1] > fold[1] && t[1] < fold[3])
                 [str(t[2], " ", q[0] + 1), under ? -1 : d - rules_driver_d / 2]])
        drc(min([for (a = acc) a[1]]) >= 0, "trimmers adjustable from behind", acc,
            str("mm from each trimmer's centre to the nearest TALLER rear-face part - the iso board and what stands on it counted from the main board's rear face - less a ", rules_driver_d, " mm screwdriver's radius (rules.driver_d), with the module out of the rack; -1 = under the power ribbon's fold"));
    mb_front = [["J-UMBILICAL body", ["r", ec - fl / 2, ec + fl / 2]], ["J-B2B-MOD", rect_c(b2b_at, b2b_w + 2.54, b2b_l + 2.54)]];
    sf = worst([for (s = sp) ["standoff", s[1]]], mb_front);
    drc(sf[0] >= boards_part_clear, "standoffs clear of the NE8FAV and J-B2B-MOD between the boards", sf[0], str("mm (", sf[2], ")"));
    // The panel standoffs stand in the whole depth from the panel to the main
    // board: clear of the NE8FAV's body and pegs, the toggle's body and lugs,
    // LED-PANEL's nut, J-LED-PANEL, and below the jack board.
    p_front = [["J-UMBILICAL body", ["r", ec - fl / 2 - [0, ethercon_peg_below], ec + fl / 2]],
               ["SW-POWER body", rect_c(tog, tog_body[0], tog_body[1])],
               ["LED-PANEL nut", ["c", led, led_nut_d / 2]],
               ["J-LED-PANEL", hdr_rect],
               ["jack board", ["r", [b_x0, jb_y0], [b_x1, b_y1]]]];
    pf = worst([for (s = psp) ["panel standoff", s[1]]], p_front);
    drc(pf[0] >= boards_part_clear, "panel standoffs clear of the NE8FAV, SW-POWER, the LED and the jack board", pf[0], str("mm (", pf[2], "), across the corners of the hex"));
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
    // LED-PANEL behind the panel (ADR 0024 point 16): its nut, housing and
    // sleeved joints stand in the gap between the panel and the main board,
    // below the jack board; the lead turns down there to J-LED-PANEL.
    // what stands out of the main board's front face low down: J-B2B-ISO's tails, the iso standoffs' screw heads
    mb_front_low = concat([["J-B2B-ISO tails", rect_c(b2b_iso_at, b2bi_l + b2b_pad_d, b2bi_w + b2b_pad_d)]],
                          [for (s = iso_board_standoff_at) ["iso standoff screw head", ["c", s, m3_head_d / 2]]]);
    drc(led_tail_room >= 3 * led_wire_d, "LED-PANEL behind the panel: in front of the main board", [led_body_l - T, led_tail_l, led_tail_room],
        str("mm: the housing behind the panel's rear face, the cut leads' sleeved joints behind it, and what is left to the main board's front face - room for the lead's wires to turn (3 x led.wire_d, ",
            3 * led_wire_d, "); uncut, the leads would reach through the board"));
    lc = worst([["LED-PANEL nut", ["c", led, led_nut_d / 2]], ["LED-PANEL tail", ["c", led, led_tail_d / 2]]],
               concat([["jack board", ["r", [b_x0, jb_y0], [b_x1, b_y1]]], ["SW-POWER body", rect_c(tog, tog_body[0], tog_body[1])],
                       ["J-UMBILICAL body", ["r", ec - fl / 2, ec + fl / 2]], ["J-LED-PANEL", hdr_rect]],
                      [for (s = psp) ["panel standoff", s[1]]], mb_front_low));
    drc(lc[0] >= boards_part_clear, "LED-PANEL behind the panel: clear of the jack board, SW-POWER, the NE8FAV, the panel standoffs and J-LED-PANEL", lc[0],
        str("mm in plan (", lc[1], " / ", lc[2], "); led.nut_d is tbd"));
    he = min(hdr_rect[1][0] - b_x0, b_x1 - hdr_rect[2][0], hdr_rect[1][1] - b_y0);
    hc = worst([["J-LED-PANEL", hdr_rect]], concat(mb_front_low, [["J-UMBILICAL body", ["r", ec - fl / 2, ec + fl / 2]]],
                                                  [for (s = panel_standoff_at) ["panel standoff head keep-out", ["c", s, m3_head_d / 2 + boards_part_clear]]]));
    drc(he >= boards_copper_edge && hc[0] >= boards_part_clear, "J-LED-PANEL on the main board's front face", [he, hc[0]],
        str("mm: the mated header's body to the board's edge (boards.copper_edge ", boards_copper_edge, "), and to the nearest front-face part (", hc[2], ")"));
    drc(hdr_room >= 3 * led_wire_d, "J-LED-PANEL's mated housing behind the panel: room for the lead to turn", [led_header[2], hdr_room],
        "mm: the B2B-XH-A with its XHP-2 mated above the main board's front face, and what is left to the panel's rear face for the wires leaving its top (3 x led.wire_d)");
    lp = ["r", [led[0] - lead_w / 2, hdr[1]], [led[0] + lead_w / 2, led[1]]];
    lw = worst([["CBL-LED-PANEL", lp]], concat(mb_front_low, [["SW-POWER body", rect_c(tog, tog_body[0], tog_body[1])]],
                                              [for (s = psp) ["panel standoff", s[1]]]));
    drc(lw[0] >= boards_part_clear && lead_spare >= 0, "CBL-LED-PANEL's run, LED to header", [lw[0], lead_run, lead_spare],
        str("mm: the lead's two wires, in plan, to the nearest part they pass (", lw[2], "); the run as laid, joint to crimp; and what is left of led.cable_l (",
            led_cable_l, ") to fold into the gap once the board is home"));

    // ---- depth
    ds = [["the mated power socket with its ribbon folded over it", depth_max_rear],
          ["J-PWR-EURO shroud", mb_d + boards_t + power_h],
          ["tallest bulk cap (tbd height)", mb_d + boards_t + tall_cap_h],
          ["trimmer", mb_d + boards_t + tall_trim[2]],
          ["NE8FAV tails", mb_d + ethercon_tails],
          ["the iso board's tallest part", mb_d + boards_t + ib_gap + boards_t + max(concat([iso_body[2]], [for (f = iso_filter) f[4]]))]];
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
    echo("PANEL", "part", "LED-PANEL", led[0], led[1], "led", led_bezel_d, led_proud);
    for (i = [0 : len(panel_standoff_at) - 1]) echo("PANEL", "part", str("panel stud ", i + 1), panel_standoff_at[i][0], panel_standoff_at[i][1], "stud", panel_standoff_stud_head_d);
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
    for (b = [["module-jack", b_x0, jb_y0, b_x1, b_y1], ["module-main", b_x0, b_y0, b_x1, b_y1]])
        echo("PCB", b[0], "board", "outline", b[1], b[2], b[3], b[4]);
    echo("PCB", "module-iso", "board", "outline", ib_poly);
    echo("PCB", "module-jack", "board", "thickness", boards_t, "depth", jb_d, "side", "jacks and pots on the front (toward the panel); a plain rectangle, no cut-out");
    echo("PCB", "module-main", "board", "thickness", boards_t, "depth", mb_d, "side", "NE8FAV, J-LED-PANEL and J-B2B-MOD's insulator on the front; power header, J-B2B-ISO's insulator, trimmers, bulk caps on the rear");
    echo("PCB", "module-iso", "board", "thickness", boards_t, "depth", mb_d + boards_t + ib_gap, "side", "U-ISO and its filter on the REAR (away from the main board); J-B2B-ISO's posts through it; the front faces the main board's rear across the gap");
    for (j = jacks) echo("PCB", "module-jack", "jack", j[0], j[1][0], j[1][1], jsgn(j[1]) > 0 ? 180 : 0,
                         "PJ398SM on its side: the angle (deg, from +x) from the barrel to the sleeve pad; pins 3, 2, 1 at this many mm along it", [-jack_pins[0], -jack_pins[1], -jack_pins[2]]);
    for (i = [0 : 2]) echo("PCB", "module-jack", "pot", layout_pots[i], pots[i][0], pots[i][1], 0, "R0904N, pins down at dy", pot_pins[0], "pitch", pot_pins[1]);
    echo("PCB", "module-main", "connector", "J-LED-PANEL", hdr[0], hdr[1], 0, "JST B2B-XH-A, top entry, FRONT face, row along x: pin 1 (LED_ANODE) on the left seen from the panel, pin 2 (AGND_MOD) on the right; pitch", led_header_pitch, "; mated height", led_header[2]);
    echo("PCB", "module-main", "panel", "LED-PANEL", led[0], led[1], "panel-mounted (Dialight 605), its lead plugged into J-LED-PANEL; its sleeved joints end", led_tail_room, "in front of the main board");
    for (i = [0 : len(standoff_at) - 1]) {
        echo("PCB", "module-jack", "standoff", str("MECH-STANDOFF-MOD ", i + 1), standoff_at[i][0], standoff_at[i][1], standoff_hole_d, m3_head_d, so_l);
        echo("PCB", "module-main", "standoff", str("MECH-STANDOFF-MOD ", i + 1), standoff_at[i][0], standoff_at[i][1], standoff_hole_d, m3_head_d, so_l);
    }
    for (i = [0 : len(panel_standoff_at) - 1])
        echo("PCB", "module-main", "standoff", str("MECH-PANEL-STANDOFF-MOD ", i + 1), panel_standoff_at[i][0], panel_standoff_at[i][1], standoff_hole_d, m3_head_d, pso_l);
    for (i = [0 : len(iso_board_standoff_at) - 1]) for (b = ["module-main", "module-iso"])
        echo("PCB", b, "standoff", str("MECH-STANDOFF-ISO ", i + 1), iso_board_standoff_at[i][0], iso_board_standoff_at[i][1], standoff_hole_d, m3_head_d, ib_gap);
    for (b = ["module-main", "module-iso"])
        echo("PCB", b, "connector", "J-B2B-ISO", b2b_iso_at[0], b2b_iso_at[1], 0, b2b_iso_rows, b2b_iso_pins, b2b_pitch,
             b == "module-main" ? "long axis along x, pin 1 at the bottom left seen from the panel, its pair above it; TOP side (F.Cu), NOT mirrored - the insulator is on this board's rear, but each pin is one straight conductor through both boards, so both KiCad top views (panel views) take the same unmirrored pin map"
                                : "long axis along x, pin 1 at the bottom left seen from the panel, its pair above it; top side (F.Cu), the posts through this board from the main board's side");
    for (b = ["module-jack", "module-main"])
        echo("PCB", b, "connector", "J-B2B-MOD", b2b_at[0], b2b_at[1], 0, b2b_rows, b2b_pins, b2b_pitch,
             b == "module-jack" ? "long axis along y, pin 1 at the top left; TOP side (F.Cu), NOT mirrored - the header's body is on this board's rear, but each pin is one straight conductor through both boards, so pin k sits at the same panel-frame place on both, and both KiCad top views are panel views: the same unmirrored pin map as the main board. Placed on B.Cu it mirrors, and every net lands one column over"
                                : "long axis along y, pin 1 at the top left; top side (F.Cu), the insulator on this face");
    echo("PCB", "module-main", "connector", "J-UMBILICAL", ec[0], ec[1], 0, "NE8FAV, latch up");
    echo("PCB", "module-main", "connector", "J-PWR-EURO", pw[0], pw[1], 0, "rear face, long axis along y, pin 1 (-12 V) at the bottom");
    for (i = [0 : len(tall_at) - 1]) echo("PCB", "module-main", "tall", tall_at[i][2], tall_at[i][0], tall_at[i][1], "rear face, an envelope - the layout places these");
    echo("PCB", "module-iso", "tall", "U-ISO", iso_at[0], iso_at[1], "rear face, RPA20-2412SAW body", iso_body, "; pins' tails out of the front face", iso_tail);
    for (f = iso_filter) if (f[2] == "toroid")
        echo("PCB", "module-iso", "tall", f[5], f[0], f[1], str("rear face, woody:L_CommonModeChoke_Bourns_PM3700 turned ", f[8], " degrees (its span over the terminals, ", f[3], ", does not fit square here); an envelope - the layout places it"));
        else echo("PCB", "module-iso", "tall", f[5], f[0], f[1], "rear face, an envelope - the layout places these");
    echo("PCB", "module-main", "panel", "SW-POWER", tog[0], tog[1], str("panel-mounted, wired, ONE nut on the front (the body on the panel's rear face; the D4 kit's second nut not fitted); lever ON ", layout_toggle_on, ", lugs in a line along the throw; lugs end"), zd(toggle_body[2] + toggle_lugs) - mb_z1, "in front of the main board");
    // Keep-outs: what each face must leave clear, and the height it allows.
    for (j = jacks) echo("PCB", "module-jack", "keepout", str("barrel ", j[0]), j[1][0], j[1][1], 3.0, "d, no copper under the barrel (Thonk's PJ398SM note)");
    for (b = ["module-jack", "module-main", "module-iso"])
        for (s = b == "module-main" ? concat(standoff_at, panel_standoff_at, iso_board_standoff_at) : b == "module-iso" ? iso_board_standoff_at : standoff_at)
        echo("PCB", b, "keepout", "standoff head", s[0], s[1], m3_head_d + 2 * boards_part_clear,
             b == "module-jack" ? "d, no parts and no copper but the mount's own pad, which is AGND_MOD (metal standoffs; power-entry.md Grounding)"
                                : "d, no parts and no copper but the mount's own pad, on no net (metal standoffs; power-entry.md Grounding)");
    echo("PCB", "module-main", "keepout", "front: under the jack board", b_x0, jb_y0, b_x1, b_y1, so_l - pot_legs + boards_t - boards_part_clear,
         "max part height on the front face where the pots' legs are; ", so_l - (jack_tails - boards_t) - boards_part_clear, " under a jack's tails");
    echo("PCB", "module-jack", "keepout", "rear: toward the main board", b_x0, jb_y0, b_x1, b_y1, so_l - boards_part_clear, "max part height on the rear face, less whatever the main board puts under it");
    echo("PCB", "module-main", "keepout", "front: SW-POWER wiring", tog[0] - tog_body[0] / 2, tog[1] - tog_body[1] / 2, tog[0] + tog_body[0] / 2, tog[1] + tog_body[1] / 2,
         zd(toggle_body[2] + toggle_lugs) - mb_z1, "the lugs' ends above the front face");
    echo("PCB", "module-main", "keepout", "front: under LED-PANEL", led[0] - led_nut_d / 2, led[1] - led_nut_d / 2, led[0] + led_nut_d / 2, led[1] + led_nut_d / 2,
         led_tail_room - boards_part_clear, "max part height on the front face under the LED's housing and its sleeved joints");
    echo("PCB", "module-main", "keepout", "rear: ribbon fold", fold[0], fold[1], fold[2], fold[3], fold_h, "max part height on the rear face under the ribbon (the socket's back)");
    for (R = ib_rects)
        echo("PCB", "module-main", "keepout", "rear: under the iso board", R[1][0], R[1][1], R[2][0], R[2][1], iso_board_under_h,
             "max part height on the rear face under the iso board (iso_board.under_h); U-ISO's tails stand out of the iso board's front into the same gap");
    for (R = ib_rects)
        echo("PCB", "module-iso", "keepout", "front: toward the main board", R[1][0], R[1][1], R[2][0], R[2][1], iso_board_under_h,
             "max part height on the front face (it faces the main board's rear, across the gap)");
    echo("PCB", "module-iso", "keepout", "rear: ribbon fold", fold[0], fold[1], fold[2], fold[3], fold_h - ib_gap - boards_t - boards_part_clear,
         "max part height on the rear face under the power ribbon's fold (it starts this far behind the iso board)");
}

// ============================================================== figure ====
// Legend zones, for the panel drawing.
module legend_2d() { for (l = legend) translate(l[1][1]) square(l[1][2] - l[1][1]); }

if (!figure) {
    if (part == "assembly") assembly();
    else if (part == "panel") panel_2d();
    else if (part == "jack_board") jack_board_2d();
    else if (part == "main_board") main_board_2d();
    else if (part == "iso_board") iso_board_2d();
    else if (part == "drc") drc_report();
    else if (part == "pcb_geom") pcb_geometry();
    else if (part == "art") panel_art();
    else assert(false, str("unknown part ", part));
}
