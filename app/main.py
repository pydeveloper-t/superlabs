import os
import argparse
from api.papertrader import Papertrader, Calculation
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

paper_trader = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Bot for https://paper-trader.frwd.one."
    )


async def work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip():
        calculation = Calculation(pair=update.message.text, timeframe=None, candles=None, ma=None, tp=None, sl=None)
        image_file = await paper_trader.process(calculation_param=calculation)
        if image_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                caption=update.message.text,
                photo=image_file
            )
            try:
                os.remove(image_file)
            except:
                pass
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"No calculation has been made for "
                                                                                  f"the pair '{update.message.text}'. "
                                                                                  f"Check the input data")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='https://paper-trader.frwd.one')
    parser.add_argument('--path', help='Path to root folder', type=str, required=True)
    token = os.environ.get('tl_token')
    if not token:
        raise SystemExit('The environment variable "tl_token" not set')
    paper_trader = Papertrader(project_tag='papertrader', basepath=parser.parse_args().path)
    application = ApplicationBuilder().token(token).build()
    start_handler = CommandHandler('start', start)
    work_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), work)
    application.add_handler(start_handler)
    application.add_handler(work_handler)
    application.run_polling()
