// The three boards, each seen from the panel (the frame's x and y): the jack
// board on the left, the main board in the middle, the iso board on the right. Solid: what stands on the face
// toward the panel. Outlined: what stands on the rear face. Drawn from the
// same lists the DRC and pcb-geometry.echo use.
include <module.scad>
use <lib/annot.scad>
figure = true;
$k = 1.2;
Z = 0.2;                       // drawing convention: layers stacked for the orthographic camera
DX = W + 22;                   // drawing convention: the main board's offset on the sheet

module r2(a, b) { translate(a) square(b - a); }
module fill(c) { color(c) translate([0, 0, 2 * Z]) linear_extrude(0.05) children(); }
module outline(c) { color(c) translate([0, 0, 3 * Z]) linear_extrude(0.05) difference() { offset(r = 0.25) children(); children(); } }
module tag(p, s, sz = 1.5) label([p[0], p[1], 4 * Z], s, size = sz);

// ---- jack board
color(C_PCB) linear_extrude(Z) jack_board_2d();
color([0.8, 0.8, 0.8, 0.5]) translate([0, 0, -Z]) linear_extrude(0.05) square([W, H]);   // the panel behind, for scale
for (j = jacks) { let(r = jack_body_rect(j[1])) fill(C_BLACK) r2(r[1], r[2]);
                  fill("Gold") for (i = [0 : 2]) translate([ju(j[1], jack_pins[i]), j[1][1]]) square([jack_pads[i][1], jack_pads[i][0]], center = true);
                  tag(j[1] + [0, jack_body_w / 2 + 1.4], j[0], 1.2); }
for (i = [0 : 2]) { fill(C_METAL) r2(pots[i] + [-pot_body[2] / 2, pot_body[0]], pots[i] + [pot_body[2] / 2, pot_body[1]]);
                    tag(pots[i] + [0, pot_body[0] - 1.6], layout_pots[i], 1.2); }
for (s = standoff_at) { fill(C_METAL) translate(s) circle(d = m3_head_d); tag(s + [0, -4.2], "standoff"); }
fill("Gold") r2(b2b_at - [b2b_w, b2b_l] / 2 - [1.27, 1.27], b2b_at + [b2b_w, b2b_l] / 2 + [1.27, 1.27]);
tag(b2b_at + [0, -b2b_l / 2 - 2.6], "J-B2B-MOD", 1.2);
// Below the jack board: what it now ends above (ADR 0024 point 15), outlined.
outline("DimGray") r2(tog - tog_body / 2, tog + tog_body / 2);
tag([cx, tog[1]], "SW-POWER (below)", 1.1);
outline("DimGray") r2(ec - fl / 2, ec + fl / 2);
tag(ec, "NE8FAV (below)", 1.3);
tag([cx, -6], str("JACK BOARD - ", b_x1 - b_x0, " x ", b_y1 - jb_y0, ", ", jb_d, " behind the panel"), 1.5);

// ---- main board
translate([DX, 0, 0]) {
    color(C_PCB2) linear_extrude(Z) main_board_2d();
    fill(C_EC) r2(ec - fl / 2, ec + fl / 2);
    tag(ec, "J-UMBILICAL (NE8FAV)");
    fill("Gold") r2(b2b_at - [b2b_w, b2b_l] / 2 - [1.27, 1.27], b2b_at + [b2b_w, b2b_l] / 2 + [1.27, 1.27]);
    for (s = standoff_at) fill(C_METAL) translate(s) circle(d = standoff_af / cos(30), $fn = 6);
    for (s = panel_standoff_at) { fill(C_METAL) translate(s) circle(d = standoff_af / cos(30), $fn = 6); tag(s + [0, 4.6], "to the panel", 1.1); }
    fill(C_NYLON) r2(hdr_rect[1], hdr_rect[2]);
    tag(hdr + [0, -led_header[1] / 2 - 1.4], "J-LED-PANEL", 1.1);
    tag(hdr + [-led_header_pitch / 2, 0], "1", 0.9);
    outline("Green") translate(led) circle(d = led_nut_d, $fn = 6);
    outline("Green") r2([led[0] - led_wire_d, hdr[1] + led_header[1] / 2], [led[0] + led_wire_d, led[1] - led_nut_d / 2]);
    tag(led + [0, led_nut_d / 2 + 1.2], "LED-PANEL (panel)", 1.1);
    outline(C_PCB) r2([b_x0, jb_y0], [b_x1, b_y1]);
    tag([cx, jb_y0 - 1.6], "the jack board, above", 1.1);
    // Rear face, outlined.
    outline("Red") r2(pw - [power_w, power_l] / 2, pw + [power_w, power_l] / 2);
    tag(pw + [0, power_l / 2 + 1.5], "J-PWR-EURO (rear)");
    tag(pw + [0, -power_l / 2 + 1.5], "-12 V");
    outline("DarkOrange") r2([pw[0] + power_socket_w / 2 - power_ribbon_w, b_y0], pw + [power_socket_w / 2, power_socket_l / 2]);
    for (i = [0 : len(tall_at) - 1]) let(t = tall_at[i])
        if (t[2] == "cap") outline("Blue") translate([t[0], t[1]]) circle(d = tall_cap_d);
        else outline("Blue") r2([t[0], t[1]] - [tall_trim[0], tall_trim[1]] / 2, [t[0], t[1]] + [tall_trim[0], tall_trim[1]] / 2);
    outline("DimGray") r2(tog - tog_body / 2, tog + tog_body / 2);
    tag(tog + [0, -tog_body[1] / 2 - 1.5], "SW-POWER lugs, in front");
    // The iso board behind, its spacers and J-B2B-ISO's insulator on the rear face.
    outline("Purple") polygon(ib_poly);
    tag([b_x0 + 9, iso_board_y1 - 1.6], "the iso board, behind", 1.1);
    outline("Red") r2(b2bi_rect[1], b2bi_rect[2]);
    tag(b2b_iso_at + [0, b2bi_w / 2 + 2.6], "J-B2B-ISO (rear)", 1.1);
    for (s = iso_board_standoff_at) outline("Purple") translate(s) circle(d = standoff_af / cos(30), $fn = 6);
    tag([cx, -6], str("MAIN BOARD - ", b_x1 - b_x0, " x ", b_y1 - b_y0, ", ", mb_d, " behind the panel"), 1.5);
    tag([cx, -9], "solid: front face - outlined: rear face; orange: ribbon");
}

// ---- iso board (ADR 0023 point 2, amended 2026-10-03): solid is its REAR face here, where its parts stand
translate([2 * DX, 0, 0]) {
    color(C_PCB2) linear_extrude(Z) iso_board_2d();
    fill(C_METAL) r2(iso_rect[1], iso_rect[2]);
    tag(iso_at, "U-ISO", 1.5);
    fill("Gold") for (q = iso_pins) translate(iso_at + q) circle(d = 2 * iso_pin_d);
    for (f = iso_filter) {
        if (f[2] == "can") fill(C_CAP) translate([f[0], f[1]]) circle(d = f[3]);
        else if (f[2] == "toroid") fill(C_BLACK) translate([f[0], f[1]]) circle(d = f[6]);
        else fill(C_BLACK) r2([f[0], f[1]] - [f[3], f[3]] / 2, [f[0], f[1]] + [f[3], f[3]] / 2);
        tag([f[0], f[1]], f[5], 1.0);
    }
    fill("Gold") r2(b2b_iso_at - [b2bi_l, b2bi_w] / 2 - [1.27, 1.27], b2b_iso_at + [b2bi_l, b2bi_w] / 2 + [1.27, 1.27]);
    tag(b2b_iso_at + [0, -b2bi_w / 2 - 2.6], "J-B2B-ISO", 1.1);
    for (s = iso_board_standoff_at) fill(C_METAL) translate(s) circle(d = m3_head_d);
    outline("Red") r2(pw - [power_w, power_l] / 2, pw + [power_w, power_l] / 2);
    tag(pw + [0, -power_l / 2 + 1.5], "J-PWR-EURO", 1.0);
    outline("DarkOrange") r2([fold[0], fold[1]], [fold[2], fold[3]]);
    for (i = [0 : len(tall_at) - 1]) let(t = tall_at[i])
        if (t[2] == "cap") outline("Blue") translate([t[0], t[1]]) circle(d = tall_cap_d);
        else outline("Blue") r2([t[0], t[1]] - [tall_trim[0], tall_trim[1]] / 2, [t[0], t[1]] + [tall_trim[0], tall_trim[1]] / 2);
    tag([cx, -6], str("ISO BOARD - ", b_x1 - b_x0, " x ", iso_board_y1 - ib_y0, ", ", mb_d + boards_t + ib_gap, " behind the panel"), 1.5);
    tag([cx, -9], "solid: rear face - outlined: the main board's rear-face parts beside it");
}
label([DX + cx, H + 6, 1], "THE MODULE'S THREE BOARDS, seen from the panel - mm, panel frame", size = 2.0);
