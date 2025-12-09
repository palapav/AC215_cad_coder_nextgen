import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.1328125, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.1381578947368421, 0.0).circle(0.1381578947368421)
loop1=wp_sketch0.moveTo(0.1381578947368421, 0.0).circle(0.12952302631578946)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.75)
solid=solid0
