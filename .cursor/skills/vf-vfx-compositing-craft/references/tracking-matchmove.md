# Tracking and matchmove

- Choose point, planar, surface or camera tracking from the motion/geometry evidence rather than convenience.
- Exclude moving/non-rigid regions that violate the track model.
- Verify the track over the entire usable range, including occlusion and high-parallax sections.
- Judge alignment with stable overlay/reference points and not only a tracker confidence number.
- Preserve lens/distortion assumptions consistently between tracking, CG and comp.
- When a track is used to drive roto, cleanup or CG, validate the downstream result as well as the track itself.
