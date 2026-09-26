// Figure source: included into, never used by, woody_body.scad - imports
// resolve against the top-level file, which is why figures sit beside it.
// The spine - the one board, on its edge down the side, that replaces the
// carrier - picked out: the lid off, the spine, its parts, headers,
// standoffs, the breath sensor and the display link in bright yellow,
// everything else faded, each labelled from the same variables that place
// it. fig_view = "side" is the labelled view square onto the spine's face;
// "3d" is a perspective with only the title.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
show_lid = false;
origin = "centre";
fig_view = "side";
// A literal list: an override is evaluated where the model first assigns
// highlight, before the model's own variables exist.
highlight = ["spine", "parts spine", "tall parts spine mouth", "tall parts spine tail", "breath sensor",
             "ZIF display link", "FFC to the display",
             "J-SPINE right_thumb", "J-SPINE right_hand", "J-SPINE left_thumb", "J-SPINE left_hand",
             "spine standoff 1", "spine standoff 2"];
$k = 3;
module fig() {
    assembly();
    s = 3.6;
    // Labels on a plane just inboard of the spine's parts, facing the camera,
    // which looks at the spine's face from the centre of the body.
    y = spine_y - ssg * (boards_tall_h + 8);
    v = ssg > 0 ? "front" : "back";
    zt = T + 6;
    zb = -8;
    if (fig_view == "side") {
        label([mean(spine_x), y, zt + 14], "THE SPINE: one board on its edge in the side channel, inboard of the LED strip", v, size = s * 1.15);
        label([mean(spine_x), y, zt + 6], str("one rectangle, ", round(spine_x[1] - spine_x[0]), " x ", spine_z[1] - spine_z[0],
              " mm, with a drop for the breath sensor"), v, size = s * 0.9);
        callout([conn_x("left_hand"), y, top_z - 1], [conn_x("left_hand") + 4, y, zt - 2], "header up to the LH key board", v, size = s * 0.85);
        callout([conn_x("right_hand"), y, top_z - 1], [conn_x("right_hand") + 4, y, zt - 2], "header up to the RH key board", v, size = s * 0.85);
        callout([conn_x("left_thumb"), y, thumb_z + 1], [conn_x("left_thumb") - 4, y, zb], "header down to LT", v, size = s * 0.85, halign = "right");
        callout([conn_x("right_thumb"), y, thumb_z + 1], [conn_x("right_thumb") + 4, y, zb], "header down to RT", v, size = s * 0.85);
        callout([zif_disp[0], y, zif_disp[1]], [zif_disp[0] - 6, y, zt - 2], "display link", v, size = s * 0.85, halign = "right");
        callout([tall_c[0][0], y, tall_c[0][1]], [tall_c[0][0] - 4, y, zb - 9], "display regulator + caps", v, size = s * 0.85, halign = "right");
        callout([tall_c[1][0], y, tall_c[1][1]], [tall_c[1][0] + 4, y, zb - 9], "Matrix regulator + caps", v, size = s * 0.85);
        callout([sensor_c[0], y, sensor_c[1]], [sensor_c[0] + 4, y, zb - 18], "breath sensor, far from the display", v, size = s * 0.85);
        label([mean(spine_x), y, zb - 28], "umbilical, SPI out, LED-strip drive and service header: SMT along the face; the Matrix pigtail and patch lead land at the tail end",
              v, size = s * 0.75, c = "DimGray");
    } else
        label([mean(spine_x), W + 14, T + 6], "THE SPINE (yellow) - one board on its edge", size = s * 1.6, c = "Black");
}
at_origin() fig();
