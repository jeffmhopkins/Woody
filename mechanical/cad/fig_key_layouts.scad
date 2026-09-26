// Candidate top-key spacings side by side, to scale, from above. Each row is
// [name, lh_gaps, rh_gaps] - the same form as config/body.yaml's
// layout.lh_gaps / rh_gaps - so a row can be copied there unchanged. The
// first row is always the CURRENT config, so the figure cannot show a
// "current" that is not current. Caps are the MT165 outline; dashed boxes
// are the oak-top holes at the configured clearance.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
$k = 2;

options = [];          // set by outputs.yaml
row_h = 44;
hand_gap = 34;         // drawing space between the two hands, not the body's

module row(i, name, lg, rg) {
    y = -i * row_h;
    xl = [for (j = [0 : len(lg)]) cum(lg, j)];
    x0r = sum(lg) + hand_gap;
    xr = [for (j = [0 : len(rg)]) x0r + cum(rg, j)];
    xs_all = concat(xl, xr);
    color([0.71, 0.53, 0.33]) translate([-20, y - 14, -1]) cube([max(xs_all) + 40, 28, 1]);
    for (x = xs_all) {
        color([0.93, 0.91, 0.86]) translate([x, y, 0]) linear_extrude(1.5) square(switch_keycap, center = true);
        color([0.3, 0.3, 0.3]) translate([x, y, 0.1]) linear_extrude(1.45)
            difference() { square(switch_keycap + 2 * stack_cap_clear, center = true); square(switch_keycap + 2 * stack_cap_clear - 0.5, center = true); }
    }
    for (j = [0 : len(lg) - 1]) label([(xl[j] + xl[j + 1]) / 2, y + 12, 2], str(lg[j]), size = 3.2);
    for (j = [0 : len(rg) - 1]) label([(xr[j] + xr[j + 1]) / 2, y + 12, 2], str(rg[j]), size = 3.2);
    for (j = [0 : len(lg)]) label([xl[j], y, 2], str("LH", j + 1), size = 2.6, c = "DarkRed");
    for (j = [0 : len(rg)]) label([xr[j], y, 2], str("RH", j + 1), size = 2.6, c = "DarkRed");
    label([-24, y, 2], name, size = 3.6, halign = "right");
    label([max(xs_all) + 24, y, 2], str("LH ", sum(lg), " + RH ", sum(rg), " = ", sum(lg) + sum(rg), " mm"), size = 3.2, halign = "left");
}

all = concat([["now in config/body.yaml", layout_lh_gaps, layout_rh_gaps]], options);
for (i = [0 : len(all) - 1]) row(i, all[i][0], all[i][1], all[i][2]);
label([sum(layout_lh_gaps) + hand_gap / 2, row_h * 0.62, 2],
      "gaps key centre to key centre, mm - hands drawn closer together than on the body", size = 3.2);
