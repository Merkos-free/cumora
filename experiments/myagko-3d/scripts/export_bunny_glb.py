#!/usr/bin/env python3
"""Open the downloaded Bunny Soft Toy .blend, add a tiny showcase idle,
render a preview, and export a browser-ready GLB while preserving the armature.
Runs inside Blender in background mode.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--preview", required=True)
    p.add_argument("--summary", required=True)
    return p.parse_args(argv)


def model_objects():
    objs = [o for o in bpy.context.scene.objects if o.type in {"MESH", "ARMATURE"} and not o.hide_get()]
    meshes = [o for o in objs if o.type == "MESH"]
    arms = [o for o in objs if o.type == "ARMATURE"]
    if not meshes:
        raise RuntimeError("No mesh objects found in asset")
    return objs, meshes, arms


def world_bbox(meshes):
    lo = Vector((float("inf"),) * 3)
    hi = Vector((float("-inf"),) * 3)
    for o in meshes:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


def center_model(objs, meshes):
    lo, hi = world_bbox(meshes)
    center_xy = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    roots = [o for o in objs if o.parent not in objs]
    for o in roots:
        o.location -= center_xy
    bpy.context.view_layer.update()
    return world_bbox(meshes)


def ensure_idle(arms):
    if not arms:
        return {"created": False, "reason": "no armature"}
    arm = arms[0]
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    action = bpy.data.actions.new("MYAGKO_Idle")
    arm.animation_data_create()
    arm.animation_data.action = action

    # Whole-character breathing/bounce: safe regardless of bone naming.
    base_z = arm.location.z
    base_rot = arm.rotation_euler.copy()
    for frame, dz, yaw in [(1, 0.0, -0.025), (30, 0.035, 0.025), (60, 0.0, -0.025)]:
        arm.location.z = base_z + dz
        arm.rotation_euler = base_rot
        arm.rotation_euler[2] += yaw
        arm.keyframe_insert(data_path="location", frame=frame)
        arm.keyframe_insert(data_path="rotation_euler", frame=frame)

    names = [b.name for b in arm.pose.bones]
    lower = {b.name: b.name.lower() for b in arm.pose.bones}
    head = next((arm.pose.bones[n] for n, s in lower.items() if "head" in s), None)
    ears = [arm.pose.bones[n] for n, s in lower.items() if "ear" in s][:4]

    if head:
        head.rotation_mode = "XYZ"
        original = head.rotation_euler.copy()
        for frame, tilt in [(1, -0.05), (30, 0.06), (60, -0.05)]:
            head.rotation_euler = original.copy()
            head.rotation_euler[1] += tilt
            head.keyframe_insert(data_path="rotation_euler", frame=frame)
    for idx, ear in enumerate(ears):
        ear.rotation_mode = "XYZ"
        original = ear.rotation_euler.copy()
        sign = -1 if idx % 2 else 1
        for frame, bend in [(1, 0.0), (20, 0.10 * sign), (40, -0.07 * sign), (60, 0.0)]:
            ear.rotation_euler = original.copy()
            ear.rotation_euler[0] += bend
            ear.keyframe_insert(data_path="rotation_euler", frame=frame)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 60
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_set(1)
    return {"created": True, "armature": arm.name, "bones": names, "head": head.name if head else None, "ears": [e.name for e in ears]}


def make_preview(meshes, out_path: str):
    # Clean preview-only cameras/lights; leave model intact.
    for o in list(bpy.data.objects):
        if o.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(o, do_unlink=True)

    lo, hi = world_bbox(meshes)
    size = hi - lo
    center = (lo + hi) / 2
    max_dim = max(size.x, size.y, size.z, 0.1)

    # Soft studio floor.
    bpy.ops.mesh.primitive_plane_add(size=max_dim * 6, location=(0, 0, lo.z - 0.01))
    floor = bpy.context.object
    floor.name = "PREVIEW_Floor"
    mat = bpy.data.materials.new("PREVIEW_FloorMat")
    mat.diffuse_color = (0.92, 0.88, 0.82, 1)
    mat.roughness = 0.92
    floor.data.materials.append(mat)

    # Camera with a slightly elevated product-shot angle.
    cam_data = bpy.data.cameras.new("PREVIEW_Camera")
    cam = bpy.data.objects.new("PREVIEW_Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (max_dim * 2.3, -max_dim * 3.6, max_dim * 1.65)
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = 58
    bpy.context.scene.camera = cam

    def add_area(name, loc, energy, size_area, color):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size_area
        data.color = color
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (center - obj.location).to_track_quat("-Z", "Y").to_euler()
        return obj

    add_area("PREVIEW_Key", (-max_dim * 2.2, -max_dim * 2.7, max_dim * 3.2), 900, max_dim * 3, (1.0, 0.78, 0.68))
    add_area("PREVIEW_Fill", (max_dim * 2.8, -max_dim * 1.0, max_dim * 1.9), 650, max_dim * 2.5, (0.72, 0.82, 1.0))
    add_area("PREVIEW_Rim", (0, max_dim * 2.0, max_dim * 3.0), 1000, max_dim * 2.0, (1.0, 0.6, 0.68))

    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.color = (0.055, 0.045, 0.04)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = out_path
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    scene.frame_set(1)
    bpy.ops.render.render(write_still=True)

    # Mark preview-only objects for easy exclusion from GLB.
    return [floor, cam] + [o for o in bpy.context.scene.objects if o.name.startswith("PREVIEW_") and o.type == "LIGHT"]


def export_glb(model_objs, output: str):
    bpy.ops.object.select_all(action="DESELECT")
    for o in model_objs:
        if o.name in bpy.context.view_layer.objects:
            o.select_set(True)
    active = next((o for o in model_objs if o.type == "ARMATURE"), model_objs[0])
    bpy.context.view_layer.objects.active = active
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output,
        export_format="GLB",
        use_selection=True,
        export_animations=True,
        export_skins=True,
        export_morph=True,
        export_apply=False,
        export_yup=True,
    )


def main():
    args = parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.preview).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(Path(args.input).resolve()))
    objs, meshes, arms = model_objects()
    lo0, hi0 = center_model(objs, meshes)
    idle = ensure_idle(arms)
    preview_objects = make_preview(meshes, str(Path(args.preview).resolve()))
    export_glb(objs, str(Path(args.output).resolve()))

    lo, hi = world_bbox(meshes)
    summary = {
        "objects": [{"name": o.name, "type": o.type} for o in objs],
        "meshes": [{"name": o.name, "vertices": len(o.data.vertices), "polygons": len(o.data.polygons)} for o in meshes],
        "armatures": [{"name": a.name, "bones": [b.name for b in a.data.bones]} for a in arms],
        "materials": sorted({m.name for o in meshes for m in o.data.materials if m}),
        "bbox": {"min": list(lo), "max": list(hi)},
        "idle": idle,
        "glbBytes": Path(args.output).stat().st_size,
        "previewBytes": Path(args.preview).stat().st_size,
    }
    Path(args.summary).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
