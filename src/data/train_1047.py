import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.0, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.75, 0.0).lineTo(0.75, 0.37894736842105264).lineTo(0.6236842105263158, 0.37894736842105264).lineTo(0.6236842105263158, 0.25263157894736843).lineTo(0.12631578947368421, 0.25263157894736843).lineTo(0.12631578947368421, 0.37894736842105264).lineTo(0.0, 0.37894736842105264).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.5)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.546875, -0.2578125, 0.25), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.06315789473684211, 0.0).circle(0.06184210526315789)
solid1=wp_sketch1.add(loop1).extrude(-0.625)
solid=solid.cut(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.34375, -0.2578125, 0.25), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch2.moveTo(0.06315789473684211, 0.0).circle(0.06184210526315789)
solid2=wp_sketch2.add(loop2).extrude(-0.625)
solid=solid.cut(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(0.0, -0.375, 0.0), cq.Vector(3.749399456654644e-33, 1.0, -6.123233995736766e-17), cq.Vector(1.0, 0.0, 6.123233995736766e-17)))
loop3=wp_sketch3.moveTo(0.25, 0.0).lineTo(0.25, 0.12631578947368421).lineTo(0.0, 0.12631578947368421).lineTo(0.0, 0.0).close()
solid3=wp_sketch3.add(loop3).extrude(-0.75)
solid=solid.cut(solid3)
