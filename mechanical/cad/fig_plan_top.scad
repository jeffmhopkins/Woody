// Figure source: included into, never used by, woody_body.scad - imports
// resolve against the top-level file, which is why figures sit beside it.
// Plan from above, orthographic: where the length goes and the keys, drawn
// from the same parameters the parts are cut from, so the labels cannot
// disagree with the geometry.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
$k = 3;
origin = "centre";
module fig() {
assembly();
z = T + 12;
s = 5;
yb = -14;
// Where the length goes, band by band. Bands meet at key centres.
bands = [["mouth", 0, x_lh0], ["LH", x_lh0, x_gap0], ["gap", x_gap0, x_rh0],
         ["RH", x_rh0, x_tail0], ["tail", x_tail0, L]];
for (i = [0 : len(bands) - 1]) let(b = bands[i], y = yb - (i % 2) * 12) {
    dim([b[1], y, z], [b[2], y, z], str(b[0], " ", b[2] - b[1]), [0, -5, 0], size = s * 0.8);
    seg([b[1], 0, z], [b[1], y - 2, z], r = 0.05);
}
seg([L, 0, z], [L, yb - 14, z], r = 0.05);
dim([0, W + 12, z], [L, W + 12, z], str("overall length ", L, " (derived)"), [0, 6, 0], size = s);
dim([L + 12, 0, z], [L + 12, W, z], str("W ", W), [12, 0, 0], size = s);
for (k = top_keys) label([key_xy(k)[0], key_xy(k)[1] - 13, z], k[0], size = 3.5, c = "DarkRed");
label([L / 2, W + 30, z], keys_placed == len(keys) ? "LAYOUT FROM config/key-layout.yaml"
      : str("PROVISIONAL: ", len(keys) - keys_placed, " of ", len(keys), " keys unplaced - length derived from the provisional layout"),
      size = s, c = keys_placed == len(keys) ? "Black" : "DarkRed");
}
at_origin() fig();
