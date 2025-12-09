import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.75, 0.0).lineTo(0.75, 0.2131578947368421).lineTo(0.0, 0.2131578947368421).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.015625)
solid=solid0
