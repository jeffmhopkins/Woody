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
highlight = [];   // solid ids to draw bright yellow, the rest faded (fig_mezzanines.scad)
show_routing = true;
ghost_shell = false;  // draw the shell translucent to see inside
// Sections. "y" / "x" clip every part with a half-space (keep Y < cut, or
// a slab X > cut) and stay 3D. "y2d" / "x2d" are true section DRAWINGS: each
// part cut by the plane with projection(cut = true), coloured per part, laid
// flat - "y2d" as (X, Z), "x2d" as (Y, Z) looking toward the tail. Use the
// 2D ones for anything dimensioned; OpenCSG loses part colours on 3D cuts.
cut = "none";
cut_at = 0;
cut_key = "";         // or name a key (or "matrix"): the X cut goes through its centre
cut_depth = 1000;     // "x" keeps a slab this deep beyond the cut
figure = false;       // set true by a figure that includes this file
// Where X = 0 sits in the rendered picture: "mouth" (the model's own frame),
// "centre" or "tail". Cameras aim at the origin, so a render stays framed
// when the derived length changes.
origin = "mouth";

LAYERS = ["plate_top", "oak_top", "oak_bottom", "oak_grooves", "thumb_plate", "side",
          "mouth_cap", "tail_cap", "ubolt_backplate",
          "matrix_window", "oak_rebates", "service_cover"];

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
thumb_recess_clear = 1.0;  // drawing convention: cap-to-recess clearance, an M2 question (ADR 0010)
rc = switch_keycap + 2 * thumb_recess_clear;    // a thumb recess, square
cluster_margin = 4;        // drawing convention: board edge past the outermost switch body

// The MOUTH END. The display is on the underside, lengthwise, nearest the
// mouthpiece (ADR 0008's "top"). It cannot share the underside under the
// left-hand run with the left-thumb arc, so the keys start where BOTH the
// first top cap and the first thumb recess clear it. Everything is measured
// from x_in0, the inside face of the mouth cap.
disp_board = [58.782, 25.495];   // read off DISP_DXF's DIMENSION entities (OpenSCAD cannot measure an import)
disp_x0 = x_in0 + layout_mouth_extra;
disp_x1 = disp_x0 + disp_board[0];
// The left-thumb cluster's extent relative to LH1 (x_lh0 = 0), recesses included.
lt_rel = concat([for (i = [0 : 3]) layout_lt_arc_start + i * layout_lt_arc_length / 3], [layout_lt_arc_start, layout_lt_arc_start + layout_lt_arc_length]);
mouth_req = max(x_in0 + layout_mouth_extra + switch_keycap / 2 + stack_cap_clear,  // the first top cap
                disp_x1 + 0.5 + layout_underside_clear - (min(lt_rel) - rc / 2));  // the first thumb recess (display cut is +0.5)

// The TAIL's needs, measured from the last top key's centre. Everything at
// the tail hangs off the right hand, so it can be worked out in the right
// hand's own frame (x_rh0 = 0) before the right hand is placed.
rt_rest_rel = [layout_rt_rest_at * rh_run, W / 2];
function rt_rel(i) = i == 0 ? rt_rest_rel + [layout_rt_offset, 0]
                   : rt_rest_rel + [-0.6 * layout_rt_offset, (i == 1 ? -1 : 1) * 0.6 * layout_rt_offset];
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
    rt_last_rel + rc / 2 + layout_underside_clear + openings_service_cover_w + 2 * layout_tail_clear + ethercon_depth,
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
    cl == "left_thumb" ? lt_arc(i / (n - 1)) :
    cl == "right_thumb" ? rt_xy(i) : [0, 0];

// The left thumb's four keys lie on the tip's sweep, mostly along the body
// (ADR 0010). A half-sine bulge of lt_arc_lateral across a lt_arc_length run.
function lt_arc(t) = [x_lh0 + layout_lt_arc_start + t * layout_lt_arc_length,
                      W / 2 - layout_lt_arc_lateral / 2 + layout_lt_arc_lateral * sin(180 * t)];
rt_rest = [x_rh0, 0] + rt_rest_rel;
// Right-thumb control switches, offset from the rest (ADR 0010): one toward
// the tail, two flanking it toward the mouthpiece. Placeholder geometry.
function rt_xy(i) = [x_rh0, 0] + rt_rel(i);
// Three spare-switch cutouts, required in the DXF by M3 (ADR 0010): octave
// up and down extend the left-thumb arc, hold sits before the right thumb.
// Straight extensions of the arc's end keys - the half-sine is not
// extrapolated, it leaves the body.
lt_step = layout_lt_arc_length / (count("left_thumb") - 1);
// Beside the arc's end keys, across the body - extending the arc along it
// cost length the owner asked to remove (2026-09-26). Placeholders for M2.
spare_xy = [lt_arc(0) + [0, lt_step], lt_arc(1) + [0, lt_step], rt_rest - [1.6 * layout_rt_offset, 0]];

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

// The tail underside after the right-thumb cluster: the service cover,
// turned across the body.
service_xy = [rt_last + rc / 2 + layout_underside_clear + openings_service_cover_w / 2, W / 2];
L = top_last + tail_req;
x_in1 = L - ends_tail_cap_t;
matrix_xy = [matrix_x(L), W / 2];
// Where an X section cuts: a number, a key id, or "matrix" for its centre.
cut_pos = cut_key == "" ? cut_at : cut_key == "matrix" ? matrix_xy[0] : key_xy(key_by_id(cut_key))[0];

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
    if (cut == "y") translate([-big / 2, cut_pos - big, -big / 2]) cube(big);
    else if (cut == "x") translate([cut_pos, -big / 2, -big / 2]) cube([cut_depth, big, big]);
}
// Every solid goes through P() WITH A NAME, so colour survives a section cut
// and the clash check can pull any one solid out on its own:
//   only = "<id>"      draw just that solid (tools/cad.py clash)
//   list_solids = true  echo every solid's id (the clash check's inventory)
only = "";
list_solids = false;
module P(c, shell = false, id = "") {
    assert(id != "", "every solid needs an id - the clash check cannot see an unnamed one");
    if (list_solids) echo("SOLID", id);
    // highlight: solids named in it are drawn bright yellow and the rest
    // faded, so one assembly can be picked out of the body in a render.
    hl = len(highlight) > 0;
    cc = hl && len([for (h = highlight) if (h == id) 1]) > 0 ? [1.0, 0.85, 0.0]
       : hl ? [c[0], c[1], c[2], 0.18]
       : (shell && ghost_shell) ? [c[0], c[1], c[2], 0.25] : c;
    if (only == "" || only == id) color(cc)
        if (cut == "none") children();
        else if (cut == "y2d")
            mirror([0, 1]) section_2d() rotate([90, 0, 0]) translate([0, -cut_pos, 0]) children();
        else if (cut == "x2d")
            rotate(-90) section_2d() rotate([0, -90, 0]) translate([-cut_pos, 0, 0]) children();
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
// thickness sets the inset depth"); the display; service opening;
// fastener and U-bolt holes. Full width; grooves as for the oak top.
// Frame: model XY minus [x_in0, 0].
module oak_bottom_2d() {
    difference() {
        square([x_in1 - x_in0, W]);
        translate([-x_in0, 0]) {
            for (k = bottom_keys) translate(key_xy(k)) rotate(key_rot(k))
                square(switch_keycap + 2 * thumb_recess_clear, center = true);
            for (s = spare_xy) translate(s) square(switch_keycap + 2 * thumb_recess_clear, center = true);
            display_board_cut_2d();
            translate(service_xy) square([openings_service_cover_w, openings_service_cover_l], center = true);
            for (f = fasteners()) translate(f) circle(d = hardware_fastener_clear_d);
            for (u = ubolt_legs()) translate(u) circle(d = hardware_ubolt_rod_d + 0.5);
        }
    }
}

// The outline a thumb cluster's plate and board share, before cutouts.
function thumb_pts(cl) = concat([for (k = cluster_keys(cl)) key_xy(k)],
                                cl == "left_thumb" ? [spare_xy[0], spare_xy[1]] : [spare_xy[2]]);
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
        for (s = (cl == "left_thumb" ? [spare_xy[0], spare_xy[1]] : [spare_xy[2]]))
            cutout_at(s, 0, plate_cutout);
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
        rrect(W, T, 1);
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
        rrect(W, T, 1);
        translate(ec_c) circle(d = ethercon_bore_d);
        for (h = ec_holes) translate(h) circle(d = ethercon_hole_d);
        translate(usb_c) square([openings_usb_slot_w, openings_usb_slot_h], center = true);
    }
}
// Behind the tail cap: carries the connector (ADR 0009: "let the oak be the
// face the screws pass through rather than the thing the screws hold").
ubolt_bp = [hardware_ubolt_span, u_w - 6];
module ubolt_backplate_2d() {
    difference() {
        translate(ubolt_c) square(ubolt_bp, center = true);
        for (u = ubolt_legs()) translate(u) circle(d = hardware_ubolt_rod_d + 0.5);
    }
}
// The matrix window: frosted acrylic, flush with the oak top, on an oak lip
// (owner, 2026-09-26). The acrylic is the rebate's size less a fit clearance.
matrix_rebate = openings_matrix_window + 2 * openings_matrix_lip;
module matrix_window_2d() { translate(matrix_xy) offset(r = 0.5) offset(delta = -0.6) square(matrix_rebate, center = true); }
// Rebates in the oak top's upper face - a router pass, like the grooves, so
// exported on their own. Frame: as the oak panels.
module oak_rebates_2d() { translate([-x_in0, 0]) translate(matrix_xy) square(matrix_rebate, center = true); }
module service_cover_2d() {
    translate(service_xy) rotate(90) difference() {
        square([openings_service_cover_l + 6, openings_service_cover_w + 6], center = true);
        for (s = [-1, 1]) translate([s * (openings_service_cover_l / 2 + 1.5), 0]) circle(d = 2.4);
    }
}

// --------------------------------------------------------- features ------
disp_c = [(disp_x0 + disp_x1) / 2, W / 2];
// The board lies lengthwise (ADR 0008) on the UNDERSIDE, glass down, in a
// through-cut in the oak bottom (decided 2026-09-26).
// Its outline is the vendor's own DXF, not retyped numbers.
DISP_DXF = "../../datasheets/mechanical/LILYGO-T-DISPLAY-S3-AMOLED-OUTLINE.dxf";
module display_board_outline_2d() {
    translate(disp_c) rotate(-90) translate([-disp_board[1] / 2, -disp_board[0] / 2]) import(DISP_DXF, layer = "KeepOutLayer");
}
module display_board_cut_2d() { offset(delta = boards_display_cut_clear) display_board_outline_2d(); }
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
// patch plug runs down the side lane - and the LED strips stop short of that.
tail_equip_x = min(usb_plug_x0, L - ends_tail_cap_t - ethercon_depth - ethercon_rj45_plug_l);
tail_fastener_x = tail_equip_x - tail_fastener_back;

// Six fasteners up from the bottom into the plate, zig-zagging between the
// long edges ~80 mm apart (ADR 0009).
// Three stations of two, one each side: beside the underside display at the
// mouth end, in the gap between the hands, and between the last key board
// and the connector. ADR 0009's "~80 mm apart" was for a 457 mm body; on
// the derived body the stations fall where the keys are not.
fastener_x = [(disp_x0 + disp_x1) / 2, (x_gap0 + x_rh0) / 2, tail_fastener_x];
function fasteners() =
    [for (x = fastener_x, sd = [0, 1]) [x, sd == 0 ? u_y0 + hardware_fastener_inset : W - u_y0 - hardware_fastener_inset]];

// U-bolt in the inter-hand gap on the bottom face (ADR 0009); legs ACROSS the
// body, since the shortened gap has no room along it beside the thumb arc.
ubolt_c = [(x_gap0 + x_rh0) / 2, W / 2];
function ubolt_legs() = [for (s = [-1, 1]) ubolt_c + [0, s * hardware_ubolt_span / 2]];

// ================================================================ 3D ======

// The etherCON housing's bottom below the floor, if the connector is low.

module lam(z, t, c, shell = true, id = "") {
    P(c, shell, id) translate([0, 0, z]) linear_extrude(t) children();
}

module lid(dz = 0) {
    translate([0, 0, dz]) {
        P(C_OAK, true, "oak top") translate([x_in0, 0, z_oak_top_bot + explode]) difference() {
            linear_extrude(oak_top_t) oak_top_2d();
            translate([0, 0, -EPS]) linear_extrude(stack_groove_depth + EPS) oak_grooves_2d();
            translate([0, 0, oak_top_t - openings_matrix_acrylic_t]) linear_extrude(openings_matrix_acrylic_t + EPS) oak_rebates_2d();
        }
        lam(z_plate_bot + explode / 2, plate_thickness, C_ALU, false, "key plate")
            translate([plate_x0, plate_y0]) plate_top_2d();
    }
}

module u_channel() {
    P(C_OAK, true, "oak bottom") translate([x_in0, 0, -explode]) difference() {
        linear_extrude(oak_bottom_t) oak_bottom_2d();
        translate([0, 0, oak_bottom_t - stack_groove_depth]) linear_extrude(stack_groove_depth + EPS) oak_grooves_2d();
        // Fastener counterbores from the bottom face (a drill, not a cut:
        // the DXF carries the clearance hole, the drawing the counterbore).
        translate([-x_in0, 0, -EPS]) for (f = fasteners()) translate(f)
            cylinder(d = hardware_fastener_cbore_d, h = hardware_fastener_cbore_depth + EPS);
    }
    // Each side: one sheet, bottom edge in the bottom groove, top edge in the top.
    for (i = [0, 1])
        P(C_ACRYLIC, true, str("side ", i == 0 ? "left" : "right")) translate([x_in0, side_y[i] + stack_side_t, z_side0 + explode * 0.3]) rotate([90, 0, 0])
            linear_extrude(stack_side_t) side_2d();
}

module caps() {
    P(C_ACRYLIC, true, "mouth cap") translate([ends_mouth_cap_t - explode / 3, 0, 0]) rotate([90, 0, 90]) mirror([0, 0, 1])
        linear_extrude(ends_mouth_cap_t) mouth_cap_2d();
    P(C_OAK_DARK, true, "tail cap") translate([x_in1 + explode / 3, 0, 0]) rotate([90, 0, 90])
        linear_extrude(ends_tail_cap_t) tail_cap_2d();
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
    for (i = [0 : len(spare_xy) - 1]) switch_at(spare_xy[i], 0, false, str("spare ", i + 1), true);
}

module thumb_plates_3d() {
    lam(z_floor - explode * 0.5, plate_thickness, C_ALU, false, "thumb plates") thumb_plate_both_2d();
}

module cluster_boards() {
    for (cl = ["left_hand", "right_hand"])
        P(C_PCB, false, str("board ", cl)) translate([0, 0, z_plate_top - switch_pcb_below_seat - switch_pcb_t + explode * 0.25])
            linear_extrude(switch_pcb_t) offset(-0.5) cluster_window_2d(cluster_keys(cl));
    for (cl = ["left_thumb", "right_thumb"])
        P(C_PCB, false, str("board ", cl)) translate([0, 0, z_floor + switch_pcb_below_seat - explode * 0.25])
            linear_extrude(switch_pcb_t) offset(-3) thumb_outline_2d(cl);
}

module display_board() {
    // Vendor STEP, meshed; its frame matches the DXF: x across, y along, glass
    // at z = 5.5. Flipped glass-down, glass at boards_display_recess.
    P([0.22, 0.24, 0.30], false, "display board") translate([disp_c[0], disp_c[1], boards_display_recess + 5.5 - explode])
        rotate([180, 0, 0]) rotate([0, 0, -90]) translate([-disp_board[1] / 2, -disp_board[0] / 2, 0])
            import("vendor/t-display-s3-amoled.stl");   // flex clipped at mesh time (outputs.yaml)
}

module tail_equipment() {
    // The Matrix, face up under the top window.
    P([0.10, 0.10, 0.12], false, "Matrix board") translate([matrix_xy[0] - boards_matrix_board / 2, matrix_xy[1] - boards_matrix_board / 2, matrix_board_z])
        cube([boards_matrix_board, boards_matrix_board, switch_pcb_t]);
    P(C_LED, false, "Matrix LEDs") translate([matrix_xy[0] - boards_matrix_emitters / 2, matrix_xy[1] - boards_matrix_emitters / 2, matrix_board_z + switch_pcb_t])
        cube([boards_matrix_emitters, boards_matrix_emitters, boards_matrix_led_h]);
    // The Matrix's pigtail where it leaves the two pad rows, below the board;
    // the wires run on to the right mezzanine (not drawn - thin wires).
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

// ADR 0014 sized the strips at 420 mm for a 457 mm body. They now start
// 10 mm in from the mouth cap and stop 3 mm short of the last fastener pair,
// in front of the tail equipment - the USB-C plug and lead, the patch plug,
// the etherCON - which fills the strips' side channels; drc.echo reports the
// shortfall.
strip_x0 = x_in0 + 10;
strip_x1 = tail_fastener_x - 1.5 - 3;
strip_run_adr = 420;
strip_l = min(strip_run_adr, strip_x1 - strip_x0);
module led_strips() {
    for (s = [0, 1]) {
        y = s == 0 ? u_y0 + lighting_strip_gap : W - u_y0 - lighting_strip_gap - lighting_strip_t;
        P(C_LED, false, str("LED strip ", s == 0 ? "left" : "right")) translate([strip_x0, y, z_floor + cavity_h / 2 - lighting_strip_w / 2])
            cube([strip_l, lighting_strip_t, lighting_strip_w]);
    }
}

// ------------------------------------------------------------ routing -----
// The tube and the looms run along the two side channels at routing_lane_z,
// inside the LED strips, and drop to what they serve. Lanes are a model
// choice (config/body.yaml routing): the clash check reports what is in them.
// The strip sits on the side's inside face; strip_gap is the diffusion gap
// between them (ADR 0014), so the strip stands strip_gap in from the side.
function lane_y(side, d) = side == "left" ? u_y0 + lighting_strip_gap + lighting_strip_t + 1 + d / 2
                                          : W - u_y0 - lighting_strip_gap - lighting_strip_t - 1 - d / 2;
tube_y = lane_y(routing_tube_lane, routing_tube_od);
// A FLAT RIBBON through points: each segment is swept with the ribbon's
// cross-section turned to suit its direction - lying FLAT along and across
// the body, on edge only where it drops to a socket. Stood on edge along the
// body, a 15 mm ribbon does not fit the 12-13 mm between the thumb boards'
// parts and the key boards' parts (found by the clash check, 2026-09-26).
module ribbon(pts, w) {
    t = routing_ribbon_t;
    for (i = [0 : len(pts) - 2]) let(a = pts[i], b = pts[i + 1], dv = [abs(b[0] - a[0]), abs(b[1] - a[1]), abs(b[2] - a[2])],
                                   ax = dv[0] >= dv[1] && dv[0] >= dv[2] ? 0 : dv[1] >= dv[2] ? 1 : 2,
                                   sec = ax == 0 ? [0.01, w, t] : ax == 1 ? [w, 0.01, t] : [w, t, 0.01])
        hull() { translate(a) cube(sec, center = true); translate(b) cube(sec, center = true); }
}
// A run through points, as a chain of hulled spheres.
module run(pts, d) {
    for (i = [0 : len(pts) - 2]) hull() { translate(pts[i]) sphere(d = d, $fn = 16); translate(pts[i + 1]) sphere(d = d, $fn = 16); }
}
// The display's two header-socket strips (LilyGO DXF), standing into the cavity.
disp_sock_x0 = disp_c[0] + 35.433 - disp_board[0] / 2 - 17.78;
disp_sock_x1 = disp_sock_x0 + 35.56;
disp_sock_top = boards_display_recess + 6.6 + boards_disp_socket_h;
top_z = z_plate_top - switch_pcb_below_seat - switch_pcb_t;     // top cluster boards' underside
thumb_z = z_floor + switch_pcb_below_seat + switch_pcb_t;       // thumb boards' top face
function mid_x(cl) = (min(xs(cluster_keys(cl))) + max(xs(cluster_keys(cl)))) / 2;
function sgn(side) = side == "right" ? 1 : -1;
function xspan(cl) = [min(xs(cluster_keys(cl))), max(xs(cluster_keys(cl)))];

// STACKING HEADERS (owner, 2026-09-26: "tighter vertically with stacking
// headers"). Where the chain hops from a thumb board to the key board
// straight above it (RT -> RH, LT -> LH), one 2 x 6 header runs from the
// thumb board's top face to the key board's underside, where the two
// overlap along the body, on the side away from the tube. It passes through
// the mezzanine between them. It engages as the lid closes, so it must
// blind-mate; its height is the board gap, not a stock size.
stack_pairs = [["right_thumb", "right_hand"], ["left_thumb", "left_hand"]];
// It lies along the body at the key board's edge (clear of the top
// switches' pins, which are on the centreline), midway between two thumb
// keys (clear of theirs), at the mid nearest the middle of where the two
// boards overlap, on the side away from the tube.
function thumb_mids(cl) = let(t = xs(cluster_keys(cl))) [for (i = [0 : len(t) - 2]) (t[i] + t[i + 1]) / 2];
function stack_mid(pr) = let(a = xspan(pr[0]), b = xspan(pr[1]), m = (max(a[0], b[0]) + min(a[1], b[1])) / 2,
                             mids = thumb_mids(pr[0]), d = [for (x = mids) abs(x - m)]) mids[search(min(d), d)[0]];
function stack_c(pr) = [stack_mid(pr), W / 2 - sgn(routing_tube_lane) * (switch_cluster_pcb_w / 2 - boards_stack_w / 2 - 0.5)];
stack_sz = [boards_stack_l, boards_stack_w];   // along the body
function stack_of(cl) = [for (pr = stack_pairs) if (pr[0] == cl || pr[1] == cl) stack_c(pr)];

// NO CARRIER (owner, 2026-09-26: "we don't need a carrier" - "standoffs off
// the oak, and standoffs / attaching headers on PCBs"). Its circuits go on
// two MEZZANINES, one in each gap between a thumb board and the key board
// above it, threaded on that pair's stacking header and standing on
// standoffs off the oak bottom. RIGHT: the breath sensor with its reference
// and ADC, the umbilical, the SPI out to the module, and the Matrix's
// regulator. LEFT: the display's regulator, the display link and the
// LED-strip drive - one regulator per dev board (ADR 0013), and the breath
// sensor as far from the display's AMOLED as the mezzanines allow, because
// it is the hottest thing in the instrument (ADR 0003). Each runs its key board's length
// (the left one starts past the display) and the width between the strips;
// it is single-sided, parts up, and the key board's parts are its ceiling.
// The chain runs through them: Matrix -> right mezzanine -> RT, RH through
// the right stack -> the link between the hands -> left mezzanine -> LT, LH.
mezz_z = thumb_z + boards_cluster_smt_h + boards_mezz_clear;          // underside
mezz_top = mezz_z + switch_pcb_t;
mezz_room = top_z - boards_cluster_smt_h - boards_mezz_clear - mezz_top;   // parts height above it
mezz_w = u_w - 2 * (lighting_strip_gap + lighting_strip_t + boards_mezz_clear);
function mezz_side(pr) = pr[1] == "left_hand" ? "left" : "right";
function mezz_x(pr) = let(k = xspan(pr[1]), e = plate_cutout / 2 + cluster_margin)
    [pr[1] == "left_hand" ? max(k[0] - e, disp_sock_x1 + boards_mezz_clear) : k[0] - e, k[1] + e];
function mezz_y() = [W / 2 - mezz_w / 2, W / 2 + mezz_w / 2];
mz_l = mezz_x(stack_pairs[1]);
mz_r = mezz_x(stack_pairs[0]);
// SUPPORTS (owner: "standoffs off the oak, and standoffs / attaching
// headers on PCBs"): spacers down onto the thumb board, midway between two
// of its keys (clear of their pins) wherever the stacking header is not;
// and standoffs down to the oak at an end of the mezzanine that runs well
// past the thumb board.
// A spacer is placed only where it clears every thumb switch's footprint
// (a right-thumb key off the centreline sits under the board's edge, so
// there it moves to the centreline).
ks33_stub = 2.6;   // half-width of the KS-33's pole and pins where they stand proud of a board [clash.txt, off the vendor STEP]
function clear_of_thumbs(p, cl) = min([for (k = cluster_keys(cl)) max(abs(key_xy(k)[0] - p[0]), abs(key_xy(k)[1] - p[1]))])
                                  >= ks33_stub + boards_standoff_d / 2 + 0.3;
function spacers(pr) = let(y = mezz_y(), i = boards_standoff_d / 2 + 1)
    [for (xx = thumb_mids(pr[0])) if (xx != stack_mid(pr))
        let(edge = [for (yy = [y[0] + i, y[1] - i]) if (clear_of_thumbs([xx, yy], pr[0])) [xx, yy]])
        each (len(edge) > 0 ? edge : clear_of_thumbs([xx, W / 2], pr[0]) ? [[xx, W / 2]] : [])];
function standoffs(pr) = let(x = mezz_x(pr), t = xspan(pr[0]), y = mezz_y(), i = boards_standoff_d / 2 + 1, reach = rc / 2 + 16)
    [for (xx = [x[0] + i, x[1] - i], yy = [y[0] + i, y[1] - i]) if (xx < t[0] - reach || xx > t[1] + reach) [xx, yy]];

// THE BREATH SENSOR: MPXV4006DP case 1351-01, SURFACE MOUNT (datasheet p.2),
// on the right mezzanine at its mouth-end edge, ports facing the mouth and
// overhanging the edge (the lower barb reaches the board's surface, so the
// ports must overhang it - p.7). Lead rows run along X, leads out to +-Y.
sensor_c = [mz_r[0] + boards_sensor_body / 2,
            routing_tube_lane == "left" ? mezz_y()[0] + boards_sensor_leads / 2 + 0.5 : mezz_y()[1] - boards_sensor_leads / 2 - 0.5];
sensor_face_x = sensor_c[0] - boards_sensor_body / 2;
p1_tip = [sensor_face_x - boards_sensor_port_l, sensor_c[1] - 2.1, mezz_top + boards_sensor_port_z[0]];
module sensor_3d() {
    P([0.20, 0.20, 0.22], false, "breath sensor") union() {
        translate([sensor_c[0] - boards_sensor_body / 2, sensor_c[1] - boards_sensor_body / 2, mezz_top])
            cube([boards_sensor_body, boards_sensor_body, boards_sensor_h]);
        translate([sensor_c[0] - 5.1, sensor_c[1] - boards_sensor_leads / 2, mezz_top]) cube([10.2, boards_sensor_leads, 1.2]);
        for (i = [0, 1]) translate([sensor_face_x + EPS, sensor_c[1] + (i == 0 ? -2.1 : 2.1), mezz_top + boards_sensor_port_z[i]])
            rotate([0, -90, 0]) cylinder(d = boards_sensor_port_d, h = boards_sensor_port_l);
    }
}
// FFC connectors (right-angle ZIF), all on the side away from the tube: the
// link between the hands - at the left mezzanine's tail end, and just behind
// the sensor on the right one, its cable passing beside the sensor - and the
// display link at the left one's mouth end.
function zif_y(l) = W / 2 - sgn(routing_tube_lane) * (mezz_w / 2 - l / 2 - 0.3);
zif_link = [[mz_l[1] - boards_zif_w / 2, zif_y(boards_zif_l)], [mz_r[0] + boards_sensor_body + 1 + boards_zif_w / 2, zif_y(boards_zif_l)]];
zif_disp = [mz_l[0] + boards_zif_w / 2, zif_y(boards_zif_disp_l)];
// Each mezzanine's tall parts - a regulator module and its bulk capacitors:
// the right one's at its tail end, the left one's just behind the display
// link, both clear of the stacking header.
tall_c = [[mz_l[0] + boards_zif_w + 1 + boards_tall_l / 2, W / 2], [mz_r[1] - 2 - boards_tall_l / 2, W / 2]];

module mezzanines_3d() {
    for (pr = stack_pairs) let(x = mezz_x(pr), y = mezz_y(), sd = mezz_side(pr)) {
        P(C_PCB, false, str("mezzanine ", sd)) translate([x[0], y[0], mezz_z]) cube([x[1] - x[0], mezz_w, switch_pcb_t]);
        for (i = [0 : len(standoffs(pr)) - 1]) if (len(standoffs(pr)) > 0) let(c = standoffs(pr)[i]) P(C_STEEL, false, str("standoff ", sd, " ", i + 1))
            translate([c[0], c[1], z_floor]) cylinder(d = boards_standoff_d, h = mezz_z - z_floor, $fn = 6);
        for (i = [0 : len(spacers(pr)) - 1]) if (len(spacers(pr)) > 0) let(c = spacers(pr)[i]) P(C_STEEL, false, str("spacer ", sd, " ", i + 1))
            translate([c[0], c[1], thumb_z]) cylinder(d = boards_standoff_d, h = mezz_z - thumb_z, $fn = 6);
        // SMT parts over the whole top face, less what stands on it.
        P([0.35, 0.55, 0.40], false, str("parts mezzanine ", sd)) translate([0, 0, mezz_top]) linear_extrude(boards_smt_h) difference() {
            translate([x[0] + 0.5, y[0] + 0.5]) square([x[1] - x[0] - 1, mezz_w - 1]);
            translate(stack_c(pr)) square(stack_sz + [1, 1], center = true);
            for (c = concat(standoffs(pr), spacers(pr))) translate(c) circle(d = boards_standoff_d + 0.5);
            translate(tall_c[sd == "left" ? 0 : 1]) square([boards_tall_l + 1, boards_tall_w + 1], center = true);
            if (sd == "left") {
                translate(zif_link[0]) square([boards_zif_w + 1, boards_zif_l + 1], center = true);
                translate(zif_disp) square([boards_zif_w + 1, boards_zif_disp_l + 1], center = true);
            } else {
                translate(sensor_c) square([boards_sensor_body + 1, boards_sensor_leads + 1], center = true);
                translate(zif_link[1]) square([boards_zif_w + 1, boards_zif_l + 1], center = true);
            }
        }
    }
    for (i = [0, 1]) P([0.30, 0.30, 0.55], false, str("tall parts mezzanine ", i == 0 ? "left" : "right"))
        translate([tall_c[i][0] - boards_tall_l / 2, tall_c[i][1] - boards_tall_w / 2, mezz_top])
            cube([boards_tall_l, boards_tall_w, boards_tall_h]);
    for (z = [["link left", zif_link[0], boards_zif_l], ["link right", zif_link[1], boards_zif_l], ["display link", zif_disp, boards_zif_disp_l]])
        P([0.85, 0.85, 0.80], false, str("ZIF ", z[0])) translate([z[1][0] - boards_zif_w / 2, z[1][1] - z[2] / 2, mezz_top])
            cube([boards_zif_w, z[2], boards_zif_h]);
}

module headers_3d() {
    // Stacking headers: one solid from the thumb board's top face to the key
    // board's underside, through the mezzanine, named for the pair.
    for (pr = stack_pairs) let(c = stack_c(pr))
        P([0.12, 0.12, 0.14], false, str("J-STACK ", pr[0], " to ", pr[1]))
            translate([c[0] - stack_sz[0] / 2, c[1] - stack_sz[1] / 2, thumb_z]) cube([stack_sz[0], stack_sz[1], top_z - thumb_z]);
}

// PARTS ON THE BOARDS, as envelopes. Cluster boards: a component layer on
// the cavity side (the plate side cannot take a SOIC - ks33-geometry.md).
// The Matrix: its back-side parts. The display board: its two header-socket
// strips, standing up. The mezzanines' parts are with the mezzanines.
module parts_3d() {
    for (cl = ["left_hand", "right_hand"])
        P([0.35, 0.55, 0.40], false, str("parts ", cl)) translate([0, 0, top_z - boards_cluster_smt_h])
            linear_extrude(boards_cluster_smt_h) difference() {
                offset(-0.5) cluster_window_2d(cluster_keys(cl));
                for (h = stack_of(cl)) translate(h) square(stack_sz + [1, 1], center = true);
            }
    for (cl = ["left_thumb", "right_thumb"])
        P([0.35, 0.55, 0.40], false, str("parts ", cl)) translate([0, 0, thumb_z])
            linear_extrude(boards_cluster_smt_h) difference() {
                offset(-3) thumb_outline_2d(cl);
                for (h = stack_of(cl)) translate(h) square(stack_sz + [1, 1], center = true);
                for (pr = stack_pairs) if (pr[0] == cl) for (c = spacers(pr)) translate(c) circle(d = boards_standoff_d + 1);
            }
    P([0.20, 0.20, 0.22], false, "Matrix underside parts") translate([matrix_xy[0] - 9.5, matrix_xy[1] - 9.5, matrix_board_z - boards_matrix_under_h])
        cube([19, 19, boards_matrix_under_h]);
    // Display board frame (LilyGO DXF): rows at x = 1.289 / 24.149, centred
    // y = 35.433, 14 pins; mapped to the body as display_board() places it.
    for (bx = [1.289, 24.149]) P([0.12, 0.12, 0.14], false, str("display socket ", bx < 10 ? 1 : 2))
        translate([disp_c[0] + 35.433 - disp_board[0] / 2 - 17.78, disp_c[1] + bx - disp_board[1] / 2 - 1.27, boards_display_recess + 6.6])
            cube([35.56, 2.54, boards_disp_socket_h]);
}

module routing_3d() {
    trap_y = u_y0 + lighting_strip_gap + lighting_strip_t + 1 + routing_trap_d / 2;
    // The trap sits over the display's socket strips, ending before the left
    // mezzanine and the left-hand key board (the two leave it no height); from it the tube runs down the tube lane over the left
    // mezzanine's parts, across the gap, onto the sensor on the right one.
    trap_x0 = min(mz_l[0], xspan("left_hand")[0] - plate_cutout / 2 - cluster_margin) - boards_mezz_clear - routing_trap_l;
    run_z = mezz_top + boards_smt_h + routing_tube_od / 2 + boards_mezz_clear;
    // The trap rides over the display's socket strips.
    trap_z = max(routing_lane_z, disp_sock_top + routing_trap_d / 2 + boards_mezz_clear);
    P([0.95, 0.60, 0.45], false, "breath tube") run([
        [0, tube_yz[0], tube_yz[1]], [x_in0 + 3, tube_yz[0], tube_yz[1]],
        [x_in0 + 12, tube_y, trap_z],
        [trap_x0 - 6, tube_y, trap_z], [trap_x0, trap_y, trap_z]], routing_tube_od);
    P([0.95, 0.60, 0.45], false, "breath trap") translate([trap_x0, trap_y, trap_z]) rotate([0, 90, 0])
        cylinder(d = routing_trap_d, h = routing_trap_l);
    // Onto the sensor's P1 barb (the upper port, datasheet p.6 Table 3).
    P([0.95, 0.60, 0.45], false, "breath tube to sensor") run([
        [trap_x0 + routing_trap_l, trap_y, trap_z], [mz_l[0] + 4, tube_y, run_z], [mz_l[1], tube_y, run_z],
        [p1_tip[0] - 6, p1_tip[1], p1_tip[2]], [p1_tip[0] + 2, p1_tip[1], p1_tip[2]]], routing_tube_od * 0.8);
    // FLAT FLEX: the link between the hands, straight across the gap from
    // ZIF to ZIF; and the display link, from the left mezzanine's mouth end
    // down onto the display's socket strips.
    t = routing_ribbon_t;
    lz = mezz_top + boards_zif_h / 2;
    lz_over = mezz_top + max(boards_zif_h, boards_smt_h) + t / 2 + 0.2;
    P([0.80, 0.60, 0.25], false, "FFC between the hands") ribbon([
        [zif_link[0][0] + boards_zif_w / 2, zif_link[0][1], lz], [mz_r[0] - 3, zif_link[0][1], lz],
        [mz_r[0] - 0.5, zif_link[1][1], lz_over], [zif_link[1][0] - boards_zif_w / 2, zif_link[1][1], lz_over]], routing_ffc_w);
    P([0.80, 0.60, 0.25], false, "FFC to the display") ribbon([
        // over the mezzanine's own parts, then down onto the display's sockets
        [zif_disp[0] - boards_zif_w / 2, zif_disp[1], lz_over], [disp_sock_x1 + 3, zif_disp[1], lz_over],
        [disp_sock_x1 + 1, zif_disp[1], disp_sock_top + t / 2 + 0.3], [disp_c[0] + 6, zif_disp[1], disp_sock_top + t / 2 + 0.3]], routing_ffc_disp_w);
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
    lam(-1.5 - explode, 1.5, C_ACRYLIC, false, "service cover") service_cover_2d();
}

module assembly() {
    if (show_u) u_channel();
    if (show_caps) caps();
    if (show_lid) lid(explode);
    if (show_keys) { keys_3d(); thumb_plates_3d(); }
    if (show_boards) { cluster_boards(); display_board(); tail_equipment(); }
    if (show_strips) led_strips();
    if (show_routing) routing_3d();
    if (show_boards) { sensor_3d(); headers_3d(); parts_3d(); mezzanines_3d(); }
    if (show_hardware) hardware_3d();
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
    drc(undef, "what the mouth end needs", mouth_req - (x_in0 + layout_mouth_extra + switch_keycap / 2 + stack_cap_clear) > 0.01
        ? "the display on the underside (it must clear the left-thumb recesses)" : "the first top key",
        str("display occupies X ", disp_x0, " to ", disp_x1));
    tail_names = ["last key board, the last fastener pair, then the patch plug and the etherCON depth",
                  "last key board, the LED matrix on the top face, then the etherCON depth (matrix not centred)",
                  "right-thumb cluster, the service cover, then the etherCON depth",
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
    drc(strip_l >= strip_run_adr, "LED strips at ADR 0014's length", strip_l,
        str("mm per side against ", strip_run_adr, " in ADR 0014 - fewer LEDs per side if shorter"));
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
    rc = switch_keycap + 2 * thumb_recess_clear;
    feats = concat([for (k = bottom_keys) [k[0], key_xy(k), [rc, rc]]],
                   [for (i = [0 : 2]) [str("spare ", i + 1), spare_xy[i], [rc, rc]]],
                   [                    ["service opening", service_xy, [openings_service_cover_w, openings_service_cover_l]],
                    ["display", disp_c, [disp_board[0] + 1, disp_board[1] + 1]],
                    for (u = ubolt_legs()) ["U-bolt leg", u, [hardware_ubolt_rod_d, hardware_ubolt_rod_d]]],
                   [for (i = [0 : len(fasteners()) - 1]) [str("M3 #", i + 1), fasteners()[i], [hardware_fastener_cbore_d, hardware_fastener_cbore_d]]]);
    function gap(a, b) = max(abs(a[1][0] - b[1][0]) - (a[2][0] + b[2][0]) / 2,
                             abs(a[1][1] - b[1][1]) - (a[2][1] + b[2][1]) / 2);
    clashes = [for (i = [0 : len(feats) - 1], j = [i + 1 : 1 : len(feats) - 1])
               if (gap(feats[i], feats[j]) < 3) str(feats[i][0], " / ", feats[j][0], " ", gap(feats[i], feats[j]))];
    drc(len(clashes) == 0, "oak-bottom cuts at least 3 mm apart (display, thumb recesses, spares, window, service, U-bolt, counterbores)",
        clashes, "pairs closer than 3 mm, with the web between them (negative = overlap)");
    // Through-cuts only: a fastener's counterbore is partial depth from the
    // outside face, so its clearance hole is what meets the side.
    function thru_w(f) = f[0][0] == "M" ? hardware_fastener_clear_d : f[2][1];
    edge = min([for (f = feats) min(f[1][1] - thru_w(f) / 2 - u_y0, W - u_y0 - f[1][1] - thru_w(f) / 2)]);
    drc(edge >= 2, "oak-bottom cuts inside the U", edge, "mm, smallest web to the inside of a side");

    // Sides in grooves
    drc(undef, "interior width between the acrylic sides", u_w, "mm - was the full width less two sides; the oak lips now come off it too");
    drc(stack_groove_depth <= min(oak_top_t, oak_bottom_t) / 2, "groove leaves at least half the oak under it",
        min(oak_top_t, oak_bottom_t) - stack_groove_depth, "mm of oak under the groove in the thinner panel");
    drc(stack_side_inset >= 2, "oak lip outside each groove", stack_side_inset, "mm - thinner and it splits off along the grain");

    // Z stack
    drc(cavity_h > 0, "cavity height", cavity_h, "mm between the key plate and the oak bottom");
    z_pole = z_plate_top - switch_pole_tip_below_seat;
    drc(undef, "top switch pole tip below the lid", z_lid_bot - z_pole, "mm into the cavity");
    dz_disp = boards_display_recess + 6.6;
    drc(undef, "display board height above the floor", dz_disp - z_floor,
        "mm it stands into the cavity (6.6 = the vendor STEP's full stack); keep the thumb plate and looms off it");
    echo("DRC", "INFO", "oak bottom thickness (thumb keys flush at full travel)", oak_bottom_t,
         "mm, the same rule as the oak top; thumb caps stand proud of the bottom face by the travel at rest");
    th_pole = z_floor + switch_pole_tip_below_seat;
    drc(undef, "thumb switch pole tip height in the cavity", th_pole, "mm above the bottom face");

    // Mezzanines (no carrier, 2026-09-26)
    for (pr = stack_pairs) let(x = mezz_x(pr))
        echo("DRC", "INFO", str("mezzanine ", mezz_side(pr), " (derived)"), [x[1] - x[0], mezz_w],
             str("mm long x wide, at ", mezz_z, " mm up; the key board's run and the width between the strips"));
    drc(mezz_room >= boards_smt_h, "mezzanine parts room under the key boards", mezz_room,
        "mm from its top face to the key board's parts, less clearances - the height every mezzanine part must fit");
    drc(boards_sensor_h <= mezz_room, "breath sensor fits on the right mezzanine", mezz_room - boards_sensor_h, "mm spare above it");
    drc(boards_tall_h <= mezz_room, "tall parts fit on the mezzanines", mezz_room - boards_tall_h,
        "mm spare - negative means the bulk capacitors lie down or go SMD polymer, and the bucks lie flat");
    drc(boards_stack_l + 2 <= mz_r[1] - mz_r[0], "stacking header lands on the mezzanine", mz_r[1] - mz_r[0], "mm of board along the body");
    echo("DRC", "INFO", "FFC link between the hands", zif_link[1][0] - zif_link[0][0],
         "mm, ZIF centre to ZIF centre; buy it with a service loop so the lid opens");

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
    else if (p == "service_cover") service_cover_2d();
    else assert(false, str("unknown part ", p));
}

function origin_x() = origin == "centre" ? -L / 2 : origin == "tail" ? -L : 0;
module at_origin() { translate([origin_x(), 0, 0]) children(); }

if (!figure) {
    if (part == "assembly") at_origin() assembly();
    else if (part == "drc") drc_report();
    else part_2d(part);
}
