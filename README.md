# 🤖 Afaq Store Bot

An intelligent Telegram bot for Afaq Store that helps customers find products using AI-powered conversations, image analysis, and voice messages.

## ✨ Features

- 💬 Natural Arabic conversations (Egyptian dialect)
- 🖼️ Image analysis for product recommendations
- 🎤 Voice message support
- 📦 Product catalog integration
- 💾 Conversation history with PostgreSQL
- 📊 Built-in metrics and monitoring
- 🔄 Automatic retry logic for API calls
- 🧹 Admin tools for maintenance

## 📁 Project Structure

```
afaq-store-bot/
├── app.py                  # Main Flask application
├── config.py              # Configuration management
├── database.py            # Database operations
├── models.py              # AI model initialization
├── handlers/
│   ├── telegram.py        # Telegram handlers
│   └── commands.py        # Bot commands
├── services/
│   ├── gemini.py          # Gemini AI logic
│   ├── products.py        # Product management
│   └── history.py         # Conversation history
├── utils/
│   ├── logger.py          # Logging setup
│   ├── metrics.py         # Metrics tracking
│   └── validators.py      # Input validation
└── routes/
    ├── health.py          # Health check
    ├── metrics.py         # Metrics endpoint
    └── admin.py           # Admin endpoints
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/afaq-store-bot.git
cd afaq-store-bot
```

### 2. Set Up Environment

```bash

python -m venv venv
source venv\Scripts\activate

pip install -r requirements.txt

```

### 3. Run Locally

```bash
python app.py
```

## 🔧 Configuration

Required environment variables:

```env
GEMINI_API_KEY=your_gemini_api_key
TELEGRAM_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://... (optional for local)
```

See `.env.example` for all available options.

## 🚂 Deploy to Railway

1. **Create a new Railway project**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"

2. **Add PostgreSQL**
   - Click "New" → "Database" → "PostgreSQL"
   - Railway automatically sets `DATABASE_URL`

3. **Set Environment Variables**
   ```
   GEMINI_API_KEY=your_key
   TELEGRAM_TOKEN=your_token
   ```

4. **Deploy**
   - Push to GitHub
   - Railway automatically deploys

## 📊 API Endpoints

- `GET /` - Home page with status
- `GET /health` - Health check
- `GET /metrics` - Bot metrics
- `POST /telegram` - Telegram webhook
- `POST /admin/cleanup` - Clean old conversations (requires auth)

## 🤖 Bot Commands

- `/start` - Welcome message
- `/help` - Show help
- `/clear` or `/reset` - Clear conversation history
- `/stats` - Show user statistics

## 🛠️ Development

### Code Structure

Each module is independent:
- `handlers/` - Process incoming messages
- `services/` - Business logic
- `routes/` - HTTP endpoints
- `utils/` - Helper functions

## 📝 Adding New Features

### Add a New Command

Edit `handlers/commands.py`:

```python
def handle_command(command, user_key):
    if command == "/newcommand":
        return "Response for new command"
```

### Add a New Route

Create file in `routes/` and register in `app.py`:

```python
from routes.myroute import myroute_bp
app.register_blueprint(myroute_bp)
```

## 🔒 Security

- API keys stored in environment variables
- Admin endpoints protected with bearer token
- File size validation for uploads
- Input validation for all requests

## 📈 Monitoring

Check `/metrics` for:
- Total messages processed
- Response time percentiles (P50, P95, P99)
- Error counts
- Active conversations

## 🧹 Maintenance

Clean old conversations (30+ days):

```bash
curl -X POST https://your-app.railway.app/admin/cleanup \
  -H "Authorization: Bearer your_admin_secret"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License

## 💬 Support

For issues and questions, please open a GitHub issue.

## 🎉 Acknowledgments

- Built with [Gemini AI](https://ai.google.dev/)
- Deployed on [Railway](https://railway.app)
- Telegram Bot API