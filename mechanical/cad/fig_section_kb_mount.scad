// Cross-section through a column (ADR 0024): the left hand's tail corner,
// seen from the tail. Every level of the stack is labelled from the values it
// is computed from, bottom to top: the stud pressed into the bottom plate, the
// spacer, the main board, the standoff threaded onto the stud and faced to the
// gap, the key board, the spacer that sets its depth, the key plate, and the
// screw down into the standoff, its head in a blind pocket in the oak top.
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
stud_in_nom = hardware_stud_l - (plate_thickness + hardware_kb_spacer_l + switch_pcb_t);
// a leader from the level zv at the column to a label placed at zl
module lv(zv, s, zl) {
    seg([x0, zv, 1], [xr, zl, 1], r = 0.04);
    label([xr - 0.5, zl, 1], s, size = 0.8, halign = "right");
}
lv(T, str("top face ", T, " - unbroken"), 40.5);
lv(z_plate_top + col_pocket_depth, str("pocket floor, ", T - z_plate_top - col_pocket_depth, " of wood over it"), 37.6);
lv(z_plate_top + hardware_col_screw_head_h, str("M2.5 x ", hardware_col_screw_l, " low head, ", hardware_col_screw_head_h, " tall"), 34.7);
lv(z_plate_top, str("key plate ", plate_thickness, ", seat ", z_plate_top), 31.8);
lv(z_plate_bot - hardware_kb_spacer_l / 2, str("spacer ", hardware_kb_spacer_l), 28.9);
lv(kb_top - boards_key_board_t / 2, str("key board ", boards_key_board_t, ", top ", kb_top, " = seat - ", switch_pcb_below_seat), 26.0);
lv(cb_top + col_standoff_l / 2, str("standoff faced to ", col_standoff_l, " (stock ", hardware_col_standoff_stock_l, ")"), 21.0);
lv(cb_top + stud_in_nom, str("stud end, ", stud_in_nom, " into the standoff"), 16.0);
lv(cb_z + switch_pcb_t / 2, str("main board ", switch_pcb_t, ", underside ", cb_z), 11.8);
lv(z_bplate_top + hardware_kb_spacer_l / 2, str("spacer ", hardware_kb_spacer_l), 8.9);
lv(z_floor + plate_thickness / 2, str("bottom plate ", plate_thickness, ", FHL-M2.5-", hardware_stud_l), 6.0);
lv(0, "bottom face 0", 2.0);
label([m[1] + 6, T + 3.2, 1], str("column at X = ", cut_pos(), " (LH tail corner), from the tail"), size = 0.9, halign = "right");
