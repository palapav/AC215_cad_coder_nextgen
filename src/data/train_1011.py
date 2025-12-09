import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, -0.46875, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(1.2109375, 0.0).lineTo(1.2109375, 1.2109375).lineTo(0.0, 1.2109375).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.6118421052631579, 0.6118421052631579).circle(0.3569078947368421)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.484375)
solid=solid0
