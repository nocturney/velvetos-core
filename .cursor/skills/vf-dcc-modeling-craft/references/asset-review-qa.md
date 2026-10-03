# DCC asset review QA

Use for production review after form/topology work and before declaring an asset ready for downstream use.

- Review silhouette and proportions before wireframe quality; topology that preserves a wrong form is still wrong.
- Inspect shaded, wireframe and normal/face-orientation views where available.
- For deforming assets, test representative extreme poses or deformation zones instead of inferring readiness from edge loops alone.
- For subdivision assets, compare cage and subdivided result for pinching, waviness, unintended shrinkage and support-loop artifacts.
- For hard-surface assets, inspect long specular highlights to expose normal and topology defects.
- For bake targets, inspect the utility maps directly and compare them with the high/low relationship.
- Check transforms, scale, axes/origin and exported bounding dimensions against the intended downstream convention.
- Inspect the exported artifact independently when possible; scene cleanliness does not guarantee exported correctness.
- Capture one neutral turntable or multi-view evidence set when review repeatability matters.

Report which downstream use was tested: static render, deformation, subdivision, bake, print, exchange or another declared target.