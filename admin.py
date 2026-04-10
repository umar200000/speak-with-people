from string import Template
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from database import get_all_users, get_user_count, delete_user

app = FastAPI()

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
        </div>
    </div>

    <div class="main">
    <h1>bu ci/cd ni test qilish</h1>
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
