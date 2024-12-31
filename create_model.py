import bpy
import sys
sys.path.append(r"c:\users\hrith\appdata\local\programs\python\python310\lib\site-packages") #path to yaml, import wasnt working
import yaml
import math

#pwsh command:
# blender --background --python create_model.py -- config.yaml


# Remove-Item .\models\new.blend

def create_cube(size, location,  chip_name, material=None):
    # Create a cube with the given size
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cube = bpy.context.object
    cube.name = chip_name
    
    cube.scale = (size[0] , size[1] , size[2] ) 
    bpy.ops.object.transform_apply(scale=True)
    if material:
        cube.data.materials.append(material)
    return cube

def create_cylinder(radius, depth, location, material=None):

    #Create a cylinder with the given radius, depth, and location.

    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, vertices=8)
    cylinder = bpy.context.object
    if material:
        cylinder.data.materials.append(material)
    return cylinder

def create_sphere(radius, location, material=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    sphere = bpy.context.object
    if material:
        sphere.data.materials.append(material)
    return sphere

def flip_chip(chip_obj):
    print("flip_chip function called.")
    if not chip_obj:
        print("Error: No object provided.")
        return

    # Ensure parenting is correct
    if len(chip_obj.children) == 0:
        print(f"Warning: Chip '{chip_obj.name}' has no children (bumps).")
    else:
        print(f"Child location before flip: {chip_obj.children[0].location}")

    # Apply transformations to ensure clean rotation
    bpy.context.view_layer.objects.active = chip_obj
    chip_obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Perform the rotation (180 degrees in radians)
    print(f"Before flip: {chip_obj.rotation_euler}")
    chip_obj.rotation_euler[0] += math.pi  # Rotate 180 degrees
    chip_obj.matrix_world = chip_obj.matrix_world  # Update world matrix
    print(f"After flip: {chip_obj.rotation_euler}")

    # Update children's world locations
    for child in chip_obj.children:
        child.matrix_world = child.matrix_world  # Refresh child transformation
    print(f"Child '{child.name}' location after flip: {child.children[0].location}")

    print(f"Object '{chip_obj.name}' flipped 180 degrees.")

    
    
# Function to create and assign a material with transparency

def create_material(name, color, opacity):

    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    
    # Remove default nodes
    nodes.clear()
        
    # Add a Principled BSDF shader
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node.location = (0, 0)
    principled_node.inputs['Base Color'].default_value = color  # RGBA color
    principled_node.inputs['Alpha'].default_value = opacity / 100  # Opacity as percentage

    # Add an output node
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (200, 0)

    # Connect the shader to the output
    material.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

    # below is unused, deprecated?
    # Enable transparency
    # material.blend_method = 'BLEND' # Set to 'BLEND' for transparency
    # material.shadow_method = 'HASHED' # Handle shadows with transparency

    return material

# UNUSED, eventually chip coordinates could be given by a corner instead of center in 3d space, for clarity
def corner_coord_to_center(corner_location, size):
    if len(corner_location) != 3 or len(size) != 3:
        raise ValueError("Both 'location' and 'size' must be lists of length 3.")
    
    # Compute the offset to move the origin to the corner
    corner_offset = [dim / 2 for dim in size]
    
    # Subtract the offset from the center location
    adjusted_location = (
        corner_location[0] - corner_offset[0],
        corner_location[1] - corner_offset[1],
        corner_location[2] - corner_offset[2]
    )
    
    return adjusted_location
    

def add_bumps(chip_config, chip_context, material_list, vias=False):
    print(f"adding bumps to {chip_context.name}")
    
    chip_height = chip_config.get('size', [10, 10, 0.5])[2]
    chip_location = chip_config.get('location', [0, 0, 0])
    if vias == False:
        bumps_config = chip_config.get('bumps', {})
    else:
        bumps_config = chip_config.get('vias', {})


    bump_size = bumps_config.get('bump_size', 0.1)
    bump_spacing = bumps_config.get('bump_spacing', 0.2)
    bump_pattern = bumps_config.get('bump_pattern', 'grid')
    num_bumps_x = bumps_config.get('number_of_bumps_x', 10)
    num_bumps_y = bumps_config.get('number_of_bumps_y', 10)
    rows_to_create = bumps_config.get('rows_to_create', [[0, num_bumps_y]])
    use_sphere = bumps_config.get('use_solder_joint', False)
    
    bumps_z = chip_location[2] - chip_height / 2 - bump_size / 2
    print(f"Bumps at {bumps_z}")
    
    bump_material = None
    bump_type = bumps_config.get('bump_type')
    if bump_type == "power":
        bump_material = material_list[0]
    elif bump_type == "data":
        bump_material = material_list[5] 
            
    if bump_material is None:
        bump_material = material_list[0]

    if bump_pattern == "grid":
        for row_set in rows_to_create:
            for x in range(num_bumps_x): 
                for y in range(num_bumps_y):
                    if y not in range(row_set[0], row_set[1] + 1):
                        continue 
                    bump_location = (
                        chip_location[0] + x * bump_spacing - (num_bumps_x - 1) * bump_spacing / 2,
                        chip_location[1] + y * bump_spacing - (num_bumps_y - 1) * bump_spacing / 2,
                        chip_location[2] - chip_height / 2 - bump_size / 2
                    )

                    radius=bump_size / 2
                    depth=bump_size
                    if vias == True:
                        depth=bumps_config.get('bump_length',2)
                        bump_location=[bump_location[0],bump_location[1],bump_location[2]-0.4]
                    location=bump_location
                    
                    if use_sphere==True:
                        bump_context = create_sphere(radius, location, bump_material)
                    else:
                        bump_context = create_cylinder(radius, depth, location, bump_material)
                    

                    bump_context.parent = chip_context
                
    return chip_context

# add wire connections between chips
def add_fences(chip_config, chip_context, material_list):
    print(f"Adding fences to {chip_context.name}")
    material= material_list[5]
    # Retrieve bump configuration
    chip_location = chip_config.get('location', [0, 0, 0])
    chip_size = chip_config.get('size', [10, 10, 0.5])
    bumps_config = chip_config.get('bumps', {})

    bump_size = bumps_config.get('bump_size', 0.1)
    bump_spacing = bumps_config.get('bump_spacing', 0.2)
    num_bumps_x = bumps_config.get('number_of_bumps_x', 10)
    num_bumps_y = bumps_config.get('number_of_bumps_y', 10)

    
    bar_width = 0.15  # Width of the bar
    bar_depth = 0.15  # Depth of the bar
    
    # Calculate bar length based on bump spacing and number of bumps in the y-direction
    #
    bar_length = chip_size[1]
    # Iterate over rows of bumps
    for x in range(num_bumps_x):
        bar_location = (
            chip_location[0] + x * bump_spacing - (num_bumps_x - 1) * bump_spacing / 2,  # Centered in x
            chip_location[1],  # Aligned along the y-axis
            chip_location[2] + chip_size[2] / 2 - bar_depth/2 +.03   # Positioned below the bumps
        )
        
        size= [bar_width , bar_length , bar_depth ] 
        bar_obj = create_cube(size, bar_location, "bar", material)
        bar_obj = bpy.context.active_object
        # Adjust bar dimensions
        bar_obj.name = f"Fence_{x}"
        
        # Parent the bar to the chip
        bar_obj.parent = chip_context
    
    print(f"Added {num_bumps_x} fences to {chip_context.name}")


#creates layers in the substrate, UNUSED
def add_subst_layers(size, location, subst_context, layers, material_list):
    layer_locs = calculate_layer_locations(location, size, layers)
    sheet_size = [size[0],size[1]+0.5,0.05]
    for layer_loc in layer_locs:
        sheet_obj=create_cube(sheet_size, layer_loc, material_list[0])
        sheet_obj.parent=subst_context
    
    return subst_context

# UNUSED
def calculate_layer_locations(location, size, layers):

    x = location[0]
    y = location[1]
    z = location[2]

    depth = size[2]

    layer_locations = [
        [x, y, z - depth / 2 + (i + 1) * depth / layers]
        for i in range(layers-1)
    ]

    return layer_locations

# hard coded
def add_chiplet(material_list):
    size=[10, 10, 0.5] 
    location=[0,18.5,-0.7]
    name="chiplet"
    cube_obj=create_cube(size, location, name, material_list[6])

# hard coded
def add_cable(material_list):
    size=[3, 4, 0.6] 
    location=[0,22.5,-0.4]
    name="cable_block"
    cube_obj=create_cube(size, location, name, material_list[2])

    radius=0.3
    depth =5
    location=[0,25.5,-0.4]
    name="cable"
    cable_obj = create_cylinder(radius, depth, location, material_list[0])
    cable_obj.rotation_euler[0] = math.radians(90)
    
def create_shapes(config, material_list):
    if 'chips' in config:
        for cube_config in config['chips']:
       # cube_config = config['chip']
            size = cube_config.get('size', [1, 1, 1])  # Default size is 1
            location = cube_config.get('location', [0, 0, 0])  # Default location is [0, 0, 0]
            is_flipped = cube_config.get('is_flipped')
            name = cube_config.get('name', 'chip')
            print(f"Creating cube {name} with size {size} at location {location}")
            if name=="interposer":
                cube_mat = material_list[2]
            else: 
                cube_mat = material_list[3]
            cube_obj=create_cube(size, location, name, cube_mat)
            if not name=="interposer":
                add_bumps(cube_config, cube_obj,material_list)
           # if is_flipped:
                #flip_chip(cube_obj)
            if name=="interposer":
                print(f"adding wire connections")
                add_fences(cube_config, cube_obj, material_list)
            if 'vias' in cube_config:
                chip_vias = True
                add_bumps(cube_config, cube_obj,material_list, chip_vias)

    

    if 'substrate' in config:
        for subst_config in config['substrate']:
            
            size = subst_config.get('size', [1, 1, 1])  # Default size is 1
            location = subst_config.get('location', [0, 0, 0])  # Default location is [0, 0, 0]
            name = subst_config.get('name', 'subst')
            material= material_list[4]
            #layers=5
            print(f"Creating cube {name} with size {size} at location {location}")
            subst_obj=create_cube(size, location, name, material)
            add_bumps(subst_config, subst_obj,material_list)
    
    add_chiplet(material_list)
    add_cable(material_list)

def load_config(file_path):
    # Load the configuration from the YAML file
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

if __name__ == "__main__":
    # Handle arguments properly
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]  # Get arguments after '--'
    
    # Check if config file argument is passed, default to "config.yaml"
    config_file = "config.yaml"
    if len(argv) > 0:
        config_file = argv[0]

    print(f"Loading configuration from {config_file}")
    
    # Load configuration
    config = load_config(config_file)


    # Manual material creation for color and transparency
    prism_material = create_material("PrismMaterial", (0.8, 0.2, 0.2, 1), 50) # Red  with 50% opacity
    shape_material = create_material("ShapeMaterial", (0.2, 0.8, 0.2, 1), 100) # Green with 30% opacity
    teal= create_material("teal", ((58/255),(154/255),(145/255),1), 50)
    blue = create_material("blue", ((3/255),(168/255),(248/255),1), 35)
    lightgray = create_material("lightgray", ((210/255),(210/255),(210/255),1), 35)
    yellow = create_material("yellow", ((248/255),(170/255),(24/255),1), 80)
    lightgreen = create_material("lightgreen", ((52/255),(193/255),(28/255),1), 50)
    material_list = [prism_material, shape_material, teal, blue, lightgray, yellow, lightgreen]
    
    
    create_shapes(config, material_list)

    # save the file
    bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\hrith\OneDrive\Documents\Python Scripts\models\new.blend")
    print("Blender file saved.")
