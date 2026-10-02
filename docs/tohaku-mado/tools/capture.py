#!/usr/bin/env python3
"""mado admin/LIFF スクリーンショット撮影（Playwright + mock_server）"""
import json, os, sys, time, datetime
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8787"
OUT = os.environ.get("SHOTS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots"))
os.makedirs(OUT, exist_ok=True)
TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()
NOW = int(time.time() * 1000)

def ts(offset_min):
    ms = NOW - offset_min * 60000
    return {"__ms": ms}

ORDERS = [
    {"id": "O-004", "orderNumber": 4, "status": "pending", "orderSource": "line", "date": TODAY,
     "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "salesPointName": "売店", "qrLabel": "売店レジ前",
     "bookingId": "TEST-2500201", "total": 1170,
     "items": [{"emoji": "🍺", "name": "瓶ビール（中瓶）", "quantity": 1, "price": 770},
                {"emoji": "🍊", "name": "オレンジジュース", "quantity": 1, "price": 430}],
     "createdAt": ts(2)},
    {"id": "O-002", "orderNumber": 2, "status": "preparing", "orderSource": "line", "date": TODAY,
     "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "salesPointName": "休憩室", "qrLabel": "花の間2",
     "bookingId": "TEST-2500203", "total": 1960,
     "items": [{"emoji": "🍜", "name": "天ぷらそば", "quantity": 2, "price": 980}],
     "createdAt": ts(14)},
    {"id": "O-001", "orderNumber": 1, "status": "served", "orderSource": "proxy", "date": TODAY,
     "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "salesPointName": "控室", "qrLabel": "月の間1",
     "bookingId": "TEST-2500200", "total": 3300,
     "items": [{"emoji": "🍱", "name": "精進料理膳", "quantity": 1, "price": 3300}],
     "createdAt": ts(35)},
    {"id": "O-003", "orderNumber": 3, "status": "ready_to_pay", "orderSource": "line", "date": TODAY,
     "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "salesPointName": "控室", "qrLabel": "月の間1",
     "bookingId": "TEST-2500200", "checkinId": "CK-001", "total": 1660, "sapStatus": "sent",
     "items": [{"emoji": "☕", "name": "ブレンドコーヒー", "quantity": 1, "price": 400},
                {"emoji": "🧊", "name": "アイスコーヒー", "quantity": 1, "price": 400},
                {"emoji": "🍊", "name": "オレンジジュース", "quantity": 1, "price": 430},
                {"emoji": "🍋", "name": "レモネード", "quantity": 1, "price": 430}],
     "createdAt": ts(58)},
    {"id": "O-005", "orderNumber": 5, "status": "ready_to_pay", "orderSource": "proxy", "date": TODAY,
     "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "salesPointName": "控室", "qrLabel": "月の間1",
     "bookingId": "TEST-2500203", "total": 980, "sapStatus": "cart_added",
     "items": [{"emoji": "🍜", "name": "天ぷらそば", "quantity": 1, "price": 980}],
     "createdAt": ts(66)},
]

CHECKINS = [
    {"id": "CK-001", "status": "checked_in", "date": TODAY, "hallId": "HALL-18YT",
     "reservationId": "RSV-001", "bookingId": "TEST-2500200", "deceasedName": "東博　太郎",
     "funeralCompany": "幕内祭典", "checkinNumber": 1, "checkinType": "chief_mourner",
     "memberName": "東博　一郎", "total": 3080, "sapStatus": "sent", "createdAt": ts(120)},
    {"id": "CK-002", "status": "waiting", "date": TODAY, "hallId": "HALL-18YT",
     "reservationId": "RSV-002", "bookingId": "TEST-2500201", "deceasedName": "窓口　花子",
     "funeralCompany": "あすなろ祭典", "checkinNumber": 2,
     "createdAt": ts(90)},
    {"id": "CK-003", "status": "notified", "date": TODAY, "hallId": "HALL-18YT",
     "reservationId": "RSV-004", "bookingId": "TEST-2500203", "deceasedName": "四ツ木　勇",
     "funeralCompany": "幕内祭典", "checkinNumber": 3, "total": 1960, "sapStatus": "sent",
     "createdAt": ts(60)},
    {"id": "CK-004", "status": "paid", "date": TODAY, "hallId": "HALL-18YT",
     "reservationId": "RSV-003", "bookingId": "TEST-2500202", "deceasedName": "広済　次郎",
     "funeralCompany": "セレモニー光", "checkinNumber": 4, "total": 5280, "sapStatus": "sent",
     "createdAt": ts(30)},
]

RESERVATIONS = json.load(open('/dev/stdin')) if False else None  # server-side copy used instead

with open(__file__.replace('capture.py', 'mock_server.py')) as f:
    pass

FIREBASE_STUB = r"""
(() => {
  const COLL = window.__MOCK_COLLECTIONS__ || {};
  function revive(o){
    if (o && typeof o === 'object') {
      if ('__ms' in o) { const ms=o.__ms; return {seconds: Math.floor(ms/1000), _seconds: Math.floor(ms/1000), toDate: () => new Date(ms)}; }
      if (Array.isArray(o)) return o.map(revive);
      const r={}; for (const k of Object.keys(o)) r[k]=revive(o[k]); return r;
    }
    return o;
  }
  function snap(docs){
    const ds = docs.map(d => ({id: d.id, data: () => revive(d)}));
    return {docChanges: () => ds.map(doc => ({type: 'added', doc})), docs: ds,
            forEach: (fn) => ds.forEach(fn), size: ds.length, empty: ds.length===0};
  }
  function query(name){
    return {where: () => query(name), orderBy: () => query(name), limit: () => query(name),
            onSnapshot: (cb, err) => { setTimeout(() => { try { cb(snap(COLL[name]||[])); } catch(e){ console.error('snap-cb', name, e); } }, 80); return () => {}; },
            get: async () => snap(COLL[name]||[])};
  }
  const fdb = {useEmulator: () => {}, collection: (name) => query(name)};
  window.firebase = {initializeApp: () => ({}), firestore: Object.assign(() => fdb, {FieldValue: {serverTimestamp: () => new Date()}})};
})();
"""

QRCODE_STUB = r"""
window.QRCode = function(el, opts){
  const size = (opts && opts.width) || 160;
  const c = document.createElement('canvas'); c.width=size; c.height=size;
  const g = c.getContext('2d');
  g.fillStyle='#fff'; g.fillRect(0,0,size,size);
  g.fillStyle='#111';
  const n=21, cell=size/n;
  let seed=42; const rnd=()=>{seed=(seed*16807)%2147483647; return seed/2147483647;};
  for(let y=0;y<n;y++)for(let x=0;x<n;x++){ if(rnd()>0.5) g.fillRect(x*cell,y*cell,cell,cell); }
  const fp=(x,y)=>{g.fillStyle='#111';g.fillRect(x,y,cell*7,cell*7);g.fillStyle='#fff';g.fillRect(x+cell,y+cell,cell*5,cell*5);g.fillStyle='#111';g.fillRect(x+cell*2,y+cell*2,cell*3,cell*3);};
  fp(0,0); fp(size-cell*7,0); fp(0,size-cell*7);
  if(el) el.appendChild(c);
  this._el = el;
};
window.QRCode.CorrectLevel = {L:1,M:0,Q:3,H:2};
"""

LEAFLET_STUB = r"""
(function(){
  const layer = () => ({addTo: () => layer(), setLatLng: () => layer(), setRadius: () => layer(), on: () => layer(), remove: () => {}, bindPopup: () => layer()});
  window.L = {map: () => ({setView: function(){return this;}, on: () => {}, remove: () => {}, addLayer: () => {}, invalidateSize: () => {}, fitBounds: () => {}}),
              tileLayer: () => layer(), marker: () => layer(), circle: () => layer(), latLng: (a,b)=>({lat:a,lng:b})};
})();
"""

XLSX_STUB = "window.XLSX={utils:{json_to_sheet:()=>({}),book_new:()=>({}),book_append_sheet:()=>{}},writeFile:()=>{}};"


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ''
    collections = {"orders": ORDERS, "checkins": CHECKINS,
                   "reservations": []}  # reservations listener: give same as REST below
    import urllib.request
    rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
    for r in rs:
        r.setdefault("createdAt", ts(600))
    collections["reservations"] = rs

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.5,
                                  locale="ja-JP", timezone_id="Asia/Tokyo")
        # block/stub external
        def route_ext(route):
            url = route.request.url
            if "firebase-app-compat" in url:
                route.fulfill(content_type="application/javascript", body=FIREBASE_STUB)
            elif "firebase-firestore-compat" in url:
                route.fulfill(content_type="application/javascript", body="/* stub */")
            elif "qrcode.min.js" in url:
                route.fulfill(content_type="application/javascript", body=QRCODE_STUB)
            elif "leaflet" in url and url.endswith(".js"):
                route.fulfill(content_type="application/javascript", body=LEAFLET_STUB)
            elif "xlsx.full.min.js" in url:
                route.fulfill(content_type="application/javascript", body=XLSX_STUB)
            elif url.startswith(BASE):
                route.continue_()
            else:
                route.abort()
        ctx.route("**/*", route_ext)
        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)

        page = ctx.new_page()
        page.on("console", lambda m: m.type == "error" and print("CONSOLE-ERR:", m.text[:300]))
        page.on("pageerror", lambda e: print("PAGE-ERR:", str(e)[:300]))

        def shot(name, full=False):
            page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        def tab(panel):
            page.click(f"[onclick*=\"showPanel('{panel}'\"]")
            page.wait_for_timeout(700)

        # --- login screen (no token) ---
        if only in ('', 'login'):
            ctx2 = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.5, locale="ja-JP", timezone_id="Asia/Tokyo")
            ctx2.route("**/*", route_ext)
            p2 = ctx2.new_page()
            p2.goto(BASE + "/admin.html")
            p2.wait_for_timeout(1200)
            p2.screenshot(path=f"{OUT}/a00-login.png")
            print("shot: a00-login")
            ctx2.close()

        page.goto(BASE + "/admin.html")
        page.wait_for_timeout(2500)

        if only in ('', 'orders'):
            shot("a01-orders-kanban")
            # order edit modal
            try:
                page.click("text=✏️ 編集", timeout=3000)
                page.wait_for_timeout(600)
                shot("a02-order-edit-modal")
                page.evaluate("try{closeOrderEditModal()}catch(e){}")
                page.wait_for_timeout(300)
            except Exception as e:
                print("edit modal fail", e)
            try:
                page.click("text=📋 注文詳細", timeout=3000)
                page.wait_for_timeout(900)
                shot("a03-order-detail-modal")
                page.evaluate("try{closeOrderDetailPanel()}catch(e){};document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay]').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'})")
                page.wait_for_timeout(300)
            except Exception as e:
                print("detail modal fail", e)

        if only in ('', 'proxy'):
            tab('proxy')
            shot("a05-proxy-step1")
            try:
                page.click("text=⚙️ 斎場・売上場所設定", timeout=2000)
                page.wait_for_timeout(400)
                shot("a06-proxy-step0-settings")
            except Exception as e:
                print("proxy step0 fail", e)
            try:
                page.click("text=📋 予約一覧から選ぶ", timeout=2000)
                page.wait_for_timeout(700)
                shot("a07-proxy-rsv-picker")
                # pick first reservation
                page.click("text=東博　太郎", timeout=2000)
                page.wait_for_timeout(700)
                shot("a08-proxy-step2-payer")
            except Exception as e:
                print("proxy picker fail", e)
            try:
                page.click("text=葬儀社", timeout=2000)
                page.wait_for_timeout(600)
                shot("a09-proxy-step3-menu")
            except Exception as e:
                print("proxy step3 fail", e)

        if only in ('', 'rooms'):
            tab('roomAssignments')
            page.wait_for_timeout(600)
            shot("a10-room-assignments")
            try:
                page.click("text=紐付け", timeout=2000)
                page.wait_for_timeout(600)
                shot("a11-ra-assign-modal")
                page.keyboard.press("Escape")
                page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay]').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'})")
            except Exception as e:
                print("ra modal fail", e)

        if only in ('', 'rsv'):
            tab('reservations')
            page.wait_for_timeout(400)
            try:
                page.fill('#rsvTabFrom', TODAY)
                page.fill('#rsvTabTo', TODAY)
                page.click('#panelReservations button:has-text("🔍")', timeout=2000)
            except Exception as e:
                print('rsv search fail', e)
            page.wait_for_timeout(800)
            shot("a12-reservations")
            try:
                page.click("text=📌 確定", timeout=2000)
                page.wait_for_timeout(600)
                shot("a13-rsv-confirm-modal")
                page.keyboard.press("Escape")
                page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay]').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'})")
            except Exception as e:
                print("rsv confirm fail", e)

        if only in ('', 'checkins'):
            tab('checkins')
            page.wait_for_timeout(800)
            shot("a14-checkins")
            try:
                page.click("text=未承諾のみ", timeout=2000)
                page.wait_for_timeout(500)
                shot("a15-checkins-unconsent")
                page.click("text=未承諾のみ", timeout=2000)
            except Exception as e:
                print("unconsent fail", e)
            try:
                page.click("#panelCheckins button:has-text('QR')", timeout=2000)
                page.wait_for_timeout(700)
                shot("a16-checkin-qr-modal")
                page.keyboard.press("Escape")
                page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay]').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'})")
            except Exception as e:
                print("qr modal fail", e)

        if only in ('', 'payment'):
            tab('payment')
            page.wait_for_timeout(900)
            shot("a17-payment-kanban")

        if only in ('', 'pc'):
            tab('preConsents')
            page.wait_for_timeout(1000)
            shot("a18-preconsents")
            try:
                page.click("text=紐付け", timeout=2000)
                page.wait_for_timeout(800)
                shot("a19-pc-link-modal")
                page.keyboard.press("Escape")
                page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay]').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'})")
            except Exception as e:
                print("pc link fail", e)

        if only in ('', 'settings'):
            try:
                page.click("text=⚙️ 設定", timeout=2000)
                page.wait_for_timeout(400)
                shot("a20-settings-dropdown")
                for label, name in [("初期設定", "a21-settings"), ("会員", "a22-members"), ("商品", "a23-products"), ("得意先", "a24-customers"), ("斎場設定", "a25-halls"), ("ユーザー", "a26-users"), ("QR発行", "a27-qr")]:
                    try:
                        page.click("text=⚙️ 設定", timeout=1500)
                        page.wait_for_timeout(250)
                        page.click(f".settings-dropdown >> text={label}", timeout=1500)
                        page.wait_for_timeout(800)
                        shot(name)
                    except Exception as e:
                        print("settings item fail", label, e)
            except Exception as e:
                print("settings fail", e)

        page.close()

        # --- LIFF previews ---
        if only in ('', 'liff'):
            lp = ctx.new_page()
            lp.set_viewport_size({"width": 430, "height": 932})
            for scr in ["friend", "top", "top-day", "register", "pre-info", "pre-complete", "checkin-pending", "checkin-done", "profile"]:
                try:
                    lp.goto(f"{BASE}/index.html?preview={scr}")
                    lp.wait_for_timeout(1200)
                    lp.screenshot(path=f"{OUT}/l-{scr}.png", full_page=(scr == 'pre-info'))
                    print("shot: l-" + scr)
                except Exception as e:
                    print("liff fail", scr, e)
            lp.close()

        browser.close()


if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)
    main()
