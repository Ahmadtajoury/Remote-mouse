"""
Remote Mouse Controller
------------------------
Requirements:  pip install flask pyautogui pillow pynput
Usage:         py remote_mouse.py
"""

import sys, io, socket, base64

try:
    from flask import Flask, request, jsonify
    import pyautogui
    from PIL import ImageGrab
    from pynput.keyboard import Key, Controller as KeyboardController
except ImportError as e:
    print(f"Missing: {e}\nRun: pip install flask pyautogui pillow pynput")
    sys.exit(1)

pyautogui.FAILSAFE = False
keyboard = KeyboardController()
app = Flask(__name__)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

MEDIA_KEYS = {
    'play_pause': Key.media_play_pause,
    'next':       Key.media_next,
    'prev':       Key.media_previous,
    'mute':       Key.media_volume_mute,
}

@app.route('/')
def index():
    return HTML

@app.route('/move', methods=['POST'])
def move():
    d = request.json
    pyautogui.moveRel(d.get('dx', 0), d.get('dy', 0), duration=0)
    return jsonify(ok=True)

@app.route('/click', methods=['POST'])
def click():
    d = request.json
    pyautogui.doubleClick(button=d['button']) if d.get('double') else pyautogui.click(button=d.get('button','left'))
    return jsonify(ok=True)

@app.route('/mousedown', methods=['POST'])
def mousedown():
    pyautogui.mouseDown(button=request.json.get('button','left'))
    return jsonify(ok=True)

@app.route('/mouseup', methods=['POST'])
def mouseup():
    pyautogui.mouseUp(button=request.json.get('button','left'))
    return jsonify(ok=True)

@app.route('/scroll', methods=['POST'])
def scroll():
    pyautogui.scroll(int(request.json.get('dy', 0)))
    return jsonify(ok=True)

@app.route('/type', methods=['POST'])
def type_text():
    text = request.json.get('text', '')
    if text == '__BACKSPACE__':      pyautogui.press('backspace')
    elif text == '__ENTER__':        pyautogui.press('enter')
    elif text.startswith('__KEY__'): pyautogui.press(text[7:])
    else:                            pyautogui.typewrite(text, interval=0.01)
    return jsonify(ok=True)

@app.route('/media', methods=['POST'])
def media():
    key = MEDIA_KEYS.get(request.json.get('action',''))
    if key:
        keyboard.press(key); keyboard.release(key)
    return jsonify(ok=True)

@app.route('/volume', methods=['POST'])
def volume():
    a = request.json.get('action','')
    if a == 'up':    pyautogui.press('volumeup')
    elif a == 'down': pyautogui.press('volumedown')
    elif a == 'mute': pyautogui.press('volumemute')
    return jsonify(ok=True)

@app.route('/screenshot')
def screenshot():
    try:
        img = ImageGrab.grab()
        img = img.resize((480, 270))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=15)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return jsonify(img=b64)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/screenshot-view')
def screenshot_view():
    return """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Screen Mirror</title><style>body{margin:0;background:#000;display:flex;align-items:center;justify-content:center;height:100vh;}
img{max-width:100%;max-height:100vh;object-fit:contain;}</style></head>
<body><img id="i"><script>
async function f(){try{const r=await fetch('/screenshot');const d=await r.json();if(d.img)document.getElementById('i').src='data:image/jpeg;base64,'+d.img;}catch(e){}setTimeout(f,80);}f();
</script></body></html>"""

HTML = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<title>Remote Mouse</title>
<style>
* { box-sizing:border-box; margin:0; padding:0; touch-action:none; -webkit-user-select:none; }
body { font-family:-apple-system,sans-serif; background:#111; color:#eee; height:100vh; display:flex; flex-direction:column; overflow:hidden; }
#tabs { display:flex; background:#1c1c1c; border-bottom:1px solid #2a2a2a; flex-shrink:0; }
.tab { flex:1; padding:12px 4px; text-align:center; font-size:11px; color:#666; cursor:pointer; border-bottom:2px solid transparent; }
.tab.active { color:#fff; border-bottom-color:#4CAF50; }
#pages { flex:1; overflow:hidden; }
#pages > div { display:none; flex-direction:column; height:100%; }
#pages > div.active { display:flex; }
#trackpad { flex:1; background:#181818; position:relative; }
#trackpad-hint { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); color:#2a2a2a; font-size:13px; pointer-events:none; text-align:center; line-height:2; }
#click-bar { display:flex; height:68px; flex-shrink:0; border-top:1px solid #2a2a2a; }
.click-btn { flex:1; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; letter-spacing:.5px; color:#888; }
#left-click { background:#1e1e1e; border-right:1px solid #2a2a2a; }
#right-click { background:#1a1a1a; }
.click-btn.pressed, .click-btn:active { background:#4CAF50 !important; color:#000; }
#keyboard-page { padding:14px; gap:10px; overflow-y:auto; }
textarea { width:100%; padding:10px; background:#1e1e1e; border:1px solid #333; border-radius:10px; color:#fff; font-size:16px; resize:none; touch-action:auto; }
#send-btn { padding:12px; background:#4CAF50; color:#000; border:none; border-radius:10px; font-size:15px; font-weight:700; cursor:pointer; width:100%; }
.key-row { display:flex; gap:8px; }
.spec-key { flex:1; padding:14px 4px; background:#1e1e1e; border:1px solid #333; border-radius:10px; text-align:center; font-size:13px; color:#ccc; }
.spec-key:active { background:#4CAF50; color:#000; }
#media-page { padding:20px; gap:14px; overflow-y:auto; }
.media-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; }
.media-btn { padding:20px 8px; background:#1e1e1e; border:1px solid #333; border-radius:14px; text-align:center; font-size:24px; }
.media-btn span { display:block; font-size:10px; color:#666; margin-top:5px; }
.media-btn:active { background:#4CAF50; }
.vol-row { display:flex; align-items:center; gap:10px; }
.vol-btn { padding:16px; background:#1e1e1e; border:1px solid #333; border-radius:14px; text-align:center; font-size:20px; min-width:54px; }
.vol-btn:active { background:#4CAF50; }
#vol-slider { flex:1; accent-color:#4CAF50; }
.mute-btn { width:100%; padding:16px; background:#1e1e1e; border:1px solid #333; border-radius:14px; text-align:center; font-size:15px; color:#aaa; }
.mute-btn:active { background:#4CAF50; color:#000; }
#screen-page { background:#000; }
#screen-toolbar { display:flex; gap:8px; padding:8px; background:#111; flex-shrink:0; }
#screen-toolbar button { flex:1; padding:9px; background:#1e1e1e; border:1px solid #333; border-radius:8px; color:#eee; font-size:12px; }
#screen-toolbar button.on { background:#4CAF50; color:#000; border-color:#4CAF50; }
#screen-wrap { flex:1; display:flex; align-items:center; justify-content:center; }
#screen-img { width:100%; object-fit:contain; display:none; }
#screen-ph { color:#333; font-size:13px; }
</style>
</head>
<body>
<div id="tabs">
  <div class="tab active" onclick="showTab('trackpad')">🖱 Trackpad</div>
  <div class="tab" onclick="showTab('keyboard')">⌨️ Keys</div>
  <div class="tab" onclick="showTab('media')">🎵 Media</div>
  <div class="tab" onclick="showTab('screen')">🖥 Screen</div>
</div>
<div id="pages">
  <div id="trackpad-page" class="active">
    <div id="trackpad">
      <div id="trackpad-hint">Drag = move mouse<br>Tap = left click<br>Hold = right click<br>2 fingers = scroll</div>
    </div>
    <div id="click-bar">
      <div class="click-btn" id="left-click"  ontouchstart="btnDown('left')"  ontouchend="btnUp('left')">LEFT CLICK</div>
      <div class="click-btn" id="right-click" ontouchstart="btnDown('right')" ontouchend="btnUp('right')">RIGHT CLICK</div>
    </div>
  </div>
  <div id="keyboard-page">
    <textarea id="type-input" rows="3" placeholder="Type here..."></textarea>
    <button id="send-btn" onclick="sendText()">Send ↵</button>
    <div class="key-row">
      <div class="spec-key" onclick="sendKey('__BACKSPACE__')">⌫ Backspace</div>
      <div class="spec-key" onclick="sendKey('__ENTER__')">↵ Enter</div>
    </div>
    <div class="key-row">
      <div class="spec-key" onclick="sendKey('__KEY__win')">❖ Win</div>
      <div class="spec-key" onclick="sendKey('__KEY__tab')">⇥ Tab</div>
      <div class="spec-key" onclick="sendKey('__KEY__escape')">Esc</div>
      <div class="spec-key" onclick="sendKey('__KEY__space')">Space</div>
    </div>
    <div class="key-row">
      <div class="spec-key" onclick="sendKey('__KEY__up')">↑</div>
      <div class="spec-key" onclick="sendKey('__KEY__down')">↓</div>
      <div class="spec-key" onclick="sendKey('__KEY__left')">←</div>
      <div class="spec-key" onclick="sendKey('__KEY__right')">→</div>
    </div>
  </div>
  <div id="media-page">
    <div class="media-grid">
      <div class="media-btn" onclick="media('prev')">⏮<span>Prev</span></div>
      <div class="media-btn" onclick="media('play_pause')">⏯<span>Play/Pause</span></div>
      <div class="media-btn" onclick="media('next')">⏭<span>Next</span></div>
    </div>
    <div class="vol-row">
      <div class="vol-btn" onclick="vol('down')">🔉</div>
      <input type="range" id="vol-slider" min="0" max="20" value="10" oninput="volSlide(this)">
      <div class="vol-btn" onclick="vol('up')">🔊</div>
    </div>
    <div class="mute-btn" onclick="vol('mute')">🔇 &nbsp;Mute</div>
  </div>
  <div id="screen-page">
    <div id="screen-toolbar">
      <button id="stream-btn" onclick="toggleStream()">▶ Start Mirror</button>
      <button onclick="openPop()">⛶ Pop Out</button>
    </div>
    <div id="screen-wrap">
      <img id="screen-img" alt="screen">
      <div id="screen-ph">Tap Start Mirror</div>
    </div>
  </div>
</div>
<script>
function showTab(name) {
  const names = ['trackpad','keyboard','media','screen'];
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', names[i]===name));
  document.querySelectorAll('#pages > div').forEach(p => p.classList.remove('active'));
  document.getElementById(name+'-page').classList.add('active');
}

// ── Batched mouse movement ──
// Collects finger movement and sends it at most once every 16ms (~60fps)
// instead of firing a separate request on every single touchmove event.
let pendingDx = 0, pendingDy = 0, movePending = false;

function flushMove() {
  movePending = false;
  if (!pendingDx && !pendingDy) return;
  const dx = pendingDx, dy = pendingDy;
  pendingDx = 0; pendingDy = 0;
  post('/move', { dx, dy });
}

const pad = document.getElementById('trackpad');
let lastX=0, lastY=0, tapMoved=false, holdTimer=null, touch2Y=0;

pad.addEventListener('touchstart', e => {
  e.preventDefault();
  if (e.touches.length === 1) {
    const t = e.touches[0]; lastX = t.clientX; lastY = t.clientY; tapMoved = false;
    holdTimer = setTimeout(() => { if (!tapMoved) { vibe(40); post('/click',{button:'right'}); } }, 600);
  }
  if (e.touches.length === 2) touch2Y = (e.touches[0].clientY + e.touches[1].clientY) / 2;
}, { passive: false });

pad.addEventListener('touchmove', e => {
  e.preventDefault();
  if (e.touches.length === 1) {
    const t = e.touches[0];
    const dx = (t.clientX - lastX) * 2.5, dy = (t.clientY - lastY) * 2.5;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) { tapMoved = true; clearTimeout(holdTimer); }
    lastX = t.clientX; lastY = t.clientY;
    pendingDx += Math.round(dx);
    pendingDy += Math.round(dy);
    // Schedule a flush only if one isn't already queued
    if (!movePending) { movePending = true; setTimeout(flushMove, 16); }
  }
  if (e.touches.length === 2) {
    const y = (e.touches[0].clientY + e.touches[1].clientY) / 2;
    post('/scroll', { dy: Math.round((touch2Y - y) / 8) }); touch2Y = y;
  }
}, { passive: false });

pad.addEventListener('touchend', e => {
  e.preventDefault(); clearTimeout(holdTimer);
  if (!tapMoved) { post('/click', { button: 'left' }); vibe(10); }
}, { passive: false });

function btnDown(b) { document.getElementById(b+'-click').classList.add('pressed'); post('/mousedown',{button:b}); }
function btnUp(b)   { document.getElementById(b+'-click').classList.remove('pressed'); post('/mouseup',{button:b}); }
function sendText() { const el=document.getElementById('type-input'); if(!el.value) return; post('/type',{text:el.value}); el.value=''; }
function sendKey(k) { post('/type',{text:k}); }
function media(a)   { post('/media',{action:a}); }
function vol(a)     { post('/volume',{action:a}); }
function volSlide(el) {
  const diff=el.value-10; if(!diff) return;
  const a=diff>0?'up':'down';
  for(let i=0;i<Math.abs(diff);i++) setTimeout(()=>post('/volume',{action:a}),i*60);
  setTimeout(()=>el.value=10,Math.abs(diff)*60+50);
}

let streaming=false, mirrorLoop=null;
function toggleStream() {
  streaming=!streaming;
  const btn=document.getElementById('stream-btn');
  const img=document.getElementById('screen-img');
  const ph=document.getElementById('screen-ph');
  if(streaming){
    img.style.display='block'; ph.style.display='none';
    btn.textContent='⏹ Stop Mirror'; btn.classList.add('on');
    fetchFrame();
  } else {
    clearTimeout(mirrorLoop);
    img.style.display='none'; ph.style.display='block';
    btn.textContent='▶ Start Mirror'; btn.classList.remove('on');
  }
}
async function fetchFrame() {
  if(!streaming) return;
  try {
    const res=await fetch('/screenshot'); const data=await res.json();
    if(data.img) document.getElementById('screen-img').src='data:image/jpeg;base64,'+data.img;
  } catch(e){}
  if(streaming) mirrorLoop=setTimeout(fetchFrame,80);
}
function openPop() { window.open('/screenshot-view','_blank'); }
function vibe(ms) { if(navigator.vibrate) navigator.vibrate(ms); }
function post(url,data) { fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).catch(()=>{}); }
</script>
</body>
</html>"""

if __name__ == '__main__':
    ip = get_local_ip()
    print(f"\n{'='*42}\n  Remote Mouse Controller\n{'='*42}")
    print(f"  Open on your phone:  http://{ip}:5000")
    print(f"  Same WiFi required.  Ctrl+C to stop.\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
