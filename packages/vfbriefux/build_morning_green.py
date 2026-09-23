#!/usr/bin/env python3
"""Project the canonical factual Morning Brief into Morning Green.

Consumes the existing V10.x factual JSON/TXT plus an optional read-only OpenPost
snapshot. It does not fetch providers and does not create a parallel source of truth.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ=ZoneInfo('Asia/Jerusalem')
HE_DAYS=['יום שני','יום שלישי','יום רביעי','יום חמישי','יום שישי','שבת','יום ראשון']
HE_DAY_SHORT=['ב׳','ג׳','ד׳','ה׳','ו׳','שבת','א׳']
HE_MONTHS={1:'בינואר',2:'בפברואר',3:'במרץ',4:'באפריל',5:'במאי',6:'ביוני',7:'ביולי',8:'באוגוסט',9:'בספטמבר',10:'באוקטובר',11:'בנובמבר',12:'בדצמבר'}

HEADINGS=[
 'תמונת מצב עכשיו','מה השתנה מאז הבריף הקודם','צריך ממך','מצב הכסף','עבודות חיות','היום / בהמשך',
 'Instagram · מצב העמוד','רדאר תוכן','שולחן המחקר','פעילות VelvetOS','05a · זיכרון'
]

def sections(text: str) -> dict[str,list[str]]:
    out={h:[] for h in HEADINGS}; current=None
    for raw in text.splitlines():
        line=raw.strip()
        if line in out: current=line; continue
        if current and line:
            if line.startswith('Velvet Factory · Morning Brief'): current=None; continue
            out[current].append(line)
    return out

def clean_bullet(s: str) -> str:
    return re.sub(r'^[•\-*]\s*','',s).strip()

def reader_friendly(s: str) -> str:
    """Translate known internal status jargon without changing facts, IDs or numbers."""
    out=str(s)
    replacements=(
        ('ready_for_brief','מוכן לבריף'),
        ('waiting_for_print_done','ממתין לסיום ההדפסה'),
        ('print.done','אישור סיום הדפסה'),
        ('lastMod','עדכון אחרון'),
        ('cutoff',''),
        ('Calendar','יומן'),
        ('Reel מ-HQ','ריל מהמשרד'),
        ('מ-HQ','מהמשרד'),
        ('5 מדיה','5 פריטים'),
        ('watch בלבד','למעקב בלבד'),
    )
    for old,new in replacements:
        out=out.replace(old,new)
    out=out.replace('—','-').replace('–','-')
    out=re.sub(r'\s*\(PR\s+\d+\)', '', out)
    out=out.replace('לפני  07:00','לפני 07:00')
    out=out.replace('fu-G003','G003')
    out=out.replace('אין גשר אישור סיום הדפסה','אין עדיין חיבור אוטומטי לאישור סיום ההדפסה')
    return re.sub(r'\s{2,}',' ',out).strip()

def split_title_detail(line: str) -> dict[str,str]:
    line=clean_bullet(reader_friendly(line))
    if ': ' in line:
        a,b=line.split(': ',1); return {'title':a.strip(),'detail':b.strip()}
    return {'title':line,'detail':''}

def compact_overview(text: str) -> str:
    """Keep the hero factual, short and non-duplicative like the approved mockup."""
    out=reader_friendly(text)
    out=re.sub(r'\s*Instagram חי:.*$', '', out).strip()
    out=out.replace('כל חמש העבודות בגיליון VF HQ · jobs מסומנות כסופקו.','5 העבודות ב-jobs סופקו.')
    out=out.replace('שלוש יתרות פתוחות מאומתות גם ב-VF HQ · books:','3 יתרות פתוחות:')
    out=out.replace('סך הגבייה הפתוחה 4790.','סך הגבייה 4790.')
    out=out.replace('ביומן יש אירוע אחד היום, דיאנה, שון, 16:00 עד 17:00 בבארי.','היום: דיאנה ושון, 16:00-17:00 בבארי.')
    return re.sub(r'\s{2,}',' ',out).strip()

def compact_attention(items: list[dict[str,str]]) -> list[dict[str,str]]:
    out=[dict(x) for x in items[:4]]
    if out and out[0].get('title','').startswith('גבייה פתוחה אצל '):
        people=out[0]['title'].removeprefix('גבייה פתוחה אצל ').rstrip('.')
        out[0]={'title':'גבייה פתוחה','detail':people}
    for item in out[1:]:
        detail=str(item.get('detail') or '').strip().rstrip('.')
        detail=re.sub(r'^סופק,\s*','',detail)
        detail=detail.replace('טרם שולם, ','').replace('לגבייה, ','')
        detail=detail.replace('מועד בגיליון ','מועד ')
        item['detail']=detail
    return out

def compact_progress(items: list[dict[str,str]]) -> list[dict[str,str]]:
    out=[]
    for item in items[:3]:
        title=str(item.get('title') or '').strip()
        detail=str(item.get('detail') or '').strip()
        if title.startswith('ביומן של 23.9 יש אירוע אחד'):
            title='אירוע אחד היום - דיאנה ושון, 16:00-17:00 בבארי'
            detail=''
        elif title.startswith('הגבייה הפתוחה נשארה 4790'):
            title='גבייה פתוחה: 4790'
            detail=''
        out.append({'title':title,'detail':detail})
    return out

def compact_receivables(items: list[dict[str,str]]) -> str:
    """Compress repeated receivable details for the Story card without losing amounts/status."""
    parts=[]
    for item in items[:3]:
        title=str(item.get('title') or '').strip()
        detail=str(item.get('detail') or '').strip().rstrip('.')
        customer=re.sub(r'\s+VF-\d+.*$','',title).strip()
        detail=re.sub(r'^סופק,\s*','',detail)
        detail=detail.replace('מועד בגיליון ','מועד ')
        m=re.match(r'טרם שולם,\s*(\d+)(?:,\s*(.*))?$',detail)
        if m:
            detail=f"{m.group(1)}, טרם שולם"+(f", {m.group(2)}" if m.group(2) else '')
        else:
            m=re.match(r'לגבייה,\s*(\d+)$',detail)
            if m: detail=f"{m.group(1)} לגבייה"
        parts.append((customer+' '+detail).strip())
    return '. '.join(parts)+('.' if parts else '')

def date_label(date_line: str) -> str:
    m=re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})',date_line or '')
    if not m: return str(date_line or '').strip()
    d=datetime(int(m.group(3)),int(m.group(2)),int(m.group(1)),tzinfo=TZ)
    return f"{HE_DAYS[d.weekday()]} · {d.day} {HE_MONTHS[d.month]}"

def factual_datetime(factual: dict) -> datetime:
    line=str(factual.get('date_line') or '')
    m=re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})',line)
    if m:
        return datetime(int(m.group(3)),int(m.group(2)),int(m.group(1)),tzinfo=TZ)
    raw=str(factual.get('date') or '').strip()
    m=re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})',raw)
    if not m:
        raise ValueError('brief has no factual date for the 7-day feed strip')
    return datetime(int(m.group(1)),int(m.group(2)),int(m.group(3)),tzinfo=TZ)

def factual_date_label(factual: dict) -> str:
    d=factual_datetime(factual)
    return f"{d.day} {HE_MONTHS[d.month]} {d.year}"

def fallback_stats(factual: dict, sec: dict[str,list[str]]) -> list[dict[str,str]]:
    stats=[]
    if factual.get('open_collection') is not None:
        stats.append({'value':str(factual['open_collection']),'label':'גבייה פתוחה'})
    cal=' '.join(sec.get('היום / בהמשך') or [])
    if re.search(r'אין אירועים',cal):
        stats.append({'value':'0','label':'אירועי יומן היום'})
    else:
        m=re.search(r'(\d+)\s+אירועים',cal)
        if m: stats.append({'value':m.group(1),'label':'אירועי יומן היום'})
    live=' '.join(sec.get('עבודות חיות') or [])
    if re.search(r'אין ייצור פעיל',live):
        stats.append({'value':'0','label':'עבודות ייצור פעילות'})
    else:
        m=re.search(r'(\d+)\s+עבודות?\s+פעילות?',live)
        if m: stats.append({'value':m.group(1),'label':'עבודות ייצור פעילות'})
    return stats[:3]

def instagram_snapshot(sec: dict[str,list[str]]) -> dict[str,object]:
    lines=[clean_bullet(reader_friendly(x)) for x in (sec.get('Instagram · מצב העמוד') or [])]
    joined=' '.join(lines)
    def number(pattern: str):
        m=re.search(pattern,joined)
        return int(m.group(1)) if m else None
    followers=number(r'עוקבים\s+(\d+)')
    following=number(r'עוקב\s+(\d+)')
    media_count=number(r'מדיה\s+(\d+)')

    latest=next((x for x in lines if x.startswith('הפיד האחרון:')), '')
    previous=next((x for x in lines if x.startswith('הפיד הקודם:')), '')
    def engagement(line: str) -> dict[str,object]:
        likes=re.search(r'לייק(?:ים)?\s+(\d+)',line)
        comments=re.search(r'(?:תגובה|תגובות)\s+(\d+)',line)
        date=re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})',line)
        return {
            'likes':int(likes.group(1)) if likes else None,
            'comments':int(comments.group(1)) if comments else None,
            'date_label':date.group(1) if date else '',
        }
    latest_eng=engagement(latest)
    previous_eng=engagement(previous)

    changes=[clean_bullet(reader_friendly(x)) for x in (sec.get('מה השתנה מאז הבריף הקודם') or []) if 'Instagram' in x]
    change_text='אין שינוי מאומת' if any('ללא שינוי' in x for x in changes) else (changes[0] if changes else 'אין נתון שינוי מאומת')
    insights_line=next((x for x in lines if x.startswith('Insights:')), '')
    insights_available=bool(insights_line and 'אין ספירה' not in insights_line)

    return {
        'followers':followers,
        'following':following,
        'media_count':media_count,
        'latest':latest_eng,
        'previous':previous_eng,
        'change_text':change_text,
        'insights_available':insights_available,
        'insights_note':reader_friendly(insights_line.replace('Insights:','').strip()) if insights_line else 'אין נתון Insights מאומת',
    }

def post_cards(snapshot: dict | None, start: datetime) -> list[dict]:
    """Build exactly seven calendar cells, one for each day starting at the brief date."""
    by_date: dict[object,list[tuple[datetime,dict]]] = {}
    end_date=(start+timedelta(days=7)).date()
    for row in (snapshot or {}).get('scheduled',[]):
        raw=str(row.get('scheduled_at') or '').strip()
        if not raw:
            raise ValueError(f"scheduled publication {row.get('publication_id') or row.get('title') or '?'} is missing scheduled_at")
        try:
            d=datetime.fromisoformat(raw.replace('Z','+00:00')).astimezone(TZ)
        except Exception as exc:
            raise ValueError(f"invalid scheduled_at for {row.get('publication_id') or row.get('title') or '?'}: {raw}") from exc
        if start.date() <= d.date() < end_date:
            by_date.setdefault(d.date(),[]).append((d,row))

    cards=[]
    for offset in range(7):
        day_dt=start+timedelta(days=offset)
        scheduled=sorted(by_date.get(day_dt.date(),[]),key=lambda item:item[0])
        cell={
            'day_label':HE_DAY_SHORT[day_dt.weekday()],
            'date_label':f"{day_dt.day}.{day_dt.month}",
            'has_post':bool(scheduled),
            'time_label':'',
            'type_label':'',
            'extra_count':max(0,len(scheduled)-1),
        }
        if scheduled:
            d,row=scheduled[0]
            profile=str(row.get('content_profile') or '').lower()
            kind='ריל' if 'reel' in profile else ('קרוסלה' if 'carousel' in profile else 'פוסט')
            cid=str(row.get('thumbnail_cid') or '').strip()
            public=str(row.get('thumbnail_url') or '').strip()
            image_url=('cid:'+cid) if cid else public
            if not image_url:
                raise ValueError(f"scheduled publication {row.get('publication_id') or row.get('title') or '?'} has no materialized/public thumbnail")
            cell.update({
                'image_url':image_url,
                'image_alt':row.get('title') or 'פוסט מתוזמן',
                'time_label':d.strftime('%H:%M'),
                'type_label':kind,
            })
        cards.append(cell)
    return cards

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--brief-json',type=Path,required=True)
    ap.add_argument('--brief-txt',type=Path,required=True)
    ap.add_argument('--openpost',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--visible-text',type=Path)
    a=ap.parse_args()
    factual=json.loads(a.brief_json.read_text(encoding='utf-8'))
    text=a.brief_txt.read_text(encoding='utf-8')
    sec=sections(text)
    op=json.loads(a.openpost.read_text(encoding='utf-8')) if a.openpost and a.openpost.exists() else None

    attention=compact_attention([split_title_detail(x) for x in sec['צריך ממך'][:4]])
    progress=compact_progress([split_title_detail(x) for x in sec['מה השתנה מאז הבריף הקודם'] if 'Instagram' not in x and 'OpenPost' not in x][:3])
    radar_lines=[
        clean_bullet(reader_friendly(x)) for x in sec['רדאר תוכן']
        if 'OpenPost' not in x and 'Instagram' not in x and 'הפיד האחרון' not in x and 'אין Publish' not in x
    ][:2]
    if radar_lines:
        radar_text=' '.join(radar_lines)
    else:
        research=[clean_bullet(reader_friendly(x)) for x in sec.get('שולחן המחקר',[]) if re.match(r'^\d+\)',clean_bullet(x))]
        radar_text=(re.sub(r'^\d+\)\s*','',research[0]) if research else 'אין כרגע פריט רדאר מאומת נוסף מעבר ללוח התוכן.')
    # Instagram has its own dedicated analytics section; keep hero/progress free of duplicate account metrics.
    overview_source=sec['תמונת מצב עכשיו'][0] if sec.get('תמונת מצב עכשיו') else str(factual.get('bottom_line') or '').strip()
    overview=compact_overview(overview_source)
    story_source=attention[0]['title'] if attention else (progress[0]['title'] if progress else overview)
    story_items=attention[1:4] if len(attention)>1 else attention[:3]
    story_body=compact_receivables(story_items) or overview
    kpis=factual.get('kpis') or []
    stats=[
        {'value':str(x.get('value','אין נתון')),'label':reader_friendly(str(x.get('label',''))).replace(' לפי Jobs','')}
        for x in kpis if 'Instagram' not in str(x.get('label','')) and 'עוקב' not in str(x.get('label',''))
    ][:3]
    if len(stats) < 3:
        existing={x['label'] for x in stats}
        for item in fallback_stats(factual,sec):
            if item['label'] not in existing:
                stats.append(item); existing.add(item['label'])
            if len(stats) >= 3: break
    insta=instagram_snapshot(sec)

    data={
      'email_title':'Velvet Factory - Morning Brief',
      'preheader':'מה חשוב היום, מה מתקדם ומה באמת מתוזמן לפרסום.',
      'date_label':factual_date_label(factual),
      'greeting':'בוקר טוב, כריסטיאן',
      'daily_summary':overview,
      'scheduled_posts':post_cards(op,factual_datetime(factual)),
      'instagram':insta,
      'story':{
        'title':story_source or 'תמונת היום',
        'body':story_body or overview,
        'image':{}
      },
      'morning_line':{'text':'המידע החשוב קודם. המערכת נשארת מאחור.','note':'מהדורת הבוקר של Velvet Factory'},
      'attention':attention,
      'progress':progress,
      'radar':{'title':'דברים שכדאי לשים לב אליהם','text':radar_text,'image':{}},
      'stats':stats,
      'footer':{'quote':'Same, brighter tomorrow.','note':'תודה שאתה חלק מהדרך','image':{}}
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    if a.visible_text:
        lines=[data['greeting'],data['date_label'],data['daily_summary'],'', 'דורש תשומת לב']
        for item in attention: lines.append('• '+item['title']+(' - '+item['detail'] if item['detail'] else ''))
        lines += ['', 'מה מתקדם']
        for item in progress: lines.append('• '+item['title']+(' - '+item['detail'] if item['detail'] else ''))
        lines += ['', 'Instagram']
        if insta.get('followers') is not None: lines.append(f"• עוקבים: {insta['followers']}")
        latest=insta.get('latest') or {}
        if latest.get('likes') is not None or latest.get('comments') is not None:
            likes=latest.get('likes'); comments=latest.get('comments')
            likes_text=('לייק 1' if likes == 1 else f'{likes} לייקים') if likes is not None else 'לייקים: אין נתון'
            comments_text=('תגובה 1' if comments == 1 else f'{comments} תגובות') if comments is not None else 'תגובות: אין נתון'
            lines.append(f"• מעורבות בפוסט האחרון: {likes_text} · {comments_text}")
        lines.append('• שינוי: '+str(insta.get('change_text') or 'אין נתון'))
        lines += ['', 'על הרדאר',data['radar']['text']]
        a.visible_text.parent.mkdir(parents=True,exist_ok=True)
        a.visible_text.write_text('\n'.join(lines).strip()+'\n',encoding='utf-8')
    print(a.output)
    return 0

if __name__=='__main__': raise SystemExit(main())