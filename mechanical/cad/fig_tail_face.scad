// The tail face from outside: the etherCON (an NE8FAV, latch up, ADR 0021)
// centred in its recess, and the MIDI jack in a corner beside it (issue #45;
// owner, 2026-10-07: "TRS can go in corner"), with the margins the ADRs argue
// from. Seen from outside, +Y (the far side) is on the right.
include <woody_body.scad>
use <lib/annot.scad>
figure = true;
origin = "tail";
module fig() {
assembly();
x = L + 12;
module d(a, b, s, off) dim([x, a[0], a[1]], [x, b[0], b[1]], s, [0, off[0], off[1]], view = "right", size = 1.8);
fl_lo = ec_c[1] - ec_fl[1] / 2; fl_hi = ec_c[1] + ec_fl[1] / 2;
fl_l = ec_c[0] - ec_fl[0] / 2; fl_r = ec_c[0] + ec_fl[0] / 2;
d([fl_l - 4, 0], [fl_l - 4, fl_lo], str(fl_lo), [-4, 0]);
d([fl_l - 4, fl_hi], [fl_l - 4, T], str(T - fl_hi), [-4, 0]);
d([fl_l, -5], [fl_r, -5], str("flange ", ec_fl[0], " x ", ec_fl[1]), [0, -3]);
d([0, -14], [ec_c[0], -14], str(ec_c[0], " to the axis: centred"), [0, -3]);
d([0, -22], [W, -22], str("W ", W), [0, -3]);
// The lane the jack's body stands in, behind the face: flange edge to the side's inside face.
d([midi_lane[0], T + 5], [midi_lane[1], T + 5], str("lane ", midi_lane[1] - midi_lane[0], " behind the face"), [0, 3]);
d([midi_c[0], T + 1.5], [W, T + 1.5], str(W - midi_c[0]), [0, 1]);
d([W + 5, midi_c[1]], [W + 5, T], str(T - midi_c[1], " from the top"), [4, 0]);
label([x, ec_c[0], ec_c[1]], str("bore ", ethercon_bore_d), view = "right", size = 1.8, c = "White");
// The recess's floor is oak too: it leaves the connector its panel.
label([x, ec_c[0], ec_c[1] - ec_fl[1] / 2 - 3.5], str("recess ", ec_recess_d, " deep, ", ec_panel_t, " mm panel"), view = "right", size = 1.5);
label([x, 10, T + 6], str("MIDI jack (", midi_corner, "): counterbore ", round(midi_cbore_d * 10) / 10, " x ", midi_cbore_depth, " deep, ", midi_panel, " panel"), view = "right", size = 1.3);
}
at_origin() fig();
