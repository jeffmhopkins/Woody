// The underside, orthographic, seen from below: thumb keys, spares, U-bolt,
// matrix window, service cover and the six fasteners.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
$k = 3;
origin = "centre";
module fig() {
assembly();
z = -30;
module lb(p, s, c = "Black") translate([0, 0, z]) mirror([0, 1, 0]) label([p[0], -p[1], 0], s, size = 3.5, c = c);
for (k = bottom_keys) lb(key_xy(k) + [0, 12], k[0], "DarkRed");
for (i = [0 : 2]) lb(spare_xy[i] + [0, 12], str("spare ", i + 1), "MediumVioletRed");
lb(ubolt_c + [0, -16], "U-bolt");
lb(matrix_xy + [0, 18], "matrix window");
lb(disp_c + [0, 18], "display");
lb(service_xy + [0, -12], "service cover");
for (i = [0 : len(fasteners()) - 1]) lb(fasteners()[i] + [0, fasteners()[i][1] > W / 2 ? 8 : -8], str("M3 #", i + 1));
}
at_origin() fig();
