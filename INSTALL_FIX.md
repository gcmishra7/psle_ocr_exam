# 🔧 Installation Fix Guide

## ❌ **Problem:** sqlite3-utils installation error

You encountered: `ERROR: Could not find a version that satisfies the requirement sqlite3-utils>=3.35.0`

## ✅ **Solution:** Use the smart setup script

I've fixed the dependency issue and created better installation options.

---

## 🚀 **Option 1: Smart Setup Script (Recommended)**

```bash
# Run the smart setup script
python setup_quiz_system.py
```

This script will:
- ✅ Install essential packages one by one
- ✅ Skip problematic dependencies 
- ✅ Test each installation
- ✅ Set up directories and environment
- ✅ Provide clear error messages

---

## 🚀 **Option 2: Manual Essential Installation**

If the setup script doesn't work, install manually:

```bash
# Install core packages first
pip install streamlit>=1.28.0
pip install gradio>=4.0.0
pip install Pillow>=10.1.0
pip install pandas>=2.1.0
pip install python-dotenv>=1.0.0
pip install numpy>=1.24.0

# Optional: Install enhanced features
pip install pdf2image>=1.17.0
pip install opencv-python-headless>=4.8.0
pip install pytesseract>=0.3.10
```

---

## 🚀 **Option 3: Simplified Requirements**

Use the fixed requirements file:

```bash
# Use the simplified requirements (no sqlite3-utils)
pip install -r requirements_simple.txt
```

---

## 🎓 **Start the Quiz System**

After installation, start the system:

```bash
# Complete system (recommended)
python enhanced_main.py --mode both

# Or just the quiz interface
python enhanced_main.py --mode gradio
```

**URLs:**
- **PDF Processing:** http://localhost:8501
- **Quiz Interface:** http://localhost:7860

---

## 🔧 **What I Fixed**

1. **Removed sqlite3-utils** - Using built-in Python sqlite3 instead
2. **Created smart setup script** - Installs packages individually with error handling
3. **Simplified requirements** - Only essential packages for core functionality
4. **Better error handling** - Clear messages when packages fail

---

## 📊 **Database Note**

The original error was caused by `sqlite3-utils>=3.35.0` which isn't needed because:
- ✅ Python includes `sqlite3` built-in
- ✅ Our `SimpleDatabaseManager` uses built-in sqlite3
- ✅ No external sqlite3 packages required

---

## 🎯 **Quick Test**

After installation, test the quiz system:

```bash
# Test if essential components work
python -c "import streamlit, gradio, PIL; print('✅ Essential packages installed!')"

# Test if optional components work  
python -c "import cv2, numpy, pdf2image; print('✅ Optional packages installed!')"
```

---

## 🚀 **Ready to Go**

Your enhanced quiz system with:
- ✅ **Gradio interface** (much better than Streamlit for quizzes)
- ✅ **Smart image extraction** (diagrams, tables, equations - no full pages)
- ✅ **Proper image display** (fixed all path issues)
- ✅ **Modern quiz experience** (prev/next navigation, progress tracking)

**Start now:**
```bash
python setup_quiz_system.py
```