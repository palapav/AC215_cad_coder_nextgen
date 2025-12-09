import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, 0.0, 0.0), cq.Vector(3.749399456654644e-33, 1.0, -6.123233995736766e-17), cq.Vector(1.0, 0.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.4765625, 0.0).lineTo(0.4765625, 0.015049342105263158).lineTo(0.0, 0.015049342105263158).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(-0.75)
solid=solid0
