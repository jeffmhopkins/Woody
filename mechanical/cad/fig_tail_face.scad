// The tail face from outside: etherCON (rotated, ADR 0009), USB-C slot, and
// the margins the ADR argues from.
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
label([x, usb_c[0], usb_c[1] + 8], "USB-C (tbd)", view = "right", size = 1.8);
label([x, ec_c[0], ec_c[1]], str("bore ", ethercon_bore_d), view = "right", size = 1.8, c = "White");
}
at_origin() fig();
