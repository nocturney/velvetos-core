#target photoshop
/* VelvetOS product-layer extractor. Select Subject only; no Firefly / Generative Fill. */
(function () {
    app.displayDialogs = DialogModes.NO;

    function readText(path) {
        var f = new File(path);
        if (!f.exists) throw new Error("config missing: " + path);
        f.encoding = "UTF-8";
        f.open("r");
        var text = f.read();
        f.close();
        return text;
    }

    function parseJson(text) {
        if (typeof JSON !== "undefined" && JSON.parse) return JSON.parse(text);
        return eval("(" + text + ")");
    }

    function writeJson(path, value) {
        var f = new File(path);
        if (!f.parent.exists) f.parent.create();
        f.encoding = "UTF-8";
        f.open("w");
        f.write(JSON.stringify(value, null, 2));
        f.close();
    }

    function selectSubject() {
        var desc = new ActionDescriptor();
        desc.putBoolean(stringIDToTypeID("sampleAllLayers"), false);
        executeAction(stringIDToTypeID("autoCutout"), desc, DialogModes.NO);
    }

    function refineEdge(doc) {
        /* Small deterministic edge refinement; never invents product pixels. */
        try { doc.selection.smooth(1); } catch (_) {}
        try { doc.selection.feather(0.6); } catch (_) {}
    }

    function exportProductLayer(item) {
        var sceneFile = new File(item.scene);
        if (!sceneFile.exists) throw new Error("scene missing: " + item.scene);
        var outFile = new File(item.productLayer);
        if (!outFile.parent.exists) outFile.parent.create();

        var doc = app.open(sceneFile);
        var original = doc.activeLayer;
        var cutout = original.duplicate();
        cutout.name = "VF_PRODUCT_LAYER";
        doc.activeLayer = cutout;

        selectSubject();
        refineEdge(doc);
        doc.selection.invert();
        doc.selection.clear();
        doc.selection.deselect();
        original.visible = false;

        var opts = new PNGSaveOptions();
        opts.interlaced = false;
        doc.saveAs(outFile, opts, true, Extension.LOWERCASE);
        doc.close(SaveOptions.DONOTSAVECHANGES);
    }

    var configPath = $.getenv("VF_AE_REEL_CONFIG");
    if (!configPath) throw new Error("VF_AE_REEL_CONFIG is not set");
    var cfg = parseJson(readText(configPath));
    var completed = [];

    try {
        for (var i = 0; i < cfg.scenes.length; i++) {
            exportProductLayer(cfg.scenes[i]);
            completed.push(cfg.scenes[i].id);
        }
        writeJson(cfg.photoshopDone, {
            ok: true,
            stage: "photoshop_product_layers",
            scenes: completed,
            productPixelsSource: "scene_selection_only",
            fireflyUsed: false
        });
    } catch (err) {
        try {
            writeJson(cfg.photoshopDone, {
                ok: false,
                stage: "photoshop_product_layers",
                error: String(err)
            });
        } catch (_) {}
        throw err;
    }
})();