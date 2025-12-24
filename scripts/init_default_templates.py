"""初始化默认消息范本脚本

功能：
1. 检查数据库中是否已有消息范本
2. 如果没有，写入默认范本
3. 支持 --force 参数强制覆盖

使用方法：
    python scripts/init_default_templates.py
    python scripts/init_default_templates.py --force
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 数据库文件路径
DATA_DIR = os.getenv("DATA_DIR", project_root)
DB_NAME = os.path.join(DATA_DIR, "loan_bot.db")

# 默认消息范本
DEFAULT_START_WORK_MESSAGE = """🇵🇭 版本一｜标准版

Good morning po! 😊 Our team is now online and ready to assist you today.

Feel free to message us anytime if you have questions or need more information.

⸻

🇵🇭 版本二｜更亲切一点

Good morning po! ☀️ We're now open and happy to assist you today.

Just send us a message if you need help or would like to learn more.

⸻

🇵🇭 版本三｜偏官方群公告

Good morning po! Our working hours have started for today.

Our team is online and ready to assist you with your inquiries.

Please feel free to message us anytime."""

DEFAULT_END_WORK_MESSAGE = """🇵🇭 版本一｜标准版

Good evening po! 🌙 Our working hours have ended for today.

Thank you for messaging us. We will respond to your inquiry as soon as possible tomorrow.

⸻

🇵🇭 版本二｜更亲切

Good evening po! 😊 We're done for today, but thank you for reaching out.

Our team will get back to you tomorrow during working hours.

⸻

🇵🇭 版本三｜官方群公告

Good evening po! Our team is now offline.

Messages received will be attended to tomorrow.

Thank you for your understanding."""

DEFAULT_WELCOME_MESSAGE = """🇵🇭 版本一｜标准版

Welcome po! 👋

Thank you for joining our group, {username}!

This group is for sharing information and updates about our services.

Please check the pinned message or message our admin if you have questions 😊

⸻

🇵🇭 版本二｜更亲切本地版

Hi po! 😊 Welcome to the group, {username}!

We're happy to have you here.

Kindly check the pinned post for important details.

Message lang po if you need any assistance.

⸻

🇵🇭 版本三｜偏官方群说明

Welcome po and thank you for joining, {username}!

This group is intended for general information and customer support only.

Our team will assist you politely during working hours.

⸻

🇵🇭 版本四｜简洁机器人版

Hello po! 👋 Welcome to our official group, {username}.

Please read the pinned message for important information.

Our support team is available during working hours 😊"""

DEFAULT_ANNOUNCEMENTS = [
    """We are a service-focused company dedicated to providing simple and reliable mobile-based solutions for everyday needs.

PH：

Kami po ay isang service-focused company na nagbibigay ng simple at maaasahang mobile-based solutions para sa araw-araw.""",
    """Our goal is to make services more accessible through clear processes and friendly assistance.

PH：

Layunin po namin na gawing mas accessible ang aming services sa pamamagitan ng malinaw na proseso at maayos na assistance.""",
    """We believe in transparency, respect, and clear communication with every customer.

PH：

Naniniwala po kami sa transparency, respeto, at malinaw na pakikipag-usap sa bawat customer.""",
]

DEFAULT_PROMOTION_MESSAGES = [
    """🔹【轮播 1｜公司介绍】

EN：

We are a service-focused company dedicated to providing simple and reliable mobile-based solutions for everyday needs.

PH：

Kami po ay isang service-focused company na nagbibigay ng simple at maaasahang mobile-based solutions para sa araw-araw.

⸻

🔹【轮播 2｜我们在做什么】

EN：

Our goal is to make services more accessible through clear processes and friendly assistance.

PH：

Layunin po namin na gawing mas accessible ang aming services sa pamamagitan ng malinaw na proseso at maayos na assistance.

⸻

🔹【轮播 3｜服务理念】

EN：

We believe in transparency, respect, and clear communication with every customer.

PH：

Naniniwala po kami sa transparency, respeto, at malinaw na pakikipag-usap sa bawat customer.

⸻

🔹【轮播 4｜团队与支持】

EN：

Our support team is trained to assist politely and answer questions during working hours.

PH：

Ang aming support team po ay handang tumulong nang maayos at sumagot sa mga tanong sa oras ng trabaho.

⸻

🔹【轮播 5｜适用人群】

EN：

Our services are suitable for individuals looking for simple and short-term solutions for everyday situations.

PH：

Ang aming services po ay angkop para sa mga naghahanap ng simple at pansamantalang solusyon para sa pang-araw-araw na pangangailangan.

⸻

🔹【轮播 6｜使用体验】

EN：

We focus on providing a smooth experience with clear steps and helpful guidance.

PH：

Pinagtutuunan po namin ng pansin ang maayos na experience, malinaw na hakbang, at helpful na guidance.

⸻

🔹【轮播 7｜信任与合规】

EN：

We respect privacy and follow responsible communication practices at all times.

PH：

Iginagalang po namin ang privacy at sumusunod sa maayos at responsableng paraan ng komunikasyon.

⸻

🔹【轮播 8｜温和 CTA】

EN：

Interested in learning more?

Feel free to message us anytime for more information.

PH：

Gusto po bang malaman pa?

Message lang po anytime para sa karagdagang impormasyon.""",
    """Our goal is to make services more accessible through clear processes and friendly assistance.

PH：

Layunin po namin na gawing mas accessible ang aming services sa pamamagitan ng malinaw na proseso at maayos na assistance.""",
    """We believe in transparency, respect, and clear communication with every customer.

PH：

Naniniwala po kami sa transparency, respeto, at malinaw na pakikipag-usap sa bawat customer.""",
]

DEFAULT_ANTI_FRAUD_MESSAGES = [
    """⚠️ Reminder po: We will never ask for your OTP, password, or private information. Please communicate only with our official admins.

⸻

🇵🇭 版本 2（更本地 Taglish）

Paalala po 😊 Hindi po kami humihingi ng OTP o password. Makipag-usap lamang po sa official admins.

⸻

🇵🇭 版本 3（最简英文）

Stay safe. We never ask for OTP, passwords, or private details. Official communication only.

⸻

🇵🇭 版本 4（温和型）

For your safety, please avoid sharing personal information and verify official accounts before responding.""",
    """⚠️ Important: Never share your OTP, password, or personal details with anyone. Only trust our official admins.

⸻

🇵🇭 版本 2

Mahalaga po: Huwag po ibahagi ang inyong OTP, password, o personal na detalye sa sinuman. Magtiwala lamang po sa aming official admins.""",
    """🔒 Security Reminder: Protect your account. We will never request your password or OTP via message.

⸻

🇵🇭 版本 2

🔒 Paalala sa Seguridad: Protektahan ang inyong account. Hindi po namin hihingin ang inyong password o OTP sa pamamagitan ng mensahe.""",
    """🛡️ Safety First: Always verify the identity of the person you're communicating with. Official admins only.

⸻

🇵🇭 版本 2

🛡️ Seguridad Una: Laging i-verify ang pagkakakilanlan ng taong kinakausap ninyo. Official admins lamang.""",
]


def check_database_exists():
    """检查数据库文件是否存在"""
    if not os.path.exists(DB_NAME):
        print(f"❌ 数据库文件不存在: {DB_NAME}")
        print("   请先运行机器人初始化数据库")
        return False
    return True


def check_group_config_exists(conn, cursor):
    """检查是否有群组配置"""
    cursor.execute("SELECT COUNT(*) FROM group_message_config")
    count = cursor.fetchone()[0]
    return count > 0


def check_templates_exist(conn, cursor, force=False):
    """检查消息范本是否存在"""
    results = {
        "group_messages": False,
        "announcements": False,
        "promotions": False,
        "anti_fraud": False,
    }

    # 检查群组消息
    cursor.execute(
        'SELECT COUNT(*) FROM group_message_config WHERE start_work_message IS NOT NULL AND start_work_message != ""'
    )
    if cursor.fetchone()[0] > 0:
        results["group_messages"] = True

    # 检查公告
    cursor.execute("SELECT COUNT(*) FROM company_announcements")
    if cursor.fetchone()[0] > 0:
        results["announcements"] = True

    # 检查宣传语录
    cursor.execute("SELECT COUNT(*) FROM company_promotion_messages")
    if cursor.fetchone()[0] > 0:
        results["promotions"] = True

    # 检查防诈骗语录
    cursor.execute("SELECT COUNT(*) FROM anti_fraud_messages")
    if cursor.fetchone()[0] > 0:
        results["anti_fraud"] = True

    return results


def init_group_messages(conn, cursor, force=False):
    """初始化群组消息配置"""
    # 检查是否有群组配置
    if not check_group_config_exists(conn, cursor):
        print("⚠️  没有群组配置，无法写入群组消息")
        print("   请先使用 /groupmsg_setup 在群组中添加配置")
        return 0

    # 获取所有群组配置
    cursor.execute("SELECT chat_id, chat_title FROM group_message_config")
    configs = cursor.fetchall()

    updated_count = 0

    for config in configs:
        chat_id = config[0]
        chat_title = config[1] or f"ID: {chat_id}"

        # 检查是否已有消息（改进空消息检测）
        cursor.execute(
            """
            SELECT start_work_message, end_work_message, welcome_message 
            FROM group_message_config 
            WHERE chat_id = ?
        """,
            (chat_id,),
        )
        row = cursor.fetchone()

        # 改进空消息检测：检查是否为None或空字符串或只包含空白字符
        def is_empty_message(msg):
            return msg is None or not msg or not msg.strip()

        has_start = not is_empty_message(row[0])
        has_end = not is_empty_message(row[1])
        has_welcome = not is_empty_message(row[2])

        # 如果force=False且所有消息都已存在，则跳过
        if not force and has_start and has_end and has_welcome:
            print(f"   ⏭️  跳过 {chat_title} (已有消息)")
            continue

        # 更新消息（填充空消息或强制覆盖）
        updates = []
        params = []

        # 如果force=True，或者消息为空，则填充
        if force or not has_start:
            updates.append("start_work_message = ?")
            params.append(DEFAULT_START_WORK_MESSAGE)

        if force or not has_end:
            updates.append("end_work_message = ?")
            params.append(DEFAULT_END_WORK_MESSAGE)

        if force or not has_welcome:
            updates.append("welcome_message = ?")
            params.append(DEFAULT_WELCOME_MESSAGE)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(chat_id)

            cursor.execute(
                f"""
                UPDATE group_message_config 
                SET {', '.join(updates)}
                WHERE chat_id = ?
            """,
                params,
            )

            updated_count += 1
            print(f"   ✅ {chat_title} - 已写入默认消息")

    return updated_count


def init_announcements(conn, cursor, force=False):
    """初始化公司公告"""
    cursor.execute("SELECT COUNT(*) FROM company_announcements")
    count = cursor.fetchone()[0]

    if not force and count > 0:
        print(f"   ⏭️  跳过公司公告 (已有 {count} 条)")
        return 0

    if force:
        # 删除现有公告
        cursor.execute("DELETE FROM company_announcements")

    added_count = 0
    for announcement in DEFAULT_ANNOUNCEMENTS:
        cursor.execute(
            """
            INSERT INTO company_announcements (message, is_active)
            VALUES (?, 1)
        """,
            (announcement,),
        )
        added_count += 1

    print(f"   ✅ 已写入 {added_count} 条公司公告")
    return added_count


def init_promotions(conn, cursor, force=False):
    """初始化公司宣传轮播语录"""
    cursor.execute("SELECT COUNT(*) FROM company_promotion_messages")
    count = cursor.fetchone()[0]

    if not force and count > 0:
        print(f"   ⏭️  跳过公司宣传轮播语录 (已有 {count} 条)")
        return 0

    if force:
        # 删除现有语录
        cursor.execute("DELETE FROM company_promotion_messages")

    added_count = 0
    for promotion in DEFAULT_PROMOTION_MESSAGES:
        cursor.execute(
            """
            INSERT INTO company_promotion_messages (message, is_active)
            VALUES (?, 1)
        """,
            (promotion,),
        )
        added_count += 1

    print(f"   ✅ 已写入 {added_count} 条公司宣传轮播语录")
    return added_count


def init_anti_fraud(conn, cursor, force=False):
    """初始化防诈骗语录"""
    cursor.execute("SELECT COUNT(*) FROM anti_fraud_messages")
    count = cursor.fetchone()[0]

    if not force and count > 0:
        print(f"   ⏭️  跳过防诈骗语录 (已有 {count} 条)")
        return 0

    if force:
        # 删除现有语录
        cursor.execute("DELETE FROM anti_fraud_messages")

    added_count = 0
    for anti_fraud in DEFAULT_ANTI_FRAUD_MESSAGES:
        cursor.execute(
            """
            INSERT INTO anti_fraud_messages (message, is_active)
            VALUES (?, 1)
        """,
            (anti_fraud,),
        )
        added_count += 1

    print(f"   ✅ 已写入 {added_count} 条防诈骗语录")
    return added_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="初始化默认消息范本")
    parser.add_argument("--force", action="store_true", help="强制覆盖已有数据")
    args = parser.parse_args()

    print("=" * 60)
    print("初始化默认消息范本")
    print("=" * 60)
    print(f"数据库路径: {DB_NAME}")
    print(f"强制模式: {'是' if args.force else '否'}")
    print()

    # 检查数据库
    if not check_database_exists():
        sys.exit(1)

    # 连接数据库
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # 检查现有数据
        print("📋 检查现有数据...")
        templates_status = check_templates_exist(conn, cursor, args.force)

        print(f"   群组消息: {'✅ 已有' if templates_status['group_messages'] else '❌ 无'}")
        print(f"   公司公告: {'✅ 已有' if templates_status['announcements'] else '❌ 无'}")
        print(f"   宣传语录: {'✅ 已有' if templates_status['promotions'] else '❌ 无'}")
        print(f"   防诈骗语录: {'✅ 已有' if templates_status['anti_fraud'] else '❌ 无'}")
        print()

        if not args.force and all(templates_status.values()):
            print("✅ 所有消息范本都已存在")
            print("   如需覆盖，请使用 --force 参数")
            return

        # 开始写入
        print("📝 开始写入默认消息范本...")
        print()

        total_updated = 0

        # 1. 群组消息
        print("1. 群组消息配置（开工、收工、欢迎信息）")
        print("-" * 60)
        updated = init_group_messages(conn, cursor, args.force)
        total_updated += updated
        print()

        # 2. 公司公告
        print("2. 公司公告")
        print("-" * 60)
        updated = init_announcements(conn, cursor, args.force)
        total_updated += updated
        print()

        # 3. 公司宣传轮播语录
        print("3. 公司宣传轮播语录")
        print("-" * 60)
        updated = init_promotions(conn, cursor, args.force)
        total_updated += updated
        print()

        # 4. 防诈骗语录
        print("4. 防诈骗语录")
        print("-" * 60)
        updated = init_anti_fraud(conn, cursor, args.force)
        total_updated += updated
        print()

        # 提交事务
        conn.commit()

        # 显示结果
        print("=" * 60)
        print("✅ 初始化完成！")
        print("=" * 60)
        print(f"总共写入/更新: {total_updated} 项")
        print()
        print("💡 提示：")
        print("   - 使用 'python 检查消息范本.py' 验证写入结果")
        print("   - 使用机器人命令查看和编辑消息内容")
        print("   - 群组消息需要先有群组配置（使用 /groupmsg_setup）")

    except Exception as e:
        conn.rollback()
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
