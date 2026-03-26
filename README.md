# 🚀 Smart Email Classifier – Email Categorization System

An AI-powered web application that automatically classifies emails into categories like **Work, Social, Spam, and Purchases**.  
It helps users manage their inbox efficiently and identify unwanted or malicious emails. 🤖📩  

---

## 📌 Features

- 🔐 **Secure Authentication**  
  User login system using Supabase with encrypted credentials  

- 📥 **Live Gmail Integration**  
  Fetch latest emails using IMAP and Google App Password  

- 📸 **OCR Support**  
  Extract and classify text from screenshots/images using Tesseract OCR  

- 🧠 **Machine Learning Model**  
  Built with Scikit-Learn to accurately categorize emails  

- 🎨 **Modern UI**  
  Responsive and dark-mode friendly interface using Streamlit  

---

## 🛠️ Tech Stack

- **Python** – Core logic  
- **Scikit-Learn** – Machine Learning  
- **Supabase / PostgreSQL** – Database & Backend  
- **Streamlit** – Frontend  
- **Pytesseract** – OCR  
- **GitHub & Streamlit Cloud** – Deployment  

---

## ⚙️ How It Works

1. User logs in securely  
2. Connects Gmail using App Password  
3. Fetches latest emails from inbox  
4. ML model analyzes email content  
5. Emails are categorized into:
   - Work  
   - Social  
   - Spam  
   - Purchases  
