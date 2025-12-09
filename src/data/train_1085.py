import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.265625, 0.0, -0.2890625), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.24054276315789475, 0.0).lineTo(0.24054276315789475, 0.12294407894736842).threePointArc((0.09581992725462049, 0.2886513157894737), (0.24054276315789475, 0.454358552631579)).lineTo(0.24054276315789475, 0.5078125).lineTo(0.0, 0.5078125).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.0234375, 0.0, 0.1640625), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop1=wp_sketch1.moveTo(0.0, 0.0).threePointArc((0.021299342105263155, 0.0014397894202626707), (0.04259868421052631, 0.0)).lineTo(0.04259868421052631, 0.05468749999999999).lineTo(0.0, 0.05468749999999999).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(0.75)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(0.0234375, 0.0, -0.2890625), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop2=wp_sketch2.moveTo(0.24588815789473684, 0.0).lineTo(0.24588815789473684, 0.5078125).lineTo(0.0, 0.5078125).lineTo(0.0, 0.454358552631579).threePointArc((0.14472283590327426, 0.2886513157894737), (0.0, 0.12294407894736842)).lineTo(0.0, 0.0).close()
solid2=wp_sketch2.add(loop2).extrude(0.75)
solid=solid.union(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(-0.0234375, 0.0, -0.2890625), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop3=wp_sketch3.moveTo(0.02236842105263158, 0.0).lineTo(0.043421052631578944, 0.0).lineTo(0.043421052631578944, 0.125).threePointArc((0.021710526315789472, 0.12353241541718396), (0.0, 0.125)).lineTo(0.0, 0.0).close()
solid3=wp_sketch3.add(loop3).extrude(0.75)
solid=solid.union(solid3)
