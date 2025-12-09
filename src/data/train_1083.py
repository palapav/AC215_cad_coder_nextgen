import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.5703125, -0.2890625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(1.3203125, 0.0).lineTo(1.3203125, 0.4864309210526316).lineTo(0.0, 0.4864309210526316).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.140625)
solid=solid0
