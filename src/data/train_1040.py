import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.21875, -0.1640625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.28421052631578947, 0.0).threePointArc((-0.7216361787420418, 0.1618421052631579), (0.28421052631578947, 0.3236842105263158)).lineTo(0.0, 0.3236842105263158).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.4296875)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.21875, -0.1640625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.2866776315789474, 0.0).threePointArc((0.3130755113564729, 0.1640625), (0.2866776315789474, 0.328125)).lineTo(0.0, 0.328125).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(0.4296875)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(0.5, -0.1640625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch2.moveTo(0.24868421052631579, 0.0).lineTo(0.24868421052631579, 0.328125).lineTo(0.0, 0.328125).threePointArc((0.026397879777525536, 0.1640625), (0.0, 0.0)).close()
solid2=wp_sketch2.add(loop2).extrude(0.1328125)
solid=solid.union(solid2)
