import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.5625, 0.0, -0.1875), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.0, 0.375).threePointArc((-0.1875, 0.1875), (0.0, 0.0)).close()
solid0=wp_sketch0.add(loop0).extrude(0.125)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.5625, 0.0, -0.1875), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop1=wp_sketch1.moveTo(0.0, 0.0).threePointArc((0.1875, 0.1875), (0.0, 0.375)).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(0.125)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.5625, 0.0, -0.1875), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop2=wp_sketch2.moveTo(1.125, 0.0).threePointArc((0.9355263157894738, 0.18947368421052632), (1.125, 0.37894736842105264)).lineTo(0.0, 0.37894736842105264).threePointArc((0.18947368421052632, 0.18947368421052632), (0.0, 0.0)).close()
solid2=wp_sketch2.add(loop2).extrude(0.125)
solid=solid.union(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(-0.5625, 0.0, -0.1875), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop3=wp_sketch3.moveTo(0.0, 0.0).threePointArc((0.1875, 0.1875), (0.0, 0.375)).lineTo(0.0, 0.0).close()
solid3=wp_sketch3.add(loop3).extrude(0.125)
solid=solid.union(solid3)
# Generating a workplane for sketch 4
wp_sketch4 = cq.Workplane(cq.Plane(cq.Vector(0.5625, 0.0, -0.1875), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop4=wp_sketch4.moveTo(0.0, 0.375).threePointArc((-0.1875, 0.1875), (0.0, 0.0)).close()
solid4=wp_sketch4.add(loop4).extrude(0.125)
solid=solid.union(solid4)
# Generating a workplane for sketch 5
wp_sketch5 = cq.Workplane(cq.Plane(cq.Vector(-0.640625, -0.125, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop5=wp_sketch5.moveTo(0.0734375, 0.0).circle(0.07500000000000001)
solid5=wp_sketch5.add(loop5).extrude(-0.25)
solid=solid.cut(solid5)
# Generating a workplane for sketch 6
wp_sketch6 = cq.Workplane(cq.Plane(cq.Vector(0.484375, -0.125, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop6=wp_sketch6.moveTo(0.07500000000000001, 0.0).circle(0.07500000000000001)
solid6=wp_sketch6.add(loop6).extrude(-0.25)
solid=solid.cut(solid6)
