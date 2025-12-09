import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.2421875, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.24868421052631579, 0.0).circle(0.24868421052631579)
loop1=wp_sketch0.moveTo(0.04144736842105263, 0.0).circle(0.025904605263157892)
loop2=wp_sketch0.moveTo(0.24868421052631579, -0.20205592105263157).circle(0.025904605263157892)
loop3=wp_sketch0.moveTo(0.24868421052631579, 0.20205592105263157).circle(0.025904605263157892)
loop4=wp_sketch0.moveTo(0.4507401315789473, 0.0).circle(0.025904605263157892)
solid0=wp_sketch0.add(loop0).add(loop1).add(loop2).add(loop3).add(loop4).extrude(0.4375)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.15625, 0.0, 0.4375), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop5=wp_sketch1.moveTo(0.15789473684210525, 0.0).circle(0.15789473684210525)
solid1=wp_sketch1.add(loop5).extrude(0.03125)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.0546875, 0.0, 0.46875), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop6=wp_sketch2.moveTo(0.05131578947368422, 0.0).circle(0.05131578947368422)
solid2=wp_sketch2.add(loop6).extrude(0.28125)
solid=solid.union(solid2)
