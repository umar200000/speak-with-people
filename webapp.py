import os
import json
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from database import (
    add_user,
    get_user,
    get_all_tariffs,
    get_user_mocks,
    get_all_speak_tariffs,
    get_user_subscription,
    get_usage_status,
    add_daily_usage,
    is_premium,
    DAILY_LIMIT_SECONDS,
)

webapp = FastAPI()


from starlette.middleware.base import BaseHTTPMiddleware

class NgrokMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response

webapp.add_middleware(NgrokMiddleware)

HTML_PATH = os.path.join(os.path.dirname(__file__), "index.html")


class RegisterData(BaseModel):
    telegram_id: int = 0
    phone: str = ""
    gender: str = ""
    first_name: str = ""
    username: str = ""


@webapp.get("/", response_class=HTMLResponse)
def home():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


@webapp.get("/api/check/{telegram_id}")
def check_user(telegram_id: int):
    user = get_user(telegram_id)
    if user and user.get("gender"):
        return {"registered": True, "gender": user["gender"]}
    return {"registered": False}


@webapp.get("/api/tariffs")
def api_tariffs():
    return {"tariffs": get_all_tariffs(active_only=True)}


@webapp.get("/api/mocks/{telegram_id}")
def api_mocks(telegram_id: int):
    return {"mocks": get_user_mocks(telegram_id)}


@webapp.get("/api/speak_tariffs")
def api_speak_tariffs():
    return {"tariffs": get_all_speak_tariffs(active_only=True)}


@webapp.get("/api/subscription/{telegram_id}")
def api_subscription(telegram_id: int):
    return {"subscription": get_user_subscription(telegram_id)}


@webapp.get("/api/usage/{telegram_id}")
def api_usage(telegram_id: int):
    return get_usage_status(telegram_id)


class UsageReport(BaseModel):
    telegram_id: int
    seconds: int = 0
    partner_telegram_id: int = 0


@webapp.post("/api/usage/report")
def api_usage_report(data: UsageReport):
    """Qo'ng'iroq tugaganda sarflangan soniyani hisobga qo'shish.
    Agar partner premium bo'lsa — non-premium user'ga hisoblanmaydi."""
    if data.seconds <= 0:
        return get_usage_status(data.telegram_id)
    user_premium = is_premium(data.telegram_id)
    partner_premium = (
        is_premium(data.partner_telegram_id) if data.partner_telegram_id else False
    )
    # Premium userning vaqti hisobga olinmaydi umuman
    if user_premium:
        return get_usage_status(data.telegram_id)
    # Non-premium, lekin partner premium bo'lsa — hisoblanmaydi
    if partner_premium:
        return get_usage_status(data.telegram_id)
    # Ikkalasi ham non-premium — usage'ga qo'shiladi
    add_daily_usage(data.telegram_id, data.seconds)
    return get_usage_status(data.telegram_id)


@webapp.post("/api/register")
def register(data: RegisterData):
    from database import update_user_gender
    existing = get_user(data.telegram_id)
    if existing:
        update_user_gender(data.telegram_id, data.gender)
    else:
        add_user(
            telegram_id=data.telegram_id,
            phone=data.phone,
            gender=data.gender,
            first_name=data.first_name,
            username=data.username,
        )
    return {"ok": True}


# ===== WEBSOCKET MATCHING + SIGNALING =====

waiting_users = {}   # ws_id -> {ws, filters, user_info}
active_pairs = {}    # ws_id -> partner_ws_id
ws_connections = {}  # ws_id -> ws


def check_match(user1, user2):
    f1 = user1["filters"]
    f2 = user2["filters"]

    if f1["lang"] != f2["lang"]:
        return False

    level_order = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}
    u1_lvl = level_order.get(f1["userLevel"], 0)
    u2_lvl = level_order.get(f2["userLevel"], 0)

    if not (f2["minLevel"] <= u1_lvl <= f2["maxLevel"]):
        return False
    if not (f1["minLevel"] <= u2_lvl <= f1["maxLevel"]):
        return False

    u1_gender = f1.get("userGender", "")
    u2_gender = f2.get("userGender", "")

    # Gender filter — bo'sh gender bo'lsa any deb qabul qilinadi
    if f1["gender"] == "boys" and u2_gender and u2_gender != "Erkak":
        return False
    if f1["gender"] == "girls" and u2_gender and u2_gender != "Ayol":
        return False
    if f2["gender"] == "boys" and u1_gender and u1_gender != "Erkak":
        return False
    if f2["gender"] == "girls" and u1_gender and u1_gender != "Ayol":
        return False

    return True


@webapp.websocket("/ws/match")
async def websocket_match(ws: WebSocket):
    await ws.accept()
    ws_id = id(ws)
    ws_connections[ws_id] = ws

    try:
        while True:
            data = json.loads(await ws.receive_text())
            action = data.get("action")

            if action == "search":
                user_info = data.get("user_info", {}) or {}
                user_tid = int(user_info.get("telegram_id") or 0)
                user_premium = is_premium(user_tid) if user_tid else False
                user_info["is_premium"] = user_premium
                if user_tid:
                    user_info["telegram_id"] = user_tid

                # Agar non-premium bo'lsa, qolgan vaqtini tekshirish
                if not user_premium and user_tid:
                    status = get_usage_status(user_tid)
                    if status["remaining_seconds"] <= 0:
                        await ws.send_text(json.dumps({
                            "action": "limit-reached",
                            "usage": status,
                        }))
                        continue

                user_entry = {
                    "ws": ws,
                    "filters": data.get("filters", {}),
                    "user_info": user_info,
                }
                waiting_users[ws_id] = user_entry

                matched = False
                for other_id, other in list(waiting_users.items()):
                    if other_id == ws_id:
                        continue
                    if check_match(user_entry, other):
                        del waiting_users[ws_id]
                        del waiting_users[other_id]
                        active_pairs[ws_id] = other_id
                        active_pairs[other_id] = ws_id

                        # Call limit hisoblash: ikkalasi ham non-premium bo'lsa
                        # kichik qolgan vaqti bo'yicha cheklash, aks holda limitsiz
                        u1p = bool(user_entry["user_info"].get("is_premium"))
                        u2p = bool(other["user_info"].get("is_premium"))
                        if u1p or u2p:
                            call_limit = 0  # 0 = limitsiz
                        else:
                            tid1 = int(user_entry["user_info"].get("telegram_id") or 0)
                            tid2 = int(other["user_info"].get("telegram_id") or 0)
                            r1 = get_usage_status(tid1)["remaining_seconds"] if tid1 else DAILY_LIMIT_SECONDS
                            r2 = get_usage_status(tid2)["remaining_seconds"] if tid2 else DAILY_LIMIT_SECONDS
                            call_limit = max(0, min(r1, r2))

                        await ws.send_text(json.dumps({
                            "action": "matched",
                            "partner": other["user_info"],
                            "is_caller": True,
                            "call_limit_seconds": call_limit,
                            "self_is_premium": u1p,
                            "partner_is_premium": u2p,
                        }))
                        await other["ws"].send_text(json.dumps({
                            "action": "matched",
                            "partner": user_entry["user_info"],
                            "is_caller": False,
                            "call_limit_seconds": call_limit,
                            "self_is_premium": u2p,
                            "partner_is_premium": u1p,
                        }))
                        matched = True
                        break

                if not matched:
                    await ws.send_text(json.dumps({"action": "waiting"}))

            elif action == "cancel":
                waiting_users.pop(ws_id, None)
                await ws.send_text(json.dumps({"action": "cancelled"}))

            elif action in ("offer", "answer", "ice-candidate", "timer-sync", "connection-state", "mute-state"):
                partner_id = active_pairs.get(ws_id)
                if partner_id and partner_id in ws_connections:
                    await ws_connections[partner_id].send_text(json.dumps(data))

            elif action == "end-call":
                partner_id = active_pairs.get(ws_id)
                if partner_id and partner_id in ws_connections:
                    try:
                        await ws_connections[partner_id].send_text(
                            json.dumps({"action": "call-ended"})
                        )
                    except Exception:
                        pass
                active_pairs.pop(ws_id, None)
                if partner_id:
                    active_pairs.pop(partner_id, None)

    except WebSocketDisconnect:
        pass
    finally:
        waiting_users.pop(ws_id, None)
        partner_id = active_pairs.pop(ws_id, None)
        if partner_id:
            active_pairs.pop(partner_id, None)
            if partner_id in ws_connections:
                try:
                    await ws_connections[partner_id].send_text(
                        json.dumps({"action": "call-ended"})
                    )
                except Exception:
                    pass
        ws_connections.pop(ws_id, None)


# Adminkani /admin ostida mount qilish
from admin import app as admin_app
webapp.mount("/admin", admin_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(webapp, host="0.0.0.0", port=8080)
