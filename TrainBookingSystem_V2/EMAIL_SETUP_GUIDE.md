# 🚂 Bangladesh Railway Booking System V2 - Email Setup Guide

## ✨ New Features

This enhanced version includes:
- **Modern, Polished GUI** with smooth animations
- **Gmail Ticket Delivery** - Send tickets directly to customer email
- **Interactive Seat Maps** with visual indicators
- **Real-time Status Updates** 
- **Professional Email Templates** with QR codes

---

## 📧 Gmail Email Setup (Required for Ticket Delivery)

### Step 1: Prepare Your Gmail Account

1. **Open Google Account Settings**
   - Go to: https://myaccount.google.com/security

2. **Enable 2-Step Verification**
   - Click on "2-Step Verification" 
   - Follow the setup wizard
   - This is **required** for App Passwords

### Step 2: Generate App Password

1. **Navigate to App Passwords**
   - Go to: https://myaccount.google.com/apppasswords
   - Or: Security → App passwords

2. **Create New App Password**
   - Select app: **Mail**
   - Select device: **Windows Computer** (or your device)
   - Click **Generate**

3. **Copy the 16-Character Password**
   - Google will show a 16-character password
   - **Copy this immediately** (it won't be shown again)
   - Example format: `abcd efgh ijkl mnop`

### Step 3: Configure in Application

1. **Launch the Application**
   - Run: `python main_v2.py`
   - Login or register an account

2. **Go to Settings Tab**
   - Click on the "⚙️ Settings" tab

3. **Enter Your Credentials**
   - **Gmail Address**: Your full Gmail address (e.g., `yourname@gmail.com`)
   - **App Password**: Paste the 16-character password (remove spaces)
   - Click **"💾 Save Email Settings"**

4. **Test Email Delivery**
   - Click **"✉️ Send Test Email"**
   - Enter a recipient email
   - Check if test email arrives

### Step 4: Configure .env File (Alternative Method)

You can also configure email by editing the `.env` file:

```env
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop
```

---

## 🎫 How to Use Ticket Email Delivery

### Single Ticket Booking

1. Fill in booking details
2. Click **"🎫 Book Ticket"**
3. Success dialog will appear
4. Enter recipient email (pre-filled with your email)
5. Click **"📨 Send Ticket to Email"**
6. Wait for confirmation
7. Check inbox for ticket with QR code

### Round Trip Booking

1. Fill in onward and return journey details
2. Click **"🎫 Book Round Trip"**
3. Choose to send tickets via email
4. All tickets will be sent automatically

---

## 📨 What's Included in Email

Each ticket email contains:

- ✅ **Professional HTML Template** with Bangladesh Railway branding
- 🎫 **Complete Booking Details** (ID, Train, Date, Seat, etc.)
- 📱 **QR Code Attachment** for easy scanning at station
- 🎨 **Color-coded Status** indicators
- 📋 **Journey Information** and instructions

---

## ⚠️ Troubleshooting

### "Email not configured" Error
- **Solution**: Go to Settings tab and configure Gmail credentials

### "Authentication failed" Error
- **Solution**: Make sure you're using an **App Password**, not your regular Gmail password
- Check that 2-Step Verification is enabled

### "Connection timeout" Error
- **Solution**: Check your internet connection
- Ensure port 587 is not blocked by firewall

### Email not received
- **Solution**: Check spam/junk folder
- Verify recipient email address is correct
- Try sending test email first

### "Invalid credentials" Error
- **Solution**: Re-generate App Password from Google Account
- Remove any spaces from the password
- Make sure 2-Step Verification is still enabled

---

## 🔒 Security Notes

- ✅ App Passwords are safer than using your main Gmail password
- ✅ App Passwords can be revoked anytime from Google Account settings
- ✅ `.env` file is excluded from version control (in `.gitignore`)
- ⚠️ Never share your App Password publicly
- ⚠️ Don't commit `.env` file to Git repositories

---

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements_v2.txt
   ```

2. **Start API Server** (in one terminal)
   ```bash
   python api_server_v2.py
   ```

3. **Start Application** (in another terminal)
   ```bash
   python main_v2.py
   ```

4. **Configure Email**
   - Login/Register
   - Go to Settings tab
   - Enter Gmail credentials
   - Test email delivery

5. **Start Booking!**
   - Book tickets
   - Automatically send to email
   - Customers receive professional tickets with QR codes

---

## 📦 Required Packages

All required packages are in `requirements_v2.txt`:

- `python-dotenv` - For environment variables
- `qrcode` - For QR code generation
- `pillow` - For image processing
- `matplotlib` - For charts and analytics
- And more...

---

## 💡 Tips

- **Pre-fill Email**: Your registered email is pre-filled when sending tickets
- **Multiple Recipients**: You can send same ticket to different emails multiple times
- **QR Code**: Each ticket has a unique QR code attached
- **Professional Look**: Emails are HTML-formatted with modern design
- **Instant Delivery**: Emails are sent in background thread (non-blocking)

---

## 🎯 Features Overview

### Modern GUI Enhancements
- ✨ Gradient-style headers
- 🎨 Color-coded seat maps with window indicators
- 💺 Interactive seat selection
- 🎭 Hover effects and animations
- 📊 Real-time status updates
- ⏰ Live clock in status bar

### Email Features
- 📧 Gmail SMTP integration
- 🎫 Professional HTML email templates
- 📱 QR code generation and attachment
- 🔄 Background email sending
- ✅ Delivery confirmation
- 🧪 Test email functionality

### User Experience
- 👤 User authentication system
- 💾 Remember user details
- 🔄 Auto-refresh booking history
- ⚡ Fast and responsive
- 🎯 Intuitive navigation

---

## 📞 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Verify all dependencies are installed
3. Ensure API server is running
4. Check Gmail credentials are correct
5. Test with a simple test email first

---

## 🎉 Enjoy Your Modern Railway Booking System!

Happy booking! 🚂✨

