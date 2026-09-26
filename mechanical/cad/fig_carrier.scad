// Figure source: included into, never used by, woody_body.scad - imports
// resolve against the top-level file, which is why figures sit beside it.
// The carrier picked out of the body: the lid off, the carrier and what is
// modelled on it in bright yellow, everything else faded, and each part
// labelled from the same variables that place it. fig_view = "plan" is the
// labelled top view; "3d" is a perspective with only the title.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
show_lid = false;
origin = "centre";
fig_view = "plan";
highlight = ["carrier", "parts carrier underside", "carrier tall parts", "breath sensor",
             "J-CHAIN carrier", "J-CHAIN carrier tails", "J-DISP carrier", "J-DISP carrier tails"];
$k = 3;
module fig() {
    assembly();
    z = T + 4;
    s = 4.2;
    cy = W / 2;
    top = W + 8;
    bot = -10;
    // The carrier's outline, traced on top: from above it is under the key boards.
    color("DarkGoldenrod") translate([0, 0, z - 0.2]) linear_extrude(0.1) difference() {
        translate([carrier_x0, cy - boards_carrier_w / 2]) square([boards_carrier_l, boards_carrier_w]);
        translate([carrier_x0 + 0.8, cy - boards_carrier_w / 2 + 0.8]) square([boards_carrier_l - 1.6, boards_carrier_w - 1.6]);
    }
    if (fig_view == "plan") {
        label([(carrier_x0 + carrier_x1) / 2, top + 20, z], str("CARRIER - ", boards_carrier_l, " x ", boards_carrier_w,
              " mm, a placeholder size, centred between the hands for now"), size = s * 1.2);
        callout([carrier_hdr[1][0], carrier_hdr[1][1], z], [carrier_x0 - 6, top + 6, z], "J-DISP: loom to the display", size = s, halign = "right");
        callout([carrier_hdr[0][0], carrier_hdr[0][1], z], [carrier_x1 + 6, top + 6, z], "J-CHAIN: loom to the keys", size = s);
        callout([sensor_c[0], sensor_c[1], z], [carrier_x0 - 6, bot, z], "breath sensor", size = s, halign = "right");
        callout([tall_c[0], tall_c[1] - boards_tall_w / 2 + 2, z], [carrier_x1 + 6, bot, z], "tall parts: 5 V bucks, bulk capacitors", size = s);
        label([(carrier_x0 + carrier_x1) / 2, bot - 12, z], "and on its underside: power entry, breath ADC, SPI out to the module, LED-strip drive", size = s);
        // Neighbours, for orientation.
        for (cl = ["left_hand", "right_hand"])
            label([mid_x(cl), bot - 26, z], cl == "left_hand" ? "left-hand keys, over it" : "right-hand keys, over it", size = s * 0.8, c = "DimGray");
        label([matrix_xy[0], bot - 26, z], "LED matrix", size = s * 0.8, c = "DimGray");
        label([disp_c[0], bot - 26, z], "display, underside", size = s * 0.8, c = "DimGray");
    } else
        label([(carrier_x0 + carrier_x1) / 2, W + 14, z], "CARRIER (yellow)", size = s * 1.4, c = "Black");
}
at_origin() fig();
