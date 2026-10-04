// The tail face from outside: the etherCON (an NE8FAV, latch up, ADR 0021) in
// its recess, and the margins the ADRs argue from. Since issue #37 the face
// carries nothing else: the USB-C slot is gone, and the MIDI jack is in the
// oak bottom, in the lane beside the connector (its position dimensioned here).
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
origin = "tail";
module fig() {
assembly();
x = L + 12;
module d(a, b, s, off) dim([x, a[0], a[1]], [x, b[0], b[1]], s, [0, off[0], off[1]], view = "right", size = 1.8);
fl_lo = ec_c[1] - ec_fl[1] / 2; fl_hi = ec_c[1] + ec_fl[1] / 2;
d([ec_c[0] - ec_fl[0] / 2 - 4, 0], [ec_c[0] - ec_fl[0] / 2 - 4, fl_lo], str(fl_lo), [-4, 0]);
d([ec_c[0] - ec_fl[0] / 2 - 4, fl_hi], [ec_c[0] - ec_fl[0] / 2 - 4, T], str(T - fl_hi), [-4, 0]);
d([ec_c[0] - ec_fl[0] / 2, -5], [ec_c[0] + ec_fl[0] / 2, -5], str("flange ", ec_fl[0], " x ", ec_fl[1]), [0, -3]);
d([0, -14], [W, -14], str("W ", W), [0, -3]);
// The MIDI jack's place in the lane, seen through the face: across, from the side.
d([midi_xy[1], 0], [W, 0], str("MIDI jack (in the oak bottom) ", W - midi_xy[1], " from the side"), [0, -3]);
label([x, ec_c[0], ec_c[1]], str("bore ", ethercon_bore_d), view = "right", size = 1.8, c = "White");
// The recess's floor is oak too: it leaves the connector its panel.
label([x, ec_c[0], ec_c[1] - ec_fl[1] / 2 - 3.5], str("recess ", ec_recess_d, " deep, ", ec_panel_t, " mm panel"), view = "right", size = 1.5);
}
at_origin() fig();
