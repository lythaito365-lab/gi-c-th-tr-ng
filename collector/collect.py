#!/usr/bin/env python3
"""Thu thập giá, ghi ra data/prices.json và data/history.json. Chỉ dùng thư viện chuẩn."""
import json, os, sys, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta, date

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
VN = timezone(timedelta(hours=7))
STALE_MANUAL_DAYS = 3
HEADERS = {"User-Agent": "Mozilla/5.0 (bantin-gia-ca)"}


def fetch(url, body=None):
    req = urllib.request.Request(url, data=body, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def item(id, name, cat, unit, price, source, region="all"):
    return dict(id=id, name=name, cat=cat, region=region, unit=unit, price=price, source=source)


# ---- Nguồn tự động. Mỗi hàm trả về danh sách item; lỗi ở một nguồn không ảnh hưởng nguồn khác.
def vietcombank():
    root = ET.fromstring(fetch("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10"))
    out = []
    for e in root.iter("Exrate"):
        c = e.get("CurrencyCode")
        if c in ("USD", "EUR", "JPY", "CNY"):
            try:
                out.append(item(f"fx-{c.lower()}-sell", f"{c}/VND bán ra", "ngoai-te", "đ",
                                float(e.get("Sell").replace(",", "")), "Vietcombank"))
            except (AttributeError, ValueError):
                pass
    return out


def world_rates():
    r = json.loads(fetch("https://open.er-api.com/v6/latest/USD"))["rates"]
    out = [item("fx-usd-mid", "USD/VND thị trường", "ngoai-te", "đ", round(r["VND"], 2), "open.er-api.com")]
    if r.get("XAU"):
        out.append(item("gold-world", "Vàng thế giới", "vang", "USD/oz", round(1 / r["XAU"], 2), "open.er-api.com"))
    return out


def sjc():
    j = json.loads(fetch("https://sjc.com.vn/GoldPrice/Services/PriceService.ashx",
                         b"method=GetCurrentGoldPricesByBranch&BranchId=1"))
    row = next(r for r in j["data"] if "SJC" in r["TypeName"])
    return [item("gold-sjc-buy", "Vàng SJC mua vào", "vang", "đ/lượng", float(row["BuyValue"]), "SJC"),
            item("gold-sjc-sell", "Vàng SJC bán ra", "vang", "đ/lượng", float(row["SellValue"]), "SJC")]


def manual():
    """Giá nhập tay trong data/manual.json (nông sản, thực phẩm, nhiên liệu, giá chợ theo vùng)."""
    with open(os.path.join(DATA, "manual.json"), encoding="utf-8") as f:
        rows = json.load(f)["items"]
    out = []
    for m in rows:
        if m.get("price") is None:
            continue
        it = item(m["id"], m["name"], m["cat"], m["unit"], float(m["price"]),
                  m.get("source", "Nhập tay"), m.get("region", "all"))
        it["asof"] = m.get("asof")
        out.append(it)
    return out


SOURCES = [vietcombank, world_rates, sjc, manual]


def load(name, default):
    p = os.path.join(DATA, name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return default


def save(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def main():
    now = datetime.now(VN)
    old, hist = load("prices.json", {"items": []}), load("history.json", {})
    fresh, errors = {}, []
    for src in SOURCES:
        try:
            for it in src():
                fresh[it["id"]] = it
        except Exception as e:
            errors.append(f"{src.__name__}: {type(e).__name__}: {e}")
    if not fresh:
        print("Không lấy được giá nào:", errors, file=sys.stderr)
        sys.exit(1)

    items = list(fresh.values())
    for it in old["items"]:  # nguồn lỗi: giữ giá cũ và đánh dấu
        if not old.get("demo") and it["id"] not in fresh:
            it["stale"] = True
            items.append(it)

    for it in items:
        if it["id"] in fresh:
            it["asof"] = it.get("asof") or now.isoformat(timespec="minutes")
            it["stale"] = (now.date() - date.fromisoformat(it["asof"][:10])).days > STALE_MANUAL_DAYS
            pts = hist.setdefault(it["id"], [])
            if not pts or pts[-1][1] != it["price"] or \
               (now - datetime.fromisoformat(pts[-1][0])).total_seconds() > 3600:
                pts.append([now.isoformat(timespec="minutes"), it["price"]])
                hist[it["id"]] = pts[-300:]
        pts = hist.get(it["id"], [])
        ref = next((p for p in reversed(pts) if datetime.fromisoformat(p[0]) <= now - timedelta(hours=24)),
                   pts[0] if len(pts) > 1 else None)
        it["change"] = round(it["price"] - ref[1], 4) if ref else None
        it["change_pct"] = round(it["change"] / ref[1] * 100, 3) if ref and ref[1] else None
        it["spark"] = [p[1] for p in pts[-48:]]

    save("history.json", hist)
    save("prices.json", {"updated": now.isoformat(timespec="seconds"), "demo": False,
                         "errors": errors, "items": items})
    print(f"Đã ghi {len(items)} mục, {len(errors)} nguồn lỗi")
    for e in errors:
        print(" -", e)


if __name__ == "__main__":
    main()
