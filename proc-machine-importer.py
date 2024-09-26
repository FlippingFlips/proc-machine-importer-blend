import sys, bpy, json, math, glob

# the size of the playfield will be replace by arguments if any given, see example next line:
# Blender --factory-startup --background --python GeneratePlayfieldAndItems.py -- 514.350 1066.8 12
pf_width = 514.350
pf_length = 1066.8
pf_thickness = 12
machine_json_path = 'machine.json'
cut_holes = True
export_file_name = "newfile.blend"
# default object name, make sure it exists in the obj_converted directory
# - name can be set in the json under objName
# - names should match for blender
default_light_insert = "25mmSquare"
hide_inserts = False

C = bpy.context
# set metric millimeters in the file and scale for precision
C.scene.unit_settings.system = 'METRIC'
C.scene.unit_settings.length_unit = 'MILLIMETERS'
C.scene.unit_settings.scale_length = 0.001

# get arguments passed into script after blender
argv = sys.argv
argv = argv[argv.index("--") + 1:]
if argv is not None:
    i = 0    
    for arg in argv:
        if i == 0:
            pf_width = float(arg)
        elif i == 1:
            pf_length = float(arg)
        elif i == 2:
            pf_thickness = float(arg)
        i+=1

#sys.exit()

def select_collection(name):
    bpy.context.view_layer.active_layer_collection = bpy.data.scenes['Scene'].view_layers['ViewLayer'].layer_collection.children[name]

def set_boolean_modifiers(collectionName, hide=False):
    # set up a boolean operator on every item to cut hole
    # hide it, so when opened the playfield is cut.
    for led in bpy.data.collections[collectionName].all_objects:
        led.select_set(True)
        b = playfield.modifiers.new(type="BOOLEAN", name=led.name)
        b.object = led
        b.operation = "DIFFERENCE"    
        led.hide_set(hide) ## TODO- change this to hide the collection not every led

def generate_collection(collectionName, jsonSection):
    # set up a CNC insert for every LED
    # - get the insert object for the item, make a copy of it
    # - move it into a collection

    target_collection = C.scene.collection.children.get(collectionName)

    for led in json_data[jsonSection]:    
        
        for x in range(1, 3):            
            if led["ObjName"] is None:
                insert_obj = bpy.data.objects[default_light_insert + ".00" + str(x)]
            else:
                insert_obj = bpy.data.objects[led["ObjName"] + ".00" + str(x)]

            # select and duplicate the insert to get new transforms
            insert_obj.select_set(True)
            bpy.context.view_layer.objects.active = insert_obj    
            bpy.ops.object.duplicate(linked=False)

            # select the copy and rename it to the machine item
            selected = bpy.context.selected_objects[0]
            selected.name = led["Name"] + ".00" + str(x) 

            #set pos
            pos = ((led["XPos"]), -(led["YPos"]), 0.00)
            selected.location = pos    

            #set rotate
            if led["ZRot"] is not None:
                if led["ZRot"] > 0:
                    selected.rotation_euler[2] = math.radians(-led["ZRot"])
            else:
                selected.rotation_euler[2] = 0

            # link to another collection and remove from the old
            target_collection.objects.link(selected)    
            from_collection.objects.unlink(selected)

            # set selection off because it will duplicate selections
            selected.select_set(False)



# Read in a machine.json (PROC)
json_data = {}
with open(machine_json_path, 'r') as f:
    json_data = json.load(f)
    #json_data = json.loads(str)    

# Default scene Camera clip
#C.scene.camera.space_data.clip_end = 100000
# delete std cube
bpy.ops.object.delete()
bpy.data.objects['Camera'].select_set(True)
bpy.ops.object.delete()
bpy.data.objects['Light'].select_set(True)
bpy.ops.object.delete()

# create and link some collections
switches = bpy.data.collections.new("SWITCHES")
C.scene.collection.children.link(switches)
leds = bpy.data.collections.new("LEDS")
C.scene.collection.children.link(leds)
lamps = bpy.data.collections.new("LAMPS")
C.scene.collection.children.link(lamps)
drivers = bpy.data.collections.new("DRIVERS")
C.scene.collection.children.link(drivers)

# create playfield: set the playfield with -Y going down the playfield, by flippers on the Y: -900 or so
bpy.ops.mesh.primitive_cube_add()
playfield = C.selected_objects[0]
playfield.name = "Playfield"
playfield.dimensions = (pf_width, pf_length, pf_thickness)
playfield.location = (pf_width / 2, -(pf_length / 2), -(pf_thickness / 2))
bpy.ops.object.transform_apply(location = True, scale = True, rotation = True)

# create the CNC collection for storing inserts
cnc = bpy.data.collections.new("CNC")
C.scene.collection.children.link(cnc)

# get all the available objects and import them to CNC collection
select_collection("CNC")
for file in glob.glob("./obj_converted/*.obj"):
    bpy.ops.wm.obj_import(filepath=file)

print(list(bpy.data.objects))

# set up collections to move inserts to
from_collection = C.scene.collection.children.get("CNC")

playfield.select_set(False)

generate_collection("LEDS", "PRLeds") # create led collection items
if cut_holes:
    set_boolean_modifiers("LEDS", hide_inserts) # cut led holes

generate_collection("LAMPS", "PRLamps") # create led collection items
if cut_holes:
    set_boolean_modifiers("LAMPS", hide_inserts) # cut lamp holes

# remove CNC collection
collection_to_delete = bpy.data.collections['CNC']
bpy.data.collections.remove(collection_to_delete)    

# Save the current Blender file with a specified filepath
filepath = export_file_name
bpy.ops.wm.save_as_mainfile(filepath=filepath)

# quit blender
bpy.ops.wm.quit_blender()