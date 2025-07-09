# 🚨 Emergency Installation Guide

## ❌ **Problem:** Pip/Network Errors During Installation

You're encountering pip errors like:
```
ERROR: Exception:
Traceback (most recent call last):
  File "pip/_vendor/urllib3/response.py", line 438, in _error_catcher
```

## ✅ **SOLUTION: Multiple Installation Methods**

I've created several robust installation options to handle these errors.

---

## 🚀 **Method 1: Robust Installer (Recommended)**

This installer handles pip errors and tries multiple installation methods:

```bash
python install_robust.py
```

**Features:**
- ✅ Automatically upgrades pip
- ✅ Tries 5 different installation methods per package
- ✅ Handles network timeouts and errors
- ✅ Provides detailed error reporting
- ✅ Creates directories and configuration

---

## 🚀 **Method 2: Manual Step-by-Step**

If the robust installer fails, install manually:

### Step 1: Fix Pip
```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# If that fails, try with no cache
python -m pip install --upgrade pip --no-cache-dir
```

### Step 2: Install Core Packages
```bash
# Install packages one by one
python -m pip install streamlit --no-cache-dir
python -m pip install gradio --no-cache-dir
python -m pip install Pillow --no-cache-dir
python -m pip install pandas --no-cache-dir
python -m pip install python-dotenv --no-cache-dir
python -m pip install numpy --no-cache-dir
```

### Step 3: Test Installation
```bash
python -c "import streamlit, gradio, PIL; print('✅ Core packages working!')"
```

---

## 🚀 **Method 3: Alternative Package Managers**

If pip continues to fail, try alternative methods:

### Using conda (if available):
```bash
conda install streamlit gradio pillow pandas python-dotenv numpy -c conda-forge
```

### Using homebrew (macOS):
```bash
brew install python
pip3 install streamlit gradio Pillow pandas python-dotenv numpy
```

---

## 🚀 **Method 4: Offline Installation**

For persistent network issues:

### Download packages manually:
1. Go to https://pypi.org/
2. Download `.whl` files for: streamlit, gradio, Pillow, pandas, python-dotenv, numpy
3. Install locally:
```bash
python -m pip install /path/to/downloaded/package.whl
```

---

## 🎓 **Start the Quiz System**

Once any core packages are installed, you can start:

### Option A: Simple Launcher
```bash
python start_quiz.py
```

### Option B: Direct Launch
```bash
# For quiz interface only
python enhanced_main.py --mode gradio

# For both interfaces
python enhanced_main.py --mode both
```

### Option C: Individual Components
```bash
# Start Gradio quiz interface
python -c "
from app.gradio_quiz_app import launch_quiz_app
launch_quiz_app()
"

# Start Streamlit processing (separate terminal)
python -m streamlit run main.py --server.port=8501
```

---

## 🔧 **Common Pip Error Solutions**

### Error: "Could not find a version that satisfies the requirement"
```bash
# Try with --force-reinstall
python -m pip install --force-reinstall package_name

# Try with different index
python -m pip install --index-url https://pypi.org/simple/ package_name
```

### Error: "urllib3" or network issues
```bash
# Clear pip cache
python -m pip cache purge

# Install with no cache
python -m pip install --no-cache-dir package_name

# Use trusted host
python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org package_name
```

### Error: "Permission denied"
```bash
# Install for current user only
python -m pip install --user package_name
```

---

## 🎯 **Minimum Working Setup**

You only need these 4 packages for basic functionality:

```bash
pip install streamlit gradio Pillow pandas
```

Then create these files manually:

### Create `data` directories:
```bash
mkdir -p data/images data/uploads
```

### Create `.env` file:
```bash
echo "DATABASE_PATH=./data/questions.db" > .env
```

---

## 🚀 **Test Your Installation**

After any installation method, test with:

```bash
# Test basic imports
python -c "
try:
    import streamlit, gradio, PIL, pandas
    print('✅ SUCCESS: All core packages working!')
    print('🚀 Start quiz with: python start_quiz.py')
except ImportError as e:
    print(f'❌ Missing: {e}')
"
```

---

## 🎉 **What You Get**

Once installed, your enhanced quiz system provides:

- ✅ **Modern Gradio Interface** - Much better than Streamlit for quizzes
- ✅ **Smart Image Extraction** - Diagrams, tables, equations (no full pages)
- ✅ **Proper Image Display** - Fixed all path and rendering issues
- ✅ **Quiz Navigation** - Previous/Next buttons, progress tracking
- ✅ **Answer Recording** - Interactive MCQ selection with feedback

---

## 🆘 **Still Having Issues?**

If all methods fail, you can:

1. **Use Python Virtual Environment:**
```bash
python -m venv quiz_env
source quiz_env/bin/activate  # Linux/Mac
# or
quiz_env\Scripts\activate     # Windows
pip install streamlit gradio Pillow pandas
```

2. **Contact Support:** 
   - Check the error logs for specific issues
   - Try installation on a different network
   - Consider using a different Python version (3.8-3.11 recommended)

---

## 🚀 **Quick Start (Any Method)**

```bash
# Try the robust installer first
python install_robust.py

# If that fails, install manually
pip install streamlit gradio Pillow pandas

# Start the quiz system
python start_quiz.py
```

**Your enhanced quiz system with Gradio interface and smart image extraction is ready!** 🎉