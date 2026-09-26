// =====================================================================
// WOODY - INSTRUMENT BODY
// A laminated stack of flat parts, every layer a 2D through-cut (ADR 0009).
//
// DO NOT PUT NUMBERS HERE. Dimensions come from generated/params.scad, which
// tools/cad.py writes from config/key-layout.yaml and config/body.yaml - each
// value there carries its source and a status (settled / nominal / tbd).
// This file holds GEOMETRY: how those numbers become parts. The few literal
// numbers below are drawing conventions (clearances for pictures, colours)
// and are named as such.
//
//   part = "assembly"            the instrument, 3D (default)
//   part = "<layer>"             one flat part, 2D, as it is cut - see LAYERS
//   part = "drc"                 the design-rule report, echo only
//
// Coordinates: X along the body from the mouthpiece end, Y across, Z up from
// the bottom face. The key plate's frame maps as X = x0 + y, Y = y0 + x.
//
// Render with `python3 tools/cad.py build`, never by hand into renders/:
// the build fingerprints every image against this file and its inputs.
// =====================================================================

include <generated/params.scad>

part = "assembly";
explode = 0;          // mm between layers in the exploded view
show_lid = true;
show_u = true;
show_caps = true;
show_keys = true;
show_boards = true;
show_hardware = true;
show_strips = true;
highlight = [];   // solid ids to draw bright yellow, the rest faded (fig_centre.scad)
show_routing = true;
ghost_shell = false;  // draw the shell translucent to see inside
// Sections. "y" / "x" clip every part with a half-space (keep Y < cut, or
// a slab X > cut) and stay 3D. "y2d" / "x2d" are true section DRAWINGS: each
// part cut by the plane with projection(cut = true), coloured per part, laid
// flat - "y2d" as (X, Z), "x2d" as (Y, Z) looking toward the tail. Use the
// 2D ones for anything dimensioned; OpenCSG loses part colours on 3D cuts.
cut = "none";
cut_at = 0;
cut_key = "";         // or name a key (or "matrix", or "ribbon" for the left key board's): the cut goes through its centre
cut_depth = 1000;     // "x" keeps a slab this deep beyond the cut
figure = false;       // set true by a figure that includes this file
// Where X = 0 sits in the rendered picture: "mouth" (the model's own frame),
// "centre" or "tail". Cameras aim at the origin, so a render stays framed
// when the derived length changes.
origin = "mouth";

LAYERS = ["plate_top", "oak_top", "oak_bottom", "oak_grooves", "thumb_plate", "side",
          "mouth_cap", "tail_cap", "ubolt_backplate",
          "matrix_window", "oak_rebates"];

$fn = 40;
EPS = 0.01;           // drawing convention: coplanar-face nudge

// ---------------------------------------------------------------- frame ----
// L, THE OVERALL LENGTH, IS DERIVED (owner, 2026-09-26: "minimize total
// length"). It is computed below the key layout, from the keys, the
// underside and the connector - see "length" - not read from a register.
W = envelope_width;
T = envelope_thickness;

// KEYS ARE FLUSH AT FULL TRAVEL (decided 2026-09-26): a pressed cap's top is
// level with the top face. So the plate sits UNDER the oak top, and the oak
// is exactly as thick as the cap stands above the seat at the bottom of its
// stroke. At rest each cap stands proud by the travel.
oak_top_t = switch_keycap_top_above_seat - switch_total_travel;
// Thumb keys too (same date): the thumb plate is on the oak bottom's inside
// face, so the same rule sets the oak bottom from below.
oak_bottom_t = switch_keycap_top_above_seat - switch_total_travel;
z_oak_top_bot = T - oak_top_t;                  // underside of the oak = plate top face
z_plate_top = z_oak_top_bot;                    // the switch seat
z_plate_bot = z_plate_top - plate_thickness;
z_lid_bot = z_plate_bot;                        // the lid's underside is the plate's
z_floor = oak_bottom_t;                   // inside face of the oak bottom
z_thumb_top = z_floor + plate_thickness;        // thumb plate, on the inside face
cavity_h = z_lid_bot - z_floor;

lid_t = T - z_lid_bot;
// The sides stand BETWEEN the oak panels, in grooves (decided 2026-09-26):
// oak top and bottom are full width, each side is set in by an oak lip.
side_y = [stack_side_inset, W - stack_side_inset - stack_side_t];   // outer face of each side
groove_w = stack_side_t + 2 * stack_groove_clear;
u_y0 = stack_side_inset + stack_side_t;         // inside face of the left side
u_w = W - 2 * u_y0;                             // the interior, between the sides
z_side0 = z_floor - stack_groove_depth;         // side's bottom edge, in the bottom groove
z_side1 = z_oak_top_bot + stack_groove_depth;   // side's top edge, in the top groove
x_in0 = ends_mouth_cap_t;                       // between the end caps

// The key plate's origin (config/key-layout.yaml: "top-left of key plate").
plate_x0 = x_in0;
plate_y0 = u_y0;                                // the plate sits between the sides

// ------------------------------------------------------- length budget ----
function sum(v, i = 0) = i >= len(v) ? 0 : v[i] + sum(v, i + 1);
function cum(v, i) = i <= 0 ? 0 : sum([for (j = [0 : i - 1]) v[j]]);
lh_run = sum(layout_lh_gaps);
rh_run = sum(layout_rh_gaps);
// THE THUMB KEYS ARE SPACED AND CUT LIKE THE TOP (owner, 2026-09-26: "spacing
// between keys need to be right like the top"): the top's pitch between
// adjacent keys, the top's cap-to-oak clearance, and - when the top uses one
// slot per hand - one slot per group of thumb keys either side of a rest.
thumb_recess_clear = stack_cap_clear;
rc = switch_keycap + 2 * thumb_recess_clear;    // a thumb recess, square
thumb_pitch = layout_lh_gaps[0];                 // the top's index-to-middle pitch
cluster_margin = 4;        // drawing convention: board edge past the outermost switch body

// The MOUTH END. There is no display (owner, 2026-09-26: "remove the upper
// display ... we can do all this with the matrix led"; ADR 0015), so the
// keys start where the first top cap clears the mouth cap, the first thumb
// recess clears it too, and the breath trap fits across the mouth band
// before the first key board and thumb row. Everything is measured from x_in0,
// the inside face of the mouth cap.
// The left-thumb cluster's extent relative to LH1 (x_lh0 = 0), recesses included.
// A straight line: a pair, the thumb rest, a pair (owner, 2026-09-26).
// THE THUMB RESTS ARE DIRECTLY UNDER THE MIDDLE-FINGER KEYS (owner,
// 2026-09-26): layout.lt_rest_under / rt_rest_under name the key. Measured
// along its hand's provisional gaps, so it is known before the hands are
// placed; when key-layout.yaml gets real x/y this wants the key's own x.
function run_rel(id) = cum(id[0] == "L" ? layout_lh_gaps : layout_rh_gaps, ord(id[2]) - 49);
lt_rest_rel = run_rel(layout_lt_rest_under);
// TWO ROWS ACROSS THE BODY, the rest between them (owner, 2026-09-26: "left
// thumb with dual horizontal rows too, with gap still in the middle"): LT1 /
// LT2 side by side toward the mouth, LT3 / LT4 side by side toward the tail.
lt_rel = [for (i = [0 : 3]) lt_rest_rel + (i < 2 ? -1 : 1) * layout_lt_rest / 2];
lt_dy = [for (i = [0 : 3]) (i % 2 == 0 ? -1 : 1) * thumb_pitch / 2];   // across, from the centreline
// The breath trap sits mid-height, above the main board's parts, so it has
// to clear the first KEY board: clash.txt checks it against the main board.
// The breath sensor is at the mouth end too (ADR 0017), and its leads must
// stop short of the first thumb row's pins.
ks33_stub = 2.6;   // half-width of the KS-33's pole and pins where they stand proud of a board [clash.txt, off the vendor STEP]
board_lead = plate_cutout / 2 + cluster_margin;   // first key board edge before LH1
trap_band = boards_board_clear + routing_trap_l + boards_board_clear;
mouth_names = ["the first top key", "the first thumb recess", "the breath trap before the first boards",
               "the breath sensor before the first thumb row"];
mouth_claims = [x_in0 + layout_mouth_extra + switch_keycap / 2 + stack_cap_clear,
                x_in0 + layout_underside_clear - (min(lt_rel) - rc / 2),
                x_in0 + trap_band + board_lead,
                x_in0 + boards_board_clear + 0.5 + boards_sensor_body / 2 + boards_sensor_lead_row / 2 + ks33_stub + 0.5 - min(lt_rel)];
mouth_req = max(mouth_claims);

// The TAIL's needs, measured from the last top key's centre. Everything at
// the tail hangs off the right hand, so it can be worked out in the right
// hand's own frame (x_rh0 = 0) before the right hand is placed.
rt_rest_rel = [run_rel(layout_rt_rest_under), W / 2];
// Like the left thumb (owner, 2026-09-26: "four keys right thumb too"):
// RT1 / RT2 side by side a half rest toward the mouth, RT3 / RT4 a half rest
// toward the tail.
function rt_rel(i) = rt_rest_rel + [(i < 2 ? -1 : 1) * layout_rt_rest / 2, (i % 2 == 0 ? -1 : 1) * thumb_pitch / 2];
top_last_rel = max([for (i = [0 : len(layout_rh_gaps)]) cum(layout_rh_gaps, i)]);
rt_last_rel = max([for (i = [0 : count("right_thumb") - 1]) rt_rel(i)[0]]);
// BEHIND THE MATRIX, IN ORDER (2026-09-26): the USB-C extension's plug off
// the Matrix's tail edge (if that edge faces the tail), a clearance, the
// RJ45 plug and boot mated into the etherCON's rear socket, then the
// etherCON body to the tail face.
usb_behind = openings_matrix_usb_to_tail ? openings_usb_plug_l : 0;
// STACKED (owner, 2026-09-26): the rear socket and the patch plug pass UNDER
// the Matrix, so behind it only the etherCON's full-height housing queues.
behind_matrix = usb_behind + layout_tail_clear + ethercon_housing_d + ends_tail_cap_t;
// IN FRONT OF IT: the USB-C plug off the mouth edge (if that edge faces the
// mouth) and the patch plug both reach forward, and the last fastener pair
// stands in front of whichever is first; all of it must clear the right-hand
// key board. Measured from the last key centre to where the equipment starts.
usb_front = openings_matrix_usb_to_tail ? 0 : openings_usb_plug_l;
tail_fastener_back = 3;    // drawing convention: last fastener centre to the tail equipment
equip_start_rel = plate_cutout / 2 + cluster_margin + layout_tail_clear + tail_fastener_back + 3 / 2;
tail_claims_rel = [
    top_last_rel + equip_start_rel + ethercon_rj45_plug_l + ethercon_depth + ends_tail_cap_t,
    top_last_rel + plate_cutout / 2 + cluster_margin + layout_tail_clear + boards_matrix_board + behind_matrix,
    rt_last_rel + rc / 2 + layout_underside_clear + ends_tail_cap_t];
// The LED matrix CENTRED in the space after the keys (owner, 2026-09-26):
// midway between the last cap's slot edge and the tail face. The connector
// still has to fit behind it, so the tail grows to whatever that takes:
// centre = (edge + tail) / 2, and centre + half board + clearance + depth
// <= tail, so tail >= edge + 2 x (half board + clearance + depth).
cap_edge_rel = switch_keycap / 2 + stack_cap_clear;
matrix_centred_req = max(cap_edge_rel + 2 * (boards_matrix_board / 2 + behind_matrix),
                         2 * (equip_start_rel + usb_front + boards_matrix_board / 2) - cap_edge_rel);
tail_req = max(max(tail_claims_rel) - top_last_rel, layout_matrix_centred ? matrix_centred_req : 0);

// EQUAL BANDS (owner, 2026-09-26): the space before the left hand, between
// the hands and after the right hand are the same - the largest any of them
// needs. Measured as the plan drawing labels them: body end to the first
// key centre, last left key to the first right key, last key to the tail.
// The tail is sized by its own contents (above) and is NOT one of the equal
// bands since the matrix was centred in it (owner, 2026-09-26).
band = layout_equal_bands ? max(mouth_req, layout_gap) : undef;
// THE GAP BETWEEN THE HANDS MATCHES THE KEYS-TO-MATRIX GAP (owner, same
// day): the clear space from the last left cap to the first right cap equals
// the clear space from the last cap to the matrix window's near edge. The
// matrix is centred in the tail, so that space is known before the right
// hand is placed: (cap slot edge + tail) / 2 - half window - half cap.
matrix_clear = (cap_edge_rel + tail_req) / 2 - openings_matrix_window / 2 - switch_keycap / 2;
gap_c2c = layout_gap_matches_matrix ? max(layout_gap, matrix_clear + switch_keycap)
        : layout_equal_bands ? band : layout_gap;
x_lh0 = layout_equal_bands ? band : mouth_req;
x_gap0 = x_lh0 + lh_run;
x_rh0 = x_gap0 + gap_c2c;
x_tail0 = x_rh0 + rh_run;
// -------------------------------------------------------------- keys ------
function key_id(k) = k[0];
function key_face(k) = k[1];
function key_n(k) = ord(k[0][2]) - 48;
function count(cl) = len([for (k = keys) if (k[6] == cl) 1]);
function lerp(a, b, t) = a + (b - a) * t;

// Provisional positions, used only while a key's x/y is null.
function prov_xy(k) =
    let(cl = k[6], i = key_n(k) - 1, n = count(cl), c = W / 2)
    cl == "left_hand"  ? [x_lh0 + cum(layout_lh_gaps, i), c + layout_lh_offsets[i]] :
    cl == "right_hand" ? [x_rh0 + cum(layout_rh_gaps, i), c + layout_rh_offsets[i]] :
    cl == "left_thumb" ? [x_lh0 + lt_rel[i], c + lt_dy[i]] :
    cl == "right_thumb" ? rt_xy(i) : [0, 0];

// The thumb rest: the gap in the middle of the left-thumb line.
lt_rest_xy = [x_lh0 + (lt_rel[1] + lt_rel[2]) / 2, W / 2];
rt_rest = [x_rh0, 0] + rt_rest_rel;
// The thumb keys either side of each rest, as groups: one oak slot each
// when stack.cap_holes is "slot", as the top has one per hand.
function thumb_slots() = [for (cl = ["left_thumb", "right_thumb"])
    let(r = cl == "left_thumb" ? lt_rest_xy[0] : rt_rest[0], ks = cluster_keys(cl))
    for (before = [true, false]) let(g = [for (k = ks) if ((key_xy(k)[0] < r) == before) k]) if (len(g) > 0) g];
// Right-thumb control switches, either side of the rest (ADR 0010).
function rt_xy(i) = [x_rh0, 0] + rt_rel(i);
// NO SPARE-SWITCH CUTOUTS (owner, 2026-09-26: the right thumb is "only the
// three", the left thumb the four in a line). ADR 0010 reserved three; the
// chain bits stay reserved (config/key-layout.yaml), the cutouts do not.
spare_xy = [];

// THE TAIL END, and so the length. Past the last top key: its cluster board's
// overhang, a clearance, and the etherCON's depth behind the tail face - the
// connector cannot sit under the key boards (drc.echo, etherCON height). The
// underside's right-thumb cluster must also be inside.
top_last = max([for (k = keys) if (k[1] == "top") key_xy(k)[0]]);
rt_last = max([for (k = keys) if (k[1] == "bottom") key_xy(k)[0]]);
// THE LED MATRIX IS ON THE TOP FACE, after the last key (owner, 2026-09-26):
// the Matrix board face up under the plate, past the last key board. The
// last fastener pair stands in front of the tail equipment (see below).
matrix_near_x = top_last + plate_cutout / 2 + cluster_margin + layout_tail_clear + boards_matrix_board / 2;
function matrix_x(l) = layout_matrix_centred ? (top_last + cap_edge_rel + l) / 2 : matrix_near_x;

L = top_last + tail_req;
x_in1 = L - ends_tail_cap_t;
matrix_xy = [matrix_x(L), W / 2];
// Where an X section cuts: a number, a key id, or "matrix" for its centre.
// A Y cut through a named key goes through its Y (its row along the body).
function cut_pos() = cut_key == "" ? cut_at : cut_key == "matrix" ? matrix_xy[0] : cut_key == "ribbon" ? ffc_x("left_hand")
        : key_xy(key_by_id(cut_key))[cut == "y" || cut == "y2d" ? 1 : 0];

function placed(k) = !is_undef(k[2]) && !is_undef(k[3]);
function key_xy(k) = placed(k) ? [plate_x0 + k[3], plate_y0 + k[2]] : prov_xy(k);
function key_rot(k) = k[4];
top_keys = [for (k = keys) if (key_face(k) == "top") k];
bottom_keys = [for (k = keys) if (key_face(k) == "bottom") k];
function cluster_keys(cl) = [for (k = keys) if (k[6] == cl) k];
function xs(list) = [for (k = list) key_xy(k)[0]];
function key_by_id(id) = [for (k = keys) if (k[0] == id) k][0];

// ----------------------------------------------------------- colours ------
C_OAK = [0.71, 0.53, 0.33];
C_OAK_DARK = [0.60, 0.43, 0.26];
C_ACRYLIC = [0.88, 0.93, 0.98, 0.55];
C_ALU = [0.78, 0.80, 0.83];
C_PCB = [0.16, 0.42, 0.24];
C_SWITCH = [0.18, 0.18, 0.20];
C_CAP = [0.93, 0.91, 0.86];
C_SPARE = [0.85, 0.20, 0.60];
C_STEEL = [0.55, 0.57, 0.60];
C_CONN = [0.25, 0.25, 0.27];
C_LED = [1.0, 0.75, 0.30];
C_FROSTED = [0.94, 0.95, 0.97, 0.85];

// ----------------------------------------------------------- clipping -----
module clip_space() {
    big = 4 * L;
    if (cut == "y") translate([-big / 2, cut_pos() - big, -big / 2]) cube(big);
    else if (cut == "x") translate([cut_pos(), -big / 2, -big / 2]) cube([cut_depth, big, big]);
}
// Every solid goes through P() WITH A NAME, so colour survives a section cut
// and the clash check can pull any one solid out on its own:
//   only = "<id>"      draw just that solid (tools/cad.py clash)
//   list_solids = true  echo every solid's id (the clash check's inventory)
only = "";
list_solids = false;
function id_match(h, id) = h == id || (h[len(h) - 1] == "*" && len(id) >= len(h) - 1
    && (len(h) == 1 || [for (i = [0 : len(h) - 2]) id[i]] == [for (i = [0 : len(h) - 2]) h[i]]));
module P(c, shell = false, id = "") {
    assert(id != "", "every solid needs an id - the clash check cannot see an unnamed one");
    if (list_solids) echo("SOLID", id);
    // highlight: solids named in it are drawn bright yellow and the rest
    // faded, so one assembly can be picked out of the body in a render. An
    // entry ending in "*" matches every id that starts with the rest of it.
    hl = len(highlight) > 0;
    cc = hl && len([for (h = highlight) if (id_match(h, id)) 1]) > 0 ? [1.0, 0.85, 0.0]
       : hl ? [c[0], c[1], c[2], 0.18]
       : (shell && ghost_shell) ? [c[0], c[1], c[2], 0.25] : c;
    if (only == "" || only == id) color(cc)
        if (cut == "none") children();
        else if (cut == "y2d")
            mirror([0, 1]) section_2d() rotate([90, 0, 0]) translate([0, -cut_pos(), 0]) children();
        else if (cut == "x2d")
            rotate(-90) section_2d() rotate([0, -90, 0]) translate([-cut_pos(), 0, 0]) children();
        else intersection() { children(); clip_space(); }
}

// The part's section in the plane z = 0. projection(cut = true) warns
// "Projection() failed" on a part that never reaches the plane (a side
// lamina, on the centreline), and a build that tolerated that warning would
// tolerate a real failure too. A 0.02 mm slab first makes a miss an empty
// result, not an error.
module section_2d() {
    projection() intersection() {
        children();
        translate([-1e4, -1e4, -0.01]) cube([2e4, 2e4, 0.02]);
    }
}

// ================================================================ 2D ======
// Each flat part in its OWN sheet frame, as it goes to the cutter. The
// assembly places these; the DXF exports are exactly these.

module rrect(x, y, r = 0.5) {
    offset(r) offset(-r) square([x, y]);
}
// SANDED EDGES (stack.edge_r). A panel's long edges: its (y, z) section
// with every corner rounded, run the panel's length. A cap's outer face:
// rounded all round, the inner face square where it meets the body.
module sanded_panel(len, t) {
    rotate([90, 0, 90]) linear_extrude(len) rrect(W, t, stack_edge_r);
}
module sanded_cap(t) {
    hull() {
        linear_extrude(t - stack_edge_r) rrect(W, T, stack_edge_r);
        translate([0, 0, t - stack_edge_r]) minkowski() {
            linear_extrude(EPS) offset(-stack_edge_r) square([W, T]);
            sphere(stack_edge_r, $fn = 16);
        }
    }
}
module cutout_at(xy, rot, s) {
    translate(xy) rotate(rot) square([s, s], center = true);
}

// Key plate: lid footprint, in the plate's own frame = model XY minus origin.
module plate_top_2d() {
    difference() {
        translate([0, stack_groove_clear]) square([plate_x1 - x_in0, u_w - 2 * stack_groove_clear]);
        translate([-plate_x0, -plate_y0]) {
            for (k = top_keys) cutout_at(key_xy(k), key_rot(k), plate_cutout);
            for (f = fasteners()) translate(f) circle(d = tap_d_m3);
        }
    }
}
tap_d_m3 = 2.5;   // drawing convention: M3 tap drill; see the DRC on thread engagement

// Oak top: the lid's wood, ON TOP of the plate, full width. One hole per key
// (or one slot per hand), which the cap travels in. No fastener holes - the
// fasteners stop in the plate, so the playing face is unbroken oak. The side
// grooves are NOT in this outline: they are a saw cut, not a through-cut,
// and export separately (oak_grooves_2d). Frame: model XY minus [x_in0, 0].
module oak_top_2d() {
    difference() {
        square([x_in1 - x_in0, W]);
        translate([-x_in0, 0])
            if (stack_cap_holes == "slot")
                for (cl = ["left_hand", "right_hand"]) keys_2d(cluster_keys(cl), switch_keycap + 2 * stack_cap_clear);
            else
                for (k = top_keys) translate(key_xy(k)) rotate(key_rot(k))
                    square(switch_keycap + 2 * stack_cap_clear, center = true);
        translate([-x_in0, 0]) translate(matrix_xy) square(openings_matrix_window, center = true);
    }
}

// The U's floor. Thumb recesses are the through-cuts (ADR 0009: "oak
// thickness sets the inset depth"), plus the
// fastener and U-bolt holes. Full width; grooves as for the oak top.
// Frame: model XY minus [x_in0, 0].
module oak_bottom_2d() {
    difference() {
        square([x_in1 - x_in0, W]);
        translate([-x_in0, 0]) {
            if (stack_cap_holes == "slot")
                for (g = thumb_slots()) keys_2d(g, rc);
            else
                for (k = bottom_keys) translate(key_xy(k)) rotate(key_rot(k)) square(rc, center = true);
            for (s = spare_xy) translate(s) square(switch_keycap + 2 * thumb_recess_clear, center = true);
            for (f = fasteners()) translate(f) circle(d = hardware_fastener_clear_d);
            for (u = ubolt_legs()) translate(u) circle(d = ubolt_hole_d);
        }
    }
}

// The outline a thumb cluster's plate and board share, before cutouts.
function thumb_pts(cl) = [for (k = cluster_keys(cl)) key_xy(k)];
module thumb_outline_2d(cl) {
    intersection() {
        hull() for (p = thumb_pts(cl)) translate(p) square(switch_keycap + 4, center = true);
        translate([x_in0, u_y0 + 0.5]) square([x_in1 - x_in0, u_w - 1]);
    }
}
// One thumb plate per thumb cluster, on the oak bottom's inside face.
// Frame: model XY.
module thumb_plate_2d(cl) {
    difference() {
        thumb_outline_2d(cl);
        for (k = cluster_keys(cl)) cutout_at(key_xy(k), key_rot(k), plate_cutout);
    }
}
module thumb_plate_both_2d() { thumb_plate_2d("left_thumb"); thumb_plate_2d("right_thumb"); }

// The acrylic side: one sheet, standing in a groove in each oak panel.
// Frame: X along, Y = model Z from the side's bottom edge.
module side_2d() { square([x_in1 - x_in0, z_side1 - z_side0]); }

// The grooves, for the shop: one line pair per side, groove_depth deep, cut
// along each oak panel's inner face. A saw or router pass - the ONE operation
// in the stack that is not a through-cut, and deliberately so: it is what
// holds the sides between the oak. Frame: as the oak panels.
module oak_grooves_2d() { for (y = side_y) translate([0, y - stack_groove_clear]) square([x_in1 - x_in0, groove_w]); }

// End caps, full cross-section. Frame: X = model Y, Y = model Z.
module mouth_cap_2d() {
    difference() {
        rrect(W, T, stack_edge_r);
        translate(tube_yz) circle(d = ends_tube_hole_d);
    }
}
tube_yz = [W / 2, z_floor + cavity_h / 2];

// The NE8FDP's rear envelope, rotated with the connector: [across Y, height Z].
ec_house = ethercon_rotated ? [ethercon_housing_h, ethercon_housing_w] : [ethercon_housing_w, ethercon_housing_h];
ec_fl = ethercon_rotated ? [ethercon_flange_h, ethercon_flange_w] : [ethercon_flange_w, ethercon_flange_h];
// The housing and the flange behind the cap both stand in the cavity.
ec_env = [max(ec_house[0], ec_fl[0]), max(ec_house[1], ec_fl[1])];
ec_clear = 0.3;    // drawing convention: connector envelope to the floor, and its socket to the Matrix
// THE CONNECTOR STANDS ON THE FLOOR (owner, 2026-09-26: raise the body's
// thickness rather than pocket the oak bottom). Its axis is derived: the
// envelope sits ec_clear above the oak bottom, and the body is made thick
// enough that the rear socket still passes under the Matrix (drc.echo).
ec_c = [W / 2 + ethercon_offset_y, z_floor + ec_clear + ec_env[1] / 2];    // etherCON centre on the tail face
ec_sock = ethercon_rotated ? [ethercon_socket_h, ethercon_socket_w] : [ethercon_socket_w, ethercon_socket_h];
ec_plug = ethercon_rotated ? [ethercon_rj45_plug_h, ethercon_rj45_plug_w] : [ethercon_rj45_plug_w, ethercon_rj45_plug_h];
// The rear socket sits off the axis: 0.35 + half its height, on the side away from the latch.
ec_sock_off_mag = 0.35 + ethercon_socket_h / 2;
ec_sock_dir = (W / 2 - ec_c[0] >= 0 ? 1 : -1) * (ethercon_socket_toward_centre ? 1 : -1);
ec_panel_x = L - ends_tail_cap_t;                  // flange and chassis sit behind the tail cap's inside face
ec_sock_c = ethercon_rotated ? ec_c + [ec_sock_dir * ec_sock_off_mag, 0] : ec_c - [0, ec_sock_off_mag];
ec_holes = [for (s = [-1, 1]) ec_c + s * (ethercon_rotated ? [ethercon_hole_dy, ethercon_hole_dx] : [ethercon_hole_dx, ethercon_hole_dy]) / 2];
// The USB-C extension's receptacle (owner, 2026-09-26): beside the
// etherCON, 2 mm of oak clear of its flange on the tail face, inside the
// sides, at the cavity's mid height.
usb_web_min = 2;   // drawing convention: oak between two tail-face cutouts
usb_c = [min(max(ec_c[0] + ec_fl[0] / 2, ec_c[0] + ec_house[0] / 2) + usb_web_min + openings_usb_slot_w / 2, W - u_y0 - openings_usb_slot_w / 2),
         z_floor + cavity_h / 2];

module tail_cap_2d() {
    difference() {
        rrect(W, T, stack_edge_r);
        translate(ec_c) circle(d = ethercon_bore_d);
        for (h = ec_holes) translate(h) circle(d = ethercon_hole_d);
        translate(usb_c) square([openings_usb_slot_w, openings_usb_slot_h], center = true);
    }
}
// The U-bolt's backplate, on the oak bottom's inside face under the nuts: it
// spreads the strap load over the oak (ADR 0009: "let the oak be the face the
// screws pass through rather than the thing the screws hold"). The gap
// fastener pair stands at the same station, so across the body the plate
// stops at their clearance circle - the oak's own clearance round the screw -
// and is located by the legs alone; the screws never pass through it.
ubolt_bp = [hardware_ubolt_span, u_w - 2 * (hardware_fastener_inset + hardware_fastener_clear_d / 2)];
module ubolt_backplate_2d() {
    difference() {
        translate(ubolt_c) square(ubolt_bp, center = true);
        for (u = ubolt_legs()) translate(u) circle(d = ubolt_hole_d);
    }
}
// The matrix window: frosted acrylic, flush with the oak top, on an oak lip
// (owner, 2026-09-26). The acrylic is the rebate's size less a fit clearance.
matrix_rebate = openings_matrix_window + 2 * openings_matrix_lip;
module matrix_window_2d() { translate(matrix_xy) offset(r = 0.5) offset(delta = -0.6) square(matrix_rebate, center = true); }
// Rebates in the oak top's upper face - a router pass, like the grooves, so
// exported on their own. Frame: as the oak panels.
module oak_rebates_2d() { translate([-x_in0, 0]) translate(matrix_xy) square(matrix_rebate, center = true); }

// --------------------------------------------------------- features ------
// Each key's square, unioned, then CLOSED (grow, shrink) so squares closer
// than 2 x close merge into one outline that follows the keys round an
// offset or a side-by-side pair. Hulling key to key instead left diagonal
// wedges wherever the order zig-zags across a pair.
module keys_2d(ks, s, close = 1.5) {
    offset(delta = -close) offset(delta = close)
        for (k = ks) translate(key_xy(k)) rotate(key_rot(k)) square(s, center = true);
}
   // drawing convention: board edge past the outermost switch body
// A top cluster board: the switch footprints, chained, grown to the board
// width over a single line (switch.cluster_pcb_w). Outline is an M3 output.
module cluster_window_2d(ks) {
    offset(delta = (switch_cluster_pcb_w - plate_cutout) / 2) keys_2d(ks, plate_cutout, close = 3);
}

// Tail equipment: the Matrix, the etherCON and the USB-C extension.
// TIGHT TO THE WINDOW (owner, 2026-09-26: "led matrix tighter to the
// acrylic"). The key plate stops short of the Matrix, so the board's top
// face sits against the oak top's underside and its LEDs stand up into the
// window opening through the oak lip, under the acrylic.
matrix_board_z = z_oak_top_bot - switch_pcb_t;
matrix_top_z = z_oak_top_bot + boards_matrix_led_h;              // LED tops
// The key plate ends before the Matrix, so past it the lid is the oak alone.
plate_x1 = matrix_xy[0] - boards_matrix_board / 2 - 1;
// The USB-C extension's plug, in the Matrix's mouth or tail edge.
usb_plug_x0 = openings_matrix_usb_to_tail ? matrix_xy[0] + boards_matrix_board / 2 : matrix_xy[0] - boards_matrix_board / 2 - openings_usb_plug_l;
// The tail equipment starts at the first of that plug and the patch plug.
// The last fastener pair stands just in front of it - beside the Matrix the
// patch plug runs down the side lane.
tail_equip_x = min(usb_plug_x0, L - ends_tail_cap_t - ethercon_depth - ethercon_rj45_plug_l);
tail_fastener_x = tail_equip_x - tail_fastener_back;
fastener_notch = 1.5 + boards_board_clear;   // an M3's radius and a clearance: what a board or a run keeps from a screw

// Six fasteners up from the bottom into the plate, zig-zagging between the
// long edges ~80 mm apart (ADR 0009).
// Three stations of two, one each side: in the mouth band before the first
// boards, in the gap between the hands, and between the last key board and
// the connector. ADR 0009's "~80 mm apart" was for a 457 mm body; on the
// derived body the stations fall where the keys are not.
fastener_x = [(x_in0 + x_lh0 - board_lead) / 2, (x_gap0 + x_rh0) / 2, tail_fastener_x];
function fasteners() =
    [for (x = fastener_x, sd = [0, 1]) [x, sd == 0 ? u_y0 + hardware_fastener_inset : W - u_y0 - hardware_fastener_inset]];

// U-bolt in the inter-hand gap on the bottom face (ADR 0009); legs ACROSS the
// body, since the shortened gap has no room along it beside the left thumb line.
ubolt_c = [(x_gap0 + x_rh0) / 2, W / 2];
function ubolt_legs() = [for (s = [-1, 1]) ubolt_c + [0, s * hardware_ubolt_span / 2]];
ubolt_hole_d = hardware_ubolt_rod_d + 0.5;   // drawing convention: the legs' clearance hole in the oak and the backplate

// ================================================================ 3D ======

// The etherCON housing's bottom below the floor, if the connector is low.

module lam(z, t, c, shell = true, id = "") {
    P(c, shell, id) translate([0, 0, z]) linear_extrude(t) children();
}

module lid(dz = 0) {
    translate([0, 0, dz]) {
        P(C_OAK, true, "oak top") translate([x_in0, 0, z_oak_top_bot + explode]) intersection() { sanded_panel(x_in1 - x_in0, oak_top_t); difference() {
            linear_extrude(oak_top_t) oak_top_2d();
            translate([0, 0, -EPS]) linear_extrude(stack_groove_depth + EPS) oak_grooves_2d();
            translate([0, 0, oak_top_t - openings_matrix_acrylic_t]) linear_extrude(openings_matrix_acrylic_t + EPS) oak_rebates_2d();
        } }
        lam(z_plate_bot + explode / 2, plate_thickness, C_ALU, false, "key plate")
            translate([plate_x0, plate_y0]) plate_top_2d();
    }
}

module u_channel() {
    P(C_OAK, true, "oak bottom") translate([x_in0, 0, -explode]) intersection() { sanded_panel(x_in1 - x_in0, oak_bottom_t); difference() {
        linear_extrude(oak_bottom_t) oak_bottom_2d();
        translate([0, 0, oak_bottom_t - stack_groove_depth]) linear_extrude(stack_groove_depth + EPS) oak_grooves_2d();
        // Fastener counterbores from the bottom face (a drill, not a cut:
        // the DXF carries the clearance hole, the drawing the counterbore).
        translate([-x_in0, 0, -EPS]) for (f = fasteners()) translate(f)
            cylinder(d = hardware_fastener_cbore_d, h = hardware_fastener_cbore_depth + EPS);
    } }
    // Each side: one sheet, bottom edge in the bottom groove, top edge in the top.
    // Exploded, the sides move out and down so the boards between them show.
    for (i = [0, 1])
        P(C_ACRYLIC, true, str("side ", i == 0 ? "left" : "right")) translate([x_in0, side_y[i] + stack_side_t + (i == 0 ? -1 : 1) * explode * 1.5, z_side0 - explode * 0.6]) rotate([90, 0, 0])
            linear_extrude(stack_side_t) side_2d();
}

module caps() {
    P(C_OAK_DARK, true, "mouth cap") translate([ends_mouth_cap_t - explode / 3, 0, 0]) rotate([90, 0, 90]) mirror([0, 0, 1])
        intersection() { linear_extrude(ends_mouth_cap_t) mouth_cap_2d(); sanded_cap(ends_mouth_cap_t); }
    P(C_OAK_DARK, true, "tail cap") translate([x_in1 + explode / 3, 0, 0]) rotate([90, 0, 90])
        intersection() { linear_extrude(ends_tail_cap_t) tail_cap_2d(); sanded_cap(ends_tail_cap_t); }
}

module switch_at(xy, rot, top, name, spare = false) {
    // Seat (collar underside) on the plate's key face.
    tf = top ? [xy[0], xy[1], z_plate_top + explode / 2] : [xy[0], xy[1], z_floor - explode];
    // P() OUTSIDE the placement: a section cuts in world coordinates, and a
    // P() inside translate() cut every switch in its own frame instead.
    P(C_SWITCH, false, str("switch ", name)) translate(tf) rotate([top ? 0 : 180, 0, rot]) import("vendor/ks33.stl");
    P(spare ? C_SPARE : C_CAP, false, str("cap ", name)) translate(tf) rotate([top ? 0 : 180, 0, rot])
        translate([0, 0, switch_keycap_top_above_seat - 2.5])
            linear_extrude(2.5, scale = 0.85) square(switch_keycap, center = true);
    // The cap's TRAVEL: the space it sweeps when pressed. Only for the clash
    // check - drawn nowhere else - so a cap that would hit something at the
    // bottom of its stroke is caught, not just one that hits at rest.
    if (only == str("travel ", name) || list_solids)
        P(C_CAP, false, str("travel ", name)) translate(tf) rotate([top ? 0 : 180, 0, rot])
            translate([0, 0, switch_keycap_top_above_seat - 2.5 - switch_total_travel])
                linear_extrude(switch_total_travel) difference() {
                    square(switch_keycap * 0.85, center = true);
                    // The stem and actuator move WITH the cap: measured off the
                    // mesh, 11.0 x 5.6 above the housing top at +3.2.
                    square([11.4, 6.0], center = true);
                }
}

module keys_3d() {
    for (k = keys) switch_at(key_xy(k), key_rot(k), key_face(k) == "top", k[0]);
    for (i = [0 : 1 : len(spare_xy) - 1]) switch_at(spare_xy[i], 0, false, str("spare ", i + 1), true);
}

module thumb_plates_3d() {
    lam(z_floor - explode * 0.5, plate_thickness, C_ALU, false, "thumb plates") thumb_plate_both_2d();
}

module cluster_boards() {
    for (cl = ["left_hand", "right_hand"])
        P(C_PCB, false, str("board ", cl)) translate([0, 0, z_plate_top - switch_pcb_below_seat - switch_pcb_t + explode * 0.25])
            linear_extrude(switch_pcb_t) offset(-0.5) cluster_window_2d(cluster_keys(cl));
}

module tail_equipment() {
    // The Matrix, face up under the top window.
    P([0.10, 0.10, 0.12], false, "Matrix board") translate([matrix_xy[0] - boards_matrix_board / 2, matrix_xy[1] - boards_matrix_board / 2, matrix_board_z])
        cube([boards_matrix_board, boards_matrix_board, switch_pcb_t]);
    P(C_LED, false, "Matrix LEDs") translate([matrix_xy[0] - boards_matrix_emitters / 2, matrix_xy[1] - boards_matrix_emitters / 2, matrix_board_z + switch_pcb_t])
        cube([boards_matrix_emitters, boards_matrix_emitters, boards_matrix_led_h]);
    // The Matrix's ribbon where it leaves the two pad rows, below the board;
    // it runs on to J-MCU (drawn with the tail wiring).
    for (i = [0, 1]) P([0.15, 0.15, 0.15], false, str("Matrix harness ", i + 1))
        translate([matrix_xy[0] - 12.7, matrix_xy[1] + (i == 0 ? -1 : 1) * 11.43 - 1.27, matrix_board_z - boards_matrix_harness_h])
            cube([25.4, 2.54, boards_matrix_harness_h]);   // rows 22.86 apart [ds]
    P(C_FROSTED, false, "matrix window") translate([0, 0, T - openings_matrix_acrylic_t + explode]) linear_extrude(openings_matrix_acrylic_t) matrix_window_2d();
    // The etherCON: flange and chassis behind the tail cap (mounting is free).
    // The NE8FDP as drawn (NE8FDP.dxf): flange outside the tail cap, main
    // housing behind the panel, rear RJ45 socket beyond it, off the axis.
    // Its front passes through the cap's bore; the flange sits against the
    // cap's inside face; housing and rear socket stand inboard of it.
    P(C_CONN, false, "etherCON") union() {
        translate([ec_panel_x - 2, ec_c[0] - ec_fl[0] / 2, ec_c[1] - ec_fl[1] / 2]) cube([2, ec_fl[0], ec_fl[1]]);
        translate([ec_panel_x - EPS, ec_c[0], ec_c[1]]) rotate([0, 90, 0]) cylinder(d = ethercon_bore_d - 0.2, h = L - ec_panel_x + 2 * EPS);
        translate([ec_panel_x - ethercon_housing_d, ec_c[0] - ec_house[0] / 2, ec_c[1] - ec_house[1] / 2])
            cube([ethercon_housing_d, ec_house[0], ec_house[1]]);
        translate([ec_panel_x - ethercon_depth, ec_sock_c[0] - ec_sock[0] / 2, ec_sock_c[1] - ec_sock[1] / 2])
            cube([ethercon_depth - ethercon_housing_d + EPS, ec_sock[0], ec_sock[1]]);
    }
    // The RJ45 patch lead's plug and boot, mated into that rear socket.
    // It turns with the connector, as the socket does.
    P([0.55, 0.70, 0.85], false, "RJ45 plug") translate([ec_panel_x - ethercon_depth - ethercon_rj45_plug_l, ec_sock_c[0] - ec_plug[0] / 2, ec_sock_c[1] - ec_plug[1] / 2])
        cube([ethercon_rj45_plug_l, ec_plug[0], ec_plug[1]]);
    // The USB-C extension's plug in the Matrix's tail edge, under the board.
    P([0.35, 0.35, 0.38], false, "USB-C plug") translate([usb_plug_x0, matrix_xy[1] - openings_usb_slot_w / 2, matrix_board_z - openings_usb_slot_h])
        cube([openings_usb_plug_l, openings_usb_slot_w, openings_usb_slot_h]);
    // The USB-C extension: receptacle body behind the tail cap, and a cable
    // run to the Matrix board's edge (drawn straight; it is a flexible lead).
    P(C_CONN, false, "USB-C receptacle") translate([x_in1 - openings_usb_ext_depth, usb_c[0] - openings_usb_slot_w / 2, usb_c[1] - openings_usb_slot_h / 2])
        cube([openings_usb_ext_depth, openings_usb_slot_w, openings_usb_slot_h]);
    // Routed beside the etherCON, on the receptacle's side.
    usb_from = [openings_matrix_usb_to_tail ? matrix_xy[0] + boards_matrix_board / 2 + usb_behind : usb_plug_x0,
                matrix_xy[1], matrix_board_z - openings_usb_slot_h / 2];
    P([0.15, 0.15, 0.15], false, "USB-C lead") run([usb_from, [usb_from[0] + 4, usb_c[0], usb_from[2]],
        [x_in1 - openings_usb_ext_depth - 4, usb_c[0], usb_c[1]], [x_in1 - openings_usb_ext_depth, usb_c[0], usb_c[1]]], 4);
}

// ONE LED STRIP, lying on the main board (owner, 2026-09-26: "one led
// strip, on the center board. It'll diffuse to both sides" - ADR 0016). It
// runs down the board's centreline, between the thumb switches' two rows of
// pins, LEDs up, and lights both acrylic sides through the cavity. Placed
// with the main board below.
module led_strips() {
    P(C_LED, false, "LED strip") translate([strip_x0, strip_y, cb_top]) cube([strip_l, lighting_strip_w, lighting_strip_t]);
}

// ------------------------------------------------------------ routing -----
// The breath tube runs from the mouth cap to the trap and the sensor inside
// the mouth band, against one side (routing_tube_lane); there are no looms
// since ADR 0017 - the key boards are on flat flex and the Matrix on a
// ribbon, both drawn below. The lane is a model choice (config/body.yaml
// routing): the clash check reports what is in it.
// Inboard of the fastener line, which is close to the sides.
function lane_y(side, d) = let(e = hardware_fastener_inset + fastener_notch + d / 2)
    side == "left" ? u_y0 + e : W - u_y0 - e;
tube_y = lane_y(routing_tube_lane, routing_tube_od);
// A FLAT RIBBON through points: each segment is swept with the ribbon's
// cross-section turned to suit its direction - lying FLAT along and across
// the body, on edge only where it drops to a socket. Stood on edge along the
// body, a 15 mm ribbon does not fit the 12-13 mm between the thumb boards'
// (now the main board's)
// parts and the key boards' parts (found by the clash check, 2026-09-26).
module ribbon(pts, w, t = routing_ribbon_t) {
    for (i = [0 : len(pts) - 2]) let(a = pts[i], b = pts[i + 1], dv = [abs(b[0] - a[0]), abs(b[1] - a[1]), abs(b[2] - a[2])],
                                   ax = dv[0] >= dv[1] && dv[0] >= dv[2] ? 0 : dv[1] >= dv[2] ? 1 : 2,
                                   sec = ax == 0 ? [0.01, w, t] : ax == 1 ? [w, 0.01, t] : [w, t, 0.01])
        hull() { translate(a) cube(sec, center = true); translate(b) cube(sec, center = true); }
}
// A run through points, as a chain of hulled spheres.
module run(pts, d) {
    for (i = [0 : len(pts) - 2]) hull() { translate(pts[i]) sphere(d = d, $fn = 16); translate(pts[i + 1]) sphere(d = d, $fn = 16); }
}
top_z = z_plate_top - switch_pcb_below_seat - switch_pcb_t;     // top cluster boards' underside
thumb_z = z_floor + switch_pcb_below_seat + switch_pcb_t;       // the main board's top face, where the thumb switches solder
function mid_x(cl) = (min(xs(cluster_keys(cl))) + max(xs(cluster_keys(cl)))) / 2;
function sgn(side) = side == "right" ? 1 : -1;
function xspan(cl) = [min(xs(cluster_keys(cl))), max(xs(cluster_keys(cl)))];

// THE MAIN BOARD (owner, 2026-09-26: "instead of individual bottom boards,
// and the center board, maybe we can do one big long board" - ADR 0017).
// ONE flat board at the thumb boards' level carries the thumb switches, both
// thumb registers and everything the carrier did, from the mouth cap to the
// end of the right hand. Its parts face up, under the key boards; the key
// boards connect to it by ribbons. At this level it has more room
// than the centre board had: drc.echo prints it. The cb_ names
// are kept from the centre board it replaced.
function tspan(cl) = let(p = [for (q = thumb_pts(cl)) q[0]]) [min(p) - (switch_keycap + 4) / 2, max(p) + (switch_keycap + 4) / 2];
function kspan(cl) = xspan(cl) + [-1, 1] * (plate_cutout / 2 + cluster_margin);
tube_side = sgn(routing_tube_lane);
// Across: the full width inside the sides; the tube runs above it.
cb_y = [u_y0 + boards_board_clear, W - u_y0 - boards_board_clear];
cb_x = [x_in0 + boards_board_clear, max(kspan("right_hand")[1], tspan("right_thumb")[1])];
cb_z = thumb_z - switch_pcb_t;          // underside: where the thumb boards were
cb_top = thumb_z;
cb_room = top_z - boards_cluster_smt_h - boards_board_clear - cb_top;   // parts height under the key boards
gap_x = [kspan("left_hand")[1] + boards_board_clear, kspan("right_hand")[0] - boards_board_clear];   // nothing overhead
gap_room = z_lid_bot - boards_board_clear - cb_top;
chain = ["right_thumb", "right_hand", "left_thumb", "left_hand"];
function is_top(cl) = cl == "left_hand" || cl == "right_hand";
// Where the thumb switches' pins stand through the board's top face.
function pins_at(p, r) = len([for (k = bottom_keys) if (max(abs(key_xy(k)[0] - p[0]), abs(key_xy(k)[1] - p[1])) < ks33_stub + r) 1]) > 0;

// THE BREATH SENSOR: MPXV4006DP case 1351-01, SURFACE MOUNT (datasheet p.2),
// AT THE MOUTH END (owner, 2026-09-26, with the main board): on the far side
// from the tube, ports towards the tail, beside the breath trap - the
// shortest tube this body can have. The lower barb reaches the board's
// surface (p.7), so the board has a slot in front of it.
sensor_c = [cb_x[0] + 0.5 + boards_sensor_body / 2, cb_y[tube_side < 0 ? 1 : 0] + tube_side * (boards_sensor_leads / 2 + 0.5)];
sensor_face_x = sensor_c[0] + boards_sensor_body / 2;
p2_y = sensor_c[1] + boards_sensor_port_offset;
p1_tip = [sensor_face_x + boards_sensor_port_l, sensor_c[1] - boards_sensor_port_offset, cb_top + boards_sensor_port_z[0]];
module sensor_3d() {
    P([0.20, 0.20, 0.22], false, "breath sensor") union() {
        translate([sensor_c[0] - boards_sensor_body / 2, sensor_c[1] - boards_sensor_body / 2, cb_top])
            cube([boards_sensor_body, boards_sensor_body, boards_sensor_h]);
        translate([sensor_c[0] - boards_sensor_lead_row / 2, sensor_c[1] - boards_sensor_leads / 2, cb_top]) cube([boards_sensor_lead_row, boards_sensor_leads, boards_sensor_lead_h]);
        for (i = [0, 1]) translate([sensor_face_x - EPS, sensor_c[1] + (i == 0 ? -1 : 1) * boards_sensor_port_offset, cb_top + boards_sensor_port_z[i]])
            rotate([0, 90, 0]) cylinder(d = boards_sensor_port_d, h = boards_sensor_port_l);
    }
}
sensor_room = under_keys(sensor_c, [boards_sensor_body, boards_sensor_leads]) ? cb_room : gap_room;
// The strip: the centreline band between the thumb switches' two rows of
// pins, from past the sensor to the board's tail end.
strip_y = W / 2 - lighting_strip_w / 2;
strip_x0 = sensor_c[0] + boards_sensor_lead_row / 2 + boards_board_clear;
jm_x1 = cb_x[1] - 1;                               // J-MCU's mouth, at the main board's tail edge
jm_x0 = jm_x1 - boards_mcu_conn_w;
strip_l = min(cb_x[1] - lighting_strip_inset, jm_x0 - boards_board_clear) - strip_x0;

// THE KEY BOARDS ARE ON RIBBONS (owner, 2026-09-26: ribbons rather than
// blind-mating stacking headers, so the lid comes off with them attached -
// ADR 0017). One 12-way flat flex ribbon per key board, the chain's 12
// conductors (ADR 0001's pinout), between two low ZIF connectors: one on the
// key board's underside in the band beside its switches' pins, away from
// the tube, and one on the main board's far edge band below it, where
// nothing is overhead but the plate. Closed, the ribbon folds up the far
// side of the cavity and back in under the key board; its length is set by
// the lid flipped open over the far edge (drc.echo).
ffc_sz = [boards_ffc_conn_l, boards_ffc_conn_w];   // along x, across y
ffc_s = tube_side < 0 ? 1 : -1;                  // the far side, where the ribbons are
// Exploded, the main board rises by e_mb and the key boards by e_kb; the
// cables stretch to follow, so they stay connected in the picture.
e_mb = explode * 0.1;
e_kb = explode * 0.25;
kb_ffc_y = W / 2 + ffc_s * (switch_cluster_pcb_w / 2 - boards_ffc_conn_w / 2 - 0.5);
kb_ffc_z = top_z - boards_ffc_conn_h;           // underside of the key board's connector
mb_ffc_z = cb_top + boards_ffc_conn_h;          // top of the main board's connector
// A C: both connectors take the ribbon from the far side, level, and it
// runs out of one, round a semicircle toward the side wall, and into the
// other. The semicircle spans the two entry heights; the main board's
// connector stands in from the wall by it.
ffc_zk = kb_ffc_z + boards_ffc_conn_h / 2;      // entry heights
ffc_zm = cb_top + boards_ffc_conn_h / 2;
ffc_r = (ffc_zk - ffc_zm) / 2;
ffc_yc = (ffc_s > 0 ? W - u_y0 : u_y0) - ffc_s * (boards_board_clear + ffc_r);   // the C's centre, and the main connector's mouth
mb_ffc_y = ffc_yc - ffc_s * boards_ffc_conn_w / 2;
// Clear of the key board's switch pins above and the thumb switches' pins
// through the main board below.
function ffc_clear(x, cl) = min([for (k = concat(cluster_keys(cl), bottom_keys)) let(y = key_face(k) == "top" ? kb_ffc_y : mb_ffc_y)
    max(abs(key_xy(k)[0] - x) - boards_ffc_conn_l / 2, abs(key_xy(k)[1] - y) - boards_ffc_conn_w / 2)]) >= ks33_stub + 0.3;
// Along the key board: the clear place nearest its middle, from its keys'
// positions and the midpoints between them.
function ffc_x(cl) = let(t = [for (k = cluster_keys(cl)) key_xy(k)[0]], m = (min(t) + max(t)) / 2,
                         c = concat(t, [for (i = [0 : len(t) - 2]) (t[i] + t[i + 1]) / 2], [m]),
                         ok = [for (x = c) if (ffc_clear(x, cl)) x], d = [for (x = ok) abs(x - m)])
    len(ok) > 0 ? ok[search(min(d), d)[0]] : undef;
ribbon_cls = ["left_hand", "right_hand"];
function kb_ffc(cl) = [ffc_x(cl), kb_ffc_y];
function mb_ffc(cl) = [ffc_x(cl), mb_ffc_y];
// ONE CLEAN ARC (owner, 2026-09-26: "a clean arc instead of whatever that
// is"), in (y, z) at the connector's x: out of the key board's connector,
// round the C toward the side wall, into the main board's. Its length is
// what one arc can have in that space, so the lid tilts only a little with
// the ribbons attached; to take it off, flip the two ZIF latches first
// (drc.echo gives the angle).
function ffc_path(cl) = let(zk = ffc_zk + e_kb, zm = ffc_zm + e_mb, r = (zk - zm) / 2, zc = (zk + zm) / 2)
    concat([[kb_ffc_y + ffc_s * boards_ffc_conn_w / 2, zk]],
           [for (a = [90 : -7.5 : -90]) [ffc_yc + ffc_s * r * cos(a), zc + r * sin(a)]]);
function path_len(p) = sum([for (i = [0 : len(p) - 2]) norm(p[i + 1] - p[i])]);
// The lid hinged on its far top edge and opened by phi: where the key
// board's connector goes, and how far that is from the main board's.
function ffc_need(phi) = let(s = tube_side < 0 ? 1 : -1, hy = s > 0 ? W : 0, a = s * (kb_ffc_y - hy), b = kb_ffc_z - T,
                             q = [a * cos(-phi) - b * sin(-phi), a * sin(-phi) + b * cos(-phi)])
    norm([hy + s * q[0] - mb_ffc_y, T + q[1] - mb_ffc_z]);
function ffc_open_angle(l, phi = 0) = phi < 180 && ffc_need(phi + 1) <= l - 3 ? ffc_open_angle(l, phi + 1) : phi;
module ribbons_3d() {
    for (cl = ribbon_cls) let(k = kb_ffc(cl), m = mb_ffc(cl), p = ffc_path(cl)) {
        P([0.85, 0.85, 0.80], false, str("ZIF ", cl, " key board")) translate([k[0] - ffc_sz[0] / 2, k[1] - ffc_sz[1] / 2, kb_ffc_z + e_kb])
            cube([ffc_sz[0], ffc_sz[1], boards_ffc_conn_h]);
        P([0.85, 0.85, 0.80], false, str("ZIF ", cl, " main board")) translate([m[0] - ffc_sz[0] / 2, m[1] - ffc_sz[1] / 2, cb_top + e_mb])
            cube([ffc_sz[0], ffc_sz[1], boards_ffc_conn_h]);
        // Swept as a strip of the ribbon's width along x, bending in (y, z).
        P([0.80, 0.55, 0.20], false, str("ribbon ", cl)) for (i = [0 : len(p) - 2])
            hull() for (q = [p[i], p[i + 1]]) translate([k[0], q[0], q[1]]) cube([routing_ffc_w, routing_ffc_t, routing_ffc_t], center = true);
    }
}

// THE MATRIX AND THE UMBILICAL (owner, 2026-09-26: "what about matrix led
// esp32 and ethercon wire connections?"), both onto the main board's tail
// end. The Matrix: a flat 24-way ribbon soldered to its pads (ADR 0018), down
// just inside its mouth edge, one bend, and level beside the patch plug
// into J-MCU - the Matrix is on the lid,
// so it unplugs there like the key boards. The umbilical: the slim patch
// lead from the etherCON's rear socket, in an S-bend at its legal radius
// down into J-UMB, which stands in from the plug by what that bend needs.
// An S-bend in (x, z), moving toward -x, level at both ends, radius r:
// two arcs, with a vertical run between them if the drop is more than 2r.
function sbend(a, e, r, n = 8) = let(h = a[1] - e[1], sg = h >= 0 ? 1 : -1, H = abs(h),
                                     th = H >= 2 * r ? 90 : acos(1 - H / (2 * r)), dx = 2 * r * sin(th), xs = e[0] + dx)
    concat([a], [for (i = [0 : n]) let(t = 90 + th * i / n) [xs + r * cos(t), a[1] + sg * (-r + r * sin(t))]],
           [for (i = [0 : n]) let(t = 270 + th * (n - i) / n) [e[0] + r * cos(t), e[1] + sg * (r + r * sin(t))]], [e]);
function sbend_dx(h, r) = abs(h) >= 2 * r ? 2 * r : 2 * r * sin(acos(1 - abs(h) / (2 * r)));
module tail_wiring_3d() {
    P([0.85, 0.85, 0.80], false, "J-MCU") translate([jm_x0, jm_y - jm_sz[1] / 2, cb_top + e_mb]) cube([jm_sz[0], jm_sz[1], boards_mcu_conn_h]);
    P([0.85, 0.85, 0.80], false, "J-UMB") translate([ju_x1 - ju_sz[0], ec_sock_c[0] - ju_sz[1] / 2, cb_top + e_mb]) cube([ju_sz[0], ju_sz[1], boards_umb_conn_h]);
    P([0.30, 0.30, 0.80], false, "Matrix ribbon") for (i = [0 : len(mcu_path) - 2])
        hull() for (q = [mcu_path[i], mcu_path[i + 1]]) translate([q[0], jm_y, q[1]]) cube([routing_mcu_ribbon_t, routing_mcu_ribbon_w, routing_mcu_ribbon_t], center = true);
    P([0.25, 0.45, 0.75], false, "patch lead") run([for (q = umb_path) [q[0], ec_sock_c[0], q[1]]], routing_umb_cable_od);
}

// The regulator block (a module and its bulk capacitors, for the one dev
// board left - ADR 0015), turned across the body at the board's tail end, on
// the far side, in front of J-MCU - drc.echo says whether it fits where it
// stands.
tall_sz = [boards_tall_w, boards_tall_l];   // along x, across y
far_y = cb_y[tube_side < 0 ? 1 : 0] + tube_side * (boards_tall_l / 2 + 0.5);
tall_c = [[jm_x0 - boards_board_clear - boards_tall_w / 2, far_y]];   // just in front of J-MCU
// Is any key board overhead? Each key's board footprint taken as a
// cluster_pcb_w square, unrotated - the window's gap-closing is ignored, so
// this errs towards "clear"; the clash check has the real outline.
function under_keys(c, sz) = len([for (cl = ["left_hand", "right_hand"], k = cluster_keys(cl))
    if (abs(key_xy(k)[0] - c[0]) < (switch_cluster_pcb_w + sz[0]) / 2 && abs(key_xy(k)[1] - c[1]) < (switch_cluster_pcb_w + sz[1]) / 2) 1]) > 0;
tall_room = under_keys(tall_c[0], tall_sz) ? cb_room : gap_room;
ubolt_hole_r = hardware_ubolt_nut_af / cos(30) / 2 + boards_board_clear;   // the U-bolt's nuts stand above the board's underside
module cb_2d() {
    difference() {
        translate([cb_x[0], cb_y[0]]) square([cb_x[1] - cb_x[0], cb_y[1] - cb_y[0]]);
        // The slot in front of the sensor's lower port.
        translate([sensor_face_x - EPS, p2_y - boards_sensor_port_d / 2 - 1])
            square([boards_sensor_port_l + 2, boards_sensor_port_d + 2]);
        // A notch for each screw the board's edge reaches, a hole over each
        // U-bolt nut.
        for (f = fasteners()) translate(f) circle(r = fastener_notch);
        for (u = ubolt_legs()) translate(u) circle(r = ubolt_hole_r);
    }
}
// J-MCU: on the tube side of the regulator block, at the board's tail edge.
jm_sz = [boards_mcu_conn_w, boards_mcu_conn_l];
// Across: the ribbon clear of the patch plug beside it.
jm_y = ec_sock_c[0] + ffc_s * (ec_plug[0] / 2 + boards_board_clear + routing_mcu_ribbon_w / 2);
jm_z = cb_top + boards_mcu_conn_h / 2;
mcu_r = 4;   // drawing convention: the ribbon's bends
// Down just inside the Matrix's mouth edge (its USB-C plug leaves that
// edge), one bend, and level into J-MCU.
mcu_x = matrix_xy[0] - boards_matrix_board / 2 + 1.5;
mcu_path = concat([[mcu_x, matrix_board_z - boards_matrix_harness_h]],
                  [for (i = [0 : 8]) let(t = 90 * i / 8) [mcu_x - mcu_r + mcu_r * cos(t), jm_z + e_mb + mcu_r - mcu_r * sin(t)]],
                  [[jm_x1, jm_z + e_mb]]);
// J-UMB: in line with the patch plug, where its bend lands.
pb_x = ec_panel_x - ethercon_depth - ethercon_rj45_plug_l;     // the patch plug's cable end
umb_r = routing_umb_cable_od * routing_umb_bend_r_per_od;
ju_z = cb_top + boards_umb_conn_h / 2;
ju_x1 = pb_x - 1 - sbend_dx(ec_sock_c[1] - ju_z, umb_r);       // J-UMB's mouth
ju_sz = [boards_umb_conn_w, boards_umb_conn_l];
umb_path = sbend([pb_x, ec_sock_c[1]], [ju_x1, ju_z + e_mb], umb_r);
// Standoffs off the oak: candidates along both edge bands and at the thumb
// rests, kept where nothing else is - the soldered thumb switches, clipped
// into their plates, carry the board between them.
function so_clear(p) = let(r = boards_standoff_d / 2 + 0.5)
    !pins_at(p, r) && abs(p[1] - W / 2) >= lighting_strip_w / 2 + r
    && min([for (f = fasteners()) norm(p - f)]) >= fastener_notch + r
    && min([for (u = ubolt_legs()) norm(p - u)]) >= ubolt_hole_r + r
    && max(abs(p[0] - sensor_c[0]) - boards_sensor_body / 2, abs(p[1] - sensor_c[1]) - boards_sensor_leads / 2) >= r
    && max(abs(p[0] - tall_c[0][0]) - tall_sz[0] / 2, abs(p[1] - tall_c[0][1]) - tall_sz[1] / 2) >= r
    && min([for (cl = ribbon_cls) max(abs(p[0] - mb_ffc(cl)[0]) - boards_ffc_conn_l / 2, abs(p[1] - mb_ffc_y) - boards_ffc_conn_w / 2)]) >= r + 3
    && max(abs(p[0] - (jm_x0 + jm_x1) / 2) - jm_sz[0] / 2, abs(p[1] - jm_y) - jm_sz[1] / 2) >= r
    && max(abs(p[0] - (ju_x1 - ju_sz[0] / 2)) - ju_sz[0] / 2, abs(p[1] - ec_sock_c[0]) - ju_sz[1] / 2) >= r + routing_umb_cable_od;
cb_standoffs = [for (x = [cb_x[0] + 4, lt_rest_xy[0], (gap_x[0] + gap_x[1]) / 2, rt_rest[0], (rt_rest[0] + jm_x0) / 2, cb_x[1] - 4],
                     y = [cb_y[0] + 4, cb_y[1] - 4]) if (so_clear([x, y])) [x, y]];
module centre_board_3d() {
    P(C_PCB, false, "main board") translate([0, 0, cb_z]) linear_extrude(switch_pcb_t) cb_2d();
    P([0.35, 0.55, 0.40], false, "parts main board") translate([0, 0, cb_top]) linear_extrude(boards_smt_h) difference() {
        offset(-0.5) cb_2d();
        for (cl = ribbon_cls) translate(mb_ffc(cl)) square(ffc_sz + [1, 1], center = true);
        translate([jm_x0 - 0.5, jm_y - jm_sz[1] / 2 - 0.5]) square(jm_sz + [1, 1]);
        translate([ju_x1 - ju_sz[0] - 0.5, ec_sock_c[0] - ju_sz[1] / 2 - 0.5]) square(ju_sz + [1, 1]);
        translate([ju_x1, ec_sock_c[0] - routing_umb_cable_od / 2 - 0.5]) square([cb_x[1] - ju_x1 + 1, routing_umb_cable_od + 1]);   // under the lead
        // and nothing under the C, between the connector and the wall
        for (cl = ribbon_cls) translate([mb_ffc(cl)[0] - routing_ffc_w / 2 - 0.5, ffc_s > 0 ? ffc_yc : 0])
            square([routing_ffc_w + 1, ffc_s > 0 ? W : ffc_yc]);
        translate(sensor_c) square([boards_sensor_body + 1, boards_sensor_leads + 1], center = true);
        for (c = tall_c) translate(c) square(tall_sz + [1, 1], center = true);
        for (c = cb_standoffs) translate(c) circle(d = boards_standoff_d + 1);
        translate([strip_x0 - 0.5, strip_y - 0.5]) square([strip_l + 1, lighting_strip_w + 1]);
    }
    P([0.30, 0.30, 0.55], false, "tall parts main board")
        translate([tall_c[0][0] - tall_sz[0] / 2, tall_c[0][1] - tall_sz[1] / 2, cb_top]) cube([tall_sz[0], tall_sz[1], boards_tall_h]);
    // Off the oak, or off a thumb plate where one is under it.
    for (i = [0 : 1 : len(cb_standoffs) - 1]) let(c = cb_standoffs[i], f = on_thumb_plate(c) ? z_thumb_top : floor_at(c[0]))
        P(C_STEEL, false, str("main board standoff ", i + 1)) translate([c[0], c[1], f]) cylinder(d = boards_standoff_d, h = cb_z - f, $fn = 6);
}
function on_thumb_plate(p) = len([for (cl = ["left_thumb", "right_thumb"])
    let(q = thumb_pts(cl), h = (switch_keycap + 4) / 2)
    if (p[0] >= min([for (a = q) a[0]]) - h && p[0] <= max([for (a = q) a[0]]) + h
        && p[1] >= min([for (a = q) a[1]]) - h && p[1] <= max([for (a = q) a[1]]) + h) 1]) > 0;
function floor_at(x) = abs(x - ubolt_c[0]) <= ubolt_bp[0] / 2 ? z_floor + hardware_backplate_t + hardware_ubolt_nut_h : z_floor;


// PARTS ON THE BOARDS, as envelopes. Cluster boards: a component layer on
// the cavity side (the plate side cannot take a SOIC - ks33-geometry.md).
// The Matrix: its back-side parts. The main board's parts are with it.
module parts_3d() {
    for (cl = ["left_hand", "right_hand"])
        P([0.35, 0.55, 0.40], false, str("parts ", cl)) translate([0, 0, top_z - boards_cluster_smt_h])
            linear_extrude(boards_cluster_smt_h) difference() {
                offset(-0.5) cluster_window_2d(cluster_keys(cl));
                translate(kb_ffc(cl)) square(ffc_sz + [1, 1], center = true);
            }
    P([0.20, 0.20, 0.22], false, "Matrix underside parts") translate([matrix_xy[0] - 9.5, matrix_xy[1] - 9.5, matrix_board_z - boards_matrix_under_h])
        cube([19, 19, boards_matrix_under_h]);
}

module routing_3d() {
    trap_y = lane_y(routing_tube_lane, routing_trap_d);   // inboard of the fastener line, like the tube
    // The trap sits in the mouth band, above the main board and before the
    // first key board. The sensor is beside it on the far side (ADR 0017):
    // from the trap the tube turns across, over the strip, and back onto the
    // sensor's port, which faces the tail.
    trap_x0 = x_lh0 - board_lead - boards_board_clear - routing_trap_l;
    trap_z = z_floor + cavity_h / 2;
    P([0.95, 0.60, 0.45], false, "breath tube") run([
        [0, tube_yz[0], tube_yz[1]], [x_in0 + 3, tube_yz[0], tube_yz[1]],
        [x_in0 + 12, tube_y, trap_z],
        [trap_x0 - 6, tube_y, trap_z], [trap_x0, trap_y, trap_z]], routing_tube_od);
    P([0.95, 0.60, 0.45], false, "breath trap") translate([trap_x0, trap_y, trap_z]) rotate([0, 90, 0])
        cylinder(d = routing_trap_d, h = routing_trap_l);
    P([0.95, 0.60, 0.45], false, "breath tube to sensor") run([
        [trap_x0 + routing_trap_l, trap_y, trap_z], [trap_x0 + routing_trap_l + 4, trap_y, p1_tip[2]],
        [trap_x0 + routing_trap_l + 4, p1_tip[1], p1_tip[2]], [p1_tip[0] + routing_tube_od + 1, p1_tip[1], p1_tip[2]],
        [p1_tip[0] - 2, p1_tip[1], p1_tip[2]]], routing_tube_od * 0.8);
}

module hardware_3d() {
    // Fasteners: M3 socket caps from the bottom face into the plate.
    for (i = [0 : len(fasteners()) - 1]) let(f = fasteners()[i]) P(C_STEEL, false, str("M3 #", i + 1)) translate([f[0], f[1], -explode]) {
        translate([0, 0, hardware_fastener_cbore_depth - 3]) cylinder(d = 5.5, h = 3);
        cylinder(d = 3, h = z_plate_top - 0.4 + explode * 2);
    }
    // U-bolt: loop below, legs through the floor to the backing plate, a nut
    // on each leg above the plate.
    P(C_STEEL, false, "U-bolt") translate([0, 0, -explode]) {
        for (u = ubolt_legs()) translate([u[0], u[1], -hardware_ubolt_drop + hardware_ubolt_span / 2])
            cylinder(d = hardware_ubolt_rod_d, h = z_floor + hardware_backplate_t + hardware_ubolt_nut_h + hardware_ubolt_drop - hardware_ubolt_span / 2);
        translate([ubolt_c[0], ubolt_c[1], -hardware_ubolt_drop + hardware_ubolt_span / 2]) rotate([0, 0, 90]) rotate([-90, 0, 0])
            rotate_extrude(angle = 180) translate([hardware_ubolt_span / 2, 0]) circle(d = hardware_ubolt_rod_d);
    }
    for (i = [0, 1]) P(C_STEEL, false, str("U-bolt nut ", i + 1))
        translate([ubolt_legs()[i][0], ubolt_legs()[i][1], z_floor + hardware_backplate_t - explode])
            cylinder(d = hardware_ubolt_nut_af / cos(30), h = hardware_ubolt_nut_h, $fn = 6);
    lam(z_floor, hardware_backplate_t, C_ALU, false, "U-bolt backplate") ubolt_backplate_2d();
}

// The shell is drawn LAST: a see-through (ghosted or faded) part drawn
// before what is behind it hides it in the preview renderer, which is how
// the ribbons went missing from the first renders of them.
module assembly() {
    if (show_keys) { keys_3d(); thumb_plates_3d(); }
    if (show_boards) { cluster_boards(); tail_equipment(); }
    if (show_strips) translate([0, 0, e_mb]) led_strips();
    if (show_routing) routing_3d();
    if (show_boards) { parts_3d(); translate([0, 0, e_mb]) { sensor_3d(); centre_board_3d(); } ribbons_3d(); tail_wiring_3d(); }
    if (show_hardware) hardware_3d();
    if (show_lid) lid(explode);
    if (show_caps) caps();
    if (show_u) u_channel();
}

// =============================================================== DRC ======
// Arithmetic checks on the parameters. Each prints one line:
//   ECHO: "DRC", "PASS"|"FAIL"|"NOTE", "<rule>", <measured>, "<why it matters>"
// FAIL is a design finding for M4, not a build error: the build still
// renders, so the pictures show the problem the line names.

module drc(ok, rule, v, why) {
    echo("DRC", ok == undef ? "NOTE" : ok ? "PASS" : "FAIL", rule, v, why);
}

module drc_report() {
    echo("DRC", "INFO", "layout", keys_placed == len(keys) ? "placed" : "PROVISIONAL",
         str(keys_placed, " of ", len(keys), " keys placed in config/key-layout.yaml"));
    echo("DRC", "INFO", "tbd parameters in play", len(tbd_params), tbd_params);

    echo("DRC", "INFO", "overall length (derived)", L, str("mm = ", L / 25.4, " in; mouth cap to LH1 ", x_lh0,
         ", keys ", top_last - x_lh0, " centre to centre, last key to tail face ", L - top_last));
    drc(undef, "what the mouth end needs", mouth_names[search(max(mouth_claims), mouth_claims)[0]], str(mouth_req, " mm from the mouth cap to LH1"));
    tail_names = ["last key board, the last fastener pair, then the patch plug and the etherCON depth",
                  "last key board, the LED matrix on the top face, then the etherCON depth (matrix not centred)",
                  "the right-thumb cluster against the tail cap"];
    drc(undef, "what the tail end needs", layout_matrix_centred && matrix_centred_req >= max(tail_claims_rel) - top_last_rel
        ? str("the LED matrix centred after the keys, with ", cap_edge_rel + 2 * (boards_matrix_board / 2 + behind_matrix)
            >= 2 * (equip_start_rel + usb_front + boards_matrix_board / 2) - cap_edge_rel
            ? "the etherCON behind it" : "its USB-C plug and the last fastener pair in front of it, clear of the key board") : tail_names[search(max(tail_claims_rel), tail_claims_rel)[0]],
        str(tail_req, " mm after the last key"));
    echo("DRC", "INFO", "behind the Matrix, to the tail face", behind_matrix,
         str("mm = USB-C plug ", usb_behind, " + clearance ", layout_tail_clear, " + etherCON housing ", ethercon_housing_d,
             " + tail cap ", ends_tail_cap_t, " - the rear socket and patch plug pass under the Matrix"));
    under_m = matrix_board_z - boards_matrix_under_h;
    drc(ec_sock_c[1] + ec_sock[1] / 2 <= under_m && ec_sock_c[1] + ec_plug[1] / 2 <= under_m,
        "etherCON rear socket and patch plug pass under the Matrix", under_m - max(ec_sock_c[1] + ec_sock[1] / 2, ec_sock_c[1] + ec_plug[1] / 2),
        "mm below the Matrix's underside parts");
    // The thinnest body that takes the connector on the floor with its rear
    // socket under the Matrix, and its envelope under the key plate. Every
    // term above moves one for one with T, so the shortfall adds directly.
    t_min = T + max(ec_sock_c[1] + max(ec_sock[1], ec_plug[1]) / 2 + ec_clear - under_m,
                    ec_c[1] + ec_env[1] / 2 + ec_clear - z_oak_top_bot);
    drc(T >= t_min, "body thickness takes the etherCON on the floor, its rear socket under the Matrix", T - t_min,
        str("mm spare; the thinnest body that does is ", t_min, " mm (envelope.thickness)"));
    mc = (top_last + cap_edge_rel + L) / 2 - matrix_xy[0];
    drc(abs(mc) < 0.01 || !layout_matrix_centred, "LED matrix centred between the last cap and the tail face", mc, "mm off centre");
    if (layout_gap_matches_matrix)
        drc(abs((x_rh0 - x_gap0 - switch_keycap) - (matrix_xy[0] - openings_matrix_window / 2 - top_last - switch_keycap / 2)) < 0.01
            || gap_c2c == layout_gap,
            "clear gap between the hands = clear gap from the last key to the matrix window",
            [x_rh0 - x_gap0 - switch_keycap, matrix_xy[0] - openings_matrix_window / 2 - top_last - switch_keycap / 2],
            str("mm cap edge to cap edge, and cap edge to window edge; ", gap_c2c, " centre to centre (minimum ", layout_gap, ")"));
    if (layout_equal_bands && !layout_gap_matches_matrix)
        drc(undef, "equal bands (mouth = between hands)", band,
            str("mm each; set by the ", band == mouth_req ? "mouth end" : "minimum gap",
                " - mouth needs ", mouth_req, ", gap minimum ", layout_gap, "; the tail is sized on its own"));
    drc(undef, "LED strip on the main board (derived)", strip_l,
        str("mm, one strip lighting both sides (ADR 0016) - ", floor(strip_l * lighting_strip_per_m / 1000), " LEDs at ", lighting_strip_per_m, "/m"));
    drc(p1_tip[2] - routing_tube_od * 0.4 >= cb_top + lighting_strip_t + boards_board_clear, "breath tube crosses the strip clear of it",
        p1_tip[2] - routing_tube_od * 0.4 - cb_top - lighting_strip_t, "mm above the strip's top face");
    // Each run's end keys put half a cap into the neighbouring band - the
    // ADR 0009 table counts runs centre to centre.
    lh = xs(cluster_keys("left_hand")); rh = xs(cluster_keys("right_hand"));
    // Square caps and cutouts, axis-aligned: the clear gap between two is the
    // larger of the per-axis gaps. Over EVERY pair of top keys, so an offset
    // key or a side-by-side pair is measured the same as a neighbour in line.
    function sq_gap(a, b, s) = max(abs(a[0] - b[0]) - s, abs(a[1] - b[1]) - s);
    function min_pair(s) = min([for (i = [0 : len(top_keys) - 1], j = [i + 1 : 1 : len(top_keys) - 1])
                                sq_gap(key_xy(top_keys[i]), key_xy(top_keys[j]), s)]);
    drc(undef, "top key gaps along the body (LH then RH)", [layout_lh_gaps, layout_rh_gaps], str("mm; runs ", lh_run, " + ", rh_run, "; a 0 is a side-by-side pair"));
    drc(undef, "top key offsets across the body (LH then RH)", [layout_lh_offsets, layout_rh_offsets], "mm from the centreline, + toward the player's left");
    cap_gap = min_pair(switch_keycap);
    drc(cap_gap >= 1.0, "cap-to-cap gap, tightest pair", cap_gap,
        "mm between adjacent MT165 caps; under ~1 mm a pad pressing one catches the next");
    drc(stack_cap_holes == "slot" || cap_gap - 2 * stack_cap_clear >= 2.0,
        str("oak web between cap holes (", stack_cap_holes, ")"),
        stack_cap_holes == "slot" ? "n/a - one slot per hand" : cap_gap - 2 * stack_cap_clear,
        "mm of oak between adjacent holes; under 2 mm, cross-grain, it will not survive - use slots");
    drc(min_pair(plate_cutout) >= 2.0, "key plate web between cutouts", min_pair(plate_cutout), "mm of aluminium");
    edge_web = min([for (k = top_keys) min(key_xy(k)[1] - plate_cutout / 2 - (u_y0 + stack_groove_clear),
                                            (W - u_y0 - stack_groove_clear) - key_xy(k)[1] - plate_cutout / 2)]);
    drc(edge_web >= 3, "key plate web from a cutout to the plate edge", edge_web,
        "mm; the switch's latch arms need plate round them, and the plate edge sits in the side grooves' shadow");
    edge_cap = min([for (k = top_keys) min(key_xy(k)[1] - switch_keycap / 2 - stack_cap_clear, W - key_xy(k)[1] - switch_keycap / 2 - stack_cap_clear)]);
    drc(edge_cap >= 4, "oak between a cap slot and the body's long edge", edge_cap, "mm of oak top outside the slot");
    echo("DRC", "INFO", "oak top thickness (flush at full travel)", oak_top_t,
         "mm = keycap_top_above_seat - total_travel; keycap height is tbd, so this is too");
    drc(undef, "key cap stands proud of the top face at rest", switch_total_travel, "mm = the travel");
    drc(stack_cap_clear * 2 >= 0.015 * (switch_keycap + 2 * stack_cap_clear), "cap hole clearance beats oak cross-grain movement across the hole",
        stack_cap_clear, str("mm per side vs ", 0.015 * (switch_keycap + 2 * stack_cap_clear), " mm of movement at 1.5 % (ADR 0009)"));
    d_gap = (min(rh) - max(lh)) - switch_keycap;
    drc(undef, "inter-hand gap between caps", d_gap, "mm of clear band for the U-bolt and right thumb rest");
    d_uv = min([for (u = ubolt_legs(), p = concat([for (k = bottom_keys) key_xy(k)], spare_xy))
                max(abs(p[0] - u[0]), abs(p[1] - u[1])) - rc / 2 - hardware_ubolt_rod_d / 2]);
    drc(d_uv >= 2, "U-bolt legs clear of the thumb recesses", d_uv, "mm, worst case");

    // Everything cut through the oak bottom, pairwise: [name, centre, size].
    feats = concat(stack_cap_holes == "slot"
                       ? [for (g = thumb_slots()) let(p = [for (k = g) key_xy(k)], x = [for (q = p) q[0]], y = [for (q = p) q[1]])
                          [str(g[0][0], len(g) > 1 ? str("-", g[len(g) - 1][0], " slot") : ""),
                           [(min(x) + max(x)) / 2, (min(y) + max(y)) / 2], [max(x) - min(x) + rc, max(y) - min(y) + rc]]]
                       : [for (k = bottom_keys) [k[0], key_xy(k), [rc, rc]]],
                   [for (i = [0 : 1 : len(spare_xy) - 1]) [str("spare ", i + 1), spare_xy[i], [rc, rc]]],
                   [for (u = ubolt_legs()) ["U-bolt leg", u, [hardware_ubolt_rod_d, hardware_ubolt_rod_d]]],
                   [for (i = [0 : len(fasteners()) - 1]) [str("M3 #", i + 1), fasteners()[i], [hardware_fastener_cbore_d, hardware_fastener_cbore_d]]]);
    function gap(a, b) = max(abs(a[1][0] - b[1][0]) - (a[2][0] + b[2][0]) / 2,
                             abs(a[1][1] - b[1][1]) - (a[2][1] + b[2][1]) / 2);
    clashes = [for (i = [0 : len(feats) - 1], j = [i + 1 : 1 : len(feats) - 1])
               if (gap(feats[i], feats[j]) < 3) str(feats[i][0], " / ", feats[j][0], " ", gap(feats[i], feats[j]))];
    drc(len(clashes) == 0, "oak-bottom cuts at least 3 mm apart (thumb recesses, U-bolt, counterbores)",
        clashes, "pairs closer than 3 mm, with the web between them (negative = overlap)");
    // Through-cuts only: a fastener's counterbore is partial depth from the
    // outside face, so its clearance hole is what meets the side.
    function thru_w(f) = f[0][0] == "M" ? hardware_fastener_clear_d : f[2][1];
    edge = min([for (f = feats) min(f[1][1] - thru_w(f) / 2 - u_y0, W - u_y0 - f[1][1] - thru_w(f) / 2)]);
    drc(edge >= 2, "oak-bottom cuts inside the U", edge, "mm, smallest web to the inside of a side");
    // The counterbore comes up from the outside face and the side groove down
    // from the inside face; where their depths overlap, the oak between them
    // across the body is all that keeps the counterbore out of the groove.
    cbore_share = hardware_fastener_cbore_depth - (oak_bottom_t - stack_groove_depth);
    cbore_web = hardware_fastener_inset - hardware_fastener_cbore_d / 2 - stack_groove_clear;
    drc(cbore_share <= 0 || cbore_web > 0, "fastener counterbores clear of the side grooves", cbore_share <= 0 ? "n/a - they do not share a depth" : cbore_web,
        cbore_share <= 0 ? "" : str("mm of oak across the body, over the ", cbore_share, " mm of depth the counterbore and the groove share; negative breaks through"));
    // The U-bolt's backplate: its nuts on it, and clear of the gap fasteners.
    bp_nut = ubolt_bp[1] / 2 - hardware_ubolt_span / 2 - hardware_ubolt_nut_af / cos(30) / 2;
    bp_web = ubolt_bp[1] / 2 - hardware_ubolt_span / 2 - ubolt_hole_d / 2;
    drc(bp_nut >= 0 && bp_web >= 2, "U-bolt nuts bear on the backplate, which stops at the gap fasteners' clearance",
        [bp_nut, bp_web], "mm, a nut's corners inside the plate end, and plate beyond each leg hole");

    // Sides in grooves
    drc(undef, "interior width between the acrylic sides", u_w, "mm - was the full width less two sides; the oak lips now come off it too");
    drc(stack_groove_depth <= min(oak_top_t, oak_bottom_t) / 2, "groove leaves at least half the oak under it",
        min(oak_top_t, oak_bottom_t) - stack_groove_depth, "mm of oak under the groove in the thinner panel");
    drc(stack_side_inset >= 2, "oak lip outside each groove", stack_side_inset, "mm - thinner and it splits off along the grain");
    drc(stack_edge_r < stack_side_inset && stack_edge_r <= min(oak_top_t, oak_bottom_t) / 2, "sanded edge radius leaves the lips a flat",
        stack_side_inset - stack_edge_r, "mm of flat left on the lip beside the acrylic");

    // Z stack
    drc(cavity_h > 0, "cavity height", cavity_h, "mm between the key plate and the oak bottom");
    z_pole = z_plate_top - switch_pole_tip_below_seat;
    drc(undef, "top switch pole tip below the lid", z_lid_bot - z_pole, "mm into the cavity");
    echo("DRC", "INFO", "oak bottom thickness (thumb keys flush at full travel)", oak_bottom_t,
         "mm, the same rule as the oak top; thumb caps stand proud of the bottom face by the travel at rest");
    th_pole = z_floor + switch_pole_tip_below_seat;
    drc(undef, "thumb switch pole tip height in the cavity", th_pole, "mm above the bottom face");

    // The main board (ADR 0017)
    drc(undef, "main board (derived)", [cb_x[1] - cb_x[0], cb_y[1] - cb_y[0]],
        str("mm long x wide, underside at ", cb_z, " mm - mouth cap to the end of the right hand, the full width inside the sides"));
    drc(cb_room >= boards_smt_h, "main board parts room under the key boards", cb_room,
        "mm from its top face to the key boards' parts, less the clearances - every part there must fit this");
    drc(undef, "main board parts room where no key board is overhead", gap_room, "mm, up to the plate");
    drc(boards_sensor_h <= sensor_room, "breath sensor fits at the mouth end", sensor_room - boards_sensor_h, "mm spare above it");
    drc(len(cb_standoffs) >= 4, "main board standoffs found clear of everything", len(cb_standoffs),
        "standoffs off the oak; the soldered thumb switches carry the board between them");
    drc(boards_tall_h <= tall_room, "regulator block fits where it stands", tall_room - boards_tall_h,
        str("mm spare, ", under_keys(tall_c[0], tall_sz) ? "under a key board" : "beside the key boards, clear to the lid",
            " [approx: key board footprints as squares; clash.txt is the check] - negative means low-profile parts"));
    for (cl = ribbon_cls) drc(ffc_x(cl) != undef, str("ribbon connector on the ", cl, " key board clear of its switches"),
                              ffc_x(cl) == undef ? "none found" : ffc_x(cl), "mm along the body");
    drc(ju_x1 - ju_sz[0] >= cb_x[0] && ju_x1 <= cb_x[1], "J-UMB on the main board, the patch lead at its bend radius", [ju_x1, umb_r],
        "mm along the body (its mouth), and the lead's bend radius in mm (routing.umb_bend_r_per_od x the diameter)");
    drc(undef, "Matrix ribbon length", path_len(mcu_path), "mm from the Matrix's edge to J-MCU, as drawn");
    rp = ffc_path(ribbon_cls[0]);
    drc(max([for (q = rp) q[1]]) <= z_lid_bot - 1, "ribbon arc clear of the lid", z_lid_bot - max([for (q = rp) q[1]]), "mm under the lid at its peak");
    drc(undef, "ribbon arc length, and the lid tilt it allows attached", [path_len(rp), ffc_open_angle(path_len(rp))],
        "mm, and degrees the lid opens on its far edge before the ribbon is taut (3 mm slack) - beyond that, flip the ZIF latches");

    mw = plate_x1 - (top_last + plate_cutout / 2);
    drc(mw >= 3, "key plate beyond the last key cutout", mw, "mm of aluminium; the plate stops short of the Matrix");
    lip_t = oak_top_t - openings_matrix_acrylic_t;
    drc(lip_t >= 2, "oak lip under the frosted window", lip_t, str("mm thick, ", openings_matrix_lip, " mm wide; the acrylic sits flush on it"));
    rw = min([for (k = top_keys) sq_gap(key_xy(k), matrix_xy, (switch_keycap + 2 * stack_cap_clear + matrix_rebate) / 2)]);
    drc(rw >= 3, "oak between the last cap slot and the window rebate", rw, "mm on the top face");
    drc(undef, "LED tops to the frosted window's top face", T - matrix_top_z,
        "mm - frosted acrylic this far above the LEDs softens the pixels; the owner chose it (2026-09-26)");

    // Tail face
    ec_lo = ec_c[1] - ec_env[1] / 2; ec_hi = ec_c[1] + ec_env[1] / 2;
    drc(ec_lo >= z_floor && ec_hi <= z_oak_top_bot, "etherCON body inside the cavity height",
        [ec_lo, ec_hi, z_floor, z_oak_top_bot], "body Z range vs cavity Z range at the tail, where the key plate has ended");
    drc(plate_x1 - (tail_fastener_x + tap_d_m3 / 2) >= 2, "key plate reaches past the last fastener pair",
        plate_x1 - (tail_fastener_x + tap_d_m3 / 2), "mm of plate beyond the tap hole; the plate stops short of the Matrix");
    drc(T - openings_matrix_acrylic_t - matrix_top_z >= 0.3, "LED tops under the frosted window",
        T - openings_matrix_acrylic_t - matrix_top_z, "mm, LED tops to the acrylic's underside - the board's top face is against the oak");
    drc(boards_matrix_emitters <= openings_matrix_window - 0.5, "LED array fits the window opening it stands in",
        openings_matrix_window - boards_matrix_emitters, "mm across, opening less the array");
    fl_margin = min(ec_c[1] - ec_fl[1] / 2, T - (ec_c[1] + ec_fl[1] / 2));
    drc(fl_margin >= 0, "etherCON flange fits behind the tail cap", fl_margin, "mm, the smaller of above and below the flange, inside the cap's height");
    // The bore is what is cut from the cap; the flange only clamps against it.
    drc(undef, "tail cap material below and above the etherCON bore",
        [ec_c[1] - ethercon_bore_d / 2, T - (ec_c[1] + ethercon_bore_d / 2)], "mm - the connector stands on the floor, so it is not centred");
    // USB-C by panel-mount extension (owner, 2026-09-26).
    usb_room = (W - u_y0) - (ec_c[0] + ec_house[0] / 2);
    drc(usb_room >= openings_usb_slot_w + 2, "USB-C extension receptacle beside the etherCON body", usb_room - openings_usb_slot_w,
        str("mm spare across, inside the sides, for a ", openings_usb_slot_w, " mm receptacle"));
    usb_web = (usb_c[0] - openings_usb_slot_w / 2) - (ec_c[0] + ec_fl[0] / 2);
    drc(usb_web >= 2, "tail cap web between the USB-C cutout and the etherCON flange", usb_web, "mm of oak on the tail face");
    usb_run = norm([x_in1 - openings_usb_ext_depth - (matrix_xy[0] + boards_matrix_board / 2), usb_c[0] - matrix_xy[1], usb_c[1] - (matrix_board_z - 2)]);
    echo("DRC", "INFO", "USB-C extension cable run, Matrix edge to receptacle", usb_run,
         "mm straight line; buy the shortest extension that reaches, with slack for the tail cap to come off");

    // Plate
    drc(undef, "M3 thread engagement in the key plate", plate_thickness,
        "mm of aluminium = ~2 threads at 0.5 pitch [calc]; plain tapping will strip, so the BOM's 'insert or tapped boss' is the only option");
    fk = min([for (f = fasteners(), k = top_keys) max(abs(key_xy(k)[0] - f[0]), abs(key_xy(k)[1] - f[1])) - plate_cutout / 2 - tap_d_m3 / 2]);
    drc(fk >= 2, "fastener holes clear of the top switch cutouts", fk, "mm of plate between a tap hole and the nearest cutout");
    fe = min([for (f = fasteners()) min(f[1] - tap_d_m3 / 2 - (u_y0 + stack_groove_clear), (W - u_y0 - stack_groove_clear) - f[1] - tap_d_m3 / 2)]);
    drc(fe >= 1.5, "fastener tap holes inside the plate edge", fe, "mm of plate outside the hole");
}

// ============================================================ dispatch ====
module part_2d(p) {
    if (p == "plate_top") plate_top_2d();
    else if (p == "oak_top") oak_top_2d();
    else if (p == "oak_bottom") oak_bottom_2d();
    else if (p == "thumb_plate") thumb_plate_both_2d();
    else if (p == "oak_grooves") oak_grooves_2d();
    else if (p == "side") side_2d();
    else if (p == "mouth_cap") mouth_cap_2d();
    else if (p == "tail_cap") tail_cap_2d();
    else if (p == "ubolt_backplate") ubolt_backplate_2d();
    else if (p == "matrix_window") matrix_window_2d();
    else if (p == "oak_rebates") oak_rebates_2d();
    else assert(false, str("unknown part ", p));
}

function origin_x() = origin == "centre" ? -L / 2 : origin == "tail" ? -L : 0;
module at_origin() { translate([origin_x(), 0, 0]) children(); }

if (!figure) {
    if (part == "assembly") at_origin() assembly();
    else if (part == "drc") drc_report();
    else part_2d(part);
}
