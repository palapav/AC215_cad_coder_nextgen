import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, -0.25, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(1.5, 0.0).lineTo(1.5, 0.18947368421052632).lineTo(0.7578947368421053, 0.18947368421052632).threePointArc((0.7026315789473685, 0.24473684210526317), (0.7578947368421053, 0.3)).lineTo(1.5, 0.3).lineTo(1.5, 0.5052631578947369).lineTo(0.0, 0.5052631578947369).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.0625, both=True)
solid=solid0
