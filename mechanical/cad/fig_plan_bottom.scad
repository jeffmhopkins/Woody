// The underside, orthographic, seen from below: thumb keys, the left thumb's
// rest, U-bolt and the six fasteners.
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
lb(lt_rest_xy, "thumb rest", "SaddleBrown");
lb(ubolt_c + [0, -16], "U-bolt");
lb(rt_rest, "thumb rest", "SaddleBrown");
for (i = [0 : len(fasteners()) - 1]) lb(fasteners()[i] + [0, fasteners()[i][1] > W / 2 ? 8 : -8], str("M3 #", i + 1));
}
at_origin() fig();
