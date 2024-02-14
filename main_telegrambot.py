import logging
from openai import OpenAI

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure the LM Studio client with the local server
client = OpenAI(base_url="http://localhost:4000/v1", api_key="not-needed")

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am a bot powered by an intelligent assistant. How can I assist you today?",
        reply_markup=ForceReply(selective=True),
    )

async def chat_with_llm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the user's message to the LLM and return the response."""
    input_text = update.message.text
    await update.message.reply_text("Message received. Let me think...")
    # Initialize the conversation history if it doesn't exist in the context
    if 'history' not in context.bot_data:
        context.bot_data['history'] = [
            {"role": "system", "content": "You are an assistant called Ben. You are an assistant of Max. Keep the answer under 50 words"},
            # Add the initial user message to the history
            {"role": "user", "content": input_text},
        ]
    else:
        # Append new user message to the existing history
        context.bot_data['history'].append({"role": "user", "content": input_text})

    # Make the request to the locally running server
    completion = client.chat.completions.create(
        model="local-model",  # this field is currently unused
        messages=context.bot_data['history'],
        temperature=0.7,
    )

    # Extract the response content
    response_content = completion.choices[0].message.content if completion.choices[0].message else ''
    
    # Send the response content to the user
    await update.message.reply_text(response_content)

    # Update the history with the assistant's response
    context.bot_data['history'].append({"role": "assistant", "content": response_content})

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("Telegram_API").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non-command i.e message - send the message to LLM
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_llm))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
