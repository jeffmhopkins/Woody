// THE PARTS AS THEY GO TO A SHOP (issue #42). The body model's own solids,
// one at a time, each moved into its own part frame, and the numbers a
// drawing of each needs - nothing here draws a part afresh, so a fabrication
// file cannot disagree with the model it came from.
//
//   fab = "oak_top" | "oak_bottom" | "mouth_cap" | "tail_cap"
//                         that solid, 3D, in its part frame (STL; STEP from it)
//   fab = "tail_cap_recess"   the tail cap's etherCON recess, 2D (a router
//                         pass, so not in tail-cap.dxf), in tail-cap.dxf's frame
//   fab = "geom"          echo only: every part's stock, its layers with
//                         their faces and depths, and its holes and hardware,
//                         in its part frame (tools/fab.py reads it)
//
// PART FRAMES. The oak panels: woody_body.scad's own (model XY minus
// [x_in0, 0]); z = 0 is the panel's bottom face - the oak top's underside,
// the oak bottom's outside face. The plates: the key plate's (model XY minus
// [plate_x0, plate_y0]), seen from above. The caps: their DXF's, X = model Y,
// Y = model Z, Z = through the cap - from its outer face for the mouth cap,
// from its inner face for the tail cap (so each DXF is the cap seen from the
// side its Z = 0 face is on: the mouth cap from outside, the tail cap from
// inside).
//
// No numbers here: every one is woody_body.scad's, from generated/params.scad.
include <woody_body.scad>
figure = true;
fab = "geom";

// (X, Y, Z) -> (Y, Z, X): a cap's frame from the model's
module cap_frame(x0) multmatrix([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -x0], [0, 0, 0, 1]]) children();

module fab_solid() {
    if (fab == "oak_top") translate([-x_in0, 0, -z_oak_top_bot]) lid();
    else if (fab == "oak_bottom") translate([-x_in0, 0, 0]) u_channel();
    else if (fab == "mouth_cap") cap_frame(0) caps();
    else if (fab == "tail_cap") cap_frame(x_in1) caps();
}
fab_ids = [["oak_top", "oak top"], ["oak_bottom", "oak bottom"], ["mouth_cap", "mouth cap"], ["tail_cap", "tail cap"]];
function fab_id(p) = [for (f = fab_ids) if (f[0] == p) f[1]][0];

// ---------------------------------------------------------------- echo ----
function sh(p, o) = [p[0] - o[0], p[1] - o[1]];
module stock(p, t, sz, faces) echo("FAB", p, "stock", t, sz[0], sz[1], faces);
// a layer: its cut file, the face it is cut from, its depth ("through" for the outline)
module layer(p, dxf, face, depth, what) echo("FAB", p, "layer", dxf, face, depth, what);
// a hole: what it is, its centre, diameter, depth from a face, and the BOM row that goes in it ("" for none)
module hole(p, what, c, d, face, depth, bom = "") echo("FAB", p, "hole", what, c[0], c[1], d, face, depth, bom);
module fab_geom() {
    o = [x_in0, 0];
    stock("oak_top", oak_top_t, [x_in1 - x_in0, W], ["underside", "playing face"]);
    layer("oak_top", "mechanical/export/oak-top.dxf", "", "through", "outline, cap slots, matrix window");
    layer("oak_top", "mechanical/export/oak-grooves.dxf", "underside", stack_groove_depth, "side grooves");
    layer("oak_top", "mechanical/export/oak-pockets.dxf", "underside", col_pocket_depth, "column screw head pockets" + (usb_pocket_need > 0 ? " and the recovery USB-C pocket" : ""));
    layer("oak_top", "mechanical/export/oak-inserts.dxf", "underside", hardware_mx_insert_l, "Matrix carrier insert holes");
    layer("oak_top", "mechanical/export/oak-relief.dxf", "underside", openings_matrix_relief_d, "relief over the Matrix");
    layer("oak_top", "mechanical/export/oak-rebates.dxf", "playing face", openings_matrix_acrylic_t, "matrix window rebate");
    layer("oak_top", "mechanical/export/oak-logo.dxf", "playing face", logo_depth, str("maker's mark etch, filled: ", logo_fill));
    for (m = columns()) hole("oak_top", "column screw head pocket", sh(m, o), hardware_col_pocket_d, "underside", col_pocket_depth);
    for (m = mx_mounts) hole("oak_top", "threaded insert hole", sh(m, o), hardware_mx_insert_hole, "underside", hardware_mx_insert_l, "MECH-MX-INSERT");

    stock("oak_bottom", oak_bottom_t, [x_in1 - x_in0, W], ["outside face", "inside face"]);
    layer("oak_bottom", "mechanical/export/oak-bottom.dxf", "", "through", "outline, thumb recesses, U-bolt and MIDI jack holes");
    layer("oak_bottom", "mechanical/export/oak-grooves.dxf", "inside face", stack_groove_depth, "side grooves");
    layer("oak_bottom", "mechanical/export/oak-bottom-pockets.dxf", "inside face", midi_cbore_depth, "MIDI jack counterbore");
    for (u = ubolt_legs()) hole("oak_bottom", "U-bolt leg", sh(u, o), ubolt_hole_d, "", "through", "MECH-UBOLT");
    hole("oak_bottom", "MIDI jack", sh(midi_xy, o), midi_hole_d, "", "through", "J-MIDI-OUT");
    hole("oak_bottom", "MIDI jack counterbore", sh(midi_xy, o), midi_cbore_d, "inside face", midi_cbore_depth);

    stock("mouth_cap", ends_mouth_cap_t, [W, T], ["outer face", "inner face"]);
    layer("mouth_cap", "mechanical/export/mouth-cap.dxf", "", "through", "outline, breath inlet tap drill");
    hole("mouth_cap", "breath inlet insert, tap drill", tube_yz, inlet_tap_drill_d, "", "through", "INLET-INSERT");

    stock("tail_cap", ends_tail_cap_t, [W, T], ["inner face", "outer face"]);
    layer("tail_cap", "mechanical/export/tail-cap.dxf", "", "through", "outline, etherCON bore and screw holes");
    layer("tail_cap", "mechanical/fab/tail-cap-recess.dxf", "outer face", ec_recess_d, "etherCON recess: leaves the connector its panel");
    hole("tail_cap", "etherCON bore", ec_c, ethercon_bore_d, "", "through", "J-UMBILICAL-INST");
    for (h = ec_holes) hole("tail_cap", "etherCON flange screw", h, ethercon_hole_d, "", "through", "MECH-ETHERCON-SCREW");

    po = [plate_x0, plate_y0];
    stock("plate_top", plate_thickness, [plate_x1 - x_in0, u_w], ["underside", "top face"]);
    layer("plate_top", "mechanical/export/plate-top.dxf", "", "through", "outline, switch cutouts, column screw holes");
    for (m = columns()) hole("plate_top", "column screw clearance", sh(m, po), hardware_col_plate_hole, "", "through", "MECH-COL-SCREW");
    stock("plate_bottom", plate_thickness, [bplate_x1 - x_in0, u_w], ["underside", "top face"]);
    layer("plate_bottom", "mechanical/export/plate-bottom.dxf", "", "through", "outline, thumb switch cutouts, stud and U-bolt holes, windows");
    for (i = [0 : len(cb_standoffs) - 1]) hole("plate_bottom", i < n_cols ? "stud, column" : "stud, end mount",
                                               sh(cb_standoffs[i], po), hardware_stud_hole, "underside", "through", "MECH-MB-STUD");
    for (u = ubolt_legs()) hole("plate_bottom", "U-bolt leg", sh(u, po), ubolt_hole_d, "", "through", "MECH-UBOLT");
    // the switch cutouts, every part that has them: count, and the square
    echo("FAB", "plate_top", "cutouts", len(top_keys), plate_cutout);
    echo("FAB", "plate_bottom", "cutouts", len(bottom_keys), plate_cutout);
}

if (fab == "geom") fab_geom();
else if (fab == "tail_cap_recess") { if (ec_recess_d > 0) ec_recess_2d(); }
else {
    assert(fab_id(fab) != undef, str("fab_parts.scad: unknown fab ", fab));
    // only the one named solid, through P()'s own filter: the spec passes
    // only = its id, since a -D is the one way to set woody_body.scad's own
    assert(only == fab_id(fab), str("fab_parts.scad: fab ", fab, " wants only = \"", fab_id(fab), "\""));
    fab_solid();
}
