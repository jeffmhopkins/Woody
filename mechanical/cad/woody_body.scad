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
ghost_shell = false;  // draw the shell translucent to see inside
// Sections. "y" / "x" clip every part with a half-space (keep Y < cut, or
// a slab X > cut) and stay 3D. "y2d" / "x2d" are true section DRAWINGS: each
// part cut by the plane with projection(cut = true), coloured per part, laid
// flat - "y2d" as (X, Z), "x2d" as (Y, Z) looking toward the tail. Use the
// 2D ones for anything dimensioned; OpenCSG loses part colours on 3D cuts.
cut = "none";
cut_at = 0;
cut_key = "";         // or name a key: the X cut goes through its centre
cut_depth = 1000;     // "x" keeps a slab this deep beyond the cut
figure = false;       // set true by a figure that includes this file

LAYERS = ["plate_top", "oak_top", "oak_bottom", "thumb_plate", "side_outer",
          "side_inner", "mouth_cap", "tail_cap", "tail_backplate", "ubolt_backplate",
          "diffuser", "service_cover"];

$fn = 40;
EPS = 0.01;           // drawing convention: coplanar-face nudge

// ---------------------------------------------------------------- frame ----
L = envelope_length;
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
lid_y0 = stack_side_t - stack_rebate_w;         // lid sits in the rebates
lid_w = W - 2 * lid_y0;
u_y0 = stack_side_t;                            // inside face of each side
u_w = W - 2 * stack_side_t;
x_in0 = ends_mouth_cap_t;                       // between the end caps
x_in1 = L - ends_tail_cap_t;

// The key plate's origin (config/key-layout.yaml: "top-left of key plate").
plate_x0 = x_in0;
plate_y0 = lid_y0;

// ------------------------------------------------------- length budget ----
seg_sum = layout_margin_mouth + layout_mouthpiece + layout_display_band
        + layout_lh_run + layout_gap + layout_rh_run + layout_tail + layout_margin_tail;
slack = L - seg_sum;
function grow(s) = layout_slack_to == s ? slack : 0;
x_mouth0 = layout_margin_mouth;
x_disp0 = x_mouth0 + layout_mouthpiece + grow("mouth");
x_lh0 = x_disp0 + layout_display_band;
x_gap0 = x_lh0 + layout_lh_run;
x_rh0 = x_gap0 + layout_gap + grow("gap");
x_tail0 = x_rh0 + layout_rh_run;
x_tail1 = x_tail0 + layout_tail + grow("tail");

// -------------------------------------------------------------- keys ------
function key_id(k) = k[0];
function key_face(k) = k[1];
function key_n(k) = ord(k[0][2]) - 48;
function count(cl) = len([for (k = keys) if (k[6] == cl) 1]);
function lerp(a, b, t) = a + (b - a) * t;

// Provisional positions, used only while a key's x/y is null.
function prov_xy(k) =
    let(cl = k[6], i = key_n(k) - 1, n = count(cl), c = W / 2 + layout_lateral_inset)
    cl == "left_hand"  ? [x_lh0 + i * layout_lh_run / (n - 1), c] :
    cl == "right_hand" ? [x_rh0 + i * layout_rh_run / (n - 1), c] :
    cl == "left_thumb" ? lt_arc(i / (n - 1)) :
    cl == "right_thumb" ? rt_xy(i) : [0, 0];

// The left thumb's four keys lie on the tip's sweep, mostly along the body
// (ADR 0010). A half-sine bulge of lt_arc_lateral across a lt_arc_length run.
function lt_arc(t) = [x_lh0 + layout_lt_arc_start + t * layout_lt_arc_length,
                      W / 2 - layout_lt_arc_lateral / 2 + layout_lt_arc_lateral * sin(180 * t)];
rt_rest = [x_rh0 + layout_rt_rest_at * layout_rh_run, W / 2];
// Right-thumb control switches, offset from the rest (ADR 0010): one toward
// the tail, two flanking it toward the mouthpiece. Placeholder geometry.
function rt_xy(i) = i == 0 ? rt_rest + [layout_rt_offset, 0]
                  : rt_rest + [-0.6 * layout_rt_offset, (i == 1 ? -1 : 1) * 0.6 * layout_rt_offset];
// Three spare-switch cutouts, required in the DXF by M3 (ADR 0010): octave
// up and down extend the left-thumb arc, hold sits before the right thumb.
// Straight extensions of the arc's end keys - the half-sine is not
// extrapolated, it leaves the body.
lt_step = layout_lt_arc_length / (count("left_thumb") - 1);
spare_xy = [lt_arc(0) - [lt_step, 0], lt_arc(1) + [lt_step, 0], rt_rest - [1.6 * layout_rt_offset, 0]];

function placed(k) = !is_undef(k[2]) && !is_undef(k[3]);
function key_xy(k) = placed(k) ? [plate_x0 + k[3], plate_y0 + k[2]] : prov_xy(k);
function key_rot(k) = k[4];
top_keys = [for (k = keys) if (key_face(k) == "top") k];
bottom_keys = [for (k = keys) if (key_face(k) == "bottom") k];
function cluster_keys(cl) = [for (k = keys) if (k[6] == cl) k];
function xs(list) = [for (k = list) key_xy(k)[0]];
function key_by_id(id) = [for (k = keys) if (k[0] == id) k][0];
cut_pos = cut_key == "" ? cut_at : key_xy(key_by_id(cut_key))[0];

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
C_DIFFUSER = [1, 1, 1, 0.6];

// ----------------------------------------------------------- clipping -----
module clip_space() {
    big = 4 * L;
    if (cut == "y") translate([-big / 2, cut_pos - big, -big / 2]) cube(big);
    else if (cut == "x") translate([cut_pos, -big / 2, -big / 2]) cube([cut_depth, big, big]);
}
// Every visible part goes through P(), so colour survives a section cut.
module P(c, shell = false) {
    cc = (shell && ghost_shell) ? [c[0], c[1], c[2], 0.25] : c;
    color(cc)
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
        square([x_in1 - x_in0, lid_w]);
        translate([-plate_x0, -plate_y0]) {
            for (k = top_keys) cutout_at(key_xy(k), key_rot(k), plate_cutout);
            for (f = fasteners()) translate(f) circle(d = tap_d_m3);
        }
    }
}
tap_d_m3 = 2.5;   // drawing convention: M3 tap drill; see the DRC on thread engagement

// Oak top: the lid's wood, ON TOP of the plate. One hole per key, which the
// cap travels in. No fastener holes - the fasteners stop in the plate, so the
// playing face is unbroken oak. Frame: as the plate.
module oak_top_2d() {
    difference() {
        square([x_in1 - x_in0, lid_w]);
        translate([-plate_x0, -plate_y0])
            for (k = top_keys) translate(key_xy(k)) rotate(key_rot(k))
                square(switch_keycap + 2 * stack_cap_clear, center = true);
    }
}

// The U's floor. Thumb recesses are the through-cuts (ADR 0009: "oak
// thickness sets the inset depth"); matrix window; service opening;
// fastener and U-bolt holes. Frame: model XY minus [x_in0, u_y0].
module oak_bottom_2d() {
    difference() {
        square([x_in1 - x_in0, u_w]);
        translate([-x_in0, -u_y0]) {
            for (k = bottom_keys) translate(key_xy(k)) rotate(key_rot(k))
                square(switch_keycap + 2 * thumb_recess_clear, center = true);
            for (s = spare_xy) translate(s) square(switch_keycap + 2 * thumb_recess_clear, center = true);
            translate(matrix_xy) square(openings_matrix_window, center = true);
            display_board_cut_2d();
            translate(service_xy) square([openings_service_cover_l, openings_service_cover_w], center = true);
            for (f = fasteners()) translate(f) circle(d = hardware_fastener_clear_d);
            for (u = ubolt_legs()) translate(u) circle(d = hardware_ubolt_rod_d + 0.5);
        }
    }
}
thumb_recess_clear = 1.0;  // drawing convention: cap-to-recess clearance, an M2 question (ADR 0010)

// One thumb plate per thumb cluster, on the oak bottom's inside face.
// Frame: model XY.
module thumb_plate_2d(cl) {
    ks = cluster_keys(cl);
    pts = concat([for (k = ks) key_xy(k)],
                 cl == "left_thumb" ? [spare_xy[0], spare_xy[1]] : [spare_xy[2]]);
    difference() {
        intersection() {
            hull() for (p = pts) translate(p) square(switch_keycap + 4, center = true);
            translate([x_in0, u_y0 + 0.5]) square([x_in1 - x_in0, u_w - 1]);
        }
        for (k = ks) cutout_at(key_xy(k), key_rot(k), plate_cutout);
        for (s = (cl == "left_thumb" ? [spare_xy[0], spare_xy[1]] : [spare_xy[2]]))
            cutout_at(s, 0, plate_cutout);
    }
}
module thumb_plate_both_2d() { thumb_plate_2d("left_thumb"); thumb_plate_2d("right_thumb"); }

// The acrylic side is TWO laminae, which is how a rebate becomes a pair of
// through-cuts: the outer one full height, the inner one stopping short of
// the lid. Frame: X along, Y = model Z.
module side_outer_2d() { square([x_in1 - x_in0, T]); }
module side_inner_2d() { square([x_in1 - x_in0, z_lid_bot]); }

// End caps, full cross-section. Frame: X = model Y, Y = model Z.
module mouth_cap_2d() {
    difference() {
        rrect(W, T, 1);
        translate(tube_yz) circle(d = ends_tube_hole_d);
    }
}
tube_yz = [W / 2, z_floor + cavity_h / 2];

ec_c = [W / 2 + ethercon_offset_y, T / 2];                 // etherCON centre on the tail face
ec_fl = ethercon_rotated ? [ethercon_flange_h, ethercon_flange_w] : [ethercon_flange_w, ethercon_flange_h];
ec_holes = [for (s = [-1, 1]) ec_c + s * (ethercon_rotated ? [ethercon_hole_dy, ethercon_hole_dx] : [ethercon_hole_dx, ethercon_hole_dy]) / 2];
usb_c = [ec_c[0] + ec_fl[0] / 2 + (W - ec_c[0] - ec_fl[0] / 2) / 2, z_floor + 1.6 + 1.6];

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
module tail_backplate_2d() {
    difference() {
        translate([u_y0, z_floor]) square([u_w, cavity_h]);
        translate(ec_c) circle(d = ethercon_bore_d);
        for (h = ec_holes) translate(h) circle(d = ethercon_hole_d);
        translate(usb_c) square([openings_usb_slot_w, openings_usb_slot_h], center = true);
    }
}
ubolt_bp = [2 * hardware_ubolt_span, u_w - 12];
module ubolt_backplate_2d() {
    difference() {
        translate(ubolt_c) square(ubolt_bp, center = true);
        for (u = ubolt_legs()) translate(u) circle(d = hardware_ubolt_rod_d + 0.5);
    }
}
module diffuser_2d() { translate(matrix_xy) square(openings_matrix_window + 4, center = true); }
module service_cover_2d() {
    translate(service_xy) difference() {
        square([openings_service_cover_l + 6, openings_service_cover_w + 6], center = true);
        for (s = [-1, 1]) translate([s * (openings_service_cover_l / 2 + 1.5), 0]) circle(d = 2.4);
    }
}

// --------------------------------------------------------- features ------
disp_c = [x_disp0 + layout_display_band / 2, W / 2];
// The board lies lengthwise (ADR 0008) on the UNDERSIDE, glass down, in a
// through-cut in the oak bottom (decided 2026-09-26).
// Its outline is the vendor's own DXF, not retyped numbers.
DISP_DXF = "../../datasheets/mechanical/LILYGO-T-DISPLAY-S3-AMOLED-OUTLINE.dxf";
disp_board = [58.782, 25.495];   // read off DISP_DXF's DIMENSION entities, for centring only
module display_board_outline_2d() {
    translate(disp_c) rotate(-90) translate([-disp_board[1] / 2, -disp_board[0] / 2]) import(DISP_DXF, layer = "KeepOutLayer");
}
module display_board_cut_2d() { offset(0.5) display_board_outline_2d(); }
cluster_margin = 4;   // drawing convention: board edge past the outermost switch body
module cluster_window_2d(ks) {
    x = xs(ks);
    translate([min(x) - plate_cutout / 2 - cluster_margin, W / 2 - switch_cluster_pcb_w / 2])
        square([max(x) - min(x) + plate_cutout + 2 * cluster_margin, switch_cluster_pcb_w]);
}

// Tail equipment. The Matrix hangs under the carrier (carrier.md section 7)
// with its LEDs facing the window in the oak bottom.
carrier_x1 = x_in1 - boards_carrier_from_tail;
carrier_x0 = carrier_x1 - boards_carrier_l;
matrix_xy = [carrier_x1 - boards_matrix_board / 2 - 2, W / 2 + (u_w / 2 - boards_matrix_board / 2 - 1)];
service_xy = [matrix_xy[0] - boards_matrix_board / 2 - openings_service_cover_l / 2 - 8, W / 2 - 8];

// Six fasteners up from the bottom into the plate, zig-zagging between the
// long edges ~80 mm apart (ADR 0009).
function fasteners() =
    let(n = hardware_fastener_count, a = x_in0 + hardware_fastener_end, b = x_in1 - hardware_fastener_end)
    [for (i = [0 : n - 1]) [lerp(a, b, i / (n - 1)),
                            i % 2 == 0 ? lid_y0 + hardware_fastener_inset : W - lid_y0 - hardware_fastener_inset]];

// U-bolt in the inter-hand gap on the bottom face (ADR 0009); legs along X.
ubolt_c = [(x_gap0 + x_rh0) / 2, W / 2];
function ubolt_legs() = [for (s = [-1, 1]) ubolt_c + [s * hardware_ubolt_span / 2, 0]];

// ================================================================ 3D ======

module lam(z, t, c, shell = true) {
    P(c, shell) translate([0, 0, z]) linear_extrude(t) children();
}

module lid(dz = 0) {
    translate([0, 0, dz]) {
        lam(z_oak_top_bot + explode, oak_top_t, C_OAK)
            translate([plate_x0, plate_y0]) oak_top_2d();
        lam(z_plate_bot + explode / 2, plate_thickness, C_ALU, false)
            translate([plate_x0, plate_y0]) plate_top_2d();
    }
}

module u_channel() {
    lam(-explode, oak_bottom_t, C_OAK) translate([x_in0, u_y0]) oak_bottom_2d();
    // The two laminae of each side: outer full height, inner to the lid.
    for (s = [0, 1]) {
        y_out = s == 0 ? 0 : W - lid_y0;
        y_in = s == 0 ? lid_y0 : u_y0 + u_w;
        P(C_ACRYLIC, true) translate([x_in0, y_out + lid_y0, 0]) rotate([90, 0, 0])
            linear_extrude(lid_y0) side_outer_2d();
        P(C_ACRYLIC, true) translate([x_in0, y_in + stack_rebate_w, 0]) rotate([90, 0, 0])
            linear_extrude(stack_rebate_w) side_inner_2d();
    }
}

module caps() {
    P(C_ACRYLIC, true) translate([ends_mouth_cap_t - explode / 3, 0, 0]) rotate([90, 0, 90]) mirror([0, 0, 1])
        linear_extrude(ends_mouth_cap_t) mouth_cap_2d();
    P(C_OAK_DARK, true) translate([x_in1 + explode / 3, 0, 0]) rotate([90, 0, 90])
        linear_extrude(ends_tail_cap_t) tail_cap_2d();
}

module switch_at(xy, rot, top, spare = false) {
    // Seat (collar underside) on the plate's key face.
    tf = top ? [xy[0], xy[1], z_plate_top + explode / 2] : [xy[0], xy[1], z_floor - explode];
    // P() OUTSIDE the placement: a section cuts in world coordinates, and a
    // P() inside translate() cut every switch in its own frame instead.
    P(C_SWITCH) translate(tf) rotate([top ? 0 : 180, 0, rot]) import("vendor/ks33.stl");
    P(spare ? C_SPARE : C_CAP) translate(tf) rotate([top ? 0 : 180, 0, rot])
        translate([0, 0, switch_keycap_top_above_seat - 2.5])
            linear_extrude(2.5, scale = 0.85) square(switch_keycap, center = true);
}

module keys_3d() {
    for (k = keys) switch_at(key_xy(k), key_rot(k), key_face(k) == "top");
    for (s = spare_xy) switch_at(s, 0, false, true);
}

module thumb_plates_3d() {
    lam(z_floor - explode * 0.5, plate_thickness, C_ALU, false) thumb_plate_both_2d();
}

module cluster_boards() {
    for (cl = ["left_hand", "right_hand"])
        P(C_PCB) translate([0, 0, z_plate_top - switch_pcb_below_seat - switch_pcb_t + explode * 0.25])
            linear_extrude(switch_pcb_t) offset(-0.5) cluster_window_2d(cluster_keys(cl));
    for (cl = ["left_thumb", "right_thumb"])
        P(C_PCB) translate([0, 0, z_floor + switch_pcb_below_seat - explode * 0.25])
            linear_extrude(switch_pcb_t) offset(-3) thumb_plate_2d(cl);
}

module display_board() {
    // Vendor STEP, meshed; its frame matches the DXF: x across, y along, glass
    // at z = 5.5. Flipped glass-down, glass at boards_display_recess.
    P([0.22, 0.24, 0.30]) translate([disp_c[0], disp_c[1], boards_display_recess + 5.5 - explode])
        rotate([180, 0, 0]) rotate([0, 0, -90]) translate([-disp_board[1] / 2, -disp_board[0] / 2, 0])
            intersection() {
                import("vendor/t-display-s3-amoled.stl");
                // The STEP models the display flex unfolded 20 mm past the board;
                // in the instrument it folds under, so it is clipped for drawing.
                translate([-1, -1.2, -2]) cube([28, 61, 9]);
            }
}

module tail_equipment() {
    // Carrier and the Matrix hung under it.
    P(C_PCB) translate([carrier_x0, W / 2 - boards_carrier_w / 2, boards_carrier_z]) cube([boards_carrier_l, boards_carrier_w, switch_pcb_t]);
    P([0.10, 0.10, 0.12]) translate([matrix_xy[0], matrix_xy[1], z_floor + 2 + 0.8])
        cube([boards_matrix_board, boards_matrix_board, 1.6], center = true);
    P(C_LED) translate([matrix_xy[0], matrix_xy[1], z_floor + 2 - 0.3])
        cube([boards_matrix_emitters, boards_matrix_emitters, 0.6], center = true);
    P(C_DIFFUSER) translate([0, 0, z_floor]) linear_extrude(1) diffuser_2d();
    // Tail backplate and the etherCON body behind it.
    P(C_ALU) translate([x_in1 - hardware_backplate_t, 0, 0]) rotate([90, 0, 90])
        linear_extrude(hardware_backplate_t) tail_backplate_2d();
    P(C_CONN) translate([L, ec_c[0], ec_c[1]]) rotate([0, -90, 0]) {
        cylinder(d = ethercon_body_d, h = ethercon_depth);
        translate([0, 0, -2]) linear_extrude(2) square([ec_fl[1], ec_fl[0]], center = true);
    }
    P(C_PCB) translate([x_in1 - 20, usb_c[0], z_floor + 1.6]) cube([20, 9, 1.6], center = false);
}

module led_strips() {
    for (s = [0, 1]) {
        y = s == 0 ? u_y0 + lighting_strip_gap : W - u_y0 - lighting_strip_gap - 1;
        P(C_LED) translate([(L - 420) / 2, y, z_floor + cavity_h / 2 - lighting_strip_w / 2])
            cube([420, 1, lighting_strip_w]);
    }
}

module hardware_3d() {
    // Fasteners: M3 socket caps from the bottom face into the plate.
    for (f = fasteners()) P(C_STEEL) translate([f[0], f[1], -explode]) {
        translate([0, 0, hardware_fastener_cbore_depth - 3]) cylinder(d = 5.5, h = 3);
        cylinder(d = 3, h = z_plate_top - 0.4 + explode * 2);
    }
    // U-bolt: loop below, legs through the floor to the backing plate.
    P(C_STEEL) translate([0, 0, -explode]) {
        for (u = ubolt_legs()) translate([u[0], u[1], -hardware_ubolt_drop + hardware_ubolt_span / 2])
            cylinder(d = hardware_ubolt_rod_d, h = z_floor + hardware_backplate_t + 6 + hardware_ubolt_drop - hardware_ubolt_span / 2);
        translate([ubolt_c[0], ubolt_c[1], -hardware_ubolt_drop + hardware_ubolt_span / 2]) rotate([-90, 0, 0])
            rotate_extrude(angle = 180) translate([hardware_ubolt_span / 2, 0]) circle(d = hardware_ubolt_rod_d);
    }
    lam(z_floor, hardware_backplate_t, C_ALU, false) ubolt_backplate_2d();
    lam(-1.5 - explode, 1.5, C_ACRYLIC, false) service_cover_2d();
}

module assembly() {
    if (show_u) u_channel();
    if (show_caps) caps();
    if (show_lid) lid(explode);
    if (show_keys) { keys_3d(); thumb_plates_3d(); }
    if (show_boards) { cluster_boards(); display_board(); tail_equipment(); }
    if (show_strips) led_strips();
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

    drc(slack >= 0, "length budget closes (ADR 0009 table)", slack,
        str("mm of slack, assigned to '", layout_slack_to, "'"));
    // Each run's end keys put half a cap into the neighbouring band - the
    // ADR 0009 table counts runs centre to centre.
    lh = xs(cluster_keys("left_hand")); rh = xs(cluster_keys("right_hand"));
    echo("DRC", "INFO", "oak top thickness (flush at full travel)", oak_top_t,
         "mm = keycap_top_above_seat - total_travel; keycap height is tbd, so this is too");
    drc(undef, "key cap stands proud of the top face at rest", switch_total_travel, "mm = the travel");
    drc(stack_cap_clear * 2 >= 0.015 * (switch_keycap + 2 * stack_cap_clear), "cap hole clearance beats oak cross-grain movement across the hole",
        stack_cap_clear, str("mm per side vs ", 0.015 * (switch_keycap + 2 * stack_cap_clear), " mm of movement at 1.5 % (ADR 0009)"));
    d_gap = (min(rh) - max(lh)) - switch_keycap;
    drc(undef, "inter-hand gap between caps", d_gap, "mm of clear band for the U-bolt and right thumb rest");
    d_uv = min([for (u = ubolt_legs()) min([for (k = bottom_keys) norm(key_xy(k) - u)])]) - hardware_ubolt_rod_d / 2 - (switch_keycap / 2 + thumb_recess_clear) * sqrt(2);
    drc(d_uv >= 2, "U-bolt legs clear of the thumb recesses", d_uv, "mm, worst case");

    // Everything cut through the oak bottom, pairwise: [name, centre, size].
    rc = switch_keycap + 2 * thumb_recess_clear;
    feats = concat([for (k = bottom_keys) [k[0], key_xy(k), [rc, rc]]],
                   [for (i = [0 : 2]) [str("spare ", i + 1), spare_xy[i], [rc, rc]]],
                   [["matrix window", matrix_xy, [openings_matrix_window, openings_matrix_window]],
                    ["service opening", service_xy, [openings_service_cover_l, openings_service_cover_w]],
                    ["display", disp_c, [disp_board[0] + 1, disp_board[1] + 1]],
                    ["U-bolt", ubolt_c, [hardware_ubolt_span + hardware_ubolt_rod_d, hardware_ubolt_rod_d]]],
                   [for (i = [0 : len(fasteners()) - 1]) [str("M3 #", i + 1), fasteners()[i], [hardware_fastener_cbore_d, hardware_fastener_cbore_d]]]);
    function gap(a, b) = max(abs(a[1][0] - b[1][0]) - (a[2][0] + b[2][0]) / 2,
                             abs(a[1][1] - b[1][1]) - (a[2][1] + b[2][1]) / 2);
    clashes = [for (i = [0 : len(feats) - 1], j = [i + 1 : 1 : len(feats) - 1])
               if (gap(feats[i], feats[j]) < 3) str(feats[i][0], " / ", feats[j][0], " ", gap(feats[i], feats[j]))];
    drc(len(clashes) == 0, "oak-bottom cuts at least 3 mm apart (display, thumb recesses, spares, window, service, U-bolt, counterbores)",
        clashes, "pairs closer than 3 mm, with the web between them (negative = overlap)");
    edge = min([for (f = feats) min(f[1][1] - f[2][1] / 2 - u_y0, W - u_y0 - f[1][1] - f[2][1] / 2)]);
    drc(edge >= 2, "oak-bottom cuts inside the U", edge, "mm, smallest web to the inside of a side");

    // Z stack
    drc(cavity_h > 0, "cavity height", cavity_h, "mm between the key plate and the oak bottom");
    z_pole = z_plate_top - switch_pole_tip_below_seat;
    drc(undef, "top switch pole tip below the lid", z_lid_bot - z_pole, "mm into the cavity");
    z_pcb_bot = z_plate_top - switch_pcb_below_seat - switch_pcb_t;
    drc(boards_carrier_z + switch_pcb_t < z_pcb_bot, "carrier clears the top cluster boards", z_pcb_bot - boards_carrier_z - switch_pcb_t,
        "mm between the carrier's top face and the cluster boards' underside, for components on both");
    dz_disp = boards_display_recess + 6.6;
    drc(undef, "display board height above the floor", dz_disp - z_floor,
        "mm it stands into the cavity (6.6 = the vendor STEP's full stack); keep the thumb plate and looms off it");
    echo("DRC", "INFO", "oak bottom thickness (thumb keys flush at full travel)", oak_bottom_t,
         "mm, the same rule as the oak top; thumb caps stand proud of the bottom face by the travel at rest");
    th_pole = z_floor + switch_pole_tip_below_seat;
    drc(undef, "thumb switch pole tip height in the cavity", th_pole, "mm above the bottom face");

    // Carrier
    drc(boards_carrier_w <= u_w - 2 * (lighting_strip_gap + 1), "carrier fits between the LED strips",
        u_w - 2 * (lighting_strip_gap + 1) - boards_carrier_w, "mm spare across");
    drc(boards_carrier_z + switch_pcb_t < z_lid_bot, "carrier under the lid", z_lid_bot - boards_carrier_z - switch_pcb_t,
        "mm of component height above the carrier");
    rt_top = z_floor + switch_pole_tip_below_seat;
    rt_in = max([for (k = cluster_keys("right_thumb")) key_xy(k)[0]]) > carrier_x0;
    drc(!rt_in || boards_carrier_z > rt_top, "carrier clears the right-thumb switch bodies", boards_carrier_z - rt_top, "mm");

    // Tail face
    ec_in = x_in1 - (ethercon_depth - ends_tail_cap_t);
    drc(carrier_x1 < ec_in, "carrier clears the etherCON body", ec_in - carrier_x1, "mm along X");
    ec_lo = ec_c[1] - ethercon_body_d / 2; ec_hi = ec_c[1] + ethercon_body_d / 2;
    drc(ec_lo >= z_floor && ec_hi <= z_lid_bot, "etherCON body inside the cavity height",
        [ec_lo, ec_hi, z_floor, z_lid_bot], "body Z range vs cavity Z range; outside = through-cuts in the oak at the tail");
    panel = ends_tail_cap_t + hardware_backplate_t;
    drc(panel <= ethercon_max_panel_t, "etherCON panel stack within the connector's maximum",
        panel, str("mm (tail cap + backplate) vs ", ethercon_max_panel_t, " max for the NE8FDP"));
    fl_margin = (T - ec_fl[1]) / 2;
    drc(fl_margin >= 5, "etherCON flange margin on the tail face", fl_margin, "mm above and below (ADR 0009: 6.00 rotated)");
    usb_x = matrix_xy[0] + boards_matrix_board / 2;
    drc(x_in1 - usb_x < 5, "Matrix USB-C at the tail face (ADR 0009: 'Keep that edge of the board at the tail')",
        x_in1 - usb_x, "mm from the board edge to the tail cap; more than a few = a panel-mount USB-C extension");
    beside = u_w - (ec_c[0] - u_y0 + ethercon_body_d / 2);
    drc(beside >= boards_matrix_board + 1, "room beside the etherCON body for the Matrix board at the tail",
        beside, str("mm across, vs ", boards_matrix_board, " board"));

    // Plate
    drc(undef, "M3 thread engagement in the key plate", plate_thickness,
        "mm of aluminium = ~2 threads at 0.5 pitch [calc]; plain tapping will strip, so the BOM's 'insert or tapped boss' is the only option");
    drc(min([for (f = fasteners()) min([for (k = top_keys) norm(key_xy(k) - f)])]) > plate_cutout / 2 * sqrt(2) + 3,
        "fasteners clear of the top switch cutouts",
        min([for (f = fasteners()) min([for (k = top_keys) norm(key_xy(k) - f)])]), "mm, centre to nearest key centre");
}

// ============================================================ dispatch ====
module part_2d(p) {
    if (p == "plate_top") plate_top_2d();
    else if (p == "oak_top") oak_top_2d();
    else if (p == "oak_bottom") oak_bottom_2d();
    else if (p == "thumb_plate") thumb_plate_both_2d();
    else if (p == "side_outer") side_outer_2d();
    else if (p == "side_inner") side_inner_2d();
    else if (p == "mouth_cap") mouth_cap_2d();
    else if (p == "tail_cap") tail_cap_2d();
    else if (p == "tail_backplate") tail_backplate_2d();
    else if (p == "ubolt_backplate") ubolt_backplate_2d();
    else if (p == "diffuser") diffuser_2d();
    else if (p == "service_cover") service_cover_2d();
    else assert(false, str("unknown part ", p));
}

if (!figure) {
    if (part == "assembly") assembly();
    else if (part == "drc") drc_report();
    else part_2d(part);
}
