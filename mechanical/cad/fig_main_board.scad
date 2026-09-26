// Figure source: included into, never used by, woody_body.scad - imports
// resolve against the top-level file, which is why figures sit beside it.
// The main board - the one long board at the thumb level that carries the
// thumb switches and everything the carrier did (ADR 0017) - picked out: the
// lid off, the board, its parts, the LED strip, the stacking headers,
// standoffs and the breath sensor in bright yellow, everything else faded,
// each labelled from the same variables that place it. fig_view = "plan" is
// the labelled view from above; "3d" is a perspective with only the title.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
show_lid = false;
origin = "centre";
fig_view = "plan";
// A literal list: an override is evaluated where the model first assigns
// highlight, before the model's own variables exist.
highlight = ["main board", "parts main board", "tall parts main board", "breath sensor", "LED strip",
             "J-STACK right_thumb to right_hand", "J-STACK left_thumb to left_hand",
             "main board standoff 1", "main board standoff 2", "main board standoff 3", "main board standoff 4",
             "main board standoff 5", "main board standoff 6", "main board standoff 7", "main board standoff 8"];
$k = 3;
module fig() {
    assembly();
    z = T + 4;
    s = 4.2;
    s2 = s * 0.85;
    top = W + 8;
    bot = -10;
    // The outline traced on top: from above, the board is under the key boards.
    color("DarkGoldenrod") translate([0, 0, z - 0.2]) linear_extrude(0.1) difference() {
        offset(0.4) cb_2d();
        offset(-0.4) cb_2d();
    }
    if (fig_view == "plan") {
        callout([gap_x[0] + 10, W / 2, z], [gap_x[0] + 12, bot - 10, z], "LED strip - lights both sides", size = s2);
        callout([tall_c[0][0], tall_c[0][1], z], [tall_c[0][0] - 2, top, z], "regulator + bulk caps", size = s2, halign = "right");
        callout([sensor_c[0], sensor_c[1], z], [sensor_c[0] - 2, top, z], "breath sensor (mouth end)", size = s2, halign = "left");
        callout([stack_x(stack_pairs[1]), stack_y, z], [stack_x(stack_pairs[1]) - 2, bot, z], "stacking header to LH", size = s2, halign = "right");
        callout([stack_x(stack_pairs[0]), stack_y, z], [stack_x(stack_pairs[0]) + 16, bot, z], "stacking header to RH", size = s2);
        callout([cb_standoffs[0][0], cb_standoffs[0][1], z], [cb_standoffs[0][0] + 2, bot - 10, z], "standoffs", size = s2);
        label([0, bot - 24, z], str("MAIN BOARD ", round(cb_x[1] - cb_x[0]), " x ", cb_y[1] - cb_y[0],
              " mm - the thumb switches, both thumb registers and the carrier circuits, one board"), size = s2, halign = "left");
        label([0, bot - 34, z], str(cb_room, " mm for parts under the keys, ", gap_room, " mm where no key board is overhead"), size = s2, halign = "left");
    } else
        label([L / 2, W + 14, z], "MAIN BOARD (yellow)", size = s * 1.4, c = "Black");
}
at_origin() fig();
