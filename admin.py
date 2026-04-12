from string import Template
from datetime import datetime
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from database import (
    get_all_users,
    get_user_count,
    delete_user,
    get_all_tariffs,
    get_tariff,
    add_tariff,
    update_tariff,
    delete_tariff,
)

app = FastAPI()


def format_price(price):
    try:
        return f"{int(price):,}".replace(",", " ") + " so'm"
    except Exception:
        return str(price)

HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; display: flex; height: 100vh; }

        /* SIDEBAR */
        .sidebar {
            width: 240px; background: #1e1e2d; color: white; padding: 0;
            display: flex; flex-direction: column; flex-shrink: 0;
        }
        .sidebar-logo {
            padding: 24px 20px; border-bottom: 1px solid #2d2d44;
            font-size: 20px; font-weight: bold; text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .sidebar-menu { padding: 12px 0; flex: 1; }
        .sidebar-menu a {
            display: flex; align-items: center; gap: 12px;
            padding: 14px 24px; color: #8a8aa0; text-decoration: none;
            font-size: 15px; transition: all 0.2s;
        }
        .sidebar-menu a:hover { background: #2d2d44; color: white; }
        .sidebar-menu a.active { background: #2d2d44; color: white; border-left: 3px solid #667eea; }
        .sidebar-menu a .icon { font-size: 18px; width: 24px; text-align: center; }

        /* MAIN CONTENT */
        .main { flex: 1; overflow-y: auto; padding: 30px; }

        /* STATS */
        .stats { display: flex; gap: 20px; margin-bottom: 30px; }
        .stat-card {
            background: white; padding: 24px 32px; border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06); flex: 1; text-align: center;
        }
        .stat-card .number { font-size: 40px; font-weight: bold; color: #667eea; }
        .stat-card .label { color: #999; margin-top: 6px; font-size: 14px; }
        .stat-card.male .number { color: #4a90d9; }
        .stat-card.female .number { color: #e91e8c; }

        /* TABLE */
        .card {
            background: white; border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06); overflow: hidden;
        }
        .card-header {
            padding: 18px 24px; border-bottom: 1px solid #f0f0f0;
            font-size: 18px; font-weight: 600; color: #333;
        }
        table { width: 100%; border-collapse: collapse; }
        th {
            background: #f8f9ff; color: #667eea; padding: 14px 16px;
            text-align: left; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;
        }
        td { padding: 14px 16px; border-bottom: 1px solid #f5f5f5; vertical-align: middle; }
        tr:hover td { background: #fafbff; }

        .user-info { display: flex; align-items: center; gap: 12px; }
        .user-avatar {
            width: 42px; height: 42px; border-radius: 50%; object-fit: cover;
            background: #e8eaff; display: flex; align-items: center; justify-content: center;
            color: #667eea; font-weight: bold; font-size: 16px; flex-shrink: 0;
        }
        .user-avatar img { width: 42px; height: 42px; border-radius: 50%; object-fit: cover; }
        .user-name { font-weight: 600; color: #333; }
        .user-username { font-size: 13px; color: #999; }

        .gender-male { color: #4a90d9; font-weight: 600; }
        .gender-female { color: #e91e8c; font-weight: 600; }

        .btn-delete {
            background: #ff4757; color: white; border: none; padding: 8px 16px;
            border-radius: 8px; cursor: pointer; font-size: 13px; transition: all 0.2s;
        }
        .btn-delete:hover { background: #e8384f; transform: scale(1.05); }

        .empty { text-align: center; padding: 60px; color: #999; font-size: 16px; }

        /* Modal */
        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5); z-index: 100; align-items: center; justify-content: center;
        }
        .modal-overlay.active { display: flex; }
        .modal {
            background: white; border-radius: 16px; padding: 32px; width: 400px;
            text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        }
        .modal h3 { margin-bottom: 12px; color: #333; }
        .modal p { color: #777; margin-bottom: 24px; }
        .modal-buttons { display: flex; gap: 12px; justify-content: center; }
        .modal-buttons button {
            padding: 10px 28px; border-radius: 8px; border: none;
            cursor: pointer; font-size: 14px; font-weight: 600;
        }
        .btn-cancel { background: #f0f0f0; color: #555; }
        .btn-confirm { background: #ff4757; color: white; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-logo">Speak Bot</div>
        <div class="sidebar-menu">
            <a href="/" class="active">
                <span class="icon">&#128101;</span> Foydalanuvchilar
            </a>
            <a href="/tariffs">
                <span class="icon">&#11088;</span> Tariflar
            </a>
        </div>
    </div>

    <div class="main">
        <div class="stats">
            <div class="stat-card">
                <div class="number">$total</div>
                <div class="label">Jami foydalanuvchilar</div>
            </div>
            <div class="stat-card male">
                <div class="number">$male</div>
                <div class="label">Erkaklar</div>
            </div>
            <div class="stat-card female">
                <div class="number">$female</div>
                <div class="label">Ayollar</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">Foydalanuvchilar ro'yxati</div>
            $table
        </div>
    </div>

    <div class="modal-overlay" id="deleteModal">
        <div class="modal">
            <h3>O'chirishni tasdiqlang</h3>
            <p>Bu foydalanuvchini o'chirishni xohlaysizmi?</p>
            <div class="modal-buttons">
                <button class="btn-cancel" onclick="closeModal()">Bekor qilish</button>
                <a id="deleteLink" href="#"><button class="btn-confirm">O'chirish</button></a>
            </div>
        </div>
    </div>

    <script>
        function confirmDelete(telegramId) {
            document.getElementById('deleteModal').classList.add('active');
            document.getElementById('deleteLink').href = '/delete/' + telegramId;
        }
        function closeModal() {
            document.getElementById('deleteModal').classList.remove('active');
        }
        document.getElementById('deleteModal').addEventListener('click', function(e) {
            if (e.target === this) closeModal();
        });
    </script>
</body>
</html>
""")


def format_date(date_str):
    try:
        dt = datetime.strptime(str(date_str), "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y, %H:%M")
    except Exception:
        return date_str or ""


@app.get("/", response_class=HTMLResponse)
def admin_page():
    users = get_all_users()
    total = len(users)
    male = sum(1 for u in users if u["gender"] == "Erkak")
    female = sum(1 for u in users if u["gender"] == "Ayol")

    if not users:
        table = '<div class="empty">Hozircha foydalanuvchilar yo\'q</div>'
    else:
        rows = ""
        for i, u in enumerate(users, 1):
            gender_class = "gender-male" if u["gender"] == "Erkak" else "gender-female"

            # Avatar: rasm bor bo'lsa ko'rsat, bo'lmasa harf
            photo = u.get("photo_url") or ""
            if photo:
                avatar = f'<div class="user-avatar"><img src="{photo}" alt=""></div>'
            else:
                letter = (u["first_name"] or "?")[0].upper()
                avatar = f'<div class="user-avatar">{letter}</div>'

            username = u.get("username") or ""
            username_display = f'<div class="user-username">@{username}</div>' if username else '<div class="user-username">username yo\'q</div>'

            rows += f"""
            <tr>
                <td>{i}</td>
                <td>
                    <div class="user-info">
                        {avatar}
                        <div>
                            <div class="user-name">{u['first_name']}</div>
                            {username_display}
                        </div>
                    </div>
                </td>
                <td>{u['phone']}</td>
                <td class="{gender_class}">{u['gender']}</td>
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

    return HTML_TEMPLATE.substitute(total=total, male=male, female=female, table=table)


@app.get("/delete/{telegram_id}")
def delete_user_route(telegram_id: int):
    delete_user(telegram_id)
    return RedirectResponse(url="/", status_code=303)


# ===== TARIFFS =====

TARIFFS_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tariflar — Admin Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; display: flex; min-height: 100vh; }
        .sidebar { width: 240px; background: #1e1e2d; color: white; display: flex; flex-direction: column; flex-shrink: 0; }
        .sidebar-logo { padding: 24px 20px; border-bottom: 1px solid #2d2d44; font-size: 20px; font-weight: bold; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .sidebar-menu { padding: 12px 0; flex: 1; }
        .sidebar-menu a { display: flex; align-items: center; gap: 12px; padding: 14px 24px; color: #8a8aa0; text-decoration: none; font-size: 15px; transition: all 0.2s; }
        .sidebar-menu a:hover { background: #2d2d44; color: white; }
        .sidebar-menu a.active { background: #2d2d44; color: white; border-left: 3px solid #667eea; }
        .sidebar-menu a .icon { font-size: 18px; width: 24px; text-align: center; }
        .main { flex: 1; overflow-y: auto; padding: 30px; }

        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
        .page-title { font-size: 26px; font-weight: 700; color: #333; }
        .btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 10px 20px; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }
        .btn-primary:hover { opacity: 0.9; }

        .card { background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); overflow: hidden; }
        .card-header { padding: 18px 24px; border-bottom: 1px solid #f0f0f0; font-size: 18px; font-weight: 600; color: #333; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #f8f9ff; color: #667eea; padding: 14px 16px; text-align: left; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
        td { padding: 14px 16px; border-bottom: 1px solid #f5f5f5; vertical-align: middle; }
        tr:hover td { background: #fafbff; }

        .badge-active { background: #e0fce8; color: #1f9a43; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .badge-inactive { background: #fde2e2; color: #c0392b; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }

        .actions { display: flex; gap: 8px; }
        .btn-edit { background: #4a90d9; color: white; border: none; padding: 8px 14px; border-radius: 8px; cursor: pointer; font-size: 13px; text-decoration: none; }
        .btn-edit:hover { background: #3d7dc1; }
        .btn-delete { background: #ff4757; color: white; border: none; padding: 8px 14px; border-radius: 8px; cursor: pointer; font-size: 13px; }
        .btn-delete:hover { background: #e8384f; }

        .empty { text-align: center; padding: 60px; color: #999; font-size: 16px; }

        .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 100; align-items: center; justify-content: center; padding: 20px; }
        .modal-overlay.active { display: flex; }
        .modal { background: white; border-radius: 16px; padding: 28px; width: 100%; max-width: 460px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); max-height: 90vh; overflow-y: auto; }
        .modal h3 { margin-bottom: 16px; color: #333; font-size: 20px; }
        .form-group { margin-bottom: 14px; }
        .form-group label { display: block; font-size: 13px; font-weight: 600; color: #555; margin-bottom: 6px; }
        .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; font-family: inherit; }
        .form-group input:focus, .form-group textarea:focus, .form-group select:focus { outline: none; border-color: #667eea; }
        .form-row { display: flex; gap: 12px; }
        .form-row .form-group { flex: 1; }
        .modal-buttons { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
        .modal-buttons button, .modal-buttons a { padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; text-decoration: none; }
        .btn-cancel { background: #f0f0f0; color: #555; }
        .btn-confirm { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .btn-confirm-del { background: #ff4757; color: white; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-logo">Speak Bot</div>
        <div class="sidebar-menu">
            <a href="/"><span class="icon">&#128101;</span> Foydalanuvchilar</a>
            <a href="/tariffs" class="active"><span class="icon">&#11088;</span> Tariflar</a>
        </div>
    </div>

    <div class="main">
        <div class="page-header">
            <div class="page-title">Tariflar</div>
            <button class="btn-primary" onclick="openAdd()">+ Yangi tarif</button>
        </div>

        <div class="card">
            <div class="card-header">Tariflar ro'yxati</div>
            $table
        </div>
    </div>

    <!-- Add/Edit modal -->
    <div class="modal-overlay" id="formModal">
        <div class="modal">
            <h3 id="formTitle">Yangi tarif</h3>
            <form id="tariffForm" method="POST" action="/tariffs/save">
                <input type="hidden" name="tariff_id" id="fId" value="">
                <div class="form-group">
                    <label>Tarif nomi</label>
                    <input type="text" name="title" id="fTitle" required placeholder="1 ta mock">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Mock soni</label>
                        <input type="number" name="mock_count" id="fMock" required min="1" value="1">
                    </div>
                    <div class="form-group">
                        <label>Narxi (so'm)</label>
                        <input type="number" name="price" id="fPrice" required min="0" value="39000">
                    </div>
                </div>
                <div class="form-group">
                    <label>Tavsif</label>
                    <textarea name="description" id="fDesc" rows="2" placeholder="Ixtiyoriy"></textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Tartib (sort)</label>
                        <input type="number" name="sort_order" id="fSort" value="0">
                    </div>
                    <div class="form-group">
                        <label>Holat</label>
                        <select name="is_active" id="fActive">
                            <option value="1">Faol</option>
                            <option value="0">Faol emas</option>
                        </select>
                    </div>
                </div>
                <div class="modal-buttons">
                    <button type="button" class="btn-cancel" onclick="closeForm()">Bekor qilish</button>
                    <button type="submit" class="btn-confirm">Saqlash</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Delete modal -->
    <div class="modal-overlay" id="deleteModal">
        <div class="modal" style="max-width: 400px; text-align: center;">
            <h3>O'chirishni tasdiqlang</h3>
            <p style="color: #777; margin-bottom: 20px;">Bu tarifni o'chirishni xohlaysizmi?</p>
            <div class="modal-buttons" style="justify-content: center;">
                <button class="btn-cancel" onclick="closeDelete()">Bekor qilish</button>
                <a id="deleteLink" href="#" class="btn-confirm-del">O'chirish</a>
            </div>
        </div>
    </div>

    <script>
        function openAdd() {
            document.getElementById('formTitle').textContent = "Yangi tarif";
            document.getElementById('fId').value = '';
            document.getElementById('fTitle').value = '';
            document.getElementById('fMock').value = '1';
            document.getElementById('fPrice').value = '39000';
            document.getElementById('fDesc').value = '';
            document.getElementById('fSort').value = '0';
            document.getElementById('fActive').value = '1';
            document.getElementById('formModal').classList.add('active');
        }
        function openEdit(id, title, mock, price, desc, active, sort) {
            document.getElementById('formTitle').textContent = "Tarifni tahrirlash";
            document.getElementById('fId').value = id;
            document.getElementById('fTitle').value = title;
            document.getElementById('fMock').value = mock;
            document.getElementById('fPrice').value = price;
            document.getElementById('fDesc').value = desc;
            document.getElementById('fSort').value = sort;
            document.getElementById('fActive').value = active;
            document.getElementById('formModal').classList.add('active');
        }
        function closeForm() { document.getElementById('formModal').classList.remove('active'); }

        function confirmDelete(id) {
            document.getElementById('deleteLink').href = '/tariffs/delete/' + id;
            document.getElementById('deleteModal').classList.add('active');
        }
        function closeDelete() { document.getElementById('deleteModal').classList.remove('active'); }

        document.getElementById('formModal').addEventListener('click', function(e) { if (e.target === this) closeForm(); });
        document.getElementById('deleteModal').addEventListener('click', function(e) { if (e.target === this) closeDelete(); });
    </script>
</body>
</html>
""")


def _esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


@app.get("/tariffs", response_class=HTMLResponse)
def tariffs_page():
    tariffs = get_all_tariffs(active_only=False)
    if not tariffs:
        table = '<div class="empty">Hozircha tariflar yo\'q. Yangi tarif qo\'shing.</div>'
    else:
        rows = ""
        for i, t in enumerate(tariffs, 1):
            status = '<span class="badge-active">Faol</span>' if t["is_active"] else '<span class="badge-inactive">Faol emas</span>'
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
    return TARIFFS_TEMPLATE.substitute(table=table)


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
        update_tariff(int(tariff_id), title, mock_count, price, description, is_active, sort_order)
    else:
        add_tariff(title, mock_count, price, description, is_active, sort_order)
    return RedirectResponse(url="/tariffs", status_code=303)


@app.get("/tariffs/delete/{tariff_id}")
def tariffs_delete(tariff_id: int):
    delete_tariff(tariff_id)
    return RedirectResponse(url="/tariffs", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
