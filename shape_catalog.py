"""Qt-free catalogue of what the shape loader offers and the viewer's default settings.

ShapeLoaderDialog (shape_loader_dialog.py), DisplayOptionsDialog and the transformation sliders
(wireframe_viewer.py) read these, and so does the web interface, so the lists and ranges live in one place.
"""
BASIC_SHAPES = ['Cube', 'Sphere', 'Tetrahedron', 'Octahedron', 'Icosahedron', 'Dodecahedron',
                'Torus', 'Cylinder', 'Cone', 'Pyramid', 'Prism']
PARAMETRIC_SHAPES = ['Mobius Strip', 'Klein Bottle', 'Trefoil Knot', 'Helicoid', 'Catenoid', 'Sine Surface', 'Gyroid']
FRACTALS = ['Sierpinski Triangle', 'Koch Snowflake', 'Menger Sponge', 'Apollonian Gasket', 'Jerusalem Cube',
            'Sierpinski Tetrahedron', 'Pythagoras Tree 3D']

# (min, max, default[, step]) of the loader's spin boxes
PARAM_RESOLUTION = (10, 100, 30)        # U and V resolution of parametric shapes
FRACTAL_ITERATIONS = (1, 8, 4)
FRACTAL_SIZE = (0.1, 10.0, 1.0, 0.1)

# DisplayOptionsDialog defaults (RGB 0-255) and ranges
DISPLAY = {"show_faces": True, "show_edges": True, "show_vertices": False,  # faces use OBJECT_COLOR
           "edge_color": (0, 0, 0), "vertex_color": (255, 0, 0),
           "edge_width": (1, 10, 1), "vertex_size": (1, 20, 5)}
# SceneObject colours (RGBA 0-1)
OBJECT_COLOR = (0.7, 0.7, 0.7, 1.0)
HOVER_COLOR = (1.0, 0.0, 0.0, 1.0)
# transformation sliders: (min, max, initial, step); they apply to every object in the scene
TRANSLATION_SLIDER = (-5, 5, 0, 0.1)
SCALE_SLIDER = (0.1, 2, 1, 0.1)
# ObjectPropertiesDialog ranges
PROPERTY_RANGES = {"mass": (0.1, 1000), "scale": (0.1, 10, 0.1), "rotation_speed": (-10, 10, 0.1)}
