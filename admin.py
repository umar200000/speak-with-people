import os
import hmac
import hashlib
from datetime import datetime
from string import Template

from fastapi import FastAPI, Form, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from database import (
    get_all_users,
    delete_user,
    get_all_tariffs,
    get_tariff,
    add_tariff,
    update_tariff,
    delete_tariff,
    get_all_users_with_mocks,
    set_user_mocks,
    adjust_user_mocks,
    LANGUAGES,
)

# ===== AUTH =====
ADMIN_USERNAME = "ustoz1999"
ADMIN_PASSWORD = "umar2000"
COOKIE_NAME = "speak_admin_session"
# Secret (fayldan o'qish yoki default)
AUTH_SECRET = os.environ.get("ADMIN_SECRET", "speak-bot-admin-secret-7x2k9")


def _session_token():
    """Login bo'yicha signed token."""
    raw = f"{ADMIN_USERNAME}:{ADMIN_PASSWORD}:{AUTH_SECRET}"
    return hmac.new(AUTH_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()


def _is_authed(request: Request) -> bool:
    tok = request.cookies.get(COOKIE_NAME, "")
    return hmac.compare_digest(tok, _session_token()) if tok else False


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # login, static, favicon — auth kerakmas
        if path.endswith("/login") or path.endswith("/favicon.ico"):
            return await call_next(request)
        if not _is_authed(request):
            return RedirectResponse(url="/admin/login", status_code=303)
        return await call_next(request)


app = FastAPI()
app.add_middleware(AuthMiddleware)


def format_price(price):
    try:
        return f"{int(price):,}".replace(",", " ") + " so'm"
    except Exception:
        return str(price)


def _esc(s):
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


# ===== SHARED CSS / SIDEBAR =====
BASE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', 'SF Pro Display', sans-serif; background: #f0f2f5; display: flex; min-height: 100vh; color: #1c1c1e; }
.sidebar { width: 240px; background: #1e1e2d; color: white; display: flex; flex-direction: column; flex-shrink: 0; position: sticky; top: 0; height: 100vh; }
.sidebar-logo { padding: 24px 20px; border-bottom: 1px solid #2d2d44; font-size: 20px; font-weight: 700; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); letter-spacing: 0.3px; }
.sidebar-menu { padding: 12px 0; flex: 1; }
.sidebar-menu a { display: flex; align-items: center; gap: 12px; padding: 14px 24px; color: #8a8aa0; text-decoration: none; font-size: 15px; transition: all 0.2s; font-weight: 500; }
.sidebar-menu a:hover { background: #2d2d44; color: white; }
.sidebar-menu a.active { background: #2d2d44; color: white; border-left: 3px solid #667eea; }
.sidebar-menu a .icon { font-size: 18px; width: 24px; text-align: center; }
.sidebar-footer { padding: 14px 20px; border-top: 1px solid #2d2d44; }
.sidebar-footer a { display: flex; align-items: center; gap: 10px; color: #8a8aa0; text-decoration: none; font-size: 13px; padding: 8px; border-radius: 8px; transition: all 0.2s; }
.sidebar-footer a:hover { background: #2d2d44; color: white; }
.main { flex: 1; overflow-y: auto; padding: 30px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
.page-title { font-size: 26px; font-weight: 700; color: #333; }
.btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 10px 20px; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s; }
.btn-primary:hover { opacity: 0.92; transform: translateY(-1px); }
.stats { display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
.stat-card { background: white; padding: 24px 32px; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); flex: 1; min-width: 180px; text-align: center; }
.stat-card .number { font-size: 38px; font-weight: 800; color: #667eea; }
.stat-card .label { color: #999; margin-top: 6px; font-size: 14px; }
.stat-card.male .number { color: #4a90d9; }
.stat-card.female .number { color: #e91e8c; }
.stat-card.mocks .number { color: #34c759; }
.card { background: white; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); overflow: hidden; }
.card-header { padding: 18px 24px; border-bottom: 1px solid #f0f0f0; font-size: 17px; font-weight: 600; color: #333; }
table { width: 100%; border-collapse: collapse; }
th { background: #f8f9ff; color: #667eea; padding: 14px 16px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; }
td { padding: 14px 16px; border-bottom: 1px solid #f5f5f5; vertical-align: middle; font-size: 14px; }
tr:hover td { background: #fafbff; }
.user-info { display: flex; align-items: center; gap: 12px; }
.user-avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 15px; flex-shrink: 0; }
.user-avatar img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.user-name { font-weight: 600; color: #333; }
.user-username { font-size: 12px; color: #999; }
.gender-male { color: #4a90d9; font-weight: 600; }
.gender-female { color: #e91e8c; font-weight: 600; }
.badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; display: inline-block; }
.badge-active { background: #e0fce8; color: #1f9a43; }
.badge-inactive { background: #fde2e2; color: #c0392b; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-edit { background: #4a90d9; color: white; border: none; padding: 7px 14px; border-radius: 8px; cursor: pointer; font-size: 12px; text-decoration: none; font-weight: 600; }
.btn-edit:hover { background: #3d7dc1; }
.btn-delete { background: #ff4757; color: white; border: none; padding: 7px 14px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; }
.btn-delete:hover { background: #e8384f; }
.btn-give { background: #34c759; color: white; border: none; padding: 7px 12px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; }
.btn-give:hover { background: #2ea847; }
.btn-remove { background: #ff9500; color: white; border: none; padding: 7px 12px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; }
.btn-remove:hover { background: #e8860a; }
.empty { text-align: center; padding: 60px; color: #999; font-size: 15px; }
.lang-cell { display: flex; gap: 6px; flex-wrap: wrap; }
.lang-pill { background: #f2f2f7; border-radius: 10px; padding: 6px 10px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; }
.lang-pill .flag { font-size: 14px; }
.lang-pill .count { color: #34c759; font-weight: 800; }
.lang-pill.zero .count { color: #999; }
.modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 100; align-items: center; justify-content: center; padding: 20px; }
.modal-overlay.active { display: flex; }
.modal { background: white; border-radius: 16px; padding: 26px; width: 100%; max-width: 480px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); max-height: 92vh; overflow-y: auto; }
.modal h3 { margin-bottom: 16px; color: #333; font-size: 19px; }
.modal p { color: #777; margin-bottom: 16px; font-size: 14px; line-height: 1.5; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 12px; font-weight: 700; color: #555; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.3px; }
.form-group input, .form-group textarea, .form-group select { width: 100%; padding: 11px 12px; border: 1px solid #ddd; border-radius: 9px; font-size: 14px; font-family: inherit; transition: border-color 0.2s; }
.form-group input:focus, .form-group textarea:focus, .form-group select:focus { outline: none; border-color: #667eea; }
.form-row { display: flex; gap: 12px; }
.form-row .form-group { flex: 1; }
.modal-tabs { display: flex; gap: 4px; background: #f2f2f7; border-radius: 10px; padding: 4px; margin-bottom: 16px; }
.modal-tab { flex: 1; padding: 9px 10px; text-align: center; cursor: pointer; border-radius: 8px; font-size: 13px; font-weight: 600; color: #666; transition: all 0.2s; border: none; background: transparent; }
.modal-tab.active { background: white; color: #667eea; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.modal-tab-content { display: none; }
.modal-tab-content.active { display: block; }
.modal-buttons { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
.modal-buttons button, .modal-buttons a { padding: 10px 20px; border-radius: 9px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; text-decoration: none; }
.btn-cancel { background: #f0f0f0; color: #555; }
.btn-confirm { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
.btn-confirm-del { background: #ff4757; color: white; }
.btn-confirm-green { background: #34c759; color: white; }
.btn-confirm-orange { background: #ff9500; color: white; }
.lang-info-row { background: #f9f9fc; border-radius: 10px; padding: 12px 14px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; font-size: 13px; }
.lang-info-row strong { color: #333; }
@media (max-width: 820px) {
    body { flex-direction: column; }
    .sidebar { width: 100%; height: auto; position: static; flex-direction: row; overflow-x: auto; }
    .sidebar-logo { padding: 16px; font-size: 16px; flex-shrink: 0; }
    .sidebar-menu { display: flex; padding: 0; }
    .sidebar-menu a { padding: 12px 14px; font-size: 13px; white-space: nowrap; border-left: none; border-bottom: 3px solid transparent; }
    .sidebar-menu a.active { border-left: none; border-bottom-color: #667eea; }
    .sidebar-footer { display: none; }
    .main { padding: 16px; }
}
"""


def sidebar_html(active):
    items = [
        ("/admin/", "users", "&#128101;", "Foydalanuvchilar"),
        ("/admin/tariffs", "tariffs", "&#11088;", "Tariflar"),
        ("/admin/mocks", "mocks", "&#127919;", "Mock berish"),
    ]
    html = '<div class="sidebar"><div class="sidebar-logo">Speak Bot</div><div class="sidebar-menu">'
    for href, key, icon, label in items:
        cls = "active" if key == active else ""
        html += f'<a href="{href}" class="{cls}"><span class="icon">{icon}</span> {label}</a>'
    html += "</div>"
    html += '<div class="sidebar-footer"><a href="/admin/logout">&#128274; Chiqish</a></div>'
    html += "</div>"
    return html


def layout(active, body):
    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin Panel — Speak Bot</title>
<style>{BASE_CSS}</style>
</head>
<body>
{sidebar_html(active)}
<div class="main">{body}</div>
</body>
</html>"""


# ===== LOGIN =====
LOGIN_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kirish — Admin Panel</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', sans-serif; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
.login-card { background: white; border-radius: 18px; box-shadow: 0 20px 60px rgba(0,0,0,0.25); width: 100%; max-width: 400px; padding: 38px 32px; }
.login-logo { text-align: center; margin-bottom: 24px; }
.login-logo .icon { display: inline-flex; width: 64px; height: 64px; border-radius: 18px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 8px 24px rgba(102,126,234,0.35); }
.login-title { text-align: center; font-size: 22px; font-weight: 700; color: #1c1c1e; margin-bottom: 6px; }
.login-sub { text-align: center; font-size: 14px; color: #8e8e93; margin-bottom: 28px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 12px; font-weight: 700; color: #555; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.3px; }
.form-group input { width: 100%; padding: 12px 14px; border: 1px solid #ddd; border-radius: 10px; font-size: 15px; transition: all 0.2s; }
.form-group input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.12); }
.btn-login { width: 100%; padding: 13px; border: none; border-radius: 11px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 15px; font-weight: 700; cursor: pointer; margin-top: 6px; transition: all 0.2s; }
.btn-login:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(102,126,234,0.35); }
.err { background: #fde2e2; color: #c0392b; padding: 10px 14px; border-radius: 10px; font-size: 13px; margin-bottom: 14px; font-weight: 600; }
</style>
</head>
<body>
<form method="POST" action="/admin/login" class="login-card">
    <div class="login-logo"><div class="icon">&#128274;</div></div>
    <div class="login-title">Admin Panel</div>
    <div class="login-sub">Davom etish uchun tizimga kiring</div>
    $error
    <div class="form-group">
        <label>Login</label>
        <input type="text" name="username" required autofocus>
    </div>
    <div class="form-group">
        <label>Parol</label>
        <input type="password" name="password" required>
    </div>
    <button class="btn-login" type="submit">Kirish</button>
</form>
</body>
</html>""")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if _is_authed(request):
        return RedirectResponse(url="/admin/", status_code=303)
    return LOGIN_TEMPLATE.substitute(error="")


@app.post("/login", response_class=HTMLResponse)
def login_submit(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        resp = RedirectResponse(url="/admin/", status_code=303)
        resp.set_cookie(
            COOKIE_NAME,
            _session_token(),
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/",
        )
        return resp
    return LOGIN_TEMPLATE.substitute(
        error='<div class="err">Login yoki parol noto\'g\'ri</div>'
    )


@app.get("/logout")
def logout():
    resp = RedirectResponse(url="/admin/login", status_code=303)
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp


# ===== USERS =====
def format_date(date_str):
    try:
        dt = datetime.strptime(str(date_str), "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y, %H:%M")
    except Exception:
        return date_str or ""


@app.get("/", response_class=HTMLResponse)
def users_page():
    users = get_all_users()
    total = len(users)
    male = sum(1 for u in users if u["gender"] == "Erkak")
    female = sum(1 for u in users if u["gender"] == "Ayol")

    if not users:
        table = '<div class="empty">Hozircha foydalanuvchilar yo\'q</div>'
    else:
        rows = ""
        for i, u in enumerate(users, 1):
            gender_class = (
                "gender-male" if u["gender"] == "Erkak" else "gender-female"
            )
            photo = u.get("photo_url") or ""
            if photo:
                avatar = f'<div class="user-avatar"><img src="{_esc(photo)}" alt=""></div>'
            else:
                letter = (u["first_name"] or "?")[0].upper()
                avatar = f'<div class="user-avatar">{_esc(letter)}</div>'
            username = u.get("username") or ""
            username_display = (
                f'<div class="user-username">@{_esc(username)}</div>'
                if username
                else '<div class="user-username">username yo\'q</div>'
            )
            rows += f"""
            <tr>
                <td>{i}</td>
                <td>
                    <div class="user-info">
                        {avatar}
                        <div>
                            <div class="user-name">{_esc(u['first_name'])}</div>
                            {username_display}
                        </div>
                    </div>
                </td>
                <td>{_esc(u['phone'])}</td>
                <td class="{gender_class}">{_esc(u['gender'])}</td>
                <td>{format_date(u['created_at'])}</td>
                <td>
                    <button class="btn-delete" onclick="confirmDelete({u['telegram_id']})">O'chirish</button>
                </td>
            </tr>"""
        table = f"""
        <table>
            <tr><th>#</th><th>Foydalanuvchi</th><th>Telefon</th><th>Jins</th><th>Sana</th><th>Amal</th></tr>
            {rows}
        </table>"""

    body = f"""
<div class="page-header">
    <div class="page-title">Foydalanuvchilar</div>
</div>
<div class="stats">
    <div class="stat-card">
        <div class="number">{total}</div>
        <div class="label">Jami foydalanuvchilar</div>
    </div>
    <div class="stat-card male">
        <div class="number">{male}</div>
        <div class="label">Erkaklar</div>
    </div>
    <div class="stat-card female">
        <div class="number">{female}</div>
        <div class="label">Ayollar</div>
    </div>
</div>
<div class="card">
    <div class="card-header">Foydalanuvchilar ro'yxati</div>
    {table}
</div>

<div class="modal-overlay" id="deleteModal">
    <div class="modal" style="max-width: 400px; text-align: center;">
        <h3>O'chirishni tasdiqlang</h3>
        <p>Bu foydalanuvchini o'chirishni xohlaysizmi?</p>
        <div class="modal-buttons" style="justify-content: center;">
            <button class="btn-cancel" onclick="closeDel()">Bekor qilish</button>
            <a id="deleteLink" href="#" class="btn-confirm-del">O'chirish</a>
        </div>
    </div>
</div>
<script>
function confirmDelete(id) {{
    document.getElementById('deleteLink').href = '/admin/delete/' + id;
    document.getElementById('deleteModal').classList.add('active');
}}
function closeDel() {{ document.getElementById('deleteModal').classList.remove('active'); }}
document.getElementById('deleteModal').addEventListener('click', function(e) {{ if (e.target === this) closeDel(); }});
</script>
"""
    return layout("users", body)


@app.get("/delete/{telegram_id}")
def delete_user_route(telegram_id: int):
    delete_user(telegram_id)
    return RedirectResponse(url="/admin/", status_code=303)


# ===== TARIFFS =====
@app.get("/tariffs", response_class=HTMLResponse)
def tariffs_page():
    tariffs = get_all_tariffs(active_only=False)
    if not tariffs:
        table = '<div class="empty">Hozircha tariflar yo\'q. Yangi tarif qo\'shing.</div>'
    else:
        rows = ""
        for i, t in enumerate(tariffs, 1):
            status = (
                '<span class="badge badge-active">Faol</span>'
                if t["is_active"]
                else '<span class="badge badge-inactive">Faol emas</span>'
            )
            title_js = _esc(t["title"])
            desc_js = _esc(t.get("description") or "")
            rows += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{_esc(t['title'])}</strong></td>
                <td>{t['mock_count']} ta</td>
                <td>{format_price(t['price'])}</td>
                <td>{_esc(t.get('description') or '—')}</td>
                <td>{status}</td>
                <td>{t.get('sort_order', 0)}</td>
                <td>
                    <div class="actions">
                        <button class="btn-edit" onclick="openEdit({t['id']}, '{title_js}', {t['mock_count']}, {t['price']}, '{desc_js}', {t['is_active']}, {t.get('sort_order', 0)})">Tahrir</button>
                        <button class="btn-delete" onclick="confirmDelete({t['id']})">O'chirish</button>
                    </div>
                </td>
            </tr>"""
        table = f"""
        <table>
            <tr><th>#</th><th>Nomi</th><th>Mock</th><th>Narxi</th><th>Tavsif</th><th>Holat</th><th>Tartib</th><th>Amal</th></tr>
            {rows}
        </table>"""

    body = f"""
<div class="page-header">
    <div class="page-title">Tariflar</div>
    <button class="btn-primary" onclick="openAdd()">+ Yangi tarif</button>
</div>
<div class="card">
    <div class="card-header">Tariflar ro'yxati</div>
    {table}
</div>

<div class="modal-overlay" id="formModal">
    <div class="modal">
        <h3 id="formTitle">Yangi tarif</h3>
        <form id="tariffForm" method="POST" action="/admin/tariffs/save">
            <input type="hidden" name="tariff_id" id="fId" value="">
            <div class="form-group"><label>Tarif nomi</label><input type="text" name="title" id="fTitle" required placeholder="1 ta mock"></div>
            <div class="form-row">
                <div class="form-group"><label>Mock soni</label><input type="number" name="mock_count" id="fMock" required min="1" value="1"></div>
                <div class="form-group"><label>Narxi (so'm)</label><input type="number" name="price" id="fPrice" required min="0" value="39000"></div>
            </div>
            <div class="form-group"><label>Tavsif</label><textarea name="description" id="fDesc" rows="2" placeholder="Ixtiyoriy"></textarea></div>
            <div class="form-row">
                <div class="form-group"><label>Tartib (sort)</label><input type="number" name="sort_order" id="fSort" value="0"></div>
                <div class="form-group"><label>Holat</label><select name="is_active" id="fActive"><option value="1">Faol</option><option value="0">Faol emas</option></select></div>
            </div>
            <div class="modal-buttons">
                <button type="button" class="btn-cancel" onclick="closeForm()">Bekor qilish</button>
                <button type="submit" class="btn-confirm">Saqlash</button>
            </div>
        </form>
    </div>
</div>
<div class="modal-overlay" id="deleteModal">
    <div class="modal" style="max-width: 400px; text-align: center;">
        <h3>O'chirishni tasdiqlang</h3>
        <p>Bu tarifni o'chirishni xohlaysizmi?</p>
        <div class="modal-buttons" style="justify-content: center;">
            <button class="btn-cancel" onclick="closeDelete()">Bekor qilish</button>
            <a id="deleteLink" href="#" class="btn-confirm-del">O'chirish</a>
        </div>
    </div>
</div>

<script>
function openAdd() {{
    document.getElementById('formTitle').textContent = "Yangi tarif";
    document.getElementById('fId').value = '';
    document.getElementById('fTitle').value = '';
    document.getElementById('fMock').value = '1';
    document.getElementById('fPrice').value = '39000';
    document.getElementById('fDesc').value = '';
    document.getElementById('fSort').value = '0';
    document.getElementById('fActive').value = '1';
    document.getElementById('formModal').classList.add('active');
}}
function openEdit(id, title, mock, price, desc, active, sort) {{
    document.getElementById('formTitle').textContent = "Tarifni tahrirlash";
    document.getElementById('fId').value = id;
    document.getElementById('fTitle').value = title;
    document.getElementById('fMock').value = mock;
    document.getElementById('fPrice').value = price;
    document.getElementById('fDesc').value = desc;
    document.getElementById('fSort').value = sort;
    document.getElementById('fActive').value = active;
    document.getElementById('formModal').classList.add('active');
}}
function closeForm() {{ document.getElementById('formModal').classList.remove('active'); }}
function confirmDelete(id) {{
    document.getElementById('deleteLink').href = '/admin/tariffs/delete/' + id;
    document.getElementById('deleteModal').classList.add('active');
}}
function closeDelete() {{ document.getElementById('deleteModal').classList.remove('active'); }}
document.getElementById('formModal').addEventListener('click', function(e) {{ if (e.target === this) closeForm(); }});
document.getElementById('deleteModal').addEventListener('click', function(e) {{ if (e.target === this) closeDelete(); }});
</script>
"""
    return layout("tariffs", body)


@app.post("/tariffs/save")
def tariffs_save(
    tariff_id: str = Form(""),
    title: str = Form(...),
    mock_count: int = Form(...),
    price: int = Form(...),
    description: str = Form(""),
    is_active: int = Form(1),
    sort_order: int = Form(0),
):
    if tariff_id and tariff_id.strip():
        update_tariff(
            int(tariff_id), title, mock_count, price, description, is_active, sort_order
        )
    else:
        add_tariff(title, mock_count, price, description, is_active, sort_order)
    return RedirectResponse(url="/admin/tariffs", status_code=303)


@app.get("/tariffs/delete/{tariff_id}")
def tariffs_delete(tariff_id: int):
    delete_tariff(tariff_id)
    return RedirectResponse(url="/admin/tariffs", status_code=303)


# ===== MOCK BERISH =====
LANG_META = {
    "arabic": {"flag": "🕌", "name": "Arabcha"},
    "turkish": {"flag": "🇹🇷", "name": "Turkcha"},
    "english": {"flag": "🇬🇧", "name": "Inglizcha"},
}


@app.get("/mocks", response_class=HTMLResponse)
def mocks_page():
    users = get_all_users_with_mocks()
    tariffs = get_all_tariffs(active_only=True)

    total_mocks = sum(
        sum(u["mocks"].values()) for u in users
    )
    active_holders = sum(1 for u in users if sum(u["mocks"].values()) > 0)

    if not users:
        table = '<div class="empty">Hozircha foydalanuvchilar yo\'q</div>'
    else:
        rows = ""
        for i, u in enumerate(users, 1):
            photo = u.get("photo_url") or ""
            if photo:
                avatar = f'<div class="user-avatar"><img src="{_esc(photo)}" alt=""></div>'
            else:
                letter = (u["first_name"] or "?")[0].upper()
                avatar = f'<div class="user-avatar">{_esc(letter)}</div>'
            username = u.get("username") or ""
            username_display = (
                f'<div class="user-username">@{_esc(username)}</div>'
                if username
                else ""
            )
            mocks = u["mocks"]
            pills = ""
            for lang in LANGUAGES:
                meta = LANG_META[lang]
                cnt = mocks.get(lang, 0)
                zero_cls = " zero" if cnt == 0 else ""
                pills += f'<span class="lang-pill{zero_cls}"><span class="flag">{meta["flag"]}</span> <span class="count">{cnt}</span></span>'

            first_name_js = _esc(u["first_name"] or "").replace("`", "")
            username_js = _esc(username).replace("`", "")
            rows += f"""
            <tr>
                <td>{i}</td>
                <td>
                    <div class="user-info">
                        {avatar}
                        <div>
                            <div class="user-name">{_esc(u['first_name'])}</div>
                            {username_display}
                        </div>
                    </div>
                </td>
                <td>{_esc(u['phone'])}</td>
                <td><div class="lang-cell">{pills}</div></td>
                <td>
                    <div class="actions">
                        <button class="btn-give" onclick="openGive({u['telegram_id']}, '{first_name_js}', '{username_js}', {mocks['arabic']}, {mocks['turkish']}, {mocks['english']})">+ Mock berish</button>
                        <button class="btn-remove" onclick="openRemove({u['telegram_id']}, '{first_name_js}', {mocks['arabic']}, {mocks['turkish']}, {mocks['english']})">− Olib tashlash</button>
                    </div>
                </td>
            </tr>"""
        table = f"""
        <table>
            <tr><th>#</th><th>Foydalanuvchi</th><th>Telefon</th><th>Mocklar</th><th>Amal</th></tr>
            {rows}
        </table>"""

    # Tariff options JS
    tariff_options = ""
    for t in tariffs:
        tariff_options += f'<option value="{t["mock_count"]}">{_esc(t["title"])} (+{t["mock_count"]} mock)</option>'
    tariff_options_html = tariff_options if tariff_options else '<option value="0">Tarif topilmadi</option>'

    body = f"""
<div class="page-header">
    <div class="page-title">Mock berish</div>
</div>
<div class="stats">
    <div class="stat-card mocks">
        <div class="number">{total_mocks}</div>
        <div class="label">Jami berilgan mocklar</div>
    </div>
    <div class="stat-card">
        <div class="number">{active_holders}</div>
        <div class="label">Mocklari bor foydalanuvchilar</div>
    </div>
    <div class="stat-card">
        <div class="number">{len(users)}</div>
        <div class="label">Jami foydalanuvchilar</div>
    </div>
</div>
<div class="card">
    <div class="card-header">Foydalanuvchilar va mocklari</div>
    {table}
</div>

<!-- GIVE MODAL -->
<div class="modal-overlay" id="giveModal">
    <div class="modal">
        <h3>+ Mock berish</h3>
        <p id="giveUserInfo" style="margin-bottom:12px;"></p>
        <form method="POST" action="/admin/mocks/give">
            <input type="hidden" name="telegram_id" id="giveTid">
            <div class="form-group">
                <label>Til</label>
                <select name="language" id="giveLang" onchange="updateGiveCurrent()">
                    <option value="arabic">🕌 Arabcha</option>
                    <option value="turkish">🇹🇷 Turkcha</option>
                    <option value="english">🇬🇧 Inglizcha</option>
                </select>
            </div>
            <div class="lang-info-row">Joriy balans: <strong id="giveCurrent">0</strong> mock</div>

            <div class="modal-tabs">
                <button type="button" class="modal-tab active" onclick="switchGiveTab('tariff')">Tarif bo'yicha</button>
                <button type="button" class="modal-tab" onclick="switchGiveTab('manual')">Qo'lda</button>
            </div>

            <div class="modal-tab-content active" id="giveTabTariff">
                <div class="form-group">
                    <label>Tarifni tanlang</label>
                    <select name="tariff_count" id="giveTariff">
                        {tariff_options_html}
                    </select>
                </div>
            </div>

            <div class="modal-tab-content" id="giveTabManual">
                <div class="form-group">
                    <label>Mock soni</label>
                    <input type="number" name="manual_count" id="giveManual" min="1" value="1">
                </div>
            </div>

            <input type="hidden" name="mode" id="giveMode" value="tariff">

            <div class="modal-buttons">
                <button type="button" class="btn-cancel" onclick="closeGive()">Bekor qilish</button>
                <button type="submit" class="btn-confirm-green">Berish</button>
            </div>
        </form>
    </div>
</div>

<!-- REMOVE MODAL -->
<div class="modal-overlay" id="removeModal">
    <div class="modal">
        <h3>− Mock olib tashlash</h3>
        <p id="removeUserInfo" style="margin-bottom:12px;"></p>
        <form method="POST" action="/admin/mocks/remove">
            <input type="hidden" name="telegram_id" id="removeTid">
            <div class="form-group">
                <label>Til</label>
                <select name="language" id="removeLang" onchange="updateRemoveCurrent()">
                    <option value="arabic">🕌 Arabcha</option>
                    <option value="turkish">🇹🇷 Turkcha</option>
                    <option value="english">🇬🇧 Inglizcha</option>
                </select>
            </div>
            <div class="lang-info-row">Joriy balans: <strong id="removeCurrent">0</strong> mock</div>
            <div class="form-group">
                <label>Olib tashlash soni</label>
                <input type="number" name="count" id="removeCount" min="1" value="1">
            </div>
            <div class="form-group">
                <label style="color:#999">Yoki to'liq nolga tushirish</label>
                <label style="font-weight:500; font-size:13px; text-transform:none; color:#555; cursor:pointer;">
                    <input type="checkbox" name="zero_out" id="removeZero" style="width:auto; margin-right:6px;"> Balansni 0 qilish
                </label>
            </div>
            <div class="modal-buttons">
                <button type="button" class="btn-cancel" onclick="closeRemove()">Bekor qilish</button>
                <button type="submit" class="btn-confirm-orange">Olib tashlash</button>
            </div>
        </form>
    </div>
</div>

<script>
var giveUser = {{ tid: 0, balances: {{ arabic: 0, turkish: 0, english: 0 }} }};
var removeUser = {{ tid: 0, balances: {{ arabic: 0, turkish: 0, english: 0 }} }};

function openGive(tid, firstName, username, aMock, tMock, eMock) {{
    giveUser.tid = tid;
    giveUser.balances = {{ arabic: aMock, turkish: tMock, english: eMock }};
    document.getElementById('giveTid').value = tid;
    var u = username ? ' (@' + username + ')' : '';
    document.getElementById('giveUserInfo').innerHTML = '<strong>' + firstName + '</strong>' + u;
    document.getElementById('giveLang').value = 'english';
    updateGiveCurrent();
    switchGiveTab('tariff');
    document.getElementById('giveModal').classList.add('active');
}}
function closeGive() {{ document.getElementById('giveModal').classList.remove('active'); }}
function updateGiveCurrent() {{
    var lang = document.getElementById('giveLang').value;
    document.getElementById('giveCurrent').textContent = giveUser.balances[lang] || 0;
}}
function switchGiveTab(tab) {{
    document.getElementById('giveMode').value = tab;
    var tabs = document.querySelectorAll('#giveModal .modal-tab');
    tabs[0].classList.toggle('active', tab === 'tariff');
    tabs[1].classList.toggle('active', tab === 'manual');
    document.getElementById('giveTabTariff').classList.toggle('active', tab === 'tariff');
    document.getElementById('giveTabManual').classList.toggle('active', tab === 'manual');
}}

function openRemove(tid, firstName, aMock, tMock, eMock) {{
    removeUser.tid = tid;
    removeUser.balances = {{ arabic: aMock, turkish: tMock, english: eMock }};
    document.getElementById('removeTid').value = tid;
    document.getElementById('removeUserInfo').innerHTML = '<strong>' + firstName + '</strong>';
    document.getElementById('removeLang').value = 'english';
    document.getElementById('removeCount').value = 1;
    document.getElementById('removeZero').checked = false;
    updateRemoveCurrent();
    document.getElementById('removeModal').classList.add('active');
}}
function closeRemove() {{ document.getElementById('removeModal').classList.remove('active'); }}
function updateRemoveCurrent() {{
    var lang = document.getElementById('removeLang').value;
    document.getElementById('removeCurrent').textContent = removeUser.balances[lang] || 0;
}}

document.getElementById('giveModal').addEventListener('click', function(e) {{ if (e.target === this) closeGive(); }});
document.getElementById('removeModal').addEventListener('click', function(e) {{ if (e.target === this) closeRemove(); }});
</script>
"""
    return layout("mocks", body)


@app.post("/mocks/give")
def mocks_give(
    telegram_id: int = Form(...),
    language: str = Form(...),
    mode: str = Form("tariff"),
    tariff_count: int = Form(0),
    manual_count: int = Form(0),
):
    if language not in LANGUAGES:
        return RedirectResponse(url="/admin/mocks", status_code=303)
    delta = tariff_count if mode == "tariff" else manual_count
    delta = max(0, int(delta))
    if delta > 0:
        adjust_user_mocks(telegram_id, language, delta)
    return RedirectResponse(url="/admin/mocks", status_code=303)


@app.post("/mocks/remove")
def mocks_remove(
    telegram_id: int = Form(...),
    language: str = Form(...),
    count: int = Form(0),
    zero_out: str = Form(""),
):
    if language not in LANGUAGES:
        return RedirectResponse(url="/admin/mocks", status_code=303)
    if zero_out:
        set_user_mocks(telegram_id, language, 0)
    else:
        delta = -abs(int(count or 0))
        if delta != 0:
            adjust_user_mocks(telegram_id, language, delta)
    return RedirectResponse(url="/admin/mocks", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3000)
