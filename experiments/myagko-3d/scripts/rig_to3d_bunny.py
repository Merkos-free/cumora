#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import bpy
from mathutils import Vector


def args():
    a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument('--base-blend',required=True); p.add_argument('--generated-glb',required=True); p.add_argument('--output',required=True); p.add_argument('--preview',required=True); p.add_argument('--summary',required=True); return p.parse_args(a)

def bbox(objs):
    lo=Vector((1e9,1e9,1e9)); hi=Vector((-1e9,-1e9,-1e9))
    for o in objs:
        if o.type!='MESH': continue
        for c in o.bound_box:
            w=o.matrix_world@Vector(c)
            for i in range(3): lo[i]=min(lo[i],w[i]); hi[i]=max(hi[i],w[i])
    return lo,hi

def main():
    a=args(); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(Path(a.base_blend).resolve()))
    base_meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    blo,bhi=bbox(base_meshes); bsize=bhi-blo; bcenter=(blo+bhi)/2
    for o in list(base_meshes): bpy.data.objects.remove(o,do_unlink=True)
    # import generated model
    bpy.ops.import_scene.gltf(filepath=str(Path(a.generated_glb).resolve()))
    gen=[o for o in bpy.context.selected_objects if o.type=='MESH']
    if not gen: gen=[o for o in bpy.context.scene.objects if o.type=='MESH']
    glo,ghi=bbox(gen); gsize=ghi-glo; gcenter=(glo+ghi)/2
    s=min(bsize.x/max(gsize.x,1e-6), bsize.y/max(gsize.y,1e-6), bsize.z/max(gsize.z,1e-6))
    roots=[o for o in gen if o.parent not in gen]
    for o in roots:
        o.scale*=s
    bpy.context.view_layer.update(); glo,ghi=bbox(gen); gcenter=(glo+ghi)/2
    delta=bcenter-gcenter
    for o in roots: o.location+=delta
    bpy.context.view_layer.update()
    # join meshes for robust automatic weights
    bpy.ops.object.select_all(action='DESELECT')
    for o in gen: o.select_set(True)
    bpy.context.view_layer.objects.active=gen[0]
    if len(gen)>1: bpy.ops.object.join()
    mesh=bpy.context.object; mesh.name='MYAGKO_Premium_Bunny'
    # improve smoothing
    for p in mesh.data.polygons: p.use_smooth=True
    # parent to existing armature, automatic weights
    bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active=arm
    try: bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    except Exception:
        bpy.ops.object.parent_set(type='ARMATURE_NAME')
    # story action on existing named bones
    action=bpy.data.actions.new('MYAGKO_ScrollStory'); arm.animation_data_create(); arm.animation_data.action=action
    frame_keys=[1,24,48,72,96,120]
    arm.rotation_mode='XYZ'; base_loc=arm.location.copy(); base_rot=arm.rotation_euler.copy()
    for f,dz,ry in [(1,0,0),(24,.03,-.05),(48,.12,.05),(72,.26,-.06),(96,.44,.07),(120,.58,0)]:
        arm.location=base_loc+Vector((0,0,dz)); arm.rotation_euler=base_rot.copy(); arm.rotation_euler[1]+=ry; arm.keyframe_insert('location',frame=f); arm.keyframe_insert('rotation_euler',frame=f)
    def pb(name): return arm.pose.bones.get(name)
    for name,axis,vals in [
        ('head',1,[0,.05,-.05,.1,-.04,0]),
        ('leftEar_1',0,[0,.12,-.18,.22,-.12,0]),('rightEar_1',0,[0,-.12,.18,-.22,.12,0]),
        ('leftHand_1',2,[0,.18,.42,.7,.35,.1]),('rightHand_1',2,[0,-.18,-.42,-.7,-.35,-.1]),
        ('leftLeg_1',0,[0,.04,-.06,.08,-.04,0]),('rightLeg_1',0,[0,-.04,.06,-.08,.04,0])]:
        b=pb(name)
        if not b: continue
        b.rotation_mode='XYZ'; orig=b.rotation_euler.copy()
        for f,v in zip(frame_keys,vals): b.rotation_euler=orig.copy(); b.rotation_euler[axis]+=v; b.keyframe_insert('rotation_euler',frame=f)
    bpy.context.scene.frame_start=1; bpy.context.scene.frame_end=120; bpy.context.scene.render.fps=30; bpy.context.scene.frame_set(54)
    # preview floor / camera / lights
    lo,hi=bbox([mesh]); size=hi-lo; center=(lo+hi)/2; md=max(size.x,size.y,size.z,.1)
    bpy.ops.mesh.primitive_plane_add(size=md*7, location=(center.x,center.y,lo.z-.008)); floor=bpy.context.object
    fm=bpy.data.materials.new('PreviewFloor'); fm.diffuse_color=(.25,.19,.18,1); fm.roughness=.9; floor.data.materials.append(fm)
    camd=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',camd); bpy.context.scene.collection.objects.link(cam); cam.location=(center.x+md*1.25,center.y-md*2.6,center.z+md*.75); cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler(); camd.lens=62; bpy.context.scene.camera=cam
    def area(name,loc,energy,color):
        d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.size=md*2.3; d.color=color; o=bpy.data.objects.new(name,d); bpy.context.scene.collection.objects.link(o); o.location=loc; o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    area('Key',(center.x-md*1.6,center.y-md*1.8,center.z+md*1.8),280,(1,.78,.72)); area('Fill',(center.x+md*2,center.y-md*.7,center.z+md),160,(.78,.86,1)); area('Rim',(center.x,center.y+md*1.5,center.z+md*1.7),250,(1,.55,.68))
    world=bpy.context.scene.world or bpy.data.worlds.new('World'); bpy.context.scene.world=world; world.use_nodes=True; world.node_tree.nodes['Background'].inputs['Color'].default_value=(.018,.014,.014,1); world.node_tree.nodes['Background'].inputs['Strength'].default_value=.15
    sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=900; sc.render.resolution_y=900; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.filepath=str(Path(a.preview).resolve()); sc.view_settings.look='Medium High Contrast'; sc.view_settings.exposure=-.3; bpy.ops.render.render(write_still=True)
    # export only mesh + armature
    bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active=arm
    bpy.ops.export_scene.gltf(filepath=str(out.resolve()),export_format='GLB',use_selection=True,export_animations=True,export_skins=True,export_morph=True,export_yup=True)
    summary={'mesh':mesh.name,'vertices':len(mesh.data.vertices),'polygons':len(mesh.data.polygons),'armature':arm.name,'bones':[b.name for b in arm.data.bones],'action':'MYAGKO_ScrollStory','frames':[1,120],'glbBytes':out.stat().st_size,'previewBytes':Path(a.preview).stat().st_size}
    Path(a.summary).write_text(json.dumps(summary,ensure_ascii=False,indent=2)); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
