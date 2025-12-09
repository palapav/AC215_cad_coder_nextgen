import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.5859375, -0.6171875, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(1.3359375, 0.0).lineTo(1.3359375, 1.0265625).lineTo(0.0, 1.0265625).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.18281250000000002, 0.253125).lineTo(0.18281250000000002, 0.8718750000000001).lineTo(0.1265625, 0.8718750000000001).lineTo(0.1265625, 0.253125).close()
loop2=wp_sketch0.moveTo(1.209375, 0.253125).lineTo(1.209375, 0.8718750000000001).lineTo(1.153125, 0.8718750000000001).lineTo(1.153125, 0.253125).close()
solid0=wp_sketch0.add(loop0).add(loop1).add(loop2).extrude(0.0546875)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.5859375, -0.6171875, 0.0546875), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop3=wp_sketch1.moveTo(1.3359375, 0.0).lineTo(1.3359375, 0.0984375).lineTo(0.0, 0.0984375).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop3).extrude(0.0546875)
solid=solid.union(solid1)
