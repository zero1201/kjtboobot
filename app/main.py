import discord
from discord.ext import commands
from discord import app_commands

# Botの設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

# Bot起動時の処理
@bot.event
async def on_ready():
    print(f'{bot.user} がログインしました！')
    
    # スラッシュコマンドを同期
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)} 個のスラッシュコマンドを同期しました')
    except Exception as e:
        print(f'コマンド同期エラー: {e}')

# 1. お知らせ機能
@bot.tree.command(name="お知らせ", description="高機能な埋め込みお知らせを送信します")
@app_commands.describe(
    title="タイトル",
    content="本文（Enterまたは \\n で改行OK）",
    mention="everyone / here / なし",
    color="red, green, blue, yellow, random, #hex",
    image_url="画像URL",
    thumbnail_url="サムネURL",
    footer="フッター文字",
    channel="送信先チャンネル"
)
async def announcement(
    interaction: discord.Interaction,
    title: str,
    content: str,
    mention: str = "everyone",
    color: str = "blue",
    image_url: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    footer: Optional[str] = None,
    channel: Optional[discord.TextChannel] = None
):

    # ===== 権限チェック =====
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 権限がありません", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    send_channel = channel or interaction.channel

    # ===== 改行対応（←今回の追加ポイント）=====
    content = content.replace("\\n", "\n")

    # ===== 色設定 =====
    color_dict = {
        "red": discord.Color.red(),
        "green": discord.Color.green(),
        "blue": discord.Color.blue(),
        "yellow": discord.Color.gold(),
        "random": discord.Color.random()
    }

    if color.startswith("#"):
        embed_color = discord.Color(int(color[1:], 16))
    else:
        embed_color = color_dict.get(color.lower(), discord.Color.blue())

    # ===== Embed生成 =====
    embed = discord.Embed(
        title=f"📢 {title}",
        description=content,
        color=embed_color,
        timestamp=discord.utils.utcnow()
    )

    # ===== 画像 =====
    if image_url and image_url.startswith(("http://", "https://")):
        embed.set_image(url=image_url)

    if thumbnail_url and thumbnail_url.startswith(("http://", "https://")):
        embed.set_thumbnail(url=thumbnail_url)

    # ===== フッター =====
    footer_text = footer or f"送信者: {interaction.user.display_name}"
    embed.set_footer(text=footer_text, icon_url=interaction.user.display_avatar.url)

    # ===== メンション =====
    mention_map = {
        "everyone": "@everyone",
        "here": "@here",
        "なし": ""
    }
    mention_text = mention_map.get(mention.lower(), "@everyone")

    # ===== 送信 =====
    try:
        if mention_text:
            await send_channel.send(mention_text)

        await send_channel.send(embed=embed)

        await interaction.followup.send("✅ お知らせを送信しました！", ephemeral=True)

    except discord.Forbidden:
        await interaction.followup.send("❌ 送信権限がありません", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"⚠ エラー: {e}", ephemeral=True)

# 2. モデレーションコマンド
@bot.tree.command(name="ban", description="ユーザーをBANします")
@app_commands.describe(
    member="BANするメンバー",
    reason="理由"
)
async def ban_command(interaction: discord.Interaction, member: discord.Member, reason: str = "理由なし"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("BANする権限がありません。", ephemeral=True)
        return
    
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="BAN実行",
            description=f"{member.mention} がBANされました",
            color=discord.Color.red()
        )
        embed.add_field(name="理由", value=reason)
        embed.add_field(name="実行者", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)

@bot.tree.command(name="kick", description="ユーザーをキックします")
@app_commands.describe(
    member="キックするメンバー",
    reason="理由"
)
async def kick_command(interaction: discord.Interaction, member: discord.Member, reason: str = "理由なし"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("キックする権限がありません。", ephemeral=True)
        return
    
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="キック実行",
            description=f"{member.mention} がキックされました",
            color=discord.Color.orange()
        )
        embed.add_field(name="理由", value=reason)
        embed.add_field(name="実行者", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)

@bot.tree.command(name="to", description="ユーザーをタイムアウトします")
@app_commands.describe(
    member="タイムアウトするメンバー",
    minutes="分数",
    reason="理由"
)
async def timeout_command(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "理由なし"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("タイムアウトする権限がありません。", ephemeral=True)
        return
    
    try:
        import datetime
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        
        embed = discord.Embed(
            title="タイムアウト実行",
            description=f"{member.mention} が{minutes}分間タイムアウトされました",
            color=discord.Color.yellow()
        )
        embed.add_field(name="理由", value=reason)
        embed.add_field(name="実行者", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)

@bot.tree.command(name="unto", description="ユーザーのタイムアウトを解除します")
@app_commands.describe(
    member="タイムアウトを解除するメンバー"
)
async def untimeout_command(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("タイムアウトを解除する権限がありません。", ephemeral=True)
        return
    
    try:
        await member.timeout(None)
        
        embed = discord.Embed(
            title="タイムアウト解除",
            description=f"{member.mention} のタイムアウトが解除されました",
            color=discord.Color.green()
        )
        embed.add_field(name="実行者", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)

# 3. 情報表示コマンド
@bot.tree.command(name="info", description="サーバーまたはユーザーの情報を表示します")
@app_commands.describe(
    target="情報を取得する対象（ユーザーまたはサーバー）"
)
async def info_command(interaction: discord.Interaction, target: str = "サーバー"):
    guild = interaction.guild
    
    if target.lower() == "サーバー":
        embed = discord.Embed(
            title=f"{guild.name} の情報",
            color=discord.Color.blue()
        )
        
        # サーバーアイコン
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # 基本情報
        embed.add_field(name="オーナー", value=guild.owner.mention if guild.owner else "不明", inline=True)
        embed.add_field(name="メンバー数", value=guild.member_count, inline=True)
        embed.add_field(name="作成日", value=guild.created_at.strftime('%Y/%m/%d'), inline=True)
        embed.add_field(name="チャンネル数", value=len(guild.channels), inline=True)
        embed.add_field(name="ロール数", value=len(guild.roles), inline=True)
        embed.add_field(name="ブースト数", value=guild.premium_subscription_count, inline=True)
        
        await interaction.response.send_message(embed=embed)
        
    else:
        # ユーザー名で検索
        member = None
        if target.startswith('<@') and target.endswith('>'):
            # メンション形式
            user_id = target.replace('<@', '').replace('>', '').replace('!', '')
            try:
                member = guild.get_member(int(user_id))
            except:
                pass
        else:
            # 名前で検索
            for m in guild.members:
                if target.lower() in m.name.lower() or (m.nick and target.lower() in m.nick.lower()):
                    member = m
                    break
        
        if member:
            embed = discord.Embed(
                title=f"{member.name} の情報",
                color=member.color if member.color != discord.Color.default() else discord.Color.blue()
            )
            
            # アバター
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            
            # ユーザー情報
            embed.add_field(name="ユーザー名", value=f"{member.name}", inline=True)
            embed.add_field(name="ニックネーム", value=member.nick if member.nick else "なし", inline=True)
            embed.add_field(name="ID", value=member.id, inline=False)
            embed.add_field(name="参加日", value=member.joined_at.strftime('%Y/%m/%d %H:%M'), inline=True)
            embed.add_field(name="アカウント作成日", value=member.created_at.strftime('%Y/%m/%d %H:%M'), inline=True)
            
            # ロール
            roles = [role.mention for role in member.roles[1:]]  # @everyoneを除外
            if roles:
                embed.add_field(name="ロール", value=" ".join(roles), inline=False)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("ユーザーが見つかりませんでした。", ephemeral=True)

# 4. 認証パネル設置コマンド
@bot.tree.command(name="認証", description="認証パネルを設置します")
@app_commands.describe(
    role="認証後に付与するロール",
    title="パネルのタイトル",
    description="パネルの説明文"
)
async def auth_panel(interaction: discord.Interaction, role: discord.Role, title: str = "認証パネル", description: str = "ボタンをクリックして認証を完了してください"):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
        return
    
    # 埋め込みメッセージの作成
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )
    embed.add_field(name="付与されるロール", value=role.mention)
    embed.set_footer(text="このメッセージは認証パネルです")
    
    # ボタンの作成
    class AuthButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            
        @discord.ui.button(label="認証する", style=discord.ButtonStyle.success, custom_id="auth_button", emoji="✅")
        async def auth_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                # 既にロールを持っているかチェック
                if role in interaction.user.roles:
                    await interaction.response.send_message("既に認証済みです！", ephemeral=True)
                    return
                
                # ロールを付与
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"{role.mention} ロールを付与しました！認証完了です。", ephemeral=True)
                
            except Exception as e:
                await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)
    
    view = AuthButton()
    await interaction.response.send_message("認証パネルを設置しました！", ephemeral=True)
    await interaction.channel.send(embed=embed, view=view)

# ヘルプコマンド
@bot.tree.command(name="help", description="Botの使い方を表示します")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bot ヘルプ",
        description="利用可能なコマンド一覧",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🎯 お知らせコマンド",
        value="`/お知らせ` - 埋め込みお知らせを送信します",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ モデレーションコマンド",
        value=(
            "`/ban` - ユーザーをBANします\n"
            "`/kick` - ユーザーをキックします\n"
            "`/to` - ユーザーをタイムアウトします\n"
            "`/unto` - タイムアウトを解除します"
        ),
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ 情報コマンド",
        value="`/info` - サーバーまたはユーザーの情報を表示します",
        inline=False
    )
    
    embed.add_field(
        name="✅ 認証コマンド",
        value="`/認証` - 認証パネルを設置します",
        inline=False
    )
    
    embed.set_footer(text="各コマンドには詳細な説明があります。スラッシュ(/)を入力して確認してください。")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Botの実行
if __name__ == "__main__":
    print("Discord Bot 起動プログラム")
    print("=" * 50)
    print("\n注意: トークンは外部に漏らさないでください！\n")
    
    # トークンを入力
    TOKEN = input("Discord Botトークンを入力してください: ").strip()
    
    if not TOKEN:
        print("エラー: トークンが入力されていません")
        print("\nDiscord Botトークンの取得方法:")
        print("1. https://discord.com/developers/applications にアクセス")
        print("2. アプリケーションを選択")
        print("3. Botタブを開く")
        print("4. 'TOKEN' の下にある 'Copy' をクリック")
        print("5. ここに貼り付ける")
    else:
        print("\nBotを起動しています...")
        bot.run(TOKEN)
