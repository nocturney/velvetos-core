#target aftereffects
/* VelvetOS Adobe Reel builder: deterministic 2.5D motion + Hebrew overlays. */
(function () {
    app.beginUndoGroup("VelvetOS Premium Reel");

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

    function writeMarker(path, value) {
        var f = new File(path);
        if (!f.parent.exists) f.parent.create();
        f.encoding = "UTF-8";
        f.open("w");
        f.write(JSON.stringify(value, null, 2));
        f.close();
    }

    function importFile(path) {
        var f = new File(path);
        if (!f.exists) throw new Error("asset missing: " + path);
        return app.project.importFile(new ImportOptions(f));
    }

    function fitPortrait(layer) {
        var src = layer.source;
        var sx = 1080 / src.width;
        var sy = 1920 / src.height;
        var s = Math.max(sx, sy) * 100;
        var scaleValue = layer.threeDLayer ? [s, s, s] : [s, s];
        layer.property("ADBE Transform Group").property("ADBE Scale").setValue(scaleValue);
        layer.property("ADBE Transform Group").property("ADBE Position").setValue([540, 960, 0]);
    }

    function setOpacityFade(layer, start, end, fade) {
        var op = layer.property("ADBE Transform Group").property("ADBE Opacity");
        op.setValueAtTime(start, 0);
        op.setValueAtTime(start + fade, 100);
        op.setValueAtTime(Math.max(start + fade, end - fade), 100);
        op.setValueAtTime(end, 0);
    }

    function resolveFont(family, weight) {
        try {
            var fonts = app.fonts.getFontsByFamilyName(family);
            var wanted = weight >= 700 ? /Bold|700/i : /SemiBold|600|Medium/i;
            for (var i = 0; i < fonts.length; i++) {
                var label = String(fonts[i].styleName || "") + " " + String(fonts[i].postScriptName || "");
                if (wanted.test(label)) return fonts[i].postScriptName || fonts[i].familyName;
            }
            if (fonts.length) return fonts[0].postScriptName || fonts[0].familyName;
        } catch (_) {}
        return family;
    }

    function hexColor(hex) {
        var h = String(hex).replace("#", "");
        return [
            parseInt(h.substring(0, 2), 16) / 255,
            parseInt(h.substring(2, 4), 16) / 255,
            parseInt(h.substring(4, 6), 16) / 255
        ];
    }

    function addRevealMask(layer, start, duration, width, height) {
        var masks = layer.property("ADBE Mask Parade");
        var mask = masks.addProperty("ADBE Mask Atom");
        mask.name = "VF_LINE_REVEAL";
        var prop = mask.property("ADBE Mask Shape");
        var a = new Shape();
        a.vertices = [[0, -height], [4, -height], [4, height], [0, height]];
        a.closed = true;
        var b = new Shape();
        b.vertices = [[-width, -height], [4, -height], [4, height], [-width, height]];
        b.closed = true;
        prop.setValueAtTime(start, a);
        prop.setValueAtTime(start + duration, b);
    }

    function addHebrewText(comp, value, pos, size, weight, color, start, end) {
        var layer = comp.layers.addText(value);
        layer.name = "VF_HE_" + value;
        var textProp = layer.property("ADBE Text Properties").property("ADBE Text Document");
        var td = textProp.value;
        td.font = resolveFont("Rubik", weight); // committed Rubik, headline 700 / subhead 600
        td.fontSize = size;
        td.fillColor = color;
        td.applyFill = true;
        td.applyStroke = false;
        td.justification = ParagraphJustification.RIGHT_JUSTIFY;
        try {
            if (typeof ParagraphDirection !== "undefined") td.direction = ParagraphDirection.RIGHT_TO_LEFT;
        } catch (_) {}
        if (weight >= 700) td.fauxBold = true;
        textProp.setValue(td);
        layer.property("ADBE Transform Group").property("ADBE Position").setValue(pos);
        layer.inPoint = start;
        layer.outPoint = end;
        addRevealMask(layer, start + 0.05, 0.42, 760, size * 0.72);
        return layer;
    }

    function addAccentRule(comp, y, color, start, end) {
        var shape = comp.layers.addShape();
        shape.name = "VF_ACCENT_RULE_WIPE";
        var contents = shape.property("ADBE Root Vectors Group");
        var group = contents.addProperty("ADBE Vector Group");
        var rect = group.property("ADBE Vectors Group").addProperty("ADBE Vector Shape - Rect");
        rect.property("ADBE Vector Rect Size").setValue([180, 8]);
        var fill = group.property("ADBE Vectors Group").addProperty("ADBE Vector Graphic - Fill");
        fill.property("ADBE Vector Fill Color").setValue(color);
        shape.property("ADBE Transform Group").property("ADBE Position").setValue([770, y]);
        var scale = shape.property("ADBE Transform Group").property("ADBE Scale");
        scale.setValueAtTime(start, [0, 100]);
        scale.setValueAtTime(start + 0.38, [100, 100]);
        shape.inPoint = start;
        shape.outPoint = end;
        return shape;
    }

    function addSunlightSweep(comp, duration) {
        var light = comp.layers.addSolid([1.0, 0.78, 0.53], "VF_SOFT_SUNLIGHT_SWEEP", 900, 2300, 1, duration);
        light.blendingMode = BlendingMode.SCREEN;
        light.property("ADBE Transform Group").property("ADBE Opacity").setValue(11);
        light.property("ADBE Transform Group").property("ADBE Rotation").setValue(-18);
        var pos = light.property("ADBE Transform Group").property("ADBE Position");
        pos.setValueAtTime(0, [-450, 920]);
        pos.setValueAtTime(duration, [1530, 920]);
        try {
            var blur = light.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2");
            blur.property(1).setValue(140);
        } catch (_) {}
        return light;
    }

    function addDust(comp, duration) {
        try {
            var dust = comp.layers.addSolid([0, 0, 0], "VF_SUBTLE_DUST", 1080, 1920, 1, duration);
            dust.blendingMode = BlendingMode.SCREEN;
            dust.property("ADBE Transform Group").property("ADBE Opacity").setValue(16);
            dust.property("ADBE Effect Parade").addProperty("CC Particle World");
            return dust;
        } catch (_) {
            return null;
        }
    }

    function addEndCard(comp, cfg, start, duration) {
        var bg = comp.layers.addSolid([0.015, 0.02, 0.028], "VF_END_CARD_BG", 1080, 1920, 1, duration);
        bg.inPoint = start;
        bg.outPoint = duration;
        setOpacityFade(bg, start, duration, 0.28);

        var logoItem = importFile(cfg.assets.logo);
        var logo = comp.layers.add(logoItem);
        logo.name = "VF_EXACT_GOLD_LOGO";
        logo.inPoint = start;
        logo.outPoint = duration;
        logo.property("ADBE Transform Group").property("ADBE Position").setValue([540, 760]);
        var sw = logoItem.width ? 420 / logoItem.width * 100 : 60;
        logo.property("ADBE Transform Group").property("ADBE Scale").setValue([sw, sw]);

        addHebrewText(comp, cfg.copy.cta, [720, 1100], 46, 700, [1, 1, 1], start + 0.35, duration);
    }

    var configPath = $.getenv("VF_AE_REEL_CONFIG");
    if (!configPath) throw new Error("VF_AE_REEL_CONFIG is not set");
    var cfg = parseJson(readText(configPath));
    var duration = cfg.canvas.durationSeconds;

    try {
        app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    } catch (_) {}
    app.newProject();

    var comp = app.project.items.addComp("VF_REEL_MASTER", 1080, 1920, 1, duration, 30);
    comp.bgColor = [0.01, 0.01, 0.01];

    var SAFE_TOP = 150;
    var SAFE_BOTTOM = 384; // bottom 20% of 1920
    var SAFE_RIGHT_BUTTON_STRIP = 190;
    var COPY_RIGHT_X = 1080 - SAFE_RIGHT_BUTTON_STRIP - 30;
    var sceneBeats = cfg.storyboard.scenes;

    for (var i = 0; i < cfg.scenes.length; i++) {
        var scene = cfg.scenes[i];
        var beat = sceneBeats[i];
        var plateItem = importFile(scene.emptyPlate);
        var productItem = importFile(scene.productLayer);
        var plate = comp.layers.add(plateItem);
        var product = comp.layers.add(productItem);
        plate.name = "VF_PLATE_" + scene.id;
        product.name = "VF_PRODUCT_" + scene.id;
        plate.threeDLayer = true;
        product.threeDLayer = true;
        fitPortrait(plate);
        fitPortrait(product);
        plate.property("ADBE Transform Group").property("ADBE Position").setValue([540, 960, 140]);
        product.property("ADBE Transform Group").property("ADBE Position").setValue([540, 960, 0]);
        plate.inPoint = beat.start;
        plate.outPoint = beat.end;
        product.inPoint = beat.start;
        product.outPoint = beat.end;
        setOpacityFade(plate, beat.start, beat.end, 0.18);
        setOpacityFade(product, beat.start, beat.end, 0.18);
        var ps = product.property("ADBE Transform Group").property("ADBE Scale");
        var baseScale = ps.value;
        ps.setValueAtTime(beat.start, baseScale);
        ps.setValueAtTime(beat.end, [
            baseScale[0] * 1.025,
            baseScale[1] * 1.025,
            baseScale.length > 2 ? baseScale[2] : 100
        ]);
    }

    var camera = comp.layers.addCamera("VF_2_5D_CAMERA", [540, 960]);
    camera.property("ADBE Transform Group").property("ADBE Position").setValueAtTime(0, [540, 960, -2400]);
    camera.property("ADBE Transform Group").property("ADBE Position").setValueAtTime(duration, [540, 960, -2140]);
    try {
        var camOpts = camera.property("ADBE Camera Options Group");
        camOpts.property("ADBE Camera Depth of Field").setValue(1);
        camOpts.property("ADBE Camera Aperture").setValue(42);
        var focus = camOpts.property("ADBE Camera Focus Distance");
        focus.setValueAtTime(0, 2400);
        focus.setValueAtTime(duration * 0.52, 2260);
        focus.setValueAtTime(duration, 2400);
    } catch (_) {}

    addSunlightSweep(comp, duration);
    if (cfg.enableDust !== false) addDust(comp, duration);

    if (cfg.audioStrategy && cfg.audioStrategy.file) {
        var audioItem = importFile(cfg.audioStrategy.file);
        var audioLayer = comp.layers.add(audioItem);
        audioLayer.name = "VF_APPROVED_AUDIO";
        audioLayer.startTime = 0;
        audioLayer.inPoint = 0;
        audioLayer.outPoint = Math.min(duration, audioItem.duration || duration);
    }

    var accent = hexColor(cfg.copy.accentHex);
    var copyEnd = Math.min(duration - 2.2, 9.8);
    addHebrewText(comp, cfg.copy.headlineLines[0], [COPY_RIGHT_X, SAFE_TOP + 170], 92, 700, [1, 1, 1], 0.25, copyEnd);
    addHebrewText(comp, cfg.copy.headlineLines[1], [COPY_RIGHT_X, SAFE_TOP + 270], 92, 700, accent, 0.55, copyEnd);
    addAccentRule(comp, SAFE_TOP + 345, accent, 0.92, copyEnd);
    addHebrewText(comp, cfg.copy.subhead, [COPY_RIGHT_X, SAFE_TOP + 430], 34, 600, [0.96, 0.96, 0.96], 1.10, copyEnd);
    addHebrewText(comp, cfg.copy.icons.join("   •   "), [COPY_RIGHT_X, SAFE_TOP + 500], 25, 600, [0.91, 0.91, 0.91], 1.65, copyEnd);

    for (var d = 0; d < cfg.copy.detailLabels.length && d < cfg.storyboard.details.length; d++) {
        var detail = cfg.storyboard.details[d];
        addHebrewText(comp, cfg.copy.detailLabels[d], [420, 1920 - SAFE_BOTTOM - 72], 30, 600, accent, detail.start, detail.end);
    }

    var endStart = Math.max(duration - 2.1, 10.0);
    addEndCard(comp, cfg, endStart, duration);

    var rq = app.project.renderQueue.items.add(comp);
    var om = rq.outputModule(1);
    try { om.applyTemplate("Lossless"); } catch (_) {}
    om.file = new File(cfg.losslessOutput);

    app.project.save(new File(cfg.aepFile));
    writeMarker(cfg.afterEffectsDone, {
        ok: true,
        stage: "after_effects_build",
        comp: "VF_REEL_MASTER",
        width: 1080,
        height: 1920,
        fps: 30,
        durationSeconds: duration,
        safeTop: SAFE_TOP,
        safeBottom: SAFE_BOTTOM,
        safeRightButtonStrip: SAFE_RIGHT_BUTTON_STRIP
    });

    app.endUndoGroup();
})();