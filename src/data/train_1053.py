import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.75, 0.0).lineTo(0.75, 0.3631578947368421).lineTo(0.0, 0.3631578947368421).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.7342105263157895, 0.015789473684210527).lineTo(0.7342105263157895, 0.3473684210526316).lineTo(0.015789473684210527, 0.3473684210526316).lineTo(0.015789473684210527, 0.015789473684210527).close()
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.6328125)
solid=solid0
