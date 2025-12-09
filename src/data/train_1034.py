import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.2890625, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.12031249999999999, 0.0).lineTo(0.12031249999999999, 0.41562499999999997).lineTo(0.91875, 0.41562499999999997).lineTo(0.91875, 0.0).lineTo(1.0390625, 0.0).lineTo(1.0390625, 0.0546875).lineTo(0.9624999999999999, 0.0546875).lineTo(0.9624999999999999, 0.459375).lineTo(0.07656249999999999, 0.459375).lineTo(0.07656249999999999, 0.0546875).lineTo(0.0, 0.0546875).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.1875)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.2265625, 0.046875, 0.09375), cq.Vector(-1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, 1.0, 6.123233995736766e-17)))
loop1=wp_sketch1.moveTo(0.0, 0.0).threePointArc((0.027343749999999997, -0.027343749999999997), (0.05468749999999999, 0.0)).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(-0.3125)
solid=solid.cut(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.2265625, 0.046875, 0.09375), cq.Vector(-1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, 1.0, 6.123233995736766e-17)))
loop2=wp_sketch2.moveTo(0.0, 0.0).threePointArc((0.027343749999999997, -0.027343749999999997), (0.05468749999999999, 0.0)).lineTo(0.0, 0.0).close()
solid2=wp_sketch2.add(loop2).extrude(-0.3125)
solid=solid.cut(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(0.7421875, 0.046875, 0.09375), cq.Vector(-1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, 1.0, 6.123233995736766e-17)))
loop3=wp_sketch3.moveTo(0.0, 0.0).threePointArc((0.027343749999999997, -0.027343749999999997), (0.05468749999999999, 0.0)).lineTo(0.0, 0.0).close()
solid3=wp_sketch3.add(loop3).extrude(-0.3125)
solid=solid.cut(solid3)
# Generating a workplane for sketch 4
wp_sketch4 = cq.Workplane(cq.Plane(cq.Vector(0.7421875, 0.046875, 0.09375), cq.Vector(-1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, 1.0, 6.123233995736766e-17)))
loop4=wp_sketch4.moveTo(0.0, 0.0).threePointArc((0.027343749999999997, -0.027343749999999997), (0.05468749999999999, 0.0)).lineTo(0.0, 0.0).close()
solid4=wp_sketch4.add(loop4).extrude(-0.3125)
solid=solid.cut(solid4)
