import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.234375, 0.0, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.23684210526315788, 0.0).circle(0.23684210526315788)
loop1=wp_sketch0.moveTo(0.23684210526315788, 0.0).circle(0.11842105263157894)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.1171875)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.21875, -0.1171875, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop2=wp_sketch1.moveTo(0.21710526315789475, 0.0).circle(0.21258223684210528)
loop3=wp_sketch1.moveTo(0.21710526315789475, 0.0).circle(0.11759868421052633)
solid1=wp_sketch1.add(loop2).add(loop3).extrude(0.0390625)
solid=solid.union(solid1)
