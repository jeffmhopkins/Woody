// Figure source: included into, never used by, woody_body.scad - imports
// resolve against the top-level file, which is why figures sit beside it.
// The centre board - the one flat board between the thumb boards and the
// key boards that carries the carrier's circuits - picked out: the lid off,
// the board, its parts, the stacking headers, standoffs and the breath
// sensor in bright yellow, everything else faded, each
// labelled from the same variables that place it. fig_view = "plan" is the
// labelled view from above; "3d" is a perspective with only the title.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
show_lid = false;
origin = "centre";
fig_view = "plan";
// A literal list: an override is evaluated where the model first assigns
// highlight, before the model's own variables exist.
highlight = ["centre board", "parts centre board", "tall parts centre board", "breath sensor",
             "J-STACK right_thumb to right_hand", "J-STACK left_thumb to left_hand",
             "centre board standoff 1", "centre board standoff 2", "centre board standoff 3",
             "centre board standoff 4", "centre board standoff 5", "centre board standoff 6"];
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
        callout([tall_c[0][0], tall_c[0][1], z], [tall_c[0][0] - 2, top, z], "regulator + bulk caps", size = s2, halign = "right");
        callout([stack_x(stack_pairs[1]), stack_y, z], [stack_x(stack_pairs[1]) - 2, bot, z], "stacking header LT-LH", size = s2, halign = "right");
        callout([sensor_c[0], sensor_c[1], z], [sensor_c[0] + 2, bot, z], "breath sensor (gap)", size = s2);
        callout([stack_x(stack_pairs[0]), stack_y, z], [stack_x(stack_pairs[0]) + 16, bot - 10, z], "stacking header RT-RH", size = s2);
        callout([cb_standoffs[0][0], cb_standoffs[0][1], z], [cb_standoffs[0][0] - 2, bot - 10, z], "standoffs / spacers", size = s2, halign = "right");
        label([0, bot - 24, z], str("CENTRE BOARD ", round(cb_x[1] - cb_x[0]), " x ", cb_y[1] - cb_y[0], " mm, between the thumb boards and the key boards"),
              size = s2, halign = "left");
        label([0, bot - 34, z], str(cb_room, " mm for parts under the keys, ", gap_room, " mm in the gap between the hands"), size = s2, halign = "left");
    } else
        label([L / 2, W + 14, z], "CENTRE BOARD (yellow)", size = s * 1.4, c = "Black");
}
at_origin() fig();
