import discord
from discord.ext import commands
from discord.ext import tasks
from discord.ui import View, Select, Button
from datetime import datetime, timedelta
from discord.ext.commands import has_any_role  # Pastikan has_any_role diimpor dengan benar
import asyncio
import logging

TOKEN = 'MTI5OTM5Njg1MTYyMzEzMzI3NA.GXwhbA.CyCPbmuLaQAxo4BIzDThpcc3ka9gTXIyurW8nk'

# Atur logging
logging.basicConfig(level=logging.INFO)


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

links = {}

@bot.event
async def on_ready():
    print(f'Bot siap digunakan. Masuk sebagai {bot.user.name} di Ventro')

@bot.event
async def on_member_join(member):
    server_name = "Ventro"
    welcome_channel = discord.utils.get(member.guild.text_channels, name='welcome')
    if welcome_channel:
        embed = discord.Embed(title="Selamat Datang di Ventro!", description=f'Selamat datang di {server_name}, {member.mention}!', color=0x00ff00)
        embed.set_thumbnail(url=str(member.avatar.url))
        await welcome_channel.send(embed=embed)
    
    default_role = discord.utils.get(member.guild.roles, name='MEMBER')
    if default_role:
        await member.add_roles(default_role)

@bot.event
async def on_member_remove(member):
    goodbye_channel = discord.utils.get(member.guild.text_channels, name='goodbye')
    if goodbye_channel:
        embed = discord.Embed(title="Sampai Jumpa!", description=f'{member.name} telah meninggalkan Ventro.', color=0xff0000)
        embed.set_thumbnail(url=str(member.avatar.url))
        await goodbye_channel.send(embed=embed)
    
    with open('left_members.txt', 'a') as f:
        roles = [role.name for role in member.roles if role != member.guild.default_role]
        f.write(f'{member.id}:{",".join(roles)}\n')

@bot.event
async def on_member_update(before, after):
    if before.pending and not after.pending:
        with open('left_members.txt', 'r') as f:
            lines = f.readlines()
        with open('left_members.txt', 'w') as f:
            for line in lines:
                member_id, roles = line.strip().split(':')
                if int(member_id) == after.id:
                    roles_to_add = [discord.utils.get(after.guild.roles, name=role) for role in roles.split(',')]
                    for role in roles_to_add:
                        if role:
                            await after.add_roles(role)
                else:
                    f.write(line)

class UsernameModal(discord.ui.Modal, title='Isi Nama Karakter Anda'):
    username = discord.ui.TextInput(label='Nama Karakter', placeholder='Masukkan Nama_Karakter Anda di sini')

    def __init__(self, interaction, role):
        super().__init__()
        self.interaction = interaction
        self.role = role

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.user.edit(nick=self.username.value)
        await interaction.user.add_roles(self.role)
        await interaction.response.send_message(f'Terima kasih {self.username.value}, Anda telah diberikan peran {self.role.name}.', ephemeral=True)

class RoleButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝Register Role", style=discord.ButtonStyle.green)
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name='VERIFY')
        if role:
            modal = UsernameModal(interaction, role)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message('Peran VERIFY tidak ditemukan.', ephemeral=True)

class RequestRequestModal(discord.ui.Modal, title='Request VENTRO'):
    Request_reason = discord.ui.TextInput(label='Alasan Masuk VENTRO', placeholder='Masukkan alasan Masuk VENTRO Anda di sini')
    channel_name = discord.ui.TextInput(label='Nama Lengkap', placeholder='Masukkan Nama anda.')

    def __init__(self, interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel_name = self.channel_name.value
        admin_role = discord.utils.get(guild.roles, name='ADMINS')

        if admin_role is None:
            await interaction.response.send_message('Role ADMINS tidak ditemukan. Mohon periksa pengaturan server Anda.', ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            admin_role: discord.PermissionOverwrite(read_messages=True)
        }

        category = discord.utils.get(guild.categories, name='VENTRO')
        if category is None:
            category = await guild.create_category(name='VENTRO')

        new_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title="Request Join VENTRO",
            description=f'Channel khusus "{channel_name}" telah dibuat untuk Masuk kedalam VENTRO Anda.',
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await new_channel.send(f"Channel ini dibuat untuk Masuk sebagai bagian dari VENTRO oleh {interaction.user.mention}.\n**Alasan masuk VENTRO**: {self.Request_reason.value}")

class RequestButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💰Req Verify", style=discord.ButtonStyle.primary)
    async def request_req_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RequestRequestModal(interaction)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="ℹ️Info", style=discord.ButtonStyle.secondary)
    async def info_req_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Request Member Information",
            description="**VENTRO:**\n\n - Dalam tahap Perbaikan -",
            color=0x0000ff
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command()
async def role_buttons(ctx):
    view = RoleButtonView()
    embed = discord.Embed(
        title="Selamat Datang di Ventro",
        description="Klik tombol di bawah untuk register agar bisa melihat akses lainnya:",
        color=0x7289DA
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def req_buttons(ctx):
    view = RequestButtonView()
    embed = discord.Embed(
        title="Informasi VENTRO",
        description="Klik tombol di bawah untuk request atau mendapatkan informasi tentang VENTRO:",
        color=0xFFD700
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def create_text_channel(ctx, channel_name):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        await guild.create_text_channel(channel_name)
        embed = discord.Embed(title="Saluran Teks Dibuat", description=f'Saluran teks "{channel_name}" telah dibuat.', color=0x00ff00)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Kesalahan", description=f'Saluran teks "{channel_name}" sudah ada.', color=0xff0000)
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def create_voice_channel(ctx, channel_name):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        await guild.create_voice_channel(channel_name)
        embed = discord.Embed(title="Saluran Suara Dibuat", description=f'Saluran suara "{channel_name}" telah dibuat.', color=0x00ff00)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Kesalahan", description=f'Saluran suara "{channel_name}" sudah ada.', color=0xff0000)
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def assign_role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles:
        embed = discord.Embed(title="Kesalahan", description=f'{member.mention} sudah memiliki peran {role.name}.', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        await member.add_roles(role)
        embed = discord.Embed(title="Peran Diberikan", description=f'Peran {role.name} telah diberikan kepada {member.mention}.', color=0x00ff00)
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles:
        await member.remove_roles(role)
        embed = discord.Embed(title="Peran Dihapus", description=f'Peran {role.name} telah dihapus dari {member.mention}.', color=0x00ff00)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Kesalahan", description=f'{member.mention} tidak memiliki peran {role.name}.', color=0xff0000)
        await ctx.send(embed=embed)
@bot.command(name='h')
async def help_command(ctx):
    embed = discord.Embed(
        title="Daftar Perintah Ventrobot",
        description="Berikut adalah perintah-perintah yang dapat Anda gunakan:",
        color=0x00aeef
    )
    
    embed.add_field(name="!role_buttons", value="Menampilkan tombol untuk mendaftar dan mendapatkan akses.", inline=False)
    embed.add_field(name="!req_buttons", value="Menampilkan tombol untuk request atau mendapatkan informasi tentang VENTRO.", inline=False)
    embed.add_field(name="!create_text_channel [nama_channel]", value="Membuat saluran teks baru dengan nama yang ditentukan.", inline=False)
    embed.add_field(name="!create_voice_channel [nama_channel]", value="Membuat saluran suara baru dengan nama yang ditentukan.", inline=False)
    embed.add_field(name="!role [member] [role]", value="Memberikan peran tertentu kepada anggota.", inline=False)
    embed.add_field(name="!remove_role [member] [role]", value="Menghapus peran tertentu dari anggota.", inline=False)
    embed.add_field(name="!ann [text]", value="Mengirimkan informasi di channel #news.", inline=False)
    embed.add_field(name="!start_auto_delete [channel_id] [interval_minutes] [amount]", value="Contoh penggunaan: !start_auto_delete 123456789123456789 10 50 akan menghapus 50 pesan setiap 10 menit dari channel dengan ID 123456789123456789.", inline=False)
    embed.add_field(name="!delete [jumlah]", value="Perintah ini menghapus sejumlah pesan secara manual dari channel tempat perintah dikirim.", inline=False)
    embed.add_field(name="!h", value="Menampilkan daftar perintah dan fungsinya.", inline=False)

    embed.set_footer(text="Gunakan perintah dengan bijak!")
    
    await ctx.send(embed=embed)
ANNOUNCEMENT_CHANNEL_ID = 1299387074335739934
@bot.command(name='ann')
@commands.has_any_role('MODERATOR', 'MANAGEMENT', 'VENTRO')  # Hanya peran yang diperbolehkan
async def announce(ctx, *, announcement: str):
    # Mencari channel berdasarkan ID
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    
    # Jika channel ditemukan, kirimkan pengumuman
    if channel:
        await channel.send(announcement)
        await ctx.send(f'Pengumuman telah dikirim: "{announcement}"')
    else:
        await ctx.send('Channel pengumuman tidak ditemukan.')

@announce.error
async def announce_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send('Anda tidak memiliki izin untuk menggunakan perintah ini.')

# ID dari channel yang akan menerima promosi
PROMO_CHANNEL_ID = 1299541109399355473  # Gantilah dengan channel ID yang sesuai

# Fungsi untuk mengirim pesan promosi
async def send_promo():
    channel = bot.get_channel(PROMO_CHANNEL_ID)
    if channel:
        promo_message = "# 🔥 Jangan lupa cek produk terbaru kami! Diskon hingga 50%! Kunjungi website kami sekarang juga!\n\n> - 🌐 https://silumankatak.github.io/\n\n@everyone"
        await channel.send(promo_message)

# Membuat task yang berjalan setiap 6 jam
@tasks.loop(hours=6)
async def promo_task():
    await send_promo()

# Mulai task setelah bot siap
@bot.event
async def on_ready():
    print(f'Bot sudah online! Bot login sebagai {bot.user}')
    promo_task.start()  # Mulai task promosi setiap 6 jam

# Perintah untuk menampilkan statistik server
@bot.command(name='stats')
@commands.has_any_role('MODERATOR', 'MANAGEMENT', 'VENTRO')  # Batasan akses untuk role tertentu
async def stats(ctx):
    guild = ctx.guild  # Mendapatkan informasi server saat ini

    # Menghitung statistik dasar server
    total_members = guild.member_count
    total_channels = len(guild.channels)
    total_text_channels = len(guild.text_channels)
    total_voice_channels = len(guild.voice_channels)
    total_roles = len(guild.roles)
    total_emojis = len(guild.emojis)

    # Cek apakah server memiliki ikon, jika ya, gunakan URL-nya
    icon_url = guild.icon.url if guild.icon else None

    # Membuat embed yang rapi untuk menampilkan statistik
    embed = discord.Embed(title=f"📊 Statistik Server: {guild.name}", color=discord.Color.blue())
    
    if icon_url:
        embed.set_thumbnail(url=icon_url)

    embed.add_field(name="👥 Jumlah Anggota", value=total_members, inline=False)
    embed.add_field(name="💬 Jumlah Saluran", value=f"{total_channels} total (Text: {total_text_channels}, Voice: {total_voice_channels})", inline=False)
    embed.add_field(name="📜 Jumlah Peran", value=total_roles, inline=False)
    embed.add_field(name="😀 Jumlah Emoji", value=total_emojis, inline=False)
    embed.set_footer(text=f"ID Server: {guild.id}")

    # Mengirimkan embed ke channel
    await ctx.send(embed=embed)

# Perintah untuk mengirim pesan pribadi
@bot.command(name='pm')
@commands.has_any_role('MANAGEMENT', 'VENTRO')  # Batasan hanya role tertentu
async def pm(ctx, user: discord.User, *, text: str):
    try:
        # Kirimkan pesan pribadi ke user yang disebutkan
        await user.send(f" {text}")
        await ctx.send(f"✅ Pesan berhasil dikirim ke {user.name}.")
    except discord.Forbidden:
        # Jika bot tidak dapat mengirim pesan pribadi
        await ctx.send(f"❌ Gagal mengirim pesan ke {user.name}. Pastikan user menerima pesan pribadi.")
    except Exception as e:
        # Jika ada kesalahan lain
        await ctx.send(f"⚠️ Terjadi kesalahan: {str(e)}")

@bot.command(name='deletepm')
async def deletepm(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        # Gantikan pesan sebelumnya dengan pesan baru
        await ctx.send("🗑️ Pesan ini telah dihapus.")
    else:
        await ctx.send("❌ Perintah ini hanya dapat digunakan di DM.")

# Fungsi untuk menghapus pesan dalam jumlah tertentu pada channel tertentu
async def delete_messages(channel, amount):
    deleted = await channel.purge(limit=amount)
    print(f"{len(deleted)} pesan berhasil dihapus dari {channel.name}")

# Command untuk mulai otomatis menghapus pesan setiap interval waktu tertentu
@bot.command(name='start_auto_delete')
@has_any_role('MANAGEMENT', 'VENTRO')  # Hanya role tertentu yang bisa menggunakan perintah ini
async def submit(self, interaction: discord.Interaction):
        member_id = int(self.member_select.values[0])
        role_id = int(self.role_select.values[0])
        
        member = interaction.guild.get_member(member_id)
        role = interaction.guild.get_role(role_id)

        if not member or not role:
            await interaction.response.send_message("❌ Anggota atau role tidak ditemukan.", ephemeral=True)
            return

        # Menambahkan logging untuk debugging
        logging.info(f"Mencoba memberikan role '{role.name}' kepada {member.name}")

        try:
            if role in member.roles:
                await member.remove_roles(role)
                await interaction.response.send_message(f"✅ Role '{role.name}' dihapus dari {member.mention}.", ephemeral=True)
            else:
                await member.add_roles(role)
                await interaction.response.send_message(f"✅ Role '{role.name}' diberikan kepada {member.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot tidak memiliki izin untuk memberikan role ini.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Terjadi kesalahan: {str(e)}", ephemeral=True)

@bot.command()
@commands.has_any_role('MANAGEMENT', 'VENTRO')  # Hanya role tertentu yang bisa menggunakan perintah ini
async def role(ctx, member: discord.Member, *, role_name: str):
    """Memberikan atau menghapus role dari anggota."""
    
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if role is None:
        await ctx.send(f"❌ Role '{role_name}' tidak ditemukan di server ini.")
        return

    if role in member.roles:
        try:
            await member.remove_roles(role)
            await ctx.send(f"✅ Role '{role.name}' dihapus dari {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ Bot tidak memiliki izin untuk menghapus role ini.")
        except Exception as e:
            await ctx.send(f"❌ Terjadi kesalahan: {str(e)}")
    else:
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Role '{role.name}' diberikan kepada {member.mention}.")
        except discord.Forbidden:
            await ctx.send("❌ Bot tidak memiliki izin untuk memberikan role ini.")
        except Exception as e:
            await ctx.send(f"❌ Terjadi kesalahan: {str(e)}")

@bot.command()
@commands.has_permissions(manage_messages=True)  # Hanya pengguna dengan izin ini yang dapat menggunakan perintah
async def delete(ctx, jumlah: int):
    """Menghapus sejumlah pesan dari channel saat ini. Max 150 pesan."""
    
    if jumlah < 1 or jumlah > 150:
        await ctx.send("❌ Jumlah pesan yang ingin dihapus harus antara 1 dan 150.")
        return

    deleted = await ctx.channel.purge(limit=jumlah + 1)  # +1 untuk menghapus perintah itu sendiri
    await ctx.send(f"✅ {len(deleted)} pesan berhasil dihapus!", delete_after=5)  # Kirim pesan dan hapus setelah 5 detik



bot.run(TOKEN)
