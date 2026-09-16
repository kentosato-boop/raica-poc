#!/usr/bin/env python3
"""v11.0: 精算QR撮り直し＋QRカード/受付票/ご利用票(recorder方式)＋従業員ボタン"""
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request

TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()

RECORDER = """
const _o = window.open.bind(window);
window.open = (...a) => {
  const w = _o(...a);
  window._slipW = w;
  if (w && w.document) {
    const _w = w.document.write.bind(w.document);
    w.document.write = (s) => { window.__writes = (window.__writes || []); window.__writes.push(String(s)); _w(s); };
  }
  return w;
};
"""


def main():
    rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
    for r in rs:
        r.setdefault("createdAt", ts(600))
    collections = {"orders": ORDERS2, "checkins": CHECKINS, "reservations": rs}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 1100}, device_scale_factor=2,
                                  locale="ja-JP", timezone_id="Asia/Tokyo")

        def route_ext(route):
            url = route.request.url
            if "firebase-app-compat" in url:
                route.fulfill(content_type="application/javascript", body=FIREBASE_STUB)
            elif "firebase-firestore-compat" in url:
                route.fulfill(content_type="application/javascript", body="/*s*/")
            elif "qrcode.min.js" in url:
                route.fulfill(content_type="application/javascript", body=QRCODE_STUB)
            elif "xlsx.full.min.js" in url:
                route.fulfill(content_type="application/javascript", body=XLSX_STUB)
            elif url.startswith(BASE):
                route.continue_()
            else:
                route.fulfill(status=200, content_type="application/octet-stream", body=b"")

        ctx.route("**/*", route_ext)
        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');localStorage.setItem('mado_suppress_autoprint','1');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        page = ctx.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(2800)
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(1500)

        def closemodals():
            page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],.modal-overlay').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'});document.querySelectorAll('#toastZone .toast').forEach(t=>t.remove());")
            page.wait_for_timeout(300)

        def render_write(html, path, width=760):
            p2 = ctx.new_page()
            p2.set_viewport_size({"width": width, "height": 1100})
            p2.set_content(html, wait_until="domcontentloaded")
            p2.wait_for_timeout(1600)
            p2.screenshot(path=path, full_page=True)
            p2.close()
            print("saved:", path.split("/")[-1])

        # ── 精算QRモーダル（修正後mock） ──
        page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
        page.wait_for_timeout(1500)
        for so, name in [("783", "a64-priceqr-ok"), ("784", "a65-priceqr-blocked")]:
            try:
                page.evaluate(f"openPriceSimModal([{{sapSalesOrder:'{so}'}}], '1', 'CK-01')")
                page.wait_for_timeout(2400)
                page.screenshot(path=f"{OUT}/{name}.png")
                print("shot:", name)
                closemodals()
            except Exception as e:
                print("FAIL", name, str(e)[:80])
                closemodals()

        # ── 受付QRカード（QRボタン→印刷ウィンドウ; recorder） ──
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[2])")
        page.wait_for_timeout(1500)
        page.evaluate(RECORDER)
        try:
            page.evaluate("window.__writes=[]")
            page.locator("#rsvTableWrap .rsv-qr-btn:has-text('QR'):visible").first.click()
            page.wait_for_timeout(3500)
            writes = page.evaluate("window.__writes || []")
            final = next((w for w in reversed(writes) if "qr" in w.lower() and ("card" in w or "喪家名" in w)), None)
            print("qr-card writes:", len(writes), "final:", bool(final))
            if final:
                render_write(final, f"{OUT}/a16-checkin-qr-modal.png", width=560)
            try:
                page.evaluate("if(window._slipW)window._slipW.close()")
            except Exception:
                pass
        except Exception as e:
            print("FAIL a16", str(e)[:100])

        # ── 受付票（一括印刷; recorder） ──
        try:
            page.evaluate("window.__writes=[]; printReceptionList().catch(e=>window.__perr=String(e))")
            page.wait_for_timeout(3200)
            writes = page.evaluate("window.__writes || []")
            err = page.evaluate("window.__perr||''")
            final = next((w for w in reversed(writes) if "card" in w and "qr-0" in w), None)
            print("a71 writes:", len(writes), "err:", err[:60])
            if final:
                render_write(final, f"{OUT}/a71-checkin-slip.png", width=700)
            try:
                page.evaluate("if(window._slipW)window._slipW.close()")
            except Exception:
                pass
        except Exception as e:
            print("FAIL a71", str(e)[:100])

        # ── 自動精算機ご利用票（recorder） ──
        page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
        page.wait_for_timeout(1200)
        try:
            page.evaluate("""window.__writes=[]; printSettlementSheet({
              qrText: JSON.stringify({salesOrder:'783',amount:64260,currency:'JPY'}),
              amountNum: 64260, orderNo: '783', mourner: '東博　花子', company: '幕内祭典', label: '喪主' })""")
            page.wait_for_timeout(2500)
            writes = page.evaluate("window.__writes || []")
            final = next((w for w in reversed(writes) if "ご利用票" in w), None)
            print("a52 writes:", len(writes))
            if final:
                render_write(final, f"{OUT}/a52-settlement-slip.png", width=900)
        except Exception as e:
            print("FAIL a52", str(e)[:100])

        # ── 従業員ボタン（可視要素のbounding boxでクリップ） ──
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(900)
        page.select_option('#proxySP', 'SP-YT01')
        page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
        page.wait_for_timeout(1200)
        try:
            page.click("text=🚶 予約なし", timeout=3000)
            page.wait_for_timeout(1300)
            box = page.evaluate("""(()=>{const b=[...document.querySelectorAll('#panelProxy button')]
              .find(x=>x.offsetParent && x.textContent.includes('従業員'));
              if(!b) return null; const r=b.getBoundingClientRect();
              return {x:r.x-2,y:r.y-2,width:r.width+4,height:r.height+4};})()""")
            if box:
                page.screenshot(path=f"{OUT}/btn/p-btn-payer-employee.png", clip=box)
                print("ok: p-btn-payer-employee")
            else:
                allb = page.evaluate("[...document.querySelectorAll('button')].filter(x=>x.offsetParent&&x.textContent.includes('従業員')).length")
                print("FAIL employee: visible count =", allb)
        except Exception as e:
            print("FAIL employee", str(e)[:90])

        browser.close()


if __name__ == '__main__':
    main()
