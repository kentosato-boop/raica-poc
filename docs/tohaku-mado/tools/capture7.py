#!/usr/bin/env python3
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, ORDERS, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request
rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
for r in rs: r.setdefault("createdAt", ts(600))
collections = {"orders": ORDERS2, "checkins": CHECKINS, "reservations": rs}
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
    # ログインキータブ（未ログインコンテキスト）
    ctx2 = browser.new_context(viewport={"width":1600,"height":1000}, device_scale_factor=1.5, locale="ja-JP")
    ctx2.route("**/*", route_ext)
    p2 = ctx2.new_page(); p2.goto(BASE + "/admin.html"); p2.wait_for_timeout(1200)
    try:
        p2.click("text=ログインキー", timeout=2500); p2.wait_for_timeout(400)
        p2.screenshot(path=OUT+"/a45-login-key-tab.png"); print("shot: a45-login-key-tab")
    except Exception as e: print("key tab fail", e)
    ctx2.close()
    page = ctx.new_page()
    page.goto(BASE + "/admin.html"); page.wait_for_timeout(2500)
    page.evaluate("const s=document.getElementById(\'globalHallSelect\'); s.style.display=\'\'; s.value=\'HALL-18YT\'; onGlobalHallChange();")
    page.wait_for_timeout(800)
    # SAP送信内容モーダル
    try:
        page.click("text=送信内容", timeout=2500); page.wait_for_timeout(800)
        page.screenshot(path=OUT+"/a46-sap-payload-modal.png"); print("shot: a46-sap-payload-modal")
        page.evaluate("document.querySelectorAll(\'div[id*=Modal],div[id*=Overlay]\').forEach(e=>{if(getComputedStyle(e).position===\'fixed\')e.style.display=\'none\'})")
    except Exception as e: print("payload fail", e)
    # 初期設定フルページ
    try:
        page.evaluate("showPanelFromMenu(\'settings\')"); page.wait_for_timeout(1200)
        page.screenshot(path=OUT+"/a47-settings-full.png", full_page=True); print("shot: a47-settings-full")
    except Exception as e: print("settings full fail", e)
    browser.close()

