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
def get_db_connection():
    """Obtener conexión a la base de datos SQLite."""
    try:
        connection = sqlite3.connect('santiago_rp.db')
        connection.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
        return connection
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
                date DATETIME,
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
                date DATETIME
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
    PRIMARY = 0x5865F2  # Discord blurple
    SUCCESS = 0x57F287  # Discord green
    WARNING = 0xFEE75C  # Discord yellow
    DANGER = 0xED4245   # Discord red
    INFO = 0xEB459E     # Discord pink
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
    JOB_APPLICATIONS = 1365153550816116797  # Channel where /postular-trabajo is used
    JOB_REVIEW = 1365158553412964433  # Channel where staff review applications
    JOB_LOGS = 1367390263743348848  # Added for job logs (using same as SANCTION_LOGS for simplicity)

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
    "municipality": {
        "id": 1364101710431125545,
        "emoji": "🏛️",
        "color": Colors.MUNICIPALITY,
        "title": "Municipalidad",
        "description": "Trámites municipales, licencias, propiedades"
    },
    "purchases": {
        "id": 1364101786734039052,
        "emoji": "🛍️",
        "color": Colors.SUCCESS,
        "title": "Compras",
        "description": "Problemas con compras, beneficios o paquetes VIP"
    },
    "benefits": {
        "id": 1364101877847031858,
        "emoji": "🎁",
        "color": Colors.INFO,
        "title": "Beneficios",
        "description": "Reclamos o consultas sobre beneficios especiales"
    },
    "alliances": {
        "id": 1364101958142660681,
        "emoji": "🤝",
        "color": Colors.PRIMARY,
        "title": "Alianzas",
        "description": "Solicitudes de alianzas entre facciones/empresas"
    },
    "doubts": {
        "id": 1364102041961758770,
        "emoji": "💭",
        "color": Colors.WARNING,
        "title": "Dudas",
        "description": "Consultas sobre reglas, mecánicas o funcionamiento"
    },
    "appeals": {
        "id": 1364102108894199911,
        "emoji": "📜",
        "color": Colors.APPEALS,
        "title": "Apelaciones",
        "description": "Apelar sanciones, baneos o advertencias"
    },
    "reports": {
        "id": 1364102219393142866,
        "emoji": "⚠️",
        "color": Colors.REPORTS,
        "title": "Reportes",
        "description": "Reportar jugadores, bugs o problemas graves"
    },
    "illegal_faction": {
        "id": 1364102328470212748,
        "emoji": "🕵️",
        "color": Colors.ILLEGAL,
        "title": "Facción Ilegal",
        "description": "Registro o consultas de facciones ilegales"
    },
    "robbery_claim": {
        "id": 1364102435425091695,
        "emoji": "🚔",
        "color": Colors.DANGER,
        "title": "Reclamo Robo",
        "description": "Reportar robos o pérdida de items/vehículos"
    },
    "business_creation": {
        "id": 1364102590123479122,
        "emoji": "🏢",
        "color": Colors.LEGAL,
        "title": "Creación Empresa",
        "description": "Solicitud para crear una empresa legal"
    },
    "ck_request": {
        "id": 1364102678816358420,
        "emoji": "💀",
        "color": Colors.DANGER,
        "title": "Solicitud CK",
        "description": "Solicitar Character Kill (muerte permanente)"
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
    "restaurant_rj": {"name": "Restaurante R&J", "role_id": Roles.RESTAURANT_RJ},
    "pasteleria": {"name": "Pastelería", "role_id": Roles.PASTELERIA},
    "agencia_vehiculos": {"name": "Agencia de Vehículos", "role_id": Roles.AGENCIA_VEHICULOS},
    "tienda_apple": {"name": "Tienda Apple", "role_id": Roles.TIENDA_APPLE},
    "握
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
    date = datetime.now()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sanciones (sanction_id, user_id, username, reason, sanction_type, proof_url, admin_id, admin_name, date, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sanction_id, user_id, username, reason, sanction_type, proof_url, admin_id, admin_name, date, 1))
        conn.commit()
        print(f"Sanción {sanction_id} guardada correctamente.")
        return sanction_id
    except sqlite3.Error as e:
        print(f"Error al guardar sanción: {e}")
        raise
    finally:
        if conn:
            conn.close()

def count_active_sanctions(user_id: int) -> int:
    """Contar sanciones activas de un usuario."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM sanciones WHERE user_id = ? AND active = ?', (user_id, 1))
        result = cursor.fetchone()
        count = result['count']
        return count
    except sqlite3.Error as e:
        print(f"Error al contar sanciones: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_user_sanctions(user_id: int) -> list:
    """Obtener todas las sanciones activas de un usuario."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT sanction_id, reason, sanction_type, proof_url, admin_name, date
            FROM sanciones
            WHERE user_id = ? AND active = ?
            ORDER BY date DESC
        ''', (user_id, 1))
        sanctions = cursor.fetchall()
        result = [(s['sanction_id'], s['reason'], s['sanction_type'], s['proof_url'], s['admin_name'], s['date'].isoformat()) for s in sanctions]
        return result
    except sqlite3.Error as e:
        print(f"Error al obtener sanciones: {e}")
        raise
    finally:
        if conn:
            conn.close()

def delete_user_sanctions(user_id: int) -> int:
    """Marcar todas las sanciones activas de un usuario como inactivas."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE sanciones SET active = ? WHERE user_id = ? AND active = ?', (0, user_id, 1))
        affected_rows = cursor.rowcount
        conn.commit()
        return affected_rows
    except sqlite3.Error as e:
        print(f"Error al borrar sanciones: {e}")
        raise
    finally:
        if conn:
            conn.close()

# =============================================
# AUTOCOMPLETE PARA SANCIONES
# =============================================
async def sanction_type_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocompletar tipos de sanción."""
    sanction_types = [
        {"name": "Advertencia 1", "role_id": Roles.WARN_1},
        {"name": "Advertencia 2", "role_id": Roles.WARN_2},
        {"name": "Advertencia 3", "role_id": Roles.WARN_3}
    ]
    return [
        app_commands.Choice(name=sanction["name"], value=sanction["name"])
        for sanction in sanction_types
        if current.lower() in sanction["name"].lower()
    ]

# =============================================
# FUNCIONES DE CALIFICACIONES
# =============================================
def save_rating(staff_id: int, staff_name: str, rating: int, comment: str, user_id: int, user_name: str):
    """Guardar una calificación en la base de datos."""
    rating_id = str(uuid.uuid4())
    date = datetime.now()
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
        raise
    finally:
        if conn:
            conn.close()

def get_top_staff() -> tuple:
    """Obtener el staff con mejor promedio de calificación (mínimo 3 calificaciones)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT staff_id, staff_name, AVG(rating) as avg_rating, COUNT(rating) as count_rating
            FROM calificaciones
            GROUP BY staff_id
            HAVING COUNT(rating) >= 3
            ORDER BY AVG(rating) DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        if result:
            return (result['staff_id'], result['staff_name'], result['avg_rating'], result['count_rating'])
        return None
    except sqlite3.Error as e:
        print(f"Error al obtener top staff: {e}")
        raise
    finally:
        if conn:
            conn.close()

def clear_ratings():
    """Borrar todas las calificaciones de la base de datos."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM calificaciones')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al borrar calificaciones: {e}")
        raise
    finally:
        if conn:
            conn.close()

# =============================================
# AUTOCOMPLETE
# =============================================
async def rating_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocompletar calificaciones con estrellas (1 a 5)."""
    ratings = [
        {"value": "1", "name": "🌟 1 Estrella"},
        {"value": "2", "name": "🌟🌟 2 Estrellas"},
        {"value": "3", "name": "🌟🌟🌟 3 Estrellas"},
        {"value": "4", "name": "🌟🌟🌟🌟 4 Estrellas"},
        {"value": "5", "name": "🌟🌟🌟🌟🌟 5 Estrellas"}
    ]
    return [
        app_commands.Choice(name=rating["name"], value=rating["value"])
        for rating in ratings
        if current.lower() in rating["name"].lower() or not current
    ]

# =============================================
# COMPONENTES UI PERSONALIZADOS
# =============================================
class CloseServerModal(ui.Modal, title="🔒 Cerrar Servidor"):
    reason = ui.TextInput(
        label="Razón del cierre",
        placeholder="Ejemplo: Mantenimiento programado, falta de jugadores...",
        style=discord.TextStyle.long,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class GradientButton(ui.Button):
    """Botón con efecto de gradiente personalizado y cooldown."""
    cooldowns = {}  # Diccionario para rastrear cooldowns: {user_id: {button_id: timestamp}}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.original_label = self.label
        self.original_style = self.style
        self.original_emoji = self.emoji
        
    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        button_id = self.custom_id

        # Verificar cooldown
        if user_id in self.cooldowns and button_id in self.cooldowns[user_id]:
            last_used = self.cooldowns[user_id][button_id]
            time_since_last = time.time() - last_used
            if time_since_last < 60:  # Cooldown de 60 segundos
                remaining = int(60 - time_since_last)
                await interaction.response.send_message(embed=create_embed(
                    title="⏳ En Cooldown",
                    description=f"Por favor, espera {remaining} segundos antes de usar este botón nuevamente.",
                    color=Colors.WARNING
                ), ephemeral=True)
                return

        # Actualizar cooldown
        if user_id not in self.cooldowns:
            self.cooldowns[user_id] = {}
        self.cooldowns[user_id][button_id] = time.time()

        self.style = discord.ButtonStyle.grey
        self.label = "⌛ Procesando..."
        self.emoji = None
        try:
            await interaction.message.edit(view=self.view)
        except discord.errors.NotFound:
            print(f"⚠️ No se pudo editar el mensaje: canal no encontrado.")
            return
        except discord.errors.HTTPException as e:
            print(f"⚠️ Error HTTP al editar mensaje: {e}")
            return
        
        try:
            if self.custom_id == "ticket_claim":
                await handle_ticket_claim(interaction)
            elif self.custom_id == "ticket_close":
                await handle_ticket_close(interaction)
            elif self.custom_id == "ticket_add_user":
                await handle_ticket_add_user(interaction)
            elif self.custom_id == "start_server":
                await handle_server_start(interaction)
            elif self.custom_id == "start_vote":
                await handle_vote_start(interaction)
            elif self.custom_id == "close_server":
                await handle_server_close(interaction)
        except Exception as e:
            print(f"Error en botón {self.custom_id}: {e}")
            try:
                await interaction.followup.send(embed=create_embed(
                    title="❌ Error",
                    description="Ocurrió un error al procesar tu acción. Por favor, intenta de nuevo.",
                    color=Colors.DANGER
                ), ephemeral=True)
            except (discord.errors.NotFound, discord.errors.InteractionResponded) as followup_error:
                print(f"⚠️ No se pudo enviar mensaje de error: {followup_error}")
        finally:
            self.style = self.original_style
            self.label = self.original_label
            self.emoji = self.original_emoji
            try:
                await interaction.message.edit(view=self.view)
            except discord.errors.NotFound:
                print(f"⚠️ No se pudo restaurar el mensaje: canal no encontrado.")
            except discord.errors.HTTPException as e:
                print(f"⚠️ Error HTTP al restaurar mensaje: {e}")

class VoteStartModal(ui.Modal, title="🗳️ Iniciar Votación"):
    votes_required = ui.TextInput(
        label="Número de votos requeridos",
        placeholder="Ejemplo: 6",
        style=discord.TextStyle.short,
        required=True
    )
    
    authorized_by = ui.TextInput(
        label="Autorizado por (nombre sin @)",
        placeholder="Ejemplo: Nicolas",
        style=discord.TextStyle.short,
        required=True
    )
    
    authorized_by_id = ui.TextInput(
        label="ID de Discord de quien autorizó",
        placeholder="Ejemplo: 123456789012345678",
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class GeneralHelpModal(ui.Modal, title="🧩 Solicitud de Ayuda"):
    roblox_username = ui.TextInput(
        label="Tu nombre en Roblox",
        placeholder="Ejemplo: SantiagoRP_Player",
        style=discord.TextStyle.short,
        required=True
    )
    
    issue = ui.TextInput(
        label="Describe tu problema",
        style=discord.TextStyle.long,
        placeholder="Por favor, detalla tu problema para que podamos ayudarte...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class MunicipalityModal(ui.Modal, title="🏛️ Trámite Municipal"):
    roblox_username = ui.TextInput(
        label="Tu nombre en Roblox",
        placeholder="Ejemplo: SantiagoRP_Player",
        style=discord.TextStyle.short,
        required=True
    )
    
    procedure = ui.TextInput(
        label="¿Qué trámite necesitas?",
        style=discord.TextStyle.long,
        placeholder="Ejemplo: Licencia de conducir, registro de vehículo, propiedad...",
        required=True
    )
    
    details = ui.TextInput(
        label="Detalles adicionales",
        style=discord.TextStyle.long,
        placeholder="Proporciona cualquier información adicional relevante...",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class IllegalFactionModal(ui.Modal, title="🕵️ Creación de Facción Ilegal"):
    faction_name = ui.TextInput(
        label="Nombre de la Facción",
        placeholder="Ejemplo: Cartel del Noroeste",
        required=True
    )
    
    owners = ui.TextInput(
        label="Dueño(s) (Roblox)",
        placeholder="Ejemplo: Player1, Player2, Player3",
        style=discord.TextStyle.long,
        required=True
    )
    
    description = ui.TextInput(
        label="Descripción de la Facción",
        style=discord.TextStyle.long,
        placeholder="Describe los objetivos y actividades de tu facción...",
        required=True
    )
    
    discord_link = ui.TextInput(
        label="Link de Discord de la facción",
        placeholder="Ejemplo: https://discord.gg/abcdef",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class CloseTicketModal(ui.Modal, title="🔒 Cerrar Ticket"):
    reason = ui.TextInput(
        label="Razón del cierre",
        placeholder="Ejemplo: Problema resuelto, usuario inactivo...",
        style=discord.TextStyle.long,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class PurchasesModal(ui.Modal, title="🛍️ Ticket de Compras"):
    roblox_username = ui.TextInput(
        label="Tu nombre en Roblox",
        placeholder="Ejemplo: SantiagoRP_Player",
        style=discord.TextStyle.short,
        required=True
    )
    
    issue = ui.TextInput(
        label="Razón del ticket",
        style=discord.TextStyle.long,
        placeholder="Describe el problema con tu compra en detalle...",
        required=True
    )
    
    payment_proof = ui.TextInput(
        label="Link del comprobante de pago (opcional)",
        style=discord.TextStyle.short,
        placeholder="Ejemplo: https://imgur.com/abcdef",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class BenefitsModal(ui.Modal, title="🎁 Reclamo de Beneficios"):
    roblox_username = ui.TextInput(
        label="Tu nombre en Roblox",
        placeholder="Ejemplo: SantiagoRP_Player",
        style=discord.TextStyle.short,
        required=True
    )
    
    benefits = ui.TextInput(
        label="Beneficios a reclamar",
        style=discord.TextStyle.long,
        placeholder="Detalla los beneficios que deseas reclamar...",
        required=True
    )
    
    proof_link = ui.TextInput(
        label="Link de pruebas (opcional)",
        style=discord.TextStyle.short,
        placeholder="Ejemplo: https://imgur.com/abcdef",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class AlliancesModal(ui.Modal, title="🤝 Solicitud de Alianza"):
    server_name = ui.TextInput(
        label="Nombre del servidor",
        placeholder="Ejemplo: Los Santos RP",
        style=discord.TextStyle.short,
        required=True
    )
    
    owner_name = ui.TextInput(
        label="Nombre de Discord del dueño",
        placeholder="Ejemplo: Username#1234",
        style=discord.TextStyle.short,
        required=True
    )
    
    server_link = ui.TextInput(
        label="Link del servidor",
        placeholder="Ejemplo: https://discord.gg/abcdef",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class AppealsModal(ui.Modal, title="📜 Apelación"):
    roblox_username = ui.TextInput(
        label="Tu nombre en Roblox",
        placeholder="Ejemplo: SantiagoRP_Player",
        style=discord.TextStyle.short,
        required=True
    )
    
    appeal_type = ui.TextInput(
        label="Tipo de apelación",
        placeholder="Ejemplo: Sanción, Baneo, Advertencia",
        style=discord.TextStyle.short,
        required=True
    )
    
    appeal_reason = ui.TextInput(
        label="Razón de la apelación",
        style=discord.TextStyle.long,
        placeholder="Explica por qué deberías ser despenalizado...",
        required=True
    )
    
    proof_link = ui.TextInput(
        label="Link de pruebas (opcional)",
        style=discord.TextStyle.short,
        placeholder="Ejemplo: https://imgur.com/abcdef",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class ReportsModal(ui.Modal, title="⚠️ Reporte"):
    reported_name = ui.TextInput(
        label="Nombre de la persona a reportar",
        placeholder="Ejemplo: SantiagoRP_Player",
        style=discord.TextStyle.short,
        required=True
    )
    
    report_type = ui.TextInput(
        label="Tipo de reporte",
        placeholder="Ejemplo: Usuario, Staff",
        style=discord.TextStyle.short,
        required=True
    )
    
    report_reason = ui.TextInput(
        label="Razón del reporte",
        style=discord.TextStyle.long,
        placeholder="Describe detalladamente el problema encontrado...",
        required=True
    )
    
    proof_link = ui.TextInput(
        label="Link de pruebas (opcional)",
        style=discord.TextStyle.short,
        placeholder="Ejemplo: https://imgur.com/abcdef",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class RobberyClaimModal(ui.Modal, title="🚔 Reclamo de Robo"):
    roblox_username = ui.TextInput(
        label="Tu nombre en Roblox",
        placeholder="Ejemplo: SantiagoRP_Player",
        style=discord.TextStyle.short,
        required=True
    )
    
    involved_players = ui.TextInput(
        label="Nombres de personas involucradas",
        style=discord.TextStyle.long,
        placeholder="Lista los nombres de Roblox de todos los involucrados...",
        required=True
    )
    
    proof_link = ui.TextInput(
        label="Link de pruebas (opcional)",
        style=discord.TextStyle.short,
        placeholder="Ejemplo: https://imgur.com/abcdef",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class BusinessCreationModal(ui.Modal, title="🏢 Creación de Empresa"):
    roblox_username = ui.TextInput(
        label="Nombre(s) de Roblox del/los dueño(s)",
        style=discord.TextStyle.long,
        placeholder="Ejemplo: SantiagoRP_Player, OtroJugador...",
        required=True
    )
    
    business_description = ui.TextInput(
        label="Descripción de la empresa",
        style=discord.TextStyle.long,
        placeholder="Describe el propósito y servicios de la empresa...",
        required=True
    )
    
    business_type = ui.TextInput(
        label="Tipo de empresa",
        placeholder="Ejemplo: Restaurante, Taller, Tienda...",
        style=discord.TextStyle.short,
        required=True
    )
    
    discord_link = ui.TextInput(
        label="Link de Discord de la empresa",
        placeholder="Ejemplo: https://discord.gg/abcdef",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class CKRequestModal(ui.Modal, title="💀 Solicitud de CK"):
    target_name = ui.TextInput(
        label="Nombre de la persona para CK",
        placeholder="Ejemplo: SantiagoRP_Player",
        style=discord.TextStyle.short,
        required=True
    )
    
    ck_reason = ui.TextInput(
        label="Razón del CK",
        style=discord.TextStyle.long,
        placeholder="Explica detalladamente por qué solicitas el CK...",
        required=True
    )
    
    proof_link = ui.TextInput(
        label="Link de pruebas",
        style=discord.TextStyle.short,
        placeholder="Ejemplo: https://imgur.com/abcdef",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

class AddUserModal(ui.Modal, title="➕ Agregar Usuario al Ticket"):
    username = ui.TextInput(
        label="Nombre de usuario de Discord",
        placeholder="Ejemplo: Jrsmile22 (sin @)",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.interaction = interaction

# =============================================
# VISTAS INTERACTIVAS
# =============================================
class ControlPanelView(ui.View):
    """Panel de control administrativo con botones interactivos."""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GradientButton(
            style=discord.ButtonStyle.success,
            label="Abrir Servidor",
            emoji="🚀",
            custom_id="start_server"
        ))
        self.add_item(GradientButton(
            style=discord.ButtonStyle.primary,
            label="Iniciar Votación",
            emoji="🗳️",
            custom_id="start_vote"
        ))
        self.add_item(GradientButton(
            style=discord.ButtonStyle.red,
            label="Cerrar Servidor",
            emoji="🔒",
            custom_id="close_server"
        ))

class TicketActionsView(ui.View):
    """Acciones para tickets con validación de roles."""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GradientButton(
            style=discord.ButtonStyle.green,
            label="Atender Ticket",
            emoji="🛎️",
            custom_id="ticket_claim"
        ))
        self.add_item(GradientButton(
            style=discord.ButtonStyle.red,
            label="Cerrar Ticket",
            emoji="🔒",
            custom_id="ticket_close"
        ))
        self.add_item(GradientButton(
            style=discord.ButtonStyle.blurple,
            label="Añadir Usuario",
            emoji="➕",
            custom_id="ticket_add_user"
        ))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Verificar que el usuario tenga permisos de staff."""
        if not any(role.id in Roles.STAFF for role in interaction.user.roles):
            await interaction.response.send_message(embed=create_embed(
                title="❌ Acceso Denegado",
                description="No tienes permisos para realizar esta acción.",
                color=Colors.DANGER
            ), ephemeral=True)
            return False
        return True

class SupportButton(ui.Button):
    """Botón que dirige al canal de soporte o reglas."""
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label="📚 Ver Reglas",
            emoji="📜",
            custom_id="support_button"
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=create_embed(
            title="📚 Reglas del Servidor",
            description=(
                "Por favor, lee las reglas del servidor en el canal correspondiente antes de abrir un ticket.\n"
                "Abrir tickets sin motivo válido resultará en **sanciones**.\n"
                "Si necesitas ayuda, visita nuestro canal de soporte o consulta las reglas en <#1339386615688335397>."
            ),
            color=Colors.INFO
        ), ephemeral=True)

class TicketCreationView(ui.View):
    """Sistema de tickets interactivo con menú desplegable y botón de soporte."""
    def __init__(self):
        super().__init__(timeout=None)
        options = [
            discord.SelectOption(
                label=f"{data['emoji']} {data['title']}",
                value=ticket_type,
                description=data["description"][:100],
                emoji=data["emoji"]
            )
            for ticket_type, data in TICKET_CATEGORIES.items()
        ]
        
        self.select = ui.Select(
            placeholder="🎟️ Elige el tipo de ticket que necesitas...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select"
        )
        self.select.callback = self.on_select
        self.add_item(self.select)
        self.add_item(SupportButton())
    
    async def on_select(self, interaction: discord.Interaction):
        """Manejar selección de categoría de ticket."""
        category = self.select.values[0]
        modal_classes = {
            "general_help": GeneralHelpModal,
            "municipality": MunicipalityModal,
            "illegal_faction": IllegalFactionModal,
            "purchases": PurchasesModal,
            "benefits": BenefitsModal,
            "alliances": AlliancesModal,
            "doubts": GeneralHelpModal,
            "appeals": AppealsModal,
            "reports": ReportsModal,
            "robbery_claim": RobberyClaimModal,
            "business_creation": BusinessCreationModal,
            "ck_request": CKRequestModal
        }
        
        modal_class = modal_classes.get(category, GeneralHelpModal)
        modal = modal_class(title=f"{TICKET_CATEGORIES[category]['emoji']} {TICKET_CATEGORIES[category]['title']}")
        
        await interaction.response.send_modal(modal)
        
        timed_out = await modal.wait()
        if timed_out:
            return await interaction.followup.send(embed=create_embed(
                title="⌛ Tiempo Agotado",
                description="El tiempo para completar el formulario ha expirado. Por favor, intenta nuevamente.",
                color=Colors.WARNING
            ), ephemeral=True)
        
        data = {child.label: child.value for child in modal.children if isinstance(child, ui.TextInput)}
        await create_ticket_channel(interaction=modal.interaction, category=category, data=data)

# =============================================
# FUNCIONES PRINCIPALES
# =============================================
async def create_ticket_channel(interaction: discord.Interaction, category: str, data: dict):
    """Crear un canal de ticket profesional."""
    try:
        category_info = TICKET_CATEGORIES.get(category, {})
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        for role_id in Roles.STAFF:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True
                )
        
        ticket_num = len([c for c in interaction.guild.get_channel(category_info["id"]).channels 
                         if c.name.startswith(f"{category}-")]) + 1
        channel_name = f"{category}-{ticket_num:03d}-{interaction.user.name}"[:100]
        
        ticket_channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=discord.Object(id=category_info["id"]),
            overwrites=overwrites
        )
        
        embed = create_embed(
            title=f"{category_info['emoji']} Ticket: {category_info['title']}",
            description=f"**Usuario:** {interaction.user.mention}\n**Categoría:** {category_info['title']}\n\nPor favor, espera la atención de nuestro equipo.",
            color=category_info["color"],
            user=interaction.user
        )
        
        for field, value in data.items():
            embed.add_field(name=field, value=value or "No especificado", inline=False)
        
        view = TicketActionsView()
        message = await ticket_channel.send(
            content=f"🎟️ {interaction.user.mention} | ¡Gracias por crear un ticket!",
            embed=embed,
            view=view
        )
        await message.pin()
        
        confirm_embed = create_embed(
            title="✅ Ticket Creado",
            description=(
                f"Tu ticket ha sido creado en {ticket_channel.mention}. Un miembro del staff lo atenderá pronto.\n\n"
                "**⚠️ Advertencia:** Abrir tickets sin motivo válido resultará en **sanciones**. Asegúrate de proporcionar información clara y relevante."
            ),
            color=Colors.SUCCESS,
            user=interaction.user
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)
        
        log_channel = bot.get_channel(Channels.TICKET_LOGS)
        if log_channel:
            log_embed = create_embed(
                title=f"{category_info['emoji']} Nuevo Ticket",
                description=f"**Tipo:** {category_info['title']}\n**Usuario:** {interaction.user.mention}\n**Canal:** {ticket_channel.mention}",
                color=category_info["color"]
            )
            await log_channel.send(embed=log_embed)
        
    except Exception as e:
        print(f"Error al crear ticket: {e}")
        await interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No pudimos crear tu ticket. Por favor, intenta de nuevo o contacta a un administrador.",
            color=Colors.DANGER
        ), ephemeral=True)

async def handle_ticket_claim(interaction: discord.Interaction):
    """Manejar reclamación de ticket por parte del staff."""
    if not any(role.id in Roles.STAFF for role in interaction.user.roles):
        return await interaction.response.send_message(embed=create_embed(
            title="❌ Acceso Denegado",
            description="Solo el staff puede atender tickets.",
            color=Colors.DANGER
        ), ephemeral=True)
    
    embed = interaction.message.embeds[0]
    for field in embed.fields:
        if field.name == "🛎️ Atendido por":
            return await interaction.response.send_message(embed=create_embed(
                title="❌ Ticket Ya Atendido",
                description="Este ticket ya ha sido reclamado por otro miembro del staff.",
                color=Colors.DANGER
            ), ephemeral=True)
    
    embed.add_field(name="🛎️ Atendido por", value=interaction.user.mention, inline=False)
    
    new_view = TicketActionsView()
    for child in new_view.children:
        if child.custom_id == "ticket_claim":
            child.disabled = True
            child.label = "Atendido"
            child.style = discord.ButtonStyle.grey
    
    await interaction.response.send_message(embed=create_embed(
        title="✅ Ticket Atendido",
        description="Has reclamado este ticket con éxito.",
        color=Colors.SUCCESS
    ), ephemeral=True)
    
    await interaction.message.edit(embed=embed, view=new_view)
    
    attention_embed = create_embed(
        title="🛎️ Ticket en Atención",
        description=f"¡Tu ticket está siendo atendido por {interaction.user.mention}!\nPor favor, ten paciencia mientras revisamos tu caso.",
        color=Colors.SUCCESS,
        user=interaction.user
    )
    await interaction.channel.send(embed=attention_embed)

async def handle_ticket_close(interaction: discord.Interaction):
    """Manejar cierre de ticket con confirmación."""
    modal = CloseTicketModal()
    await interaction.response.send_modal(modal)
    
    timed_out = await modal.wait()
    if timed_out:
        return
    
    view = TicketActionsView()
    for child in view.children:
        child.disabled = True
    try:
        await interaction.message.edit(view=view)
    except discord.errors.NotFound:
        print(f"⚠️ No se pudo editar el mensaje al cerrar ticket: canal no encontrado.")
        return
    
    closing_embed = create_embed(
        title="🔒 Cerrando Ticket",
        description=f"Este ticket se cerrará en 5 segundos.\n**Razón:** {modal.reason.value}",
        color=Colors.DANGER
    )
    await modal.interaction.followup.send(embed=closing_embed)
    
    log_channel = bot.get_channel(Channels.TICKET_LOGS)
    if log_channel:
        log_embed = create_embed(
            title="📌 Ticket Cerrado",
            description=f"**Canal:** {interaction.channel.name}\n**Cerrado por:** {interaction.user.mention}\n**Razón:** {modal.reason.value}",
            color=Colors.DANGER,
            user=interaction.user
        )
        await log_channel.send(embed=log_embed)
    
    await asyncio.sleep(5)
    try:
        await interaction.channel.delete(reason=f"Cerrado por {interaction.user}. Razón: {modal.reason.value}")
    except discord.errors.NotFound:
        print(f"⚠️ No se pudo eliminar el canal: ya no existe.")
    except Exception as e:
        print(f"Error al eliminar canal: {e}")
        await modal.interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se pudo cerrar el canal. Por favor, ciérralo manualmente.",
            color=Colors.DANGER
        ), ephemeral=True)

async def handle_ticket_add_user(interaction: discord.Interaction):
    """Manejar agregar usuario a ticket."""
    modal = AddUserModal()
    await interaction.response.send_modal(modal)
    
    timed_out = await modal.wait()
    if timed_out:
        return
    
    username = modal.username.value
    member = None
    
    for guild_member in interaction.guild.members:
        if guild_member.name.lower() == username.lower():
            member = guild_member
            break
    
    if not member:
        return await modal.interaction.followup.send(embed=create_embed(
            title="❌ Usuario no Encontrado",
            description=f"No se encontró al usuario '{username}' en el servidor.",
            color=Colors.DANGER
        ), ephemeral=True)
    
    try:
        await interaction.channel.set_permissions(
            member,
            read_messages=True,
            send_messages=True,
            view_channel=True
        )
    except discord.errors.NotFound:
        print(f"⚠️ No se pudo modificar permisos: canal no encontrado.")
        await modal.interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="El canal ya no existe. No se pudo agregar al usuario.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    await modal.interaction.followup.send(embed=create_embed(
        title="✅ Usuario Agregado",
        description=f"Se ha agregado a {member.mention} al ticket.",
        color=Colors.SUCCESS
    ), ephemeral=True)
    
    ticket_embed = create_embed(
        title="➕ Usuario Agregado",
        description=f"{member.mention} ha sido agregado al ticket por {interaction.user.mention}.",
        color=Colors.SUCCESS
    )
    try:
        await interaction.channel.send(embed=ticket_embed)
    except discord.errors.NotFound:
        print(f"⚠️ No se pudo enviar mensaje: canal no encontrado.")

async def handle_server_start(interaction: discord.Interaction):
    """Manejar inicio del servidor."""
    global server_status
    
    if not any(role.id in Roles.STAFF for role in interaction.user.roles):
        return await interaction.response.send_message(embed=create_embed(
            title="❌ Acceso Denegado",
            description="No tienes permisos para abrir el servidor.",
            color=Colors.DANGER
        ), ephemeral=True)
    
    server_status = "abierto"
    
    embed = create_embed(
        title="🚀 ¡Santiago RP Abierto! 🎉",
        description=(
            "🎮 **¡El servidor está listo para la acción!** 🎉\n"
            "¡Únete ahora y vive la experiencia de rol más intensa en Santiago RP! 🚨\n\n"
            "**📢 Cómo Unirte:**\n"
            "🔸 **Lista de servidores**: Busca 'S SANTIAGO RP | ESTRICTO | SPANISH' en ERLC.\n"
            "🔸 **Código de servidor**: Usa **STRPP** en ajustes.\n"
            "🔸 **Enlace directo (PC)**: [Unirse ahora](https://policeroleplay.community/join?code=STRPP)\n\n"
            "🙌 ¡Nos vemos en el servidor!"
        ),
        color=Colors.SUCCESS,
        user=interaction.user
    )
    embed.set_image(url="https://media.discordapp.net/attachments/1340184960379781191/1363350692651335903/RobloxScreenShot20250416_193740099_1.jpg")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else "")
    embed.set_footer(text="Santiago RP | ¡La aventura comienza! | Creado por Smile")
    
    channel = bot.get_channel(Channels.ANNOUNCEMENTS)
    try:
        await channel.purge(limit=3)
        message = await channel.send(embed=embed)
        
        mention1 = await channel.send("@everyone")
        mention2 = await channel.send("@everyone")
        
        await asyncio.sleep(30)
        await mention1.delete()
        await mention2.delete()
        
        print(f"✅ Anuncio enviado al canal {Channels.ANNOUNCEMENTS}")
    except discord.errors.Forbidden:
        print(f"❌ Error: El bot no tiene permisos para gestionar el canal {Channels.ANNOUNCEMENTS} o enviar mensajes")
        await interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se pudo enviar el anuncio. Verifica los permisos del bot.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    except discord.errors.NotFound:
        print(f"❌ Error: No se encontró el canal con ID {Channels.ANNOUNCEMENTS}")
        await interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se encontró el canal de anuncios. Contacta a un administrador.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    except Exception as e:
        print(f"❌ Error al enviar anuncio: {e}")
        await interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="Ocurrió un error al procesar la acción. Por favor, intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    await interaction.response.send_message(embed=create_embed(
        title="✅ Éxito",
        description="El servidor ha sido abierto correctamente.",
        color=Colors.SUCCESS
    ), ephemeral=True)

async def handle_server_close(interaction: discord.Interaction):
    """Manejar cierre del servidor con modal para razón."""
    global server_status
    
    if not any(role.id in Roles.STAFF for role in interaction.user.roles):
        return await interaction.response.send_message(embed=create_embed(
            title="❌ Acceso Denegado",
            description="No tienes permisos para cerrar el servidor.",
            color=Colors.DANGER
        ), ephemeral=True)
    
    modal = CloseServerModal()
    await interaction.response.send_modal(modal)
    
    timed_out = await modal.wait()
    if timed_out:
        return
    
    server_status = "cerrado"
    reason = modal.reason.value
    
    embed = create_embed(
        title="🔒 ¡Santiago RP Cerrado! 😔",
        description=(
            "🎮 **El servidor ha sido cerrado temporalmente.**\n"
            "No te preocupes, ¡volveremos pronto con más acción y rol! 🚨\n\n"
            "**📢 Información Importante:**\n"
            f"🔸 **Razón del cierre:** {reason}\n"
            "🔸 El servidor ya no está disponible para unirse.\n"
            "🔸 Mantente atento a este canal para la próxima apertura.\n"
            "🔸 Únete a nuestro Discord para actualizaciones: **[Santiago RP](https://discord.gg/santiagorp)**\n\n"
            "🙌 ¡Gracias por ser parte de nuestra comunidad!"
        ),
        color=Colors.DANGER,
        user=interaction.user
    )
    embed.set_image(url="https://media.discordapp.net/attachments/1340184960379781191/1364072022837170247/RobloxScreenShot20250413_175238971.jpg")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else "")
    embed.set_footer(text="Santiago RP | ¡Volveremos pronto! | Creado por Smile")
    
    channel = bot.get_channel(Channels.ANNOUNCEMENTS)
    try:
        await channel.purge(limit=3)
        message = await channel.send(embed=embed)
        await message.add_reaction("😔")
        
        mention1 = await channel.send("@everyone")
        mention2 = await channel.send("@everyone")
        
        await asyncio.sleep(30)
        await mention1.delete()
        await mention2.delete()
        
        print(f"✅ Anuncio enviado al canal {Channels.ANNOUNCEMENTS}")
    except discord.errors.Forbidden:
        print(f"❌ Error: El bot no tiene permisos para gestionar el canal {Channels.ANNOUNCEMENTS} o enviar mensajes")
        await modal.interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se pudo enviar el anuncio. Verifica los permisos del bot.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    except discord.errors.NotFound:
        print(f"❌ Error: No se encontró el canal con ID {Channels.ANNOUNCEMENTS}")
        await modal.interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se encontró el canal de anuncios. Contacta a un administrador.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    except Exception as e:
        print(f"❌ Error al enviar anuncio: {e}")
        await modal.interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="Ocurrió un error al procesar la acción. Por favor, intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    await modal.interaction.followup.send(embed=create_embed(
        title="✅ Éxito",
        description=f"El servidor ha sido cerrado correctamente.\n**Razón:** {reason}",
        color=Colors.SUCCESS
    ), ephemeral=True)

async def handle_vote_start(interaction: discord.Interaction):
    """Manejar inicio de votación para abrir el servidor."""
    global server_status
    
    if not any(role.id in Roles.STAFF for role in interaction.user.roles):
        return await interaction.response.send_message(embed=create_embed(
            title="❌ Acceso Denegado",
            description="No tienes permisos para iniciar una votación.",
            color=Colors.DANGER
        ), ephemeral=True)
    
    modal = VoteStartModal()
    await interaction.response.send_modal(modal)
    
    timed_out = await modal.wait()
    if timed_out:
        return
    
    server_status = "votacion"
    
    authorized_user = None
    authorized_mention = f"@{modal.authorized_by.value}"
    
    if modal.authorized_by_id.value:
        try:
            authorized_user = await interaction.guild.fetch_member(int(modal.authorized_by_id.value))
            if authorized_user:
                authorized_mention = authorized_user.mention
        except:
            pass
    
    if not authorized_user:
        for member in interaction.guild.members:
            if member.name.lower() == modal.authorized_by.value.lower():
                authorized_user = member
                authorized_mention = member.mention
                break
    
    embed = create_embed(
        title="🗳️ ¡Encuesta Iniciada! 📢",
        description=(
            "🎮 **¡Es hora de decidir!** 🗳️\n"
            "Hemos iniciado una encuesta para votar la apertura del servidor Santiago RP.\n\n"
            "**📜 Reglas para Votar:**\n"
            "🔸 Comprométete a participar activamente en el rol.\n"
            "🔸 Evita el antirol y cumple las normativas.\n"
            "🔸 No participes en facciones sin rol correspondiente.\n"
            f"🔸 **Votos requeridos:** {modal.votes_required.value}\n\n"
            "👍 **Vota a favor** | 👎 **Vota en contra**"
        ),
        color=Colors.WARNING,
        user=interaction.user
    )
    embed.set_image(url="https://media.discordapp.net/attachments/1360714101327663135/1360762037495529672/Screenshot_20250412_194212_CapCut.jpg")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else "")
    embed.add_field(name="Autorizado por", value=authorized_mention, inline=True)
    embed.set_footer(text="Santiago RP | ¡Tu voto cuenta! | Creado por Smile")
    
    channel = bot.get_channel(Channels.ANNOUNCEMENTS)
    try:
        await channel.purge(limit=3)
        message = await channel.send(embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        
        mention1 = await channel.send("@everyone")
        mention2 = await channel.send("@everyone")
        
        await asyncio.sleep(30)
        await mention1.delete()
        await mention2.delete()
        
        print(f"✅ Anuncio enviado al canal {Channels.ANNOUNCEMENTS}")
    except discord.errors.Forbidden:
        print(f"❌ Error: El bot no tiene permisos para gestionar el canal {Channels.ANNOUNCEMENTS} o enviar mensajes")
        await modal.interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se pudo enviar el anuncio. Verifica los permisos del bot.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    except discord.errors.NotFound:
        print(f"❌ Error: No se encontró el canal con ID {Channels.ANNOUNCEMENTS}")
        await modal.interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se encontró el canal de anuncios. Contacta a un administrador.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    except Exception as e:
        print(f"❌ Error al enviar anuncio: {e}")
        await modal.interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="Ocurrió un error al procesar la acción. Por favor, intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    await modal.interaction.followup.send(embed=create_embed(
        title="✅ Éxito",
        description="La votación ha sido iniciada correctamente.",
        color=Colors.SUCCESS
    ), ephemeral=True)

def is_ratings_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel_id != Channels.RATINGS:
            await interaction.response.send_message(embed=create_embed(
                title="❌ Canal Incorrecto",
                description=f"Este comando solo puede usarse en <#{Channels.RATINGS}>.",
                color=Colors.DANGER
            ), ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

# =============================================
# COMANDOS Y EVENTOS
# =============================================

# =============================
# FLUJO DE VERIFICACIÓN POR DM
# =============================

async def iniciar_cuestionario_verificacion(interaction: discord.Interaction, bot):
    preguntas = [
        "🎮 ¿Cuál es tu nombre de usuario de Roblox?",
        "🔍 ¿Qué buscas en el server?",
        "⚔️ ¿Cuál es la diferencia entre MG2 y MG?",
        "💥 ¿Qué es RK?",
        "🗡️ ¿Qué es CK?",
        "📜 ¿Qué es OCC y IC?",
        "🛡️ ¿Qué es ZZ?",
        "🌐 ¿Cómo conociste el servidor?",
        "⭐ ¿Del 1/10 qué tan bien crees que roleas?",
        "🎭 ¿Sabes de rol?",
        "📖 ¿Sabes las normas del servidor y del rol?"
    ]
    respuestas = []

    guild = interaction.guild

    confirm_embed = discord.Embed(
        title="🌟 ¡Bienvenido a la Verificación de SantiagoRP! 🌟",
        description=(
            "Estás a punto de comenzar el cuestionario de verificación. "
            "Asegúrate de tener tus DMs abiertos y responde con seriedad.\n\n"
            "📋 **Preguntas**: 11\n"
            "⏳ **Tiempo por pregunta**: 3 minutos\n"
            "✅ Presiona el botón para empezar."
        ),
        color=Colors.PRIMARY,
        timestamp=datetime.now()
    )
    confirm_embed.set_footer(text="Santiago RP | Verificación")
    confirm_embed.set_thumbnail(url=guild.icon.url if guild and guild.icon else None)

    view = ui.View()
    confirm_button = ui.Button(label="Iniciar Verificación", style=discord.ButtonStyle.primary, emoji="🚀")
    
    async def confirm_callback(interaction_btn: discord.Interaction):
        if interaction_btn.user.id != interaction.user.id:
            await interaction_btn.response.send_message("❌ Solo el usuario que inició puede confirmar.", ephemeral=True)
            return
        await interaction_btn.response.send_message("✅ ¡Cuestionario iniciado! Revisa tus DMs.", ephemeral=True)
        await start_questionnaire(interaction_btn, guild)
    
    confirm_button.callback = confirm_callback
    view.add_item(confirm_button)

    try:
        await interaction.user.send(embed=confirm_embed, view=view)
        await interaction.response.send_message("📩 Te he enviado un mensaje privado para iniciar la verificación. ¡Revisa tus DMs!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("🚫 No puedo enviarte mensajes privados. Habilita tus DMs y vuelve a intentarlo.", ephemeral=True)
        return

    async def start_questionnaire(interaction_btn, guild):
        welcome_embed = discord.Embed(
            title="🎉 ¡Cuestionario de Verificación Iniciado! 🎉",
            description=(
                "Responde cada pregunta con claridad y seriedad. "
                "Tienes **3 minutos** por pregunta. ¡Buena suerte! 🍀"
            ),
            color=Colors.PRIMARY
        )
        welcome_embed.set_footer(text="Santiago RP | Verificación")
        welcome_embed.set_thumbnail(url=guild.icon.url if guild and guild.icon else None)

        await interaction_btn.user.send(embed=welcome_embed)

        def check(m):
            return m.author.id == interaction_btn.user.id and isinstance(m.channel, discord.DMChannel)

        for i, pregunta in enumerate(preguntas, 1):
            question_embed = discord.Embed(
                title=f"Pregunta {i}/{len(preguntas)}",
                description=pregunta,
                color=Colors.PRIMARY
            )
            question_embed.set_footer(text="Tiempo restante: 3 minutos")
            question_embed.set_thumbnail(url=guild.icon.url if guild and guild.icon else None)
            await interaction_btn.user.send(embed=question_embed)
            try:
                mensaje = await bot.wait_for('message', check=check, timeout=180)
                respuestas.append(mensaje.content)
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏰ ¡Tiempo Agotado!",
                    description="No respondiste a tiempo. Usa el botón de verificación para intentarlo de nuevo.",
                    color=Colors.WARNING
                )
                await interaction_btn.user.send(embed=timeout_embed)
                return

        embed = discord.Embed(
            title="📝 Nueva Solicitud de Verificación",
            description=f"**Usuario:** {interaction_btn.user.mention} ({interaction_btn.user.id})\n"
                        f"**Nombre en Roblox:** {respuestas[0]}",
            color=Colors.PRIMARY,
            timestamp=datetime.now()
        )
        for i, pregunta in enumerate(preguntas):
            embed.add_field(name=pregunta, value=respuestas[i] or "Sin respuesta", inline=False)
        embed.set_footer(text="Santiago RP | Sistema de Verificación")
        embed.set_thumbnail(url=guild.icon.url if guild and guild.icon else None)
        embed.set_author(name="SantiagoRP Verificación", icon_url=guild.icon.url if guild and guild.icon else None)

        view = VerificacionStaffView(interaction_btn.user, respuestas[0])
        
        canal_staff = guild.get_channel(1356740696798924951)
        if canal_staff:
            await canal_staff.send(embed=embed, view=view)
        else:
            await interaction_btn.user.send("⚠️ Error: No se encontró el canal de staff. Contacta a un administrador.")
            return

        completion_embed = discord.Embed(
            title="✅ ¡Solicitud Enviada!",
            description="Tu solicitud de verificación ha sido enviada al staff. "
                        "Recibirás una respuesta por DM en **24-48 horas**. ¡Gracias por tu paciencia!",
            color=Colors.SUCCESS
        )
        completion_embed.set_footer(text="Santiago RP | Verificación")
        await interaction_btn.user.send(embed=completion_embed)

class VerificacionStaffView(ui.View):
    def __init__(self, usuario, roblox_name):
        super().__init__(timeout=None)
        self.usuario = usuario
        self.roblox_name = roblox_name

    @ui.button(label="Aceptar", style=discord.ButtonStyle.success, emoji="✅")
    async def aceptar(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in Roles.STAFF for role in interaction.user.roles):
            await interaction.response.send_message("❌ Solo el staff puede usar este botón.", ephemeral=True)
            return
        modal = RazonStaffModal(self.usuario, self.roblox_name, True)
        await interaction.response.send_modal(modal)

    @ui.button(label="Denegar", style=discord.ButtonStyle.danger, emoji="❌")
    async def denegar(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in Roles.STAFF for role in interaction.user.roles):
            await interaction.response.send_message("❌ Solo el staff puede usar este botón.", ephemeral=True)
            return
        modal = RazonStaffModal(self.usuario, self.roblox_name, False)
        await interaction.response.send_modal(modal)

class RazonStaffModal(ui.Modal, title="Motivo de la Decisión"):
    razon = ui.TextInput(label="Motivo", required=True, style=discord.TextStyle.long)

    def __init__(self, usuario, roblox_name, aceptar):
        super().__init__()
        self.usuario = usuario
        self.roblox_name = roblox_name
        self.aceptar = aceptar

    async def on_submit(self, interaction: discord.Interaction):
        try:
            miembro = await interaction.guild.fetch_member(self.usuario.id)
        except Exception:
            await interaction.response.send_message("🚫 No se pudo encontrar al usuario.", ephemeral=True)
            return

        if self.aceptar:
            roles_a_agregar = [
                1339386615189209153, 1339386615189209150, 1339386615176630297,
                1360333071571878231, 1339386615159722121, 1339386615159722120
            ]
            for role_id in roles_a_agregar:
                rol = interaction.guild.get_role(role_id)
                if rol:
                    await miembro.add_roles(rol)
            rol_noverificado = interaction.guild.get_role(1339386615159722119)
            if rol_noverificado:
                await miembro.remove_roles(rol_noverificado)
            try:
                await miembro.edit(nick=f"{miembro.display_name} ({self.roblox_name})")
            except Exception:
                pass
            try:
                await miembro.send(
                    embed=discord.Embed(
                        title="✅ ¡Verificación Aceptada!",
                        description=f"¡Felicidades! Has sido verificado para rolear en SantiagoRP.\n\n**Motivo del staff:** {self.razon.value}",
                        color=Colors.SUCCESS,
                        timestamp=datetime.now()
                    ).set_footer(text="Santiago RP | Verificación")
                )
            except Exception:
                pass
            await interaction.response.send_message("✅ Usuario verificado y notificado por DM.", ephemeral=True)
        else:
            try:
                await self.usuario.send(
                    embed=discord.Embed(
                        title="❌ Verificación Denegada",
                        description=f"Tu verificación fue denegada por el staff.\n\n**Motivo:** {self.razon.value}",
                        color=Colors.DANGER,
                        timestamp=datetime.now()
                    ).set_footer(text="Santiago RP | Verificación")
                )
            except Exception:
                pass
            await interaction.response.send_message("❌ Usuario notificado de la denegación por DM.", ephemeral=True)

@bot.tree.command(name="panel-verificacion", description="Enviar panel de verificación (solo staff).")
async def panel_verificacion(interaction: discord.Interaction):
    if interaction.channel_id != 1339386615688335395:
        await interaction.response.send_message("❌ Solo puedes usar este comando en el canal de verificación.", ephemeral=True)
        return
    if not any(role.id in Roles.STAFF for role in interaction.user.roles):
        await interaction.response.send_message("❌ Solo el staff puede usar este comando.", ephemeral=True)
        return

    descripcion_panel = (
        "🌟 **¡Bienvenido al Sistema de Verificación de SantiagoRP!** 🌟\n\n"
        "Para unirte a nuestra comunidad de rol serio, completa el cuestionario de verificación. "
        "Responde con **honestidad y detalle** siguiendo las normativas del servidor.\n\n"
        "⏰ **Tiempo de respuesta**: 24-48 horas\n"
        "⚠️ **Advertencia**: El mal uso del sistema o respuestas inadecuadas pueden resultar en un **baneo** o suspensión.\n\n"
        "¡Demuestra tu compromiso y comienza tu aventura en SantiagoRP! 🚀"
    )
    embed = discord.Embed(
        title="🎮 Panel de Verificación",
        description=descripcion_panel,
        color=Colors.PRIMARY,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Santiago RP | Sistema de Verificación")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.set_author(name="SantiagoRP", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    view = ui.View()
    view.add_item(ui.Button(label="Verificarme", style=discord.ButtonStyle.primary, custom_id="verificarme_btn", emoji="✅"))

    async def verificarme_callback(interaction_btn: discord.Interaction):
        await iniciar_cuestionario_verificacion(interaction_btn, bot)

    view.children[0].callback = verificarme_callback

    await interaction.response.send_message(embed=embed, view=view)
    
@bot.tree.command(name="advertir-a", description="Advertir a un usuario sobre posibles sanciones.")
@app_commands.describe(
    usuario="Usuario a advertir",
    razon="Razón de la advertencia",
    prueba="URL de la prueba (opcional)"
)
async def advertir_a(interaction: discord.Interaction, usuario: discord.Member, razon: str, prueba: str = None):
    """Comando para advertir a un usuario sobre posibles sanciones."""
    if interaction.channel_id != 1358216083953291467:
        await interaction.response.send_message(
            "❌ Este comando solo puede usarse en el canal autorizado.", ephemeral=True
        )
        return

    staff_roles = set(Roles.STAFF)
    user_roles = set([role.id for role in interaction.user.roles])
    if not staff_roles.intersection(user_roles):
        await interaction.response.send_message(
            "❌ Solo el staff puede usar este comando.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    admin = interaction.user

    advertencia_embed = discord.Embed(
        title="⚠️ ¡Advertencia emitida!",
        description=(
            f"**👤 Usuario advertido:** {usuario.mention} ({usuario.id})\n"
            f"**🛡️ Staff:** {admin.mention} ({admin.id})\n"
            f"**📄 Razón:** {razon}\n"
            f"{f'**📎 Prueba:** {prueba}\n' if prueba else ''}"
            "\n\n🔔 **Recuerda:** Puedes recibir una sanción de los grados existentes (**Advertencia 1, 2, 3**), aislamiento o incluso un **baneo** si reincides o la falta es grave.\n"
            "Por favor, toma en serio esta advertencia y mejora tu comportamiento en el servidor."
        ),
        color=Colors.WARNING,
        timestamp=datetime.now()
    )
    advertencia_embed.set_footer(text="Santiago RP | Sistema de Advertencias")
    advertencia_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/564/564619.png")

    dm_ok = True
    try:
        await usuario.send(embed=advertencia_embed)
    except Exception as e:
        dm_ok = False

    await interaction.channel.send(embed=advertencia_embed)

    log_channel_id = 1367389708597858314
    log_channel = interaction.guild.get_channel(log_channel_id)
    if log_channel:
        await log_channel.send(embed=create_embed(
            title="Usuario Advertido",
            description=(
                                f"**Usuario:** {usuario.mention} ({usuario.id})\n"
                f"**Staff:** {admin.mention} ({admin.id})\n"
                f"**Razón:** {razon}\n"
                f"{f'**Prueba:** {prueba}\n' if prueba else ''}"
                f"**Notificado por DM:** {'Sí' if dm_ok else 'No'}"
            ),
            color=Colors.WARNING
        ))

    await interaction.followup.send(embed=create_embed(
        title="✅ Advertencia Enviada",
        description=f"Se ha advertido a {usuario.mention} correctamente.\n**Notificado por DM:** {'Sí' if dm_ok else 'No'}",
        color=Colors.SUCCESS
    ), ephemeral=True)

@bot.tree.command(name="sancionar", description="Sancionar a un usuario (solo staff).")
@app_commands.describe(
    usuario="Usuario a sancionar",
    tipo_sancion="Tipo de sanción (Advertencia 1, 2, 3)",
    razon="Razón de la sanción",
    prueba="URL de la prueba (opcional)"
)
@app_commands.autocomplete(tipo_sancion=sanction_type_autocomplete)
async def sancionar(interaction: discord.Interaction, usuario: discord.Member, tipo_sancion: str, razon: str, prueba: str = None):
    """Comando para sancionar a un usuario."""
    if not any(role.id in Roles.STAFF for role in interaction.user.roles):
        await interaction.response.send_message(embed=create_embed(
            title="❌ Acceso Denegado",
            description="Solo el staff puede usar este comando.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    if interaction.channel_id != Channels.SANCTIONS:
        await interaction.response.send_message(embed=create_embed(
            title="❌ Canal Incorrecto",
            description=f"Este comando solo puede usarse en <#{Channels.SANCTIONS}>.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    admin = interaction.user
    sanction_roles = {
        "Advertencia 1": Roles.WARN_1,
        "Advertencia 2": Roles.WARN_2,
        "Advertencia 3": Roles.WARN_3
    }
    
    role_id = sanction_roles.get(tipo_sancion)
    if not role_id:
        await interaction.followup.send(embed=create_embed(
            title="❌ Tipo de Sanción Inválido",
            description="Por favor, selecciona un tipo de sanción válido.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    try:
        sanction_id = save_sanction(
            user_id=usuario.id,
            username=usuario.display_name,
            reason=razon,
            sanction_type=tipo_sancion,
            proof_url=prueba,
            admin_id=admin.id,
            admin_name=admin.display_name
        )
        
        role = interaction.guild.get_role(role_id)
        if role:
            await usuario.add_roles(role)
        
        active_sanctions = count_active_sanctions(usuario.id)
        sanction_embed = create_embed(
            title="🚨 Nueva Sanción",
            description=(
                f"**Usuario:** {usuario.mention} ({usuario.id})\n"
                f"**Tipo de Sanción:** {tipo_sancion}\n"
                f"**Razón:** {razon}\n"
                f"{f'**Prueba:** {prueba}\n' if prueba else ''}"
                f"**Administrador:** {admin.mention}\n"
                f"**ID de Sanción:** `{sanction_id}`\n"
                f"**Sanciones Activas:** {active_sanctions}"
            ),
            color=Colors.DANGER,
            user=usuario
        )
        
        channel = bot.get_channel(Channels.SANCTION_LOGS)
        if channel:
            await channel.send(embed=sanction_embed)
        
        view_channel = bot.get_channel(Channels.VIEW_SANCTIONS)
        if view_channel:
            await view_channel.send(embed=sanction_embed)
        
        dm_sent = True
        try:
            await usuario.send(embed=create_embed(
                title="🚨 Has Recibido una Sanción",
                description=(
                    f"**Tipo de Sanción:** {tipo_sancion}\n"
                    f"**Razón:** {razon}\n"
                    f"{f'**Prueba:** {prueba}\n' if prueba else ''}"
                    f"**Administrador:** {admin.display_name}\n"
                    f"**Sanciones Activas:** {active_sanctions}\n\n"
                    "Si crees que esto es un error, apela en el canal correspondiente."
                ),
                color=Colors.DANGER
            ))
        except:
            dm_sent = False
        
        await interaction.followup.send(embed=create_embed(
            title="✅ Sanción Aplicada",
            description=f"Se ha sancionado a {usuario.mention} con {tipo_sancion}.\n**Notificado por DM:** {'Sí' if dm_sent else 'No'}",
            color=Colors.SUCCESS
        ), ephemeral=True)
        
    except Exception as e:
        print(f"Error al sancionar: {e}")
        await interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se pudo aplicar la sanción. Por favor, intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)

@bot.tree.command(name="revisar-sanciones", description="Revisar sanciones activas de un usuario.")
@app_commands.describe(usuario="Usuario cuyas sanciones deseas revisar")
async def revisar_sanciones(interaction: discord.Interaction, usuario: discord.Member):
    """Comando para revisar sanciones activas de un usuario."""
    try:
        sanctions = get_user_sanctions(usuario.id)
        if not sanctions:
            await interaction.response.send_message(embed=create_embed(
                title="✅ Sin Sanciones",
                description=f"{usuario.mention} no tiene sanciones activas.",
                color=Colors.SUCCESS
            ), ephemeral=True)
            return
        
        embed = create_embed(
            title=f"📜 Sanciones de {usuario.display_name}",
            description=f"**Usuario:** {usuario.mention}\n**Sanciones Activas:** {len(sanctions)}",
            color=Colors.WARNING
        )
        
        for sanction in sanctions[:25]:  # Discord embed field limit
            sanction_id, reason, sanction_type, proof_url, admin_name, date = sanction
            embed.add_field(
                name=f"Sanción: {sanction_type} ({sanction_id[:8]})",
                value=(
                    f"**Razón:** {reason}\n"
                    f"**Fecha:** {date}\n"
                    f"**Administrador:** {admin_name}\n"
                    f"{f'**Prueba:** {proof_url}' if proof_url else ''}"
                ),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"Error al revisar sanciones: {e}")
        await interaction.response.send_message(embed=create_embed(
            title="❌ Error",
            description="No se pudieron revisar las sanciones. Intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)

@bot.tree.command(name="borrar-sanciones", description="Borrar todas las sanciones activas de un usuario (solo staff).")
@app_commands.describe(usuario="Usuario cuyas sanciones deseas borrar")
async def borrar_sanciones(interaction: discord.Interaction, usuario: discord.Member):
    """Comando para borrar sanciones activas de un usuario."""
    if not any(role.id in Roles.STAFF for role in interaction.user.roles):
        await interaction.response.send_message(embed=create_embed(
            title="❌ Acceso Denegado",
            description="Solo el staff puede usar este comando.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    try:
        affected_rows = delete_user_sanctions(usuario.id)
        
        for role_id in [Roles.WARN_1, Roles.WARN_2, Roles.WARN_3, Roles.WARN_4, Roles.WARN_5]:
            role = interaction.guild.get_role(role_id)
            if role and role in usuario.roles:
                await usuario.remove_roles(role)
        
        log_channel = bot.get_channel(Channels.SANCTION_LOGS)
        if log_channel:
            await log_channel.send(embed=create_embed(
                title="🗑️ Sanciones Borradas",
                description=(
                    f"**Usuario:** {usuario.mention} ({usuario.id})\n"
                    f"**Sanciones Eliminadas:** {affected_rows}\n"
                    f"**Administrador:** {interaction.user.mention}"
                ),
                color=Colors.INFO
            ))
        
        await interaction.response.send_message(embed=create_embed(
            title="✅ Sanciones Borradas",
            description=f"Se han eliminado {affected_rows} sanciones activas de {usuario.mention}.",
            color=Colors.SUCCESS
        ), ephemeral=True)
        
    except Exception as e:
        print(f"Error al borrar sanciones: {e}")
        await interaction.response.send_message(embed=create_embed(
            title="❌ Error",
            description="No se pudieron borrar las sanciones. Intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)

@bot.tree.command(name="calificar", description="Calificar a un miembro del staff.")
@app_commands.describe(
    staff="Miembro del staff a calificar",
    calificacion="Calificación (1 a 5 estrellas)",
    comentario="Comentario sobre la calificación"
)
@app_commands.autocomplete(calificacion=rating_autocomplete)
@is_ratings_channel()
async def calificar(interaction: discord.Interaction, staff: discord.Member, calificacion: str, comentario: str):
    """Comando para calificar a un miembro del staff."""
    if not any(role.id in Roles.STAFF for role in staff.roles):
        await interaction.response.send_message(embed=create_embed(
            title="❌ Usuario Inválido",
            description="Solo puedes calificar a miembros del staff.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    try:
        rating = int(calificacion)
        if rating < 1 or rating > 5:
            await interaction.response.send_message(embed=create_embed(
                title="❌ Calificación Inválida",
                description="La calificación debe ser entre 1 y 5 estrellas.",
                color=Colors.DANGER
            ), ephemeral=True)
            return
        
        rating_id = save_rating(
            staff_id=staff.id,
            staff_name=staff.display_name,
            rating=rating,
            comment=comentario,
            user_id=interaction.user.id,
            user_name=interaction.user.display_name
        )
        
        embed = create_embed(
            title="🌟 Nueva Calificación",
            description=(
                f"**Staff:** {staff.mention} ({staff.id})\n"
                f"**Calificación:** {'🌟' * rating}\n"
                f"**Comentario:** {comentario}\n"
                f"**Usuario:** {interaction.user.mention}\n"
                f"**ID de Calificación:** `{rating_id}`"
            ),
            color=Colors.SUCCESS,
            user=staff
        )
        
        await interaction.response.send_message(embed=embed)
        
        log_channel = bot.get_channel(Channels.RATINGS)
        if log_channel:
            await log_channel.send(embed=embed)
        
    except ValueError:
        await interaction.response.send_message(embed=create_embed(
            title="❌ Calificación Inválida",
            description="Por favor, selecciona una calificación válida (1 a 5).",
            color=Colors.DANGER
        ), ephemeral=True)
    except Exception as e:
        print(f"Error al guardar calificación: {e}")
        await interaction.response.send_message(embed=create_embed(
            title="❌ Error",
            description="No se pudo guardar la calificación. Intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)

@bot.tree.command(name="mejor-staff", description="Ver el staff con la mejor calificación promedio.")
async def mejor_staff(interaction: discord.Interaction):
    """Comando para ver el staff con mejor promedio de calificación."""
    try:
        top_staff = get_top_staff()
        if not top_staff:
            await interaction.response.send_message(embed=create_embed(
                title="📊 Sin Resultados",
                description="No hay staff con suficientes calificaciones (mínimo 3).",
                color=Colors.INFO
            ), ephemeral=True)
            return
        
        staff_id, staff_name, avg_rating, count_rating = top_staff
        embed = create_embed(
            title="🏆 Mejor Staff",
            description=(
                f"**Staff:** {staff_name} (<@{staff_id}>)\n"
                f"**Promedio:** {avg_rating:.2f}/5\n"
                f"**Calificaciones:** {count_rating}"
            ),
            color=Colors.SUCCESS
        )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        print(f"Error al obtener mejor staff: {e}")
        await interaction.response.send_message(embed=create_embed(
            title="❌ Error",
            description="No se pudo obtener el mejor staff. Intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)

@bot.tree.command(name="limpiar-calificaciones", description="Borrar todas las calificaciones (solo staff).")
async def limpiar_calificaciones(interaction: discord.Interaction):
    """Comando para borrar todas las calificaciones."""
    if not any(role.id in Roles.STAFF for role in interaction.user.roles):
        await interaction.response.send_message(embed=create_embed(
            title="❌ Acceso Denegado",
            description="Solo el staff puede usar este comando.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    try:
        clear_ratings()
        await interaction.response.send_message(embed=create_embed(
            title="🗑️ Calificaciones Borradas",
            description="Se han eliminado todas las calificaciones.",
            color=Colors.SUCCESS
        ), ephemeral=True)
        
        log_channel = bot.get_channel(Channels.LOGS)
        if log_channel:
            await log_channel.send(embed=create_embed(
                title="🗑️ Calificaciones Borradas",
                description=f"**Administrador:** {interaction.user.mention}",
                color=Colors.INFO
            ))
        
    except Exception as e:
        print(f"Error al borrar calificaciones: {e}")
        await interaction.response.send_message(embed=create_embed(
            title="❌ Error",
            description="No se pudieron borrar las calificaciones. Intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)

@bot.tree.command(name="postular-trabajo", description="Solicitar un trabajo en el servidor.")
@app_commands.describe(
    roblox_username="Tu nombre de usuario en Roblox",
    trabajo="El trabajo al que deseas postular",
    experiencia="Tu experiencia previa en el rol o trabajos similares",
    disponibilidad="Tu disponibilidad horaria (en UTC)",
    razon="Por qué quieres este trabajo"
)
async def postular_trabajo(interaction: discord.Interaction, roblox_username: str, trabajo: str, experiencia: str, disponibilidad: str, razon: str):
    """Comando para postular a un trabajo en el servidor."""
    if interaction.channel_id != Channels.JOB_APPLICATIONS:
        await interaction.response.send_message(embed=create_embed(
            title="❌ Canal Incorrecto",
            description=f"Este comando solo puede usarse en <#{Channels.JOB_APPLICATIONS}>.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    job_options = {job["name"].lower(): job for job in JOB_ROLES.values()}
    selected_job = None
    for job_name, job_data in job_options.items():
        if trabajo.lower() in job_name.lower():
            selected_job = job_data
            break
    
    if not selected_job:
        await interaction.followup.send(embed=create_embed(
            title="❌ Trabajo Inválido",
            description="El trabajo especificado no es válido. Usa el autocompletado para seleccionar un trabajo.",
            color=Colors.DANGER
        ), ephemeral=True)
        return
    
    try:
        embed = create_embed(
            title="💼 Nueva Postulación de Trabajo",
            description=(
                f"**Usuario:** {interaction.user.mention} ({interaction.user.id})\n"
                f"**Nombre en Roblox:** {roblox_username}\n"
                f"**Trabajo:** {selected_job['name']}\n"
                f"**Experiencia:** {experiencia}\n"
                f"**Disponibilidad:** {disponibilidad}\n"
                f"**Razón:** {razon}"
            ),
            color=Colors.INFO,
            user=interaction.user
        )
        
        review_channel = bot.get_channel(Channels.JOB_REVIEW)
        if not review_channel:
            await interaction.followup.send(embed=create_embed(
                title="❌ Error",
                description="No se encontró el canal de revisión de postulaciones.",
                color=Colors.DANGER
            ), ephemeral=True)
            return
        
        view = JobApplicationView(interaction.user, roblox_username, selected_job)
        await review_channel.send(embed=embed, view=view)
        
        await interaction.followup.send(embed=create_embed(
            title="✅ Postulación Enviada",
            description="Tu postulación ha sido enviada al staff para revisión. Recibirás una respuesta pronto.",
            color=Colors.SUCCESS
        ), ephemeral=True)
        
    except Exception as e:
        print(f"Error al enviar postulación: {e}")
        await interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se pudo enviar la postulación. Intenta de nuevo.",
            color=Colors.DANGER
        ), ephemeral=True)

# Vista para manejar aceptación/rechazo de postulaciones
class JobApplicationView(ui.View):
    def __init__(self, user: discord.Member, roblox_username: str, job: dict):
        super().__init__(timeout=None)
        self.user = user
        self.roblox_username = roblox_username
        self.job = job
    
    @ui.button(label="Aceptar", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_button(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in Roles.STAFF for role in interaction.user.roles):
            await interaction.response.send_message(embed=create_embed(
                title="❌ Acceso Denegado",
                description="Solo el staff puede usar este botón.",
                color=Colors.DANGER
            ), ephemeral=True)
            return
        
        try:
            member = await interaction.guild.fetch_member(self.user.id)
            role = interaction.guild.get_role(self.job["role_id"])
            salary_role = interaction.guild.get_role(Roles.SUELDO)
            if role and member:
                await member.add_roles(role)
            if salary_role and member:
                await member.add_roles(salary_role)
            
            await member.edit(nick=f"{self.roblox_username} | {self.job['name']}")
            
            dm_sent = True
            try:
                await member.send(embed=create_embed(
                    title="✅ Postulación Aceptada",
                    description=f"¡Felicidades! Has sido aceptado para el trabajo de **{self.job['name']}**.",
                    color=Colors.SUCCESS
                ))
            except:
                dm_sent = False
            
            log_channel = bot.get_channel(Channels.JOB_LOGS)
            if log_channel:
                await log_channel.send(embed=create_embed(
                    title="💼 Postulación Aceptada",
                    description=(
                        f"**Usuario:** {member.mention} ({member.id})\n"
                        f"**Trabajo:** {self.job['name']}\n"
                        f"**Aprobado por:** {interaction.user.mention}\n"
                        f"**Notificado por DM:** {'Sí' if dm_sent else 'No'}"
                    ),
                    color=Colors.SUCCESS
                ))
            
            await interaction.response.send_message(embed=create_embed(
                title="✅ Postulación Aceptada",
                description=f"Se ha aceptado la postulación de {member.mention} para **{self.job['name']}**.",
                color=Colors.SUCCESS
            ), ephemeral=True)
            
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)
            
        except Exception as e:
            print(f"Error al aceptar postulación: {e}")
            await interaction.response.send_message(embed=create_embed(
                title="❌ Error",
                description="No se pudo aceptar la postulación. Intenta de nuevo.",
                color=Colors.DANGER
            ), ephemeral=True)
    
    @ui.button(label="Rechazar", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject_button(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in Roles.STAFF for role in interaction.user.roles):
            await interaction.response.send_message(embed=create_embed(
                title="❌ Acceso Denegado",
                description="Solo el staff puede usar este botón.",
                color=Colors.DANGER
            ), ephemeral=True)
            return
        
        modal = JobRejectionModal(self.user, self.job)
        await interaction.response.send_modal(modal)

# Modal para rechazar postulaciones
class JobRejectionModal(ui.Modal, title="Rechazar Postulación"):
    reason = ui.TextInput(
        label="Razón del Rechazo",
        placeholder="Explica por qué se rechaza la postulación...",
        style=discord.TextStyle.long,
        required=True
    )
    
    def __init__(self, user: discord.Member, job: dict):
        super().__init__()
        self.user = user
        self.job = job
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = await interaction.guild.fetch_member(self.user.id)
            
            dm_sent = True
            try:
                await member.send(embed=create_embed(
                    title="❌ Postulación Rechazada",
                    description=(
                        f"Tu postulación para el trabajo de **{self.job['name']}** ha sido rechazada.\n"
                        f"**Razón:** {self.reason.value}"
                    ),
                    color=Colors.DANGER
                ))
            except:
                dm_sent = False
            
            log_channel = bot.get_channel(Channels.JOB_LOGS)
            if log_channel:
                await log_channel.send(embed=create_embed(
                    title="❌ Postulación Rechazada",
                    description=(
                        f"**Usuario:** {member.mention} ({member.id})\n"
                        f"**Trabajo:** {self.job['name']}\n"
                        f"**Razón:** {self.reason.value}\n"
                        f"**Rechazado por:** {interaction.user.mention}\n"
                        f"**Notificado por DM:** {'Sí' if dm_sent else 'No'}"
                    ),
                    color=Colors.DANGER
                ))
            
            await interaction.response.send_message(embed=create_embed(
                title="❌ Postulación Rechazada",
                description=f"Se ha rechazado la postulación de {member.mention} para **{self.job['name']}**.",
                color=Colors.DANGER
            ), ephemeral=True)
            
            view = interaction.message.components[0]
            for child in view.children:
                child.disabled = True
            await interaction.message.edit(view=view)
            
        except Exception as e:
            print(f"Error al rechazar postulación: {e}")
            await interaction.response.send_message(embed=create_embed(
                title="❌ Error",
                description="No se pudo rechazar la postulación. Intenta de nuevo.",
                color=Colors.DANGER
            ), ephemeral=True)

# Autocompletado para trabajos
async def job_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocompletar trabajos disponibles."""
    return [
        app_commands.Choice(name=job["name"], value=job["name"])
        for job in JOB_ROLES.values()
        if current.lower() in job["name"].lower()
    ]

# Registrar autocompletado para postular-trabajo
bot.tree.command(name="postular-trabajo")._params["trabajo"].autocomplete = job_autocomplete

@bot.event
async def on_ready():
    """Evento que se ejecuta cuando el bot está listo."""
    print(f"✅ Bot conectado como {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")
    
    # Enviar panel de control
    channel = bot.get_channel(Channels.CONTROL_PANEL)
    if channel:
        embed = create_embed(
            title="🛠️ Panel de Control Administrativo",
            description="Utiliza los botones a continuación para gestionar el servidor.",
            color=Colors.PRIMARY
        )
        view = ControlPanelView()
        try:
            await channel.purge(limit=10)
            await channel.send(embed=embed, view=view)
        except Exception as e:
            print(f"Error al enviar panel de control: {e}")
    
    # Enviar panel de tickets
    ticket_channel = bot.get_channel(Channels.TICKETS)
    if ticket_channel:
        embed = create_embed(
            title="🎟️ Sistema de Tickets",
            description=(
                "🌟 **¡Bienvenido al Sistema de Tickets de Santiago RP!** 🌟\n\n"
                "Utiliza el menú desplegable para seleccionar el tipo de ticket que necesitas.\n"
                "🚨 **Advertencia:** Abrir tickets sin motivo válido resultará en **sanciones**.\n\n"
                "📌 **Pasos:**\n"
                "1. Selecciona una categoría.\n"
                "2. Completa el formulario con información clara.\n"
                "3. Espera la respuesta de nuestro equipo.\n\n"
                "¡Gracias por ser parte de nuestra comunidad! 🙌"
            ),
            color=Colors.PRIMARY
        )
        view = TicketCreationView()
        try:
            await ticket_channel.purge(limit=10)
            await ticket_channel.send(embed=embed, view=view)
        except Exception as e:
            print(f"Error al enviar panel de tickets: {e}")

# Iniciar el bot
if __name__ == "__main__":
    bot.run(TOKEN)
