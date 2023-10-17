import bpy
import math
import mathutils
import random
import sys

print(sys.version_info)

# --- Monomer properties ---

phi = math.pi/4
normalized_theta = math.pi/3
normalized_distance = 1 * 10
normalized_radius = 1 * 10
normalized_depth_of_monomer = 1 * 10


# --- Cylinder creation ---

def create_cylinders(cylinder_location, direction_vector, branch_name):
    rotation_to_align = get_rotation_from_direction(direction_vector)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=normalized_radius*0.4, 
        depth=normalized_depth_of_monomer*0.5, 
        location=cylinder_location, 
        rotation=rotation_to_align
    )
    # Creates a system to name the created cylinder
    bpy.context.active_object.name = branch_name + "_cylinder_" + str(len(bpy.data.objects))
   
    
def create_cylinder_between_positions(pos1, pos2, branch_name):
    # Calculates the direction
    direction = []
    for i in range(3):
        direction.append(pos2[i] - pos1[i])

    # Calculates the midpoint
    midpoint = []
    for i in range(3):
        midpoint.append((pos1[i] + pos2[i]) / 2)

    create_cylinders(midpoint, direction, branch_name)


# --- Branch Generation Functions ---

def generate_branch(num_monomers, start_position, start_direction, branch_name, theta=normalized_theta):
    monomer_positions = [start_position]
    current_position = mathutils.Vector(start_position)
    current_direction = mathutils.Vector(start_direction)

    for i in range(num_monomers):
        move_forward = current_direction * normalized_distance
        next_position = current_position + move_forward
        monomer_positions.append(tuple(next_position))
        create_cylinder_between_positions(tuple(current_position), tuple(next_position), branch_name)
        current_position = next_position
        current_direction = mathutils.Vector(rotate_point(point=current_direction,
         rotation_angles=(theta, phi, 0), center=(0,0,0)))

    return monomer_positions


def recreate_branch_from_positions(branch_positions, branch_name):
    """
    In Blender all objects remain in the scene until they are deleted
    When rotating a branch the data for the rotation is calculated but the objects from the non rotated branch are not moved
    Thats why 
    1: The non rotated branch has to be deleted
    2: The rotated branch has to be visualized
    This Method visualizes the rotated branch
    """
    for i in range(len(branch_positions) - 1):
        create_cylinder_between_positions(branch_positions[i], branch_positions[i+1], branch_name)


def get_rotation_from_direction(direction_vector):
    target_direction = mathutils.Vector(direction_vector)
    default_direction = mathutils.Vector((0, 1, 0))
    rotation_matrix = default_direction.rotation_difference(target_direction)
    euler_rotation = rotation_matrix.to_euler()
    return (euler_rotation.x, euler_rotation.y, euler_rotation.z)


def rotate_point(point, rotation_angles, center=(0,0,0)):
    vec = mathutils.Vector(point) - mathutils.Vector(center)
    mat_rot = mathutils.Euler(rotation_angles).to_matrix()
    rotated_vec = mat_rot @ vec
    rotated_vec += mathutils.Vector(center)
    return tuple(rotated_vec)


def rotate_branch_in_xy(branch, rotation_angle_xy_plane):
    if not branch:
        return []

    anchor = mathutils.Vector(branch[0])
    # The branch gets shifted so that the first point is at the origin
    # This is done to simplify the math of the rotation calculations
    shifted_branch = []
    for pt in branch:
        shifted_point = tuple(mathutils.Vector(pt) - anchor)
        shifted_branch.append(shifted_point)

    # The rotation calculations of each cylinder are performed
    rotated_shifted_branch = []
    for pt in shifted_branch:
        rotated_point = rotate_point(pt, (0, 0, rotation_angle_xy_plane))
        rotated_shifted_branch.append(rotated_point)

    # The whole branch with its applied rotation is shifted back so that the first point is back at its original position
    rotated_branch = []
    for pt in rotated_shifted_branch:
        final_point = tuple(mathutils.Vector(pt) + anchor)
        rotated_branch.append(final_point)

    return rotated_branch


def rotate_branch_in_xz(branch, rotation_angle_xz_plane):
    if not branch:
        return []

    # The branch gets shifted so that the first point is at the origin
    # This is done to simplify the math of the rotation calculations
    anchor = mathutils.Vector(branch[0])
    
    shifted_branch = []
    for pt in branch:
        shifted_point = tuple(mathutils.Vector(pt) - anchor)
        shifted_branch.append(shifted_point)

    # The rotation calculations of each cylinder are performed
    rotated_shifted_branch = []
    for pt in shifted_branch:
        rotated_point = rotate_point(pt, (rotation_angle_xz_plane, 0, 0))
        rotated_shifted_branch.append(rotated_point)

    # The whole branch with its applied rotation is shifted back so that the first point is back at its original position
    rotated_branch = []
    for pt in rotated_shifted_branch:
        final_point = tuple(mathutils.Vector(pt) + anchor)
        rotated_branch.append(final_point)

    return rotated_branch


# --- Visualization helper functions ---

def clear_mesh_objects():
    """
    In Blender all objects remain in the scene until they are deleted
    When rotating a branch the data for the rotation is calculated but the objects from the non rotated branch are not moved
    This Method deletes all mesh objects which are the rendered visualization of the data.
    """
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()


def clear_specific_branch(branch_name):
    """
    In Blender all objects remain in the scene until they are deleted.
    When rotating a branch the data for the rotation is calculated but the objects from the non rotated branch are not moved.
    This Method deletes a specific branch. The order of operations should be:
    1: Delete old mesh objects
    2: Calculate rotated branch
    3: Visualize the rotated branch
    """
    if not isinstance(branch_name, (str, tuple)):
        print("Error: branch_name should be a string or a tuple of strings!")
        return

    # All the objects in the Blender scene are deselected
    bpy.ops.object.select_all(action='DESELECT')
    
    # Objects with the respective branch name are selected
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.name.startswith(branch_name):
            obj.select_set(True)
    
    # Delete the selected objects
    bpy.ops.object.delete()


# --- Functions are called to simulate the polysaccharide structures ---

# Clear the scene
clear_mesh_objects()

# Create initial branch
initial_start_position = (0, 0, 0)
"""
With (0, 1, 0) the initial direction is on the Y axis
with initial_direction set to (0, 1, 0), theta controls the rotation in the XZ plane (or "yaw" around the Y-axis),
theta would control the pitch (rotation around the Y-axis in the XZ plane).
and phi controls the tilt or inclination from the Y-axis.
"""
initial_direction = (0, 1, 0) 
num_monomers_initial = 100

initial_branch = generate_branch(num_monomers_initial, initial_start_position, start_direction=initial_direction, branch_name="initial_branch")

# Rotate the initial_branch and update its graphical representation in Blender
# For orientation towards the z axis rotate in xy = 54°, rotate in xz = 110°
initial_branch = rotate_branch_in_xy(initial_branch, math.radians(54))
initial_branch = rotate_branch_in_xz(initial_branch, math.radians(50))

# Clear initial branch objects from scene to avoid duplication
clear_mesh_objects()

# Recreate the initial branch using its updated positions
recreate_branch_from_positions(initial_branch, "initial_branch")

# Create another branch
num_monomers_second_branch = 20
branching_point_1 = random.randint(24,30)
second_branch = generate_branch(num_monomers=num_monomers_second_branch, start_position=initial_branch[branching_point_1], 
    start_direction=initial_direction, branch_name="second_branch")

# Create another branch
num_monomers_third_branch = 30
branching_point_2 = random.randint(24,30) + branching_point_1
third_branch = generate_branch(num_monomers=num_monomers_third_branch, start_position=initial_branch[branching_point_2],
     start_direction=initial_direction, branch_name="third_branch")
#     
# Create another branch
num_monomers_fourth_branch = 30
branching_point_3 = random.randint(24,30) + branching_point_2
fourth_branch = generate_branch(num_monomers=num_monomers_fourth_branch, start_position=initial_branch[branching_point_3],
     start_direction=initial_direction, branch_name="fourth_branch")
#Try to change the position of the branch in the xy plane
fourth_branch = rotate_branch_in_xy(fourth_branch, math.radians(110))
"""
Recreate the initial branch using its updated positions
For demonstration the clear_specific_branch line of code can be deleted
The non rotated fourth branch will then be displayed but also the rotated branch
Thats why the steps are important:
    1: Create branch
    2: Rotate branch
    3: Clear visualization of old non rotated branch
    4: Visualize rotated branch by using recreate_branch_from_positions method 
"""
clear_specific_branch(branch_name="fourth_branch")
recreate_branch_from_positions(fourth_branch, "fourth_branch")
