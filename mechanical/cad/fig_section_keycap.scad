// Cross-section through LH1 along the body (the plane y = LH1's centre), seen from
// the player's side: the MT165 cap on its KS-33, at rest, and in red where its
// shell is at full travel (switch.total_travel) - the question is whether the
// skirt, fully pressed, lands on the switch's cover or its collar. The
// switch is the mesh of the banked STEP (third-party, docs/reference/ks33-geometry.md);
// the cap's wall, top width and seated height are tbd (config/body.yaml switch.keycap_*).
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
cut = "y2d";
cut_key = "LH1";
assembly();
k = key_by_id("LH1");
kx = key_xy(k)[0];
P([0.85, 0.15, 0.15], false, "pressed cap LH1") translate([kx, key_xy(k)[1], z_plate_top]) cap_shell(switch_total_travel);
// Labels stacked above the caps (the gap beside the cap is over the next key's
// switch, where text is unreadable), each leader rising from its feature.
top = z_plate_top + switch_keycap_top_above_seat;
xr = kx + 10.5;
module lv(zv, s, n) {
    seg([kx + 8.6, zv, 1], [xr, top + 1.2 * n, 1], r = 0.03);
    label([xr + 0.3, top + 1.2 * n, 1], s, size = 0.5, halign = "left");
}
lv(top, str("cap top ", switch_keycap_top_above_seat, " above the seat (tbd)"), 5);
lv(z_plate_top + cap_sk, str("skirt, at rest: ", cap_sk), 4);
lv(z_plate_top + switch_housing_top_above_seat, str("housing top: ", switch_housing_top_above_seat), 3);
lv(z_plate_top + cap_sk - switch_total_travel, str("skirt, fully pressed (red): ", cap_sk - switch_total_travel), 2);
lv(z_plate_top, "seat = plate top", 1);
label([kx + 4, top + 8.2, 1],
      str("MT165 on KS-33 at LH1: skirt inside ", switch_keycap - 2 * switch_keycap_wall, " (tbd) round the cover's ", switch_cover_w), size = 0.6);
