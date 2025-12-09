import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, -0.4140625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(1.5, 0.0).lineTo(1.5, 0.8368421052631579).lineTo(0.0, 0.8368421052631579).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.4105263157894737, 0.4105263157894737).circle(0.20526315789473684)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.3359375)
solid=solid0
