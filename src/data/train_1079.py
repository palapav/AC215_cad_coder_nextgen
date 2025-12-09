import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.265625, 0.0, -0.21875), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(1.015625, 0.0).lineTo(1.015625, 0.08552631578947369).lineTo(0.8018092105263158, 0.08552631578947369).lineTo(0.8018092105263158, 0.2993421052631579).lineTo(0.7162828947368421, 0.2993421052631579).threePointArc((0.5078125, 0.09341445698358349), (0.2993421052631579, 0.2993421052631579)).lineTo(0.2138157894736842, 0.2993421052631579).lineTo(0.2138157894736842, 0.08552631578947369).lineTo(0.0, 0.08552631578947369).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.3828125)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.203125, -0.1796875, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.043421052631578944, 0.0).circle(0.04251644736842105)
solid1=wp_sketch1.add(loop1).extrude(-0.421875)
solid=solid.cut(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(0.6171875, -0.1796875, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch2.moveTo(0.043421052631578944, 0.0).circle(0.04251644736842105)
solid2=wp_sketch2.add(loop2).extrude(-0.421875)
solid=solid.cut(solid2)
