# Quick Tutorials

[Isaac Sim Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html)

[Quick Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_index.html#isaac-sim-intro-quickstart-series)


1. In Isaac Sim, Window | Browser | Isaac Sim Assets

1. Search for UR3 and drag it into the stage.

1. Create | Physics | Ground Plane

1. Create | Physics | Physics Scene (gravity, timestep)

1. Select UR3 and set transalation to (0,0,0)

1. Select UR3 | base_link | Add | Physics | Articulation Root (allows us to command joints via Python and ROS 2)

1. ur3 | wrist_3_link | flange | right-click Create | Camera

1. Rename Camera to camera_link

1. Configure camera_link 

| Property    | Values                         |
|-------------|--------------------------------|
| Transform   | TranslateY = 0.05, OrientX=180 |
| Camera      | Lens: Focal Length = 1.88mm    |
| Camera      | Horiz Apperture: 3.68mm        |
| Camera      | Clipping: X = 0.07, Y = 0.5    |

