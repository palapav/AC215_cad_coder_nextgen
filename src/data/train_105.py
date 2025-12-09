import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.46875, 0.0, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.47368421052631576, 0.0).circle(0.47368421052631576)
solid0=wp_sketch0.add(loop0).extrude(0.09375)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.375, -0.09375, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop1=wp_sketch1.moveTo(0.37894736842105264, 0.0).circle(0.37894736842105264)
solid1=wp_sketch1.add(loop1).extrude(0.65625)
solid=solid.union(solid1)
