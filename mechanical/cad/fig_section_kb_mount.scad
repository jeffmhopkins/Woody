// Cross-section through a key board's corner mount (ADR 0020, Amendment 4):
// the left hand's tail stud, seen from the tail. Every level of the stack is
// labelled from the values it is computed from: the stud's head flush in the
// plate under the wood, the spacer and washer that set the board's depth, the
// board, and the nut under it. Drawing frame: (Y, Z).
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
cut = "x2d";
cut_key = "kb_mount";
assembly();
m = kb_mounts("left_hand")[2];
xr = m[1] + 9;
module lv(zv, s, dz = 0) {
    seg([m[1] + 3.5, zv, 1], [xr, zv + dz, 1], r = 0.03);
    label([xr + 0.5, zv + dz, 1], s, size = 0.6, halign = "left");
}
lv(T, str("top face ", T, " - unbroken"), 0.6);
lv(z_plate_top, str("FHL-M2.5-", hardware_kb_stud_l, " flush, seat ", z_plate_top), 0.2);
lv(z_plate_bot, str("plate under ", z_plate_bot, " (", plate_thickness, ")"), -0.6);
lv(z_plate_bot - hardware_kb_spacer_l, str("spacer ", hardware_kb_spacer_l, " + washer ", hardware_kb_washer_t), 0);
lv(kb_top, str("board top ", kb_top, " = seat - ", switch_pcb_below_seat), -1.0);
lv(kb_top - boards_key_board_t - hardware_kb_nut_m, str("M2.5 nut ", hardware_kb_nut_m, " under the ", boards_key_board_t, " board"), -0.4);
lv(kb_top - boards_key_board_t - kb_stud_below, str("stud ", kb_stud_below - hardware_kb_nut_m, " past the nut (min ", kb_stud_below + hardware_kb_stud_l_tol[0] - hardware_kb_nut_m, ")"), -0.6);
label([m[1] + 10, T + 3.5, 1], str("key-board mount, X = ", cut_pos(), " (LH tail), from the tail"), size = 0.6);
