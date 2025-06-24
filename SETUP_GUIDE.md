# 🚀 MCP Terminology Database Setup Guide

This guide shows you how to connect **real terminology databases** to your MCP server.

## 📁 **Step 1: Prepare Your TBX Files**

### **What are TBX files?**
TBX (TermBase eXchange) files are the industry standard for terminology databases used by:
- Microsoft Terminology Collection
- Apple Localization Glossary  
- SDL MultiTerm
- Professional translation tools

### **Where to put TBX files:**
```
data/
├── sample_ui_terms.tbx     ← We created this for you
├── microsoft_terms.tbx     ← Download from Microsoft
├── apple_terms.tbx         ← Your Apple glossary
└── custom_terms.tbx        ← Your company terms
```

### **TBX file format example:**
```xml
<termEntry id="login_001">
  <descrip type="subjectField">UI</descrip>
  <langSet xml:lang="en">
    <tig>
      <term>sign in</term>
      <termNote type="termType">preferred</termNote>
    </tig>
  </langSet>
  <langSet xml:lang="ja">
    <tig>
      <term>サインイン</term>
      <termNote type="termType">preferred</termNote>
    </tig>
  </langSet>
</termEntry>
```

---

## 🔧 **Step 2: Import TBX to Database**

### **Test the database system:**
```bash
python test_database.py
```

### **Import your TBX files:**
```bash
# Import single file
python data/tbx_importer.py data/sample_ui_terms.tbx

# Import all TBX files in data/
python data/tbx_importer.py data/

# Check statistics
python data/tbx_importer.py --stats
```

### **Expected output:**
```
✅ Import complete! 15 terms added to database.
📊 Database now contains 21 terms
```

---

## 🗄️ **Step 3: Verify Database Integration**

### **Test terminology checking:**
```bash
python test_database.py
```

### **What you'll see:**
```
🗄️ Testing Database-Driven Terminology Checker
📊 Database Statistics:
   Terms: 21
   Rules: 6
   Languages: {'en': 10, 'jp': 11}

📝 Text: 'Please login to continue'
   1. 'login' → 'sign in'
      Reason: Prefer "sign in" over "login"
      Source: rules
```

---

## 🔌 **Step 4: Connect to MCP**

### **Start the MCP server:**
```bash
# Start server
python -m uvicorn app.main:app --reload

# Or with Docker
docker compose up --build
```

### **Test MCP endpoints:**
```bash
# List available tools
curl http://localhost:8000/mcp/tools

# Check terminology
curl -X POST http://localhost:8000/mcp/call \
  -H "Authorization: Bearer TEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "check_ui_terminology",
    "arguments": {
      "text": "Please login to your email",
      "language": "en",
      "context": "login form"
    }
  }'
```

---

## 📈 **Step 5: Add Your Own Terminology**

### **Option A: Import existing TBX files**
1. Download Microsoft/Apple terminology
2. Save to `data/` folder
3. Run importer: `python data/tbx_importer.py data/your_file.tbx`

### **Option B: Add terms programmatically**
```python
from app.core.terminology import TerminologyChecker

checker = TerminologyChecker()

# Add custom terminology
checker.add_terminology(
    source_lang="en",
    target_lang="jp", 
    source_term="dashboard",
    target_term="ダッシュボード",
    term_type="preferred",
    domain="UI"
)

# Add custom rule
checker.add_rule(
    language="en",
    pattern=r"\bapp\b",
    replacement="application",
    rule_type="preferred_synonym",
    description="Use 'application' in formal contexts"
)
```

### **Option C: Create your own TBX file**
1. Copy `data/sample_ui_terms.tbx`
2. Edit with your terminology
3. Import: `python data/tbx_importer.py data/my_terms.tbx`

---

## 🎯 **Real-World Usage**

### **For Companies:**
1. Export your CAT tool terminology to TBX
2. Import into MCP database
3. Connect to LLM clients (Claude, ChatGPT, etc.)
4. Get consistent terminology suggestions

### **For Translators:**
1. Use SDL MultiTerm or similar to create TBX
2. Import client-specific terminology
3. Use MCP for real-time checking

### **For Developers:**
1. Maintain company style guide as TBX
2. Integrate with development workflow
3. Automate UI copy review

---

## 🔍 **Troubleshooting**

### **"No module named 'core'"**
```bash
# Make sure you're in the right directory
cd "Bilingual Checker MCP"
python test_database.py
```

### **"Database file not found"**
- Database is created automatically
- Check permissions in `data/` folder

### **"TBX import failed"**
- Verify TBX file is valid XML
- Check language codes (en, ja, jp)

### **"No terminology found"**
- Import TBX files first
- Check database stats: `python data/tbx_importer.py --stats`

---

## 🚀 **Next Steps**

1. ✅ **Database working** → Add LLM integration
2. ✅ **LLM integrated** → Build web frontend  
3. ✅ **Frontend ready** → Deploy for recruiters
4. ✅ **Deployed** → Add to portfolio

**You're now ready to connect LLMs to your terminology database!** 🎉 