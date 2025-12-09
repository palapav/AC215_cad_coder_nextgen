import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.7578947368421053, 0.0).circle(0.7578947368421053)
loop1=wp_sketch0.moveTo(0.7578947368421053, 0.0).circle(0.6947368421052632)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.265625)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.2109375, 0.6640625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch1.moveTo(0.4296875, 0.0).lineTo(0.4296875, 0.0859375).lineTo(0.0, 0.0859375).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop2).extrude(0.265625)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.203125, 0.671875, 0.265625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop3=wp_sketch2.moveTo(0.02138157894736842, 0.0).threePointArc((0.203125, 0.024683715127281892), (0.3848684210526316, 0.0)).lineTo(0.40625, 0.0).lineTo(0.40625, 0.05131578947368422).threePointArc((0.37619769998258146, 0.057179178866082155), (0.34638157894736843, 0.06414473684210527)).lineTo(0.059868421052631585, 0.06414473684210527).threePointArc((0.030052300017418463, 0.05717917886608228), (0.0, 0.05131578947368422)).lineTo(0.0, 0.0).close()
solid2=wp_sketch2.add(loop3).extrude(-0.2578125)
solid=solid.cut(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(-0.203125, 0.71875, 0.265625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop4=wp_sketch3.moveTo(0.0, 0.0).threePointArc((0.03111677083055083, 0.0078121498824299945), (0.0625, 0.014473684210526316)).lineTo(0.0, 0.014473684210526316).lineTo(0.0, 0.0).close()
solid3=wp_sketch3.add(loop4).extrude(-0.2578125)
solid=solid.cut(solid3)
# Generating a workplane for sketch 4
wp_sketch4 = cq.Workplane(cq.Plane(cq.Vector(-0.1796875, 0.671875, 0.265625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop5=wp_sketch4.moveTo(0.3671875, 0.0).threePointArc((0.18359375, 0.024935019919301714), (0.0, 0.0)).close()
solid4=wp_sketch4.add(loop5).extrude(-0.2578125)
solid=solid.cut(solid4)
# Generating a workplane for sketch 5
wp_sketch5 = cq.Workplane(cq.Plane(cq.Vector(0.140625, 0.734375, 0.265625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop6=wp_sketch5.moveTo(0.0, 0.0).threePointArc((0.0313832291694492, -0.00666153432809632), (0.0625, -0.014473684210526316)).lineTo(0.0625, 0.0).lineTo(0.0, 0.0).close()
solid5=wp_sketch5.add(loop6).extrude(-0.2578125)
solid=solid.cut(solid5)
