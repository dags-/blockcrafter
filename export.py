#!/usr/bin/env python

import os
import sys
import numpy as np
import math
from PIL import Image
from vispy import app, gloo, io, geometry

import mcmodel
import render

assetdir = "assets"
#assetdir = "/home/moritz/.minecraft/versions/1.13/1.13.jar"
w, h = 32, 32
rotation = 0
outdir = "out"

class Canvas(app.Canvas):
    def __init__(self):
        super().__init__()

        self.show()
        self.update()

        self.draw_attempt = False

    def on_draw(self, event):
        if self.draw_attempt:
            self.close()
        self.draw_attempt = True

        model, view, projection = render.create_transform_ortho(aspect=1.0, fake_ortho=True)

        texture = gloo.Texture2D(shape=(w, h, 4))
        depth = gloo.RenderBuffer(shape=(w, h))
        fbo = gloo.FrameBuffer(color=texture, depth=depth)
        fbo.activate()

        gloo.set_viewport(0, 0, w, h)
        gloo.set_clear_color((0.0, 0.0, 0.0, 0.0))
        gloo.set_state(depth_test=True, blend=True)

        finfo = open(os.path.join(outdir, "blocks.txt"), "w")

        assets = mcmodel.Assets(assetdir)
        for blockstate in assets.blockstates:
            print("Taking block %s" % blockstate.name)

            glblock = render.Block(blockstate)
            for index, variant in enumerate(blockstate.variants):
                print("Rendering variant %d/%d" % (index+1, len(blockstate.variants)))

                variant_name = mcmodel.encode_variant(variant)
                if variant_name == "":
                    variant_name = "-"
                block_filename = "%s_%d" % (blockstate.name, index)
                for mode in ("color", "uv"):
                    gloo.clear(color=True, depth=True)

                    actual_model = np.dot(render.create_model_transform(rotation=rotation), model)

                    glblock.render(variant, actual_model, view, projection, mode=mode)

                    image = Image.fromarray(fbo.read("color"))
                    image.save(os.path.join(outdir, "%s_%s.png" % (block_filename, mode)))
                print("%s %s %s %s" % (blockstate.name, variant_name, block_filename + "_color.png", block_filename + "_uv.png"), file=finfo)

        finfo.close()
        fbo.deactivate()
        self.close()

if __name__ == "__main__":
    import vispy
    if "--osmesa" in sys.argv[1:]:
        vispy.use("osmesa")
        assert vispy.app.use_app().backend_name == "osmesa"

    c = Canvas()
    app.run()
