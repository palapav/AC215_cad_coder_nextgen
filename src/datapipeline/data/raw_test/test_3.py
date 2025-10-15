import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, -0.640625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.0, 0.0).threePointArc((0.03237240839517088, -0.07815390739430259), (0.1105263157894737, -0.1105263157894737)).lineTo(1.3894736842105264, -0.1105263157894737).threePointArc((1.4676275916048291, -0.07815390739430259), (1.5, 0.0)).lineTo(1.5, 1.2789473684210526).threePointArc((1.4676275916048291, 1.3571012758153556), (1.3894736842105264, 1.3894736842105264)).lineTo(0.1105263157894737, 1.3894736842105264).threePointArc((0.03237240839517088, 1.3571012758153556), (0.0, 1.2789473684210526)).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.7578947368421053, 0.631578947368421).circle(0.18947368421052632)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.2265625)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.375, 0.0, 0.2265625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch1.moveTo(0.37894736842105264, 0.0).circle(0.37894736842105264)
loop3=wp_sketch1.moveTo(0.37894736842105264, 0.0).circle(0.18947368421052632)
solid1=wp_sketch1.add(loop2).add(loop3).extrude(-0.109375)
solid=solid.cut(solid1)
