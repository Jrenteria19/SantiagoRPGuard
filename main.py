import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import pytz

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuración del bot con intenciones
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# =============================================
# BASE DE DATOS (SQLITE)
# =============================================
# Ruta del archivo de la base de datos SQLite
DATABASE_PATH = "santiagorp.db"

def get_db_connection():
    """Obtener conexión a la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Para devolver filas como diccionarios
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar a SQLite: {e}")
        raise

def init_db():
    """Inicializar la base de datos SQLite para sanciones y calificaciones."""
    print("Inicializando base de datos SQLite...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tabla de sanciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sanciones (
                sanction_id TEXT PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                reason TEXT,
                sanction_type TEXT,
                proof_url TEXT,
                admin_id INTEGER,
                admin_name TEXT,
                date TEXT,
                active INTEGER
            )
        ''')
        
        # Tabla de calificaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calificaciones (
                rating_id TEXT PRIMARY KEY,
                staff_id INTEGER,
                staff_name TEXT,
                rating INTEGER,
                comment TEXT,
                user_id INTEGER,
                user_name TEXT,
                date TEXT
            )
        ''')
        
        conn.commit()
        print("Tablas 'sanciones' y 'calificaciones' creadas o verificadas correctamente.")
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")

# Inicializar base de datos al inicio
init_db()

# =============================================
# CONSTANTES Y CONFIGURACIÓN
# =============================================
class Colors:
    PRIMARY = 0x5865F2
    SUCCESS = 0x57F287
    WARNING = 0xFEE75C
    DANGER = 0xED4245
    INFO = 0xEB459E
    MUNICIPALITY = 0xF1C40F
    APPEALS = 0xE67E22
    REPORTS = 0xE74C3C
    ILLEGAL = 0x992D22
    LEGAL = 0x1ABC9C

class Channels:
    TICKETS = 1339386616405561403
    TICKET_LOGS = 1364099901813690419
    CONTROL_PANEL = 1364100260363898890
    ANNOUNCEMENTS = 1354927711306645696
    LOGS = 1364100505990729780
    SANCTIONS = 1339386616405561395
    SANCTION_LOGS = 1367390263743348848
    VIEW_SANCTIONS = 1344075561689026722
    RATINGS = 1339386616405561398
    JOB_APPLICATIONS = 1365153550816116797
    JOB_REVIEW = 1365158553412964433
    JOB_LOGS = 1367390263743348848

class Roles:
    STAFF = [1339386615247798362, 1346545514492985486, 1339386615222767662, 1347803116741066834, 1339386615235346439]
    WARN_1 = 1341459151913746503
    WARN_2 = 1341459663232696416
    WARN_3 = 1341459796846579834
    WARN_4 = 1358226550046326895
    WARN_5 = 1358226564629926060
    MEGANOTICIAS = 1348164800445808661
    BARBERO = 1348163657086799892
    TAXISTA = 1348163838905946122
    BASURERO = 1348163889619144764
    CARTERO = 1348163951921201152
    CAFETERIA = 1348163986230607902
    BANQUERO = 1348164352020185098
    RAPPI = 1348164456814874644
    MECANICO = 1348164518760546314
    COPEC = 1348164577426149419
    TIENDA_ROPA = 1348164652390940714
    GRANJERO = 1348164695621898321
    DOCTOR = 1348164862538416231
    CONSTRUCTOR = 1348164938287419453
    BURGERKING = 1348164981027508295
    JOYERIA = 1348165001579593830
    RESTAURANT_RJ = 1348165107145773096
    PASTELERIA = 1348165182685319169
    AGENCIA_VEHICULOS = 1348165259625631775
    TIENDA_APPLE = 1348165319088144425
    TACOS = 1348165379410890843
    DRAGONES_CHINA = 1348165483878416384
    SUELDO = 1346556183586148514

TICKET_CATEGORIES = {
    "general_help": {
        "id": 1364101565538893924,
        "emoji": "🧩",
        "color": Colors.PRIMARY,
        "title": "Ayuda General",
        "description": "Para cualquier duda o problema general del servidor"
    },
    "appeals": {
        "id": 1364101565538893925,
        "emoji": "📜",
        "color": Colors.APPEALS,
        "title": "Apelaciones",
        "description": "Para apelar sanciones recibidas"
    },
    "reports": {
        "id": 1364101565538893926,
        "emoji": "🚨",
        "color": Colors.REPORTS,
        "title": "Denuncias",
        "description": "Para reportar problemas o infracciones"
    },
    "jobs": {
        "id": 1364101565538893927,
        "emoji": "💼",
        "color": Colors.MUNICIPALITY,
        "title": "Trabajos",
        "description": "Para consultas o solicitudes de trabajos"
    }
}

server_status = "indefinido"

JOB_ROLES = {
    "meganoticias": {"name": "Meganoticias", "role_id": Roles.MEGANOTICIAS},
    "barbero": {"name": "Barbero", "role_id": Roles.BARBERO},
    "taxista": {"name": "Taxista", "role_id": Roles.TAXISTA},
    "basurero": {"name": "Basurero", "role_id": Roles.BASURERO},
    "cartero": {"name": "Cartero", "role_id": Roles.CARTERO},
    "cafeteria": {"name": "Cafetería", "role_id": Roles.CAFETERIA},
    "banquero": {"name": "Banquero", "role_id": Roles.BANQUERO},
    "rappi": {"name": "Rappi", "role_id": Roles.RAPPI},
    "mecanico": {"name": "Mecánico", "role_id": Roles.MECANICO},
    "copec": {"name": "Copec", "role_id": Roles.COPEC},
    "tienda_ropa": {"name": "Tienda de Ropa", "role_id": Roles.TIENDA_ROPA},
    "granjero": {"name": "Granjero", "role_id": Roles.GRANJERO},
    "doctor": {"name": "Doctor", "role_id": Roles.DOCTOR},
    "constructor": {"name": "Constructor", "role_id": Roles.CONSTRUCTOR},
    "burgerking": {"name": "Burger King", "role_id": Roles.BURGERKING},
    "joyeria": {"name": "Joyería", "role_id": Roles.JOYERIA},
    "restaurant_rj": {"name": "Restaurant RJ", "role_id": Roles.RESTAURANT_RJ},
    "pasteleria": {"name": "Pastelería", "role_id": Roles.PASTELERIA},
    "agencia_vehiculos": {"name": "Agencia de Vehículos", "role_id": Roles.AGENCIA_VEHICULOS},
    "tienda_apple": {"name": "Tienda Apple", "role_id": Roles.TIENDA_APPLE},
    "tacos": {"name": "Tacos", "role_id": Roles.TACOS},
    "dragones_china": {"name": "Dragones China", "role_id": Roles.DRAGONES_CHINA}
}

# =============================================
# HELPERS
# =============================================
def create_embed(title: str, description: str, color: int, user: discord.Member = None, thumbnail: str = None) -> discord.Embed:
    """Crear un embed profesional y consistente."""
    embed = discord.Embed(
        title=f"🌟 {title}",
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Santiago RP | Sistema Automatizado")
    if user:
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    return embed

# =============================================
# FUNCIONES DE SANCIONES
# =============================================
def save_sanction(user_id: int, username: str, reason: str, sanction_type: str, proof_url: str, admin_id: int, admin_name: str):
    """Guardar una sanción en la base de datos."""
    sanction_id = str(uuid.uuid4())
    date = datetime.now(pytz.UTC).isoformat()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sanciones (sanction_id, user_id, username, reason, sanction_type, proof_url, admin_id, admin_name, date, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sanction_id, user_id, username, reason, sanction_type, proof_url, admin_id, admin_name, date, 1))
        conn.commit()
        return sanction_id
    except sqlite3.Error as e:
        print(f"Error al guardar sanción: {e}")
        return None
    finally:
        if conn:
            conn.close()

def count_active_sanctions(user_id: int) -> int:
    """Contar sanciones activas de un usuario."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM sanciones WHERE user_id = ? AND active = 1', (user_id,))
        count = cursor.fetchone()['count']
        return count
    except sqlite3.Error as e:
        print(f"Error al contar sanciones: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def deactivate_sanction(sanction_id: str):
    """Desactivar una sanción específica."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE sanciones SET active = 0 WHERE sanction_id = ?', (sanction_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al desactivar sanción: {e}")
    finally:
        if conn:
            conn.close()

def get_user_sanctions(user_id: int):
    """Obtener todas las sanciones de un usuario."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sanciones WHERE user_id = ?', (user_id,))
        sanctions = cursor.fetchall()
        return sanctions
    except sqlite3.Error as e:
        print(f"Error al obtener sanciones: {e}")
        return []
    finally:
        if conn:
            conn.close()

# =============================================
# FUNCIONES DE CALIFICACIONES
# =============================================
def save_rating(staff_id: int, staff_name: str, rating: int, comment: str, user_id: int, user_name: str):
    """Guardar una calificación en la base de datos."""
    rating_id = str(uuid.uuid4())
    date = datetime.now(pytz.UTC).isoformat()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO calificaciones (rating_id, staff_id, staff_name, rating, comment, user_id, user_name, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (rating_id, staff_id, staff_name, rating, comment, user_id, user_name, date))
        conn.commit()
        return rating_id
    except sqlite3.Error as e:
        print(f"Error al guardar calificación: {e}")
        return None
    finally:
        if conn:
            conn.close()

# =============================================
# EVENTOS DEL BOT
# =============================================
@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")

# =============================================
# COMANDOS
# =============================================
@bot.tree.command(name="sanction", description="Aplica una sanción a un usuario")
@app_commands.describe(
    user="Usuario a sancionar",
    reason="Razón de la sanción",
    sanction_type="Tipo de sanción",
    proof_url="URL de la prueba"
)
async def sanction(interaction: discord.Interaction, user: discord.User, reason: str, sanction_type: str, proof_url: str):
    if not any(role.id in Roles.STAFF for role in interaction.user.roles):
        await interaction.response.send_message(embed=create_embed(
            "Error",
            "No tienes permisos para usar este comando.",
            Colors.DANGER
        ), ephemeral=True)
        return

    sanction_id = save_sanction(user.id, user.name, reason, sanction_type, proof_url, interaction.user.id, interaction.user.name)
    if not sanction_id:
        await interaction.response.send_message(embed=create_embed(
            "Error",
            "No se pudo guardar la sanción. Intenta de nuevo.",
            Colors.DANGER
        ), ephemeral=True)
        return

    sanction_count = count_active_sanctions(user.id)
    warn_role = None
    if sanction_count == 1:
        warn_role = Roles.WARN_1
    elif sanction_count == 2:
        warn_role = Roles.WARN_2
    elif sanction_count == 3:
        warn_role = Roles.WARN_3
    elif sanction_count == 4:
        warn_role = Roles.WARN_4
    elif sanction_count >= 5:
        warn_role = Roles.WARN_5

    if warn_role:
        role = interaction.guild.get_role(warn_role)
        if role:
            await user.add_roles(role)

    embed = create_embed(
        "Sanción Aplicada",
        f"**Usuario:** {user.mention}\n**Razón:** {reason}\n**Tipo:** {sanction_type}\n**Prueba:** [Ver]({proof_url})\n**Sanciones Activas:** {sanction_count}",
        Colors.DANGER,
        user=interaction.user
    )
    await interaction.response.send_message(embed=embed)

    log_channel = bot.get_channel(Channels.SANCTION_LOGS)
    if log_channel:
        await log_channel.send(embed=embed)

@bot.tree.command(name="view_sanctions", description="Ver sanciones de un usuario")
@app_commands.describe(user="Usuario a consultar")
async def view_sanctions(interaction: discord.Interaction, user: discord.User):
    sanctions = get_user_sanctions(user.id)
    if not sanctions:
        await interaction.response.send_message(embed=create_embed(
            "Sin Sanciones",
            f"{user.mention} no tiene sanciones registradas.",
            Colors.SUCCESS
        ), ephemeral=True)
        return

    description = ""
    for sanction in sanctions:
        status = "Activa" if sanction['active'] else "Inactiva"
        description += f"**ID:** {sanction['sanction_id']}\n**Razón:** {sanction['reason']}\n**Tipo:** {sanction['sanction_type']}\n**Prueba:** [Ver]({sanction['proof_url']})\n**Fecha:** {sanction['date']}\n**Estado:** {status}\n**Admin:** {sanction['admin_name']}\n\n"

    embed = create_embed(
        f"Sanciones de {user.name}",
        description,
        Colors.INFO,
        user=user
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="rate_staff", description="Califica a un miembro del staff")
@app_commands.describe(
    staff="Miembro del staff a calificar",
    rating="Calificación (1-5)",
    comment="Comentario sobre la calificación"
)
async def rate_staff(interaction: discord.Interaction, staff: discord.User, rating: int, comment: str):
    if rating < 1 or rating > 5:
        await interaction.response.send_message(embed=create_embed(
            "Error",
            "La calificación debe estar entre 1 y 5.",
            Colors.DANGER
        ), ephemeral=True)
        return

    rating_id = save_rating(staff.id, staff.name, rating, comment, interaction.user.id, interaction.user.name)
    if not rating_id:
        await interaction.response.send_message(embed=create_embed(
            "Error",
            "No se pudo guardar la calificación. Intenta de nuevo.",
            Colors.DANGER
        ), ephemeral=True)
        return

    embed = create_embed(
        "Calificación Enviada",
        f"**Staff:** {staff.mention}\n**Calificación:** {rating}/5\n**Comentario:** {comment}",
        Colors.SUCCESS,
        user=interaction.user
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

    rating_channel = bot.get_channel(Channels.RATINGS)
    if rating_channel:
        await rating_channel.send(embed=embed)

# =============================================
# EJECUCIÓN DEL BOT
# =============================================
bot.run(TOKEN)
