import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.2734375, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.1381578947368421, 0.0).threePointArc((0.2734375, 0.13527960526315788), (0.40871710526315785, 0.0)).lineTo(0.546875, 0.0).threePointArc((0.2734375, 0.2734375), (0.0, 0.0)).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.0, 0.2734375, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.0, 0.0).threePointArc((0.19334951048069668, -0.0800879895193034), (0.2734375, -0.2734375)).lineTo(0.2734375, 0.0).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(0.75)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.2734375, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch2.moveTo(0.0, 0.0).threePointArc((0.0800879895193034, 0.19334951048069668), (0.2734375, 0.2734375)).lineTo(0.0, 0.2734375).lineTo(0.0, 0.0).close()
solid2=wp_sketch2.add(loop2).extrude(0.75)
solid=solid.union(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(-0.40625, 0.2734375, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop3=wp_sketch3.moveTo(0.13815789473684212, 0.0).lineTo(0.4144736842105263, 0.0).lineTo(0.682154605263158, 0.0).lineTo(0.8203125000000001, 0.0).lineTo(0.8203125000000001, 0.06907894736842106).lineTo(0.0, 0.06907894736842106).lineTo(0.0, 0.0).close()
solid3=wp_sketch3.add(loop3).extrude(0.75)
solid=solid.union(solid3)
