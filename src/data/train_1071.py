import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, -0.75, 0.421875), cq.Vector(3.749399456654644e-33, 1.0, -6.123233995736766e-17), cq.Vector(1.0, 0.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.2578125, 0.0).lineTo(0.2578125, 0.2578125).lineTo(0.0, 0.2578125).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.2578125)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.2578125, -0.6640625, 0.421875), cq.Vector(3.749399456654644e-33, 1.0, -6.123233995736766e-17), cq.Vector(1.0, 0.0, 6.123233995736766e-17)))
loop1=wp_sketch1.moveTo(0.171875, 0.0).lineTo(0.171875, 0.171875).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(0.2578125)
solid=solid.union(solid1)
