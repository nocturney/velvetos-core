# נעילות VelvetOS Core

1. **role=core** ב־`CORE.json`. אין `INSTANCE.json` בליבה.
2. **מודולים תמיד בליבה** — `modules/`.
3. **presets** = תבניות לפרונט עתידי, לא מתג בליבה.
4. **samples/** = פרופיל ייחוס לחיישנים/תאימות — לא פרונט חי.
5. **instances/** = סקאפולד לפרסום ריפו פרונט נפרד.
6. **חמישה מושבים**. compliance-base בכל מופע.
7. **בלי סודות / PHI בגיט**.
8. **שלוש שכבות** (`LAYERS.md` / `ADR-THREE-LAYERS.md`): Edge ≠ שם הריפו Core; אין broker / runtime שני.
9. **Human gates:** ₪ מכירה · WhatsApp ללקוח · בוסט · Print מ־HQ — לא «אפס התערבות».
10. **Degraded Mode** = failover רשמי (`vfharness/playbooks/degraded-mode.md`) — לא קריסת Pipeline.
