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
import asyncio

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuración del bot con intenciones
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# =============================================
# BASE DE DATOS
# =============================================
def init_db():
    """Inicializar la base de datos SQLite para sanciones y calificaciones."""
    print("Inicializando base de datos 'adminsantiagoRP.db'...")
    try:
        conn = sqlite3.connect('adminsantiagoRP.db')
        c = conn.cursor()
        # Tabla de sanciones
        c.execute('''
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
                active BOOLEAN
            )
        ''')
        # Tabla de calificaciones
        c.execute('''
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
    SANCTION_LOGS = 1364100682990354516
    VIEW_SANCTIONS = 1344075561689026722
    RATINGS = 1339386616405561398  

class Roles:
    STAFF = [1339386615247798362, 1346545514492985486, 1339386615222767662, 1347803116741066834, 1339386615235346439]
    WARN_1 = 1341459151913746503
    WARN_2 = 1341459663232696416
    WARN_3 = 1341459796846579834
    WARN_4 = 1358226550046326895
    WARN_5 = 1358226564629926060

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
    date = datetime.now().isoformat()
    try:
        conn = sqlite3.connect('adminsantiagoRP.db')
        c = conn.cursor()
        # Verificar si la tabla sanciones existe, y crearla si no
        c.execute('''
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
                active BOOLEAN
            )
        ''')
        # Insertar la sanción
        c.execute('''
            INSERT INTO sanciones (sanction_id, user_id, username, reason, sanction_type, proof_url, admin_id, admin_name, date, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sanction_id, user_id, username, reason, sanction_type, proof_url, admin_id, admin_name, date, True))
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
        conn = sqlite3.connect('adminsantiagoRP.db')
        c = conn.cursor()
        # Verificar si la tabla sanciones existe
        c.execute('''
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
                active BOOLEAN
            )
        ''')
        c.execute('SELECT COUNT(*) FROM sanciones WHERE user_id = ? AND active = ?', (user_id, True))
        count = c.fetchone()[0]
        conn.close()
        return count
    except sqlite3.Error as e:
        print(f"Error al contar sanciones: {e}")
        raise

def get_user_sanctions(user_id: int) -> list:
    """Obtener todas las sanciones activas de un usuario."""
    try:
        conn = sqlite3.connect('adminsantiagoRP.db')
        c = conn.cursor()
        # Verificar si la tabla sanciones existe
        c.execute('''
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
                active BOOLEAN
            )
        ''')
        c.execute('''
            SELECT sanction_id, reason, sanction_type, proof_url, admin_name, date
            FROM sanciones
            WHERE user_id = ? AND active = ?
            ORDER BY date DESC
        ''', (user_id, True))
        sanctions = c.fetchall()
        conn.close()
        return sanctions
    except sqlite3.Error as e:
        print(f"Error al obtener sanciones: {e}")
        raise

def delete_user_sanctions(user_id: int) -> int:
    """Marcar todas las sanciones activas de un usuario como inactivas."""
    try:
        conn = sqlite3.connect('adminsantiagoRP.db')
        c = conn.cursor()
        # Verificar si la tabla sanciones existe
        c.execute('''
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
                active BOOLEAN
            )
        ''')
        c.execute('UPDATE sanciones SET active = ? WHERE user_id = ? AND active = ?', (False, user_id, True))
        affected_rows = conn.total_changes
        conn.commit()
        conn.close()
        return affected_rows
    except sqlite3.Error as e:
        print(f"Error al borrar sanciones: {e}")
        raise

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
    date = datetime.now().isoformat()
    conn = sqlite3.connect('adminsantiagoRP.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO calificaciones (rating_id, staff_id, staff_name, rating, comment, user_id, user_name, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (rating_id, staff_id, staff_name, rating, comment, user_id, user_name, date))
    conn.commit()
    conn.close()
    return rating_id

def get_top_staff() -> tuple:
    """Obtener el staff con mejor promedio de calificación (mínimo 3 calificaciones)."""
    conn = sqlite3.connect('adminsantiagoRP.db')
    c = conn.cursor()
    c.execute('''
        SELECT staff_id, staff_name, AVG(rating), COUNT(rating)
        FROM calificaciones
        GROUP BY staff_id
        HAVING COUNT(rating) >= 3
        ORDER BY AVG(rating) DESC
        LIMIT 1
    ''')
    result = c.fetchone()
    conn.close()
    return result  # (staff_id, staff_name, avg_rating, count)

def clear_ratings():
    """Borrar todas las calificaciones de la base de datos."""
    conn = sqlite3.connect('adminsantiagoRP.db')
    c = conn.cursor()
    c.execute('DELETE FROM calificaciones')
    conn.commit()
    conn.close()

# =============================================
# AUTOCOMPLETE
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
        await channel.purge(limit=3)  # Reducido de 5 a 3
        message = await channel.send(embed=embed)
        
        # Enviar dos mensajes de mención con @everyone
        mention1 = await channel.send("@everyone")
        mention2 = await channel.send("@everyone")
        
        # Programar eliminación de los mensajes de mención después de 30 segundos
        await asyncio.sleep(30)
        await mention1.delete()
        await mention2.delete()
        
        log_embed = create_embed(
            title="📢 Servidor Abierto",
            description=f"Acción realizada por {interaction.user.mention}",
            color=embed.color,
            user=interaction.user
        )
        
        log_channel = bot.get_channel(Channels.LOGS)
        await log_channel.send(embed=log_embed)
        print(f"✅ Anuncio enviado al canal {Channels.ANNOUNCEMENTS}")
        print(f"✅ Log enviado al canal {Channels.LOGS}")
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
    
    # Mostrar modal para la razón del cierre
    modal = CloseServerModal()
    await interaction.response.send_modal(modal)
    
    timed_out = await modal.wait()
    if timed_out:
        return
    
    server_status = "cerrado"
    reason = modal.reason.value
    
    # Crear embed moderno y atractivo
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
        await channel.purge(limit=3)  # Reducido de 5 a 3
        message = await channel.send(embed=embed)
        await message.add_reaction("😔")  # Añadir reacción para interacción
        
        # Enviar dos mensajes de mención con @everyone
        mention1 = await channel.send("@everyone")
        mention2 = await channel.send("@everyone")
        
        # Programar eliminación de los mensajes de mención después de 30 segundos
        await asyncio.sleep(30)
        await mention1.delete()
        await mention2.delete()
        
        log_embed = create_embed(
            title="📢 Servidor Cerrado",
            description=f"Acción realizada por {interaction.user.mention}\n**Razón:** {reason}",
            color=embed.color,
            user=interaction.user
        )
        
        log_channel = bot.get_channel(Channels.LOGS)
        await log_channel.send(embed=log_embed)
        print(f"✅ Anuncio enviado al canal {Channels.ANNOUNCEMENTS}")
        print(f"✅ Log enviado al canal {Channels.LOGS}")
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
        await channel.purge(limit=3)  # Reducido de 5 a 3
        message = await channel.send(embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        
        # Enviar dos mensajes de mención con @everyone
        mention1 = await channel.send("@everyone")
        mention2 = await channel.send("@everyone")
        
        # Programar eliminación de los mensajes de mención después de 30 segundos
        await asyncio.sleep(30)
        await mention1.delete()
        await mention2.delete()
        
        log_embed = create_embed(
            title="📢 Votación Iniciada",
            description=f"Acción realizada por {interaction.user.mention}",
            color=embed.color,
            user=interaction.user
        )
        
        log_channel = bot.get_channel(Channels.LOGS)
        await log_channel.send(embed=log_embed)
        print(f"✅ Anuncio enviado al canal {Channels.ANNOUNCEMENTS}")
        print(f"✅ Log enviado al canal {Channels.LOGS}")
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
@bot.event
async def on_ready():
    """Evento que se ejecuta cuando el bot está listo."""
    print(f'✨ {bot.user.name} está listo!')
    
    try:
        # Sincronizar comandos
        synced = await bot.tree.sync()
        print(f"🔁 Comandos sincronizados: {', '.join([cmd.name for cmd in synced])}")
        
        # Calcular el número de miembros sin bots
        guild = bot.get_guild(1357151555706683473)  # Reemplaza con el ID de tu servidor
        if guild:
            member_count = sum(1 for member in guild.members if not member.bot)
            # Establecer actividad personalizada
            activity = discord.Activity(
                type=discord.ActivityType.playing,
                name=f"🌟 Creado por Smile | SantiagoRP | 👥 {member_count} Miembros"
            )
            await bot.change_presence(activity=activity)
            print(f"🎮 Actividad establecida: {activity.name}")
        else:
            print("❌ No se encontró el servidor. Verifica el ID del servidor.")
            
    except Exception as e:
        print(f"❌ Error en on_ready: {e}")

@bot.tree.command(name="panel", description="Despliega el panel de control administrativo")
@app_commands.checks.has_any_role(*Roles.STAFF)
async def control_panel(interaction: discord.Interaction):
    """Comando para mostrar el panel de control."""
    embed = create_embed(
        title="⚙️ Panel de Control Santiago RP",
        description="Gestiona el servidor con las siguientes opciones:",
        color=Colors.PRIMARY,
        user=interaction.user
    )
    embed.add_field(name="🚀 Abrir Servidor", value="Abre el servidor para todos los jugadores.", inline=True)
    embed.add_field(name="🗳️ Iniciar Votación", value="Inicia una votación para abrir el servidor.", inline=True)
    embed.add_field(name="🔒 Cerrar Servidor", value="Cierra el servidor y notifica a los jugadores.", inline=True)
    
    await interaction.response.send_message(embed=embed, view=ControlPanelView())

def is_tickets_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel_id != Channels.TICKETS:
            await interaction.response.send_message(embed=create_embed(
                title="❌ Canal Incorrecto",
                description=f"Este comando solo puede usarse en <#{Channels.TICKETS}>.",
                color=Colors.DANGER
            ), ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

@bot.tree.command(name="tickets", description="Abre el sistema de tickets interactivo")
@is_tickets_channel()
async def setup_tickets(interaction: discord.Interaction):
    """Comando para configurar el sistema de tickets."""
    embed = create_embed(
        title="🎫 Sistema de Tickets Santiago RP",
        description=(
            "¡Bienvenido al sistema de tickets de **Santiago RP**! 🎉\n"
            "Selecciona la categoría que mejor se ajuste a tu necesidad usando el menú desplegable.\n\n"
            "**⚠️ IMPORTANTE:**\n"
            "- Asegúrate de abrir tickets con un motivo válido.\n"
            "- Los tickets sin justificación pueden resultar en **sanciones**.\n"
            "- Lee las reglas del servidor antes de crear un ticket."
        ),
        color=Colors.INFO,
        user=interaction.user
    )
    
    embed.add_field(
        name="🧩 Asistencia General",
        value=(
            "🔹 **Ayuda General**: Resuelve dudas o problemas generales.\n"
            "🔹 **Dudas**: Consulta sobre reglas o mecánicas del servidor."
        ),
        inline=False
    )
    embed.add_field(
        name="🏛️ Trámites Oficiales",
        value=(
            "🔹 **Municipalidad**: Licencias, propiedades, registros.\n"
            "🔹 **Creación Empresa**: Solicita crear una empresa legal.\n"
            "🔹 **Facción Ilegal**: Registro de facciones ilegales."
        ),
        inline=False
    )
    embed.add_field(
        name="⚠️ Reportes y Reclamos",
        value=(
            "🔹 **Compras**: Problemas con paquetes VIP o compras.\n"
            "🔹 **Beneficios**: Reclamos de beneficios especiales.\n"
            "🔹 **Reportes**: Denuncia jugadores o bugs.\n"
            "🔹 **Reclamo Robo**: Reporta pérdidas por robos.\n"
            "🔹 **Apelaciones**: Apela sanciones o baneos."
        ),
        inline=False
    )
    embed.add_field(
        name="🤝 Otros Servicios",
        value=(
            "🔹 **Alianzas**: Solicita alianzas entre facciones.\n"
            "🔹 **Solicitud CK**: Pide un Character Kill (muerte permanente)."
        ),
        inline=False
    )
    
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else "")
    embed.set_footer(text="Santiago RP | Sistema Automatizado | Creado por Smile")
    
    await interaction.response.send_message(embed=embed, view=TicketCreationView())

def is_sanctions_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel_id != Channels.SANCTIONS:
            await interaction.response.send_message(embed=create_embed(
                title="❌ Canal Incorrecto",
                description=f"Este comando solo puede usarse en <#{Channels.SANCTIONS}>.",
                color=Colors.DANGER
            ), ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

@bot.tree.command(name="sancionar-a", description="Aplica una sanción a un usuario")
@app_commands.checks.has_any_role(*Roles.STAFF)
@is_sanctions_channel()
@app_commands.autocomplete(tipo_sancion=sanction_type_autocomplete)
@app_commands.describe(
    usuario="Selecciona el usuario a sancionar",
    motivo="Explica por qué se sanciona al usuario",
    tipo_sancion="Elige el tipo de sanción (Advertencia 1, 2 o 3)",
    pruebas="Enlace a las pruebas de la sanción (ej. https://imgur.com/abc)"
)
async def sancionar_a(interaction: discord.Interaction, usuario: discord.Member, motivo: str, tipo_sancion: str, pruebas: str):
    """Comando para sancionar a un usuario."""
    await interaction.response.defer()

    # Validar tipo de sanción
    sanction_roles = {
        "Advertencia 1": Roles.WARN_1,
        "Advertencia 2": Roles.WARN_2,
        "Advertencia 3": Roles.WARN_3
    }
    
    if tipo_sancion not in sanction_roles:
        return await interaction.followup.send(embed=create_embed(
            title="❌ Tipo de Sanción Inválido",
            description="Por favor, selecciona un tipo de sanción válido (Advertencia 1, Advertencia 2, Advertencia 3).",
            color=Colors.DANGER
        ))

    # Guardar sanción en la base de datos
    sanction_id = save_sanction(
        user_id=usuario.id,
        username=usuario.name,
        reason=motivo,
        sanction_type=tipo_sancion,
        proof_url=pruebas,
        admin_id=interaction.user.id,
        admin_name=interaction.user.name
    )

    # Asignar rol correspondiente
    role_id = sanction_roles[tipo_sancion]
    role = interaction.guild.get_role(role_id)
    try:
        await usuario.add_roles(role, reason=f"Sanción {tipo_sancion} aplicada por {interaction.user.name}")
    except Exception as e:
        print(f"Error al asignar rol: {e}")
        await interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se pudo asignar el rol de sanción. Por favor, verifica los permisos del bot.",
            color=Colors.DANGER
        ))
        return

    # Verificar cantidad de sanciones para ban automático
    sanction_count = count_active_sanctions(usuario.id)
    is_banned = False
    ban_reason = None

    if sanction_count >= 3:
        try:
            ban_reason = f"Acumulación de {sanction_count} sanciones activas"
            await interaction.guild.ban(
                usuario,
                reason=ban_reason,
                delete_message_days=0
            )
            is_banned = True
            # Programar desbaneo automático después de 7 días
            await asyncio.sleep(7 * 24 * 60 * 60)  # 7 días en segundos
            await interaction.guild.unban(usuario, reason="Fin de baneo temporal por acumulación de sanciones")
        except Exception as e:
            print(f"Error al banear usuario: {e}")
            await interaction.followup.send(embed=create_embed(
                title="❌ Error",
                description="No se pudo aplicar el baneo automático. Por favor, verifica los permisos del bot.",
                color=Colors.DANGER
            ))
        return

    # Crear embed para respuesta en el canal
    sanction_embed = create_embed(
        title="⚖️ Sanción Aplicada",
        description=f"Se ha sancionado a {usuario.mention} con éxito.",
        color=Colors.DANGER,
        user=interaction.user
    )
    sanction_embed.add_field(name="🆔 ID de Sanción", value=sanction_id, inline=False)
    sanction_embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
    sanction_embed.add_field(name="📝 Motivo", value=motivo, inline=True)
    sanction_embed.add_field(name="⚠️ Tipo de Sanción", value=tipo_sancion, inline=True)
    sanction_embed.add_field(name="📸 Pruebas", value=pruebas, inline=False)
    sanction_embed.add_field(name="👮 Aplicada por", value=interaction.user.mention, inline=True)
    if is_banned:
        sanction_embed.add_field(name="🚫 Baneo Temporal", value="7 días por acumulación de sanciones", inline=False)

    await interaction.followup.send(embed=sanction_embed)

    # Enviar notificación al usuario sancionado
    dm_embed = create_embed(
        title="⚖️ Has Recibido una Sanción",
        description=(
            f"Has sido sancionado en **Santiago RP**. Aquí están los detalles:\n\n"
            f"**🆔 ID de Sanción:** {sanction_id}\n"
            f"**📝 Motivo:** {motivo}\n"
            f"**⚠️ Tipo de Sanción:** {tipo_sancion}\n"
            f"**📸 Pruebas:** {pruebas}\n"
            f"**👮 Aplicada por:** {interaction.user.mention}\n"
        ),
        color=Colors.DANGER
    )
    if is_banned:
        dm_embed.add_field(
            name="🚫 Baneo Temporal",
            value="Has sido baneado temporalmente por 7 días debido a la acumulación de sanciones.",
            inline=False
        )
    dm_embed.add_field(
        name="📜 ¿Cómo apelar?",
        value=(
            f"Puedes apelar esta sanción abriendo un ticket en <#{Channels.TICKETS}> seleccionando la categoría **Apelaciones**. "
            f"Asegúrate de incluir el **ID de Sanción** ({sanction_id}) y pruebas que respalden tu caso."
        ),
        inline=False
    )

    try:
        await usuario.send(embed=dm_embed)
    except discord.errors.Forbidden:
        await interaction.followup.send(embed=create_embed(
            title="⚠️ Advertencia",
            description=f"No se pudo enviar el mensaje directo a {usuario.mention}. Es posible que tenga los DMs cerrados.",
            color=Colors.WARNING
        ))

    # Enviar log al canal de sanciones
    log_channel = bot.get_channel(Channels.SANCTION_LOGS)
    if log_channel:
        log_embed = create_embed(
            title="📜 Registro de Sanción",
            description=f"Se ha registrado una nueva sanción en el servidor.",
            color=Colors.DANGER,
            user=interaction.user
        )
        log_embed.add_field(name="🆔 ID de Sanción", value=sanction_id, inline=False)
        log_embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
        log_embed.add_field(name="📝 Motivo", value=motivo, inline=True)
        log_embed.add_field(name="⚠️ Tipo de Sanción", value=tipo_sancion, inline=True)
        log_embed.add_field(name="📸 Pruebas", value=pruebas, inline=False)
        log_embed.add_field(name="👮 Aplicada por", value=interaction.user.mention, inline=True)
        if is_banned:
            log_embed.add_field(name="🚫 Baneo Temporal", value="7 días por acumulación de sanciones", inline=False)
        
        await log_channel.send(embed=log_embed)

def is_view_sanctions_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel_id != Channels.VIEW_SANCTIONS:
            await interaction.response.send_message(embed=create_embed(
                title="❌ Canal Incorrecto",
                description=f"Este comando solo puede usarse en <#{Channels.VIEW_SANCTIONS}>.",
                color=Colors.DANGER
            ), ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

@bot.tree.command(name="ver-sanciones", description="Muestra las sanciones activas de un usuario")
@is_view_sanctions_channel()
@app_commands.describe(
    usuario="Selecciona un usuario para ver sus sanciones (opcional, por defecto muestra las tuyas)"
)
async def ver_sanciones(interaction: discord.Interaction, usuario: discord.Member = None):
    """Comando para ver las sanciones activas de un usuario."""
    await interaction.response.defer(ephemeral=True)

    # Si no se especifica un usuario, usar el que ejecuta el comando
    target_user = usuario if usuario else interaction.user

    # Obtener sanciones del usuario
    sanctions = get_user_sanctions(target_user.id)

    # Crear embed para mostrar sanciones
    embed = create_embed(
        title="📜 Sanciones Activas",
        description=f"Lista de sanciones activas para {target_user.mention}.",
        color=Colors.INFO,
        user=target_user
    )

    if not sanctions:
        embed.add_field(
            name="✅ Sin Sanciones",
            value="Este usuario no tiene sanciones activas actualmente.",
            inline=False
        )
    else:
        for sanction in sanctions:
            sanction_id, reason, sanction_type, proof_url, admin_name, date = sanction
            embed.add_field(
                name=f"🆔 Sanción {sanction_id[:8]}...",
                value=(
                    f"**Motivo:** {reason}\n"
                    f"**Tipo:** {sanction_type}\n"
                    f"**Pruebas:** {proof_url}\n"
                    f"**Aplicada por:** {admin_name}\n"
                    f"**Fecha:** {datetime.fromisoformat(date).strftime('%d/%m/%Y %H:%M')}"
                ),
                inline=False
            )

    embed.add_field(
        name="📝 ¿Tienes una sanción injusta?",
        value=(
            f"Si crees que alguna sanción es injusta, abre un ticket en <#{Channels.TICKETS}> "
            "seleccionando la categoría **Apelaciones**. Incluye el **ID de Sanción** y pruebas que respalden tu caso."
        ),
        inline=False
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="borrar-sanciones", description="Borra todas las sanciones activas de un usuario")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    usuario="Selecciona el usuario cuyas sanciones quieres borrar"
)
async def borrar_sanciones(interaction: discord.Interaction, usuario: discord.Member):
    """Comando para borrar todas las sanciones activas de un usuario."""
    await interaction.response.defer(ephemeral=True)

    # Contar sanciones activas antes de borrar
    sanction_count = count_active_sanctions(usuario.id)
    if sanction_count == 0:
        await interaction.followup.send(embed=create_embed(
            title="ℹ️ Sin Sanciones",
            description=f"{usuario.mention} no tiene sanciones activas para borrar.",
            color=Colors.INFO,
            user=interaction.user
        ), ephemeral=True)
        return

    # Marcar sanciones como inactivas
    try:
        affected_rows = delete_user_sanctions(usuario.id)
    except Exception as e:
        print(f"Error al borrar sanciones: {e}")
        await interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se pudieron borrar las sanciones. Por favor, intenta de nuevo o contacta a soporte técnico.",
            color=Colors.DANGER,
            user=interaction.user
        ), ephemeral=True)
        return

    # Verificar si se borraron sanciones
    if affected_rows == 0:
        await interaction.followup.send(embed=create_embed(
            title="ℹ️ Sin Cambios",
            description=f"No se encontraron sanciones activas para {usuario.mention}.",
            color=Colors.INFO,
            user=interaction.user
        ), ephemeral=True)
        return

    # Remover roles de advertencia del usuario
    sanction_roles = [Roles.WARN_1, Roles.WARN_2, Roles.WARN_3]
    roles_to_remove = [interaction.guild.get_role(role_id) for role_id in sanction_roles if interaction.guild.get_role(role_id)]
    try:
        await usuario.remove_roles(*roles_to_remove, reason=f"Sanciones borradas por {interaction.user.name}")
    except Exception as e:
        print(f"Error al remover roles: {e}")
        await interaction.followup.send(embed=create_embed(
            title="⚠️ Advertencia",
            description=f"Las sanciones de {usuario.mention} fueron borradas, pero no se pudieron remover los roles de advertencia. Por favor, verifica los permisos del bot.",
            color=Colors.WARNING,
            user=interaction.user
        ), ephemeral=True)
        return

    # Enviar respuesta al administrador
    response_embed = create_embed(
        title="✅ Sanciones Borradas",
        description=f"Se han borrado **{affected_rows}** sanciones activas de {usuario.mention}.",
        color=Colors.SUCCESS,
        user=interaction.user
    )
    response_embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
    response_embed.add_field(name="👮 Borradas por", value=interaction.user.mention, inline=True)
    await interaction.followup.send(embed=response_embed, ephemeral=True)

    # Enviar notificación al usuario
    dm_embed = create_embed(
        title="🔔 Sanciones Eliminadas",
        description=(
            f"Todas tus sanciones activas en **Santiago RP** han sido eliminadas.\n\n"
            f"**Total eliminadas:** {affected_rows}\n"
            f"**Eliminadas por:** {interaction.user.mention}\n\n"
            "Asegúrate de seguir las reglas del servidor para evitar futuras sanciones."
        ),
        color=Colors.SUCCESS
    )
    try:
        await usuario.send(embed=dm_embed)
    except discord.errors.Forbidden:
        response_embed.add_field(
            name="⚠️ Advertencia",
            value=f"No se pudo enviar un mensaje directo a {usuario.mention}. Es posible que tenga los DMs cerrados.",
            inline=False
        )
        await interaction.followup.send(embed=response_embed, ephemeral=True)

    # Enviar log al canal de sanciones
    log_channel = bot.get_channel(Channels.SANCTION_LOGS)
    if log_channel:
        log_embed = create_embed(
            title="🗑️ Sanciones Borradas",
            description=f"Se han eliminado sanciones activas del servidor.",
            color=Colors.SUCCESS,
            user=interaction.user
        )
        log_embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
        log_embed.add_field(name="📉 Sanciones eliminadas", value=str(affected_rows), inline=True)
        log_embed.add_field(name="👮 Borradas por", value=interaction.user.mention, inline=True)
        await log_channel.send(embed=log_embed)

@bot.tree.command(name="banear-a", description="Aplica un baneo a un usuario")
@app_commands.checks.has_any_role(*Roles.STAFF)
@app_commands.describe(
    usuario="Selecciona el usuario a banear",
    motivo="Explica por qué se banea al usuario",
    pruebas="Enlace a las pruebas del baneo (ej. https://imgur.com/abc)"
)
async def banear_a(interaction: discord.Interaction, usuario: discord.Member, motivo: str, pruebas: str):
    """Comando para banear a un usuario."""
    # Verificar canal correcto
    if interaction.channel_id != 1357151556926963748:
        await interaction.response.send_message(embed=create_embed(
            title="❌ Canal Incorrecto",
            description=f"Este comando solo puede usarse en <#{1357151556926963748}>.",
            color=Colors.DANGER
        ), ephemeral=True)
        return

    await interaction.response.defer()

    # Guardar baneo en la base de datos
    sanction_id = save_sanction(
        user_id=usuario.id,
        username=usuario.name,
        reason=motivo,
        sanction_type="Baneo",
        proof_url=pruebas,
        admin_id=interaction.user.id,
        admin_name=interaction.user.name
    )

    # Aplicar baneo
    try:
        await interaction.guild.ban(
            usuario,
            reason=f"Baneo aplicado por {interaction.user.name}: {motivo}",
            delete_message_days=0
        )
    except Exception as e:
        print(f"Error al banear usuario: {e}")
        await interaction.followup.send(embed=create_embed(
            title="❌ Error",
            description="No se pudo aplicar el baneo. Por favor, verifica los permisos del bot.",
            color=Colors.DANGER
        ))
        return

    # Crear embed para respuesta en el canal
    ban_embed = create_embed(
        title="🚫 Baneo Aplicado",
        description=f"Se ha baneado a {usuario.mention} con éxito.",
        color=Colors.DANGER,
        user=interaction.user
    )
    ban_embed.add_field(name="🆔 ID de Baneo", value=sanction_id, inline=False)
    ban_embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
    ban_embed.add_field(name="📝 Motivo", value=motivo, inline=True)
    ban_embed.add_field(name="📸 Pruebas", value=pruebas, inline=False)
    ban_embed.add_field(name="👮 Aplicado por", value=interaction.user.mention, inline=True)

    await interaction.followup.send(embed=ban_embed)

    # Enviar notificación al usuario baneado
    dm_embed = create_embed(
        title="🚫 Has Sido Baneado",
        description=(
            f"Has sido baneado en **Santiago RP**. Aquí están los detalles:\n\n"
            f"**🆔 ID de Baneo:** {sanction_id}\n"
            f"**📝 Motivo:** {motivo}\n"
            f"**📸 Pruebas:** {pruebas}\n"
            f"**👮 Aplicado por:** {interaction.user.mention}\n"
        ),
        color=Colors.DANGER
    )
    dm_embed.add_field(
        name="📜 ¿Cómo apelar?",
        value=(
            f"Puedes apelar este baneo abriendo un ticket en <#{Channels.TICKETS}> seleccionando la categoría **Apelaciones**. "
            f"Asegúrate de incluir el **ID de Baneo** ({sanction_id}) y pruebas que respalden tu caso."
        ),
        inline=False
    )

    try:
        await usuario.send(embed=dm_embed)
    except discord.errors.Forbidden:
        await interaction.followup.send(embed=create_embed(
            title="⚠️ Advertencia",
            description=f"No se pudo enviar el mensaje directo a {usuario.mention}. Es posible que tenga los DMs cerrados.",
            color=Colors.WARNING
        ))

    # Enviar log al canal de sanciones
    log_channel = bot.get_channel(Channels.SANCTION_LOGS)
    if log_channel:
        log_embed = create_embed(
            title="📜 Registro de Baneo",
            description=f"Se ha registrado un nuevo baneo en el servidor.",
            color=Colors.DANGER,
            user=interaction.user
        )
        log_embed.add_field(name="🆔 ID de Baneo", value=sanction_id, inline=False)
        log_embed.add_field(name="👤 Usuario", value=usuario.mention, inline=True)
        log_embed.add_field(name="📝 Motivo", value=motivo, inline=True)
        log_embed.add_field(name="📸 Pruebas", value=pruebas, inline=False)
        log_embed.add_field(name="👮 Aplicado por", value=interaction.user.mention, inline=True)
        
        await log_channel.send(embed=log_embed)

async def weekly_top_staff():
    """Tarea semanal para anunciar el mejor staff y reiniciar calificaciones."""
    while True:
        now = datetime.now(pytz.UTC)
        next_monday = now + timedelta(days=(7 - now.weekday()) % 7)
        next_monday = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        if now.weekday() == 0 and now.hour == 0:  # Si ya es lunes 00:00
            next_monday += timedelta(days=7)
        seconds_until_monday = (next_monday - now).total_seconds()

        await asyncio.sleep(seconds_until_monday)

        channel = bot.get_channel(Channels.RATINGS)
        if not channel:
            print("⚠️ Canal de calificaciones no encontrado.")
            continue

        top_staff = get_top_staff()
        if top_staff:
            staff_id, staff_name, avg_rating, count = top_staff
            embed = create_embed(
                title="🏆 Staff de la Semana",
                description=(
                    f"¡Felicidades a <@{staff_id}> por ser el **Staff de la Semana**! 🎉\n\n"
                    f"**Promedio:** {avg_rating:.2f}/5 🌟\n"
                    f"**Calificaciones recibidas:** {count}\n\n"
                    "Las calificaciones han sido reiniciadas. ¡Sigue apoyando a nuestro equipo!"
                ),
                color=Colors.SUCCESS
            )
            embed.set_thumbnail(url=bot.get_user(staff_id).display_avatar.url if bot.get_user(staff_id) else None)
            await channel.send(embed=embed)

            # Notificar al staff ganador
            staff_member = bot.get_user(staff_id)
            if staff_member:
                try:
                    dm_embed = create_embed(
                        title="🎉 ¡Eres el Staff de la Semana!",
                        description=(
                            f"¡Felicidades, {staff_name}! Has sido elegido como el **Staff de la Semana** en **Santiago RP**.\n\n"
                            f"**Promedio:** {avg_rating:.2f}/5 🌟\n"
                            f"**Calificaciones recibidas:** {count}\n\n"
                            "Gracias por tu excelente trabajo. ¡Sigue así!"
                        ),
                        color=Colors.SUCCESS
                    )
                    await staff_member.send(embed=dm_embed)
                except discord.errors.Forbidden:
                    print(f"⚠️ No se pudo enviar DM a {staff_name} (DMs cerrados).")

        else:
            embed = create_embed(
                title="📊 Calificaciones Semanales",
                description="No hay suficientes calificaciones esta semana (mínimo 3 por staff). ¡Sigue calificando a nuestro equipo!",
                color=Colors.INFO
            )
            await channel.send(embed=embed)

        # Borrar calificaciones
        clear_ratings()

        # Log en SANCTION_LOGS
        log_channel = bot.get_channel(Channels.SANCTION_LOGS)
        if log_channel:
            log_embed = create_embed(
                title="🔄 Reinicio de Calificaciones",
                description="Se han reiniciado las calificaciones semanales.",
                color=Colors.INFO
            )
            if top_staff:
                log_embed.add_field(name="🏆 Staff de la Semana", value=f"<@{staff_id}> ({avg_rating:.2f}/5)", inline=True)
            await log_channel.send(embed=log_embed)

@bot.tree.command(name="calificar-staff", description="Califica a un miembro del staff")
@is_ratings_channel()
@app_commands.autocomplete(calificacion=rating_autocomplete)
@app_commands.describe(
    usuario="Selecciona el miembro del staff a calificar",
    calificacion="Elige una calificación de 1 a 5 estrellas",
    comentario="Explica por qué das esta calificación"
)
async def calificar_staff(interaction: discord.Interaction, usuario: discord.Member, calificacion: str, comentario: str):
    """Comando para calificar a un miembro del staff."""
    # Verificar que el usuario tiene un rol de STAFF
    if not any(role.id in Roles.STAFF for role in usuario.roles):
        await interaction.response.send_message(embed=create_embed(
            title="❌ Usuario No Válido",
            description=f"{usuario.mention} no es miembro del staff.",
            color=Colors.DANGER
        ), ephemeral=True)
        return

    # Validar calificación
    try:
        rating = int(calificacion)
        if rating < 1 or rating > 5:
            raise ValueError
    except ValueError:
        await interaction.response.send_message(embed=create_embed(
            title="❌ Calificación Inválida",
            description="Por favor, selecciona una calificación entre 1 y 5 estrellas.",
            color=Colors.DANGER
        ), ephemeral=True)
        return

    await interaction.response.defer()

    # Guardar calificación en la base de datos
    rating_id = save_rating(
        staff_id=usuario.id,
        staff_name=usuario.name,
        rating=rating,
        comment=comentario,
        user_id=interaction.user.id,
        user_name=interaction.user.name
    )

    # Crear embed para respuesta en el canal
    rating_embed = create_embed(
        title="🌟 Calificación Registrada",
        description=f"Se ha registrado tu calificación para {usuario.mention}.",
        color=Colors.SUCCESS,
        user=interaction.user
    )
    rating_embed.add_field(name="🆔 ID de Calificación", value=rating_id, inline=False)
    rating_embed.add_field(name="👤 Staff", value=usuario.mention, inline=True)
    rating_embed.add_field(name="🌟 Calificación", value="🌟" * rating, inline=True)
    rating_embed.add_field(name="💬 Comentario", value=comentario, inline=False)
    rating_embed.add_field(name="👥 Calificado por", value=interaction.user.mention, inline=True)

    await interaction.followup.send(embed=rating_embed)

    # Enviar notificación al staff calificado
    dm_embed = create_embed(
        title="🌟 Nueva Calificación Recibida",
        description=(
            f"Has recibido una calificación en **Santiago RP**. Aquí están los detalles:\n\n"
            f"**🆔 ID de Calificación:** {rating_id}\n"
            f"**🌟 Calificación:** {'🌟' * rating} ({rating}/5)\n"
            f"**💬 Comentario:** {comentario}\n"
            f"**👥 Calificado por:** {interaction.user.mention}"
        ),
        color=Colors.SUCCESS
    )

    try:
        await usuario.send(embed=dm_embed)
    except discord.errors.Forbidden:
        await interaction.followup.send(embed=create_embed(
            title="⚠️ Advertencia",
            description=f"No se pudo enviar el mensaje directo a {usuario.mention}. Es posible que tenga los DMs cerrados.",
            color=Colors.WARNING
        ))

    # Enviar log al canal de sanciones
    log_channel = bot.get_channel(Channels.SANCTION_LOGS)
    if log_channel:
        log_embed = create_embed(
            title="📜 Registro de Calificación",
            description=f"Se ha registrado una nueva calificación para un miembro del staff.",
            color=Colors.SUCCESS,
            user=interaction.user
        )
        log_embed.add_field(name="🆔 ID de Calificación", value=rating_id, inline=False)
        log_embed.add_field(name="👤 Staff", value=usuario.mention, inline=True)
        log_embed.add_field(name="🌟 Calificación", value=f"{'🌟' * rating} ({rating}/5)", inline=True)
        log_embed.add_field(name="💬 Comentario", value=comentario, inline=False)
        log_embed.add_field(name="👥 Calificado por", value=interaction.user.mention, inline=True)
        
        await log_channel.send(embed=log_embed)

def is_view_sanctions_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel_id != Channels.VIEW_SANCTIONS:
            await interaction.response.send_message(embed=create_embed(
                title="❌ Canal Incorrecto",
                description=f"Este comando solo puede usarse en <#{Channels.VIEW_SANCTIONS}>.",
                color=Colors.DANGER
            ), ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

@bot.tree.command(name="ayuda", description="Muestra todos los comandos disponibles del bot")
async def ayuda(interaction: discord.Interaction):
    """Comando para mostrar la lista de todos los comandos disponibles."""
    await interaction.response.defer(ephemeral=True)

    embed = create_embed(
        title="📖 Guía de Comandos de Santiago RP",
        description=(
            "¡Bienvenido a la guía de comandos de **Santiago RP**! 🎉\n"
            "A continuación, encontrarás todos los comandos disponibles, qué hacen, dónde usarlos y quiénes pueden ejecutarlos."
        ),
        color=Colors.INFO,
        user=interaction.user
    )

    # Lista de comandos con sus detalles
    commands_list = [
        {
            "name": "panel",
            "emoji": "⚙️",
            "description": "Despliega el panel de control para gestionar el servidor (abrir servidor, iniciar votación).",
            "channel": f"Cualquier canal",
            "permissions": "Staff (roles: <@&1357151555916271624>, <@&1357151555916271622>, etc.)"
        },
        {
            "name": "tickets",
            "emoji": "🎫",
            "description": "Abre el sistema interactivo de tickets para reportes, apelaciones, etc.",
            "channel": f"<#{Channels.TICKETS}>",
            "permissions": "Todos"
        },
        {
            "name": "sancionar-a",
            "emoji": "⚖️",
            "description": "Aplica una sanción (Advertencia 1, 2 o 3) a un usuario con motivo y pruebas.",
            "channel": f"<#{Channels.SANCTIONS}>",
            "permissions": "Staff (roles: <@&1357151555916271624>, <@&1357151555916271622>, etc.)"
        },
        {
            "name": "ver-sanciones",
            "emoji": "📜",
            "description": "Muestra las sanciones activas de un usuario (tuyas o de otro).",
            "channel": f"<#{Channels.VIEW_SANCTIONS}>",
            "permissions": "Todos"
        },
        {
            "name": "borrar-sanciones",
            "emoji": "🗑️",
            "description": "Elimina todas las sanciones activas de un usuario.",
            "channel": "Cualquier canal",
            "permissions": "Administradores (permiso: Administrador)"
        },
        {
            "name": "banear-a",
            "emoji": "🚫",
            "description": "Banea a un usuario con motivo y pruebas.",
            "channel": f"<#1357151556926963748>",
            "permissions": "Staff (roles: <@&1357151555916271624>, <@&1357151555916271622>, etc.)"
        },
        {
            "name": "calificar-staff",
            "emoji": "🌟",
            "description": "Califica a un miembro del staff con estrellas (1 a 5) y un comentario.",
            "channel": f"<#{Channels.RATINGS}>",
            "permissions": "Todos"
        }
    ]

    # Añadir cada comando como un campo en el embed
    for cmd in commands_list:
        embed.add_field(
            name=f"{cmd['emoji']} /{cmd['name']}",
            value=(
                f"**Descripción:** {cmd['description']}\n"
                f"**Canal:** {cmd['channel']}\n"
                f"**Permisos:** {cmd['permissions']}"
            ),
            inline=False
        )

    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else "")
    embed.set_footer(text="Santiago RP | Sistema Automatizado | Creado por Smile")

    await interaction.followup.send(embed=embed, ephemeral=True)

# =============================================
# INICIAR BOT
# =============================================
if __name__ == "__main__":
    bot.run(TOKEN)

