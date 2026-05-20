import imaplib
import email
from email.header import decode_header, make_header
import re
import time
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import sqlite3
import unicodedata
import threading
from datetime import datetime
import telebot

# ======================
# CONFIG
# ======================

BOT_TOKEN = os.getenv("UNG360_TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("UNG360_TELEGRAM_CHAT_ID")

# ======================
# GMAIL CONFIG
# ======================

EMAIL = os.getenv("UNG360_EMAIL")
PASSWORD = os.getenv("UNG360_EMAIL_PASSWORD")

IMAP_SERVER = "imap.gmail.com"

POLL_INTERVAL = 600          # 10 phút
HEARTBEAT_INTERVAL = 9000    # 2.5 giờ
MAIL_SEARCH_LIMIT = 20

DB_PATH = "data/ung360.db"
PROCESSED_FILE = "data/processed_mails.json"
received_periods = set()
missing_alert_sent = set()
camera_pending = {}
camera_alerted = {}
aibox_pending = {}

# ======================
# ALERT RULES
# ======================

UNG_ALERT = -15
HOAN_ALERT = -15
LOI_GUI_ALERT = 5000

GD_LOI_ALERT = 500
THIET_HAI_ALERT = 10_000_000

BASELINE_CODES = {
    "7": 500,
    "41": 250,
    "-1": 250
}

BASELINE_MULTIPLIER = 2
OTHER_CODE_ALERT = 10

BLACKLIST_CHANGE_ALERT = 30000

EVS_RESULT_CODE_DESCRIPTIONS = {
    "-2": "Không lấy được thông tin của user",
    "-1": "Thuê bao không tồn tại hoặc không hợp lệ",
    "0": "Giao dịch thành công",
    "1": "Yêu cầu không đúng định dạng",
    "2": "IP không được phép truy cập",
    "3": "Đối tác không tồn tại",
    "4": "Đối tác chưa login hoặc chưa thành công",
    "5": "Request Invalid Data",
    "6": "Đối tác đã bị khóa",
    "7": "Giao dịch thất bại. Lỗi ngoại lệ",
    "9": "Session hết hiệu lực",
    "10": "Session không hợp lệ",
    "11": "Không được truy cập vào thời điểm hiện tại",
    "12": "User chưa được phân quyền SOAP",
    "13": "Vượt quá session tối đa cho phép",
    "14": "Quá số kết nối cho phép",
    "15": "Session chưa được tạo",
    "16": "Quá số user login trong một thời điểm",
    "17": "Không đúng initiator",
    "18": "Session đã login thành công và còn hiệu lực",
    "19": "Không đủ tham số",
    "20": "Session chưa được login",
    "21": "IP đẩy lệnh không đúng IP khi login session",
    "25": "PIN nhập không đúng 6 ký tự số",
    "29": "Kiểu tài khoản khác stock",
    "30": "Target khác postpaid và airtime",
    "31": "Số tiền/số lượng không hợp lệ",
    "32": "Thuê bao đang trong trạng thái create",
    "33": "Thuê bao đang trong trạng thái valid",
    "34": "Thuê bao đang trong trạng thái deleted",
    "35": "Thuê bao là thuê bao trả sau",
    "36": "Thuê bao trả trước bị khóa chức năng nạp thẻ",
    "37": "Thuê bao trả trước không bị khóa chức năng nạp thẻ",
    "38": "Thuê bao trả trước gọi hàm trả sau",
    "39": "Thuê bao trả sau gọi hàm trả trước",
    "40": "Thuê bao bị khóa",
    "41": "Thuê bao không đủ tiền để giao dịch",
    "42": "View tài khoản IN thành công",
    "43": "Thuê bao không đủ tiền để chuyển cho reseller",
    "45": "View tài khoản IN không thành công",
    "46": "Mã giao dịch không hợp lệ",
    "47": "Profile thuê bao bị chặn nạp thẻ qua EVS",
    "48": "Mã giao dịch ứng tiền không tồn tại trên hệ thống",
    "49": "ID không phải là ID của giao dịch ứng tiền",
    "50": "ID ứng tiền không thành công",
    "51": "Mã giao dịch ứng tiền không phải của thuê bao gửi",
    "52": "Số thuê bao nhận không hợp lệ hoặc không tồn tại",
    "53": "Sai mã PIN của số thuê bao gửi",
    "54": "Có nhiều hơn 1 tài khoản có MSISDN là thuê bao gửi",
    "55": "Thuê bao gửi bị khóa chức năng thanh toán",
    "56": "Số thuê bao gửi không tồn tại hoặc không hợp lệ",
    "57": "Có nhiều hơn 1 tài khoản có MSISDN là thuê bao nhận",
    "58": "Check opt không thành công",
    "59": "Thông tin số gửi không đúng định dạng",
    "60": "Mã ID đối tác gửi lên đã tồn tại",
    "61": "Độ dài reference2 phải nhỏ hơn hoặc bằng 20",
    "62": "Giao dịch hoàn ứng thất bại vì khách hàng đã trả hết nợ",
    "63": "Tổng số tiền hoàn ứng vượt quá số tiền ứng + fee",
    "64": "Số điện thoại không tồn tại hoặc không còn hiệu lực",
    "65": "Không thể reset PIN/modify phone cho nhiều hơn 1 tài khoản",
    "66": "Số thuê bao không thuộc quyền quản lý của user",
    "67": "Truyền fee khác 0 khi chưa trả hết nợ gốc",
    "68": "Truyền fee bằng 0 khi đã trả hết nợ gốc",
    "69": "Không parse được XML từ response FastPay",
    "70": "Không nhận được kết quả từ FastPay",
    "71": "Số thuê bao EZ chưa đăng ký sử dụng chức năng này",
    "72": "Số thuê bao bán không hợp lệ",
    "73": "Số thuê bao bán không đúng",
    "74": "Số thuê bao EZ đã tồn tại trên hệ thống",
    "75": "Số thuê bao bán đã tồn tại trên hệ thống",
    "76": "Số bán không thể là SIM EZ",
    "77": "Số tiền thanh toán cước/ứng tiền vượt quá mức cho phép",
    "78": "Số tiền thanh toán cước/ứng tiền nhỏ hơn mức cho phép",
    "79": "Số lần ứng tiền chưa hoàn ứng 100% quá số lần cho phép",
    "80": "Có ngoại lệ xảy ra khi xử lý request",
    "81": "Số tiền fee tặng tiền không hợp lệ",
    "82": "Số tiền tặng nhỏ hơn mức cho phép",
    "83": "Số tiền tặng nhiều hơn mức cho phép",
    "84": "Số tiền phí nhỏ hơn mức cho phép",
    "85": "Số tiền phí nhiều hơn mức cho phép",
    "86": "Số tiền phí nhiều hơn số tiền tặng",
    "87": "Thuê bao không thuộc đầu số cho phép",
    "88": "Truyền số tiền phí không đúng",
    "89": "Số tiền chia sẻ nhiều hơn mức cho phép trong ngày",
    "90": "Có ngoại lệ khi check điều kiện chia sẻ",
    "91": "Số tiền chia sẻ không nằm trong mệnh giá cho phép",
    "92": "Số lượng không hợp lệ",
    "93": "Đơn giá mua phải nhỏ hơn đơn giá bán",
    "94": "Số lượng nhỏ hơn mức cho phép",
    "95": "Số lượng lớn hơn mức cho phép",
    "96": "Đơn giá bán nhỏ hơn mức cho phép",
    "97": "Đơn giá bán lớn hơn mức cho phép",
    "98": "Hệ thống không hỗ trợ loại tài khoản",
    "99": "User chưa được map với loại tài khoản phụ nào",
    "100": "User chưa được map với tài khoản DSP nào",
    "101": "Thuê bao trả sau bị khóa chức năng nạp thẻ",
    "103": "Giao dịch trùng lặp với cùng username và MSISDN",
    "1001": "Mandatory parameter missing",
    "1002": "Invalid parameter length",
    "1003": "Invalid parameter syntax",
    "1004": "Other error in request",
    "1071": "Amount not within range",
    "1072": "Invalid date time format",
    "1073": "Old and new PIN same",
    "1074": "Invalid transaction ID",
    "1075": "New PIN and confirm new PIN mismatch",
    "1396": "PGS internal error",
    "1403": "PMI no PM connection",
    "1404": "PMI request timeout",
    "1501": "EZI service busy",
    "1502": "EZI response invalid",
    "1503": "EZI no SCLogic connection",
    "1504": "EZI request timeout",
    "1505": "EZI bad data",
    "1506": "EZI bad transaction ID",
    "1507": "EZI bad MSISDN",
    "1508": "EZI bad session ID",
    "1509": "EZI bad amount",
    "1510": "EZI bad login",
    "1511": "EZI amount greater than VC balances",
    "3500": "Partial success",
    "3502": "PIN modification failure",
    "3503": "Reseller locked",
    "3504": "Reseller account not found",
    "3505": "Insufficient credit",
    "3506": "Subscriber busy",
    "3507": "Destination subscriber busy",
    "3508": "Error limit reached",
    "3509": "Consecutive error limit reached",
    "3510": "Wrong PIN",
    "3511": "R2R to same account",
    "3512": "Amount less than min allowed",
    "3513": "Amount higher than max allowed",
    "3514": "Invalid transaction",
    "3515": "Originator validity expired",
    "3516": "Destination validity expired",
    "3517": "Originator PIN not enabled",
    "3518": "Commission table problem",
    "3519": "Configuration data problem",
    "3520": "Unauthorized transaction in profile",
    "3521": "Invalid level",
    "3522": "Barred de-allocation",
    "3523": "Parameter missing in XML/http request",
    "3524": "Malformed request",
    "3525": "NOK XML parse error",
    "3526": "Malformed XML prolog",
    "3527": "ICC subscriber in CREATED state",
    "3528": "ICC subscriber in VALID state",
    "3530": "ICC subscriber in BLOCK state",
    "3531": "Scratch card recharge suspended",
    "3532": "Reseller untick deallocation flag",
    "3533": "Reseller B does not have sufficient credit",
    "3534": "Reseller untick end user flag",
    "3535": "R2R alloc wrong whitelist rule",
    "3536": "R2R dealloc wrong whitelist rule",
    "5000": "Connection timeout khi nhận reply",
}

missing_config = [
    name for name, value in {
        "UNG360_TELEGRAM_BOT_TOKEN": BOT_TOKEN,
        "UNG360_TELEGRAM_CHAT_ID": CHAT_ID,
        "UNG360_EMAIL": EMAIL,
        "UNG360_EMAIL_PASSWORD": PASSWORD,
    }.items()
    if not value
]

if missing_config:
    raise RuntimeError("Missing required environment variables: " + ", ".join(missing_config))

bot = telebot.TeleBot(BOT_TOKEN)


# ======================
# TELEGRAM COMMANDS
# ======================

def is_authorized_chat(message):
    return str(message.chat.id) == str(CHAT_ID)


def send_bot_reply(message, text):
    bot.reply_to(message, text)


def get_message_text(message):
    return (message.text or "").strip()


def get_normalized_message_text(message):
    return normalize_text(get_message_text(message)).strip()


def build_main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("Tổng lỗi hôm nay"),
        telebot.types.KeyboardButton("Trạng thái"),
        telebot.types.KeyboardButton("Bot còn chạy không"),
        telebot.types.KeyboardButton("Chat ID"),
        telebot.types.KeyboardButton("Trợ giúp"),
        telebot.types.KeyboardButton("Ẩn menu"),
    )
    return markup


def send_main_menu(message):
    bot.reply_to(
        message,
        "Mình đây. Bạn muốn kiểm tra gì?",
        reply_markup=build_main_menu()
    )


def get_db_count(table):
    if not os.path.exists(DB_PATH):
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_monitor_status_text():
    status_lines = [
        "* UNG360 Monitor Status",
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Poll interval: {POLL_INTERVAL} seconds",
        f"Heartbeat interval: {HEARTBEAT_INTERVAL} seconds",
        f"Received periods in memory: {len(received_periods)}",
        f"Camera pending: {len(camera_pending)}",
        f"AIBOX pending: {len(aibox_pending)}",
    ]

    try:
        status_lines.extend([
            f"KPI rows: {get_db_count('kpi_data')}",
            f"GD loi rows: {get_db_count('gd_loi_data')}",
            f"Same-period rows: {get_db_count('same_period_data')}",
            f"UT360 scoring rows: {get_db_count('ut360_scoring_data')}",
        ])
    except Exception as e:
        status_lines.append(f"DB status error: {e}")

    return "\n".join(status_lines)


def add_code_count(code_counts, code, value):
    if not value:
        return

    code_counts[str(code)] = code_counts.get(str(code), 0) + int(value)


def get_result_code_description(code):
    return EVS_RESULT_CODE_DESCRIPTIONS.get(str(code).strip(), "")


def format_result_code_count(code, count):
    description = get_result_code_description(code)
    line = f"- Code {code}: {count:,} GD"
    if description:
        line += f" - {description}"
    return line


def get_today_error_summary_text():
    if not os.path.exists(DB_PATH):
        return "Chưa có database để kiểm tra lỗi."

    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT report_time, total_errors, code_7, code_41, code_minus_1, other_codes
        FROM gd_loi_data
        WHERE report_time LIKE ?
        ORDER BY report_time ASC, id ASC
    """, (today + "%",))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"Chưa có dữ liệu lỗi giao dịch hôm nay ({datetime.now().strftime('%d/%m')})."

    daily_rows = [
        row for row in rows
        if str(row["report_time"]).endswith("00:00:00") and int(row["total_errors"] or 0) > 0
    ]
    base_row = daily_rows[-1] if daily_rows else None
    detail_rows = [row for row in rows if row is not base_row]

    total_errors = int(base_row["total_errors"] or 0) if base_row else 0
    code_counts = {}

    if base_row:
        add_code_count(code_counts, "7", base_row["code_7"])
        add_code_count(code_counts, "41", base_row["code_41"])
        add_code_count(code_counts, "-1", base_row["code_minus_1"])
        try:
            for code, count in json.loads(base_row["other_codes"] or "{}").items():
                add_code_count(code_counts, code, count)
        except Exception:
            pass

    for row in detail_rows:
        total_errors += int(row["total_errors"] or 0)
        add_code_count(code_counts, "7", row["code_7"])
        add_code_count(code_counts, "41", row["code_41"])
        add_code_count(code_counts, "-1", row["code_minus_1"])
        try:
            for code, count in json.loads(row["other_codes"] or "{}").items():
                add_code_count(code_counts, code, count)
        except Exception:
            pass

    lines = [
        f"* Tổng lỗi từ đầu ngày - {datetime.now().strftime('%d/%m %H:%M')}",
        f"Tổng lỗi: {total_errors:,} GD",
        f"Số bản ghi đã đọc: {len(rows)}",
    ]

    if base_row:
        lines.append(f"Mốc tổng hợp: {base_row['report_time']}")

    if code_counts:
        lines.append("")
        lines.append("Mã lỗi:")
        for code, count in sorted(code_counts.items(), key=lambda item: item[1], reverse=True):
            lines.append(format_result_code_count(code, count))
    else:
        lines.append("")
        lines.append("Chưa có số liệu mã lỗi.")

    return "\n".join(lines)


@bot.message_handler(commands=["start", "help"])
def handle_help(message):
    if not is_authorized_chat(message):
        send_bot_reply(message, f"Chat ID của bạn: {message.chat.id}")
        return

    send_bot_reply(
        message,
        "Các lệnh đang hỗ trợ:\n"
        "/status - Xem trạng thái monitor\n"
        "/errors - Tổng lỗi từ đầu ngày và mã lỗi\n"
        "/alive - Kiểm tra bot còn chạy không\n"
        "/chatid - Xem chat id hiện tại\n"
        "/help - Xem danh sách lệnh\n\n"
        "Bạn cũng có thể nhắn tự nhiên:\n"
        "trạng thái\n"
        "tổng lỗi hôm nay\n"
        "bot còn chạy không\n"
        "id\n"
        "giúp tôi"
    )


@bot.message_handler(commands=["status"])
def handle_status(message):
    if not is_authorized_chat(message):
        return

    send_bot_reply(message, get_monitor_status_text())


@bot.message_handler(commands=["errors", "loi"])
def handle_today_errors(message):
    if not is_authorized_chat(message):
        return

    send_bot_reply(message, get_today_error_summary_text())


@bot.message_handler(commands=["alive", "ping"])
def handle_alive(message):
    if not is_authorized_chat(message):
        return

    send_bot_reply(message, f"UNG360 monitor alive - {datetime.now().strftime('%d/%m %H:%M:%S')}")


@bot.message_handler(commands=["chatid"])
def handle_chat_id(message):
    send_bot_reply(message, f"Chat ID của bạn: {message.chat.id}")


@bot.message_handler(func=lambda message: True)
def handle_unknown_message(message):
    if not is_authorized_chat(message):
        return

    text = get_normalized_message_text(message)

    if text in {"alo", "hello", "hi", "chao", "chao bot", "menu", "mo menu"}:
        send_main_menu(message)
        return

    if text in {"an menu", "dong menu", "hide menu"}:
        bot.reply_to(
            message,
            "Đã ẩn menu.",
            reply_markup=telebot.types.ReplyKeyboardRemove()
        )
        return

    if text in {"help", "tro giup", "giup toi", "huong dan", "lenh"}:
        handle_help(message)
        return

    if text in {"status", "trang thai", "tinh trang", "kiem tra", "check", "monitor"}:
        handle_status(message)
        return

    if text in {
        "tong loi",
        "tong loi hom nay",
        "loi hom nay",
        "ma loi",
        "ma loi hom nay",
        "kiem tra loi",
        "thong ke loi",
        "gd loi hom nay",
    }:
        handle_today_errors(message)
        return

    if text in {
        "alive",
        "ping",
        "bot con chay khong",
        "con chay khong",
        "bot song khong",
        "bot ok khong",
        "ok khong",
    }:
        handle_alive(message)
        return

    if text in {"id", "chat id", "chatid", "ma chat", "lay id"}:
        handle_chat_id(message)
        return

    send_bot_reply(message, "Mình chưa hiểu lệnh này. Nhắn alo để mở menu lựa chọn.")


def run_telegram_polling():
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            write_error_log(f"Telegram polling error: {e}")
            time.sleep(10)


def start_telegram_bot():
    polling_thread = threading.Thread(target=run_telegram_polling, daemon=True)
    polling_thread.start()
    print("Telegram command listener started")


# ======================
# UTILS
# ======================

def to_int(value):
    if not value:
        return 0
    return int(
        str(value)
        .replace(",", "")
        .replace(".", "")
        .strip()
    )


def send_alert(message):
    bot.send_message(CHAT_ID, message)
    write_alert_log(message)


def write_named_log(folder, filename, body):
    os.makedirs(folder, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logfile = os.path.join(folder, filename)

    with open(logfile, "a", encoding="utf-8") as f:
        f.write("\n")
        f.write("=" * 70)
        f.write("\n")
        f.write(f"[{now}]\n\n")
        f.write(body)
        f.write("\n")


def write_kpi_log(body):
    today = datetime.now().strftime("%Y-%m-%d")
    write_named_log("logs/kpi", f"{today}.log", body)


def write_gd_loi_log(body):
    today = datetime.now().strftime("%Y-%m-%d")
    write_named_log("logs/gd_loi", f"{today}.log", body)


def write_ut360_scoring_log(body):
    today = datetime.now().strftime("%Y-%m-%d")
    write_named_log("logs/ut360_scoring", f"{today}.log", body)

def write_same_period_log(body):
    today = datetime.now().strftime("%Y-%m-%d")
    write_named_log("logs/same_period", f"{today}.log", body)

def write_urgent_alert_log(body):
    today = datetime.now().strftime("%Y-%m-%d")
    write_named_log("logs/urgent_alert", f"{today}.log", body)


def write_alert_log(body):
    today = datetime.now().strftime("%Y-%m-%d")
    write_named_log("logs/alert", f"{today}_alert.log", body)


def write_error_log(body):
    today = datetime.now().strftime("%Y-%m-%d")
    write_named_log("logs/error", f"{today}_error.log", body)

def write_ignored_mail_log(body):
    today = datetime.now().strftime("%Y-%m-%d")
    write_named_log("logs/ignored", f"{today}.log", body)


def normalize_text(text):
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    return text.lower()


def decode_mime_header(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def decode_payload(payload, charset):
    if not payload:
        return ""

    encodings = [charset, "utf-8", "cp1258", "latin-1"]
    for encoding in encodings:
        if not encoding:
            continue
        try:
            return payload.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue

    return payload.decode(errors="ignore")


def get_email_body(msg):
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                body += decode_payload(payload, part.get_content_charset())
    else:
        payload = msg.get_payload(decode=True)
        body = decode_payload(payload, msg.get_content_charset())

    return body


def clean_mail_body(body):
    stop_keywords = [
        "📎 File đính kèm:",
        "IMPORTANT NOTICE:",
        "THÔNG BÁO BẢO MẬT:",
    ]

    for keyword in stop_keywords:
        if keyword in body:
            body = body.split(keyword)[0]

    lines = body.splitlines()
    clean_lines = []
    skip_forward_header = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("________________________________"):
            skip_forward_header = True
            continue

        if skip_forward_header:
            if (
                stripped.startswith("From:")
                or stripped.startswith("Sent:")
                or stripped.startswith("To:")
                or stripped.startswith("Subject:")
            ):
                continue
            skip_forward_header = False

        clean_lines.append(line)

    return "\n".join(clean_lines).strip()


def load_processed_mails():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(PROCESSED_FILE):
        return set()

    try:
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_processed_mails(processed):
    os.makedirs("data", exist_ok=True)

    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed), f, ensure_ascii=False, indent=2)


def get_mail_unique_id(msg, fallback_num):
    message_id = msg.get("Message-ID")
    if message_id:
        return message_id.strip()
    return str(fallback_num)

def mark_received(mail_type, period_key):
    received_periods.add(f"{mail_type}_{period_key}")


def has_received(mail_type, period_key):
    key = f"{mail_type}_{period_key}"
    if key in received_periods:
        return True

    if has_received_in_history(mail_type, period_key):
        received_periods.add(key)
        return True

    return False

def period_key_from_datetime_text(value):
    if not value:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y%m%d%H")
        except ValueError:
            pass

    return None

def has_received_in_history(mail_type, period_key):
    if mail_type == "kpi":
        return has_period_in_db("kpi_data", "report_time", period_key)

    if mail_type == "same_period":
        return has_same_period_in_db(period_key)

    if mail_type == "mds":
        return has_mds_period_in_log(period_key)

    return False

def has_period_in_db(table, column, period_key):
    if not os.path.exists(DB_PATH):
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT {column} FROM {table}")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        if period_key_from_datetime_text(row[0]) == period_key:
            return True

    return False

def has_same_period_in_db(period_key):
    if not os.path.exists(DB_PATH):
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT raw_text FROM same_period_data")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        body = row[0] or ""
        time_match = re.search(
            r'tu\s+(\d{1,2}h)\s*-\s*(\d{1,2}h)',
            body,
            re.IGNORECASE
        )
        date_match = re.search(r'Ung360\s+(\d{4}-\d{2}-\d{2})', body)

        if date_match and time_match:
            end_hour = int(time_match.group(2).replace("h", ""))
            period_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            existing_key = period_date.strftime("%Y%m%d") + f"{end_hour:02d}"
            if existing_key == period_key:
                return True

    return False

def has_mds_period_in_log(period_key):
    try:
        dt = datetime.strptime(period_key, "%Y%m%d%H")
    except ValueError:
        return False

    logfile = os.path.join("logs", "mds", f"{dt.strftime('%Y-%m-%d')}.log")
    if not os.path.exists(logfile):
        return False

    with open(logfile, "r", encoding="utf-8") as f:
        content = f.read()

    expected = f"[Ung360MDS {dt.strftime('%Y-%m-%d %H')}:"
    return expected in content

# ======================
# DETECT MAIL TYPES
# ======================

def is_gd_loi_mail(body):
    text = normalize_text(body)
    return (
        "UNG360-ALERT" in body
        or "gd loi" in text
        or "bao cao loi giao dich" in text
        or "tong so loi" in text
    )


def is_ut360_scoring_mail(body):
    text = normalize_text(body)
    return (
        "[UT360]" in body
        or "UT360 Scoring System" in body
        or "thong ke scoring" in text
        or "thong ke service type" in text
    )
    
def is_same_period_mail(body):
    text = normalize_text(body)
    return (
        "doanh thu cung ky" in text
    )

def is_ung_service_daily_report(subject, body):
    text = normalize_text(subject + "\n" + body)
    return (
        "bao cao tong hop hang ngay dich vu ung 360" in text
        or (
            "dich vu ung 360" in text
            and "thoi gian tao bao cao" in text
            and "doanh thu ung" in text
            and "doanh thu hoan ung" in text
        )
    )

def is_kafka_monitoring_mail(subject, body):
    text = normalize_text(subject + "\n" + body)
    return (
        "monitoring - kafka topic alert" in text
        or "kafka message count bat thuong" in text
        or (
            "kafka monitor" in text
            and "topic" in text
            and "threshold" in text
            and "status" in text
        )
    )

def is_mds_mail(body):
    return "MDS" in body.upper()

def is_kpi_ung360_mail(body):
    return bool(re.search(
        r'\[Ung360\s+[\d-]+\s+\d{2}:\d{2}:\d{2}\]',
        body
    ))
    
def is_urgent_gd_alert(subject, body):
    raw_text = (subject + "\n" + body).upper()
    text = normalize_text(subject + "\n" + body)

    return (
        "UNG360-SERVICE" in raw_text
        or "canh bao:" in text
        or "trong 30 phut" in text
    )

def is_camera_mail(subject, body):
    text = normalize_text(subject + "\n" + body)
    return (
        "camera mat ket noi" in text
        or "camera da ket noi lai" in text
    )

def is_camera_down(subject, body):
    text = normalize_text(subject + "\n" + body)
    return "camera mat ket noi" in text


def is_camera_recovery(subject, body):
    text = normalize_text(subject + "\n" + body)
    return "camera da ket noi lai" in text


def is_aibox_mail(subject, body):
    text = normalize_text(subject + "\n" + body)
    return (
        "aibox mat ket noi" in text
        or "aibox da ket noi lai" in text
        or "aibox khoi phuc" in text
        or "tai nguyen vuot nguong" in text
        or "tai nguyen khoi phuc" in text
        or "tai nguyen da khoi phuc" in text
        or "tai nguyen binh thuong" in text
    )


def is_aibox_down(subject, body):
    text = normalize_text(subject + "\n" + body)
    return "aibox mat ket noi" in text


def is_aibox_recovery(subject, body):
    text = normalize_text(subject + "\n" + body)
    return (
        "aibox da ket noi lai" in text
        or "aibox khoi phuc" in text
    )


def is_aibox_resource_alert(subject, body):
    text = normalize_text(subject + "\n" + body)
    return "tai nguyen vuot nguong" in text


def is_aibox_resource_recovery(subject, body):
    text = normalize_text(subject + "\n" + body)
    return (
        "tai nguyen khoi phuc" in text
        or "tai nguyen da khoi phuc" in text
        or "tai nguyen binh thuong" in text
    )

def detect_mail_type(subject, body):
    if is_urgent_gd_alert(subject, body):
        return "urgent_gd_alert"
    if is_ut360_scoring_mail(body):
        return "ut360_scoring"
    if is_gd_loi_mail(body):
        return "gd_loi"
    if is_same_period_mail(body):
        return "same_period"
    if is_ung_service_daily_report(subject, body):
        return "ung_service_daily"
    if is_kafka_monitoring_mail(subject, body):
        return "kafka_monitoring"
    if is_mds_mail(body):
        return "mds"
    if is_aibox_mail(subject, body):
        return "aibox"
    if is_camera_mail(subject, body):
        return "camera"
    if is_kpi_ung360_mail(body):
        return "kpi"
    return None

# ======================
# DATABASE
# ======================

def init_db():
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gd_loi_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            report_time TEXT,
            total_errors INTEGER,
            ung_errors INTEGER,
            hoanung_errors INTEGER,
            damage_vnd INTEGER,
            code_7 INTEGER,
            code_41 INTEGER,
            code_minus_1 INTEGER,
            other_codes TEXT,
            raw_text TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kpi_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            report_time TEXT,
            ung_value INTEGER,
            ung_percent INTEGER,
            hoan_value INTEGER,
            hoan_percent INTEGER,
            fee_value INTEGER,
            fee_percent INTEGER,
            free_value INTEGER,
            free_percent INTEGER,
            quota_value INTEGER,
            quota_percent INTEGER,
            invite INTEGER,
            gui_ok INTEGER,
            loi_gui INTEGER,
            neif10 INTEGER,
            tapping INTEGER,
            raw_text TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ut360_scoring_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            report_date TEXT,
            free_count INTEGER,
            fee_count INTEGER,
            quota_count INTEGER,
            total_isdn INTEGER,
            blacklist_mvno_change INTEGER,
            blacklist_postpaid_change INTEGER,
            neif10_total INTEGER,
            tapping_total INTEGER,
            isdn_new INTEGER,
            raw_text TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS same_period_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            time_range TEXT,
            ung_value INTEGER,
            ung_diff INTEGER,
            ung_percent INTEGER,
            hoan_value INTEGER,
            hoan_diff INTEGER,
            hoan_percent INTEGER,
            fee_value INTEGER,
            fee_diff INTEGER,
            fee_percent INTEGER,
            free_value INTEGER,
            free_diff INTEGER,
            free_percent INTEGER,
            quota_value INTEGER,
            quota_diff INTEGER,
            quota_percent INTEGER,
            raw_text TEXT
        )
    """)

    conn.commit()
    conn.close()
    
    
def insert_kpi_data(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO kpi_data (
            created_at,
            report_time,
            ung_value,
            ung_percent,
            hoan_value,
            hoan_percent,
            fee_value,
            fee_percent,
            free_value,
            free_percent,
            quota_value,
            quota_percent,
            invite,
            gui_ok,
            loi_gui,
            neif10,
            tapping,
            raw_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("report_time", ""),
        data.get("ung_value", 0),
        data.get("ung_percent", 0),
        data.get("hoan_value", 0),
        data.get("hoan_percent", 0),
        data.get("fee_value", 0),
        data.get("fee_percent", 0),
        data.get("free_value", 0),
        data.get("free_percent", 0),
        data.get("quota_value", 0),
        data.get("quota_percent", 0),
        data.get("invite", 0),
        data.get("gui_ok", 0),
        data.get("loi_gui", 0),
        data.get("neif10", 0),
        data.get("tapping", 0),
        data.get("raw_text", "")
    ))

    conn.commit()
    conn.close()
    

def insert_gd_loi_data(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO gd_loi_data (
            created_at,
            report_time,
            total_errors,
            ung_errors,
            hoanung_errors,
            damage_vnd,
            code_7,
            code_41,
            code_minus_1,
            other_codes,
            raw_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("report_time", ""),
        data.get("total_errors", 0),
        data.get("ung_errors", 0),
        data.get("hoanung_errors", 0),
        data.get("damage_vnd", 0),
        data.get("code_7", 0),
        data.get("code_41", 0),
        data.get("code_minus_1", 0),
        json.dumps(data.get("other_codes", {}), ensure_ascii=False),
        data.get("raw_text", "")
    ))

    conn.commit()
    conn.close()


def insert_ut360_scoring_data(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ut360_scoring_data (
            created_at,
            report_date,
            free_count,
            fee_count,
            quota_count,
            total_isdn,
            blacklist_mvno_change,
            blacklist_postpaid_change,
            neif10_total,
            tapping_total,
            isdn_new,
            raw_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("report_date", ""),
        data.get("free_count", 0),
        data.get("fee_count", 0),
        data.get("quota_count", 0),
        data.get("total_isdn", 0),
        data.get("blacklist_mvno_change", 0),
        data.get("blacklist_postpaid_change", 0),
        data.get("neif10_total", 0),
        data.get("tapping_total", 0),
        data.get("isdn_new", 0),
        data.get("raw_text", "")
    ))

    conn.commit()
    conn.close()


def get_last_kpi_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM kpi_data
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)

    return None

def insert_same_period_data(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO same_period_data (
            created_at, time_range,
            ung_value, ung_diff, ung_percent,
            hoan_value, hoan_diff, hoan_percent,
            fee_value, fee_diff, fee_percent,
            free_value, free_diff, free_percent,
            quota_value, quota_diff, quota_percent,
            raw_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("time_range", ""),
        data.get("ung_value", 0), data.get("ung_diff", 0), data.get("ung_percent", 0),
        data.get("hoan_value", 0), data.get("hoan_diff", 0), data.get("hoan_percent", 0),
        data.get("fee_value", 0), data.get("fee_diff", 0), data.get("fee_percent", 0),
        data.get("free_value", 0), data.get("free_diff", 0), data.get("free_percent", 0),
        data.get("quota_value", 0), data.get("quota_diff", 0), data.get("quota_percent", 0),
        data.get("raw_text", "")
    ))

    conn.commit()
    conn.close()


def get_last_same_period_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM same_period_data
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)

    return None
    
# ======================
# PARSERS
# ======================

def parse_kpi_ung360(body):
    if (
        is_gd_loi_mail(body)
        or is_ut360_scoring_mail(body)
        or "UNG360-SERVICE" in body
        or "UNG360-NEIF10" in body
        or "CANH BAO:" in body
    ):
        return

    report_match = re.search(
        r'\[Ung360\s+([\d-]+\s+\d{2}:\d{2}:\d{2})\]',
        body
    )

    if not report_match:
        return

    report_time = report_match.group(1)
    
    dt_report = datetime.strptime(report_time, "%Y-%m-%d %H:%M:%S")
    period_key = dt_report.strftime("%Y%m%d%H")
    mark_received("kpi", period_key)

    def get_money_pct(label):
        match = re.search(
            rf'{label}:\s*([\d,\.]+)(?:\s*\(([-+]?\d+)%\))?',
            body
        )
        if match:
            value = to_int(match.group(1))
            pct = int(match.group(2)) if match.group(2) else 0
            return value, pct
        return 0, 0

    ung_value, ung_pct = get_money_pct("Ung")
    hoan_value, hoan_pct = get_money_pct("Hoan")
    fee_value, fee_pct = get_money_pct(r'-\s*FEE')
    free_value, free_pct = get_money_pct(r'-\s*FREE')
    quota_value, quota_pct = get_money_pct(r'-\s*QUOTA')

    invite_match = re.search(r'INVITE:\s*([\d,\.]+)', body)
    gui_ok_match = re.search(r'Gui OK:\s*([\d,\.]+)', body)
    loi_match = re.search(r'Loi:\s*([\d,\.]+)', body)
    neif10_match = re.search(r'Neif10:\s*([\d,\.]+)', body)
    tapping_match = re.search(r'Tapping:\s*([\d,\.]+)', body)

    invite = to_int(invite_match.group(1)) if invite_match else 0
    gui_ok = to_int(gui_ok_match.group(1)) if gui_ok_match else 0
    loi_gui = to_int(loi_match.group(1)) if loi_match else 0
    neif10 = to_int(neif10_match.group(1)) if neif10_match else 0
    tapping = to_int(tapping_match.group(1)) if tapping_match else 0

    previous = get_last_kpi_data()

    data = {
        "report_time": report_time,
        "ung_value": ung_value,
        "ung_percent": ung_pct,
        "hoan_value": hoan_value,
        "hoan_percent": hoan_pct,
        "fee_value": fee_value,
        "fee_percent": fee_pct,
        "free_value": free_value,
        "free_percent": free_pct,
        "quota_value": quota_value,
        "quota_percent": quota_pct,
        "invite": invite,
        "gui_ok": gui_ok,
        "loi_gui": loi_gui,
        "neif10": neif10,
        "tapping": tapping,
        "raw_text": body
    }

    insert_kpi_data(data)

    alerts = []
    stale_lines = []

    if ung_pct <= UNG_ALERT:
        old = previous.get("ung_value", 0) if previous else 0
        old_pct = previous.get("ung_percent", 0) if previous else 0
        alerts.append(
            f"Ung:\n"
            f"- Hiện tại: {ung_value:,} ({ung_pct}%)\n"
            f"- Kỳ trước: {old:,} ({old_pct}%) → ứng tiền giảm mạnh so với cùng thời điểm hôm trước"
        )

    if hoan_pct <= HOAN_ALERT:
        old = previous.get("hoan_value", 0) if previous else 0
        old_pct = previous.get("hoan_percent", 0) if previous else 0
        alerts.append(
            f"Hoan:\n"
            f"- Hiện tại: {hoan_value:,} ({hoan_pct}%)\n"
            f"- Kỳ trước: {old:,} ({old_pct}%) → hoàn ứng thấp hơn cùng kỳ"
        )

    if fee_pct <= -10:
        old = previous.get("fee_value", 0) if previous else 0
        old_pct = previous.get("fee_percent", 0) if previous else 0
        alerts.append(
            f"Fee:\n"
            f"- Hiện tại: {fee_value:,} ({fee_pct}%)\n"
            f"- Kỳ trước: {old:,} ({old_pct}%) → giảm mạnh so với cùng thời điểm hôm trước"
        )

    if free_pct >= 15:
        old = previous.get("free_value", 0) if previous else 0
        old_pct = previous.get("free_percent", 0) if previous else 0
        alerts.append(
            f"Free:\n"
            f"- Hiện tại: {free_value:,} ({free_pct}%)\n"
            f"- Kỳ trước: {old:,} ({old_pct}%) → FREE tăng mạnh, cần theo dõi dịch chuyển service_type"
        )

    if loi_gui >= LOI_GUI_ALERT:
        old = previous.get("loi_gui", 0) if previous else 0
        alerts.append(
            f"Gui Loi:\n"
            f"- Hiện tại: {loi_gui:,}\n"
            f"- Kỳ trước: {old:,} → lỗi gửi tăng cao bất thường"
        )

        if previous:
            if ung_value == previous.get("ung_value", 0):
                stale_lines.append(
                    f"- Ung: {previous.get('ung_value', 0):,} -> {ung_value:,} → ứng tiền không đổi so với kỳ trước"
                )

            if hoan_value == previous.get("hoan_value", 0):
                stale_lines.append(
                    f"- Hoan: {previous.get('hoan_value', 0):,} -> {hoan_value:,} → hoàn ứng không đổi so với kỳ trước"
                )

            if fee_value == previous.get("fee_value", 0):
                stale_lines.append(
                    f"- Fee: {previous.get('fee_value', 0):,} -> {fee_value:,} → FEE không đổi so với kỳ trước"
                )

            if free_value == previous.get("free_value", 0):
                stale_lines.append(
                    f"- Free: {previous.get('free_value', 0):,} -> {free_value:,} → FREE không đổi so với kỳ trước"
                )

            if quota_value == previous.get("quota_value", 0):
                stale_lines.append(
                    f"- Quota: {previous.get('quota_value', 0):,} -> {quota_value:,} → QUOTA không đổi so với kỳ trước"
                )

            if invite == previous.get("invite", 0):
                stale_lines.append(
                    f"- Invite: {previous.get('invite', 0):,} -> {invite:,} → nghi vấn pipeline đứng"
                )

            if gui_ok == previous.get("gui_ok", 0):
                stale_lines.append(
                    f"- Gui OK: {previous.get('gui_ok', 0):,} -> {gui_ok:,} → nghi vấn SMS/API không cập nhật"
                )

            if loi_gui == previous.get("loi_gui", 0):
                stale_lines.append(
                    f"- Loi Gui: {previous.get('loi_gui', 0):,} -> {loi_gui:,} → lỗi gửi không đổi so với kỳ trước"
                )

            if neif10 == previous.get("neif10", 0):
                stale_lines.append(
                    f"- Neif10: {previous.get('neif10', 0):,} -> {neif10:,} → nghi vấn log processing bị treo"
                )

            if tapping == previous.get("tapping", 0):
                stale_lines.append(
                    f"- Tapping: {previous.get('tapping', 0):,} -> {tapping:,} → nghi vấn dữ liệu đầu vào đứng"
                )

    if alerts or stale_lines:
        dt = datetime.strptime(report_time, "%Y-%m-%d %H:%M:%S")
        display_time = dt.strftime("%d/%m %H:%M")

        msg = f"* UNG360 KPI ALERT - {display_time}\n\n"

        if alerts:
            msg += "\n\n".join(alerts)

        if stale_lines:
            msg += "\n\n * Chỉ số không thay đổi:\n"
            msg += "\n".join(stale_lines)

        send_alert(msg)
    else:
        print("KPI mail processed - no alert")
        
        
def parse_gd_loi(body):
    if not is_gd_loi_mail(body):
        return
    today_key = datetime.now().strftime("%Y%m%d")

    if "0h-0h" in body or "00:00 hôm trước" in body or "00:00 hom truoc" in body:
        mark_received("gd_loi_daily", today_key)

    if "0h-8h" in body or "00:00" in body and "08:00" in body:
        mark_received("gd_loi_0_8", today_key)
    
    tong_loi = 0
    ung_loi = 0
    hoan_loi = 0
    thiet_hai = 0

    tong_match = re.search(r'Tổng:\s*([\d,\.]+)\s*lỗi', body, re.IGNORECASE)
    if not tong_match:
        tong_match = re.search(r'Tổng số lỗi\s+([\d,\.]+)\s+giao dịch', body, re.IGNORECASE)

    ung_match = re.search(r'Ứng:\s*([\d,\.]+)\s*lỗi', body, re.IGNORECASE)
    if not ung_match:
        ung_match = re.search(r'Lỗi Ứng.*?\s+([\d,\.]+)\s+giao dịch', body, re.IGNORECASE)

    hoan_match = re.search(r'Hoàn ứng.*?:\s*([\d,\.]+)\s*lỗi', body, re.IGNORECASE)
    if not hoan_match:
        hoan_match = re.search(r'Lỗi Hoàn ứng.*?\s+([\d,\.]+)\s+giao dịch', body, re.IGNORECASE)

    ung2_match = re.search(r'UNG:\s*([\d,\.]+)\s*loi', body, re.IGNORECASE)
    hoan2_match = re.search(r'HOANUNG:\s*([\d,\.]+)\s*loi', body, re.IGNORECASE)

    thiet_hai_match = re.search(r'Thi[eệ]t h[aạ]i[:\s]+([\d,\.]+)\s*VND', body, re.IGNORECASE)
    if not thiet_hai_match:
        thiet_hai_match = re.search(r'Tổng thiệt hại\s+([\d,\.]+)\s+VND', body, re.IGNORECASE)

    if tong_match:
        tong_loi = to_int(tong_match.group(1))
    if ung_match:
        ung_loi = to_int(ung_match.group(1))
    if hoan_match:
        hoan_loi = to_int(hoan_match.group(1))
    if ung2_match:
        ung_loi = to_int(ung2_match.group(1))
    if hoan2_match:
        hoan_loi = to_int(hoan2_match.group(1))

    if tong_loi == 0:
        tong_loi = ung_loi + hoan_loi

    if thiet_hai_match:
        thiet_hai = to_int(thiet_hai_match.group(1))

    code_lines = re.findall(r'Code\s+([-\w/]+):\s*([\d,\.]+)\s*GD', body)
    code_lines += re.findall(r'Lỗi\s+(-?\d+)\s+([\d,\.]+)\s+giao dịch', body)

    code_map = {}
    for code, count in code_lines:
        code_map[code] = code_map.get(code, 0) + to_int(count)

    report_time = ""
    time_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', body)
    if not time_match:
        time_match = re.search(r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})', body)

    if time_match:
        report_time = time_match.group(1)

    other_codes = {
        code: count
        for code, count in code_map.items()
        if code not in {"7", "41", "-1"}
    }

    insert_gd_loi_data({
        "report_time": report_time,
        "total_errors": tong_loi,
        "ung_errors": ung_loi,
        "hoanung_errors": hoan_loi,
        "damage_vnd": thiet_hai,
        "code_7": code_map.get("7", 0),
        "code_41": code_map.get("41", 0),
        "code_minus_1": code_map.get("-1", 0),
        "other_codes": other_codes,
        "raw_text": body
    })

    reasons = []

    if tong_loi >= GD_LOI_ALERT:
        reasons.append(f"Tổng lỗi cao: {tong_loi:,}")

    if thiet_hai >= THIET_HAI_ALERT:
        reasons.append(f"Thiệt hại cao: {thiet_hai:,} VND")

    for code, count_int in code_map.items():
        if code in BASELINE_CODES:
            baseline = BASELINE_CODES[code]
            if count_int >= baseline * BASELINE_MULTIPLIER:
                reasons.append(
                    f"Code {code} tăng bất thường: {count_int:,} GD "
                    f"(baseline {baseline:,})"
                )
        else:
            if count_int >= OTHER_CODE_ALERT:
                reasons.append(f"Code khác {code} cao: {count_int:,} GD")

    title = "* UNG360 GD LỖI BẤT THƯỜNG" if reasons else "* UNG360 GD LỖI"
    status = "CRITICAL" if reasons else "THEO DÕI"
    
    display_time = ""

    display_match = re.search(r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})', body)
    if display_match:
        dt = datetime.strptime(display_match.group(1), "%d/%m/%Y %H:%M")
        display_time = " - " + dt.strftime("%d/%m %H:%M")
    elif report_time:
        if "-" in report_time:
            dt = datetime.strptime(report_time, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(report_time, "%d/%m/%Y %H:%M")
        display_time = " - " + dt.strftime("%d/%m %H:%M")

    msg = f"""{title}{display_time}

Tổng lỗi: {tong_loi:,}
Ứng lỗi: {ung_loi:,}
Hoàn ứng lỗi: {hoan_loi:,}
Thiệt hại: {thiet_hai:,} VND

Trạng thái: {status}
"""

    if code_map:
        msg += "\nMã lỗi:\n"
        for code, count in sorted(code_map.items(), key=lambda x: x[1], reverse=True)[:10]:
            msg += format_result_code_count(code, count) + "\n"

    if reasons:
        msg += "\nLý do bất thường:\n"
        for reason in reasons:
            msg += f"- {reason}\n"

    send_alert(msg)


def parse_ut360_scoring(body):
    if not is_ut360_scoring_mail(body):
        return

    alerts = []
    text = normalize_text(body)

    def get_line_count(label):
        match = re.search(rf'^\s*{label}\s+([\d,]+)', text, re.MULTILINE)
        return to_int(match.group(1)) if match else 0

    def get_metric_count(pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        return to_int(match.group(1)) if match else 0

    date_match = re.search(r'ngay\s+(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
    report_date = date_match.group(1) if date_match else ""

    free_count = get_line_count("free")
    fee_count = get_line_count("fee")
    quota_count = get_line_count("quota")
    total_isdn = get_metric_count(r'tong isdn\s+([\d,]+)')
    neif10_total = get_metric_count(r'ban tin neif10.*?([\d,]+)')
    tapping_total = get_metric_count(r'ban tin tapping.*?([\d,]+)')
    isdn_new = get_metric_count(r'isdn moi tao\s+([\d,]+)')
    blacklist_mvno_change = 0
    blacklist_postpaid_change = 0

    blacklist_matches = re.findall(
        r'(blacklist:\w+)\s+([\d,]+)\s+([\d,]+)\s+([+-]?[\d,]+)',
        body
    )

    for key, yesterday, today, change in blacklist_matches:
        change_value = int(change.replace(",", ""))
        key_lower = key.lower()

        if key_lower == "blacklist:mvno":
            blacklist_mvno_change = change_value
        elif key_lower == "blacklist:postpaid":
            blacklist_postpaid_change = change_value

        if change_value == 0:
            alerts.append(f"* {key} không thay đổi")

        if abs(change_value) > BLACKLIST_CHANGE_ALERT:
            alerts.append(f"* {key} biến động mạnh: {change}")

    insert_ut360_scoring_data({
        "report_date": report_date,
        "free_count": free_count,
        "fee_count": fee_count,
        "quota_count": quota_count,
        "total_isdn": total_isdn,
        "blacklist_mvno_change": blacklist_mvno_change,
        "blacklist_postpaid_change": blacklist_postpaid_change,
        "neif10_total": neif10_total,
        "tapping_total": tapping_total,
        "isdn_new": isdn_new,
        "raw_text": body
    })

    if alerts:
        display_time = ""

        if report_date:
            dt = datetime.strptime(report_date, "%d/%m/%Y")
            display_time = " - " + dt.strftime("%d/%m")

        msg = f"* UT360 BLACKLIST ALERT{display_time}\n\n" + "\n".join(alerts)
        send_alert(msg)

def parse_same_period_report(body):
    if not is_same_period_mail(body):
        return

    time_match = re.search(
        r'tu\s+(\d{1,2}h)\s*-\s*(\d{1,2}h)',
        body,
        re.IGNORECASE
    )

    time_range = "N/A"
    if time_match:
        time_range = f"{time_match.group(1)} -> {time_match.group(2)}"
    
    date_match_for_period = re.search(r'Ung360\s+(\d{4}-\d{2}-\d{2})', body)

    if date_match_for_period and time_match:
        end_hour = int(time_match.group(2).replace("h", ""))
        period_date = datetime.strptime(date_match_for_period.group(1), "%Y-%m-%d")
        period_key = period_date.strftime("%Y%m%d") + f"{end_hour:02d}"
        mark_received("same_period", period_key)
    
    def get_same_period_metric(label):
        match = re.search(
            rf'{label}:\s*([\d,\.]+)\s*\(([+-]?[\d,\.]+)\s*~\s*([+-]?\d+)%',
            body,
            re.IGNORECASE
        )

        if match:
            value = to_int(match.group(1))
            diff = to_int(match.group(2))
            pct = int(match.group(3))
            return value, diff, pct

        return 0, 0, 0

    ung_value, ung_diff, ung_pct = get_same_period_metric("Ung")
    hoan_value, hoan_diff, hoan_pct = get_same_period_metric("Hoan")
    fee_value, fee_diff, fee_pct = get_same_period_metric("- FEE")
    free_value, free_diff, free_pct = get_same_period_metric("- FREE")
    quota_value, quota_diff, quota_pct = get_same_period_metric("- QUOTA")
    previous = get_last_same_period_data()

    data = {
        "time_range": time_range,
        "ung_value": ung_value,
        "ung_diff": ung_diff,
        "ung_percent": ung_pct,
        "hoan_value": hoan_value,
        "hoan_diff": hoan_diff,
        "hoan_percent": hoan_pct,
        "fee_value": fee_value,
        "fee_diff": fee_diff,
        "fee_percent": fee_pct,
        "free_value": free_value,
        "free_diff": free_diff,
        "free_percent": free_pct,
        "quota_value": quota_value,
        "quota_diff": quota_diff,
        "quota_percent": quota_pct,
        "raw_text": body
    }

    insert_same_period_data(data)

    alerts = []
    
    stale_lines = []

    if previous:
        if ung_value == previous.get("ung_value", 0):
            stale_lines.append(
                f"- Ung: {previous.get('ung_value', 0):,} -> {ung_value:,} → không đổi so với giờ trước"
            )

        if hoan_value == previous.get("hoan_value", 0):
            stale_lines.append(
                f"- Hoan: {previous.get('hoan_value', 0):,} -> {hoan_value:,} → không đổi so với giờ trước"
            )

        if fee_value == previous.get("fee_value", 0):
            stale_lines.append(
                f"- Fee: {previous.get('fee_value', 0):,} -> {fee_value:,} → không đổi so với giờ trước"
            )

        if free_value == previous.get("free_value", 0):
            stale_lines.append(
                f"- Free: {previous.get('free_value', 0):,} -> {free_value:,} → không đổi so với giờ trước"
            )

        if quota_value == previous.get("quota_value", 0):
            stale_lines.append(
                f"- Quota: {previous.get('quota_value', 0):,} -> {quota_value:,} → không đổi so với giờ trước"
            )

    if ung_pct <= -10:
        alerts.append(
            f"Ung:\n"
            f"- Hiện tại: {ung_value:,} ({ung_pct}%)\n"
            f"- Chênh lệch: {ung_diff:,} → ứng tiền giảm so với cùng kỳ"
        )

    if hoan_pct <= -5:
        alerts.append(
            f"Hoan:\n"
            f"- Hiện tại: {hoan_value:,} ({hoan_pct}%)\n"
            f"- Chênh lệch: {hoan_diff:,} → hoàn ứng giảm so với cùng kỳ"
        )

    if fee_pct <= -10:
        alerts.append(
            f"Fee:\n"
            f"- Hiện tại: {fee_value:,} ({fee_pct}%)\n"
            f"- Chênh lệch: {fee_diff:,} → doanh thu ứng phí giảm so với cùng kỳ"
        )

    if free_pct >= 15:
        alerts.append(
            f"Free:\n"
            f"- Hiện tại: {free_value:,} ({free_pct}%)\n"
            f"- Chênh lệch: {free_diff:,} → FREE tăng mạnh so với cùng kỳ"
        )

    if abs(quota_pct) >= 50:
        alerts.append(
            f"Quota:\n"
            f"- Hiện tại: {quota_value:,} ({quota_pct}%)\n"
            f"- Chênh lệch: {quota_diff:,} → QUOTA biến động mạnh so với cùng kỳ"
        )

    if alerts or stale_lines:
        date_match = re.search(r'Ung360\s+(\d{4}-\d{2}-\d{2})', body)

        display_time = time_range
        if date_match:
            dt = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            display_time = f"{dt.strftime('%d/%m')} {time_range}"

        msg = f"* UNG360 DOANH THU CÙNG KỲ ALERT - {display_time}\n\n"

        if alerts:
            msg += "\n\n".join(alerts)

        if stale_lines:
            msg += "\n\n* Chỉ số không đổi so với giờ trước:\n"
            msg += "\n".join(stale_lines)

        send_alert(msg)
    else:
        print("Same period mail processed - no alert")

def parse_mds_mail(body):
    if not is_mds_mail(body):
        return

    report_match = re.search(
        r'\[Ung360MDS\s+([\d-]+\s+\d{2}:\d{2}:\d{2})\]',
        body
    )
    if report_match:
        period_key = period_key_from_datetime_text(report_match.group(1))
        if period_key:
            mark_received("mds", period_key)

    print("MDS mail processed")

def parse_kafka_monitoring_mail(subject, body):
    if not is_kafka_monitoring_mail(subject, body):
        return

    text = normalize_text(subject + "\n" + body)
    alert_time = get_body_field(body, "Alert Time")
    display_time = datetime.now().strftime("%d/%m %H:%M")

    if alert_time:
        try:
            display_time = datetime.strptime(alert_time, "%Y-%m-%d %H:%M:%S").strftime("%d/%m %H:%M")
        except Exception:
            pass

    topic_rows = re.findall(
        r'^(tp-[^\s]+)\s+([\d.]+)\s+([\d,]+)\s+(.+?)\s+(NO_MESSAGES|LOW_TPS|OK|HIGH|WARN|ERROR)\s*$',
        body,
        re.MULTILINE | re.IGNORECASE
    )

    count_match = re.search(
        r'Topic\s+([^\s]+)\s+-\s+Tổng giờ hiện tại:\s*([\d,]+)\s*\|\s*TB 7 ngày cùng giờ:\s*([\d,]+)\s*\|\s*Chênh lệch:\s*([\d.]+%)',
        body,
        re.IGNORECASE
    )

    if not topic_rows and not count_match:
        print("Kafka monitoring mail processed - no alert rows")
        return

    msg = f"* KAFKA MONITORING ALERT - {display_time}\n\n"

    if topic_rows:
        msg += "Ứng360 Message Monitor Alert\n"
        for topic, tps, messages, threshold, status in topic_rows:
            status = status.upper()
            msg += f"- {topic}: {status} | TPS 1 phút: {tps} | Msg 5 phút: {messages} | Ngưỡng: {threshold.strip()}\n"

            if status == "NO_MESSAGES":
                msg += "  Ghi chú: Không có bản tin trong vòng 1 phút, cần kiểm tra luồng message.\n"
            elif status == "LOW_TPS":
                msg += "  Ghi chú: TPS 1 phút thấp hơn ngưỡng cấu hình.\n"

    if count_match:
        topic, current, average, diff = count_match.groups()
        msg += "Kafka Message Count bất thường\n"
        msg += f"- Topic: {topic}\n"
        msg += f"- Tổng giờ hiện tại: {current}\n"
        msg += f"- TB 7 ngày cùng giờ: {average}\n"
        msg += f"- Chênh lệch: {diff}\n"

    send_alert(msg)
    print("Kafka monitoring alert sent")
    
def parse_urgent_gd_alert(subject, body):
    if not is_urgent_gd_alert(subject, body):
        return

    total_match = re.search(
        r'CANH BAO:\s*([\d,]+)\s+loi.*?trong\s+([\d,]+)\s+phut',
        body,
        re.IGNORECASE
    )

    if total_match:
        total_error = total_match.group(1)
        window = total_match.group(2)
    else:
        total_error = "N/A"
        window = "N/A"

    source_lines = re.findall(
        r'-\s*([A-Z0-9_]+):\s*([\d,]+)\s*GD',
        body
    )

    code_lines = re.findall(
        r'-\s*Code\s+(-?\d+):\s*([\d,]+)\s*GD',
        body
    )

    time_match = re.search(r'(\d{2}/\d{2}\s+\d{2}:\d{2})', body)
    display_time = ""

    if time_match:
        display_time = " - " + time_match.group(1)

    msg = f"""* UNG360 URGENT ALERT{display_time}

Tổng lỗi: {total_error} GD / {window} phút
"""

    if source_lines:
        msg += "\nNguồn lỗi:\n"
        for source, count in source_lines[:5]:
            msg += f"- {source}: {count} GD\n"

    if code_lines:
        msg += "\nMã lỗi:\n"
        for code, count in code_lines[:5]:
            msg += format_result_code_count(code, to_int(count)) + "\n"

    send_alert(msg)

def get_body_field(body, label):
    label_norm = normalize_text(label)

    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue

        line_norm = normalize_text(line)
        if line_norm.startswith(label_norm):
            value = line[len(label):].strip(" :\t-")
            value_norm = normalize_text(value)
            if label_norm == "tai nguyen" and (
                value_norm.startswith("vuot nguong")
                or value_norm.startswith("da khoi phuc")
                or value_norm.startswith("khoi phuc")
                or value_norm.startswith("binh thuong")
            ):
                continue
            return value.strip()

    return ""


def parse_aibox_mail(subject, body):
    if not is_aibox_mail(subject, body):
        return

    time_text = get_body_field(body, "Thời gian")
    event_time = datetime.now()
    display_time = datetime.now().strftime("%d/%m %H:%M")

    if time_text:
        try:
            event_time = datetime.strptime(time_text, "%Y-%m-%d %H:%M:%S")
            display_time = event_time.strftime("%d/%m %H:%M")
        except Exception:
            pass

    if is_aibox_resource_alert(subject, body) or is_aibox_resource_recovery(subject, body):
        device = get_body_field(body, "Thiết bị") or "AIBOX"
        resource = get_body_field(body, "Tài nguyên") or "N/A"
        current_usage = get_body_field(body, "Mức sử dụng hiện tại") or "N/A"
        threshold = get_body_field(body, "Ngưỡng cảnh báo") or "N/A"
        title = "AIBOX RESOURCE ALERT" if is_aibox_resource_alert(subject, body) else "AIBOX RESOURCE RECOVERY"

        resource_rows = re.findall(
            r'^\s*(CPU|RAM|NPU Core \d+)\s+([\d.]+%)',
            body,
            re.MULTILINE
        )

        msg = f"""* {title} - {display_time}

Thiết bị: {device}
Tài nguyên: {resource}
Mức sử dụng: {current_usage}
Ngưỡng cảnh báo: {threshold}
"""

        if resource_rows:
            msg += "\nTrạng thái tài nguyên:\n"
            for name, usage in resource_rows:
                msg += f"- {name}: {usage}\n"

        send_alert(msg)
        print(f"{title} processed")
        return

    rows = re.findall(
        r'(Mất kết nối|Đang kết nối|Đã kết nối lại|Kết nối lại|Khôi phục)\s+(.+?)\s+(\d+\.\d+\.\d+\.\d+)',
        body
    )

    down_rows = []
    recovery_rows = []

    for status, name, ip in rows:
        status_norm = normalize_text(status)
        name = name.strip()
        key = f"{name}_{ip}"

        if "mat ket noi" in status_norm:
            aibox_pending[key] = {
                "name": name,
                "ip": ip,
                "down_time": event_time,
                "display_time": display_time
            }
            down_rows.append((name, ip))
        else:
            down_time = aibox_pending.get(key, {}).get("down_time")
            downtime_minutes = None
            if down_time:
                downtime_minutes = int((event_time - down_time).total_seconds() / 60)
            aibox_pending.pop(key, None)
            recovery_rows.append((name, ip, downtime_minutes))

    if is_aibox_down(subject, body) and down_rows:
        msg = f"* AIBOX MẤT KẾT NỐI - {display_time}\n\n"
        for name, ip in down_rows:
            msg += f"- {name} - {ip}\n"
        send_alert(msg)
        print(f"AIBOX down processed: {len(down_rows)} device")
        return

    if is_aibox_recovery(subject, body) and recovery_rows:
        msg = f"* AIBOX KHÔI PHỤC - {display_time}\n\n"
        for name, ip, downtime in recovery_rows:
            if downtime is None:
                msg += f"- {name} - {ip}\n"
            else:
                msg += f"- {name} - {ip} | Downtime: {downtime} phút\n"
        send_alert(msg)
        print(f"AIBOX recovery processed: {len(recovery_rows)} device")
        return

    print("AIBOX mail processed - no alert rows")


def parse_camera_mail(subject, body):
    if not is_camera_mail(subject, body):
        return

    time_match = re.search(r'Thời gian:\s*([\d-]+\s+[\d:]+)', body)
    device_match = re.search(r'Thiết bị:\s*(.+)', body)

    event_time = datetime.now()
    display_time = datetime.now().strftime("%d/%m %H:%M")

    if time_match:
        try:
            event_time = datetime.strptime(time_match.group(1), "%Y-%m-%d %H:%M:%S")
            display_time = event_time.strftime("%d/%m %H:%M")
        except Exception:
            pass

    device = device_match.group(1).strip() if device_match else "AIBOX"

    rows = re.findall(
        r'(Mất kết nối|Đã kết nối lại|Đang kết nối)\s+(.+?)\s+(\d+\.\d+\.\d+\.\d+)',
        body
    )

    affected = []
    if is_camera_down(subject, body):
        for row in rows:
            if len(row) == 3:
                status, cam_name, ip = row
            elif len(row) == 2:
                cam_name, ip = row
                status = "Mất kết nối"
            else:
                continue

            if status == "Mất kết nối":
                key = f"{device}_{ip}"
                camera_pending[key] = {
                    "device": device,
                    "cam_name": cam_name.strip(),
                    "ip": ip,
                    "down_time": event_time,
                    "display_time": display_time
                }
                affected.append((cam_name.strip(), ip))

        print(f"Camera down processed: {len(affected)} camera")

    elif is_camera_recovery(subject, body):
        recovered = []

        for row in rows:
            if len(row) == 3:
                status, cam_name, ip = row
            elif len(row) == 2:
                cam_name, ip = row
                status = "Đã kết nối lại"
            else:
                continue

            key = f"{device}_{ip}"

            if key in camera_pending:
                down_time = camera_pending[key]["down_time"]
                downtime_minutes = int((event_time - down_time).total_seconds() / 60)

                if key in camera_alerted:
                    recovered.append((cam_name.strip(), ip, downtime_minutes))

                camera_pending.pop(key, None)
                camera_alerted.pop(key, None)

        if recovered:
            msg = f"* CAMERA RECOVERY - {display_time}\n\n"
            msg += f"Thiết bị: {device}\n\n"
            msg += "Đã kết nối lại:\n"

            for cam_name, ip, downtime in recovered:
                msg += f"- {cam_name} - {ip} | Downtime: {downtime} phút\n"

            send_alert(msg)

        print(f"Camera recovery processed: {len(recovered)} camera")
        
def process_mail(subject, body):
    body = clean_mail_body(body)
    mail_content = f"Subject: {subject}\n\n{body}"
    mail_type = detect_mail_type(subject, body)

    if mail_type == "urgent_gd_alert":
        write_urgent_alert_log(mail_content)

    elif mail_type == "ut360_scoring":
        write_ut360_scoring_log(mail_content)

    elif mail_type == "gd_loi":
        write_gd_loi_log(mail_content)

    elif mail_type == "same_period":
        write_same_period_log(mail_content)

    elif mail_type == "ung_service_daily":
        today = datetime.now().strftime("%Y-%m-%d")
        write_named_log("logs/ung_service_daily", f"{today}.log", mail_content)

    elif mail_type == "kafka_monitoring":
        today = datetime.now().strftime("%Y-%m-%d")
        write_named_log("logs/kafka_monitoring", f"{today}.log", mail_content)

    elif mail_type == "mds":
        today = datetime.now().strftime("%Y-%m-%d")
        write_named_log("logs/mds", f"{today}.log", mail_content)
    elif mail_type == "aibox":
        today = datetime.now().strftime("%Y-%m-%d")
        write_named_log("logs/aibox", f"{today}.log", mail_content)
    elif mail_type == "camera":
        today = datetime.now().strftime("%Y-%m-%d")
        write_named_log("logs/camera", f"{today}.log", mail_content)
    elif mail_type == "kpi":
        write_kpi_log(mail_content)
    else:
        write_ignored_mail_log(mail_content)
        print(f"Ignored unrelated mail: {subject}")
        return False

    if mail_type == "urgent_gd_alert":
        parse_urgent_gd_alert(subject, body)

    elif mail_type == "ut360_scoring":
        parse_ut360_scoring(body)

    elif mail_type == "gd_loi":
        parse_gd_loi(body)

    elif mail_type == "same_period":
        parse_same_period_report(body)

    elif mail_type == "ung_service_daily":
        print("UNG service daily report processed")

    elif mail_type == "kafka_monitoring":
        parse_kafka_monitoring_mail(subject, body)

    elif mail_type == "mds":
        parse_mds_mail(body)
    elif mail_type == "aibox":
        parse_aibox_mail(subject, body)
    elif mail_type == "camera":
        parse_camera_mail(subject, body)
    elif mail_type == "kpi":
        parse_kpi_ung360(body)

    return True

def check_missing_mail():
    now = datetime.now()

    # Chỉ check từ phút thứ 10 trở đi
    if now.minute < 10:
        return

    period_key = now.strftime("%Y%m%d%H")
    display_hour = now.strftime("%H:00")
    display_check = now.strftime("%d/%m %H:%M")

    missing = []

    if not has_received("kpi", period_key):
        alert_key = f"missing_kpi_{period_key}"
        if alert_key not in missing_alert_sent:
            missing.append(f"- KPI realtime kỳ {display_hour}")
            missing_alert_sent.add(alert_key)

    if not has_received("same_period", period_key):
        alert_key = f"missing_same_{period_key}"
        if alert_key not in missing_alert_sent:
            missing.append(f"- Doanh thu cùng kỳ kỳ {display_hour}")
            missing_alert_sent.add(alert_key)

    if not has_received("mds", period_key):
        alert_key = f"missing_mds_{period_key}"
        if alert_key not in missing_alert_sent:
            missing.append(f"- MDS kỳ {display_hour}")
            missing_alert_sent.add(alert_key)

    if missing:
        msg = f"* UNG360 MISSING MAIL ALERT - {display_check}\n\n"
        msg += "Chưa nhận được:\n"
        msg += "\n".join(missing)
        send_alert(msg)

    # Check báo cáo GD lỗi lúc 08:10 trở đi
    if now.hour == 8 and now.minute >= 10:
        today_key = now.strftime("%Y%m%d")
        report_missing = []

        if not has_received("gd_loi_daily", today_key):
            alert_key = f"missing_gd_daily_{today_key}"
            if alert_key not in missing_alert_sent:
                report_missing.append("- GD lỗi 00:00 hôm trước -> 00:00 hôm nay, expected 08:00")
                missing_alert_sent.add(alert_key)

        if not has_received("gd_loi_0_8", today_key):
            alert_key = f"missing_gd_0_8_{today_key}"
            if alert_key not in missing_alert_sent:
                report_missing.append("- GD lỗi 00:00 hôm nay -> 08:00 hôm nay, expected 08:00")
                missing_alert_sent.add(alert_key)

        if report_missing:
            msg = f"* UNG360 MISSING REPORT ALERT - {display_check}\n\n"
            msg += "Chưa nhận được:\n"
            msg += "\n".join(report_missing)
            send_alert(msg)

def check_camera_pending():
    now = datetime.now()

    for key, item in list(camera_pending.items()):
        down_time = item["down_time"]
        diff_minutes = int((now - down_time).total_seconds() / 60)

        if diff_minutes >= 5 and key not in camera_alerted:
            msg = f"* CAMERA ALERT - {item['display_time']}\n\n"
            msg += f"Thiết bị: {item['device']}\n\n"
            msg += "Mất kết nối:\n"
            msg += f"- {item['cam_name']} - {item['ip']}\n"

            send_alert(msg)
            camera_alerted[key] = True
            
def main():
    print("Ung360 monitor is running...")

    init_db()
    start_telegram_bot()
    processed = load_processed_mails()
    last_heartbeat = time.time()

    try:
        send_alert("------> Ung360 monitor started")
    except Exception as e:
        print("Telegram startup test failed:", e)

    while True:
        try:
            if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
                try:
                    send_alert("* UNG360 Monitor Alive")
                except Exception as e:
                    write_error_log(f"Heartbeat error: {e}")
                last_heartbeat = time.time()

            print("Checking Gmail...")

            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL, PASSWORD)
            mail.select("inbox")

            status, messages = mail.search(None, 'ALL')
            all_ids = messages[0].split()
            mail_ids = all_ids[-MAIL_SEARCH_LIMIT:]

            print("So mail gan nhat can kiem tra:", len(mail_ids))

            changed = False

            for num in mail_ids:
                _, data = mail.fetch(num, "(RFC822)")
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                unique_id = get_mail_unique_id(msg, num)

                if unique_id in processed:
                    continue

                subject = decode_mime_header(msg.get("subject", ""))
                body = get_email_body(msg)

                if not body:
                    processed.add(unique_id)
                    changed = True
                    continue

                print("Subject:", subject)
                print(clean_mail_body(body))

                process_mail(subject, body)

                processed.add(unique_id)
                changed = True

            if changed:
                save_processed_mails(processed)
            else:
                print("Khong co mail moi can xu ly")

            mail.logout()

        except KeyboardInterrupt:
            print("Stopped by user")
            break

        except Exception as e:
            error_message = f"ERROR: {e}"
            print(error_message)
            write_error_log(error_message)

            try:
                send_alert("* UNG360 MONITOR ERROR\n\n" + error_message)
            except Exception:
                pass
        check_missing_mail()
        check_camera_pending()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
