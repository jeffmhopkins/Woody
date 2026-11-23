// Cross-section through a column (ADR 0025): the left hand's tail corner,
// seen from the tail. Every level of the stack is labelled from the values it
// is computed from, bottom to top: the screw from the back, its flat head
// flush in a countersink in the oak bottom, the bottom plate, the spacer, the main board,
// the standoff faced to the gap, the key board, the spacer that sets its
// depth, the key plate with the stud pressed in flush from its top face, and
// the lid's magnet in its pocket in the oak top (ADR 0025, Amendment 2026-11-23).
// Drawing frame: (Y, Z).
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
cut = "x2d";
cut_key = "kb_mount";
assembly();
m = kb_mounts("left_hand")[2];
// labels to the left, outside the body, leaders from the column's left edge
x0 = m[1] - 3.2;
xr = -3;
stud_in_nom = hardware_stud_l - (plate_thickness + kb_gap + boards_key_board_t);
screw_in_nom = hardware_col_screw_l - oak_bottom_t - (plate_thickness + hardware_kb_spacer_l + switch_pcb_t);
// a leader from the level zv at the column to a label placed at zl
module lv(zv, s, zl) {
    seg([x0, zv, 1], [xr, zl, 1], r = 0.04);
    label([xr - 0.5, zl, 1], s, size = 0.8, halign = "right");
}
lv(T, str("top face ", T, " - unbroken"), 40.5);
lv(z_plate_top + col_pocket_depth, str("pocket floor, ", T - z_plate_top - col_pocket_depth, " of wood over it"), 37.6);
lv(z_plate_top + closure_magnet_recess + closure_magnet_h / 2, str("magnet ", closure_magnet_d, " x ", closure_magnet_h, " on the stud's head"), 34.7);
lv(z_plate_top, str("key plate ", plate_thickness, ", seat ", z_plate_top, ", FHL-M2.5-", hardware_stud_l), 31.8);
lv(z_plate_bot - hardware_kb_spacer_l / 2, str("spacer ", hardware_kb_spacer_l), 28.9);
lv(kb_top - boards_key_board_t / 2, str("key board ", boards_key_board_t, ", top ", kb_top, " = seat - ", switch_pcb_below_seat), 26.0);
lv(cb_top + col_standoff_l / 2, str("standoff faced to ", col_standoff_l, " (stock ", hardware_col_standoff_stock_l, ")"), 20.5);
lv(kb_top - boards_key_board_t - stud_in_nom, str("stud end, ", stud_in_nom, " into the standoff"), 23.5);
lv(cb_top + screw_in_nom, str("screw end, ", screw_in_nom, " into the standoff"), 16.0);
lv(cb_z + switch_pcb_t / 2, str("main board ", switch_pcb_t, ", underside ", cb_z), 11.8);
lv(z_bplate_top + hardware_kb_spacer_l / 2, str("spacer ", hardware_kb_spacer_l), 8.9);
lv(z_floor + plate_thickness / 2, str("bottom plate ", plate_thickness), 6.0);
lv(col_csk_depth / 2, str("M2.5 x ", hardware_col_screw_l, " flat head, flush"), 4.0);
lv(0, "bottom face 0", 2.0);
label([m[1] + 6, T + 3.2, 1], str("column at X = ", cut_pos(), " (LH tail corner), from the tail"), size = 0.9, halign = "right");
