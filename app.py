from dotenv import load_dotenv
import os
import sys
import openai
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import random
import tiktoken
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.rule import Rule
from rich.text import Text

# 加载配置
load_dotenv()
BASEAPI = os.getenv("BASE_API", "https://api.openai.com/v1")
APIKEY = os.getenv("API_KEY")
RESPONSE_TOKENS = int(os.getenv("RESPONSE_TOKENS", "2048"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "32000"))
TEMPERATURE_MIN = float(os.getenv("TEMPERATURE_MIN", "0.4"))
TEMPERATURE_MAX = float(os.getenv("TEMPERATURE_MAX", "1.2"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))
INITIAL_ROUNDS = int(os.getenv("INITIAL_ROUNDS", "3"))
TOPIC = os.getenv("TOPIC", "")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "discussions")
LOG_DIR = os.getenv("LOG_DIR", "log")
TIKTOKEN_MODEL = os.getenv("TIKTOKEN_MODEL", "gpt-4o")

SYSTEM_PROMPT_TEMPLATE = os.getenv("SYSTEM_PROMPT", (
    "你是 {model_name}，正在参与一场多AI圆桌讨论。\n"
    "讨论主题：「{topic}」\n"
    "参与者：{participants}\n\n"
    "规则：\n"
    "1. 你必须以自己的身份发言，有独立的立场和思考角度\n"
    "2. 认真阅读其他参与者的观点，可以赞同、反驳或补充\n"
    "3. 用清晰的逻辑和论据支撑你的观点\n"
    "4. 避免空泛的套话，给出有深度的分析\n"
    "5. 每轮发言控制在300字以内，精炼表达"
))

FIRST_ROUND_PROMPT = os.getenv("FIRST_ROUND_PROMPT", (
    "# Agent\n"
    "【第 {current_round}/{total_rounds} 轮 | 剩余 {remaining} 轮】\n\n"
    "请作为 {model_name} 率先发表你对「{topic}」的观点。\n"
    "要求：亮明立场，给出核心论点和支撑论据。"
))

DISCUSSION_PROMPT = os.getenv("DISCUSSION_PROMPT", (
    "# Agent\n"
    "【第 {current_round}/{total_rounds} 轮 | 剩余 {remaining} 轮】\n\n"
    "以下是上一轮其他参与者的发言：\n{others_text}\n"
    "请参考以上观点，继续深入讨论。你可以：\n"
    "- 反驳你不认同的观点并给出理由\n"
    "- 补充其他人遗漏的角度\n"
    "- 在他人观点基础上进一步推演\n"
    "- 修正或完善自己之前的立场"
))

HUMAN_GUIDE_PROMPT = os.getenv("HUMAN_GUIDE_PROMPT", (
    "# Human\n"
    "用户介入指导：\n{human_input}\n\n"
    "请根据用户的指导调整你的讨论方向和重点。"
))

SUMMARY_PROMPT = os.getenv("SUMMARY_PROMPT", (
    "# Agent\n"
    "【最终总结轮】\n\n"
    "讨论即将结束，请总结：\n"
    "1. 你的最终立场\n"
    "2. 讨论中最有价值的观点（包括他人的）\n"
    "3. 仍存在的分歧或待探讨的问题"
))

if not APIKEY:
    print("API_KEY 未设置，请检查 .env 文件")
    sys.exit(1)

# ===== 日志配置 =====
os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 控制台 handler: WARNING 及以上
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
logger.addHandler(console_handler)

# 文件 handler 延迟创建（需要 TOPIC 确定后命名）
file_handler = None

def init_file_logger(topic):
    global file_handler
    safe_topic = "".join(c if c.isalnum() or c in "_- " else "_" for c in topic)[:50]
    log_path = os.path.join(LOG_DIR, f"{safe_topic}_{timestamp}.log")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    logger.info("日志文件: %s", log_path)
    return log_path

# Rich console
console = Console()

# 模型配色
MODEL_COLORS = [
    "cyan", "green", "yellow", "magenta", "blue",
    "red", "bright_cyan", "bright_green", "bright_yellow", "bright_magenta"
]
model_color_map = {}

def get_model_color(mid):
    if mid not in model_color_map:
        idx = len(model_color_map) % len(MODEL_COLORS)
        model_color_map[mid] = MODEL_COLORS[idx]
    return model_color_map[mid]

logger.info("BASE_API: %s", BASEAPI)
logger.info("API_KEY: %s***", APIKEY[:8])
logger.info("MAX_TOKENS: %s", MAX_TOKENS)
logger.info("RESPONSE_TOKENS: %s", RESPONSE_TOKENS)

# tiktoken
try:
    encoder = tiktoken.encoding_for_model(TIKTOKEN_MODEL)
except Exception:
    encoder = tiktoken.get_encoding("cl100k_base")

def count_tokens(messages):
    total = 0
    for msg in messages:
        total += 4
        total += len(encoder.encode(msg.get("content", "")))
    total += 2
    return total

def trim_history(messages, max_ctx):
    while count_tokens(messages) + RESPONSE_TOKENS > max_ctx and len(messages) > 2:
        for i, msg in enumerate(messages):
            if msg["role"] != "system":
                removed = messages.pop(i)
                logger.info("裁剪消息 [%s]: %s...", removed["role"], removed["content"][:40])
                break
        else:
            break
    return messages

# 配置openai
client = openai.Client(base_url=BASEAPI, api_key=APIKEY)

# 获取模型列表
model_env = os.getenv("MODELS")
if model_env:
    MODELLIST = [{"id": m.strip()} for m in model_env.split(",") if m.strip()]
else:
    try:
        resp = client.models.list()
        MODELLIST = [{"id": m.id} for m in resp.data]
    except Exception as e:
        logger.warning("获取模型列表失败: %s", e)
        sys.exit(1)

if not MODELLIST:
    logger.warning("模型列表为空")
    sys.exit(1)

# 选择模型
console.print()
table = Table(title="可用模型", show_header=True, header_style="bold cyan")
table.add_column("序号", style="dim", width=6)
table.add_column("模型名称", style="bold")
for i, m in enumerate(MODELLIST):
    table.add_row(str(i), m["id"])
console.print(table)

CHOSENMODEL = []
while True:
    try:
        idx = IntPrompt.ask("\n请输入模型序号")
        if 0 <= idx < len(MODELLIST):
            CHOSENMODEL.append(MODELLIST[idx])
            chosen_names = [m["id"] for m in CHOSENMODEL]
            console.print(f"  已选择: [bold green]{', '.join(chosen_names)}[/]")
            if not Confirm.ask("继续选择?", default=False):
                break
        else:
            console.print("[red]序号超出范围[/]")
    except (ValueError, IndexError):
        console.print("[red]输入错误，请重新输入[/]")

if not CHOSENMODEL:
    logger.warning("未选择任何模型")
    sys.exit(1)

if not TOPIC:
    TOPIC = Prompt.ask("\n请输入讨论主题")
ROUND = INITIAL_ROUNDS or IntPrompt.ask("请输入对话轮数")

# 初始化文件日志
log_path = init_file_logger(TOPIC)

participants_str = "、".join(m["id"] for m in CHOSENMODEL)
total_prompt_tokens = 0
total_completion_tokens = 0

# ===== Markdown 记录 =====
os.makedirs(OUTPUT_DIR, exist_ok=True)
safe_topic = "".join(c if c.isalnum() or c in "_- " else "_" for c in TOPIC)[:50]
md_filename = os.path.join(OUTPUT_DIR, f"{timestamp}_{safe_topic}.md")

md_lines = []

def md_append(*lines):
    for line in lines:
        md_lines.append(line)

def save_markdown():
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    logger.info("对话记录已保存: %s", md_filename)

md_append(
    f"# 🗣️ 多模型讨论记录",
    f"",
    f"> **主题**: {TOPIC}  ",
    f"> **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
    f"> **参与模型**: {participants_str}  ",
    f"> **Token 上限**: {MAX_TOKENS}",
    f"",
    f"---",
    f""
)

def get_response(messages, model_id):
    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=random.uniform(TEMPERATURE_MIN, TEMPERATURE_MAX),
        max_tokens=RESPONSE_TOKENS
    )
    content = response.choices[0].message.content
    usage = response.usage
    return content, usage.prompt_tokens, usage.completion_tokens

def build_system_prompt(model_id):
    return SYSTEM_PROMPT_TEMPLATE.format(
        model_name=model_id,
        topic=TOPIC,
        participants=participants_str
    )

def build_others_text(last_responses, exclude_mid):
    parts = []
    for other in CHOSENMODEL:
        omid = other["id"]
        if omid != exclude_mid and omid in last_responses:
            parts.append(f"---\n【{omid}】:\n{last_responses[omid]}")
    return "\n\n".join(parts)

def render_response(mid, content, round_label):
    """用 Rich 渲染模型回复"""
    color = get_model_color(mid)
    panel = Panel(
        Markdown(content),
        title=f"[bold {color}]🤖 {mid}[/]",
        subtitle=f"[dim]{round_label}[/]",
        border_style=color,
        padding=(1, 2)
    )
    console.print(panel)

def render_human_input(text):
    panel = Panel(
        Text(text, style="bold white"),
        title="[bold bright_white]🧑 Human 指导[/]",
        border_style="bright_white",
        padding=(1, 2)
    )
    console.print(panel)

def render_stats():
    total = total_prompt_tokens + total_completion_tokens
    console.print(
        f"  [dim]📊 prompt: {total_prompt_tokens:,} | "
        f"completion: {total_completion_tokens:,} | "
        f"total: {total:,}[/]"
    )

def run_round(history, round_idx, total_rounds, last_responses, human_input=None):
    global total_prompt_tokens, total_completion_tokens
    responses = {}
    remaining = total_rounds - round_idx

    for model in CHOSENMODEL:
        mid = model["id"]

        if human_input:
            history[mid].append({
                "role": "user",
                "content": HUMAN_GUIDE_PROMPT.format(human_input=human_input)
            })

        if round_idx == 1 and not last_responses:
            history[mid].append({
                "role": "user",
                "content": FIRST_ROUND_PROMPT.format(
                    current_round=round_idx,
                    total_rounds=total_rounds,
                    remaining=remaining,
                    model_name=mid,
                    topic=TOPIC
                )
            })
        else:
            others_text = build_others_text(last_responses, mid)
            history[mid].append({
                "role": "user",
                "content": DISCUSSION_PROMPT.format(
                    current_round=round_idx,
                    total_rounds=total_rounds,
                    remaining=remaining,
                    others_text=others_text
                )
            })

        history[mid] = trim_history(history[mid], MAX_TOKENS)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_model = {
            executor.submit(get_response, history[m["id"]], m["id"]): m["id"]
            for m in CHOSENMODEL
        }
        for future in as_completed(future_to_model):
            mid = future_to_model[future]
            try:
                content, pt, ct = future.result()
                responses[mid] = content
                total_prompt_tokens += pt
                total_completion_tokens += ct
                logger.info("[%s] prompt=%d, completion=%d", mid, pt, ct)
            except Exception as e:
                logger.warning("[%s] 请求失败: %s", mid, e)
                responses[mid] = f"[请求失败: {e}]"

    for model in CHOSENMODEL:
        mid = model["id"]
        if mid in responses:
            history[mid].append({"role": "assistant", "content": responses[mid]})

    # 渲染
    round_label = f"第 {round_idx}/{total_rounds} 轮"
    if human_input:
        round_label += " (含人类指导)"

    console.print()
    console.print(Rule(f"[bold]📌 {round_label}[/]", style="bright_blue"))
    console.print()

    if human_input:
        render_human_input(human_input)

    md_append(f"## 📌 {round_label}", f"")
    if human_input:
        md_append(f"### 🧑 Human 指导", f"", f"> {human_input}", f"")

    for model in CHOSENMODEL:
        mid = model["id"]
        content = responses.get(mid, "[无回复]")
        render_response(mid, content, round_label)
        md_append(f"### 🤖 {mid}", f"", f"{content}", f"")

    render_stats()
    md_append(
        f"> 📊 累计 tokens — prompt: {total_prompt_tokens:,}, completion: {total_completion_tokens:,}",
        f"", f"---", f""
    )
    save_markdown()

    return responses

# 初始化 history
history = {}
for model in CHOSENMODEL:
    mid = model["id"]
    history[mid] = [{"role": "system", "content": build_system_prompt(mid)}]

# 启动提示
console.print()
console.print(Rule("[bold bright_blue]🗣️ 多模型讨论开始[/]", style="bright_blue"))
console.print(f"  主题: [bold]{TOPIC}[/]")
console.print(f"  模型: [bold green]{participants_str}[/]")
console.print(f"  轮数: [bold]{ROUND}[/]")
console.print()

# 主循环
cumulative_round = 0
total_rounds = ROUND
last_responses = {}

while True:
    batch_rounds = total_rounds - cumulative_round
    for r in range(batch_rounds):
        cumulative_round += 1
        last_responses = run_round(
            history, cumulative_round, total_rounds, last_responses
        )

    console.print()
    console.print(Rule("[bold yellow]轮次结束[/]", style="yellow"))
    render_stats()
    console.print()

    if not Confirm.ask("是否开启新的轮次?", default=False):
        # 最终总结
        console.print()
        console.print(Rule("[bold bright_magenta]📝 最终总结[/]", style="bright_magenta"))
        console.print()

        md_append(f"## 📝 最终总结", f"")

        for model in CHOSENMODEL:
            mid = model["id"]
            history[mid].append({"role": "user", "content": SUMMARY_PROMPT})
            history[mid] = trim_history(history[mid], MAX_TOKENS)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_model = {
                executor.submit(get_response, history[m["id"]], m["id"]): m["id"]
                for m in CHOSENMODEL
            }
            for future in as_completed(future_to_model):
                mid = future_to_model[future]
                try:
                    content, pt, ct = future.result()
                    total_prompt_tokens += pt
                    total_completion_tokens += ct
                    render_response(mid, content, "最终总结")
                    md_append(f"### 🤖 {mid}", f"", f"{content}", f"")
                except Exception as e:
                    logger.warning("[%s] 总结失败: %s", mid, e)
                    md_append(f"### 🤖 {mid}", f"", f"[总结失败: {e}]", f"")

        # 统计表格
        stats_table = Table(title="📊 讨论统计", show_header=True, header_style="bold cyan")
        stats_table.add_column("指标", style="bold")
        stats_table.add_column("数值", justify="right")
        stats_table.add_row("总轮数", str(cumulative_round))
        stats_table.add_row("参与模型", str(len(CHOSENMODEL)))
        stats_table.add_row("Prompt Tokens", f"{total_prompt_tokens:,}")
        stats_table.add_row("Completion Tokens", f"{total_completion_tokens:,}")
        stats_table.add_row("总 Tokens", f"{total_prompt_tokens + total_completion_tokens:,}")
        console.print()
        console.print(stats_table)

        md_append(
            f"---", f"",
            f"## 📊 统计", f"",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总轮数 | {cumulative_round} |",
            f"| 参与模型 | {len(CHOSENMODEL)} |",
            f"| Prompt Tokens | {total_prompt_tokens:,} |",
            f"| Completion Tokens | {total_completion_tokens:,} |",
            f"| 总 Tokens | {total_prompt_tokens + total_completion_tokens:,} |",
            f""
        )
        save_markdown()

        console.print()
        console.print(f"  📄 对话记录: [link={md_filename}]{md_filename}[/]")
        console.print(f"  📋 运行日志: [link={log_path}]{log_path}[/]")
        console.print()
        console.print(Rule("[bold bright_blue]讨论结束[/]", style="bright_blue"))
        break

    extra = IntPrompt.ask("追加几轮")
    total_rounds = cumulative_round + extra

    human_input = Prompt.ask("有需要指导的方向吗? (直接回车跳过)", default="").strip()
    if human_input:
        cumulative_round += 1
        total_rounds = cumulative_round + extra - 1
        last_responses = run_round(
            history, cumulative_round, total_rounds, last_responses,
            human_input=human_input
        )