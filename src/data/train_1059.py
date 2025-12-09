import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.75, 0.0).lineTo(0.75, 0.75).lineTo(0.0, 0.75).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.09473684210526316, 0.09473684210526316).circle(0.039473684210526314)
loop2=wp_sketch0.moveTo(0.09473684210526316, 0.6552631578947369).circle(0.039473684210526314)
loop3=wp_sketch0.moveTo(0.6552631578947369, 0.09473684210526316).circle(0.039473684210526314)
loop4=wp_sketch0.moveTo(0.6552631578947369, 0.6552631578947369).circle(0.039473684210526314)
solid0=wp_sketch0.add(loop0).add(loop1).add(loop2).add(loop3).add(loop4).extrude(0.375)
solid=solid0
