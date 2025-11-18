import maya.cmds as cmds
import maya.api.OpenMaya as om
import random
import math

# =============================
# UI
# =============================
win = "heightScatterWin"
if cmds.window(win, exists=True):
    cmds.deleteUI(win)

cmds.window(win, title="Height-Based Scatter Tool", widthHeight=(320, 300))
cmds.columnLayout(adj=True, rowSpacing=8)

cmds.text(label="Scatter Object")
scatterField = cmds.textFieldButtonGrp(label="", buttonLabel="Pick", text="")
cmds.textFieldButtonGrp(scatterField, e=True, buttonCommand=lambda: set_selected(scatterField))

cmds.text(label="Base Surface")
baseField = cmds.textFieldButtonGrp(label="", buttonLabel="Pick", text="")
cmds.textFieldButtonGrp(baseField, e=True, buttonCommand=lambda: set_selected(baseField))

cmds.separator(h=10)
cmds.text(label="Scatter Settings")

cmds.intSliderGrp("sampleCount", label="Sample Count", field=True, minValue=50, maxValue=10000, value=1000)

cmds.floatSliderGrp("scaleMin", label="Scale Min", field=True, minValue=0.0, maxValue=10.0, value=0.5)
cmds.floatSliderGrp("scaleMax", label="Scale Max", field=True, minValue=0.0, maxValue=10.0, value=1.5)

cmds.floatSliderGrp("rotYMin", label="Rotation Y Min", field=True, minValue=-180, maxValue=180, value=0)
cmds.floatSliderGrp("rotYMax", label="Rotation Y Max", field=True, minValue=-180, maxValue=180, value=360)

cmds.separator(h=10)

cmds.button(
    label="Scatter!",
    height=40,
    bgc=(0.3, 0.6, 0.3),
    command=lambda *_: scatter_on_surface(
        cmds.textFieldButtonGrp(scatterField, q=True, text=True),
        cmds.textFieldButtonGrp(baseField, q=True, text=True)
    )
)

cmds.showWindow(win)


# =============================
# Helper for selecting objects
# =============================
def set_selected(field):
    sel = cmds.ls(sl=True)
    if sel:
        cmds.textFieldButtonGrp(field, e=True, text=sel[0])


# =============================
# Scatter Function
# =============================
def scatter_on_surface(scatterObj, surface):
    if not scatterObj or not surface:
        cmds.warning("Pick both scatter object and base surface.")
        return

    sel = om.MSelectionList()
    sel.add(surface)
    dagPath = sel.getDagPath(0)
    mfnMesh = om.MFnMesh(dagPath)

    sampleCount = cmds.intSliderGrp("sampleCount", q=True, value=True)

    scaleMin = cmds.floatSliderGrp("scaleMin", q=True, value=True)
    scaleMax = cmds.floatSliderGrp("scaleMax", q=True, value=True)
    rotYMin = cmds.floatSliderGrp("rotYMin", q=True, value=True)
    rotYMax = cmds.floatSliderGrp("rotYMax", q=True, value=True)

    bbox = cmds.exactWorldBoundingBox(surface)
    minY, maxY = bbox[1], bbox[4]

    created = []

    for i in range(sampleCount):

        point, normal = sample_point_on_mesh(mfnMesh)

        y = point.y
        t = (y - minY) / (maxY - minY)
        density = 1.0 - t

        if random.random() < density:
            inst = cmds.instance(scatterObj)[0]
            cmds.move(point.x, point.y, point.z, inst, absolute=True)

            # Align to surface normal
            euler = normal_to_euler(normal)

            # Random Y rotation
            extraY = random.uniform(rotYMin, rotYMax)
            euler = (euler[0], euler[1] + extraY, euler[2])

            cmds.xform(inst, ws=True, rotation=euler)

            # Random scale
            s = random.uniform(scaleMin, scaleMax)
            cmds.scale(s, s, s, inst)

            created.append(inst)

    # =============================
    # GROUP ALL SCATTERED OBJECTS
    # =============================
    if created:
        grp = cmds.group(created, name="scattered_grp#")
        print("Created", len(created), "instances grouped under:", grp)
    else:
        print("No objects created.")


# ==========================================
# Random Mesh Sampling using OpenMaya
# ==========================================
def sample_point_on_mesh(mfnMesh):
    polyCount = mfnMesh.numPolygons
    polyId = random.randint(0, polyCount - 1)

    verts = mfnMesh.getPolygonVertices(polyId)
    if len(verts) < 3:
        return om.MPoint(0,0,0), om.MVector(0,1,0)

    p0 = mfnMesh.getPoint(verts[0], om.MSpace.kWorld)
    p1 = mfnMesh.getPoint(verts[1], om.MSpace.kWorld)
    p2 = mfnMesh.getPoint(verts[2], om.MSpace.kWorld)

    u = random.random()
    v = random.random()
    if u + v > 1.0:
        u = 1.0 - u
        v = 1.0 - v
    w = 1.0 - u - v

    x = p0.x * w + p1.x * u + p2.x * v
    y = p0.y * w + p1.y * u + p2.y * v
    z = p0.z * w + p1.z * u + p2.z * v
    point = om.MPoint(x, y, z)

    normal = mfnMesh.getPolygonNormal(polyId, om.MSpace.kWorld)
    return point, normal


# ==========================================
# Convert normal to Euler
# ==========================================
def normal_to_euler(n):
    nx, ny, nz = n.x, n.y, n.z
    yaw = math.degrees(math.atan2(nx, nz))
    hyp = math.sqrt(nx*nx + nz*nz)
    pitch = -math.degrees(math.atan2(ny, hyp))
    return (pitch, yaw, 0)
