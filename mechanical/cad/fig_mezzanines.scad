// Figure source: included into, never used by, woody_body.scad - imports
// resolve against the top-level file, which is why figures sit beside it.
// The two mezzanines that replace the carrier, picked out: the lid off,
// the mezzanines, their standoffs, parts, stacking headers and flat-flex
// links in bright yellow, everything else faded, each labelled from the
// same variables that place it. fig_view = "plan" is the labelled top view;
// "3d" is a perspective with only the title.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
show_lid = false;
origin = "centre";
fig_view = "plan";
highlight = concat(
    [for (sd = ["left", "right"]) each [str("mezzanine ", sd), str("parts mezzanine ", sd),
                                        for (i = [1 : 4]) str("standoff ", sd, " ", i)]],
    ["tall parts mezzanine left", "tall parts mezzanine right", "breath sensor", "ZIF link left", "ZIF link right", "ZIF display link",
     "FFC between the hands", "FFC to the display",
     "J-STACK left_thumb to left_hand", "J-STACK right_thumb to right_hand"]);
$k = 3;
module fig() {
    assembly();
    z = T + 4;
    s = 4.2;
    top = W + 8;
    bot = -10;
    y = mezz_y();
    // Outlines traced on top: from above, the mezzanines are under the key boards.
    for (x = [mz_l, mz_r]) color("DarkGoldenrod") translate([0, 0, z - 0.2]) linear_extrude(0.1) difference() {
        translate([x[0], y[0]]) square([x[1] - x[0], mezz_w]);
        translate([x[0] + 0.8, y[0] + 0.8]) square([x[1] - x[0] - 1.6, mezz_w - 1.6]);
    }
    if (fig_view == "plan") {
        s2 = s * 0.85;
        // Callouts in fixed rows above and below the body, ordered so that no
        // leader crosses another label.
        t1 = top; t2 = top + 10; b1 = bot; b2 = bot - 10;
        callout([zif_disp[0], zif_disp[1], z], [zif_disp[0] - 2, t1, z], "flat flex to the display", size = s2, halign = "right");
        callout([(zif_link[0][0] + zif_link[1][0]) / 2, zif_link[0][1], z], [(zif_link[0][0] + zif_link[1][0]) / 2 + 2, t1, z], "flat flex between the hands", size = s2);
        so = standoffs(stack_pairs[0]);
        if (len(so) > 0) callout(concat(so[len(so) - 1], z), [so[len(so) - 1][0] + 4, t1, z], "standoffs off the oak", size = s2);
        sp = spacers(stack_pairs[1]);
        callout(concat(sp[len(sp) - 1], z), [sp[len(sp) - 1][0] - 2, t2, z], "spacers onto the thumb board", size = s2, halign = "right");
        callout(concat(tall_c[1], z), [tall_c[1][0] - 8, t2, z], "regulator + bulk caps", size = s2);
        callout(concat(tall_c[0], z), [tall_c[0][0] - 2, b1, z], "regulator + bulk caps", size = s2, halign = "right");
        callout(concat(stack_c(stack_pairs[1]), z), [stack_c(stack_pairs[1])[0] + 2, b1, z], "stacking header LT-LH", size = s2);
        callout(concat(stack_c(stack_pairs[0]), z), [stack_c(stack_pairs[0])[0] + 2, b1, z], "stacking header RT-RH", size = s2);
        callout(concat(sensor_c, z), [sensor_c[0] + 2, b2, z], "breath sensor", size = s2);
        label([0, b2 - 14, z], str("LEFT mezzanine ", round(mz_l[1] - mz_l[0]), " x ", mezz_w, ": display power + link, LED-strip drive"), size = s2, halign = "left");
        label([0, b2 - 24, z], str("RIGHT mezzanine ", round(mz_r[1] - mz_r[0]), " x ", mezz_w, ": breath, umbilical, SPI out, Matrix power"), size = s2, halign = "left");
        label([L, b2 - 14, z], "NO CARRIER: two mezzanines, each between", size = s2, halign = "right");
        label([L, b2 - 24, z], "a thumb board and the key board above it", size = s2, halign = "right");
    } else
        label([(mz_l[0] + mz_r[1]) / 2, W + 14, z], "MEZZANINES (yellow) - no carrier", size = s * 1.4, c = "Black");
}
at_origin() fig();
