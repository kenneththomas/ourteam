import os
import uuid
import cv2
from flask import current_app, session
from markupsafe import Markup, escape
from sqlalchemy import inspect, text
import squawk
from models import db

xp_actions={'send_comment':10,'receive_comment':5,'update_bio':10}

def nl2br(s):
    return Markup(str(escape(s or '')).replace('\\n','<br>\\n'))

def generate_text_from_prompt(prompt):
    return squawk.generate_text(prompt,engine=session.get('gpt_engine',current_app.config['DEFAULT_GPT_ENGINE']))

def save_uploaded_file(file,folder):
    if not file or not file.filename: return None
    from werkzeug.utils import secure_filename
    filename=f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    path=os.path.join(current_app.config['UPLOAD_FOLDER'],folder)
    os.makedirs(path,exist_ok=True); file.save(os.path.join(path,filename))
    return f"uploads/{folder}/{filename}"

def uploaded_file_path(file_url):
    if not file_url or not file_url.startswith('/static/uploads/'): return None
    candidate=os.path.abspath(os.path.join(current_app.static_folder,file_url.removeprefix('/static/').replace('/',os.sep)))
    root=os.path.abspath(current_app.config['UPLOAD_FOLDER'])
    return candidate if os.path.commonpath([candidate,root])==root else None

def generate_video_thumbnail(video_path,thumbnail_path):
    try:
        if not os.path.exists(video_path): return False
        cap=cv2.VideoCapture(video_path)
        if not cap.isOpened(): return False
        frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if not frames: cap.release(); return False
        cap.set(cv2.CAP_PROP_POS_FRAMES,int(frames*.25)); ret,frame=cap.read()
        if not ret: cap.set(cv2.CAP_PROP_POS_FRAMES,0); ret,frame=cap.read()
        if not ret: cap.release(); return False
        h,w=frame.shape[:2]; ratio=w/h
        nw,nh=(320,int(320/ratio)) if ratio>1 else (int(240*ratio),240)
        os.makedirs(os.path.dirname(thumbnail_path),exist_ok=True)
        ok=cv2.imwrite(thumbnail_path,cv2.resize(frame,(nw,nh))); cap.release()
        return bool(ok and os.path.exists(thumbnail_path))
    except Exception: return False

def ensure_current_schema():
    columns={c['name'] for c in inspect(db.engine).get_columns('employee')}
    with db.engine.begin() as conn:
        if 'company' not in columns: conn.execute(text('ALTER TABLE employee ADD COLUMN company VARCHAR'))
        if conn.execute(text("SELECT 1 FROM employee WHERE company IS NULL OR TRIM(company) = '' LIMIT 1")).first():
            conn.execute(text("UPDATE employee SET company=:company WHERE company IS NULL OR TRIM(company) = ''"),{'company':current_app.config['DEFAULT_COMPANY']})

def calculate_level(xp):
    level=1
    while xp>=level*100: xp-=level*100; level+=1
    return level

def get_management_chain(employee,levels=3):
    chain=[]; current=employee
    while current and levels>0:
        if not current.reports_to: break
        manager=db.session.get(__import__('models').Employee,current.reports_to)
        if not manager: break
        chain.append(manager); current=manager; levels-=1
    return chain

