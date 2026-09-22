#!/usr/bin/env python3
"""Project the canonical factual Morning Brief into Morning Green.

Consumes the existing V10.x factual JSON/TXT plus an optional read-only OpenPost
snapshot. It does not fetch providers and does not create a parallel source of truth.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ=ZoneInfo('Asia/Jerusalem')
HE_DAYS=['יום שני','יום שלישי','יום רביעי','יום חמישי','יום שישי','שבת','יום ראשון']
HE_MONTHS={1:'בינואר',2:'בפברואר',3:'במרץ',4:'באפריל',5:'במאי',6:'ביוני',7:'ביולי',8:'באוגוסט',9:'בספטמבר',10:'באוקטובר',11:'בנובמבר',12:'בדצמבר'}

HEADINGS=[
 'מה השתנה מאז הבריף הקודם','צריך ממך','מצב הכסף','עבודות חיות','היום / בהמשך',
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

def date_label(date_line: str) -> str:
    m=re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})',date_line or '')
    if not m: return str(date_line or '').strip()
    d=datetime(int(m.group(3)),int(m.group(2)),int(m.group(1)),tzinfo=TZ)
    return f"{HE_DAYS[d.weekday()]} · {d.day} {HE_MONTHS[d.month]}"

def post_cards(snapshot: dict | None) -> list[dict]:
    cards=[]
    for row in (snapshot or {}).get('scheduled',[])[:4]:
        raw=str(row.get('scheduled_at') or '')
        try:
            d=datetime.fromisoformat(raw.replace('Z','+00:00')).astimezone(TZ)
            day=f"{d.day}.{d.month}"; clock=d.strftime('%H:%M')
        except Exception:
            day='מתוזמן'; clock=raw
        profile=str(row.get('content_profile') or '').lower()
        kind='ריל' if 'reel' in profile else ('קרוסלה' if 'carousel' in profile else 'פוסט')
        cards.append({
            'image_url':row['thumbnail_url'],
            'image_alt':row.get('title') or 'פוסט מתוזמן',
            'date_label':day,'time_label':clock,'type_label':kind,'status_label':'מתוזמן'
        })
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

    attention=[split_title_detail(x) for x in sec['צריך ממך'][:4]]
    progress=[split_title_detail(x) for x in sec['מה השתנה מאז הבריף הקודם'][:4]]
    radar_lines=[clean_bullet(reader_friendly(x)) for x in sec['רדאר תוכן'][:3]]
    radar_text=' '.join(radar_lines) if radar_lines else 'אין פריט רדאר מאומת נוסף.'
    story_source=attention[0]['title'] if attention else (progress[0]['title'] if progress else reader_friendly(factual.get('bottom_line','')))
    story_items=attention[1:4] if len(attention)>1 else attention[:3]
    story_body=' '.join((x.get('title','')+(' - '+x.get('detail','') if x.get('detail') else '')).strip() for x in story_items).strip()
    kpis=factual.get('kpis') or []
    stats=[{'value':str(x.get('value','אין נתון')),'label':reader_friendly(str(x.get('label',''))).replace(' לפי Jobs','')} for x in kpis[:3]]

    data={
      'email_title':'Velvet Factory - Morning Brief',
      'preheader':'מה חשוב היום, מה מתקדם ומה באמת מתוזמן לפרסום.',
      'date_label':date_label(str(factual.get('date_line') or '')),
      'greeting':'בוקר טוב, כריסטיאן',
      'daily_summary':reader_friendly(str(factual.get('bottom_line') or '').strip()),
      'scheduled_posts':post_cards(op),
      'story':{
        'title':story_source or 'תמונת היום',
        'body':story_body or reader_friendly(str(factual.get('bottom_line') or '')),
        'image':{}
      },
      'morning_line':{'text':'המידע החשוב קודם. המערכת נשארת מאחור.','note':'מהדורת הבוקר של Velvet Factory'},
      'attention':attention,
      'progress':progress,
      'radar':{'title':'מה כדאי לראות לפני שזה נהיה דחוף','text':radar_text,'image':{}},
      'stats':stats,
      'footer':{'quote':'Same, brighter tomorrow.','note':'Velvet Factory · Morning Edition','image':{}}
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    if a.visible_text:
        lines=[data['greeting'],data['date_label'],data['daily_summary'],'', 'דורש תשומת לב']
        for item in attention: lines.append('• '+item['title']+(' - '+item['detail'] if item['detail'] else ''))
        lines += ['', 'מה מתקדם']
        for item in progress: lines.append('• '+item['title']+(' - '+item['detail'] if item['detail'] else ''))
        lines += ['', 'על הרדאר',data['radar']['text']]
        a.visible_text.parent.mkdir(parents=True,exist_ok=True)
        a.visible_text.write_text('\n'.join(lines).strip()+'\n',encoding='utf-8')
    print(a.output)
    return 0

if __name__=='__main__': raise SystemExit(main())