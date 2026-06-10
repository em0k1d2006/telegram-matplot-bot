import io
import os
from matplotlib.figure import Figure
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Токен вашего бота
BOT_TOKEN = "8524521478:AAE1qSCTnueW7vuV7hFl-fe50NLDC5uXZ4Q"

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def parse_numbers(text):
    """Безопасно извлекает числа из строки, игнорируя текст и опечатки."""
    text = text.replace(',', ' ').replace(';', ' ')
    parts = text.split()
    numbers = []
    for x in parts:
        try:
            numbers.append(float(x))
        except ValueError:
            continue
    return numbers

def parse_data_with_axes(text):
    """
    Разбирает строку вида: числа / название / ось_X / ось_Y / ед_X / ед_Y
    Возвращает (numbers, label, x_label, y_label, x_unit, y_unit)
    """
    parts = [p.strip() for p in text.split('/')]
    numbers = parse_numbers(parts[0])
    
    label = parts[1] if len(parts) > 1 and parts[1] else None
    x_label = parts[2] if len(parts) > 2 and parts[2] else None
    y_label = parts[3] if len(parts) > 3 and parts[3] else None
    x_unit = parts[4] if len(parts) > 4 and parts[4] else None
    y_unit = parts[5] if len(parts) > 5 and parts[5] else None
    
    return numbers, label, x_label, y_label, x_unit, y_unit

def parse_two_datasets_with_axes(text):
    """
    Разбирает строку для сравнения: числа1 / числа2 / лег1 / лег2 / ось_X / ось_Y / ед_X / ед_Y
    """
    parts = [p.strip() for p in text.split('/')]
    if len(parts) < 2:
        return None, None, None, None, None, None, None, None
        
    data1 = parse_numbers(parts[0])
    data2 = parse_numbers(parts[1])
    
    label1 = parts[2] if len(parts) >= 3 and parts[2] else "Набор 1"
    label2 = parts[3] if len(parts) >= 4 and parts[3] else "Набор 2"
    x_label = parts[4] if len(parts) >= 5 and parts[4] else None
    y_label = parts[5] if len(parts) >= 6 and parts[5] else None
    x_unit = parts[6] if len(parts) >= 7 and parts[6] else None
    y_unit = parts[7] if len(parts) >= 8 and parts[7] else None
    
    return data1, data2, label1, label2, x_label, y_label, x_unit, y_unit

def format_axis_label(name, unit):
    """Форматирует подпись оси в техническом стиле: 'Название, ед.изм.'"""
    if unit:
        return f"{name}, {unit}"
    return name

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 *Бот-Графопостроитель*\n\n"
        "Привет! Я помогу быстро построить технические, учебные и аналитические графики прямо в чате. "
        "Вы можете гибко настраивать названия осей и единицы измерения.\n\n"
        "⚙️ *Как устроен ввод данных:*\n"
        "Чтобы подписать график и оси, разделяйте блоки обычной косой чертой (`/`) по шаблону:\n"
        "`числа / название / ось X / ось Y / ед.изм. X / ед.изм. Y`\n\n"
        "📌 *Важно:* Заполнять все текстовые поля через `/` не обязательно. Если вам нужен просто быстрый график, "
        "напишите только числа через пробел!\n\n"
        "📈 *Доступные типы графиков:* \n"
        "• /line — *Линейный график*. Отлично подходит для непрерывных процессов (нагрев, разряд, изменение во времени).\n"
        "• /bar — *Столбчатая диаграмма*. Идеально для сравнения отдельных категорий, объемов или дискретных величин.\n"
        "• /scatter — *Точечный график*. Наглядно показывает разброс отдельных экспериментальных точек.\n"
        "• /hist — *Гистограмма*. Показывает распределение частоты попадания величин в интервалы. Шаблон: `числа / заголовок / ось X / ось Y`.\n"
        "• /pie — *Круговая диаграмма*. Показывает доли в процентах от общего целого. Принимает только: `числа / заголовок`.\n"
        "• /compare — *Сравнение двух наборов данных*. Наложит две линии на одно поле. Шаблон:\n"
        "`числа1 / числа2 / легенда1 / легенда2 / ось X / ось Y / ед.изм. X / ед.изм. Y`\n\n"
        "💡 *Примеры для копирования и проверки:*\n\n"
        "1️⃣ *Максимальная подпись (Линейный график):*\n"
        "/line 10 25 55 90 / Разряд батареи / Время / Емкость / мин / %\n\n"
        "2️⃣ *Пропуск полей (Столбчатый график):*\n"
        "Если название оси X менять не нужно, но хотите указать единицу измерения для оси Y, просто оставьте поле пустым между слэшами `/ /`:\n"
        "/bar 220 380 110 / Напряжение сети / Фидер / Напряжение / / В\n\n"
        "3️⃣ *Сравнение расчётных и опытных данных:*\n"
        "/compare 1 2 3 / 2 3 4 / Расчёт / Опыт / Длина / Ток / мм / А",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def line(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: `/line 5 8 12 / График / Время / Ток / с / А`", parse_mode='Markdown')
        return
    text = ' '.join(context.args)
    numbers, label, x_label, y_label, x_unit, y_unit = parse_data_with_axes(text)
    if len(numbers) < 2:
        await update.message.reply_text("Нужно минимум 2 числа.")
        return

    fig = Figure()
    ax = fig.add_subplot(111)
    ax.plot(numbers, marker='o', linestyle='-', label=label if label else None)
    if label:
        ax.legend()
        
    ax.set_title("Линейный график" if not label else f"Линейный график: {label}")
    ax.set_xlabel(format_axis_label(x_label if x_label else "Номер точки", x_unit))
    ax.set_ylabel(format_axis_label(y_label if y_label else "Значение", y_unit))
    ax.grid(True)

    img_data = io.BytesIO()
    fig.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
    
    await update.message.reply_photo(photo=img_data, caption=f"Линейный график ({len(numbers)} точек)")

async def bar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: `/bar 10 20 30 / Столбцы / Категория / Вес / / кг`", parse_mode='Markdown')
        return
    text = ' '.join(context.args)
    numbers, label, x_label, y_label, x_unit, y_unit = parse_data_with_axes(text)
    if len(numbers) < 1:
        await update.message.reply_text("Нужно хотя бы одно число.")
        return

    fig = Figure()
    ax = fig.add_subplot(111)
    ax.bar(range(len(numbers)), numbers, color='skyblue', label=label if label else None)
    if label:
        ax.legend()
        
    ax.set_title("Столбчатая диаграмма" if not label else f"Столбчатая диаграмма: {label}")
    ax.set_xlabel(format_axis_label(x_label if x_label else "Категория", x_unit))
    ax.set_ylabel(format_axis_label(y_label if y_label else "Значение", y_unit))
    ax.grid(axis='y')

    img_data = io.BytesIO()
    fig.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
    
    await update.message.reply_photo(photo=img_data, caption=f"Столбчатая диаграмма ({len(numbers)} столбцов)")

async def scatter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: `/scatter 1 2 3 / Точки / X / Y / м / В`", parse_mode='Markdown')
        return
    text = ' '.join(context.args)
    numbers, label, x_label, y_label, x_unit, y_unit = parse_data_with_axes(text)
    if len(numbers) < 2:
        await update.message.reply_text("Нужно минимум 2 числа.")
        return

    fig = Figure()
    ax = fig.add_subplot(111)
    ax.scatter(range(len(numbers)), numbers, color='red', label=label if label else None)
    if label:
        ax.legend()
        
    ax.set_title("Точечный график" if not label else f"Точечный график: {label}")
    ax.set_xlabel(format_axis_label(x_label if x_label else "Номер точки", x_unit))
    ax.set_ylabel(format_axis_label(y_label if y_label else "Значение", y_unit))
    ax.grid(True)

    img_data = io.BytesIO()
    fig.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
    
    await update.message.reply_photo(photo=img_data, caption=f"Точечный график ({len(numbers)} точек)")

async def hist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: `/hist 1 2 2 3 / Сортировка / Отрезки / Кол-во / мм / шт`", parse_mode='Markdown')
        return
    text = ' '.join(context.args)
    numbers, title, x_label, y_label, x_unit, y_unit = parse_data_with_axes(text)
    if len(numbers) < 2:
        await update.message.reply_text("Нужно минимум 2 числа для гистограммы.")
        return

    fig = Figure()
    ax = fig.add_subplot(111)
    ax.hist(numbers, bins='auto', edgecolor='black', alpha=0.7)
    
    ax.set_title(title if title else "Гистограмма распределения")
    ax.set_xlabel(format_axis_label(x_label if x_label else "Значение", x_unit))
    ax.set_ylabel(format_axis_label(y_label if y_label else "Частота", y_unit))
    ax.grid(axis='y')

    img_data = io.BytesIO()
    fig.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
    
    await update.message.reply_photo(photo=img_data, caption=f"Гистограмма ({len(numbers)} значений)")

async def pie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: `/pie 30 20 50 / Состав смеси`", parse_mode='Markdown')
        return
    text = ' '.join(context.args)
    numbers, title, _, _, _, _ = parse_data_with_axes(text)
    if len(numbers) < 2:
        await update.message.reply_text("Нужно минимум 2 числа для круговой диаграммы.")
        return

    fig = Figure()
    ax = fig.add_subplot(111)
    ax.pie(numbers, labels=[str(i+1) for i in range(len(numbers))], autopct='%1.1f%%', startangle=90)
    ax.set_title(title if title else "Круговая диаграмма")

    img_data = io.BytesIO()
    fig.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
    
    await update.message.reply_photo(photo=img_data, caption=f"Круговая диаграмма ({len(numbers)} категорий)")

async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Пример: `/compare 1 2 / 3 4 / Расчет / Опыт / Время / Ток / с / А`",
            parse_mode='Markdown'
        )
        return
    text = ' '.join(context.args)
    data1, data2, label1, label2, x_label, y_label, x_unit, y_unit = parse_two_datasets_with_axes(text)
    
    if data1 is None or data2 is None:
        await update.message.reply_text("Используйте разделитель `/` между двумя наборами чисел.", parse_mode='Markdown')
        return
    if len(data1) < 2 or len(data2) < 2:
        await update.message.reply_text("В каждом наборе должно быть минимум 2 числа.")
        return

    fig = Figure()
    ax = fig.add_subplot(111)
    x1 = range(len(data1))
    x2 = range(len(data2))
    ax.plot(x1, data1, marker='o', linestyle='-', label=label1)
    ax.plot(x2, data2, marker='s', linestyle='--', label=label2)

    if len(data1) != len(data2):
        await update.message.reply_text(f"⚠️ Длины наборов разные: {len(data1)} и {len(data2)}.")

    ax.set_title("Сравнение двух наборов данных")
    ax.set_xlabel(format_axis_label(x_label if x_label else "Номер точки", x_unit))
    ax.set_ylabel(format_axis_label(y_label if y_label else "Значение", y_unit))
    ax.legend()
    ax.grid(True)

    img_data = io.BytesIO()
    fig.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
    
    await update.message.reply_photo(photo=img_data, caption=f"Сравнение: {label1} и {label2}")

# ========== ОБРАБОТЧИК ОБЫЧНОГО ТЕКСТА ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    numbers, label, x_label, y_label, x_unit, y_unit = parse_data_with_axes(text)
    
    if len(numbers) >= 2:
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.plot(numbers, marker='o', linestyle='-', label=label if label else None)
        if label:
            ax.legend()
        ax.set_title("График по вашим данным" if not label else label)
        ax.set_xlabel(format_axis_label(x_label if x_label else "Номер точки", x_unit))
        ax.set_ylabel(format_axis_label(y_label if y_label else "Значение", y_unit))
        ax.grid(True)

        img_data = io.BytesIO()
        fig.savefig(img_data, format='png', bbox_inches='tight')
        img_data.seek(0)
        
        await update.message.reply_photo(photo=img_data, caption=f"График построен. Используйте /help для справки.")
    else:
        await update.message.reply_text("Отправьте числа через пробел или запятую (минимум 2).\nИли используйте команды: /line, /bar, /scatter, /hist, /pie, /compare")

# ========== ЗАПУСК ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("line", line))
    app.add_handler(CommandHandler("bar", bar))
    app.add_handler(CommandHandler("scatter", scatter))
    app.add_handler(CommandHandler("hist", hist))
    app.add_handler(CommandHandler("pie", pie))
    app.add_handler(CommandHandler("compare", compare))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("Бот успешно запущен и готов к работе...")
    app.run_polling()

if __name__ == "__main__":
    main()