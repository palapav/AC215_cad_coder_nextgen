import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.46710526315789475, 0.0).threePointArc((0.5576069078947369, 0.09050164473684211), (0.46710526315789475, 0.18100328947368421)).lineTo(0.46710526315789475, 0.32113486842105265).lineTo(0.0, 0.32113486842105265).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.015625, 0.015625, 0.75), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.43749999999999994, 0.0).lineTo(0.43749999999999994, 0.29473684210526313).lineTo(0.0, 0.29473684210526313).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(-0.7265625)
solid=solid.cut(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(0.4609375, 0.015625, 0.75), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch2.moveTo(0.0, 0.0).threePointArc((0.07421875, 0.07421875), (0.0, 0.1484375)).lineTo(0.0, 0.0).close()
solid2=wp_sketch2.add(loop2).extrude(-0.7265625)
solid=solid.cut(solid2)
