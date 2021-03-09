import bpy
from wreckfest_toolbox.utils import car_export_validator as validator


collection_usage = [
    ("NOT", "Don't use", "Don't use the collection"),
    ("ADD", "Add", "Add the object to the collection"),
    ("MOVE", "Move", "Move the object to the collection")
]


def move_gameplay_object_to_collection(contex: bpy.types.Context, obj: bpy.types.Object, collection_name: str):
    if collection_name in bpy.data.collections and obj.name not in bpy.data.collections[collection_name].objects:
        for collection in obj.users_collection:
            collection.objects.unlink(obj)

        collection = bpy.data.collections[collection_name]
        collection.objects.link(obj)


class WFTB_OT_create_car_collisions(bpy.types.Operator):
    """Check if the scene contain the top & bottom collision (objects named : collision_bottom & collision_top)
    If not, the operator will create them. And finally the operator will check if the good Custom Data was set"""
    bl_idname = "wftb.create_car_collisions"
    bl_label = "Car : Validate/Create collisions"

    def execute(self, context):
        if 'body' not in bpy.data.objects:
            return {'CANCELLED'}

        body = bpy.data.objects['body']

        if 'collision_bottom' not in bpy.data.objects:
            bpy.ops.mesh.primitive_cube_add()
            cube = bpy.context.active_object
            cube.name = 'collision_bottom'
            bpy.context.active_object.dimensions = body.dimensions
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        collision_bottom = bpy.data.objects['collision_bottom']

        # TODO : Use WreckfestCustomDataGroup property instead of hard coding it
        collision_bottom["WF_IsCollisionModel"] = 1
        
        move_gameplay_object_to_collection(context, cube, "Collisions")

        if 'collision_top' not in bpy.data.objects:
            bpy.ops.mesh.primitive_cube_add()
            cube = bpy.context.active_object
            cube.name = 'collision_top'
            bpy.context.active_object.dimensions = [body.dimensions.x, body.dimensions.y/2, body.dimensions.z/2]
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        collision_top = bpy.data.objects['collision_top']

        # TODO : Use WreckfestCustomDataGroup property instead of hard coding it
        collision_top["WF_IsCollisionModel"] = 1
        
        move_gameplay_object_to_collection(context, cube, "Collisions")

        return {'FINISHED'}

class WFTB_OT_create_car_proxy(bpy.types.Operator):
    """Create an object that will be treated as proxy by Wreckfest Build Asset"""
    bl_idname="wftb.create_car_proxy"
    bl_label="Create Car Proxy"
    bl_options={"UNDO"}
    
    proxy_name: bpy.props.StringProperty(name="Proxy Name", default="body")
    
    def execute(self, context):
    
        if 'body' not in bpy.data.objects:
                return {'CANCELLED'}

        body = bpy.data.objects['body']
        # Create a cube
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.name = "proxy_" + self.proxy_name
        context.active_object.dimensions = body.dimensions
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        context.active_object["WF_IsCollisionModel"] = True
        
        validator.move_gameplay_object_to_collection(context, cube, "Proxies")
            
        return {'FINISHED'}
        
    def draw(self, context):
        self.layout.prop(self, "proxy_name")

class WFTB_OT_validate_collision_spheres(bpy.types.Operator):
    """Get all the collision spheres (object with name starting with collision_sphere_) and name them correctly.
    It also add the good property on it (IsCollisionModel). And add them to Collision Spheres collection if wanted"""
    bl_idname = "wftb.validate_collision_spheres"
    bl_label = "Validate Collision Spheres"
    bl_options = {"UNDO", "REGISTER"}

    use_collection: bpy.props.EnumProperty(
        items=collection_usage,
        name="Move to collection",
        description="Move the collision spheres to the Collision Spheres collection, it create the collection if needed",
        default="NOT"
    )

    def invoke(self, context: 'Context', event: 'Event'):
        # Get all the spheres
        spheres = validator.get_collision_spheres(context)
        counter = 0
        # Rename with fake names sor I avoid the .001
        for sphere in spheres:
            sphere.name = "collision_sphere_" + str(counter) + "_tmp"
            counter += 1

        # Apply the correct name
        counter = 0
        for sphere in spheres:
            sphere.name = "collision_sphere_" + str(counter)
            counter += 1

        return {'FINISHED'}

    def execute(self, context: bpy.types.Context):
        collection = None
        if self.use_collection != "NOT":
            if "Collision Spheres" not in bpy.data.collections:
                collection = bpy.data.collections.new("Collision Spheres")
                context.scene.collection.children.link(collection)
            collection = bpy.data.collections["Collision Spheres"]

        spheres = validator.get_collision_spheres(context)
        for sphere in spheres:
            if self.use_collection == "MOVE":
                move_gameplay_object_to_collection(context, sphere, collection.name)
            elif self.use_collection == "ADD" and collection not in sphere.users_collection:
                collection.objects.link(sphere)

        return {"FINISHED"}

    def draw(self, context: bpy.types.Context):
        column = self.layout.column()
        column.prop(self, "use_collection")
        return