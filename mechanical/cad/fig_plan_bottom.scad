// The underside, orthographic, seen from below: thumb keys, the thumb rests
// and the U-bolt - the only hardware that shows (ADR 0025).
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
$k = 3;
origin = "centre";
module fig() {
assembly();
z = -30;
module lb(p, s, c = "Black") translate([0, 0, z]) mirror([0, 1, 0]) label([p[0], -p[1], 0], s, size = 3.5, c = c);
for (k = bottom_keys) lb(key_xy(k) + [0, key_xy(k)[1] < W / 2 - 1 ? -12 : 12], k[0], "DarkRed");
for (r = [[lt_rest_xy, layout_lt_rest_under], [rt_rest, layout_rt_rest_under]]) {
    lb(r[0] + [0, -3], "rest", "SaddleBrown");
    lb(r[0] + [0, 4], str("@", r[1]), "SaddleBrown");   // under that finger key
}
lb(ubolt_c + [0, -16], "U-bolt");
}
at_origin() fig();
