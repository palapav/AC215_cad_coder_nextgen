import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.7578947368421053, 0.0).circle(0.7578947368421053)
loop1=wp_sketch0.moveTo(0.7578947368421053, 0.0).circle(0.28421052631578947)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.0546875)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.21875, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch1.moveTo(0.22105263157894733, 0.0).circle(0.22105263157894733)
loop3=wp_sketch1.moveTo(0.22105263157894733, 0.0).circle(0.04144736842105263)
solid1=wp_sketch1.add(loop2).add(loop3).extrude(0.0546875)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.2734375, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop4=wp_sketch2.moveTo(0.2802631578947368, 0.0).circle(0.2802631578947368)
loop5=wp_sketch2.moveTo(0.2802631578947368, 0.0).circle(0.221875)
solid2=wp_sketch2.add(loop4).add(loop5).extrude(0.0546875)
solid=solid.union(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(-0.2734375, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop6=wp_sketch3.moveTo(0.2802631578947368, 0.0).circle(0.2802631578947368)
loop7=wp_sketch3.moveTo(0.2802631578947368, 0.0).circle(0.221875)
solid3=wp_sketch3.add(loop6).add(loop7).extrude(0.5625)
solid=solid.union(solid3)
# Generating a workplane for sketch 4
wp_sketch4 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop8=wp_sketch4.moveTo(0.7578947368421053, 0.0).circle(0.7578947368421053)
loop9=wp_sketch4.moveTo(0.7578947368421053, 0.0).circle(0.28421052631578947)
solid4=wp_sketch4.add(loop8).add(loop9).extrude(0.0546875)
solid=solid.union(solid4)
