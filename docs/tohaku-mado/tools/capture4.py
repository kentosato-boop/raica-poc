#!/usr/bin/env python3
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, ORDERS, CHECKINS, ts, BASE, OUT)
from playwright.sync_api import sync_playwright
import urllib.request
TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()
rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
for r in rs: r.setdefault("createdAt", ts(600))
collections = {"orders": ORDERS, "checkins": CHECKINS, "reservations": rs}
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    ctx = browser.new_context(viewport={"width":1600,"height":1000}, device_scale_factor=1.5, locale="ja-JP", timezone_id="Asia/Tokyo")
    def route_ext(route):
        url = route.request.url
        if "firebase-app-compat" in url: route.fulfill(content_type="application/javascript", body=FIREBASE_STUB)
        elif "firebase-firestore-compat" in url: route.fulfill(content_type="application/javascript", body="/*s*/")
        elif "qrcode.min.js" in url: route.fulfill(content_type="application/javascript", body=QRCODE_STUB)
        elif "xlsx.full.min.js" in url: route.fulfill(content_type="application/javascript", body=XLSX_STUB)
        elif url.startswith(BASE): route.continue_()
        else: route.abort()
    ctx.route("**/*", route_ext)
    ctx.add_init_script("window.__MOCK_COLLECTIONS__ = " + json.dumps(collections, ensure_ascii=False) + ";")
    ctx.add_init_script("try{sessionStorage.setItem(\'adminToken\',\'MOCK-TOKEN\');}catch(e){}")
    ctx.add_init_script(LEAFLET_STUB); ctx.add_init_script(QRCODE_STUB)
    page = ctx.new_page()
    def shot(n, full=False): page.screenshot(path=OUT+"/"+n+".png", full_page=full); print("shot:", n)
    page.goto(BASE + "/admin.html"); page.wait_for_timeout(2500)
    page.evaluate("const s=document.getElementById(\'globalHallSelect\'); s.style.display=\'\'; s.value=\'HALL-18YT\'; onGlobalHallChange();")
    page.wait_for_timeout(800)
    page.evaluate("showPanel(\'payment\',document.querySelectorAll(\'.tab-btn\')[5])")
    page.wait_for_timeout(1000)
    try:
        page.click("#panelPayment button:has-text(\'割引\')", timeout=3000); page.wait_for_timeout(800)
        shot("a30-discount-modal")
        page.evaluate("document.querySelectorAll(\'div[id*=Modal],div[id*=Overlay]\').forEach(e=>{if(getComputedStyle(e).position===\'fixed\')e.style.display=\'none\'})")
    except Exception as e: print("discount fail", e)
    try:
        page.click("#panelPayment >> text=▼ 詳細 (3)", timeout=3000); page.wait_for_timeout(900)
        shot("a31-payment-detail")
    except Exception as e: print("detail fail", e)
    try:
        page.click("#panelPayment button:has-text(\'領収書\')", timeout=2500); page.wait_for_timeout(800)
        shot("a32-receipt-split-modal")
    except Exception as e: print("receipt fail", e)
    browser.close()

