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
cut_key = "";         // or name a key (or "matrix", or "ribbon" for the left key board's, or "kb_mount" for its tail column): the cut goes through its centre
cut_depth = 1000;     // "x" keeps a slab this deep beyond the cut
figure = false;       // set true by a figure that includes this file
// Where X = 0 sits in the rendered picture: "mouth" (the model's own frame),
// "centre" or "tail". Cameras aim at the origin, so a render stays framed
// when the derived length changes.
origin = "mouth";

LAYERS = ["plate_top", "oak_top", "oak_bottom", "oak_grooves", "plate_bottom", "side",
          "mouth_cap", "tail_cap", "matrix_window", "oak_rebates", "oak_pockets"];

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
// Thumb keys too (same date): the bottom plate is on the oak bottom's inside
// face, so the same rule sets the oak bottom from below.
oak_bottom_t = switch_keycap_top_above_seat - switch_total_travel;
z_oak_top_bot = T - oak_top_t;                  // underside of the oak = plate top face
z_plate_top = z_oak_top_bot;                    // the switch seat
z_plate_bot = z_plate_top - plate_thickness;
z_lid_bot = z_plate_bot;                        // the lid's underside is the plate's
z_floor = oak_bottom_t;                   // inside face of the oak bottom
z_bplate_top = z_floor + plate_thickness;       // the bottom plate, on the inside face
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
cluster_margin = boards_kb_end_margin;   // a key board's MOUTH end past its first switch cutout (the board itself: kb_rect)
tail_margin = boards_kb_tail_margin;     // and its TAIL end past its last: longer, for the tail corners' column pockets beside the last keys' cap slots

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
// BEHIND THE MATRIX, IN ORDER: the USB-C extension's plug off the Matrix's
// tail edge (if that edge faces the tail), a clearance, then the etherCON
// (ADR 0021): its adapter board, the connector's body to the flange, and the
// tail cap. The adapter stands the connector's full height, so it queues
// behind the Matrix; J-UMB, low on the main board, passes under it.
usb_behind = openings_matrix_usb_to_tail ? openings_usb_plug_l : 0;
ec_stack_d = boards_umb_adapter_t + ethercon_pcb_setback;   // the adapter's rear face to the flange's front face
behind_matrix = usb_behind + layout_tail_clear + ec_stack_d + ends_tail_cap_t;
// IN FRONT OF IT: the USB-C plug off the mouth edge (if that edge faces the
// mouth) reaches forward, and must clear the right-hand key board. Measured
// from the last key centre to where the equipment starts. (A pair of lid
// screws stood here until the module, ADR 0025.)
usb_front = openings_matrix_usb_to_tail ? 0 : openings_usb_plug_l;
equip_start_rel = plate_cutout / 2 + tail_margin + layout_tail_clear;
tail_claims_rel = [
    top_last_rel + equip_start_rel + boards_umb_joint_d + ec_stack_d + ends_tail_cap_t,
    top_last_rel + plate_cutout / 2 + tail_margin + layout_tail_clear + boards_matrix_board + behind_matrix,
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
// the Matrix board face up under the plate, past the last key board.
matrix_near_x = top_last + plate_cutout / 2 + tail_margin + layout_tail_clear + boards_matrix_board / 2;
function matrix_x(l) = layout_matrix_centred ? (top_last + cap_edge_rel + l) / 2 : matrix_near_x;

L = top_last + tail_req;
x_in1 = L - ends_tail_cap_t;
matrix_xy = [matrix_x(L), W / 2];
// Where an X section cuts: a number, a key id, or "matrix" for its centre.
// A Y cut through a named key goes through its Y (its row along the body).
function cut_pos() = cut_key == "" ? cut_at : cut_key == "matrix" ? matrix_xy[0] :
        cut_key == "kb_mount" ? kb_mounts("left_hand")[2][cut == "y" || cut == "y2d" ? 1 : 0] : cut_key == "ribbon" ? (cut == "y" || cut == "y2d" ? chain_y : chain_x("left_hand"))
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
C_BRASS = [0.78, 0.62, 0.33];
// A PARTS ENVELOPE is not a part: it is the volume a board's components may
// fill, which clash.txt checks against everything else. Translucent amber, so
// no render shows it as a second board.
C_ENVELOPE = [0.95, 0.72, 0.25, 0.35];
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

// Key plate: the cassette's top, in the plate's own frame = model XY minus
// origin. A clearance hole at each column, for the screw that ties the plate
// to its standoff (ADR 0025).
module plate_top_2d() {
    difference() {
        translate([0, stack_groove_clear]) square([plate_x1 - x_in0, u_w - 2 * stack_groove_clear]);
        translate([-plate_x0, -plate_y0]) {
            for (k = top_keys) cutout_at(key_xy(k), key_rot(k), plate_cutout);
            for (m = columns()) translate(m) circle(d = hardware_col_plate_hole);
        }
    }
}

// Oak top: the wood ON TOP of the key plate, full width. One hole per key
// (or one slot per hand), which the cap travels in. Nothing else goes
// through it: the column screws' heads sit in blind pockets in its underside
// (ADR 0025), so the playing face is unbroken. The side grooves and the
// pockets are NOT in this outline: they are a saw cut and a drilled blind
// pocket, not through-cuts, and export separately (oak_grooves_2d,
// oak_pockets_2d). Frame: model XY minus [x_in0, 0].
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
// thickness sets the inset depth"), plus the U-bolt's leg holes. Full width;
// grooves as for the oak top. Frame: model XY minus [x_in0, 0].
module oak_bottom_2d() {
    difference() {
        square([x_in1 - x_in0, W]);
        translate([-x_in0, 0]) {
            if (stack_cap_holes == "slot")
                for (g = thumb_slots()) keys_2d(g, rc);
            else
                for (k = bottom_keys) translate(key_xy(k)) rotate(key_rot(k)) square(rc, center = true);
            for (s = spare_xy) translate(s) square(switch_keycap + 2 * thumb_recess_clear, center = true);
            for (u = ubolt_legs()) translate(u) circle(d = ubolt_hole_d);
        }
    }
}

// Where a thumb cluster's switches are.
function thumb_pts(cl) = [for (k = cluster_keys(cl)) key_xy(k)];
// THE BOTTOM PLATE (owner, 2026-09-29; ADR 0025): one aluminium plate the
// length of the main board, on the oak bottom's inside face, where the two
// thumb plates were - the cassette's floor. It carries the thumb switches'
// cutouts, the U-bolt's leg holes and a stud at every one of the main
// board's mounts, pressed in from its underside. Across, as the key plate;
// along, from the mouth cap to short of J-UMB at the tongue's end: J-UMB's
// through-hole tails stand below the tongue, and behind it the etherCON's
// adapter stands on the oak (the connector stands on the floor, ec_clear
// above it). Frame: as the key plate's, model XY minus [x_in0, u_y0].
// Its extent, bplate_x1 and bplate_y, is set below the etherCON's placement.
module plate_bottom_2d() {
    difference() {
        translate([0, stack_groove_clear]) square([bplate_x1 - x_in0, u_w - 2 * stack_groove_clear]);
        translate([-plate_x0, -plate_y0]) {
            for (k = bottom_keys) cutout_at(key_xy(k), key_rot(k), plate_cutout);
            for (u = ubolt_legs()) translate(u) circle(d = ubolt_hole_d);
            // the main board's studs, pressed in from the plate's underside
            for (c = cb_standoffs) translate(c) circle(d = hardware_stud_hole);
        }
    }
}

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

// The NE8FAV (ADR 0021), rear-mounted: flange and body behind the tail cap,
// soldered to the umbilical adapter, which stands parallel to the cap. Its
// flange is square, so ethercon.rotated turns only the latch: false puts the
// PUSH tab on top, the contact rows above the axis and G below it.
ec_rot = ethercon_rotated ? 90 : 0;
ec_fl = ethercon_rotated ? [ethercon_flange_h, ethercon_flange_w] : [ethercon_flange_w, ethercon_flange_h];   // [across Y, height Z]
ec_clear = 0.3;    // drawing convention: connector envelope to the floor
// THE CONNECTOR STANDS ON THE FLOOR (owner, 2026-09-26: raise the body's
// thickness rather than pocket the oak bottom): the flange's lower edge
// ec_clear above the oak bottom, the axis half a flange above that.
ec_c = [W / 2 + ethercon_offset_y, z_floor + ec_clear + ec_fl[1] / 2];    // etherCON centre on the tail face
ec_panel_x = L - ends_tail_cap_t;                  // the flange's front face, on the tail cap's inside face
ec_pcb_x1 = ec_panel_x - ethercon_pcb_setback;     // the adapter's front face
ua_x0 = ec_pcb_x1 - boards_umb_adapter_t;          // the adapter's rear face
// The bottom plate's end, short of J-UMB, and its width, as the key plate's.
bplate_x1 = ua_x0 - boards_umb_joint_d - boards_board_clear;
bplate_y = [u_y0 + stack_groove_clear, W - u_y0 - stack_groove_clear];
// The panel holes, upper left and lower right seen from the front ([ds]);
// from the front, +Y is on the right. (Y, Z) on the tail face.
ec_holes = [for (s = [-1, 1]) ec_c + s * [ethercon_hole_dx, -ethercon_hole_dy] / 2];
// A point given (across, up) from the axis in the connector's own frame, on the tail face.
function ec_pt(p) = ec_c + (ethercon_rotated ? [p[1], -p[0]] : p);
// THE TAIL CAP'S RECESS: the NE8FAV takes a panel of ethercon.panel_max at
// most, and the cap is thicker, so a pocket from outside leaves that much
// oak where the flange clamps. It takes the flange's outline, the PUSH tab
// (which stands in it, in front of the panel), and a margin for the cable
// connector's shell and a thumb. A router pass, like the USB-C overmould
// pocket: the DXF carries the through-cuts only.
ec_panel_t = min(ethercon_panel_max, ends_tail_cap_t);
function ethercon_fl_top() = ethercon_flange_h / 2;   // the flange's edge above the axis, in the connector's frame
ec_recess_d = ends_tail_cap_t - ec_panel_t;
module ec_recess_2d() {
    offset(r = ethercon_recess_margin) hull() {
        translate(ec_c) square(ec_fl, center = true);
        for (s = [-1, 1]) translate(ec_pt([s * ethercon_tab_w / 2, ethercon_tab_top])) circle(d = EPS * 10);
    }
}
// The USB-C extension's receptacle (owner, 2026-09-26): beside the
// etherCON, inside the sides, at the cavity's mid height. Stood on end
// (openings.usb_slot_portrait) it fits the lane between the etherCON's
// flange and the side, and sits centred in it, so the oak web to the flange
// and the room to the side share what the lane has spare.
usb_web_min = 2;   // drawing convention: oak between two tail-face cutouts
usb_sz = openings_usb_slot_portrait ? [openings_usb_slot_h, openings_usb_slot_w] : [openings_usb_slot_w, openings_usb_slot_h];   // [across Y, height Z]
usb_lane = [ec_c[0] + ec_fl[0] / 2, W - u_y0];   // flange edge to the side's inside face
usb_c = [(usb_lane[0] + usb_lane[1]) / 2, z_floor + cavity_h / 2];
// THE OVERMOULD POCKET (openings.usb_overmold): from the tail face down to a
// thin panel, so the plug's overmould reaches the receptacle, whose nose
// passes the panel's slot with its face level with the pocket floor. A
// router pass, like the counterbores: the DXF carries the through-cut slot.
usb_om = openings_usb_slot_portrait ? [openings_usb_overmold[1], openings_usb_overmold[0]] : openings_usb_overmold;   // [across Y, height Z]
usb_pocket_d = ends_tail_cap_t - openings_usb_panel_t;
usb_cut_y = max(usb_sz[0], usb_om[0]);   // the widest USB-C cutout on the tail face, across

module tail_cap_2d() {
    difference() {
        rrect(W, T, stack_edge_r);
        translate(ec_c) circle(d = ethercon_bore_d);
        for (h = ec_holes) translate(h) circle(d = ethercon_hole_d);
        translate(usb_c) square(usb_sz, center = true);
    }
}
// The matrix window: frosted acrylic, flush with the oak top, on an oak lip
// (owner, 2026-09-26). The acrylic is the rebate's size less a fit clearance.
matrix_rebate = openings_matrix_window + 2 * openings_matrix_lip;
module matrix_window_2d() { translate(matrix_xy) offset(r = 0.5) offset(delta = -0.6) square(matrix_rebate, center = true); }
// Rebates in the oak top's upper face - a router pass, like the grooves, so
// exported on their own. Frame: as the oak panels.
module oak_rebates_2d() { translate([-x_in0, 0]) translate(matrix_xy) square(matrix_rebate, center = true); }
// THE COLUMN SCREWS' POCKETS (ADR 0025): blind, drilled up into the oak top's
// underside over each column screw's head, which bears on the key plate. A
// drill, not a through-cut, so exported on their own, like the grooves and
// the rebates; their depth is the head's and a clearance
// (drc.echo "column screw pockets leave wood over them"). Frame: as the oak panels.
col_pocket_depth = hardware_col_screw_head_h + hardware_col_pocket_clear;
module oak_pockets_2d() { translate([-x_in0, 0]) for (m = columns()) translate(m) circle(d = hardware_col_pocket_d); }

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
matrix_board_z = z_oak_top_bot - boards_matrix_t;
matrix_top_z = z_oak_top_bot + boards_matrix_led_h;              // LED tops
// The key plate ends before the Matrix, so past it the lid is the oak alone.
plate_x1 = matrix_xy[0] - boards_matrix_board / 2 - 1;
// The USB-C extension's plug, in the Matrix's mouth or tail edge.
usb_plug_x0 = openings_matrix_usb_to_tail ? matrix_xy[0] + boards_matrix_board / 2 : matrix_xy[0] - boards_matrix_board / 2 - openings_usb_plug_l;
// The tail equipment starts at the first of that plug and J-UMB, behind the
// etherCON's adapter.
tail_equip_x = min(usb_plug_x0, ua_x0 - boards_umb_joint_d);

// U-bolt in the inter-hand gap on the bottom face (ADR 0009); legs ACROSS the
// body, since the shortened gap has no room along it beside the left thumb line.
// Its legs pass the oak bottom and the bottom plate, which spreads its pull
// over the oak (ADR 0025).
ubolt_c = [(x_gap0 + x_rh0) / 2, W / 2];
function ubolt_legs() = [for (s = [-1, 1]) ubolt_c + [0, s * hardware_ubolt_span / 2]];
ubolt_hole_d = hardware_ubolt_rod_d + hardware_ubolt_hole_clear;   // the legs' clearance hole in the oak and the bottom plate

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
            translate([0, 0, -EPS]) linear_extrude(col_pocket_depth + EPS) oak_pockets_2d();
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
    } }
    // Each side: one sheet, bottom edge in the bottom groove, top edge in the top.
    // Exploded, the sides move out and down so the boards between them show.
    for (i = [0, 1])
        P(C_ACRYLIC, true, str("side ", i == 0 ? "left" : "right")) translate([x_in0, side_y[i] + stack_side_t + (i == 0 ? -1 : 1) * explode * 1.5, z_side0 - explode * 0.6]) rotate([90, 0, 0])
            linear_extrude(stack_side_t) side_2d();
}

// render(): the preview renderer (OpenCSG) drops the cut-outs of an
// intersection() it has to draw as CSG, so without it the tail face showed
// neither the USB-C slot nor the flange screw holes.
module caps() {
    P(C_OAK_DARK, true, "mouth cap") translate([ends_mouth_cap_t - explode / 3, 0, 0]) rotate([90, 0, 90]) mirror([0, 0, 1])
        render() intersection() { linear_extrude(ends_mouth_cap_t) mouth_cap_2d(); sanded_cap(ends_mouth_cap_t); }
    P(C_OAK_DARK, true, "tail cap") translate([x_in1 + explode / 3, 0, 0]) rotate([90, 0, 90])
        render() difference() {
            intersection() { linear_extrude(ends_tail_cap_t) tail_cap_2d(); sanded_cap(ends_tail_cap_t); }
            translate([usb_c[0] - usb_om[0] / 2, usb_c[1] - usb_om[1] / 2, openings_usb_panel_t]) cube([usb_om[0], usb_om[1], usb_pocket_d + EPS]);
            if (ec_recess_d > 0) translate([0, 0, ec_panel_t]) linear_extrude(ec_recess_d + EPS) ec_recess_2d();
        }
}

module switch_at(xy, rot, top, name, spare = false) {
    // Seat (collar underside) on the plate's key face.
    tf = top ? [xy[0], xy[1], z_plate_top + explode / 2] : [xy[0], xy[1], z_floor - explode];
    // P() OUTSIDE the placement: a section cuts in world coordinates, and a
    // P() inside translate() cut every switch in its own frame instead.
    // Trimmed above the collar to Gateron's drawn cover (switch.cover_*): the
    // third-party mesh draws its latches up there, where the vendor has none.
    P(C_SWITCH, false, str("switch ", name)) translate(tf) rotate([top ? 0 : 180, 0, rot]) intersection() {
        import("vendor/ks33.stl");
        union() {
            translate([-10, -10, -10]) cube([20, 20, 10 + switch_collar_t]);
            hull() {
                translate([-switch_cover_w / 2, -switch_cover_w / 2, 0]) cube([switch_cover_w, switch_cover_w, switch_cover_straight_h]);
                translate([-switch_cover_top_w / 2, -switch_cover_top_w / 2, 0]) cube([switch_cover_top_w, switch_cover_top_w, switch_housing_top_above_seat]);
            }
            translate([-switch_cover_top_w / 2, -switch_cover_top_w / 2, 0]) cube([switch_cover_top_w, switch_cover_top_w, 20]);
        }
    }
    // THE CAP (MT165-MX, ADR 0002): a hollow shell, and the MX cross socket the
    // stem enters, as separate solids so the clash check lets only the SOCKET meet
    // the switch; the shell must clear it at rest and all the way down.
    P(spare ? C_SPARE : C_CAP, false, str("cap ", name)) translate(tf) rotate([top ? 0 : 180, 0, rot]) cap_shell(0);
    P(spare ? C_SPARE : C_CAP, false, str("cap socket ", name)) translate(tf) rotate([top ? 0 : 180, 0, rot]) cap_socket(0);
    // The cap's TRAVEL: the space its shell sweeps when pressed (it includes where
    // the cap sits at rest: clash-allow.yaml says why). Only for the clash check - drawn nowhere else - so a skirt that would
    // land on the switch, the plate or the oak at the bottom of its stroke is caught.
    if (only == str("travel ", name) || list_solids)
        P(C_CAP, false, str("travel ", name)) translate(tf) rotate([top ? 0 : 180, 0, rot])
            difference() {
                union() {
                    cap_shell(switch_total_travel);
                    translate([0, 0, cap_sk - switch_total_travel]) linear_extrude(switch_total_travel)
                        difference() { square(switch_keycap, center = true); square(switch_keycap - 2 * switch_keycap_wall, center = true); }
                }
                // The stem and actuator move WITH the cap: measured off the mesh,
                // 11.0 x 5.6 above the housing top. Leaving it out of the sweep keeps
                // the pressed cap from meeting the switch's (static) stem.
                translate([0, 0, -1]) linear_extrude(switch_keycap_top_above_seat + 2) square([11.4, 6.0], center = true);
            }
}
// The cap in the switch's frame (seat at z = 0), pressed by dz: its skirt's
// bottom is cap_sk above the seat at rest.
cap_sk = switch_keycap_top_above_seat - switch_keycap_h;
cap_ceiling = switch_keycap_top_above_seat - switch_keycap_top_t;     // the inside of its top
function cap_w_at(z) = switch_keycap + (switch_keycap_top_w - switch_keycap) * z / switch_keycap_h;   // outer, z above the skirt
module cap_shell(dz) {
    hi = switch_keycap_h - switch_keycap_top_t;
    translate([0, 0, cap_sk - dz]) difference() {
        linear_extrude(switch_keycap_h, scale = switch_keycap_top_w / switch_keycap) square(switch_keycap, center = true);
        translate([0, 0, -EPS]) linear_extrude(hi + EPS, scale = (cap_w_at(hi) - 2 * switch_keycap_wall) / (switch_keycap - 2 * switch_keycap_wall))
            square(switch_keycap - 2 * switch_keycap_wall, center = true);
    }
}
module cap_socket(dz) {
    translate([0, 0, switch_keycap_top_above_seat - switch_keycap_boss_below_top - dz]) cylinder(d = switch_keycap_socket_d, h = switch_keycap_boss_below_top - switch_keycap_top_t + EPS);
}

module keys_3d() {
    for (k = keys) switch_at(key_xy(k), key_rot(k), key_face(k) == "top", k[0]);
    for (i = [0 : 1 : len(spare_xy) - 1]) switch_at(spare_xy[i], 0, false, str("spare ", i + 1), true);
}

module bottom_plate_3d() {
    lam(z_floor - explode * 0.5, plate_thickness, C_ALU, false, "bottom plate")
        translate([plate_x0, plate_y0]) plate_bottom_2d();
}

// A KEY BOARD IS A RECTANGLE ACROSS THE CAVITY (owner, 2026-09-27, ADR 0020
// amended: "increase that size a little bit so that we could fit the
// standoffs... anchor it in each corner"): from the side walls less the board
// clearance, and along the body past its outermost cutouts by kb_end_margin at
// the mouth end and kb_tail_margin at the tail. A column stands at each
// corner (ADR 0025).
// Corners rounded by a drawing convention. The PCB's Edge.Cuts come from this.
kb_corner_r = 1;        // drawing convention: board corner radius
function kb_rect(cl) = let(x = xs(cluster_keys(cl)))
    [min(x) - plate_cutout / 2 - cluster_margin, u_y0 + boards_board_clear,
     max(x) + plate_cutout / 2 + tail_margin, W - u_y0 - boards_board_clear];
module key_board_2d(cl) {
    r = kb_rect(cl);
    offset(r = kb_corner_r) offset(delta = -kb_corner_r) translate([r[0], r[1]]) square([r[2] - r[0], r[3] - r[1]]);
}

// THE COLUMNS (owner, 2026-09-29; ADR 0025): at each corner of each key board
// one column ties the key plate to the bottom plate through both boards. From
// the bottom: a PEM FHL-M2.5 stud pressed into the bottom plate, head flush in
// its underside; a spacer; the main board; an M2.5 female-female hex standoff
// threaded onto the stud, clamping the main board, as long as the gap up to the
// key board; the key board; a spacer; the key plate; an M2.5 low-head screw down
// through the plate into the standoff, its head in a pocket in the oak top.
// The spacers set both boards' depths; the standoff's length is the gap. The
// DRC below checks the thread at both ends of the standoff, the studs' edge
// distance in the bottom plate and the screws' heads on the key plate.
function rect_gap(p, c, sz, r) = let(d = [cos(-r) * (p[0] - c[0]) - sin(-r) * (p[1] - c[1]), sin(-r) * (p[0] - c[0]) + cos(-r) * (p[1] - c[1])],
                                   e = [max(abs(d[0]) - sz[0] / 2, 0), max(abs(d[1]) - sz[1] / 2, 0)]) norm(e);
function cutout_gap(p) = min([for (k = top_keys) rect_gap(p, key_xy(k), [plate_cutout, plate_cutout], key_rot(k))]);
// from a point to the nearest cap hole or slot in the wood top (a slot is the
// union of its keys' holes; the 1.5 mm closing between them is ignored, which
// errs toward a larger gap only where two holes' corners nearly meet)
function cap_gap(p) = min([for (k = top_keys) rect_gap(p, key_xy(k), [1, 1] * (switch_keycap + 2 * stack_cap_clear), key_rot(k))]);
function kb_mounts(cl) = let(r = kb_rect(cl), e = hardware_kb_mount_inset)
    [[r[0] + e, r[1] + e], [r[0] + e, r[3] - e], [r[2] - e, r[1] + e], [r[2] - e, r[3] - e]];
kb_gap = hardware_kb_spacer_l;                               // plate underside to board top: what the mount stacks there
kb_top = z_plate_top - switch_pcb_below_seat;                 // the key boards' top face
function columns() = [for (cl = ["left_hand", "right_hand"], m = kb_mounts(cl)) m];
col_standoff_e = hardware_col_standoff_af / cos(30);          // the standoff's hex across its corners
col_keep_r = col_standoff_e / 2 + hardware_kb_mount_float;    // what a board keeps clear round a column's hex, off its axis
// Where the ribbon runs under a key board, from its connector's mouth to the
// board's far edge: no parts there - the model's parts envelope leaves it out.
// The key board's chain header with its plug, as a rectangle [x0, y0, x1, y1]:
// no other part there; its pin tails stop short of the plate (drc.echo
// "J-CHAIN pin tails clear of the key plate").
function kb_chain_rect(cl) = let(sp = chain_span(chain_x(cl), chain_dir(cl)))
    [sp[0], chain_y - boards_chain_hdr_l / 2, sp[1], chain_y + boards_chain_hdr_l / 2];
// Where the key board's chain header's pin tails come up through the board:
// outside every switch body (chain_clear), and short of the plate (drc.echo
// "J-CHAIN pin tails clear of the key plate").
function chain_tail_rect_at(x, d) = let(a = x - d * boards_chain_hdr_pin_back, b = x - d * (boards_chain_hdr_pin_back - 1.27))
    [min(a, b) - 1, chain_y - 6.35 / 2 - 1, max(a, b) + 1, chain_y + 6.35 / 2 + 1];
function chain_tail_rect(cl) = chain_tail_rect_at(chain_x(cl), chain_dir(cl));

module cluster_boards() {
    for (cl = ["left_hand", "right_hand"]) {
        P(C_PCB, false, str("board ", cl)) translate([0, 0, kb_top - boards_key_board_t + explode * 0.25])
            linear_extrude(boards_key_board_t) difference() {
                key_board_2d(cl);
                for (m = kb_mounts(cl)) translate(m) circle(d = hardware_kb_board_hole);
            }
        // each P() places its own solid, so a section cut sees it where it is.
        // The top of each column: the spacer under the key plate and the screw
        // down through it; the standoff and the stud are the main board's.
        for (i = [0 : len(kb_mounts(cl)) - 1]) let(m = kb_mounts(cl)[i], n = str(cl, " ", i + 1)) {
            P(C_STEEL, false, str("key-board spacer ", n)) translate([m[0], m[1], z_plate_bot - hardware_kb_spacer_l + explode * 0.2])
                difference() { cylinder(d = hardware_kb_spacer_od, h = hardware_kb_spacer_l); translate([0, 0, -1]) cylinder(d = hardware_stud_attached_hole, h = hardware_kb_spacer_l + 2); }
            // the screw: its head on the key plate's top face, in the oak top's
            // pocket; its shank down through the plate, spacer and board into the standoff
            P(C_STEEL, false, str("column screw ", n)) translate([m[0], m[1], explode * 0.8]) {
                translate([0, 0, z_plate_top]) cylinder(d = hardware_col_screw_head_d, h = hardware_col_screw_head_h);
                translate([0, 0, z_plate_top - hardware_col_screw_l]) cylinder(d = 2.5, h = hardware_col_screw_l + EPS);
            }
        }
    }
}

// WHAT A KEY BOARD'S PCB IS PLACED FROM (tools/pcb.py). Body coordinates, mm:
// x along the body from the mouth, y across it, seen from above. The PCB tool
// maps these onto the board, so the switches land in the plate's cutouts and
// the ribbon connector where the ribbon's C needs it.
module pcb_geometry() {
    for (cl = ["left_hand", "right_hand"]) {
        for (k = cluster_keys(cl)) echo("PCB", cl, "switch", k[0], key_xy(k)[0], key_xy(k)[1], key_rot(k));
        echo("PCB", cl, "chain", "J-CHAIN", chain_x(cl), chain_y, chain_dir(cl), boards_chain_hdr_l, boards_chain_hdr_pin_back);
        // the hole, then what bears on the board's underside (the column's
        // standoff, across its corners) and on its top copper (the spacer),
        // each grown by how far it can sit off the column's axis
        for (m = kb_mounts(cl)) echo("PCB", cl, "standoff", "M2.5", m[0], m[1], hardware_kb_board_hole,
                                     col_standoff_e + 2 * hardware_kb_mount_float,
                                     hardware_kb_spacer_od + 2 * hardware_kb_mount_float);
        echo("PCB", cl, "board", "thickness", boards_key_board_t, "smt_height_max", boards_cluster_smt_h,
             "side", "switches on top, parts and ribbon connector underneath");
    }
    // THE MAIN BOARD (ADR 0017, 0021, 0022), cluster "main". Parts face UP; the
    // thumb switches come in from BELOW (their seat is on the bottom plate),
    // so their footprints go on the board's underside. Body coordinates, mm;
    // its outline is export/main-board.dxf (the U-bolt holes, the sensor slot
    // and the mounts' holes are in it; there are no edge notches).
    for (k = bottom_keys) echo("PCB", "main", "switch", k[0], key_xy(k)[0], key_xy(k)[1], key_rot(k));
    // Each ribbon's header, standing on the top face, its mouth facing along
    // the body: mouth x, centre y, which way the mouth faces (+1 the tail),
    // length, mouth to far pin row - as a key board's "chain".
    for (cl = chain_ribbon_cls) echo("PCB", "main", "chain", str("J-CHAIN-", cl == "left_hand" ? "LH" : "RH"),
                                     chain_x(cl), chain_y, chain_dir(cl), boards_chain_hdr_l, boards_chain_hdr_pin_back);
    // The Matrix's header: its insulator's extent along x, centre y, length
    // across, and the mouth's direction (+1 the tail) - the ribbon comes in
    // over the tongue.
    echo("PCB", "main", "connector", "J-MCU", jm_x0, jm_x1, jm_y, jm_sz[1], 1);
    // J-UMB: the right-angle header whose tails go down through the
    // tongue and whose posts go through the adapter; its insulator's extent along x (it stands against the
    // adapter's rear face), centre y, pin count, pitch, and its row's
    // height above the top face, where it meets the adapter.
    echo("PCB", "main", "connector", "J-UMB", ua_x0 - boards_umb_joint_d, ua_x0, ec_c[0], 8, 2.54, boards_umb_joint_row_h);
    // The breath sensor: its centre, the ports toward +x (the tail), its
    // body and lead span; the slot in front of its lower port is in the DXF.
    echo("PCB", "main", "part", "U-BREATH", sensor_c[0], sensor_c[1], 0, boards_sensor_body, boards_sensor_leads);
    // The regulator block's envelope: centre, along x, across y, height.
    echo("PCB", "main", "part", "REGULATOR-BLOCK", tall_c[0][0], tall_c[0][1], 0, tall_sz[0], tall_sz[1], boards_tall_h);
    // The LED strip lying on the top face: start x, band's lower y, length, width.
    echo("PCB", "main", "strip", "LED", strip_x0, strip_y, strip_l, lighting_strip_w);
    // Each mount (ADR 0022, ADR 0025), all on the bottom plate: centre, hole,
    // what bears on the top face (a column's standoff or an end mount's nut,
    // across its corners, with float), what bears on the underside (the
    // spacer, with float), and which kind.
    for (i = [0 : len(cb_standoffs) - 1]) let(c = cb_standoffs[i])
        echo("PCB", "main", "standoff", "M2.5", c[0], c[1], hardware_kb_board_hole,
             (i < n_cols ? col_standoff_e : hardware_mb_nut_e) + 2 * hardware_kb_mount_float,
             hardware_kb_spacer_od + 2 * hardware_kb_mount_float, i < n_cols ? "column" : "end");
    // Each U-bolt leg (ADR 0022 point 7, ADR 0025): centre, the board's hole,
    // and what bears on the top face (the washer and the nut, across its
    // corners) and the underside (the spacer), which the board keeps copper
    // and parts off.
    for (u = ubolt_legs()) echo("PCB", "main", "ubolt", "M3", u[0], u[1], 2 * ubolt_board_hole_r,
                                max(hardware_ubolt_nut_af / cos(30), hardware_ubolt_washer_od), hardware_ubolt_spacer_od);
    // How tall parts may stand: under each key board, and where none is
    // overhead; and nothing under the chain headers' plugs and hairpins, or
    // under the Matrix ribbon's level run into J-MCU.
    for (cl = ["left_hand", "right_hand"]) let(r = kb_rect(cl))
        echo("PCB", "main", "keepout", str("under key board ", cl), r[0], r[1], r[2], r[3], cb_room);
    echo("PCB", "main", "keepout", "elsewhere", cb_x[0], cb_y[0], ua_x0, cb_y[1], gap_room);
    for (cl = chain_ribbon_cls) let(sp = chain_span(chain_x(cl), chain_dir(cl)))
        echo("PCB", "main", "keepout", str("ribbon ", cl), sp[0], chain_y - boards_chain_hdr_l / 2, sp[1], chain_y + boards_chain_hdr_l / 2, 0);
    echo("PCB", "main", "keepout", "Matrix ribbon", jm_x1, jm_y - routing_mcu_ribbon_w / 2, mcu_x, jm_y + routing_mcu_ribbon_w / 2,
         jm_z + e_mb - routing_mcu_ribbon_t / 2 - cb_top);
    echo("PCB", "main", "board", "thickness", switch_pcb_t, "smt_height_max", boards_smt_h,
         "side", "parts on top; the thumb switches from below, their footprints on the underside");
}

module tail_equipment() {
    // The Matrix, face up under the top window.
    P([0.10, 0.10, 0.12], false, "Matrix board") translate([matrix_xy[0] - boards_matrix_board / 2, matrix_xy[1] - boards_matrix_board / 2, matrix_board_z])
        cube([boards_matrix_board, boards_matrix_board, boards_matrix_t]);
    P(C_LED, false, "Matrix LEDs") translate([matrix_xy[0] - boards_matrix_emitters / 2, matrix_xy[1] - boards_matrix_emitters / 2, matrix_board_z + boards_matrix_t])
        cube([boards_matrix_emitters, boards_matrix_emitters, boards_matrix_led_h]);
    // The Matrix's ribbon where it leaves the two pad rows, below the board;
    // it runs on to J-MCU (drawn with the tail wiring).
    for (i = [0, 1]) P([0.15, 0.15, 0.15], false, str("Matrix harness ", i + 1))
        translate([matrix_xy[0] - 12.7, matrix_xy[1] + (i == 0 ? -1 : 1) * 11.43 - 1.27, matrix_board_z - boards_matrix_harness_h])
            cube([25.4, 2.54, boards_matrix_harness_h]);   // rows 22.86 apart [ds]
    P(C_FROSTED, false, "matrix window") translate([0, 0, T - openings_matrix_acrylic_t + explode]) linear_extrude(openings_matrix_acrylic_t) matrix_window_2d();
    // The etherCON, an NE8FAV (ADR 0021): flange and body behind the tail
    // cap, the nose into the cap's bore, the PUSH tab in front of the flange
    // in the cap's recess. Soldered to the umbilical adapter behind it.
    P(C_CONN, false, "etherCON") union() {
        translate([ec_pcb_x1, ec_c[0] - ec_fl[0] / 2, ec_c[1] - ec_fl[1] / 2]) cube([ethercon_pcb_setback, ec_fl[0], ec_fl[1]]);
        translate([ec_panel_x - EPS, ec_c[0], ec_c[1]]) rotate([0, 90, 0]) cylinder(d = ethercon_bore_d - 0.2, h = ethercon_nose_l + EPS);
        let(t = ec_pt([0, (ethercon_fl_top() + ethercon_tab_top) / 2]), tsz = ethercon_rotated ? [ethercon_tab_top - ethercon_fl_top(), ethercon_tab_w] : [ethercon_tab_w, ethercon_tab_top - ethercon_fl_top()])
            translate([ec_panel_x + ethercon_tab_front - 3, t[0] - tsz[0] / 2, t[1] - tsz[1] / 2]) cube([3, tsz[0], tsz[1]]);
    }
    // The umbilical adapter: the flange's outline, parallel to the tail cap.
    P(C_PCB, false, "umbilical adapter") translate([ua_x0, ec_c[0] - ec_fl[0] / 2, ec_c[1] - ec_fl[1] / 2]) cube([boards_umb_adapter_t, ec_fl[0], ec_fl[1]]);
    // The USB-C extension's plug in the Matrix's tail edge, under the board.
    P([0.35, 0.35, 0.38], false, "USB-C plug") translate([usb_plug_x0, matrix_xy[1] - openings_usb_slot_w / 2, matrix_board_z - openings_usb_slot_h])
        cube([openings_usb_plug_l, openings_usb_slot_w, openings_usb_slot_h]);
    // The USB-C extension: receptacle body behind the tail cap, and a cable
    // run to the Matrix board's edge (drawn straight; it is a flexible lead).
    // Its nose passes the panel under the overmould pocket, face level with
    // the pocket floor; an earless body, clamped from behind (openings.usb_mount).
    P(C_CONN, false, "USB-C receptacle") translate([x_in1 - openings_usb_ext_depth, usb_c[0] - usb_sz[0] / 2, usb_c[1] - usb_sz[1] / 2])
        cube([openings_usb_ext_depth + openings_usb_panel_t, usb_sz[0], usb_sz[1]]);
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
// since ADR 0017 - the key boards are on 1.27 mm IDC ribbons and the Matrix
// on a ribbon, both drawn below. The lane is a model choice (config/body.yaml
// routing): the clash check reports what is in it.
// Inboard of the main board's mouth-end mounts, whose studs and nuts stand
// up into the cavity beside the sides: the mount's edge band, its keep-out
// and a board clearance.
function lane_y(side, d) = let(e = (cb_y[0] - u_y0) + end_mount_in + mb_keep_d / 2 + boards_board_clear + d / 2)
    side == "left" ? u_y0 + e : W - u_y0 - e;
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
top_z = z_plate_top - switch_pcb_below_seat - boards_key_board_t;     // top cluster boards' underside
thumb_z = z_floor + switch_thumb_pcb_below_seat + switch_pcb_t;       // the main board's top face, where the thumb switches solder
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
function kspan(cl) = [kb_rect(cl)[0], kb_rect(cl)[2]];   // the key board itself
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
// Across: in from the board's edge by the wider of the lead tips and the land
// pattern's pads, + 0.5 - the pads, not the leads, must keep off the edge.
sensor_c = [cb_x[0] + 0.5 + boards_sensor_body / 2, cb_y[tube_side < 0 ? 1 : 0] + tube_side * (max(boards_sensor_leads, boards_sensor_land_w) / 2 + 0.5)];
sensor_face_x = sensor_c[0] + boards_sensor_body / 2;
p2_y = sensor_c[1] + boards_sensor_port_offset;
// The slot in the main board in front of the lower port: 1 clear of the barb all round.
port_slot_sz = [boards_sensor_port_l + 2, boards_sensor_port_d + 2];
port_slot_c = [sensor_face_x + port_slot_sz[0] / 2, p2_y];
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
// ADR 0017). THROUGH-HOLE IDC, STACKED (owner, 2026-09-27, ADR 0017 amended):
// on each board a right-angle 1.27 mm shrouded header, the key board's
// hanging from its underside directly over the main board's, both mouths
// facing the same way along the body, in the far band beside the LED strip.
// The ribbon runs out of one plug, folds back on itself and into the other:
// a flat hairpin lying along the body between the two plugs' heights, so it
// never stands across the strip's light. Its length is what the lid needs
// laid off to the side with the ribbon still plugged in (routing.chain_service);
// closed, that length is the hairpin's legs.
far_s = tube_side < 0 ? 1 : -1;                  // the far side, away from the tube
// Exploded, the main board rises by e_mb and the key boards by e_kb; the
// cables stretch to follow, so they stay connected in the picture.
e_mb = explode * 0.1;
e_kb = explode * 0.25;
chain_ribbon_cls = ["left_hand", "right_hand"];
ribbon_cls = chain_ribbon_cls;
// Across the body: the header's length along y, in from the far edge of both boards.
chain_y = W / 2 + far_s * (W / 2 - u_y0 - boards_board_clear - 0.5 - boards_chain_hdr_l / 2);
chain_zk = top_z - boards_chain_hdr_mouth_z;     // the key board's plug, its centre
chain_zm = cb_top + boards_chain_hdr_mouth_z;    // the main board's
// WHICH WAY THE CABLE LEAVES EACH SOCKET. On an FFSD cable the first socket's
// key is on the side its cable leaves by, and a -RN2 cable reverses the
// second socket's notch, so on this cable BOTH sockets' keys are on their
// cable sides (datasheets/connectors/SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf,
// sheet 1 fig 1 and sheet 2 fig 3). The main board's header stands upright,
// its key slot in the wall away from the board, so its cable leaves UPWARD;
// the key board's is the same part upside down, so its cable leaves
// DOWNWARD. The two face each other across the gap between the plugs, and
// the ribbon's spare length folds into a flat hairpin in that gap, clear of
// both boards' parts: each end turns out along the body at routing.chain_bend_r,
// the two legs run the same way, and the fold joins them. (The pin map this
// cable gives, key-board pin = 13 - main-board pin, is key-chain-loom.md's.)
chain_z_low = chain_zm + boards_chain_plug_t / 2 + routing_chain_bend_r + routing_chain_ribbon_t / 2;
chain_z_up = chain_zk - boards_chain_plug_t / 2 - routing_chain_bend_r - routing_chain_ribbon_t / 2;
chain_r = (chain_z_up - chain_z_low) / 2;        // the fold's radius
function chain_dir(cl) = routing_chain_fold[search([cl], chain_ribbon_cls)[0]];
// A header's footprint, from its mouth at x: [x0, x1] along the body - pins,
// body, and the plug standing out of the mouth.
function chain_span(x, d) = d > 0 ? [x - boards_chain_hdr_pin_back - 0.5, x + boards_chain_plug_proud]
                                  : [x - boards_chain_plug_proud, x + boards_chain_hdr_pin_back + 0.5];
// Clear of every switch's pole and pins on both boards (their stubs stand
// through the board, both faces), and of the key board's switch bodies on
// top, where the key header's pin tails come through.
// A switch's stubs: its centre pole and its two pins, from the vendor
// footprint (hardware/lib/woody.pretty/SW_Gateron_KS33_1u.kicad_mod), seen
// from above; a thumb switch hangs the other way up, so both mirror images.
ks33_pins = [[-4.4, -4.7], [2.6, -5.75]];
function key_stubs(k) = let(c = key_xy(k), m = key_face(k) == "top" ? [1] : [1, -1])
    concat([[c, ks33_stub]], [for (s = m, p = ks33_pins) [c + [p[0], s * p[1]], 1.3]]);
function chain_clear(x, cl) = let(d = chain_dir(cl), sp = chain_span(x, d), c = [(sp[0] + sp[1]) / 2, chain_y], sz = [sp[1] - sp[0], boards_chain_hdr_l],
                                  tl = chain_tail_rect_at(x, d))
    min([for (k = concat(cluster_keys(cl), bottom_keys), st = key_stubs(k)) rect_gap(st[0], c, sz, 0) - st[1] - 0.3]) >= 0
    // the key header's pin tails, on the key board's top, outside every switch body
    && min([for (k = cluster_keys(cl)) max(abs(key_xy(k)[0] - (tl[0] + tl[2]) / 2) - (tl[2] - tl[0]) / 2,
                                          abs(key_xy(k)[1] - (tl[1] + tl[3]) / 2) - (tl[3] - tl[1]) / 2) - plate_cutout / 2]) >= 0.5
    // the main board's tall parts, and the hairpin clear of them too
    && (let(h = chain_hairpin_at(x, d), x0 = min(h[0], sp[0]), x1 = max(h[1], sp[1]))
       min([for (t = tall_c) max(abs(t[0] - (x0 + x1) / 2) - ((x1 - x0) + tall_sz[0]) / 2, abs(t[1] - chain_y) - (boards_chain_hdr_l + tall_sz[1]) / 2)]) >= boards_board_clear)
    // and the header, its plug and the hairpin clear of the columns, which
    // stand through the whole gap between the boards
    && chain_col_gap(chain_hairpin_at(x, d)) >= col_keep_r + 0.5
    && chain_col_gap(sp, boards_chain_hdr_l) >= col_keep_r + 0.5;
function chain_col_gap(h, w = routing_chain_ribbon_w) = min([for (m = columns()) rect_gap(m, [(h[0] + h[1]) / 2, chain_y], [h[1] - h[0], w], 0)]);
// Along the key board: the clear mouth position nearest its middle.
function chain_x(cl) = let(t = [for (k = cluster_keys(cl)) key_xy(k)[0]], m = (min(t) + max(t)) / 2,
                           ok = [for (x = [min(t) : 0.5 : max(t)]) if (chain_clear(x, cl)) x], d = [for (x = ok) abs(x - m)])
    len(ok) > 0 ? ok[search(min(d), d)[0]] : undef;
function kb_chain(cl) = [chain_x(cl), chain_y];
function mb_chain(cl) = [chain_x(cl), chain_y];
// THE SERVICE LENGTH (routing.chain_service, ADR 0025). The key plate, with
// both key boards on it, held straight up off its columns by
// routing.chain_raise while a hand plugs or unplugs the main board's socket:
// the ribbon runs straight from the main board's plug up to the key board's,
// plus routing.chain_slack for the turns and the hand.
chain_len = (chain_zk - chain_zm - boards_chain_plug_t) + routing_chain_raise + routing_chain_slack;
// WHAT TO ORDER. An FFSD's length is overall, over both sockets, in inches, to
// +/-0.125 in (the print, sheet 1 notes 8 and 11): the ribbon between the
// sockets plus a socket's thickness at each end, and the tolerance added so
// the shortest cable made is still long enough.
chain_order_in = ceil((chain_len + 2 * boards_chain_plug_t + 0.125 * 25.4) / 25.4 * 100) / 100;
// Closed: each end's turn out along the body, two legs and the fold.
chain_drops = 2 * (PI / 2 * routing_chain_bend_r);
chain_leg = (chain_len - chain_drops - PI * chain_r) / 2;
function chain_exit(cl) = chain_x(cl) + chain_dir(cl) * boards_chain_plug_proud;
// The hairpin's extent along the body, for the parts it must clear.
function chain_hairpin_at(x, d) = let(a = x + d * boards_chain_plug_proud, b = a + d * (chain_leg + chain_r + routing_chain_ribbon_t)) [min(a, b), max(a, b)];
function chain_hairpin(cl) = chain_hairpin_at(chain_x(cl), chain_dir(cl));
function chain_path(cl) = let(xe = chain_exit(cl), dr = chain_dir(cl), zl = chain_z_low + e_mb, zu = chain_z_up + e_kb,
                              r = (zu - zl) / 2, zc = (zu + zl) / 2, xf = xe + dr * chain_leg)
    concat([[xe, chain_zm + e_mb + boards_chain_plug_t / 2], [xe + dr * routing_chain_bend_r, zl]],
           [for (a = [-90 : 10 : 90]) [xf + dr * r * cos(a), zc + r * sin(a)]],
           [[xe + dr * routing_chain_bend_r, zu], [xe, chain_zk + e_kb - boards_chain_plug_t / 2]]);
function path_len(p) = sum([for (i = [0 : len(p) - 2]) norm(p[i + 1] - p[i])]);
module chain_header(cl, z0, up) {
    x = chain_x(cl); d = chain_dir(cl);
    // the shroud, its mouth at x facing d; hanging (up = false) or standing
    translate([d > 0 ? x - boards_chain_hdr_d : x, chain_y - boards_chain_hdr_l / 2, up ? z0 : z0 - boards_chain_hdr_h])
        cube([boards_chain_hdr_d, boards_chain_hdr_l, boards_chain_hdr_h]);
}
module chain_plug(cl, zc) {
    x = chain_x(cl); d = chain_dir(cl);
    // the socket, its back standing chain_plug_proud out of the mouth
    translate([d > 0 ? x + boards_chain_plug_proud - boards_chain_plug_h : x - boards_chain_plug_proud, chain_y - boards_chain_plug_l / 2, zc - boards_chain_plug_t / 2])
        cube([boards_chain_plug_h, boards_chain_plug_l, boards_chain_plug_t]);
}
module ribbons_3d() {
    for (cl = chain_ribbon_cls) let(p = chain_path(cl)) {
        P([0.10, 0.10, 0.10], false, str("J-CHAIN ", cl, " key board")) chain_header(cl, top_z + e_kb, false);
        P([0.10, 0.10, 0.10], false, str("J-CHAIN ", cl, " main board")) chain_header(cl, cb_top + e_mb, true);
        P([0.25, 0.25, 0.30], false, str("IDC plug ", cl, " key board")) chain_plug(cl, chain_zk + e_kb);
        P([0.25, 0.25, 0.30], false, str("IDC plug ", cl, " main board")) chain_plug(cl, chain_zm + e_mb);
        // Swept as a strip of the ribbon's width across the body, bending in (x, z).
        P([0.72, 0.72, 0.74], false, str("ribbon ", cl)) for (i = [0 : len(p) - 2])
            hull() for (q = [p[i], p[i + 1]]) translate([q[0], chain_y, q[1]]) cube([routing_chain_ribbon_t, routing_chain_ribbon_w, routing_chain_ribbon_t], center = true);
    }
}

// THE MATRIX AND THE UMBILICAL (owner, 2026-09-26: "what about matrix led
// esp32 and ethercon wire connections?"), both onto the main board's tail
// end. The Matrix: a flat 24-way ribbon soldered to its pads (ADR 0018), down
// just inside its mouth edge, one bend, and level beside the patch plug
// into J-MCU - the Matrix is on the lid,
// so it unplugs there like the key boards. The umbilical (ADR 0021): no
// cable inside the body. The etherCON is soldered to its adapter, and J-UMB,
// a right-angle header on a tongue of the main board, is soldered to both.
module tail_wiring_3d() {
    P([0.85, 0.85, 0.80], false, "J-MCU") translate([jm_x0, jm_y - jm_sz[1] / 2, cb_top + e_mb]) cube([jm_sz[0], jm_sz[1], boards_mcu_conn_h]);
    P([0.10, 0.10, 0.10], false, "J-UMB") translate([ua_x0 - boards_umb_joint_d, ec_c[0] - ju_l / 2, cb_top + e_mb]) cube([boards_umb_joint_d, ju_l, boards_umb_joint_h]);
    P([0.30, 0.30, 0.80], false, "Matrix ribbon") for (i = [0 : len(mcu_path) - 2])
        hull() for (q = [mcu_path[i], mcu_path[i + 1]]) translate([q[0], jm_y, q[1]]) cube([routing_mcu_ribbon_t, routing_mcu_ribbon_w, routing_mcu_ribbon_t], center = true);
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
// THE MAIN BOARD IS IN THE U-BOLT'S CLAMP (owner, 2026-09-29; ADR 0025): up each
// leg the oak, the bottom plate, a spacer, the board, a washer, the nut. The
// board has a clearance hole for the rod; the nut and its washer stand on the
// top face and keep the board's parts clearance round the nut's corners.
ubolt_board_hole_r = (hardware_ubolt_rod_d + hardware_ubolt_board_hole_clear) / 2;
ubolt_nut_z = cb_top + hardware_ubolt_washer_t;   // the nut's underside, on its washer on the board
ubolt_keep_r = max(hardware_ubolt_nut_af / cos(30), hardware_ubolt_washer_od) / 2 + boards_board_clear;
module cb_2d() {
    difference() {
        union() {
            translate([cb_x[0], cb_y[0]]) square([cb_x[1] - cb_x[0], cb_y[1] - cb_y[0]]);
            // THE TONGUE (ADR 0021): on to the etherCON's adapter, as wide as
            // it, carrying J-UMB against the adapter's rear face.
            translate([cb_x[1] - EPS, tongue_y[0]]) square([ua_x0 - cb_x[1] + EPS, tongue_y[1] - tongue_y[0]]);
        }
        // The slot in front of the sensor's lower port.
        translate(port_slot_c - port_slot_sz / 2 - [EPS, 0]) square(port_slot_sz);
        // A hole for each U-bolt leg; no edge notches (ADR 0025).
        for (u = ubolt_legs()) translate(u) circle(r = ubolt_board_hole_r);
        // the mounts' holes (ADR 0022): the board locates on its studs
        for (c = cb_standoffs) translate(c) circle(d = hardware_kb_board_hole);
    }
}
// J-MCU: on the tube side of the regulator block, at the board's tail edge.
jm_sz = [boards_mcu_conn_w, boards_mcu_conn_l];
// Across: under the Matrix's middle, so the ribbon comes straight down.
jm_y = matrix_xy[1];
jm_z = cb_top + boards_mcu_conn_h / 2;
mcu_r = 4;   // drawing convention: the ribbon's bends
// Down just inside the Matrix's mouth edge (its USB-C plug leaves that
// edge), one bend, and level into J-MCU.
mcu_x = matrix_xy[0] - boards_matrix_board / 2 + 1.5;
mcu_path = concat([[mcu_x, matrix_board_z - boards_matrix_harness_h]],
                  [for (i = [0 : 8]) let(t = 90 * i / 8) [mcu_x - mcu_r + mcu_r * cos(t), jm_z + e_mb + mcu_r - mcu_r * sin(t)]],
                  [[jm_x1, jm_z + e_mb]]);
// J-UMB: one pin per umbilical conductor at 2.54 mm, centred on the
// etherCON's axis across the body, its row meeting the adapter at
// boards.umb_joint_row_h above the main board.
ju_l = 8 * 2.54;
ju_row_z = cb_top + boards_umb_joint_row_h;
tongue_y = [ec_c[0] - ec_fl[0] / 2, ec_c[0] + ec_fl[0] / 2];
// THE MAIN BOARD'S MOUNTS (ADR 0022, ADR 0025), all on the bottom plate: what
// a mount keeps clear round its centre - a column's standoff or an end
// mount's nut on the top face, the spacer under the board, and the float.
mb_keep_d = max(hardware_mb_nut_e, col_standoff_e, hardware_kb_spacer_od) + 2 * hardware_kb_mount_float;
end_mount_in = 4;   // drawing convention: an end mount's centre in from the board's long edge
// The breath sensor's footprint along the body, its barbs included.
sensor_keep_l = boards_sensor_body + boards_sensor_port_l;
sensor_keep_cx = sensor_c[0] - boards_sensor_body / 2 + sensor_keep_l / 2;
// J-UMB's insulator and the parts band in front of it, along the body.
umb_band_d = boards_umb_joint_d + boards_umb_parts_d;
function so_clear(p) = let(r = mb_keep_d / 2 + 0.5)
    !pins_at(p, r) && (abs(p[1] - W / 2) >= lighting_strip_w / 2 + r || p[0] < strip_x0 - r || p[0] > strip_x0 + strip_l + r)
    // a thumb switch's cutout in the bottom plate is an edge for the stud,
    // and its housing and latches stand under the board beside the spacer,
    // which keeps 0.5 from the cutout as the key plate's spacers do
    && min([for (k = bottom_keys) rect_gap(p, key_xy(k), [plate_cutout, plate_cutout], key_rot(k))])
       >= max(hardware_stud_edge, hardware_kb_spacer_od / 2 + hardware_kb_mount_float + 0.5)
    && min([for (u = ubolt_legs()) norm(p - u)]) >= ubolt_keep_r + r
    // the breath sensor's body and leads, and its barbs, which stand out
    // boards.sensor_port_l toward the tail at a nut's height
    && max(abs(p[0] - sensor_keep_cx) - sensor_keep_l / 2, abs(p[1] - sensor_c[1]) - boards_sensor_leads / 2) >= r
    // and the slot in front of the lower port, which is a board edge: a
    // mount's PWR_GND pad (ADR 0025 point 7) and its nut must not reach it
    && rect_gap(p, port_slot_c, port_slot_sz, 0) >= r
    && max(abs(p[0] - tall_c[0][0]) - tall_sz[0] / 2, abs(p[1] - tall_c[0][1]) - tall_sz[1] / 2) >= r
    && min([for (cl = chain_ribbon_cls) let(sp = chain_span(chain_x(cl), chain_dir(cl)), x0 = sp[0], x1 = sp[1])
              rect_gap(p, [(x0 + x1) / 2, chain_y], [x1 - x0, boards_chain_hdr_l], 0)]) >= r + 1
    && max(abs(p[0] - (jm_x0 + jm_x1) / 2) - jm_sz[0] / 2, abs(p[1] - jm_y) - jm_sz[1] / 2) >= r
    // J-UMB and, in front of it, the band its footprint and the parts that
    // sit at the connector need (boards.umb_parts_d), not just its insulator
    && max(abs(p[0] - (ua_x0 - umb_band_d / 2)) - umb_band_d / 2, abs(p[1] - ec_c[0]) - ju_l / 2) >= r + 1;
function first_clear(cs) = let(ok = [for (c = cs) if (so_clear(c)) c]) len(ok) > 0 ? ok[0] : undef;
// THE COLUMNS (ADR 0025) stand where the key boards' mounts are, and they are
// vertical: the main board's mount IS the key board's. Each is also tried up
// to 1 mm along the body, in 0.1 mm steps, only so that drc.echo can say how
// far a key board's mount would have to move if a thumb switch's cutout or
// anything else on the main board came too close (ADR 0022 point 8 used to
// nudge the main board's mount instead; a column cannot lean).
cb_cols = [for (m = columns()) [m, first_clear([for (i = [0 : 20]) m + [(i % 2 == 0 ? 1 : -1) * ceil(i / 2) / 10, 0]])]];
n_cols = len(cb_cols);
// And a pair tried at each end (one may be dropped beside a column, below): at the mouth, and on the tongue before J-UMB, which
// takes the umbilical's mating push - behind the parts that sit at J-UMB.
// The U-bolt's clamp holds the middle (ADR 0022 point 7).
cb_ends = concat([for (y = [cb_y[0] + end_mount_in, cb_y[1] - end_mount_in]) first_clear([for (d = [0 : 1 : 30]) [cb_x[0] + 4 + d, y]])],
                 [for (y = [tongue_y[0] + end_mount_in, tongue_y[1] - end_mount_in]) first_clear([for (d = [0 : 1 : 20]) [ua_x0 - umb_band_d - mb_keep_d / 2 - 2 - d, y]])]);
// An end mount with a column's mount within hardware.end_mount_merge_d is
// dropped: the column already holds the board there (owner, 2026-09-30).
function near_col(p) = min([for (c = cb_cols) norm(p - c[0])]);
cb_ends_dropped = [for (c = cb_ends) if (c != undef && near_col(c) < hardware_end_mount_merge_d) c];
// Every mount on the bottom plate: the columns first (n_cols of them), then the ends.
cb_standoffs = concat([for (c = cb_cols) c[0]], [for (c = cb_ends) if (c != undef && near_col(c) >= hardware_end_mount_merge_d) c]);
// The breath tube's lane (routing_3d), placed once the mounts it keeps clear of are.
tube_y = lane_y(routing_tube_lane, routing_tube_od);
module centre_board_3d() {
    P(C_PCB, false, "main board") translate([0, 0, cb_z]) linear_extrude(switch_pcb_t) cb_2d();
    P(C_ENVELOPE, false, "parts main board") translate([0, 0, cb_top]) linear_extrude(boards_smt_h) difference() {
        offset(-0.5) cb_2d();
        // nothing under the chain header and its plug (the ribbon's hairpin is above them, between the plugs)
        for (cl = chain_ribbon_cls) let(sp = chain_span(chain_x(cl), chain_dir(cl)), x0 = sp[0], x1 = sp[1])
            translate([x0 - 0.5, chain_y - boards_chain_hdr_l / 2 - 0.5]) square([x1 - x0 + 1, boards_chain_hdr_l + 1]);
        translate([jm_x0 - 0.5, jm_y - jm_sz[1] / 2 - 0.5]) square(jm_sz + [1, 1]);
        translate([ua_x0 - boards_umb_joint_d - 0.5, ec_c[0] - ju_l / 2 - 0.5]) square([boards_umb_joint_d + 1, ju_l + 1]);
        // nothing tall under the Matrix ribbon's level run into J-MCU, over the tongue
        translate([jm_x1, jm_y - routing_mcu_ribbon_w / 2 - 0.5]) square([mcu_x - jm_x1 + 1, routing_mcu_ribbon_w + 1]);
        translate(sensor_c) square([boards_sensor_body + 1, boards_sensor_leads + 1], center = true);
        for (c = tall_c) translate(c) square(tall_sz + [1, 1], center = true);
        for (c = cb_standoffs) translate(c) circle(d = mb_keep_d + 1);
        for (u = ubolt_legs()) translate(u) circle(r = ubolt_keep_r);   // the U-bolt's washer and nut
        translate([strip_x0 - 0.5, strip_y - 0.5]) square([strip_l + 1, lighting_strip_w + 1]);
    }
    P([0.30, 0.30, 0.55], false, "tall parts main board")
        translate([tall_c[0][0] - tall_sz[0] / 2, tall_c[0][1] - tall_sz[1] / 2, cb_top]) cube([tall_sz[0], tall_sz[1], boards_tall_h]);
    // THE MOUNTS (ADR 0022, ADR 0025), every one on the bottom plate: the stud,
    // its head flush in the plate's underside, the spacer, the board; then at a
    // column the standoff, threaded onto the stud up to the key board, and at
    // an end mount the nut.
    for (i = [0 : 1 : len(cb_standoffs) - 1]) let(c = cb_standoffs[i], n = i + 1) {
        P(C_STEEL, false, str("main board stud ", n)) translate([c[0], c[1], z_floor]) {
            cylinder(d = hardware_stud_head_d, h = 0.3);
            cylinder(d = 2.5, h = hardware_stud_l);
        }
        P(C_STEEL, false, str("main board spacer ", n)) translate([c[0], c[1], z_bplate_top])
            difference() { cylinder(d = hardware_kb_spacer_od, h = cb_z - z_bplate_top); translate([0, 0, -1]) cylinder(d = hardware_stud_attached_hole, h = 9); }
        if (i < n_cols)
            P(C_BRASS, false, str("column standoff ", n)) translate([c[0], c[1], cb_top])
                difference() { rotate(30) cylinder(d = col_standoff_e, h = col_standoff_l, $fn = 6); translate([0, 0, -1]) cylinder(d = 2.5, h = col_standoff_l + 2); }
        else
            P(C_STEEL, false, str("main board nut ", n)) translate([c[0], c[1], cb_top])
                difference() { cylinder(d = hardware_mb_nut_e, h = hardware_mb_nut_m, $fn = 6); translate([0, 0, -1]) cylinder(d = 2.5, h = 9); }
    }
}
col_standoff_l = (kb_top - boards_key_board_t) - cb_top;   // the gap it fills: main board top face to key board underside


// PARTS ON THE BOARDS, as envelopes. Cluster boards: a component layer on
// the cavity side (the plate side cannot take a SOIC - ks33-geometry.md).
// The Matrix: its back-side parts. The main board's parts are with it.
module parts_3d() {
    for (cl = ["left_hand", "right_hand"])
        P(C_ENVELOPE, false, str("parts ", cl)) translate([0, 0, top_z - boards_cluster_smt_h + explode * 0.25])   // moves with its board
            linear_extrude(boards_cluster_smt_h) difference() {
                offset(-0.5) key_board_2d(cl);
                let(q = kb_chain_rect(cl)) translate([q[0] - 0.5, q[1] - 0.5]) square([q[2] - q[0] + 1, q[3] - q[1] + 1]);
                // no parts under a column's standoff: the PCB keeps the same circle clear
                for (m = kb_mounts(cl)) translate(m) circle(d = col_standoff_e + 2 * hardware_kb_mount_float);
            }
    P([0.20, 0.20, 0.22], false, "Matrix underside parts") translate([matrix_xy[0] - 9.5, matrix_xy[1] - 9.5, matrix_board_z - boards_matrix_under_h])
        cube([19, 19, boards_matrix_under_h]);
}

module routing_3d() {
    trap_y = lane_y(routing_tube_lane, routing_trap_d);   // inboard of the mouth-end mounts, like the tube
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
    // U-bolt: loop below, legs through the oak bottom, the bottom plate, a
    // spacer and the main board; a washer and a nut on each leg on the board's
    // top face. A leg ends a thread's pitch past its nyloc.
    P(C_STEEL, false, "U-bolt") translate([0, 0, -explode]) {
        for (u = ubolt_legs()) translate([u[0], u[1], -hardware_ubolt_drop + hardware_ubolt_span / 2])
            cylinder(d = hardware_ubolt_rod_d, h = ubolt_nut_z + hardware_ubolt_nut_h + 0.5 + hardware_ubolt_drop - hardware_ubolt_span / 2);
        translate([ubolt_c[0], ubolt_c[1], -hardware_ubolt_drop + hardware_ubolt_span / 2]) rotate([0, 0, 90]) rotate([-90, 0, 0])
            rotate_extrude(angle = 180) translate([hardware_ubolt_span / 2, 0]) circle(d = hardware_ubolt_rod_d);
    }
    for (i = [0, 1]) P(C_STEEL, false, str("U-bolt nut ", i + 1))
        translate([ubolt_legs()[i][0], ubolt_legs()[i][1], ubolt_nut_z + explode])
            cylinder(d = hardware_ubolt_nut_af / cos(30), h = hardware_ubolt_nut_h, $fn = 6);
    for (i = [0, 1]) P(C_STEEL, false, str("U-bolt washer ", i + 1))
        translate([ubolt_legs()[i][0], ubolt_legs()[i][1], cb_top])
            difference() { cylinder(d = hardware_ubolt_washer_od, h = hardware_ubolt_washer_t); translate([0, 0, -1]) cylinder(d = hardware_ubolt_rod_d + 0.2, h = 3); }
    // the spacer between the bottom plate and the board, faced to the plates' spacers' length
    for (i = [0, 1]) P(C_BRASS, false, str("U-bolt spacer ", i + 1))
        translate([ubolt_legs()[i][0], ubolt_legs()[i][1], z_bplate_top])
            difference() { cylinder(d = hardware_ubolt_spacer_od, h = cb_z - z_bplate_top); translate([0, 0, -1]) cylinder(d = hardware_ubolt_rod_d + 0.2, h = 9); }
}

// The shell is drawn LAST: a see-through (ghosted or faded) part drawn
// before what is behind it hides it in the preview renderer, which is how
// the ribbons went missing from the first renders of them.
module assembly() {
    if (show_keys) { keys_3d(); bottom_plate_3d(); }
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
    tail_names = ["last key board, J-UMB, then the etherCON on its adapter",
                  "last key board, the LED matrix on the top face, then the etherCON depth (matrix not centred)",
                  "the right-thumb cluster against the tail cap"];
    drc(undef, "what the tail end needs", layout_matrix_centred && matrix_centred_req >= max(tail_claims_rel) - top_last_rel
        ? str("the LED matrix centred after the keys, with ", cap_edge_rel + 2 * (boards_matrix_board / 2 + behind_matrix)
            >= 2 * (equip_start_rel + usb_front + boards_matrix_board / 2) - cap_edge_rel
            ? "the etherCON behind it" : "its USB-C plug in front of it, clear of the key board") : tail_names[search(max(tail_claims_rel), tail_claims_rel)[0]],
        str(tail_req, " mm after the last key"));
    echo("DRC", "INFO", "behind the Matrix, to the tail face", behind_matrix,
         str("mm = USB-C plug ", usb_behind, " + clearance ", layout_tail_clear, " + the etherCON's adapter ", boards_umb_adapter_t,
             " + the connector to its flange ", ethercon_pcb_setback, " + tail cap ", ends_tail_cap_t, " - J-UMB passes under the Matrix"));
    under_m = matrix_board_z - boards_matrix_under_h;
    m_x1 = matrix_xy[0] + boards_matrix_board / 2 + usb_behind;
    drc(ua_x0 >= m_x1 + layout_tail_clear - 0.01, "etherCON adapter behind the Matrix", ua_x0 - m_x1,
        "mm from the Matrix's tail edge (and any plug off it) to the adapter's rear face; the adapter stands the connector's full height");
    drc(cb_top + boards_umb_joint_h <= under_m, "J-UMB passes under the Matrix", under_m - cb_top - boards_umb_joint_h,
        "mm below the Matrix's underside parts");
    // The thinnest body that takes the connector on the floor under the oak
    // top. The term moves one for one with T, so the shortfall adds directly.
    t_min = T + ec_c[1] + ec_fl[1] / 2 + ec_clear - z_oak_top_bot;
    drc(T >= t_min, "body thickness takes the etherCON on the floor", T - t_min,
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
    // THE CAP ON ITS SWITCH (MT165-MX; owner, 2026-09-28). The clash check sweeps the
    // shell through its travel against the switch's own mesh; these print the margins.
    drc(cap_ceiling >= switch_stem_top_above_seat, "keycap seats on its stem: the inside of its top above the stem's top",
        cap_ceiling - switch_stem_top_above_seat, "mm at rest - negative means the cap cannot sit at switch.keycap_top_above_seat on this stem");
    let(sk = cap_sk - switch_total_travel, inner = switch_keycap - 2 * switch_keycap_wall)
        echo("DRC", "INFO", "keycap skirt at full travel", [sk, inner],
             str("mm above the seat, and the skirt's inside width there: over the housing (top at ", switch_housing_top_above_seat,
                 ") its inside must clear the cover (", switch_cover_w, " across), and it must stay above the collar (", switch_collar_t, ") - the clash check tests both on the trimmed mesh"));
    // the skirt, fully pressed, either stays above the housing, or it comes down
    // round the cover (its inside wider) and stops above the collar - the clash
    // check tests the trimmed mesh
    let(sk = cap_sk - switch_total_travel, inner = switch_keycap - 2 * switch_keycap_wall)
        drc(sk >= switch_housing_top_above_seat || (inner >= switch_cover_w && sk >= switch_collar_t),
            "keycap skirt clears the switch's cover and collar at full travel",
            [sk - switch_housing_top_above_seat, inner - switch_cover_w, sk - switch_collar_t],
            "mm: the pressed skirt above the housing's top; or the skirt's inside less the cover's width AND the skirt above the collar - the first, or both of the others, must be positive");
    drc(cap_sk - switch_total_travel >= 0, "keycap skirt stays above the plate at full travel", cap_sk - switch_total_travel,
        "mm above the seat (the plate's top face), fully pressed");
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
                   [for (u = ubolt_legs()) ["U-bolt leg", u, [ubolt_hole_d, ubolt_hole_d]]]);
    function gap(a, b) = max(abs(a[1][0] - b[1][0]) - (a[2][0] + b[2][0]) / 2,
                             abs(a[1][1] - b[1][1]) - (a[2][1] + b[2][1]) / 2);
    clashes = [for (i = [0 : len(feats) - 1], j = [i + 1 : 1 : len(feats) - 1])
               if (gap(feats[i], feats[j]) < 3) str(feats[i][0], " / ", feats[j][0], " ", gap(feats[i], feats[j]))];
    drc(len(clashes) == 0, "oak-bottom cuts at least 3 mm apart (thumb recesses, U-bolt)",
        clashes, "pairs closer than 3 mm, with the web between them (negative = overlap)");
    // Through-cuts only. The oak ends at the groove's wall, groove_clear
    // outside the acrylic - the same edge the key plate rules measure to.
    oak_y0 = u_y0 + stack_groove_clear;
    edge = min([for (f = feats) min(f[1][1] - f[2][1] / 2 - oak_y0, W - oak_y0 - f[1][1] - f[2][1] / 2)]);
    drc(edge >= 2, "oak-bottom cuts inside the U", edge, "mm, smallest web to the side groove's wall");
    // The main board in the U-bolt's clamp (ADR 0025): up each leg the oak,
    // the bottom plate, a spacer faced to the plates' spacers' length, the
    // board, a washer and the nyloc - so the spacer must fill the plate to the
    // board's underside, or the nyloc pulls the board down.
    clamp_gap = cb_z - z_bplate_top - hardware_kb_spacer_l;
    drc(abs(clamp_gap) <= 0.05, "main board in the U-bolt's clamp", [clamp_gap, cb_z - z_bplate_top],
        "mm: the bottom plate to the board's underside less the U-bolt's spacer, faced to hardware.kb_spacer_l (must be within 0.05 - the nuts pull the board down onto it), and that gap");
    // The strap's pull goes into the bottom plate round each leg: its spacer
    // bears on plate metal, clear of a thumb switch's cutout.
    us = min([for (u = ubolt_legs(), k = bottom_keys) rect_gap(u, key_xy(k), [plate_cutout, plate_cutout], key_rot(k))]) - hardware_ubolt_spacer_od / 2;
    drc(us >= 1, "U-bolt spacers bear on the bottom plate", us, "mm from a U-bolt spacer's edge to the nearest thumb switch cutout in the plate");
    // The main board at the U-bolt station: the legs' holes leave strips of
    // board that every trace crossing the station must pass. On the outer
    // layers the washers and nuts keep copper off a little more round each leg.
    cuts_y = [for (u = ubolt_legs()) [u[1] - ubolt_board_hole_r, u[1] + ubolt_board_hole_r]];
    cuts_out = [for (u = ubolt_legs()) let(k = max(hardware_ubolt_nut_af / cos(30), hardware_ubolt_washer_od) / 2 + 0.5) [u[1] - k, u[1] + k]];
    function first_by_lo(v) = [for (c = v) if (c[0] == min([for (d = v) d[0]])) c][0];
    function sort_lo(v) = len(v) == 0 ? [] : let(f = first_by_lo(v)) concat([f], sort_lo([for (c = v) if (c != f) c]));
    function strips(cs, from, to, i = 0) = i >= len(cs) ? (to - from >= boards_board_clear ? [to - from] : [])
        : concat(min(cs[i][0], to) - from >= boards_board_clear ? [min(cs[i][0], to) - from] : [], strips(cs, max(from, cs[i][1]), to, i + 1));
    function total(v, i = 0) = i >= len(v) ? 0 : v[i] + total(v, i + 1);
    neck = strips(sort_lo(cuts_y), cb_y[0], cb_y[1]);
    neck_out = strips(sort_lo(cuts_out), cb_y[0], cb_y[1]);
    drc(total(neck) >= boards_main_neck_min, "main board neck at the U-bolt station", [neck, total(neck), total(neck_out)],
        str("mm of board across the station, strip by strip, their total on the inner layers, and on the outer layers less 0.5 copper keep-out round each washer and nut; every trace from one half to the other passes here (boards.main_neck_min ", boards_main_neck_min, ")"));
    strip_hole = min([for (u = ubolt_legs()) abs(u[1] - W / 2) - ubolt_keep_r - lighting_strip_w / 2]);
    drc(strip_hole >= 0, "LED strip clear of the U-bolt nuts", [strip_hole, strip_hole + boards_board_clear],
        "mm, the strip's edge to the nearest nut's parts keep-out (negative = the strip overlaps it), and to the nut's corners");

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
    // THE COLUMNS ARE VERTICAL (ADR 0025): each main-board mount is its key
    // board's; the offset is how far along the body the nearest clear place
    // is, which is how far the key board's mount would have to move.
    col_off = [for (c = cb_cols) c[1] == undef ? undef : c[1][0] - c[0][0]];
    drc(len([for (o = col_off) if (o != 0) 1]) == 0 && len([for (c = cb_ends) if (c == undef) 1]) == 0,
        "columns vertical: the main board's mounts under the key boards'", [col_off, len([for (c = cb_ends) if (c != undef) 1])],
        "mm each column's key-board mount must move along the body for its foot on the main board to be clear (0 = vertical where it stands; undef = nothing clear within 1 mm), and the end mounts found (mouth pair, tongue pair)");
    drc(len([for (c = cb_ends) if (c != undef) 1]) - len(cb_ends_dropped) == len(cb_standoffs) - n_cols,
        "end mounts dropped beside a column", [len(cb_ends_dropped), cb_ends_dropped, [for (c = cb_ends_dropped) near_col(c)]],
        str("end mounts dropped (count, where, mm to the nearest column) because a column's mount stands within hardware.end_mount_merge_d = ", hardware_end_mount_merge_d, " mm of them"));
    drc(len(cb_standoffs) == n_cols + 4 - len(cb_ends_dropped), "main board mounts on the bottom plate", len(cb_standoffs),
        str("mounts (ADR 0025): ", n_cols, " columns (stud, spacer, board, standoff) and ", len(cb_standoffs) - n_cols,
            " end mounts (stud, spacer, board, nut), all on the bottom plate; the U-bolt's clamp holds the middle, and the soldered thumb switches carry the board between them"));
    // THE MAIN BOARD'S DEPTH (ADR 0022): its mount on the bottom plate is the
    // key boards' mount under the key plate, so its face nearest the thumb
    // switches' seat sits the plate + the spacer below it, and it is as thin
    // as they are.
    let(d = plate_thickness + hardware_kb_spacer_l, w = switch_pcb_below_seat_window) {
        drc(abs(d - switch_thumb_pcb_below_seat) < 0.005, "main board mount sets its depth", d,
            "mm below the thumb switches' seat: the plate + hardware.kb_spacer_l, against switch.thumb_pcb_below_seat");
        drc(d >= w[0] && d <= w[1] && switch_pcb_t <= boards_key_board_t, "main board depth and thickness inside the switch pins' window",
            [d, w, switch_pcb_t], "mm: its depth, against switch.pcb_below_seat_window, and its thickness, no more than the key boards' (boards.key_board_t) so the pins show to solder");
    }
    // Everything under the main board faces the grounded bottom plate
    // (ADR 0025): the thumb switches' housings, the J-CHAIN header's tails and
    // any underside part (ADR 0017's amendment) stand in this gap.
    drc(undef, "main board underside room over the bottom plate", [cb_z - z_bplate_top - boards_board_clear, cb_z - z_floor - boards_board_clear],
        "mm an underside part may stand below the board, less the parts clearance (boards.board_clear): over the bottom plate, which now runs the board's length; and over a window cut through the plate to the oak, where a part needs it (ADR 0025)");
    mb_tails = boards_chain_hdr_tail - switch_pcb_t;
    drc(cb_z - z_bplate_top - mb_tails >= 0.5, "J-CHAIN pin tails clear of the bottom plate", cb_z - z_bplate_top - mb_tails,
        "mm from the main board's chain headers' pin tails, through the board, to the grounded bottom plate");
    drc(boards_tall_h <= tall_room, "regulator block fits where it stands", tall_room - boards_tall_h,
        str("mm spare, ", under_keys(tall_c[0], tall_sz) ? "under a key board" : "beside the key boards, clear to the lid",
            " [approx: key board footprints as squares; clash.txt is the check] - negative means low-profile parts"));
    for (cl = chain_ribbon_cls) drc(chain_x(cl) != undef, str("chain headers on the ", cl, " boards clear of the switches"),
                                    chain_x(cl) == undef ? "none found" : chain_x(cl), "mm along the body (the headers' mouths)");
    drc(tongue_y[1] - tongue_y[0] >= ju_l + 2 * boards_board_clear && ua_x0 > cb_x[1], "J-UMB on the main board's tongue, against the etherCON's adapter",
        [ua_x0 - cb_x[1], tongue_y[1] - tongue_y[0] - ju_l],
        "mm: the tongue's length past the main board, and its width less J-UMB's pin row");
    // Where J-UMB's row meets the adapter, in the connector's own frame:
    // between G below the axis and the peg line through it, a pad's worth
    // (a pitch) clear of each, and above the adapter's lower edge.
    ju_r = ethercon_rotated ? undef : ju_row_z - ec_c[1];
    ju_m = ethercon_rotated ? -1 : min(ju_r + ethercon_g_below, -ju_r, ju_r + ethercon_flange_h / 2 - 1.27) - 2.54;
    drc(ju_m >= 0, "J-UMB's row lands on the adapter clear of the etherCON's footprint", [ju_r, ju_m],
        "mm: the row from the axis (negative = below), and its margin past a pitch from G, from the peg line and from the adapter's edge; a turned connector puts its footprint across the row and is not handled");
    drc(undef, "Matrix ribbon length", path_len(mcu_path), "mm from the Matrix's edge to J-MCU, as drawn");
    // THE KEY CHAIN'S RIBBONS (ADR 0017, amended 2026-09-27): long enough to
    // plug in with the lid laid beside the body; closed, a flat hairpin.
    drc(undef, "key-chain ribbon length (derived)", chain_len,
        "mm of ribbon between the sockets: straight from the main board's plug to the key board's with the key plate raised routing.chain_raise off its columns, plus routing.chain_slack");
    drc(undef, "key-chain cable to order (FFSD length code)", chain_order_in,
        "inches overall, over both sockets, with the -0.125 in tolerance covered: FFSD-06-D-<this>-01-N-RN2");
    drc(chain_r >= routing_chain_bend_r, "key-chain ribbon fold no tighter than its bend radius", chain_r,
        "mm: the fold between the two plugs' heights, against routing.chain_bend_r");
    tails = boards_chain_hdr_tail - boards_key_board_t;
    drc(kb_gap - tails >= 0.5, "J-CHAIN pin tails clear of the key plate", kb_gap - tails,
        "mm from the key header's pin tails, through the key board, to the grounded plate - no window needed");
    drc(undef, "key-chain ribbon closed: hairpin leg and fold radius", [chain_leg, chain_r], "mm; the legs lie flat along the body between the two plugs' heights");
    for (cl = chain_ribbon_cls) let(h = chain_hairpin(cl), r = kb_rect(cl))
        drc(h[0] >= x_in0 + boards_board_clear && h[1] <= x_in1 - boards_board_clear, str("key-chain ribbon hairpin inside the body (", cl, ")"), h, "mm along the body");
    echo("DRC", "INFO", "key board to main board gap", (kb_top - boards_key_board_t) - cb_top,
         "mm from the main board's top face to a key board's underside: what the chain header, its plug and the ribbon's hairpin stand in (ADR 0017)");
    for (cl = chain_ribbon_cls) let(g = chain_col_gap(chain_hairpin(cl)))
        drc(g >= col_keep_r + 0.5, str("key-chain ribbon hairpin clear of the columns (", cl, ")"), g - col_keep_r,
            "mm from the closed hairpin to the nearest column's hex, off its axis - the columns stand through the whole gap the hairpin lies in");

    // THE KEY BOARDS' DEPTH (ADR 0020, Amendments 4 and 6): the spacer under
    // the key plate sets it, and the column's screw clamps the plate, the
    // spacer and the board onto the standoff (ADR 0025).
    mounts = columns();
    echo("DRC", "INFO", "key-board mount gap (derived)", kb_gap,
         "mm: plate underside to board top - hardware.kb_spacer_l");
    echo("DRC", "INFO", "key-board mount gap window", switch_pcb_below_seat_window - [1, 1] * plate_thickness,
         "mm: the gaps that keep the switch pins' blades in the board and some pin to solder (switch.pcb_below_seat_window)");
    let(d = plate_thickness + kb_gap,
        lo = plate_thickness + hardware_kb_plate_t_tol[0] + hardware_kb_spacer_l + hardware_kb_spacer_l_tol[0],
        hi = plate_thickness + hardware_kb_plate_t_tol[1] + hardware_kb_spacer_l + hardware_kb_spacer_l_tol[1],
        w = switch_pcb_below_seat_window) {
        drc(abs(d - switch_pcb_below_seat) < 0.005, "key-board mount sets the board depth", d,
            "mm below the seat: the plate + hardware.kb_spacer_l, against switch.pcb_below_seat");
        drc(d >= w[0] && d <= w[1], "key-board depth inside the switch pins' window", [d, w], "mm: nominal, against switch.pcb_below_seat_window");
        echo("DRC", lo >= w[0] && hi <= w[1] ? "PASS" : "NOTE", "key-board depth at the hardware's tolerance limits", [lo, hi],
             str("mm below the seat (plate and spacer each at its limit), against the window ", w,
                 lo < w[0] ? str(": at the low corner the pins' wide shoulder starts ", w[0] - lo, " mm into the hole - the first board confirms the fit") : "",
                 hi > w[1] ? str(": at the high corner ", hi - w[1], " mm less pin stands proud to solder - the first board confirms the fit") : ""));
    }
    echo("DRC", "INFO", "key-board mounts", [for (cl = ["left_hand", "right_hand"]) len(kb_mounts(cl))],
         "per board (left_hand, right_hand): a column in each corner");

    // THE COLUMNS (ADR 0025): stud, spacer, main board, standoff, key board,
    // spacer, key plate, screw. The standoff is faced to the gap it fills.
    drc(undef, "column standoff length (derived)", col_standoff_l,
        "mm: the main board's top face to a key board's underside - each column's standoff is faced to this (MECH-COL-STANDOFF)");
    drc(hardware_col_standoff_stock_l >= col_standoff_l, "column standoff faced from its stock length", hardware_col_standoff_stock_l - col_standoff_l,
        str("mm faced off a stocked ", hardware_col_standoff_stock_l, " mm standoff (hardware.col_standoff_stock_l)"));
    eng_min = hardware_thread_engage_min * 2.5;
    stud_in = [for (t = hardware_stud_l_tol) hardware_stud_l + t - (plate_thickness + hardware_kb_spacer_l + switch_pcb_t)];
    drc(stud_in[0] >= eng_min, "column: stud thread in the standoff", stud_in,
        str("mm of FHL-M2.5-", hardware_stud_l, " up into the standoff, at the stud's shortest and longest, against ", eng_min, " (hardware.thread_engage_min diameters of M2.5)"));
    screw_in = [for (t = hardware_col_screw_l_tol) hardware_col_screw_l + t - (plate_thickness + kb_gap + boards_key_board_t)];
    drc(screw_in[0] >= eng_min, "column: screw thread in the standoff", screw_in,
        str("mm of the M2.5 x ", hardware_col_screw_l, " screw down into the standoff, at its shortest and longest, against ", eng_min));
    ends = col_standoff_l + hardware_col_standoff_l_tol[0] - stud_in[1] - screw_in[1];
    drc(ends >= 0.5, "column: stud and screw ends apart in the standoff", ends,
        "mm between the stud's end and the screw's inside the standoff, both at their longest and the standoff at its shortest: if they met, the screw would bottom on the stud before it clamped the key board");
    echo("DRC", "INFO", "column standoff: thread it needs from each end", [stud_in[1] + 0.5, screw_in[1] + 0.5],
         "mm of female thread from the bottom (the stud's) and the top (the screw's), after facing: tapped through, or at least this deep from each end (MECH-COL-STANDOFF)");
    // The cassette's height is the two plates, two spacers, both boards and
    // the standoff: the flush-key rule sets its nominal, and the silicone takes
    // the rest. The boards' own tolerance is the biggest term, and the
    // standoff, faced at assembly, is what takes it out.
    let(nom = 2 * plate_thickness + 2 * hardware_kb_spacer_l + switch_pcb_t + boards_key_board_t + col_standoff_l,
        tol = [for (i = [0, 1]) 2 * hardware_kb_plate_t_tol[i] + 2 * hardware_kb_spacer_l_tol[i] + 2 * boards_pcb_t_tol[i] + hardware_col_standoff_l_tol[i]],
        faced = [for (i = [0, 1]) 2 * hardware_kb_plate_t_tol[i] + 2 * hardware_kb_spacer_l_tol[i] + hardware_col_standoff_l_tol[i]])
        drc(undef, "cassette height at the hardware's tolerance limits", [nom, z_plate_top - z_floor, nom + tol[0], nom + tol[1]],
            str("mm: the cassette, bottom plate's underside to key plate's top, nominal; the shell's room for it (oak bottom's inside face to oak top's underside); and at its limits with every part at its tolerance. The boards' thickness is most of it: facing each column's standoff to the boards as measured leaves ",
                [faced[0], faced[1]], " mm, which the silicone beads take (ADR 0025)"));
    // the bottom plate's studs: a self-clinching stud needs sheet round it -
    // PEM's least distance from its hole's centre to an edge; a thumb switch's
    // cutout, a U-bolt leg's hole and the plate's outline are all edges
    function bp_edge(p) = min(concat([for (k = bottom_keys) rect_gap(p, key_xy(k), [plate_cutout, plate_cutout], key_rot(k))],
                                     [for (u = ubolt_legs()) norm(p - u) - ubolt_hole_d / 2],
                                     [p[1] - bplate_y[0], bplate_y[1] - p[1], p[0] - x_in0, bplate_x1 - p[0]]));
    stud_edge = min([for (c = cb_standoffs) bp_edge(c)]);
    drc(stud_edge >= hardware_stud_edge, "bottom-plate studs clear of the plate's edges and cutouts", stud_edge,
        "mm from a stud's centre to the nearest thumb switch cutout, U-bolt hole or plate edge, worst case, against hardware.stud_edge");
    bsp = min([for (c = cb_standoffs, k = bottom_keys) rect_gap(c, key_xy(k), [plate_cutout, plate_cutout], key_rot(k))]) - hardware_kb_spacer_od / 2 - hardware_kb_mount_float;
    drc(bsp >= 0.5, "bottom-plate spacers clear of the thumb switch cutouts", bsp,
        "mm from a spacer's edge, off its axis by hardware.kb_mount_float, to the nearest thumb switch cutout, worst case");
    shank = hardware_stud_s - plate_thickness;
    drc(shank <= hardware_kb_spacer_l, "bottom-plate studs: unthreaded shank ends inside the spacer", shank,
        "mm of unthreaded shank above the plate, against the spacer it sits in - the main board and the standoff meet thread");
    thread = hardware_stud_l + hardware_stud_l_tol[0] - (plate_thickness + hardware_kb_spacer_l + switch_pcb_t + hardware_mb_nut_m);
    drc(thread >= 2 * hardware_m25_pitch, "end mounts: stud thread past the nut", thread,
        str("mm of FHL-M2.5-", hardware_stud_l, " past an end mount's nut at the stud's shortest, against two pitches"));
    // the key plate: each screw's head bears on plate metal, and each spacer
    // under it clear of the switch cutouts
    hd = min([for (m = mounts) cutout_gap(m)]) - hardware_col_screw_head_d / 2 - hardware_kb_mount_float;
    drc(hd >= 0.5, "column screw heads bear on the key plate", hd,
        "mm from a screw head's edge, off its axis by hardware.kb_mount_float, to the nearest switch cutout, worst case");
    sp = min([for (m = mounts) cutout_gap(m)]) - hardware_kb_spacer_od / 2 - hardware_kb_mount_float;
    drc(sp >= 0.5, "key-board spacers clear of the switch cutouts", sp,
        "mm from a spacer's edge, off its axis by hardware.kb_mount_float, to the nearest switch cutout, worst case");
    // the oak top: a blind pocket over each head, wood left round it and over it
    function pocket_gap(m) = min(cap_gap(m), m[1] - (u_y0 + stack_groove_clear), (W - u_y0 - stack_groove_clear) - m[1],
                                 rect_gap(m, matrix_xy, [matrix_rebate, matrix_rebate], 0)) - hardware_col_pocket_d / 2;
    pk = min([for (m = mounts) pocket_gap(m)]);
    drc(pk >= hardware_col_pocket_wall, "column screw pockets clear of the wood top's cuts", pk,
        "mm of wood from a pocket's edge to the nearest cap slot, side groove or window rebate, worst case, against hardware.col_pocket_wall");
    drc(oak_top_t - col_pocket_depth >= hardware_col_pocket_skin, "column screw pockets leave wood over them", oak_top_t - col_pocket_depth,
        str("mm of wood between a pocket's floor (", col_pocket_depth, " deep: the head and hardware.col_pocket_clear) and the playing face, against hardware.col_pocket_skin"));
    // the tail corners reach the last keys: the least tail margin that keeps
    // their pockets col_pocket_wall from those keys' cap slots, and their heads
    // and spacers clear of the cutouts (along the body only the tail end moves)
    let(tails = [for (cl = ["left_hand", "right_hand"]) each [kb_mounts(cl)[2], kb_mounts(cl)[3]]],
        spare = min(min([for (m = tails) cap_gap(m)]) - hardware_col_pocket_d / 2 - hardware_col_pocket_wall,
                    min([for (m = tails) cutout_gap(m)]) - max(hardware_kb_spacer_od, hardware_col_screw_head_d) / 2 - hardware_kb_mount_float - 0.5))
        echo("DRC", "INFO", "key-board tail margin, least", boards_kb_tail_margin - spare,
             str("mm past the last switch cutout that keeps the tail corners' pockets, heads and spacers clear of the last keys; boards.kb_tail_margin is ", boards_kb_tail_margin));
    kcol = min([for (cl = ["left_hand", "right_hand"], m = kb_mounts(cl)) let(q = kb_chain_rect(cl))
                rect_gap(m, [(q[0] + q[2]) / 2, (q[1] + q[3]) / 2], [q[2] - q[0], q[3] - q[1]], 0) - col_keep_r]);
    drc(kcol >= 0.5, "column standoffs clear of the chain headers", kcol,
        "mm from a standoff's hex, off its axis, to the nearest chain header and its plug, worst case - both boards' headers stand in the gap the standoffs span");

    mw = plate_x1 - (top_last + plate_cutout / 2);
    drc(mw >= 3, "key plate beyond the last key cutout", mw, "mm of aluminium; the plate stops short of the Matrix");
    lip_t = oak_top_t - openings_matrix_acrylic_t;
    drc(lip_t >= 2, "oak lip under the frosted window", lip_t, str("mm thick, ", openings_matrix_lip, " mm wide; the acrylic sits flush on it"));
    rw = min([for (k = top_keys) sq_gap(key_xy(k), matrix_xy, (switch_keycap + 2 * stack_cap_clear + matrix_rebate) / 2)]);
    drc(rw >= 3, "oak between the last cap slot and the window rebate", rw, "mm on the top face");
    drc(undef, "LED tops to the frosted window's top face", T - matrix_top_z,
        "mm - frosted acrylic this far above the LEDs softens the pixels; the owner chose it (2026-09-26)");

    // Tail face
    ec_lo = ec_c[1] - ec_fl[1] / 2; ec_hi = ec_c[1] + ec_fl[1] / 2;
    drc(ec_lo >= z_floor && ec_hi <= z_oak_top_bot, "etherCON body inside the cavity height",
        [ec_lo, ec_hi, z_floor, z_oak_top_bot], "body Z range vs cavity Z range at the tail, where the key plate has ended");
    let(cx = max([for (m = columns()) m[0]]) + hardware_col_screw_head_d / 2)
        drc(plate_x1 - cx >= 2, "key plate reaches past the column screws", plate_x1 - cx,
            "mm of plate beyond the last column screw's head; the plate stops short of the Matrix");
    drc(T - openings_matrix_acrylic_t - matrix_top_z >= 0.3, "LED tops under the frosted window",
        T - openings_matrix_acrylic_t - matrix_top_z, "mm, LED tops to the acrylic's underside - the board's top face is against the oak");
    drc(boards_matrix_emitters <= openings_matrix_window - 0.5, "LED array fits the window opening it stands in",
        openings_matrix_window - boards_matrix_emitters, "mm across, opening less the array");
    fl_margin = min(ec_c[1] - ec_fl[1] / 2, T - (ec_c[1] + ec_fl[1] / 2));
    drc(fl_margin >= 0, "etherCON flange fits behind the tail cap", fl_margin, "mm, the smaller of above and below the flange, inside the cap's height");
    // The bore is what is cut from the cap; the flange only clamps against it.
    drc(undef, "tail cap material below and above the etherCON bore",
        [ec_c[1] - ethercon_bore_d / 2, T - (ec_c[1] + ethercon_bore_d / 2)], "mm - the connector stands on the floor, so it is not centred");
    // USB-C by panel-mount extension (owner, 2026-09-26). The receptacle sits
    // behind the cap beside the flange, so its room is the lane from the
    // flange's edge to the side's inside face, not the space beside the housing.
    usb_room = usb_lane[1] - usb_lane[0];
    drc(usb_room >= usb_sz[0] + usb_web_min, "USB-C extension receptacle beside the etherCON flange", usb_room - usb_sz[0],
        str("mm spare across the ", usb_room, " mm lane from the flange's edge to the side, for a receptacle ", usb_sz[0], " mm across (",
            openings_usb_slot_portrait ? "on end" : "flat", ")"));
    usb_web = (usb_c[0] - usb_cut_y / 2) - (ec_c[0] + ec_fl[0] / 2 + ethercon_recess_margin);
    drc(usb_web >= usb_web_min, "tail cap web between the USB-C cutout and the etherCON recess", usb_web,
        str("mm of oak on the tail face, from the widest USB-C cutout (", usb_cut_y, " mm across: the overmould pocket or the slot)"));
    // The recess (ADR 0021): the NE8FAV's panel limit, met by a pocket from
    // outside; its edges stay on the face with oak round them.
    rc_top = ethercon_rotated ? ec_c[1] + ec_fl[1] / 2 : ec_c[1] + ethercon_tab_top;
    rc_web = min(T - (rc_top + ethercon_recess_margin), ec_c[1] - ec_fl[1] / 2 - ethercon_recess_margin,
                 ec_c[0] - ec_fl[0] / 2 - ethercon_recess_margin - u_y0);
    drc(rc_web >= usb_web_min, "tail cap recess for the etherCON inside the tail face", rc_web,
        str("mm of oak round the ", ec_recess_d, " mm recess that leaves the NE8FAV its ", ec_panel_t, " mm panel (ethercon.panel_max ", ethercon_panel_max, ")"));
    drc(undef, "etherCON PUSH tab against the tail face", ethercon_tab_front - ends_tail_cap_t,
        "mm the tab stands proud of the tail face (negative = inside the recess)");
    drc(undef, "etherCON locating pegs, cut off flush", ethercon_peg_below - ec_clear,
        "mm the two pegs under the flange would reach into the oak bottom if left on (ethercon.peg_below; ADR 0021)");
    drc(usb_om[0] >= usb_sz[0] && usb_om[1] >= usb_sz[1] && openings_usb_panel_t <= openings_usb_nose_l,
        "USB-C plug overmould reaches the receptacle", [usb_pocket_d, openings_usb_panel_t, openings_usb_nose_l],
        "mm: the overmould pocket's depth from the tail face; the panel left under it; the receptacle's nose, which must pass that panel so its face is level with the pocket floor");
    ear_z = [usb_c[1] - openings_usb_ear_pitch / 2, usb_c[1] + openings_usb_ear_pitch / 2];
    ears_fit = ear_z[0] >= z_floor && ear_z[1] <= z_oak_top_bot;
    drc(openings_usb_mount != "ears" || ears_fit, "USB-C receptacle mount inside the cavity", [openings_usb_mount, ear_z, [z_floor, z_oak_top_bot]],
        str("the mount; where screw ears at ", openings_usb_ear_pitch, " mm pitch would put their centres on end; the cavity's height behind the cap - ",
            ears_fit ? "ears would fit" : "ears would not, so the receptacle is earless, clamped from behind (openings.usb_mount)"));
    usb_run = norm([x_in1 - openings_usb_ext_depth - (matrix_xy[0] + boards_matrix_board / 2), usb_c[0] - matrix_xy[1], usb_c[1] - (matrix_board_z - 2)]);
    echo("DRC", "INFO", "USB-C extension cable run, Matrix edge to receptacle", usb_run,
         "mm straight line; buy the shortest extension that reaches, with slack for the tail cap to come off");

}

// ============================================================ dispatch ====
module part_2d(p) {
    if (p == "plate_top") plate_top_2d();
    else if (p == "oak_top") oak_top_2d();
    else if (p == "oak_bottom") oak_bottom_2d();
    else if (p == "plate_bottom") plate_bottom_2d();
    else if (p == "oak_grooves") oak_grooves_2d();
    else if (p == "side") side_2d();
    else if (p == "mouth_cap") mouth_cap_2d();
    else if (p == "tail_cap") tail_cap_2d();
    else if (p == "matrix_window") matrix_window_2d();
    else if (p == "oak_rebates") oak_rebates_2d();
    else if (p == "oak_pockets") oak_pockets_2d();
    else if (p == "key_board_left_hand") key_board_2d("left_hand");
    else if (p == "key_board_right_hand") key_board_2d("right_hand");
    else if (p == "main_board") cb_2d();
    else assert(false, str("unknown part ", p));
}

function origin_x() = origin == "centre" ? -L / 2 : origin == "tail" ? -L : 0;
module at_origin() { translate([origin_x(), 0, 0]) children(); }

if (!figure) {
    if (part == "assembly") at_origin() assembly();
    else if (part == "drc") drc_report();
    else if (part == "pcb_geom") pcb_geometry();
    else part_2d(part);
}
