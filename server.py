# -*- coding: utf-8 -*-
"""
server.py — NexcoreIA SAS · Servidor web
Sirve los archivos HTML estáticos, recibe formulario de contacto
y guarda los datos en SQLite para verlos desde el panel admin.
"""
from flask import Flask, request, jsonify, send_from_directory, render_template_string
import sqlite3, os, hashlib, secrets
from datetime import datetime
from pathlib import Path

app = Flask(__name__, static_folder='.')
BASE = Path(__file__).parent
DB   = BASE / 'contactos.db'

# ─── Contraseña del panel admin (cambia esto) ───────────────
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'NexcoreAdmin2026')


# ══════════════════════════════════════════════════════════════
# BASE DE DATOS
# ══════════════════════════════════════════════════════════════
def init_db():
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS contactos(
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha     TEXT DEFAULT CURRENT_TIMESTAMP,
            nombre    TEXT,
            empresa   TEXT,
            email     TEXT,
            telefono  TEXT,
            necesidad TEXT,
            mensaje   TEXT,
            ip        TEXT,
            leido     INTEGER DEFAULT 0
        )
    """)
    c.commit()
    c.close()

init_db()


# ══════════════════════════════════════════════════════════════
# RUTAS HTML ESTÁTICAS
# ══════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<page>')
def pagina(page):
    # Rutas limpias sin .html
    mapping = {
        'como-funciona': 'como-funciona.html',
        'servicios':     'servicios.html',
        'calculadora':   'calculadora.html',
        'precios':       'precios.html',
        'normativa':     'normativa.html',
        'contacto':      'contacto.html',
    }
    fname = mapping.get(page, page if page.endswith('.html') else None)
    if fname and (BASE / fname).exists():
        return send_from_directory('.', fname)
    return send_from_directory('.', 'index.html')


# ══════════════════════════════════════════════════════════════
# API — FORMULARIO DE CONTACTO
# ══════════════════════════════════════════════════════════════
@app.route('/api/contacto', methods=['POST'])
def recibir_contacto():
    data = request.get_json(silent=True) or request.form
    nombre   = str(data.get('nombre',   '')).strip()[:100]
    empresa  = str(data.get('empresa',  '')).strip()[:100]
    email    = str(data.get('email',    '')).strip()[:100]
    telefono = str(data.get('telefono', '')).strip()[:30]
    necesidad= str(data.get('necesidad','general')).strip()[:80]
    mensaje  = str(data.get('mensaje',  '')).strip()[:800]
    ip       = request.remote_addr or ''

    if not nombre or not email:
        return jsonify({'ok': False, 'error': 'Nombre y email son requeridos'}), 400

    c = sqlite3.connect(DB)
    c.execute("""
        INSERT INTO contactos(nombre,empresa,email,telefono,necesidad,mensaje,ip)
        VALUES(?,?,?,?,?,?,?)
    """, (nombre, empresa, email, telefono, necesidad, mensaje, ip))
    c.commit()
    c.close()

    return jsonify({'ok': True, 'mensaje': '✅ Mensaje recibido. Le contactamos en menos de 24 horas.'})


# ══════════════════════════════════════════════════════════════
# PANEL ADMIN — VER CONTACTOS
# ══════════════════════════════════════════════════════════════
ADMIN_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin Contactos · NexcoreIA SAS</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#060D1F;color:#E8F0FF;font-family:"DM Sans",sans-serif;min-height:100vh}
.header{background:#0A1428;border-bottom:1px solid rgba(11,92,255,.25);
  padding:16px 5%;display:flex;align-items:center;justify-content:space-between}
.header h1{font-size:18px;font-weight:700;
  background:linear-gradient(90deg,#4A9DFF,#FF8C35);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text}
.brand{font-size:12px;color:#3A5A80}
.wrap{max-width:1200px;margin:0 auto;padding:32px 5%}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:28px}
.stat{background:#0A1428;border:1px solid rgba(11,92,255,.2);border-radius:12px;
  padding:20px;text-align:center}
.stat-n{font-size:34px;font-weight:800;
  background:linear-gradient(90deg,#4A9DFF,#00E5A0);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text}
.stat-l{font-size:12px;color:#7A9ABF;margin-top:5px}
.actions{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;align-items:center}
.btn{padding:8px 18px;border-radius:8px;font-size:13px;font-weight:600;
  cursor:pointer;border:none;text-decoration:none;display:inline-block;transition:all .2s}
.btn-primary{background:linear-gradient(135deg,#0B5CFF,#0040CC);color:#fff}
.btn-outline{background:rgba(11,92,255,.1);color:#4A9DFF;border:1px solid rgba(11,92,255,.3)}
.btn-danger{background:rgba(255,60,60,.1);color:#FF6B6B;border:1px solid rgba(255,60,60,.3)}
.search-inp{background:rgba(11,92,255,.06);border:1px solid rgba(11,92,255,.2);
  border-radius:8px;padding:8px 14px;color:#E8F0FF;font-size:13px;outline:none;
  transition:border-color .2s;min-width:220px}
.search-inp:focus{border-color:#0B5CFF}
table{width:100%;border-collapse:collapse;background:#0A1428;
  border-radius:14px;overflow:hidden;border:1px solid rgba(11,92,255,.15)}
th{padding:12px 16px;text-align:left;font-size:11.5px;font-weight:700;
  text-transform:uppercase;letter-spacing:1px;color:#7A9ABF;
  border-bottom:1px solid rgba(11,92,255,.15);background:#060D1F}
td{padding:12px 16px;font-size:13.5px;border-bottom:1px solid rgba(11,92,255,.08);
  vertical-align:top;max-width:220px;word-break:break-word}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(11,92,255,.05)}
.badge-new{background:rgba(0,229,160,.15);color:#00E5A0;border:1px solid rgba(0,229,160,.3);
  font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px}
.badge-read{background:rgba(58,90,128,.1);color:#7A9ABF;border:1px solid rgba(58,90,128,.2);
  font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px}
.msg-cell{font-size:12.5px;color:#7A9ABF;max-width:280px}
.fecha{font-family:"DM Mono",monospace;font-size:12px;color:#7A9ABF}
.email-link{color:#00CFFF;text-decoration:none}
.email-link:hover{text-decoration:underline}
.mark-btn{background:rgba(11,92,255,.1);border:1px solid rgba(11,92,255,.25);
  color:#4A9DFF;border-radius:6px;padding:3px 10px;font-size:11px;cursor:pointer;
  transition:all .2s}
.mark-btn:hover{background:rgba(11,92,255,.2)}
.empty{text-align:center;padding:60px 20px;color:#3A5A80;font-size:15px}
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;
  background:#060D1F}
.login-box{background:#0A1428;border:1px solid rgba(11,92,255,.2);border-radius:16px;
  padding:40px;width:360px;text-align:center}
.login-box h2{font-size:20px;font-weight:700;margin-bottom:8px}
.login-box p{color:#7A9ABF;font-size:14px;margin-bottom:24px}
.login-inp{width:100%;background:rgba(11,92,255,.06);border:1px solid rgba(11,92,255,.2);
  border-radius:8px;padding:12px 14px;color:#E8F0FF;font-size:14px;
  outline:none;margin-bottom:12px;font-family:"DM Sans",sans-serif}
.login-inp:focus{border-color:#0B5CFF}
.err{color:#FF6B6B;font-size:13px;margin-top:8px}
.tag-n{background:rgba(255,140,53,.12);color:#FF8C35;border:1px solid rgba(255,140,53,.25);
  font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;white-space:nowrap}
</style>
</head>
<body>
{% if not autenticado %}
<div class="login-wrap">
  <div class="login-box">
    <h2>🔐 Panel Admin</h2>
    <p>NexcoreIA SAS — Contactos</p>
    <form method="POST" action="/admin">
      <input class="login-inp" type="password" name="pass" placeholder="Contraseña admin" autofocus>
      <button type="submit" class="btn btn-primary" style="width:100%;padding:12px">Ingresar</button>
      {% if error %}<div class="err">❌ Contraseña incorrecta</div>{% endif %}
    </form>
  </div>
</div>

{% else %}
<div class="header">
  <h1>📋 Panel de Contactos · NexcoreIA SAS</h1>
  <div class="brand">{{ total }} registros · <a href="/admin/logout" style="color:#4A9DFF">Salir</a></div>
</div>
<div class="wrap">
  <div class="stats">
    <div class="stat"><div class="stat-n">{{ total }}</div><div class="stat-l">Total contactos</div></div>
    <div class="stat"><div class="stat-n" style="background:linear-gradient(90deg,#00E5A0,#4A9DFF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{{ no_leidos }}</div><div class="stat-l">Sin leer</div></div>
    <div class="stat"><div class="stat-n">{{ hoy }}</div><div class="stat-l">Hoy</div></div>
  </div>

  <div class="actions">
    <input class="search-inp" type="text" id="buscar" placeholder="🔍 Buscar por nombre, email o empresa..." oninput="filtrar()">
    <a href="/admin/exportar" class="btn btn-outline">📥 Exportar CSV</a>
    <a href="/admin/marcar-todos" class="btn btn-outline">✓ Marcar todos leídos</a>
  </div>

  {% if contactos %}
  <table id="tabla">
    <thead>
      <tr>
        <th>#</th>
        <th>Estado</th>
        <th>Fecha</th>
        <th>Nombre</th>
        <th>Empresa</th>
        <th>Email</th>
        <th>Tel / WhatsApp</th>
        <th>Necesidad</th>
        <th>Mensaje</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
    {% for c in contactos %}
      <tr data-row="{{ c.nombre }} {{ c.empresa }} {{ c.email }}">
        <td class="fecha">{{ c.id }}</td>
        <td>
          {% if not c.leido %}
            <span class="badge-new">NUEVO</span>
          {% else %}
            <span class="badge-read">Leído</span>
          {% endif %}
        </td>
        <td class="fecha">{{ c.fecha[:16] }}</td>
        <td><strong>{{ c.nombre }}</strong></td>
        <td>{{ c.empresa or '—' }}</td>
        <td><a class="email-link" href="mailto:{{ c.email }}">{{ c.email }}</a></td>
        <td>{% if c.telefono %}<a class="email-link" href="https://wa.me/57{{ c.telefono|replace('+57','') }}">{{ c.telefono }}</a>{% else %}—{% endif %}</td>
        <td><span class="tag-n">{{ c.necesidad or 'general' }}</span></td>
        <td class="msg-cell">{{ c.mensaje[:120] }}{% if c.mensaje|length > 120 %}...{% endif %}</td>
        <td><button class="mark-btn" onclick="marcar({{ c.id }}, this)">✓ Leído</button></td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty">📭 Aún no hay contactos registrados</div>
  {% endif %}
</div>

<script>
function filtrar(){
  var q = document.getElementById('buscar').value.toLowerCase();
  document.querySelectorAll('#tabla tbody tr').forEach(function(r){
    r.style.display = r.dataset.row.toLowerCase().includes(q) ? '' : 'none';
  });
}
function marcar(id, btn){
  fetch('/admin/marcar/'+id, {method:'POST'})
    .then(function(r){return r.json()})
    .then(function(d){
      if(d.ok){
        var td = btn.closest('tr').querySelector('td:nth-child(2)');
        td.innerHTML = '<span class="badge-read">Leído</span>';
        btn.style.display='none';
      }
    });
}
</script>
{% endif %}
</body>
</html>
"""


# ─── Sesiones simples en memoria ───────────────────────────────
sessions = set()

@app.route('/admin', methods=['GET','POST'])
def admin():
    token = request.cookies.get('nx_admin')
    if request.method == 'POST':
        pw = request.form.get('pass','')
        if pw == ADMIN_PASS:
            tok = secrets.token_hex(16)
            sessions.add(tok)
            c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
            rows = c.execute("SELECT * FROM contactos ORDER BY id DESC").fetchall()
            total    = len(rows)
            no_leidos = sum(1 for r in rows if not r['leido'])
            hoy_str  = datetime.now().strftime('%Y-%m-%d')
            hoy      = sum(1 for r in rows if r['fecha'].startswith(hoy_str))
            c.close()
            from flask import make_response
            resp = make_response(render_template_string(
                ADMIN_TEMPLATE, autenticado=True,
                contactos=[dict(r) for r in rows],
                total=total, no_leidos=no_leidos, hoy=hoy, error=False))
            resp.set_cookie('nx_admin', tok, max_age=3600*8, httponly=True)
            return resp
        return render_template_string(ADMIN_TEMPLATE, autenticado=False, error=True)

    if token and token in sessions:
        c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
        rows = c.execute("SELECT * FROM contactos ORDER BY id DESC").fetchall()
        total    = len(rows)
        no_leidos = sum(1 for r in rows if not r['leido'])
        hoy_str  = datetime.now().strftime('%Y-%m-%d')
        hoy      = sum(1 for r in rows if r['fecha'].startswith(hoy_str))
        c.close()
        return render_template_string(
            ADMIN_TEMPLATE, autenticado=True,
            contactos=[dict(r) for r in rows],
            total=total, no_leidos=no_leidos, hoy=hoy, error=False)

    return render_template_string(ADMIN_TEMPLATE, autenticado=False, error=False)


@app.route('/admin/logout')
def admin_logout():
    tok = request.cookies.get('nx_admin','')
    sessions.discard(tok)
    from flask import redirect, make_response
    resp = make_response(redirect('/admin'))
    resp.set_cookie('nx_admin', '', expires=0)
    return resp


@app.route('/admin/marcar/<int:cid>', methods=['POST'])
def marcar_leido(cid):
    tok = request.cookies.get('nx_admin','')
    if tok not in sessions:
        return jsonify({'ok': False}), 401
    c = sqlite3.connect(DB)
    c.execute("UPDATE contactos SET leido=1 WHERE id=?", (cid,))
    c.commit(); c.close()
    return jsonify({'ok': True})


@app.route('/admin/marcar-todos')
def marcar_todos():
    tok = request.cookies.get('nx_admin','')
    if tok not in sessions:
        from flask import redirect
        return redirect('/admin')
    c = sqlite3.connect(DB)
    c.execute("UPDATE contactos SET leido=1")
    c.commit(); c.close()
    from flask import redirect
    return redirect('/admin')


@app.route('/admin/exportar')
def exportar_csv():
    tok = request.cookies.get('nx_admin','')
    if tok not in sessions:
        from flask import redirect
        return redirect('/admin')
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    rows = c.execute("SELECT * FROM contactos ORDER BY id DESC").fetchall()
    c.close()
    import io, csv
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['ID','Fecha','Nombre','Empresa','Email','Telefono','Necesidad','Mensaje','IP'])
    for r in rows:
        w.writerow([r['id'],r['fecha'],r['nombre'],r['empresa'],
                    r['email'],r['telefono'],r['necesidad'],r['mensaje'],r['ip']])
    from flask import Response
    return Response(
        '\ufeff' + output.getvalue(),  # BOM para Excel
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=contactos_nexcoreia.csv'}
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
