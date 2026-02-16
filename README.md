# ⚡ AMXX Compiler v2.0

**Professional AMX Mod X Plugin Compiler API** - Fast, Reliable, Easy to Use

[![Deploy on Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy)

---

## 🌟 Features

### Core Capabilities
- ✅ **Batch Compilation**: Compile up to 10 plugins simultaneously
- ✅ **Custom Includes**: Support for 10 custom `.inc` files per request  
- ✅ **Unlimited File Sizes**: No restrictions on source code size
- ✅ **ZIP Downloads**: All compiled plugins packaged as a single ZIP file
- ✅ **Smart Rate Limiting**: 10 compilations per 120 seconds
- ✅ **Auto Cleanup**: Temporary files automatically deleted after 10 minutes
- ✅ **Beautiful Web UI**: Professional interface for easy compilation
- ✅ **RESTful API**: Full-featured API for integration
- ✅ **No Database Required**: Everything is temporary and memory-based
- ✅ **Detailed Error Reporting**: Line numbers, error codes, and warnings

### Technical Highlights
- 🚀 Built with Flask & Gunicorn
- 🐳 Docker containerized
- 🔒 Secure input validation
- 📊 Real-time compilation statistics
- 🌍 Ready for cloud deployment
- 📝 Comprehensive API documentation

---

## 🚀 Quick Start

### Option 1: Deploy to Koyeb (Recommended)

[![Deploy on Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy)

1. Click the button above
2. Connect your GitHub account
3. Select this repository
4. Click "Deploy"
5. Your compiler will be live in 2-3 minutes!

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

### Option 2: Run Locally with Docker

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/amxx-compiler.git
cd amxx-compiler

# Build Docker image
docker build -t amxx-compiler .

# Run container
docker run -p 8000:8000 amxx-compiler

# Access at http://localhost:8000
```

### Option 3: Run Locally without Docker

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/amxx-compiler.git
cd amxx-compiler

# Install dependencies
pip install -r requirements.txt

# Run server
python server.py

# Access at http://localhost:8000
```

---

## 📖 Usage

### Web Interface

1. Open your deployed URL or `http://localhost:8000`
2. Click **"+ Add Plugin"** to add plugins
3. Paste your AMX Mod X source code
4. (Optional) Add custom include files
5. Click **"🚀 Compile All Plugins"**
6. Download your compiled plugins as ZIP!

### API Usage

**Simple Compilation:**
```bash
curl -X POST https://your-app.koyeb.app/compile \
  -H "Content-Type: application/json" \
  -d '{
    "plugins": [
      {
        "name": "my_plugin",
        "code": "#include <amxmodx>\n\npublic plugin_init() {\n    register_plugin(\"Test\", \"1.0\", \"Author\");\n}"
      }
    ]
  }'
```

**Batch Compilation with Includes:**
```bash
curl -X POST https://your-app.koyeb.app/compile \
  -H "Content-Type: application/json" \
  -d '{
    "includes": {
      "utils.inc": "stock my_function() { }"
    },
    "plugins": [
      {"name": "plugin1", "code": "..."},
      {"name": "plugin2", "code": "..."}
    ]
  }'
```

**Download Compiled Plugins:**
```bash
curl -O -J https://your-app.koyeb.app/download/COMPILATION_ID
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/health` | GET | Health check |
| `/stats` | GET | Compilation statistics |
| `/compile` | POST | Compile plugins |
| `/download/<id>` | GET | Download compiled ZIP |
| `/info/<id>` | GET | Get compilation info |

---

## ⚙️ Configuration

### Limits
```python
MAX_PLUGINS_PER_REQUEST = 10       # Maximum plugins per compilation
MAX_INCLUDES_PER_REQUEST = 10      # Maximum include files
COMPILE_TIMEOUT = 30               # Seconds per plugin
RATE_LIMIT_WINDOW = 120            # Rate limit cooldown (seconds)
FILE_RETENTION_TIME = 600          # File retention (10 minutes)
```

### Features
- **Unlimited File Sizes**: No restrictions on `.sma` or `.inc` files
- **Automatic Cleanup**: Old files deleted every 5 minutes
- **Rate Limiting**: IP-based, 10 compilations per 120 seconds
- **No Database**: Everything stored temporarily in memory
- **Security**: Input validation, path traversal prevention

---

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
│ (Web/API)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Flask Server      │
│   (Gunicorn)        │
│  - Rate Limiting    │
│  - Input Validation │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  AMXX Compiler      │
│  - Compiles .sma    │
│  - Includes support │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Temporary Storage  │
│  - ZIP creation     │
│  - Auto cleanup     │
└─────────────────────┘
```

---

## 📦 Project Structure

```
amxx-compiler/
├── server.py              # Main Flask application
├── index.html             # Web interface
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
├── amxxpc                 # AMX Mod X compiler binary
├── amxxpc32.so            # 32-bit library
├── scripting/             # Official include files
│   └── include/           # .inc files
├── temp_builds/           # Temporary build directory
├── README.md              # This file
├── DEPLOYMENT_GUIDE.md    # Deployment instructions
└── API_DOCUMENTATION.md   # API reference
```

---

## 🔧 Development

### Requirements
- Python 3.11+
- Flask 3.0.0
- Gunicorn 21.2.0
- 32-bit libraries (for compiler)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run in Development Mode
```bash
python server.py
```

### Build Docker Image
```bash
docker build -t amxx-compiler .
```

### Run Tests
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test compilation
curl -X POST http://localhost:8000/compile \
  -H "Content-Type: application/json" \
  -d '{"plugins":[{"name":"test","code":"#include <amxmodx>\npublic plugin_init() {}"}]}'
```

---

## 🚀 Deployment

### Koyeb (Recommended)

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions.

**Quick Steps:**
1. Push code to GitHub
2. Connect GitHub to Koyeb
3. Select repository
4. Deploy with Dockerfile
5. Done!

### Other Platforms

**Heroku:**
```bash
heroku create amxx-compiler
heroku stack:set container
git push heroku main
```

**Railway:**
```bash
railway init
railway up
```

**Google Cloud Run:**
```bash
gcloud run deploy amxx-compiler \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 📈 Performance

### Benchmarks
- **Compilation Speed**: ~1-3 seconds per plugin
- **Memory Usage**: ~100-200 MB (idle)
- **Request Handling**: 10 requests/120s (rate limited)
- **File Processing**: Unlimited size

### Optimization Tips
1. Use shared includes for common code
2. Batch multiple plugins in one request
3. Download files immediately (10-minute expiry)
4. Scale horizontally for high traffic

---

## 🔒 Security

### Input Validation
- ✅ Filename sanitization
- ✅ Path traversal prevention
- ✅ File extension validation
- ✅ Secure file handling

### Rate Limiting
- ✅ IP-based rate limiting
- ✅ 10 compilations per 120 seconds
- ✅ Automatic cooldown

### Temporary Storage
- ✅ No permanent data storage
- ✅ Automatic file cleanup
- ✅ 10-minute file retention
- ✅ Memory-based metadata

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Guidelines
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Keep commits atomic

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **AMX Mod X Team** - For the amazing compiler
- **Flask** - Web framework
- **Koyeb** - Cloud hosting platform
- **Community** - For feedback and support

---

## 📞 Support

### Documentation
- 📖 [Deployment Guide](DEPLOYMENT_GUIDE.md)
- 📚 [API Documentation](API_DOCUMENTATION.md)
- 🌐 [AMX Mod X Docs](https://www.amxmodx.org/)

### Help & Issues
- 🐛 [Report a Bug](https://github.com/YOUR_USERNAME/amxx-compiler/issues)
- 💡 [Request a Feature](https://github.com/YOUR_USERNAME/amxx-compiler/issues)
- 💬 [Discussions](https://github.com/YOUR_USERNAME/amxx-compiler/discussions)

### Contact
- 📧 Email: your.email@example.com
- 🐦 Twitter: @yourhandle
- 💬 Discord: Your Server

---

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/amxx-compiler?style=social)
![GitHub forks](https://img.shields.io/github/forks/YOUR_USERNAME/amxx-compiler?style=social)
![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/amxx-compiler)
![GitHub license](https://img.shields.io/github/license/YOUR_USERNAME/amxx-compiler)

---

## 🗺️ Roadmap

### v2.1 (Planned)
- [ ] Multi-language support
- [ ] Plugin templates
- [ ] Code syntax highlighting
- [ ] Real-time compilation status

### v2.2 (Planned)
- [ ] Webhook notifications
- [ ] API key authentication
- [ ] Custom compiler flags
- [ ] Compilation history

### v3.0 (Future)
- [ ] Plugin testing framework
- [ ] Code analysis tools
- [ ] Version control integration
- [ ] Collaborative editing

---

## 🎯 Use Cases

### Perfect For:
- ✅ AMX Mod X plugin developers
- ✅ Counter-Strike server administrators
- ✅ Game server communities
- ✅ Development teams
- ✅ Educational purposes

### Example Scenarios:
1. **Quick Testing**: Compile and test plugins without local setup
2. **Batch Processing**: Compile multiple plugins at once
3. **Team Collaboration**: Share compilation link with team
4. **CI/CD Integration**: Automate plugin builds
5. **Learning**: Practice AMX Mod X development

---

## 📸 Screenshots

### Web Interface
![Web Interface](https://via.placeholder.com/800x400?text=Web+Interface+Screenshot)

### API Response
![API Response](https://via.placeholder.com/800x400?text=API+Response+Screenshot)

### Download ZIP
![Download](https://via.placeholder.com/800x400?text=Download+Screenshot)

---

## 🔗 Links

- 🌐 **Live Demo**: [https://amxx-compiler.koyeb.app](https://amxx-compiler.koyeb.app)
- 📦 **GitHub**: [https://github.com/YOUR_USERNAME/amxx-compiler](https://github.com/YOUR_USERNAME/amxx-compiler)
- 📚 **Documentation**: [Docs](https://docs.yoursite.com)
- 🎮 **AMX Mod X**: [https://www.amxmodx.org](https://www.amxmodx.org)

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=YOUR_USERNAME/amxx-compiler&type=Date)](https://star-history.com/#YOUR_USERNAME/amxx-compiler&Date)

---

**Made with ❤️ by the AMX Mod X Community**

**Version**: 2.0.0 | **Last Updated**: February 15, 2026

---

<p align="center">
  <a href="https://app.koyeb.com/deploy">
    <img src="https://www.koyeb.com/static/images/deploy/button.svg" alt="Deploy on Koyeb">
  </a>
</p>
