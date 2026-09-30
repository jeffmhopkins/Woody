// The panel drawing, from the front: every cut, every centre, the legend
// zones (ADR 0024) and the reach of the screw hardware along its slots.
// Drawn from the same lists the DRC measures, so the drawing cannot show a
// layout the report did not check.
include <module.scad>
use <lib/annot.scad>
figure = true;
$k = 1.2;
Z = 0.2;                       // drawing convention: layers stacked for the orthographic camera

color(C_ALU) linear_extrude(Z) panel_2d();
// The umbilical's drop zone (ADR 0024 point 11): the NE8MX's grip and the
// strip it and its cable hang in, clipped to the panel. No control may be in it.
color([0.95, 0.55, 0.15, 0.30]) translate([0, 0, 1.5 * Z]) linear_extrude(0.05) intersection() {
    union() { translate(ec) circle(d = ethercon_cable_d); translate([ec[0] - ethercon_cable_d / 2, 0]) square([ethercon_cable_d, ec[1]]); }
    square([W, H]);
}
// Legend zones.
color([0.35, 0.55, 0.95, 0.45]) translate([0, 0, Z]) linear_extrude(0.05) legend_2d();
// What stands on the face: knob budget, plug grips, the NE8MX, washers' reach.
module ring(p, d, c) { color(c) translate([p[0], p[1], 2 * Z]) linear_extrude(0.05) difference() { circle(d = d); circle(d = d - 0.35); } }
for (p = pots) { ring(p, knob_d_max, "DimGray"); ring(p, knob_d, "Black"); }
for (j = jacks) ring(j[1], jack_plug_d, "SeaGreen");
ring(ec, ethercon_cable_d, "SeaGreen");
for (m = mounts) color([0.9, 0.3, 0.2, 0.35]) translate([m[0], m[1], Z]) linear_extrude(0.05)
    hull() for (s = [-1, 1]) translate([s * panel_slot_travel / 2, 0]) circle(d = panel_washer_od);
color([0.95, 0.75, 0.2, 0.6]) translate([ec[0] - ethercon_tab_w / 2, ec[1] + ethercon_tab_bottom, Z]) cube([ethercon_tab_w, ethercon_tab_top - ethercon_tab_bottom, 0.05]);

// Names in the zones, shortened: "J-CV-PITCH legend" -> "PITCH".
function cat(v, i = 0) = i >= len(v) ? "" : str(v[i], cat(v, i + 1));
function sub(s, a, b) = b <= a ? "" : cat([for (i = [a : b - 1]) s[i]]);
function starts(s, p) = len(s) >= len(p) && sub(s, 0, len(p)) == p;
function unpre(s, ps) = len(ps) == 0 ? s : starts(s, ps[0]) ? sub(s, len(ps[0]), len(s)) : unpre(s, [for (i = [1 : 1 : len(ps) - 1]) ps[i]]);
function short(s) = let(t = len(s) > 7 && sub(s, len(s) - 7, len(s)) == " legend" ? sub(s, 0, len(s) - 7) : s) unpre(t, ["J-CV-", "POT-", "J-", "SW-"]);
for (l = legend) label([(l[1][1][0] + l[1][2][0]) / 2, (l[1][1][1] + l[1][2][1]) / 2, 3 * Z],
                       l[0] == "title" ? "TITLE" : short(l[0]), size = 1.3, c = "Navy");
// Centres and cuts.
module cdim(p, s, dx = 0, dy = 0, h = "center") label([p[0] + dx, p[1] + dy, 3 * Z], s, size = 1.25, halign = h);
for (j = jacks) cdim(j[1], str(j[1][0], ", ", j[1][1]), 0, -jack_plug_d / 2 - 1.0);
cdim([cx, jacks[0][1][1]], str("d", jack_hole_d), 0, 0);
for (i = [0 : 2]) cdim(pots[i], str(pots[i][0], ", ", pots[i][1]), 0, knob_d_max / 2 + 1.0);
cdim(pots[1], str("d", pot_hole_d), 0, 0);
cdim(ec, str(ec[0], ", ", ec[1]), 0, 1.5);
cdim(ec, str("bore d", ethercon_bore_d + ethercon_bore_clear), 0, -1.0);
cdim(ec, str("screws d", ethercon_hole_d, " at +/-", ethercon_hole_dx / 2), 0, -3.2);
label([ec[0], ec[1] + (ethercon_tab_bottom + ethercon_tab_top) / 2, 3 * Z], "PUSH tab", size = 1.0);
label([1, led[1] - 3.4, 3 * Z], str(led[0], ", ", led[1]), size = 1.05, halign = "left");
label([1, led[1] - 5.2, 3 * Z], str("d", led_hole_d), size = 1.05, halign = "left");
cdim(tog, str(tog[0], ", ", tog[1]), toggle_nut_d / 2 + 1, -3.2, "left");
cdim(tog, str("d", toggle_hole_d, " flat ", toggle_flat), toggle_nut_d / 2 + 1, -5.0, "left");
for (m = mounts) cdim(m, str(m[0], ", ", m[1]), m[0] < cx ? 5.5 : -5.5, 0, m[0] < cx ? "left" : "right");
// Overall.
dim([0, -6, 1], [W, -6, 1], str("W ", W, " (10HP)"), [0, -2.2, 0], size = 1.8);
dim([-6, 0, 1], [-6, H, 1], str("H ", H), [-2.6, 0, 0], size = 1.8);
dim([0, -11, 1], [mount_x[0], -11, 1], str(mount_x[0]), [0, -2.0, 0], size = 1.4);
dim([mount_x[0], -11, 1], [mount_x[1], -11, 1], str(panel_hole_n_hp, " HP = ", mount_x[1] - mount_x[0]), [0, -2.0, 0], size = 1.4);
label([cx, H + 8, 1], "MODULE PANEL - from the front, mm; 2 mm aluminium", size = 2.0);
label([cx, H + 4.5, 1], "blue: legend zones - green: plug grips, NE8MX - grey: 14 mm knob budget - red: washer reach", size = 1.1);
label([cx, H + 2.2, 1], "yellow: the NE8FAV's PUSH tab, in front of the panel - no slot (ADR 0024)", size = 1.1);
label([cx, -17, 1], "orange: the umbilical's drop zone - the NE8MX's grip and the strip its cable hangs in; no control in it", size = 1.1);
