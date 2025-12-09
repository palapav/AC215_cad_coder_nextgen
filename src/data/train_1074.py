import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.53125, 0.0, 0.3203125), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(1.28125, 0.0).lineTo(1.28125, 0.10789473684210527).lineTo(0.0, 0.10789473684210527).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.4765625)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.4375, -0.2421875, 0.4296875), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.055263157894736833, 0.0).circle(0.055263157894736833)
solid1=wp_sketch1.add(loop1).extrude(-0.546875)
solid=solid.cut(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(0.5625, -0.2421875, 0.4296875), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch2.moveTo(0.055263157894736833, 0.0).circle(0.05411184210526315)
solid2=wp_sketch2.add(loop2).extrude(-0.546875)
solid=solid.cut(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(-0.2578125, -0.4765625, 0.4296875), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop3=wp_sketch3.moveTo(0.75, 0.0).lineTo(0.0, 0.0).close()
solid3=wp_sketch3.add(loop3).extrude(0.265625)
solid=solid.union(solid3)
# Generating a workplane for sketch 4
wp_sketch4 = cq.Workplane(cq.Plane(cq.Vector(-0.2578125, -0.4765625, 0.4296875), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop4=wp_sketch4.moveTo(0.75, 0.0).lineTo(0.75, 0.48157894736842105).lineTo(0.0, 0.48157894736842105).lineTo(0.0, 0.0).close()
solid4=wp_sketch4.add(loop4).extrude(0.265625)
solid=solid.union(solid4)
