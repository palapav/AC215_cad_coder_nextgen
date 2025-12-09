import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.0078125, 0.0, -0.1171875), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.010526315789473684, 0.0).lineTo(0.010526315789473684, 0.11447368421052631).lineTo(0.125, 0.11447368421052631).lineTo(0.125, 0.125).lineTo(0.0, 0.125).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
