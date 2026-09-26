// Cross-section drawing through RH3, seen from the tail looking toward the
// mouthpiece (+Y to the right): every part
// cut by the plane X = RH3's centre, coloured, and the Z stack labelled with
// the levels it is computed from. Drawing frame: (Y, Z), flat at z = 0.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
cut = "x2d";
cut_key = "RH3";
show_strips = false;
assembly();
xr = -4;
module lv(zv, s, dz = 0) {
    seg([xr, zv + dz, 1], [0, zv, 1], r = 0.06);
    label([xr - 1, zv + dz, 1], s, size = 1.3, halign = "right");
}
lv(z_plate_top + switch_keycap_top_above_seat, str("cap top at rest ", z_plate_top + switch_keycap_top_above_seat, " (tbd)"));
lv(T, str("top face ", T, " = cap top pressed"), -1.2);
lv(z_plate_top, str("plate top = seat ", z_plate_top), 0.4);
lv(z_plate_bot, str("plate under = lid under ", z_plate_bot), -0.8);
lv(z_plate_top - switch_pole_tip_below_seat, str("pole tip ", z_plate_top - switch_pole_tip_below_seat), -1.6);

lv(z_floor, str("floor ", z_floor));
lv(0, "bottom face 0");
label([W / 2, -8, 1], str("cavity ", cavity_h, " x ", u_w, " mm   sides ", stack_side_t, " in ", stack_groove_depth, " mm grooves (tbd)"), size = 1.6);
label([W / 2, -11.5, 1], str("section at X = ", cut_pos, " (RH3), seen from the tail"), size = 1.4);
