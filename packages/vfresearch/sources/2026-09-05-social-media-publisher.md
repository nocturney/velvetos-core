# Social Media Publisher embed · 2026-09-05

מושב: ייצור (`@research-synthesist`) → צמיחה (`@instagram-curator` / vfigos)  
מקור שנשלח: https://mcpmarket.com/tools/skills/social-media-publisher-2  
מקור גוף (failover): https://github.com/ndesv21/socialclaw/blob/main/skill/SKILL.md  
גם: skillselion / SkillsAuth mirrors של social-publishing / social-publisher

## חומת מקור

| URL | תוצאה |
|---|---|
| mcpmarket.com/…/social-media-publisher-2 | Cloudflare «We're verifying your browser» → **«אין גוף»** |
| raw.githubusercontent.com/ndesv21/socialclaw/…/SKILL.md | גוף מלא — SocialClaw skill |
| WebSearch (SocialClaw / social-publisher) | אישור: validate → apply → verify / reconcile |

## תקציר (מה שקראנו)

Skill של פרסום סושיאל מרובה-פלטפורמות דרך שירות hosted (SocialClaw): מפתח workspace אחד, חיבור חשבונות ב-dashboard, העלאת מדיה, **validate/preview לפני apply**, ואז **inspect / reconcile** לפני שמכריזים שפורסם. תומך X, LinkedIn, IG, FB Pages, TikTok, Discord, Telegram, YouTube, Reddit, WordPress, Pinterest.

## פסיקה

`embed` דפוס **validate → apply → verify** על `vfigos` + `vfharness` verification + `vfagents` reflection.  
**לא** התקנת SocialClaw / `npx skills` על Cloud Agent.  
**לא** blast רב-פלטפורמי מ־HQ (TikTok/X/LinkedIn נעולים בלי ראש צוות).  
**לא** API key בגיט. Meta Developer Tools MCP ≠ Publish MCP.

## מה הוטמע

| קובץ | שינוי |
|---|---|
| `vfigos/SEND.md` | שלבי validate / apply / verify + טבלת דפוס |
| `vfigos/SKILL.md` | שורת validate→apply→verify |
| `vfharness/playbooks/verification-before-claim.md` | IG: confirmed vs accepted |
| `vfagents/playbooks/reflection-before-send.md` | verify אחרי apply |
| `vfmcp/GAP.md` | Publish gap + דפוס בלי vendor |
| `vfresearch/BEST-SKILLS.md` | שורת מיפוי social-media-publisher |
| `vfresearch/LINKS.json` | רישום mcpmarket + failover GitHub |
| `BEST-SKILLS.json` | watchlist SocialClaw |

## מה דולג

| מה | למה |
|---|---|
| `npm i -g socialclaw` / `npx skills add` | נעילת Cloud Agent + אין מפתח בגיט |
| OpenClaw skill bundle / second runtime | `vfe2b` LOCK |
| פרסום אוטומטי ל־13 פלטפורמות | מנדט VF = IG `@velvets_cloud` + CTA וואטסאפ; TikTok/ads = ראש צוות |
| אוטו־DM / boost | נעול תמיד |
| טענת «פורסם» מ־providerStatus accepted | דורש verify/reconcile — כבר מיושר ל־`#ממתין-ל-כלי-IG` |

## בלוק 05

קישור social-media-publisher — הוטמע validate→apply→verify ב־`vfigos/SEND`
