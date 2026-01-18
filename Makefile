.PHONY: help install system-deps dev run format lint clean build install-dev git-save noedit undo

# Python Interpreter
PYTHON := python3

# ==============================================================================
# 🎯 DEFAULT / HELP
# ==============================================================================
help:
	@echo "🎧 CABIN AI ASSISTANT - DEVELOPER TOOLS"
	@echo "----------------------------------------------------------------"
	@echo "🛠️  SETUP:"
	@echo "  make system-deps    - Install System Libs (PortAudio via Brew)"
	@echo "  make install        - Install Project in Editable Mode"
	@echo "  make install-dev    - Install Dev Tools (Black, MyPy, Isort)"
	@echo ""
	@echo "🌍 RUN SERVER:"
	@echo "  make dev            - Run Server with RELOAD (Development)"
	@echo "  make run            - Run Server production-like (No Reload)"
	@echo ""
	@echo "✨ CODE QUALITY:"
	@echo "  make format         - Auto Format Code (Black + Isort)"
	@echo "  make lint           - Check Code Style & Types (Flake8 + MyPy)"
	@echo ""
	@echo "📦 BUILD & RELEASE:"
	@echo "  make build          - Build Wheel & Distribution"
	@echo "  make clean          - Remove all build artifacts & cache"
	@echo ""
	@echo "🐙 GIT HELPERS:"
	@echo "  make noedit         - Commit --amend --no-edit"
	@echo "  make undo           - Soft reset HEAD~1"
	@echo "----------------------------------------------------------------"

# ==============================================================================
# 🛠️ SETUP
# ==============================================================================
system-deps:
	@echo "🔧 Installing PortAudio (macOS/Homebrew)..."
	brew install portaudio

install:
	@echo "📦 Installing Dependencies & Project..."
	CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install -e .

install-dev:
	@echo "🧪 Installing Development Tools..."
	pip install black isort flake8 mypy build

# ==============================================================================
# 🌍 RUN SERVER
# ==============================================================================
dev:
	@echo "🌍 Starting API Server (Live Reload)..."
	@echo "   👉 http://localhost:1309"
	uvicorn cabin_app.main:app --host 0.0.0.0 --port 1309 --reload

run:
	@echo "🚀 Starting Production Server..."
	# Lệnh cabin-run sẽ tự động lấy port từ config.py (1309)
	cabin-run

# ==============================================================================
# ✨ CODE QUALITY
# ==============================================================================
format:
	@echo "🎨 Formatting Code..."
	isort src/
	black src/

lint:
	@echo "🔍 Linting Code..."
	flake8 src/ --max-line-length=88 --ignore=E203,W503
	mypy src/

# ==============================================================================
# 📦 BUILD & CLEANUP
# ==============================================================================
build: clean
	@echo "🏗️  Building Distribution..."
	$(PYTHON) -m build

clean:
	@echo "🧹 Cleaning up..."
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	@echo "✅ Clean complete."

# ==============================================================================
# 🐙 GIT HELPERS
# ==============================================================================
noedit:
	@git add . && git commit --amend --no-edit

undo:
	@git reset --soft HEAD~1