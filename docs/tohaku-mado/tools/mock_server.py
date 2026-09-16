#!/usr/bin/env python3
"""mado admin.html/index.html 用ローカルモックサーバー（スクリーンショット撮影用）"""
import json, re, time, datetime, http.server, socketserver, os, urllib.parse

PORT = 8787
ROOT = os.path.join(os.path.dirname(__file__), 'public')
TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()
NOW_MS = int(time.time() * 1000)

HALLS = [
    {"id": "HALL-15MY", "name": "町屋斎場", "code": "15MY", "sapPlantCode": "15MY", "facilityCode": "machiya", "geofenceEnabled": True},
    {"id": "HALL-16OC", "name": "落合斎場", "code": "16OC", "sapPlantCode": "16OC", "geofenceEnabled": False},
    {"id": "HALL-17YY", "name": "代々幡斎場", "code": "17YY", "sapPlantCode": "17YY", "geofenceEnabled": False},
    {"id": "HALL-18YT", "name": "四ツ木斎場", "code": "18YT", "sapPlantCode": "18YT", "geofenceEnabled": True},
    {"id": "HALL-19KR", "name": "桐ヶ谷斎場", "code": "19KR", "sapPlantCode": "19KR", "geofenceEnabled": False},
    {"id": "HALL-20HR", "name": "堀ノ内斎場", "code": "20HR", "sapPlantCode": "20HR", "geofenceEnabled": False},
    {"id": "HALL-21OH", "name": "お花茶屋会館", "code": "21OH", "sapPlantCode": "21OH", "geofenceEnabled": False},
]

SALES_POINTS = [
    {"id": "SP-YT01", "hallId": "HALL-18YT", "name": "控室", "type": "hikaeshitsu", "freeDrinkRuleEnabled": True, "lastOrderEnabled": True, "sortOrder": 1},
    {"id": "SP-YT02", "hallId": "HALL-18YT", "name": "休憩室", "type": "kyukei", "freeDrinkRuleEnabled": True, "lastOrderEnabled": True, "sortOrder": 2},
    {"id": "SP-YT03", "hallId": "HALL-18YT", "name": "売店", "type": "baiten", "freeDrinkRuleEnabled": False, "lastOrderEnabled": False, "sortOrder": 3},
    {"id": "SP-YT04", "hallId": "HALL-18YT", "name": "ラウンジ", "type": "lounge", "freeDrinkRuleEnabled": True, "lastOrderEnabled": True, "sortOrder": 4},
]

MENU_ITEMS = [
    {"id": "MI-001", "name": "ブレンドコーヒー", "price": 400, "emoji": "☕", "category": "ドリンク", "sapItemCode": "3579", "mvgr1": "ドリンク", "mvgr3": "ソフトドリンク", "mvgr4": "1", "mvgr5": "ホット", "plant": "18YT", "available": True},
    {"id": "MI-002", "name": "アイスコーヒー", "price": 400, "emoji": "🧊", "category": "ドリンク", "sapItemCode": "3580", "mvgr1": "ドリンク", "mvgr3": "ソフトドリンク", "mvgr4": "1", "mvgr5": "アイス", "plant": "18YT", "available": True},
    {"id": "MI-003", "name": "オレンジジュース", "price": 430, "emoji": "🍊", "category": "ドリンク", "sapItemCode": "3581", "mvgr1": "ドリンク", "mvgr3": "ソフトドリンク", "mvgr4": "1", "mvgr5": "アイス", "plant": "18YT", "available": True},
    {"id": "MI-004", "name": "瓶ビール（中瓶）", "price": 770, "emoji": "🍺", "category": "アルコール", "sapItemCode": "3601", "mvgr1": "ドリンク", "mvgr3": "アルコール", "mvgr4": "1", "mvgr5": "ビール", "plant": "18YT", "available": True},
    {"id": "MI-005", "name": "天ぷらそば", "price": 980, "emoji": "🍜", "category": "お食事", "sapItemCode": "3702", "mvgr1": "フード", "mvgr3": "麺類", "mvgr4": "1", "mvgr5": "そば", "plant": "18YT", "available": True},
    {"id": "MI-006", "name": "精進料理膳", "price": 3300, "emoji": "🍱", "category": "お食事", "sapItemCode": "3709", "mvgr1": "フード", "mvgr3": "御膳", "mvgr4": "2", "mvgr5": "法要膳", "plant": "18YT", "available": True},
    {"id": "MI-007", "name": "骨壺（白磁 7寸）", "price": 15400, "emoji": "⚱️", "category": "葬祭用品", "sapItemCode": "4101", "mvgr1": "用品", "mvgr3": "骨壺", "mvgr4": "3", "mvgr5": "白磁", "plant": "18YT", "available": True},
]

RESERVATIONS = [
    {"id": "RSV-001", "funeralCompanyCustomerId": "900000", "bookingId": "TEST-2500200", "deceasedName": "東博　太郎", "deceasedKana": "とうはく　たろう", "funeralCompany": "幕内祭典", "applicantName": "東博　一郎", "applicantKana": "とうはく　いちろう", "applicantPhone": "070-4309-6523", "date": TODAY, "cremationTime": "10:00", "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "confirmed": True, "discounts": {}, "reservedItems": [{"name": "火葬料金（最上等）", "productGroup": "10", "quantity": 1, "price": 59000}], "preConsentLinked": True, "consentCremation": True},
    {"id": "RSV-002", "bookingId": "TEST-2500201", "deceasedName": "窓口　花子", "deceasedKana": "まどぐち　はなこ", "funeralCompany": "あすなろ祭典", "applicantName": "窓口　健二", "applicantKana": "まどぐち　けんじ", "applicantPhone": "080-1234-5678", "date": TODAY, "cremationTime": "10:00", "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "confirmed": True, "discounts": {}, "reservedItems": [], "preConsentLinked": False, "consentCremation": False},
    {"id": "RSV-003", "bookingId": "TEST-2500202", "deceasedName": "広済　次郎", "deceasedKana": "こうさい　じろう", "funeralCompany": "セレモニー光", "applicantName": "広済　三郎", "applicantKana": "こうさい　さぶろう", "applicantPhone": "090-8765-4321", "date": TODAY, "cremationTime": "11:00", "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "confirmed": False, "discounts": {"kuminso": True}, "reservedItems": [{"name": "式場使用料", "productGroup": "20", "quantity": 1, "price": 100000}], "preConsentLinked": False, "consentCremation": False},
    {"id": "RSV-004", "bookingId": "TEST-2500203", "deceasedName": "四ツ木　勇", "deceasedKana": "よつぎ　いさむ", "funeralCompany": "幕内祭典", "applicantName": "四ツ木　守", "applicantKana": "よつぎ　まもる", "applicantPhone": "070-1111-2222", "date": TODAY, "cremationTime": "13:00", "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "confirmed": True, "discounts": {}, "reservedItems": [], "preConsentLinked": True, "consentCremation": True},
    {"id": "RSV-005", "bookingId": "TEST-2500204", "deceasedName": "町屋　清", "deceasedKana": "まちや　きよし", "funeralCompany": "ひかり葬祭", "applicantName": "町屋　誠", "applicantKana": "まちや　まこと", "applicantPhone": "090-3333-4444", "date": TODAY, "cremationTime": "14:00", "hallId": "HALL-15MY", "hallName": "町屋斎場", "confirmed": True, "discounts": {}, "reservedItems": [], "preConsentLinked": False, "consentCremation": False},
]

PRE_CONSENTS = [
    {"id": "PC-001", "receiptNo": "260804-0001", "receiptNumber": "260804-0001", "status": "pending", "consentCremation": True, "cremationDate": TODAY, "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "deceasedName": "窓口　花子", "deceasedKana": "まどぐち　はなこ", "familyNameKana": "まどぐち", "applicantName": "窓口　健二", "applicantLastName": "窓口", "applicantFirstName": "健二", "applicantLastNameKana": "まどぐち", "applicantFirstNameKana": "けんじ", "phone": "080-1234-5678", "email": "kenji@example.com", "zip": "124-0011", "address": "東京都葛飾区四つ木1-1-1", "relation": "長男", "people": 12, "createdAtMs": NOW_MS - 86400000},
    {"id": "PC-002", "receiptNo": "260803-0002", "receiptNumber": "260803-0002", "status": "linked", "consentCremation": True, "cremationDate": TODAY, "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "deceasedName": "東博　太郎", "deceasedKana": "とうはく　たろう", "familyNameKana": "とうはく", "applicantName": "東博　一郎", "applicantLastName": "東博", "applicantFirstName": "一郎", "applicantLastNameKana": "とうはく", "applicantFirstNameKana": "いちろう", "phone": "070-4309-6523", "email": "", "zip": "116-0001", "address": "東京都荒川区町屋2-2-2", "relation": "長男", "people": 25, "reservationId": "RSV-001", "createdAtMs": NOW_MS - 172800000},
]

ROOMS = [
    {"spId": "SP-YT01", "spName": "控室", "roomId": "R-01", "roomName": "月の間1", "freeDrinkRuleEnabled": True,
     "currentAssignment": {"rsvLabel": "東博　太郎", "funeralCompany": "幕内祭典", "rsvId": "RSV-001", "expiresAt": {"_seconds": int(time.time()) + 1520}}},
    {"spId": "SP-YT01", "spName": "控室", "roomId": "R-02", "roomName": "月の間2", "freeDrinkRuleEnabled": True, "currentAssignment": None},
    {"spId": "SP-YT02", "spName": "休憩室", "roomId": "R-11", "roomName": "花の間1", "freeDrinkRuleEnabled": True, "currentAssignment": None},
    {"spId": "SP-YT02", "spName": "休憩室", "roomId": "R-12", "roomName": "花の間2", "freeDrinkRuleEnabled": True,
     "currentAssignment": {"rsvLabel": "四ツ木　勇", "funeralCompany": "幕内祭典", "rsvId": "RSV-004", "expiresAt": {"_seconds": int(time.time()) + 300}}},
    {"spId": "SP-YT04", "spName": "ラウンジ", "roomId": "R-21", "roomName": "ラウンジ席A", "freeDrinkRuleEnabled": False, "currentAssignment": None},
]

CUSTOMERS = [
    {"id": "CU-001", "name": "幕内祭典", "code": "C-0001", "kana": "まくうちさいてん", "phone": "03-1111-2222", "discounts": {"kuminso": True, "kentai": False, "gengaku": True, "kohi": False}},
    {"id": "CU-002", "name": "あすなろ祭典", "code": "C-0002", "kana": "あすなろさいてん", "phone": "03-3333-4444", "discounts": {}},
    {"id": "CU-003", "name": "セレモニー光", "code": "C-0003", "kana": "せれもにーひかり", "phone": "03-5555-6666", "discounts": {"kuminso": True}},
]

USERS = [
    {"id": "U-001", "username": "admin", "displayName": "管理者", "role": "superadmin", "allowedHallIds": [], "defaultSalesPointId": ""},
    {"id": "U-002", "username": "yotsugi-uketsuke", "displayName": "四ツ木 受付", "role": "staff", "allowedHallIds": ["HALL-18YT"], "defaultSalesPointId": "SP-YT03"},
]

MEMBERS = [
    {"id": "M-001", "memberId": "MB-260701-001", "name": "東博　一郎", "phone": "070-4309-6523", "funeralDate": TODAY, "menuPhase": "reception", "totalVisits": 2, "totalOrders": 3, "totalSpent": 4210, "lineReachable": True},
    {"id": "M-002", "memberId": "MB-260620-014", "name": "広済　三郎", "phone": "090-8765-4321", "funeralDate": "2026-06-25", "menuPhase": "aftercare", "totalVisits": 1, "totalOrders": 1, "totalSpent": 980, "lineReachable": True},
]


def member_payload(scenario, today):
    base_member = {"id": "M-001", "memberId": "MB-260701-001", "name": "東博　一郎", "kana": "とうはく　いちろう",
                   "phone": "070-4309-6523", "email": "", "party": 2, "consentMarketing": True}
    rc = {"bookingId": "TEST-2500200", "rsvId": "RSV-001", "consentCremation": True,
          "deceasedName": "東博　太郎", "cremationDate": today, "cremationTime": "10:00", "hallName": "四ツ木斎場"}
    if scenario == 'new':
        return {"found": False}
    if scenario == 'unconsented':
        m = dict(base_member); m["consentMarketing"] = False
        return {"found": True, "member": m, "reservationConsent": dict(rc, consentCremation=False)}
    if scenario == 'precheckin':
        return {"found": True, "member": base_member, "reservationConsent": rc}
    return {"found": True, "member": base_member, "reservationConsent": rc,
            "todayCheckin": {"status": "checked_in", "checkinId": "CK-001", "checkinNumber": 1,
                             "bookingId": "TEST-2500200", "reservationId": "RSV-001"}}

MOBILE_CATALOG = {"success": True, "plant": "18YT", "sapLocationCode": "YT01",
    "salesPointName": "控室", "roomName": "月の間1",
    "categories": [{"code": "お飲み物", "name": "お飲み物"}, {"code": "お食事", "name": "お食事"},
                    {"code": "フリードリンク", "name": "フリードリンク"}],
    "products": [
      {"code": "3579", "name": "ブレンドコーヒー", "price": 400, "categoryCode": "お飲み物", "longText": "香り高いオリジナルブレンド。ホットでご提供します。", "isFreeDrink": True, "extraCategories": ["フリードリンク"]},
      {"code": "3580", "name": "アイスコーヒー", "price": 400, "categoryCode": "お飲み物", "longText": "すっきりとした味わいのアイスコーヒー。", "isFreeDrink": True, "extraCategories": ["フリードリンク"]},
      {"code": "3581", "name": "オレンジジュース", "price": 430, "categoryCode": "お飲み物", "longText": "果汁100%のオレンジジュース。", "isFreeDrink": False, "extraCategories": []},
      {"code": "3601", "name": "瓶ビール（中瓶）", "price": 770, "categoryCode": "お飲み物", "longText": "キリン一番搾り 中瓶500ml。", "isFreeDrink": False, "extraCategories": []},
      {"code": "3702", "name": "天ぷらそば", "price": 980, "categoryCode": "お食事", "longText": "海老天2本入りの温かいおそばです。", "isFreeDrink": False, "extraCategories": []},
      {"code": "3709", "name": "精進料理膳", "price": 3300, "categoryCode": "お食事", "longText": "季節の野菜を使った精進料理の御膳。", "isFreeDrink": False, "extraCategories": []},
    ]}

LIFF_ORDERS = None

def summary_payload(cid):
    return {"success": True, "checkinId": cid, "sapStatus": "sent", "sapOrderNos": ["783", "784"],
            "totals": {"totalAmount": 3080, "taxTotal": 280, "netTotal": 2800},
            "items": [{"lineNumber": 10, "name": "ブレンドコーヒー", "sapItemCode": "3579", "quantity": 2, "price": 400, "productGroup": "1", "receiptGroup": "A"},
                       {"lineNumber": 20, "name": "精進料理膳", "sapItemCode": "3709", "quantity": 1, "price": 2280, "productGroup": "2", "receiptGroup": "A"}],
            "payers": [{"payer": "chief_mourner", "label": "喪主", "amount": 3080, "discount": 0, "tax": 280}],
            "grandTotals": {"amount": 3080},
            "summary": {"payers": [
                {"payerType": "chief_mourner", "payerLabel": "喪主", "payerName": "東博 一郎", "paymentType": "cash",
                 "sapSalesOrder": "783", "customerId": "0000900123",
                 "grossAmount": 4100, "discount": 410, "netAmount": 3690, "taxAmount": 369, "totalAmount": 4059,
                 "appliedDiscounts": [{"conditionType": "Z040", "label": "区民葬割引", "rateValue": 10, "itemCount": 2, "amount": -410}]},
                {"payerType": "funeral_company", "payerLabel": "葬儀社", "payerName": "幕内祭典", "paymentType": "account",
                 "sapSalesOrder": "784", "customerId": "0001000123",
                 "grossAmount": 1540, "discount": 0, "netAmount": 1540, "taxAmount": 154, "totalAmount": 1694,
                 "cashbackTotal": 300, "cashbackNet": 273, "cashbackTax": 27}],
                "grandTotals": {"grossAmount": 5640, "discount": 410, "netAmount": 5230,
                                 "taxAmount": 523, "totalAmount": 5753, "cashbackTotal": 300}},
            "discountBreakdown": []}

PSM_ORDERS = [
    {"id": "ORD-P1", "status": "billing", "sapStatus": "success", "checkinId": "CK-001",
     "itemDetails": [
         {"sapItemCode": "3579", "name": "ブレンドコーヒー", "quantity": 2, "price": 400,
          "paymentGroupKey": "1", "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "飲料"},
         {"sapItemCode": "3709", "name": "精進料理膳", "quantity": 1, "price": 3300,
          "paymentGroupKey": "1", "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "飲料"}]},
    {"id": "ORD-P2", "status": "billing", "sapStatus": "success", "checkinId": "CK-001",
     "itemDetails": [
         {"sapItemCode": "3601", "name": "瓶ビール（中瓶）", "quantity": 2, "price": 770,
          "paymentGroupKey": "2", "thirdSalesSpecProductGroup": "2", "thirdSalesSpecProductGroupLabel": "酒類"}]},
]

def cart_payload(cid):
    disc = lambda amt, n: [{"conditionType": "Z040", "label": "区民葬割引", "rateValue": 10, "itemCount": n, "amount": -amt}]
    return {"success": True, "cart": {
        "status": "SUCCESS", "externalOrderId": "TEST-2500200",
        "items": [
            {"lineNumber": 10, "materialCode": "3579", "text": "ブレンドコーヒー", "quantity": 2, "unit": "個", "receiptGroup": 1,
             "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "喪主",
             "sapAmounts": {"grossAmount": 800, "discount": 80, "netAmount": 720, "netPriceAmount": 400,
                             "taxAmount": 72, "totalAmount": 792, "appliedDiscounts": disc(80, 1)}},
            {"lineNumber": 20, "materialCode": "3709", "text": "精進料理膳", "quantity": 1, "unit": "個", "receiptGroup": 1,
             "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "喪主",
             "sapAmounts": {"grossAmount": 3300, "discount": 330, "netAmount": 2970, "netPriceAmount": 3300,
                             "taxAmount": 297, "totalAmount": 3267, "appliedDiscounts": disc(330, 1)}},
            {"lineNumber": 30, "materialCode": "3601", "text": "瓶ビール（中瓶）", "quantity": 2, "unit": "本", "receiptGroup": 2,
             "thirdSalesSpecProductGroup": "2", "thirdSalesSpecProductGroupLabel": "葬儀社",
             "sapAmounts": {"grossAmount": 1540, "discount": 0, "netAmount": 1540, "netPriceAmount": 770,
                             "taxAmount": 154, "totalAmount": 1694}},
        ],
        "sapAmounts": {
            "totals": {"grossAmount": 5640, "discount": 410, "netAmount": 5230, "taxAmount": 523,
                        "totalAmount": 5753, "cashback": 300},
            "discountBreakdown": [{"conditionType": "Z040", "label": "区民葬割引", "rateValue": 10, "itemCount": 2, "amount": -410}],
        },
    }}

def sap_order_summary(so):
    items = [{"materialCode": "3579", "materialDescription": "ブレンドコーヒー", "netAmount": 800, "quantity": 2},
             {"materialCode": "3709", "materialDescription": "精進料理膳", "netAmount": 2000, "quantity": 1}]
    if so == "784":
        return {"success": True,
                "summary": {"sapSalesOrder": "784", "header": {"currency": "JPY", "netAmount": 2800}, "items": items},
                "amounts": {"netAmount": 2800, "grossAvailable": False}}
    return {"success": True,
            "summary": {"sapSalesOrder": so, "header": {"currency": "JPY", "netAmount": 2800, "taxAmount": 280,
                                                          "totalNetAmount": 2800}, "items": items},
            "amounts": {"netAmount": 2800, "taxAmount": 280, "grossAmount": 3080}}

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):  # noqa: N802
        self.do_API('POST')

    def do_PATCH(self):  # noqa: N802
        self.do_API('PATCH')

    def do_DELETE(self):  # noqa: N802
        self.do_API('DELETE')

    def do_GET(self):  # noqa: N802
        if self.path.startswith('/api/'):
            self.do_API('GET')
        else:
            super().do_GET()

    def do_API(self, method):
        p = self.path.split('?')[0]
        q = self.path.split('?', 1)[1] if '?' in self.path else ''
        scenario = self.headers.get('X-Scenario', 'member')
        if p == '/api/crm/call-list':
            return self._json({"success": True, "list": [
                {"memberId": "M-001", "memberName": "東博　花子", "phone": "090-1234-5678", "funeralDate": TODAY,
                 "assignment": {"status": "架電済み", "assignedTo": "U-CC01", "nextCallAt": ""},
                 "ticket": {"labels": ["海洋散骨"]}},
                {"memberId": "M-002", "memberName": "東博　一郎", "phone": "080-2345-6789", "funeralDate": TODAY,
                 "assignment": {"status": "再架電", "assignedTo": "U-CC01", "nextCallAt": TODAY + "T15:00"},
                 "ticket": {"labels": ["仏壇・仏具"]}},
                {"memberId": "M-003", "memberName": "東博　太郎", "phone": "070-3456-7890", "funeralDate": TODAY,
                 "assignment": None, "ticket": None},
                {"memberId": "M-004", "memberName": "佐藤　次郎", "phone": "090-4567-8901", "funeralDate": TODAY,
                 "assignment": {"status": "資料請求", "assignedTo": "U-CC02", "nextCallAt": ""},
                 "ticket": {"labels": ["永代供養", "手元供養"]}}]})
        if p == '/api/crm/call-tickets':
            return self._json({"success": True, "tickets": [
                {"id": "T-001", "memberName": "東博　花子", "phone": "090-1234-5678", "status": "架電済み",
                 "labels": ["海洋散骨"], "totalCalls": 2, "lastCallAt": TODAY + "T10:30:00"},
                {"id": "T-002", "memberName": "東博　一郎", "phone": "080-2345-6789", "status": "再架電",
                 "labels": ["仏壇・仏具"], "totalCalls": 1, "lastCallAt": TODAY + "T09:10:00"},
                {"id": "T-003", "memberName": "佐藤　次郎", "phone": "090-4567-8901", "status": "資料請求",
                 "labels": ["永代供養", "手元供養"], "totalCalls": 3, "lastCallAt": TODAY + "T11:45:00"}]})
        if p == '/api/crm/tickets':
            return self._json({"success": True, "openCount": 1, "tickets": [
                {"id": "LT-001", "subject": "納骨のご相談", "lineDisplayName": "東博　花子", "memberName": "東博　花子",
                 "status": "open", "lastMessage": "四十九日の納骨について教えてください", "lastMessageAt": TODAY + "T13:05:00",
                 "unreadCount": 1, "updatedAt": TODAY + "T13:05:00"},
                {"id": "LT-002", "subject": "資料のお礼", "lineDisplayName": "東博　一郎", "memberName": "東博　一郎",
                 "status": "closed", "lastMessage": "資料が届きました。ありがとうございます。", "lastMessageAt": TODAY + "T09:40:00",
                 "unreadCount": 0, "updatedAt": TODAY + "T09:40:00"}]})
        if p == '/api/crm/sub-tickets':
            return self._json({"success": True, "subTickets": [
                {"id": "S-001", "memberName": "東博　花子", "label": "海洋散骨", "status": "資料請求",
                 "assignedTo": "ラベル担当A", "nextAppointment": TODAY + " 14:00"},
                {"id": "S-002", "memberName": "佐藤　次郎", "label": "永代供養", "status": "申込手続き",
                 "assignedTo": "ラベル担当B", "nextAppointment": ""},
                {"id": "S-003", "memberName": "東博　一郎", "label": "仏壇・仏具", "status": "未対応",
                 "assignedTo": "", "nextAppointment": ""}]})
        if p == '/api/crm/stats':
            return self._json({"success": True, "stats": {
                "未登録": 1, "再架電": 1, "架電済み": 1, "資料請求": 1, "詳細打合せ": 0,
                "totalTickets": 3, "totalSubTickets": 3, "todayCalls": 4,
                "subByStatus": {"未対応": 1, "資料請求": 1, "申込手続き": 1}}})
        if p == '/api/crm/labels':
            return self._json({"success": True, "labels": [
                {"name": "海洋散骨", "color": "#0ea5e9"}, {"name": "永代供養", "color": "#8b5cf6"},
                {"name": "仏壇・仏具", "color": "#f59e0b"}, {"name": "手元供養", "color": "#10b981"}]})
        if p == '/api/member':
            return self._json(member_payload(scenario, TODAY))
        if p == '/api/product-flavors':
            return self._json({"success": True, "flavors": {}})
        if p == '/api/mobile-catalog':
            if 'roomId=R-99' in q:
                return self._json({"success": False, "errorCode": "ROOM_NOT_ASSIGNED", "error": "部屋割当がありません"})
            return self._json(MOBILE_CATALOG)
        if p == '/api/orders':
            return self._json({"success": True, "scope": "booking", "orders": [
                {"orderNumber": 3, "status": "served", "date": TODAY, "total": 1660,
                 "items": [{"emoji": "☕", "name": "ブレンドコーヒー", "quantity": 1, "price": 400, "subtotal": 400},
                            {"emoji": "🧊", "name": "アイスコーヒー", "quantity": 1, "price": 400, "subtotal": 400},
                            {"emoji": "🍊", "name": "オレンジジュース", "quantity": 1, "price": 430, "subtotal": 430},
                            {"emoji": "🍋", "name": "レモネード", "quantity": 1, "price": 430, "subtotal": 430}]},
                {"orderNumber": 1, "status": "completed", "date": TODAY, "total": 3300,
                 "items": [{"emoji": "🍱", "name": "精進料理膳", "quantity": 1, "price": 3300, "subtotal": 3300}]}]})
        if p == '/api/my-cart':
            return self._json({"success": True,
                "cart": {"total": 64260, "status": "カート蓄積中", "bySource": {"reservation": 59000, "proxy": 3300, "self": 1660, "other": 300}},
                "items": [
                  {"name": "火葬料金（最上等）", "quantity": 1, "unitPrice": 59000, "netAmount": 59000, "source": "reservation", "isPreview": False},
                  {"name": "精進料理膳", "quantity": 1, "unitPrice": 3300, "netAmount": 3300, "source": "proxy", "isPreview": False},
                  {"name": "ブレンドコーヒー ほか3点", "quantity": 4, "unitPrice": 0, "netAmount": 1660, "source": "self", "isPreview": True},
                  {"name": "オレンジジュース", "quantity": 1, "unitPrice": 300, "netAmount": 300, "source": "other", "isPreview": True}]})
        if p == '/api/my-cart/mourner-summary':
            return self._json({"success": True, "isConfirmed": True, "totalGross": 64260, "totalNet": 58418, "totalTax": 5842,
                "meta": {"hasUnassignedItems": False},
                "items": [
                  {"name": "火葬料金（最上等）", "quantity": 1, "netAmount": 59000, "productGroup": "2"},
                  {"name": "式場使用料（第1式場）", "quantity": 1, "netAmount": 0, "productGroup": "1"},
                  {"name": "精進料理膳", "quantity": 1, "netAmount": 3300, "productGroup": "20"},
                  {"name": "ブレンドコーヒー", "quantity": 2, "netAmount": 800, "productGroup": "20"},
                  {"name": "骨壺（白磁 7寸）", "quantity": 1, "netAmount": 1160, "productGroup": "10"}]})
        if p == '/api/halls':
            return self._json({"success": True, "halls": [dict(h, phone="03-3892-100" + str(i)) for i, h in enumerate(HALLS)]})
        if p == '/api/checkin' and method == 'POST':
            return self._json({"success": True, "checkinId": "CK-001", "checkinNumber": 1, "bookingId": "TEST-2500200", "reservationId": "RSV-001"})
        if p == '/api/order' and method == 'POST':
            return self._json({"success": True, "orderNumber": 6, "orderId": "O-006", "total": 1200})
        if p == '/api/pre-consent' and method == 'POST':
            return self._json({"success": True, "preConsentId": "PC-001"})
        if p == '/api/register' and method == 'POST':
            return self._json({"success": True, "autoCheckin": True, "memberId": "M-001"})
        if p == '/api/menu':
            return self._json({"menu": {"お飲み物": MENU_ITEMS[:4], "お食事": MENU_ITEMS[4:6]}, "salesPointName": "控室"})
        if p == '/api/admin/me':
            return self._json({"success": True, "user": USERS[0]})
        if p == '/api/admin/sap/products' or p.startswith('/api/admin/sap/products?'):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            kw = (qs.get('search') or [''])[0]
            cands = [
                {"sapItemCode": "200100", "name": "火葬料金（最上等）", "price": 59000, "productGroup": "2", "unit": "AU"},
                {"sapItemCode": "200101", "name": "火葬料金（特別殯館）", "price": 107500, "productGroup": "2", "unit": "AU"},
                {"sapItemCode": "200102", "name": "火葬料金（最上等・区民葬）", "price": 40000, "productGroup": "2", "unit": "AU"},
                {"sapItemCode": "3579", "name": "ブレンドコーヒー", "price": 400, "productGroup": "20", "unit": "AU"},
                {"sapItemCode": "3601", "name": "瓶ビール（中瓶）", "price": 770, "productGroup": "20", "unit": "AU"},
            ]
            items = [c for c in cands if not kw or kw.split('（')[0] in c["name"]]
            return self._json({"success": True, "items": items})
        if p == '/api/admin/sap/products/urns':
            return self._json({"success": True, "items": [
                {"code": "28307", "name": "骨壺（白磁 7寸）", "price": 1160, "size": "7寸"},
                {"code": "28308", "name": "骨壺（白磁 6寸）", "price": 1050, "size": "6寸"},
                {"code": "28315", "name": "骨壺（青磁 7寸）", "price": 1600, "size": "7寸"}]})
        if p.startswith('/api/admin/checkin/') and p.endswith('/receipt-splits'):
            return self._json({"success": True, "splits": [], "items": [
                {"materialCode": "3579", "name": "ブレンドコーヒー", "quantity": 2, "orderSource": "line", "receiptGroup": 1},
                {"materialCode": "3709", "name": "精進料理膳", "quantity": 1, "orderSource": "proxy", "receiptGroup": 1}]})
        if p == '/api/admin/checkins':
            return self._json({"success": True, "checkins": []})
        if p == '/api/admin/sap/base-url':
            return self._json({"success": True, "baseUrl": "https://saptest-staging.example.jp"})
        if p == '/api/admin/sap/products/storage-location-filter':
            return self._json({"success": True, "materialCodes": []})
        if p == '/api/admin/inventory/fetch' and method == 'POST':
            return self._json({"success": True, "items": [], "total": 0, "hasMore": False})
        if p == '/api/admin/reservation-consent-tokens' and method == 'POST':
            try:
                n = int(self.headers.get('Content-Length') or 0)
                body = json.loads(self.rfile.read(n) or b'{}')
                ids = body.get('reservationIds') or []
            except Exception:
                ids = []
            toks = [{"reservationId": rid, "consentToken": f"tok-{i+1:04d}"} for i, rid in enumerate(ids)]
            return self._json({"success": True, "tokens": toks, "ttlHours": 24})
        if p == '/api/pre-consent-fields.js':
            # 実機 functions/pre-consent-fields.js と同一のフィールド定義・エラー文言を再現
            body = ("""
window.PreConsentFields=(function(){
  function kataToHira(v){return String(v||'').replace(/[\\u30A1-\\u30F6\\u30FD\\u30FE]/g,function(c){return String.fromCharCode(c.charCodeAt(0)-0x60);});}
  function normalizeKana(v){return kataToHira(String(v||'').normalize('NFKC')).replace(/[\\s\\u3000]+/g,' ').trim();}
  function normalizeText(v){return String(v||'').normalize('NFKC').trim();}
  function digitsOnly(v){return String(v||'').replace(/[^0-9]/g,'');}
  var KANA_OK=/^[\\u3041-\\u3096\\u30F7-\\u30FA\\u30FC\\u30FB\\u309D\\u309E ]+$/,KANA_HAS=/[\\u3041-\\u3096\\u30F7-\\u30FA]/;
  var EMAIL=/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
  var SPECS=[
    {key:'hallId',label:'斎場',kind:'hall',max:100},{key:'funeralDate',label:'火葬日',kind:'date',max:10},
    {key:'deceasedLastName',label:'故人様姓',kind:'text',max:50},{key:'deceasedFirstName',label:'故人様名',kind:'text',max:50},
    {key:'deceasedLastNameKana',label:'故人様姓（かな）',kind:'kana',max:50},{key:'deceasedFirstNameKana',label:'故人様名（かな）',kind:'kana',max:50},
    {key:'applicantLastName',label:'申込者姓',kind:'text',max:50},{key:'applicantFirstName',label:'申込者名',kind:'text',max:50},
    {key:'applicantLastNameKana',label:'申込者姓（かな）',kind:'kana',max:50},{key:'applicantFirstNameKana',label:'申込者名（かな）',kind:'kana',max:50},
    {key:'applicantPhone',label:'電話番号',kind:'tel'},{key:'applicantEmail',label:'メールアドレス',kind:'email',max:254},
    {key:'applicantPostalCode',label:'郵便番号',kind:'postal'},{key:'applicantAddress',label:'住所',kind:'text',max:200},
    {key:'applicantRelationship',label:'続柄',kind:'relationship',max:50}];
  function check(s,raw,opts){
    var REQ=s.label+'は必須です';
    if(s.kind==='kana'){var v=normalizeKana(raw);
      if(!v)return{value:v,message:REQ};
      if(v.length>s.max)return{value:v,message:s.label+'は'+s.max+'文字以内で入力してください'};
      if(!KANA_OK.test(v))return{value:v,message:s.label+'はひらがなまたはカタカナで入力してください'};
      if(!KANA_HAS.test(v))return{value:v,message:s.label+'にはかなを1文字以上入力してください'};
      return{value:v,message:''};}
    if(s.kind==='tel'){var r=normalizeText(raw);
      if(r&&/[^0-9()\\-\\s]/.test(r))return{value:digitsOnly(r),message:'電話番号に使用できない文字が含まれています'};
      var v2=digitsOnly(r); if(!v2)return{value:v2,message:REQ};
      if(!/^\\d{10,11}$/.test(v2))return{value:v2,message:'電話番号は10桁または11桁で入力してください'};
      return{value:v2,message:''};}
    if(s.kind==='postal'){var r2=normalizeText(raw);
      if(r2&&/[^0-9\\-\\s]/.test(r2))return{value:digitsOnly(r2),message:'郵便番号に使用できない文字が含まれています'};
      var v3=digitsOnly(r2); if(!v3)return{value:v3,message:REQ};
      if(!/^\\d{7}$/.test(v3))return{value:v3,message:'郵便番号は7桁で入力してください'};
      return{value:v3,message:''};}
    if(s.kind==='email'){var v4=normalizeText(raw);
      if(!v4)return{value:v4,message:REQ};
      if(v4.length>s.max)return{value:v4,message:s.label+'は'+s.max+'文字以内で入力してください'};
      if(!EMAIL.test(v4))return{value:v4,message:'メールアドレスの形式が不正です'};
      return{value:v4,message:''};}
    if(s.kind==='date'){var v5=normalizeText(raw);
      if(!v5)return{value:v5,message:REQ};
      if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(v5))return{value:v5,message:'火葬日の形式が不正です'};
      if(opts&&opts.minDate&&v5<opts.minDate)return{value:v5,message:'火葬日は今日以降を指定してください'};
      return{value:v5,message:''};}
    if(s.kind==='hall'){var v6=normalizeText(raw);
      if(!v6)return{value:v6,message:REQ};
      if(opts&&opts.validHallIds&&!opts.validHallIds.has(v6))return{value:v6,message:'無効な斎場です'};
      return{value:v6,message:''};}
    if(s.kind==='relationship'){var v7=normalizeText(raw);
      if(!v7)return{value:v7,message:REQ};
      if(v7==='その他')return{value:v7,message:'続柄は具体的に入力してください'};
      return{value:v7,message:''};}
    var v8=normalizeText(raw);
    if(!v8)return{value:v8,message:REQ};
    if(v8.length>s.max)return{value:v8,message:s.label+'は'+s.max+'文字以内で入力してください'};
    return{value:v8,message:''};}
  function validatePreConsentForm(input,options){
    var errors=[],values={},opts=options||{};
    SPECS.forEach(function(s){var r=check(s,(input||{})[s.key],opts);values[s.key]=r.value;
      if(r.message)errors.push({key:s.key,label:s.label,message:r.message});});
    values.deceasedFullName=(values.deceasedLastName+'　'+values.deceasedFirstName).trim();
    return{ok:errors.length===0,errors:errors,values:values};}
  return{validatePreConsentForm:validatePreConsentForm,normalizeKana:normalizeKana};
})();
""").encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
            return
        if p == '/api/admin/halls':
            return self._json({"success": True, "halls": HALLS})
        if p == '/api/menu':
            return self._json({"menu": {"all": MENU_ITEMS}})
        if p.startswith('/api/admin/sales-points'):
            return self._json({"success": True, "salesPoints": SALES_POINTS, "items": SALES_POINTS})
        if p == '/api/admin/reservations':
            rs = RESERVATIONS
            m = re.search(r'hallId=([^&]+)', q)
            if m and m.group(1):
                rs = [r for r in rs if r["hallId"] == m.group(1)]
            m2 = re.search(r'bookingId=([^&]+)', q)
            if m2:
                rs = [r for r in RESERVATIONS if r["bookingId"] == m2.group(1)]
            return self._json({"success": True, "reservations": rs, "total": len(RESERVATIONS), "degraded": None})
        if p == '/api/admin/booking-by-qr':
            return self._json({"success": True, "reservation": RESERVATIONS[0]})
        if p == '/api/admin/pre-consents':
            return self._json({"success": True, "items": PRE_CONSENTS, "preConsents": PRE_CONSENTS,
                               "unconsented": [{"id": "RSV-002", "bookingId": "TEST-2500201", "deceasedName": "窓口　花子", "funeralCompany": "あすなろ祭典", "cremationTime": "10:00", "date": TODAY, "hallName": "四ツ木斎場", "applicantPhone": "080-1234-5678"}],
                               "truncated": False})
        if p.startswith('/api/admin/pre-consents/') and p.endswith('/candidates'):
            return self._json({"success": True, "candidates": [dict(r, matchExact=(r["id"] == "RSV-002")) for r in RESERVATIONS if r["hallId"] == "HALL-18YT"]})
        if p == '/api/admin/room-assignments':
            return self._json({"success": True, "rooms": ROOMS, "serverTime": int(time.time() * 1000)})
        if p == '/api/admin/customers':
            return self._json({"success": True, "customers": CUSTOMERS, "items": CUSTOMERS})
        if p == '/api/admin/users':
            return self._json({"success": True, "users": USERS})
        if p == '/api/admin/members':
            return self._json({"success": True, "members": MEMBERS})
        if re.match(r'^/api/admin/checkin/[^/]+/summary$', p):
            return self._json(summary_payload(p.split('/')[4]))
        m = re.match(r'^/api/admin/sap-order/([^/]+)/summary$', p)
        if m:
            return self._json(sap_order_summary(m.group(1)))
        if re.match(r'^/api/admin/checkin/[^/]+/orders$', p):
            return self._json({"success": True, "orders": PSM_ORDERS})
        if re.match(r'^/api/admin/checkin/[^/]+/cart$', p):
            return self._json(cart_payload(p.split('/')[4]))
        if re.match(r'^/api/admin/checkin/[^/]+/receipt-splits$', p):
            return self._json({"success": True, "items": summary_payload('')["items"], "groups": ["A", "B"]})
        if p == '/api/admin/webhooks':
            return self._json({"success": True, "urls": [], "webhooks": []})
        if p == '/api/admin/product-flavors':
            return self._json({"success": True, "flavors": [], "items": []})
        if p == '/api/admin/order-location-config':
            return self._json({"success": True, "config": {"defaultMinutes": 30}, "defaultMinutes": 30})
        if p == '/api/admin/richmenu-status':
            return self._json({"success": True, "reception": True, "aftercare": True})
        if p == '/api/products' or p.startswith('/api/admin/products'):
            return self._json({"success": True, "products": MENU_ITEMS, "items": MENU_ITEMS})
        return self._json({"success": True, "items": [], "urls": [], "keys": [], "logs": [], "events": []})


if __name__ == '__main__':
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), H) as srv:
        print(f"serving on http://127.0.0.1:{PORT}")
        srv.serve_forever()
