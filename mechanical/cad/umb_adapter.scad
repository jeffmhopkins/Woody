// THE UMBILICAL ADAPTER'S BOARD (hardware/boards/umb-adapter), from the body
// model: its outline and where its two connectors stand. Nothing here draws
// the adapter afresh; every number is woody_body.scad's.
//
//   adapter = "outline"   the board's outline, 2D (umb-adapter.dxf)
//   adapter = "geom"      echo only (umb-adapter-geometry.echo; tools/pcb_adapter.py reads it)
//
// ITS FRAME. The adapter stands across the body, parallel to the tail cap. Its
// drawing's two axes are the body's y (across, from the near side) and z (up
// from the oak bottom's outside face): the board seen from the tail, the
// etherCON's face toward the viewer, the far side on the right.
include <woody_body.scad>
figure = true;
adapter = "geom";

// The flange's outline, less a notch at each of the etherCON's two upper posts:
// their holes stand too near the upper edge to be drilled (ethercon.post_*).
module umb_adapter_2d() {
    assert(!ethercon_rotated, "the post notches are drawn for the latch-up connector");
    difference() {
        translate([ec_c[0] - ec_fl[0] / 2, ec_c[1] - ec_fl[1] / 2]) square(ec_fl);
        for (s = [-1, 1]) hull() for (up = [0, ec_fl[1]])
            translate([ec_c[0] + s * ethercon_post_dx / 2, ec_c[1] + ethercon_post_above + up]) circle(d = ethercon_post_d, $fn = 48);
    }
}

if (adapter == "outline") umb_adapter_2d();
else {
    // the board's thickness, and which face is which
    echo("PCB", "umb", "board", "thickness", boards_umb_adapter_t, "side", "the etherCON on the face toward the tail; J-UMB's insulator against the rear face");
    // the etherCON's axis, and whether it is turned (ethercon.rotated)
    echo("PCB", "umb", "axis", "J-UMBILICAL-INST", ec_c[0], ec_c[1], ec_rot);
    // J-UMB's row, where the header on the main board holds its posts: the
    // row's two end pins (near side first) and the pitch
    echo("PCB", "umb", "row", "J-UMB", ec_c[0] - ju_l / 2 + 1.27, ju_row_z, ec_c[0] + ju_l / 2 - 1.27, ju_row_z, 2.54);
    // the rear face along the body: the main board's J-UMB insulator ends on it
    echo("PCB", "umb", "rear", "x", ua_x0);
    // what is round the board: the main board's top face, which the tongue
    // brings to the rear face, and the oak bottom's inside face under its edge
    echo("PCB", "umb", "level", "main board top", cb_top);
    echo("PCB", "umb", "level", "oak bottom", z_floor);
}
