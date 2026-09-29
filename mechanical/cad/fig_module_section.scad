// Side section through the module at the panel's centre (x = panel.w / 2):
// the NE8FAV's axis, the toggle, J-B2B-MOD and the middle pot. Laid flat as
// (depth from the panel's front face, y): the player is on the left, the case
// on the right. Every depth is labelled from the value it is computed from,
// and the Intellijel Palette's limit is drawn both ways the manual can be read.
include <module.scad>
use <lib/annot.scad>
figure = true;
cut = "x2d";
vendor = false;
show_rails = true;
assembly();

yb = -power_drop - 6;          // the dimension lines' baseline, below everything
$k = 1.4;
module depth_dim(u0, u1, row, s) {
    dim([u0, yb - row * 6, 1], [u1, yb - row * 6, 1], s, [0, -2.2, 0], size = 1.9);
}
module mark(u, s, c = "Black", top = H + 6) {
    seg([u, yb, 1], [u, top, 1], r = 0.08, c = c);
    label([u + 0.8, top + 1.5, 1], s, size = 1.8, halign = "left", c = c);
}
depth_dim(0, T, 0, str("panel ", T));
depth_dim(T, T + jb_d, 1, str("jack body ", jb_d));
depth_dim(T + jb_d, T + jb_d + boards_t, 0, str(boards_t));
depth_dim(T + jb_d + boards_t, T + mb_d, 2, str("standoff ", so_l));
depth_dim(T, T + mb_d, 3, str("NE8FAV setback ", mb_d));
depth_dim(T + mb_d + boards_t, T + depth_max_rear, 1, str("socket + ribbon ", depth_max_rear - mb_d - boards_t));
depth_dim(T, T + depth_max_rear, 4, str("deepest ", depth_max_rear, " behind the rear face"));
mark(T + case_depth_max, str("Palette ", case_depth_max, " (rear face)"), "Red");
mark(case_depth_max, str("...from the front face"), "OrangeRed", H + 12);
mark(-(knob_gap + knob_h), str("knob ", knob_gap + knob_h, " proud"), "DimGray", H + 18);
label([T + jb_d + boards_t / 2, H + 26, 1], "jack board", size = 2, halign = "center");
label([T + mb_d + boards_t / 2, H + 30, 1], "main board", size = 2, halign = "center");
label([T + 15, -power_drop - 1.5, 1], "ribbon to the bus board", size = 1.8, halign = "left");
label([20, H + 40, 1], str("SECTION AT x = ", cut_x(), " - depth from the panel's front face, mm"), size = 2.4, halign = "center");
