# Roto, key and mattes

- Start from the matte requirement: holdout, garbage/core, edge detail, hair, transparency, motion blur or articulated roto.
- Separate matte generation from edge integration so a visually pleasant composite cannot hide a weak alpha.
- Inspect chatter, holes, edge boiling, eroded detail, contaminated transparency, despill and motion-blur continuity over time.
- Use multiple mattes when one operation cannot represent the physical edge behavior cleanly.
- Keep premultiplication state explicit before color or filtering that changes RGB near alpha edges.
- Review first, middle, last and high-motion/stress frames; one clean frame is never sufficient evidence.
