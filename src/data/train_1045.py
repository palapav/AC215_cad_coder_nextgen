import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.2734375, 0.0, -0.75), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.5526315789473685, 0.0).lineTo(0.5526315789473685, 1.5).lineTo(0.0, 1.5).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.0234375)
solid=solid0
