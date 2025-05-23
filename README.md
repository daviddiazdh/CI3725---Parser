# 🧠 CI3725 — Micro Parser

This project implements a micro parser capable of **translating code** from an **Imperative Language** to a **Lambda Language**.

---

## 📄 First Step: Lexer

The **Lexer** is the module responsible for recognizing valid and invalid tokens. It outputs either:
- A list of recognized tokens, or
- A list of lexical errors (if any are found)

> ⚠️ This step is **essential** for all subsequent stages of the parser.

### 📦 Usage

```bash
python lexer.py [file]
bash```

- [file] has to be a .imperat file