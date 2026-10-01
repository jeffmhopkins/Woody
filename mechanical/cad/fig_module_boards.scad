// Both boards, each seen from the panel (the frame's x and y): the jack board
// on the left, the main board to its right. Solid: what stands on the face
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
    fill(C_LED) r2(led - [led_smd[0], led_smd[1]] / 2, led + [led_smd[0], led_smd[1]] / 2);
    outline("Green") translate(led) circle(d = led_pipe_d);
    tag(led + [0, 3.2], "LED-PANEL", 1.1);
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
    tag([cx, -6], str("MAIN BOARD - ", b_x1 - b_x0, " x ", b_y1 - b_y0, ", ", mb_d, " behind the panel"), 1.5);
    tag([cx, -9], "solid: front face - outlined: rear face; orange: ribbon");
}
label([DX / 2 + cx, H + 6, 1], "THE MODULE'S TWO BOARDS, seen from the panel - mm, panel frame", size = 2.0);
