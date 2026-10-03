// Figure source: included into, never used by, woody_body.scad - imports
// resolve against the top-level file, which is why figures sit beside it.
// The main board - the one long board at the thumb level that carries the
// thumb switches and everything the carrier did (ADR 0017) - picked out: the
// oak top and key plate off, the board, its parts, the LED row, the key
// boards' ribbons, its mounts and the breath sensor in bright yellow, everything else faded,
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
highlight = ["main board", "parts main board", "tall parts main board", "breath sensor", "LED row",
             "J-CHAIN left_hand main board", "J-CHAIN right_hand main board", "IDC plug left_hand main board", "IDC plug right_hand main board",
             "ribbon left_hand", "ribbon right_hand",
             "main board stud*", "main board spacer*", "main board nut*", "column standoff*"];
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
        callout([gap_x[0] + 10, W / 2, z], [gap_x[0] + 12, bot - 10, z], str("LEDs (", lighting_led_count, ", one in the tail corner) - light both sides"), size = s2);
        callout([tall_c[0][0], tall_c[0][1], z], [tall_c[0][0] - 2, top, z], "regulator + bulk caps", size = s2, halign = "right");
        callout([sensor_c[0], sensor_c[1], z], [sensor_c[0] - 2, top, z], "breath sensor (mouth end)", size = s2, halign = "left");
        callout([mb_chain("left_hand")[0], chain_y, z], [mb_chain("left_hand")[0] + 2, bot, z], "ribbon to the LH key board", size = s2);
        callout([mb_chain("right_hand")[0], chain_y, z], [mb_chain("right_hand")[0] + 2, bot, z], "ribbon to the RH key board", size = s2);
        callout([cb_standoffs[0][0], cb_standoffs[0][1], z], [cb_standoffs[0][0] + 2, bot - 10, z], "columns and mounts, on the bottom plate", size = s2);
        label([0, bot - 24, z], str("MAIN BOARD ", round(cb_x[1] - cb_x[0]), " x ", cb_y[1] - cb_y[0],
              " mm - the thumb switches, both thumb registers and the carrier circuits, one board"), size = s2, halign = "left");
        label([0, bot - 34, z], str(cb_room, " mm for parts under the keys, ", gap_room, " mm where no key board is overhead"), size = s2, halign = "left");
    } else
        label([L / 2, W + 14, z], "MAIN BOARD (yellow)", size = s * 1.4, c = "Black");
}
at_origin() fig();
