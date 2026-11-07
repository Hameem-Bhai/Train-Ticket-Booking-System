import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import qrcode
from io import BytesIO
import threading
import webbrowser

from api_client_v2 import TrainAPIClientV2

# Try loading dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional


class ToolTip:
    """Create tooltip for widgets"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.show)
        self.widget.bind('<Leave>', self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox('insert')
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f'+{x}+{y}')

        label = tk.Label(self.tooltip, text=self.text,
                        background='#1e293b', foreground='#e2e8f0',
                        relief='solid', borderwidth=1,
                        font=('Segoe UI', 9), padx=8, pady=6)
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class EmailService:
    """Service for sending ticket confirmations via email"""

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('EMAIL_ADDRESS', '')
        self.sender_password = os.getenv('EMAIL_PASSWORD', '')

    def configure_email(self, email, password):
        """Configure email credentials"""
        self.sender_email = email
        self.sender_password = password

        # Save to .env file
        with open('.env', 'w') as f:
            f.write(f'EMAIL_ADDRESS={email}\n')
            f.write(f'EMAIL_PASSWORD={password}\n')

    def generate_qr_code(self, booking_id):
        """Generate QR code for booking"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"BOOKING:{booking_id}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    def create_ticket_html(self, booking_data):
        """Create HTML ticket template"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
                .ticket {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; 
                          box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
                          color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
                .content {{ padding: 30px; }}
                .info-row {{ display: flex; justify-content: space-between; padding: 15px 0; 
                           border-bottom: 1px solid #e5e7eb; }}
                .info-label {{ color: #6b7280; font-weight: 600; }}
                .info-value {{ color: #111827; font-weight: bold; }}
                .journey {{ background: #fef3c7; padding: 20px; border-radius: 10px; margin: 20px 0; 
                          border-left: 4px solid #f59e0b; }}
                .qr-section {{ text-align: center; padding: 20px; background: #f9fafb; }}
                .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; }}
                .status {{ display: inline-block; padding: 5px 15px; border-radius: 20px; 
                         background: #10b981; color: white; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="ticket">
                <div class="header">
                    <h1>🚂 Bangladesh Railway</h1>
                    <p>E-Ticket Confirmation</p>
                </div>
                <div class="content">
                    <div class="info-row">
                        <span class="info-label">Booking ID:</span>
                        <span class="info-value">{booking_data.get('booking_id', 'N/A')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Passenger Name:</span>
                        <span class="info-value">{booking_data.get('name', 'N/A')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Phone:</span>
                        <span class="info-value">{booking_data.get('phone', 'N/A')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Status:</span>
                        <span class="status">{booking_data.get('status', 'CONFIRMED')}</span>
                    </div>
                    
                    <div class="journey">
                        <h3 style="margin-top: 0; color: #92400e;">🗓️ Journey Details</h3>
                        <div class="info-row" style="border: none;">
                            <span class="info-label">Train:</span>
                            <span class="info-value">{booking_data.get('train_id', 'N/A')}</span>
                        </div>
                        <div class="info-row" style="border: none;">
                            <span class="info-label">Date:</span>
                            <span class="info-value">{booking_data.get('date', 'N/A')}</span>
                        </div>
                        <div class="info-row" style="border: none;">
                            <span class="info-label">Coach:</span>
                            <span class="info-value">{booking_data.get('coach', 'N/A')}</span>
                        </div>
                        <div class="info-row" style="border: none;">
                            <span class="info-label">Seat:</span>
                            <span class="info-value">{booking_data.get('seat', 'N/A')}</span>
                        </div>
                        <div class="info-row" style="border: none;">
                            <span class="info-label">Price:</span>
                            <span class="info-value">৳{booking_data.get('price', 0)}</span>
                        </div>
                    </div>
                    
                    <div class="qr-section">
                        <p style="color: #6b7280; margin: 0 0 10px 0;">Scan QR code at station</p>
                        <p style="color: #9ca3af; font-size: 12px;">QR Code: {booking_data.get('booking_id', 'N/A')}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>Thank you for choosing Bangladesh Railway!</p>
                    <p style="font-size: 12px; margin-top: 10px;">
                        Please arrive 30 minutes before departure time.<br>
                        Keep this ticket handy during your journey.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def send_ticket_email(self, recipient_email, booking_data, callback=None):
        """Send ticket via email with QR code"""
        try:
            if not self.sender_email or not self.sender_password:
                raise Exception("Email not configured. Please set up email in settings.")

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🎫 Train Ticket - Booking #{booking_data.get('booking_id', 'N/A')}"
            msg['From'] = self.sender_email
            msg['To'] = recipient_email

            # Create HTML content
            html_content = self.create_ticket_html(booking_data)
            msg.attach(MIMEText(html_content, 'html'))

            # Generate and attach QR code
            qr_buffer = self.generate_qr_code(booking_data.get('booking_id', 'N/A'))
            qr_attachment = MIMEApplication(qr_buffer.read(), _subtype="png")
            qr_attachment.add_header('Content-Disposition', 'attachment',
                                    filename=f"ticket_qr_{booking_data.get('booking_id', 'N/A')}.png")
            msg.attach(qr_attachment)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            if callback:
                callback(True, "Ticket sent successfully!")
            return True, "Ticket sent successfully!"

        except Exception as e:
            error_msg = str(e)
            if callback:
                callback(False, error_msg)
            return False, error_msg


class ModernLoginWindow:
    """Ultra-modern animated login/registration with Gmail verification"""
    def __init__(self, parent, api, callback):
        self.window = tk.Toplevel(parent)
        self.window.title('🚂 Bangladesh Railway - Secure Access')
        self.window.geometry('900x700')
        self.window.configure(bg='#0a0e27')
        self.window.resizable(False, False)
        self.api = api
        self.callback = callback

        # Modern color scheme
        self.bg_dark = '#0a0e27'
        self.bg_card = '#1a1f3a'
        self.accent_primary = '#6366f1'  # Indigo
        self.accent_secondary = '#8b5cf6'  # Purple
        self.accent_success = '#10b981'  # Green
        self.accent_danger = '#ef4444'  # Red
        self.text_primary = '#f1f5f9'
        self.text_secondary = '#94a3b8'

        self.current_step = 'choice'  # choice, register, verify, login

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 450
        y = (self.window.winfo_screenheight() // 2) - 350
        self.window.geometry(f'900x700+{x}+{y}')

        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        # Animated header
        header = tk.Frame(self.window, bg=self.bg_card, height=120)
        header.pack(fill='x')
        header.pack_propagate(False)

        # Logo and title
        logo_frame = tk.Frame(header, bg=self.bg_card)
        logo_frame.pack(expand=True)

        tk.Label(logo_frame, text='🚂', bg=self.bg_card, fg=self.accent_primary,
                font=('Segoe UI', 48)).pack(side='left', padx=10)

        title_frame = tk.Frame(logo_frame, bg=self.bg_card)
        title_frame.pack(side='left')
        tk.Label(title_frame, text='Bangladesh Railway', bg=self.bg_card, fg=self.text_primary,
                font=('Segoe UI Bold', 24)).pack(anchor='w')
        tk.Label(title_frame, text='Secure Authentication Portal', bg=self.bg_card, fg=self.text_secondary,
                font=('Segoe UI', 11)).pack(anchor='w')

        # Main content area
        self.content_frame = tk.Frame(self.window, bg=self.bg_dark)
        self.content_frame.pack(fill='both', expand=True, padx=40, pady=30)

        self._show_choice()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_choice(self):
        """Show initial choice: Register or Login"""
        self._clear_content()
        self.current_step = 'choice'

        # Welcome message
        tk.Label(self.content_frame, text='Welcome! 👋', bg=self.bg_dark, fg=self.text_primary,
                font=('Segoe UI Bold', 28)).pack(pady=(20, 10))
        tk.Label(self.content_frame, text='Choose an option to continue', bg=self.bg_dark, fg=self.text_secondary,
                font=('Segoe UI', 13)).pack(pady=(0, 40))

        # Choice cards
        cards_frame = tk.Frame(self.content_frame, bg=self.bg_dark)
        cards_frame.pack(expand=True)

        # Register card
        reg_card = tk.Frame(cards_frame, bg=self.bg_card, relief='flat', bd=0)
        reg_card.pack(side='left', padx=20, ipadx=40, ipady=40)

        tk.Label(reg_card, text='📝', bg=self.bg_card, font=('Segoe UI', 60)).pack(pady=(20, 15))
        tk.Label(reg_card, text='New User?', bg=self.bg_card, fg=self.text_primary,
                font=('Segoe UI Bold', 18)).pack()
        tk.Label(reg_card, text='Create your account with', bg=self.bg_card, fg=self.text_secondary,
                font=('Segoe UI', 10)).pack(pady=(5, 2))
        tk.Label(reg_card, text='Gmail verification', bg=self.bg_card, fg=self.text_secondary,
                font=('Segoe UI', 10)).pack(pady=(0, 20))

        reg_btn = tk.Button(reg_card, text='Register Now', command=self._show_register,
                           bg=self.accent_primary, fg='white', font=('Segoe UI Bold', 13),
                           padx=40, pady=12, relief='flat', cursor='hand2', borderwidth=0)
        reg_btn.pack(pady=(10, 20))
        reg_btn.bind('<Enter>', lambda e: reg_btn.config(bg=self.accent_secondary))
        reg_btn.bind('<Leave>', lambda e: reg_btn.config(bg=self.accent_primary))

        # Login card
        login_card = tk.Frame(cards_frame, bg=self.bg_card, relief='flat', bd=0)
        login_card.pack(side='left', padx=20, ipadx=40, ipady=40)

        tk.Label(login_card, text='🔐', bg=self.bg_card, font=('Segoe UI', 60)).pack(pady=(20, 15))
        tk.Label(login_card, text='Have an Account?', bg=self.bg_card, fg=self.text_primary,
                font=('Segoe UI Bold', 18)).pack()
        tk.Label(login_card, text='Login with your', bg=self.bg_card, fg=self.text_secondary,
                font=('Segoe UI', 10)).pack(pady=(5, 2))
        tk.Label(login_card, text='verified Gmail', bg=self.bg_card, fg=self.text_secondary,
                font=('Segoe UI', 10)).pack(pady=(0, 20))

        login_btn = tk.Button(login_card, text='Login Now', command=self._show_login,
                             bg=self.accent_success, fg='white', font=('Segoe UI Bold', 13),
                             padx=40, pady=12, relief='flat', cursor='hand2', borderwidth=0)
        login_btn.pack(pady=(10, 20))
        login_btn.bind('<Enter>', lambda e: login_btn.config(bg='#059669'))
        login_btn.bind('<Leave>', lambda e: login_btn.config(bg=self.accent_success))

    def _show_register(self):
        """Show registration form"""
        self._clear_content()
        self.current_step = 'register'

        # Back button
        back_btn = tk.Button(self.content_frame, text='← Back', command=self._show_choice,
                            bg=self.bg_dark, fg=self.text_secondary, font=('Segoe UI', 10),
                            relief='flat', cursor='hand2', borderwidth=0)
        back_btn.pack(anchor='w', pady=(0, 10))

        # Title
        tk.Label(self.content_frame, text='Create Your Account', bg=self.bg_dark, fg=self.text_primary,
                font=('Segoe UI Bold', 22)).pack(pady=(10, 5))
        tk.Label(self.content_frame, text='We\'ll send a verification code to your Gmail', bg=self.bg_dark,
                fg=self.text_secondary, font=('Segoe UI', 11)).pack(pady=(0, 30))

        # Form card
        form_card = tk.Frame(self.content_frame, bg=self.bg_card)
        form_card.pack(ipadx=40, ipady=30)

        self.reg_entries = {}
        fields = [
            ('📛 Full Name', 'name', False, 'e.g., John Doe'),
            ('📧 Gmail Address', 'email', False, 'your.email@gmail.com'),
            ('🔒 Password', 'password', True, 'Min 6 characters'),
            ('📱 Phone Number', 'phone', False, '01XXXXXXXXX')
        ]

        for emoji_label, key, is_pass, placeholder in fields:
            container = tk.Frame(form_card, bg=self.bg_card)
            container.pack(fill='x', pady=8)

            tk.Label(container, text=emoji_label, bg=self.bg_card, fg=self.text_primary,
                    font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))

            entry = tk.Entry(container, width=40, bg='#2a2f4a', fg=self.text_primary,
                           font=('Segoe UI', 11), relief='flat', bd=0,
                           insertbackground=self.accent_primary)
            if is_pass:
                entry.config(show='●')
            entry.pack(ipady=10)
            entry.insert(0, placeholder)
            entry.bind('<FocusIn>', lambda e, ent=entry, ph=placeholder: ent.delete(0, 'end') if ent.get() == ph else None)
            entry.bind('<FocusOut>', lambda e, ent=entry, ph=placeholder: ent.insert(0, ph) if not ent.get() else None)

            self.reg_entries[key] = entry

        # Register button
        reg_btn = tk.Button(form_card, text='📝 Register & Send Code', command=self._do_register,
                           bg=self.accent_primary, fg='white', font=('Segoe UI Bold', 13),
                           padx=60, pady=15, relief='flat', cursor='hand2', borderwidth=0)
        reg_btn.pack(pady=(20, 0))
        reg_btn.bind('<Enter>', lambda e: reg_btn.config(bg=self.accent_secondary))
        reg_btn.bind('<Leave>', lambda e: reg_btn.config(bg=self.accent_primary))

    def _do_register(self):
        name = self.reg_entries['name'].get().strip()
        email = self.reg_entries['email'].get().strip()
        password = self.reg_entries['password'].get().strip()
        phone = self.reg_entries['phone'].get().strip()

        # Validation
        if not all([name, email, password, phone]) or 'e.g.' in name or '@gmail.com' in email and email == 'your.email@gmail.com':
            messagebox.showerror('❌ Error', 'Please fill all fields correctly')
            return

        if '@gmail.com' not in email.lower():
            messagebox.showerror('❌ Error', 'Please use a valid Gmail address')
            return

        if len(password) < 6:
            messagebox.showerror('❌ Error', 'Password must be at least 6 characters')
            return

        # Store for verification
        self.temp_email = email

        # Register
        success, msg = self.api.register_email(email, password, phone, name)
        if success:
            messagebox.showinfo('✅ Success', f'Verification code sent to {email}!\nCheck your inbox.')
            self._show_verify()
        else:
            messagebox.showerror('❌ Registration Failed', msg)

    def _show_verify(self):
        """Show email verification form"""
        self._clear_content()
        self.current_step = 'verify'

        # Title
        tk.Label(self.content_frame, text='📬 Verify Your Email', bg=self.bg_dark, fg=self.text_primary,
                font=('Segoe UI Bold', 22)).pack(pady=(30, 10))
        tk.Label(self.content_frame, text=f'Enter the 6-digit code sent to', bg=self.bg_dark,
                fg=self.text_secondary, font=('Segoe UI', 11)).pack()
        tk.Label(self.content_frame, text=self.temp_email, bg=self.bg_dark,
                fg=self.accent_primary, font=('Segoe UI Bold', 12)).pack(pady=(5, 40))

        # Verification card
        verify_card = tk.Frame(self.content_frame, bg=self.bg_card)
        verify_card.pack(ipadx=60, ipady=40)

        tk.Label(verify_card, text='Enter Verification Code', bg=self.bg_card, fg=self.text_primary,
                font=('Segoe UI', 12)).pack(pady=(0, 15))

        self.verify_code = tk.Entry(verify_card, width=20, bg='#2a2f4a', fg=self.text_primary,
                                    font=('Segoe UI Bold', 20), relief='flat', bd=0, justify='center',
                                    insertbackground=self.accent_primary)
        self.verify_code.pack(ipady=12)

        verify_btn = tk.Button(verify_card, text='✅ Verify Email', command=self._do_verify,
                              bg=self.accent_success, fg='white', font=('Segoe UI Bold', 13),
                              padx=50, pady=15, relief='flat', cursor='hand2', borderwidth=0)
        verify_btn.pack(pady=(25, 10))
        verify_btn.bind('<Enter>', lambda e: verify_btn.config(bg='#059669'))
        verify_btn.bind('<Leave>', lambda e: verify_btn.config(bg=self.accent_success))

        # Resend link
        resend_frame = tk.Frame(verify_card, bg=self.bg_card)
        resend_frame.pack(pady=(15, 0))
        tk.Label(resend_frame, text="Didn't receive code? ", bg=self.bg_card, fg=self.text_secondary,
                font=('Segoe UI', 10)).pack(side='left')
        resend_btn = tk.Label(resend_frame, text='Resend', bg=self.bg_card, fg=self.accent_primary,
                             font=('Segoe UI Bold', 10), cursor='hand2')
        resend_btn.pack(side='left')
        resend_btn.bind('<Button-1>', lambda e: self._do_register())

    def _do_verify(self):
        code = self.verify_code.get().strip()
        if not code:
            messagebox.showerror('❌ Error', 'Please enter the verification code')
            return

        success, msg = self.api.verify_email(self.temp_email, code)
        if success:
            messagebox.showinfo('✅ Verified!', 'Email verified successfully!\nYou can now login.')
            self._show_login()
        else:
            messagebox.showerror('❌ Verification Failed', msg)

    def _show_login(self):
        """Show login form with one-time code"""
        self._clear_content()
        self.current_step = 'login'

        # Back button
        back_btn = tk.Button(self.content_frame, text='← Back', command=self._show_choice,
                            bg=self.bg_dark, fg=self.text_secondary, font=('Segoe UI', 10),
                            relief='flat', cursor='hand2', borderwidth=0)
        back_btn.pack(anchor='w', pady=(0, 10))

        # Title
        tk.Label(self.content_frame, text='Welcome Back! 👋', bg=self.bg_dark, fg=self.text_primary,
                font=('Segoe UI Bold', 22)).pack(pady=(10, 5))
        tk.Label(self.content_frame, text='Login with your verified Gmail', bg=self.bg_dark,
                fg=self.text_secondary, font=('Segoe UI', 11)).pack(pady=(0, 30))

        # Login card
        login_card = tk.Frame(self.content_frame, bg=self.bg_card)
        login_card.pack(ipadx=40, ipady=30)

        # Email
        tk.Label(login_card, text='📧 Gmail Address', bg=self.bg_card, fg=self.text_primary,
                font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        self.login_email = tk.Entry(login_card, width=40, bg='#2a2f4a', fg=self.text_primary,
                                    font=('Segoe UI', 11), relief='flat', bd=0,
                                    insertbackground=self.accent_primary)
        self.login_email.pack(ipady=10, pady=(0, 20))

        # One-time code section
        code_container = tk.Frame(login_card, bg='#2a2f4a')
        code_container.pack(fill='x', pady=(0, 20))

        tk.Label(code_container, text='🔐 One-Time Login Code', bg='#2a2f4a', fg=self.text_primary,
                font=('Segoe UI Semibold', 11)).pack(anchor='w', padx=15, pady=(15, 5))
        tk.Label(code_container, text='No password needed! We\'ll send a code to your email',
                bg='#2a2f4a', fg=self.text_secondary, font=('Segoe UI', 9)).pack(anchor='w', padx=15)

        code_input_frame = tk.Frame(code_container, bg='#2a2f4a')
        code_input_frame.pack(fill='x', padx=15, pady=(10, 15))

        self.login_code = tk.Entry(code_input_frame, width=15, bg='#1a1f3a', fg=self.text_primary,
                                   font=('Segoe UI', 11), relief='flat', bd=0,
                                   insertbackground=self.accent_primary)
        self.login_code.pack(side='left', ipady=8, padx=(0, 10))

        send_code_btn = tk.Button(code_input_frame, text='📨 Send Code', command=self._send_code,
                                  bg=self.accent_primary, fg='white', font=('Segoe UI', 10),
                                  padx=20, pady=8, relief='flat', cursor='hand2', borderwidth=0)
        send_code_btn.pack(side='left')
        send_code_btn.bind('<Enter>', lambda e: send_code_btn.config(bg=self.accent_secondary))
        send_code_btn.bind('<Leave>', lambda e: send_code_btn.config(bg=self.accent_primary))

        # Login button
        login_btn = tk.Button(login_card, text='🚀 Login', command=self._do_login,
                             bg=self.accent_success, fg='white', font=('Segoe UI Bold', 13),
                             padx=60, pady=15, relief='flat', cursor='hand2', borderwidth=0)
        login_btn.pack(pady=(10, 0))
        login_btn.bind('<Enter>', lambda e: login_btn.config(bg='#059669'))
        login_btn.bind('<Leave>', lambda e: login_btn.config(bg=self.accent_success))

    def _send_code(self):
        email = self.login_email.get().strip()
        if not email:
            messagebox.showerror('❌ Error', 'Please enter your Gmail address')
            return

        success, msg, code = self.api.send_login_code(email)
        if success:
            if code:
                self.login_code.delete(0, 'end')
                self.login_code.insert(0, code)
                messagebox.showinfo('📨 Code Generated', f'{msg}\n\nYour code: {code}\n(Valid for 10 minutes)')
            else:
                messagebox.showinfo('📨 Code Sent', msg)
        else:
            messagebox.showerror('❌ Error', msg)

    def _do_login(self):
        email = self.login_email.get().strip()
        code = self.login_code.get().strip()

        if not email or not code:
            messagebox.showerror('❌ Error', 'Please enter both email and code')
            return

        success, result = self.api.login_with_code(email, code)
        if success:
            messagebox.showinfo('✅ Success', f'Welcome back, {result["full_name"]}!')
            self.window.destroy()
            self.callback(result)
        else:
            messagebox.showerror('❌ Login Failed', result)


class EnhancedTrainBookingApp:

    def __init__(self, root, api):
        self.root = root
        self.api = api
        self.current_user = None
        self.email_service = EmailService()

        self.root.title('🚂 Bangladesh Railway V2 - Modern Booking System')
        self.root.geometry('1500x850')
        self.root.minsize(1300, 750)

        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # Ultra-modern dark theme with neon accents
        self.bg = '#0a0e27'            # deep space blue background
        self.panel_bg = '#1a1f3a'      # elevated panel
        self.surface = '#2a2f4a'       # input surface
        self.accent = '#6366f1'        # vibrant indigo
        self.accent_hover = '#8b5cf6'  # purple hover
        self.good = '#10b981'          # emerald success
        self.bad = '#ef4444'           # red danger
        self.warning = '#f59e0b'       # amber warning
        self.info = '#06b6d4'          # cyan info
        self.window_color = '#7c3aed'  # violet purple
        self.text_primary = '#f1f5f9'  # white text
        self.text_secondary = '#94a3b8' # gray text

        self.root.configure(bg=self.bg)

        # Enhanced fonts
        self.font_tiny = ('Segoe UI', 8)
        self.font_small = ('Segoe UI', 9)
        self.font_regular = ('Segoe UI', 10)
        self.font_bold = ('Segoe UI Semibold', 10)
        self.font_title = ('Segoe UI Bold', 18)
        self.font_heading = ('Segoe UI Semibold', 14)

        self._show_login()

    def _show_login(self):
        ModernLoginWindow(self.root, self.api, self._on_login_success)

    def _on_login_success(self, user_info):
        self.current_user = user_info
        self._build_main_ui()

    def _build_main_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self._setup_styles()
        self._build_header()
        self._build_main_content()
        self._build_status_bar()

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass

        # Base colors (light theme)
        bg = self.bg
        panel = self.panel_bg
        surf = self.surface
        accent = self.accent
        accent_hover = self.accent_hover
        text = '#1f2937'   # dark text
        muted = '#64748b'  # muted gray

        # Notebook
        style.configure('Premium.TNotebook', background=bg, borderwidth=0)
        style.configure('Premium.TNotebook.Tab',
                        background=panel,
                        foreground=muted,
                        padding=[18, 10],
                        font=('Segoe UI Semibold', 10))
        style.map('Premium.TNotebook.Tab',
                  background=[('selected', surf), ('active', '#e5eaf3')],
                  foreground=[('selected', text), ('active', text)])

        # Buttons
        style.configure('Premium.TButton',
                        background=accent,
                        foreground='#ffffff',
                        padding=8,
                        font=('Segoe UI Semibold', 10))
        style.map('Premium.TButton',
                  background=[('active', accent_hover)],
                  foreground=[('disabled', '#9aa5b1')])

        # Combobox
        style.configure('Premium.TCombobox',
                        fieldbackground=panel,
                        background=panel,
                        foreground=text,
                        arrowcolor=accent)

        # Apply notebook style instance
        self.notebook = ttk.Notebook(self.root, style='Premium.TNotebook')

        # After creating comboboxes, apply style
        if hasattr(self, 'single_train'):
            self.single_train.configure(style='Premium.TCombobox')
        # Roundtrip
        if hasattr(self, 'rt_train_onward'):
            self.rt_train_onward.configure(style='Premium.TCombobox')
        if hasattr(self, 'rt_train_return'):
            self.rt_train_return.configure(style='Premium.TCombobox')
        # Multi-booking
        if hasattr(self, 'multi_train'):
            self.multi_train.configure(style='Premium.TCombobox')
        # Compare
        if hasattr(self, 'compare_train1'):
            self.compare_train1.configure(style='Premium.TCombobox')
        if hasattr(self, 'compare_train2'):
            self.compare_train2.configure(style='Premium.TCombobox')

    def _build_header(self):
        header = tk.Frame(self.root, bg=self.panel_bg, height=90)
        header.pack(fill='x', padx=0, pady=0)
        header.pack_propagate(False)

        # Left side - animated branding
        left_frame = tk.Frame(header, bg=self.panel_bg)
        left_frame.pack(side='left', padx=25, pady=15)

        tk.Label(left_frame, text='🚂', bg=self.panel_bg, fg=self.accent,
                font=('Segoe UI', 40)).pack(side='left', padx=(0, 15))

        branding = tk.Frame(left_frame, bg=self.panel_bg)
        branding.pack(side='left')
        tk.Label(branding, text='Bangladesh Railway', bg=self.panel_bg, fg=self.text_primary,
                font=('Segoe UI Bold', 20)).pack(anchor='w')
        tk.Label(branding, text='Ultimate Booking Experience • AI Powered', bg=self.panel_bg, fg=self.text_secondary,
                font=('Segoe UI', 9)).pack(anchor='w')

        # Center - Quick stats
        stats_frame = tk.Frame(header, bg=self.panel_bg)
        stats_frame.pack(side='left', padx=40)

        try:
            bookings = self.api.get_booking_history()
            booking_count = len(bookings)
        except:
            booking_count = 0

        stat_items = [
            ('📊', str(booking_count), 'Bookings'),
            ('🎫', 'Active', 'Status'),
            ('⭐', '5.0', 'Rating')
        ]

        for emoji, value, label in stat_items:
            stat_card = tk.Frame(stats_frame, bg=self.surface)
            stat_card.pack(side='left', padx=8, ipadx=12, ipady=6)
            tk.Label(stat_card, text=emoji, bg=self.surface, font=('Segoe UI', 16)).pack(side='left', padx=(0, 8))
            info = tk.Frame(stat_card, bg=self.surface)
            info.pack(side='left')
            tk.Label(info, text=value, bg=self.surface, fg=self.text_primary,
                    font=('Segoe UI Bold', 11)).pack(anchor='w')
            tk.Label(info, text=label, bg=self.surface, fg=self.text_secondary,
                    font=('Segoe UI', 8)).pack(anchor='w')

        # Right side - user profile & actions
        right_frame = tk.Frame(header, bg=self.panel_bg)
        right_frame.pack(side='right', padx=25, pady=15)

        # Notification bell
        notif_btn = tk.Button(right_frame, text='🔔', bg=self.surface, fg=self.text_primary,
                             font=('Segoe UI', 18), relief='flat', cursor='hand2',
                             padx=10, pady=5, borderwidth=0)
        notif_btn.pack(side='right', padx=(10, 0))
        notif_btn.bind('<Enter>', lambda e: notif_btn.config(bg=self.accent))
        notif_btn.bind('<Leave>', lambda e: notif_btn.config(bg=self.surface))

        # Settings
        settings_btn = tk.Button(right_frame, text='⚙️', bg=self.surface, fg=self.text_primary,
                                font=('Segoe UI', 18), relief='flat', cursor='hand2',
                                padx=10, pady=5, borderwidth=0,
                                command=lambda: self.notebook.select(9))
        settings_btn.pack(side='right', padx=(10, 0))
        settings_btn.bind('<Enter>', lambda e: settings_btn.config(bg=self.accent))
        settings_btn.bind('<Leave>', lambda e: settings_btn.config(bg=self.surface))

        # Logout button
        logout_btn = tk.Button(right_frame, text='🚪', bg=self.bad, fg='white',
                              font=('Segoe UI', 16), relief='flat', cursor='hand2',
                              padx=10, pady=5, borderwidth=0, command=self._logout)
        logout_btn.pack(side='right', padx=(10, 0))
        logout_btn.bind('<Enter>', lambda e: logout_btn.config(bg='#dc2626'))
        logout_btn.bind('<Leave>', lambda e: logout_btn.config(bg=self.bad))

        # User profile card
        profile_card = tk.Frame(right_frame, bg=self.surface, relief='flat')
        profile_card.pack(side='right', padx=5)

        tk.Label(profile_card, text='👤', bg=self.surface, fg=self.accent,
                font=('Segoe UI', 24)).pack(side='left', padx=(12, 8))

        user_info = tk.Frame(profile_card, bg=self.surface)
        user_info.pack(side='left', padx=(0, 12), pady=8)

        tk.Label(user_info, text=f'{self.current_user["full_name"]}',
                bg=self.surface, fg=self.text_primary,
                font=('Segoe UI Bold', 11)).pack(anchor='w')
        tk.Label(user_info, text=f'{self.current_user.get("email", "User")}',
                bg=self.surface, fg=self.text_secondary,
                font=('Segoe UI', 8)).pack(anchor='w')

    def _build_main_content(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        self.tab_dashboard = tk.Frame(self.notebook, bg=self.bg)
        self.tab_booking = tk.Frame(self.notebook, bg=self.bg)
        self.tab_roundtrip = tk.Frame(self.notebook, bg=self.bg)
        self.tab_history = tk.Frame(self.notebook, bg=self.bg)
        self.tab_refunds = tk.Frame(self.notebook, bg=self.bg)
        self.tab_schedules = tk.Frame(self.notebook, bg=self.bg)
        self.tab_reports = tk.Frame(self.notebook, bg=self.bg)
        self.tab_compare = tk.Frame(self.notebook, bg=self.bg)
        self.tab_multibooking = tk.Frame(self.notebook, bg=self.bg)
        self.tab_settings = tk.Frame(self.notebook, bg=self.bg)

        self.notebook.add(self.tab_dashboard, text='🏠 Dashboard')
        self.notebook.add(self.tab_booking, text='📋 Quick Booking')
        self.notebook.add(self.tab_roundtrip, text='🔄 Round Trip')
        self.notebook.add(self.tab_multibooking, text='🎫 Multi-Booking')
        self.notebook.add(self.tab_history, text='📜 My Bookings')
        self.notebook.add(self.tab_refunds, text='💰 Refunds')
        self.notebook.add(self.tab_schedules, text='🕐 Schedules')
        self.notebook.add(self.tab_reports, text='📊 Reports')
        self.notebook.add(self.tab_compare, text='⚖️ Compare Trains')
        self.notebook.add(self.tab_settings, text='⚙️ Settings')

        self._build_dashboard_tab()
        self._build_booking_tab()
        self._build_roundtrip_tab()
        self._build_multibooking_tab()
        self._build_history_tab()
        self._build_refunds_tab()
        self._build_schedules_tab()
        self._build_reports_tab()
        self._build_compare_tab()
        self._build_settings_tab()

    def _load_trains(self):
        """Load available trains from API"""
        try:
            trains = self.api.get_trains()
            return trains if trains else []
        except:
            # Fallback data if API fails
            return [
                {"id": "T001", "name": "Sundarban Express", "route": "Dhaka-Khulna", "base_price": 550},
                {"id": "T002", "name": "Silk City Express", "route": "Dhaka-Rajshahi", "base_price": 500}
            ]

    def _refresh_trains(self):
        """Refresh train list from API"""
        self.available_trains = self._load_trains()
        train_options = [f"{t['id']} - {t['name']} ({t['route']}) - ৳{t['base_price']}"
                        for t in self.available_trains]

        # Update single booking dropdown
        if hasattr(self, 'single_train'):
            self.single_train['values'] = train_options
            if train_options:
                self.single_train.set(train_options[0])

        # Update round trip dropdowns
        if hasattr(self, 'rt_train_onward'):
            short_options = [f"{t['id']} - {t['name']}" for t in self.available_trains]
            self.rt_train_onward['values'] = short_options
            self.rt_train_return['values'] = short_options
            if short_options:
                self.rt_train_onward.set(short_options[0])
                self.rt_train_return.set(short_options[0])

        # Update multi-booking dropdown
        if hasattr(self, 'multi_train'):
            self.multi_train['values'] = train_options
            if train_options:
                self.multi_train.set(train_options[0])

        # Update compare train dropdowns
        if hasattr(self, 'compare_train1'):
            self.compare_train1['values'] = train_options
            if train_options:
                self.compare_train1.set(train_options[0])
        if hasattr(self, 'compare_train2'):
            self.compare_train2['values'] = train_options
            if train_options and len(train_options) > 1:
                self.compare_train2.set(train_options[1])

        messagebox.showinfo('Refreshed', f'Loaded {len(self.available_trains)} trains')

    def _build_booking_tab(self):
        main = tk.Frame(self.tab_booking, bg=self.bg)
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Modern header with gradient effect
        header_frame = tk.Frame(main, bg=self.panel_bg, height=100)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)

        header_content = tk.Frame(header_frame, bg=self.panel_bg)
        header_content.pack(expand=True, padx=30)

        tk.Label(header_content, text='🎫', bg=self.panel_bg, fg=self.accent,
                font=('Segoe UI', 42)).pack(side='left', padx=(0, 15))

        title_frame = tk.Frame(header_content, bg=self.panel_bg)
        title_frame.pack(side='left')
        tk.Label(title_frame, text='Quick Ticket Booking', bg=self.panel_bg, fg=self.text_primary,
                font=('Segoe UI Bold', 22)).pack(anchor='w')
        tk.Label(title_frame, text='Select your seat from the interactive coach layout • Real-time availability',
                bg=self.panel_bg, fg=self.text_secondary, font=('Segoe UI', 11)).pack(anchor='w')

        # Create two-column layout
        content = tk.Frame(main, bg=self.bg)
        content.pack(fill='both', expand=True)

        # Left side: Form with modern card design
        left_panel = tk.Frame(content, bg=self.panel_bg, relief='flat')
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))

        tk.Label(left_panel, text='📝 Booking Information', bg=self.panel_bg, fg=self.text_primary,
                font=('Segoe UI Bold', 15)).pack(pady=20, padx=20, anchor='w')

        form = tk.Frame(left_panel, bg=self.panel_bg)
        form.pack(padx=25, pady=10, fill='both', expand=True)

        # Train selection with dropdown
        train_label_frame = tk.Frame(form, bg=self.panel_bg)
        train_label_frame.grid(row=0, column=0, sticky='w', pady=8, padx=5)

        tk.Label(train_label_frame, text='Select Train:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(side='left')

        refresh_btn = tk.Button(train_label_frame, text='🔄', command=self._refresh_trains,
                               bg=self.surface, fg='#f59e0b', font=('Segoe UI', 8),
                               padx=5, pady=2, relief='flat', cursor='hand2')
        refresh_btn.pack(side='left', padx=(5, 0))
        ToolTip(refresh_btn, 'Refresh train list')

        # Load trains from API
        self.available_trains = self._load_trains()
        train_options = [f"{t['id']} - {t['name']} ({t['route']}) - ৳{t['base_price']}"
                        for t in self.available_trains]

        self.single_train_var = tk.StringVar()
        self.single_train = ttk.Combobox(form, textvariable=self.single_train_var,
                                        values=train_options, width=45,
                                        font=self.font_regular, state='readonly')
        self.single_train.grid(row=0, column=1, pady=8, padx=5, sticky='ew')
        if train_options:
            self.single_train.set(train_options[0])  # Set default
        # refresh seat map on selection changes
        self.single_train.bind('<<ComboboxSelected>>', lambda e: self._draw_seat_map())

        # Date selection
        tk.Label(form, text='Date (YYYY-MM-DD):', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=1, column=0, sticky='w', pady=8, padx=5)
        self.single_date = tk.Entry(form, bg=self.surface, fg='#e2e8f0', width=20,
                                    font=self.font_regular, relief='flat', bd=5)
        self.single_date.grid(row=1, column=1, pady=8, padx=5, sticky='ew')
        # Set default date to tomorrow
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        self.single_date.insert(0, tomorrow)
        self.single_date.bind('<FocusOut>', lambda e: self._draw_seat_map())

        # Coach selection
        tk.Label(form, text='Coach:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=2, column=0, sticky='w', pady=8, padx=5)
        self.single_coach = tk.Spinbox(form, from_=1, to=10, bg=self.surface, fg='#e2e8f0',
                                       width=18, font=self.font_regular, relief='flat', bd=5,
                                       command=self._draw_seat_map)
        self.single_coach.grid(row=2, column=1, pady=8, padx=5, sticky='ew')

        # Seat selection
        tk.Label(form, text='Seat Number:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=3, column=0, sticky='w', pady=8, padx=5)
        self.single_seat = tk.Spinbox(form, from_=1, to=60, bg=self.surface, fg='#e2e8f0',
                                      width=18, font=self.font_regular, relief='flat', bd=5)
        self.single_seat.grid(row=3, column=1, pady=8, padx=5, sticky='ew')

        # Passenger info
        tk.Label(form, text='Passenger Name:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=4, column=0, sticky='w', pady=8, padx=5)
        self.single_name = tk.Entry(form, bg=self.surface, fg='#e2e8f0', width=20,
                                    font=self.font_regular, relief='flat', bd=5)
        self.single_name.grid(row=4, column=1, pady=8, padx=5, sticky='ew')
        self.single_name.insert(0, self.current_user.get('full_name', ''))

        tk.Label(form, text='Phone:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=5, column=0, sticky='w', pady=8, padx=5)
        self.single_phone = tk.Entry(form, bg=self.surface, fg='#e2e8f0', width=20,
                                     font=self.font_regular, relief='flat', bd=5)
        self.single_phone.grid(row=5, column=1, pady=8, padx=5, sticky='ew')
        self.single_phone.insert(0, self.current_user.get('phone', ''))

        form.columnconfigure(1, weight=1)

        # Book button
        book_btn = tk.Button(left_panel, text='🎫 Book Ticket', command=self._book_single_ticket,
                            bg=self.accent, fg='#0f172a', font=('Segoe UI Semibold', 13),
                            padx=40, pady=12, relief='flat', cursor='hand2')
        book_btn.pack(pady=20)

        # Hover effects
        book_btn.bind('<Enter>', lambda e: book_btn.config(bg='#fbbf24'))
        book_btn.bind('<Leave>', lambda e: book_btn.config(bg=self.accent))

        # Right side: Seat map visualization
        right_panel = tk.Frame(content, bg=self.panel_bg, relief='ridge', bd=2)
        right_panel.pack(side='left', fill='both', expand=True)

        tk.Label(right_panel, text='💺 Seat Map', bg=self.panel_bg, fg='#e2e8f0',
                font=('Segoe UI Semibold', 12)).pack(pady=15)

        # Seat legend
        legend_frame = tk.Frame(right_panel, bg=self.panel_bg)
        legend_frame.pack(pady=10)

        tk.Label(legend_frame, text='🟩 Available', bg=self.panel_bg, fg='#10b981',
                font=self.font_small).pack(side='left', padx=10)
        tk.Label(legend_frame, text='🟥 Booked', bg=self.panel_bg, fg='#ef4444',
                font=self.font_small).pack(side='left', padx=10)
        tk.Label(legend_frame, text='🟦 Selected', bg=self.panel_bg, fg='#3b82f6',
                font=self.font_small).pack(side='left', padx=10)

        # Seat canvas
        seat_canvas_frame = tk.Frame(right_panel, bg=self.panel_bg)
        seat_canvas_frame.pack(padx=20, pady=10, fill='both', expand=True)

        self.seat_canvas = tk.Canvas(seat_canvas_frame, bg=self.surface, height=350,
                                     highlightthickness=0)
        self.seat_canvas.pack(fill='both', expand=True)

        # Draw initial seat map
        self._draw_seat_map()

        # Info label
        tk.Label(right_panel, text='Click on a seat to select it', bg=self.panel_bg, fg='#94a3b8',
                font=self.font_small).pack(pady=10)

    def _draw_seat_map(self):
        """Draw interactive seat map with train layout and availability"""
        self.seat_canvas.delete('all')

        # Try to resolve selected train/date/coach
        selected = self.single_train_var.get().strip() if hasattr(self, 'single_train_var') else ''
        train_id = selected.split(' - ')[0].strip() if selected else ''
        date = self.single_date.get().strip() if hasattr(self, 'single_date') else ''
        try:
            coach = int(self.single_coach.get()) if hasattr(self, 'single_coach') else 1
        except Exception:
            coach = 1

        booked_set = set()
        if train_id and date and coach:
            try:
                booked = self.api.get_seat_availability(train_id, date, coach)
                booked_set = set(booked)
            except Exception:
                booked_set = set()

        seat_size = 38
        gap = 10
        start_x = 40
        start_y = 50
        rows = 10
        cols_per_side = 2
        aisle_width = 60

        self.seat_buttons = {}

        # Draw train outline
        canvas_width = self.seat_canvas.winfo_width() if self.seat_canvas.winfo_width() > 1 else 450
        train_width = (cols_per_side * 2 * (seat_size + gap)) + aisle_width + 60
        train_height = rows * (seat_size + gap) + 60

        # Coach border (light)
        self.seat_canvas.create_rectangle(15, 15, train_width, train_height + 20,
                                          outline='#cbd5e1', width=2)

        # Coach label
        self.seat_canvas.create_text(train_width // 2, 30,
                                     text='🚃 COACH LAYOUT',
                                     fill=self.accent, font=('Segoe UI Bold', 12))

        # Draw aisle with better styling
        aisle_x = start_x + (cols_per_side * (seat_size + gap))
        self.seat_canvas.create_rectangle(aisle_x, start_y - 15,
                                         aisle_x + aisle_width,
                                         start_y + rows * (seat_size + gap) + 10,
                                         fill='#e2e8f0', outline='#cbd5e1', width=1)

        # Aisle markers
        for i in range(3):
            y_pos = start_y + (rows * (seat_size + gap) // 3) * i + 30
            self.seat_canvas.create_line(aisle_x + 10, y_pos,
                                        aisle_x + aisle_width - 10, y_pos,
                                        fill='#64748b', width=2, dash=(10, 5))

        self.seat_canvas.create_text(aisle_x + aisle_width/2, start_y - 25,
                                     text='← AISLE →', fill=self.text_secondary,
                                     font=('Segoe UI Semibold', 10))

        seat_num = 1
        for row in range(rows):
            for col in range(cols_per_side * 2):
                x = start_x + (col * (seat_size + gap))
                if col >= cols_per_side:
                    x += aisle_width

                y = start_y + (row * (seat_size + gap))

                is_booked = seat_num in booked_set
                color = '#ef4444' if is_booked else '#6366f1'  # red for booked, indigo for available
                text_color = '#ffffff'

                # Draw seat with shadow effect
                # Shadow
                self.seat_canvas.create_rectangle(x + 2, y + 2, x + seat_size + 2, y + seat_size + 2,
                                                  fill='#e5e7eb', outline='', tags=f'seat_{seat_num}')

                # Main seat
                rect = self.seat_canvas.create_rectangle(x, y, x + seat_size, y + seat_size,
                                                         fill=color, outline='#e2e8f0', width=2,
                                                         tags=f'seat_{seat_num}')

                # Number
                text = self.seat_canvas.create_text(x + seat_size/2, y + seat_size/2,
                                                    text=str(seat_num), fill=text_color,
                                                    font=('Segoe UI Bold', 11),
                                                    tags=f'seat_{seat_num}')

                # Window markers
                if col == 0 or col == (cols_per_side * 2 - 1):
                    window_x = x - 8 if col == 0 else x + seat_size + 3
                    self.seat_canvas.create_text(window_x, y + seat_size/2, text='🪟',
                                                 font=('Segoe UI', 10), tags=f'seat_{seat_num}')

                # Events
                if not is_booked:
                    self.seat_canvas.tag_bind(f'seat_{seat_num}', '<Button-1>',
                                              lambda e, s=seat_num: self._select_seat(s))
                    self.seat_canvas.tag_bind(f'seat_{seat_num}', '<Enter>',
                                              lambda e, s=seat_num: self._hover_seat(s, True))
                    self.seat_canvas.tag_bind(f'seat_{seat_num}', '<Leave>',
                                              lambda e, s=seat_num: self._hover_seat(s, False))

                self.seat_buttons[seat_num] = {'rect': rect, 'text': text, 'available': not is_booked}
                seat_num += 1

    def _show_booking_success_dialog(self, booking_id, train_id, date, coach, seat, name, phone):
        """Show custom success dialog with email delivery option"""
        dialog = tk.Toplevel(self.root)
        dialog.title('Booking Successful')
        dialog.geometry('500x400')
        dialog.configure(bg=self.panel_bg)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        # Success icon
        tk.Label(dialog, text='✅', bg=self.panel_bg, font=('Segoe UI', 60)).pack(pady=(30, 10))
        tk.Label(dialog, text='Booking Successful!', bg=self.panel_bg, fg='#10b981',
                font=('Segoe UI Bold', 20)).pack()

        # Booking details
        details_frame = tk.Frame(dialog, bg=self.surface, relief='flat')
        details_frame.pack(pady=20, padx=40, fill='x')

        details = [
            ('Booking ID:', booking_id),
            ('Train:', train_id),
            ('Date:', date),
            ('Coach:', str(coach)),
            ('Seat:', str(seat)),
            ('Passenger:', name)
        ]

        for i, (label, value) in enumerate(details):
            row = tk.Frame(details_frame, bg=self.surface)
            row.pack(fill='x', pady=5, padx=15)
            tk.Label(row, text=label, bg=self.surface, fg='#94a3b8',
                    font=self.font_regular).pack(side='left')
            tk.Label(row, text=value, bg=self.surface, fg='#e2e8f0',
                    font=('Segoe UI Semibold', 10)).pack(side='right')

        # Email delivery section
        if self.email_service.sender_email and self.email_service.sender_password:
            email_frame = tk.Frame(dialog, bg=self.panel_bg)
            email_frame.pack(pady=15)

            tk.Label(email_frame, text='📧 Email Delivery', bg=self.panel_bg, fg='#e2e8f0',
                    font=('Segoe UI Semibold', 11)).pack()

            email_entry = tk.Entry(email_frame, bg=self.surface, fg='#e2e8f0',
                                  font=self.font_regular, width=35, relief='flat', bd=5)
            email_entry.pack(pady=10, ipady=6)
            email_entry.insert(0, self.current_user.get('email', ''))

            def send_email():
                recipient = email_entry.get().strip()
                if not recipient:
                    messagebox.showerror('Error', 'Please enter email address')
                    return

                dialog.destroy()

                # Get booking details
                bookings = self.api.get_booking_history()
                booking = next((b for b in bookings if b['booking_id'] == booking_id), None)

                if booking:
                    booking_data = {
                        'booking_id': booking_id,
                        'name': name,
                        'phone': phone,
                        'status': booking['status'],
                        'train_id': train_id,
                        'date': date,
                        'coach': coach,
                        'seat': seat,
                        'price': booking.get('price', 500)
                    }

                    # Send in background
                    self._send_email_with_progress(recipient, booking_data)

            send_btn = tk.Button(email_frame, text='📨 Send Ticket to Email',
                               command=send_email, bg=self.accent, fg='#0f172a',
                               font=('Segoe UI Semibold', 10), padx=25, pady=10,
                               relief='flat', cursor='hand2')
            send_btn.pack(pady=5)
            send_btn.bind('<Enter>', lambda e: send_btn.config(bg=self.accent_hover))
            send_btn.bind('<Leave>', lambda e: send_btn.config(bg=self.accent))

            skip_btn = tk.Button(email_frame, text='Skip', command=dialog.destroy,
                               bg=self.surface, fg='#94a3b8',
                               font=self.font_small, padx=20, pady=6,
                               relief='flat', cursor='hand2')
            skip_btn.pack()
            skip_btn.bind('<Enter>', lambda e: skip_btn.config(bg='#475569'))
            skip_btn.bind('<Leave>', lambda e: skip_btn.config(bg=self.surface))
        else:
            close_btn = tk.Button(dialog, text='Close', command=dialog.destroy,
                                bg=self.accent, fg='#0f172a',
                                font=('Segoe UI Semibold', 10), padx=40, pady=10,
                                relief='flat', cursor='hand2')
            close_btn.pack(pady=20)
            close_btn.bind('<Enter>', lambda e: close_btn.config(bg=self.accent_hover))
            close_btn.bind('<Leave>', lambda e: close_btn.config(bg=self.accent))

        self._refresh_history()
        # Clear form
        self.single_train.delete(0, 'end')
        self.single_seat.delete(0, 'end')
        self.single_seat.insert(0, '1')
        self._draw_seat_map()

    def _send_email_with_progress(self, recipient, booking_data):
        """Send email with animated progress dialog"""
        loading = tk.Toplevel(self.root)
        loading.title('Sending Email')
        loading.geometry('400x150')
        loading.configure(bg=self.panel_bg)
        loading.resizable(False, False)
        loading.transient(self.root)

        # Center loading window
        loading.update_idletasks()
        x = (loading.winfo_screenwidth() // 2) - (loading.winfo_width() // 2)
        y = (loading.winfo_screenheight() // 2) - (loading.winfo_height() // 2)
        loading.geometry(f'+{x}+{y}')

        tk.Label(loading, text='📧', bg=self.panel_bg, font=('Segoe UI', 40)).pack(pady=(20, 10))
        status_label = tk.Label(loading, text='Preparing email...', bg=self.panel_bg,
                               fg='#e2e8f0', font=('Segoe UI', 11))
        status_label.pack()

        def send():
            loading.update()
            status_label.config(text='Generating QR code...')
            loading.update()

            status_label.config(text='Connecting to email server...')
            loading.update()

            success, msg = self.email_service.send_ticket_email(recipient, booking_data)

            loading.destroy()
            if success:
                # Success message
                success_win = tk.Toplevel(self.root)
                success_win.title('Email Sent')
                success_win.geometry('350x200')
                success_win.configure(bg=self.panel_bg)
                success_win.transient(self.root)

                x = (success_win.winfo_screenwidth() // 2) - 175
                y = (success_win.winfo_screenheight() // 2) - 100
                success_win.geometry(f'+{x}+{y}')

                tk.Label(success_win, text='✅', bg=self.panel_bg,
                        font=('Segoe UI', 50)).pack(pady=(20, 10))
                tk.Label(success_win, text='Ticket Sent Successfully!',
                        bg=self.panel_bg, fg='#10b981',
                        font=('Segoe UI Bold', 14)).pack()
                tk.Label(success_win, text=f'Check your inbox: {recipient}',
                        bg=self.panel_bg, fg='#94a3b8',
                        font=self.font_small).pack(pady=10)

                tk.Button(success_win, text='OK', command=success_win.destroy,
                         bg=self.good, fg='white', font=self.font_bold,
                         padx=30, pady=8, relief='flat', cursor='hand2').pack(pady=15)

                success_win.after(3000, success_win.destroy)
            else:
                messagebox.showerror('Error', f'Failed to send email:\n{msg}')

        thread = threading.Thread(target=send)
        thread.start()

    def _select_seat(self, seat_num):
        """Handle seat selection"""
        if not self.seat_buttons[seat_num]['available']:
            messagebox.showwarning('Unavailable', f'Seat {seat_num} is already booked!')
            return

        # Deselect all seats
        for snum, sdata in self.seat_buttons.items():
            if sdata['available']:
                self.seat_canvas.itemconfig(sdata['rect'], fill='#6366f1')

        # Select clicked seat with neon glow effect
        self.seat_canvas.itemconfig(self.seat_buttons[seat_num]['rect'], fill='#10b981')  # emerald green
        self.single_seat.delete(0, 'end')
        self.single_seat.insert(0, str(seat_num))

    def _hover_seat(self, seat_num, entering):
        """Handle seat hover effect"""
        if not self.seat_buttons[seat_num]['available']:
            return

        current_color = self.seat_canvas.itemcget(self.seat_buttons[seat_num]['rect'], 'fill')

        if entering and current_color == '#6366f1':
            self.seat_canvas.itemconfig(self.seat_buttons[seat_num]['rect'], fill='#8b5cf6')
        elif not entering and current_color == '#8b5cf6':
            self.seat_canvas.itemconfig(self.seat_buttons[seat_num]['rect'], fill='#6366f1')

    def _book_single_ticket(self):
        """Book a single ticket with email option"""
        try:
            train_selection = self.single_train.get().strip()
            if not train_selection:
                messagebox.showerror('Error', 'Please select a train')
                return
            train_id = train_selection.split(' - ')[0].strip()
            date = self.single_date.get().strip()
            coach = int(self.single_coach.get())
            seat = int(self.single_seat.get())
            name = self.single_name.get().strip()
            phone = self.single_phone.get().strip()

            if not all([train_id, date, name, phone]):
                messagebox.showerror('Error', 'Please fill all fields')
                return

            # Use single-booking endpoint
            booking_id, error = self.api.book_single(train_id, date, coach, seat, name, phone)

            if booking_id:
                self._show_booking_success_dialog(booking_id, train_id, date, coach, seat, name, phone)
                self._refresh_history()
                self._draw_seat_map()
            else:
                messagebox.showerror('Error', error or 'Booking failed')

        except ValueError:
            messagebox.showerror('Error', 'Please enter valid numbers for coach and seat')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _build_roundtrip_tab(self):
        main = tk.Frame(self.tab_roundtrip, bg=self.bg)
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Enhanced header
        header_frame = tk.Frame(main, bg=self.bg)
        header_frame.pack(pady=(0, 25))

        tk.Label(header_frame, text='🔄', bg=self.bg, fg=self.accent,
                font=('Segoe UI', 32)).pack(side='left', padx=(0, 10))

        title_frame = tk.Frame(header_frame, bg=self.bg)
        title_frame.pack(side='left')
        tk.Label(title_frame, text='Round Trip Booking', bg=self.bg, fg='#e2e8f0',
                font=('Segoe UI Bold', 18)).pack(anchor='w')
        tk.Label(title_frame, text='Book both onward and return journeys together - Save time!',
                bg=self.bg, fg='#64748b', font=self.font_small).pack(anchor='w')

        form = tk.Frame(main, bg=self.panel_bg)
        form.pack(fill='x', pady=10)

        left = tk.Frame(form, bg=self.panel_bg)
        left.pack(side='left', padx=20, pady=20, fill='both', expand=True)

        right = tk.Frame(form, bg=self.panel_bg)
        right.pack(side='left', padx=20, pady=20, fill='both', expand=True)

        # Build train options for comboboxes
        trains = self._load_trains()
        rt_options = [f"{t['id']} - {t['name']}" for t in trains]

        tk.Label(left, text='➡️ ONWARD JOURNEY', bg=self.panel_bg, fg=self.good,
                font=self.font_bold).pack(anchor='w', pady=(0, 10))
        tk.Label(left, text='Select Train', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))
        self.rt_train_onward_var = tk.StringVar()
        self.rt_train_onward = ttk.Combobox(left, textvariable=self.rt_train_onward_var,
                                            values=rt_options, width=30,
                                            font=self.font_regular, state='readonly')
        self.rt_train_onward.pack(anchor='w', pady=(2, 10), ipady=6)
        if rt_options:
            self.rt_train_onward.set(rt_options[0])

        tk.Label(left, text='Date (YYYY-MM-DD)', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))
        self.rt_date_onward = tk.Entry(left, bg=self.surface, fg='#e2e8f0', width=25,
                                       font=self.font_regular, relief='flat', bd=5)
        self.rt_date_onward.pack(anchor='w', pady=(2, 10), ipady=6)

        tk.Label(right, text='⬅️ RETURN JOURNEY', bg=self.panel_bg, fg=self.accent,
                font=self.font_bold).pack(anchor='w', pady=(0, 10))
        tk.Label(right, text='Select Train', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))
        self.rt_train_return_var = tk.StringVar()
        self.rt_train_return = ttk.Combobox(right, textvariable=self.rt_train_return_var,
                                           values=rt_options, width=30,
                                           font=self.font_regular, state='readonly')
        self.rt_train_return.pack(anchor='w', pady=(2, 10), ipady=6)
        if rt_options:
            self.rt_train_return.set(rt_options[0])

        tk.Label(right, text='Date (YYYY-MM-DD)', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))
        self.rt_date_return = tk.Entry(right, bg=self.surface, fg='#e2e8f0', width=25,
                                       font=self.font_regular, relief='flat', bd=5)
        self.rt_date_return.pack(anchor='w', pady=(2, 10), ipady=6)

        bottom = tk.Frame(main, bg=self.panel_bg, relief='ridge', bd=2)
        bottom.pack(fill='x', pady=10, padx=10)

        details = tk.Frame(bottom, bg=self.panel_bg)
        details.pack(padx=30, pady=20)

        # Configure grid columns for proper alignment
        for i in range(4):
            details.columnconfigure(i, weight=1)

        tk.Label(details, text='Coach', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=0, column=0, sticky='w', padx=5, pady=8)
        self.rt_coach = tk.Entry(details, bg=self.surface, fg='#e2e8f0', width=10,
                                font=self.font_regular, relief='flat', bd=5)
        self.rt_coach.grid(row=0, column=1, padx=5, pady=8, ipady=6)

        tk.Label(details, text='Seats (e.g., 1,2,3)', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=0, column=2, sticky='w', padx=5, pady=8)
        self.rt_seats = tk.Entry(details, bg=self.surface, fg='#e2e8f0', width=20,
                                font=self.font_regular, relief='flat', bd=5)
        self.rt_seats.grid(row=0, column=3, padx=5, pady=8, ipady=6)

        tk.Label(details, text='Passenger Name', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=1, column=0, sticky='w', padx=5, pady=8)
        self.rt_name = tk.Entry(details, bg=self.surface, fg='#e2e8f0', width=25,
                               font=self.font_regular, relief='flat', bd=5)
        self.rt_name.grid(row=1, column=1, columnspan=2, padx=5, pady=8, sticky='ew', ipady=6)
        self.rt_name.insert(0, self.current_user.get('full_name', ''))

        tk.Label(details, text='Phone', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=1, column=2, sticky='e', padx=5, pady=8)
        self.rt_phone = tk.Entry(details, bg=self.surface, fg='#e2e8f0', width=20,
                                font=self.font_regular, relief='flat', bd=5)
        self.rt_phone.grid(row=1, column=3, padx=5, pady=8, ipady=6)
        self.rt_phone.insert(0, self.current_user.get('phone', ''))

        book_btn = tk.Button(main, text='🎫 Book Round Trip', command=self._book_round_trip,
                            bg=self.accent, fg='#0f172a', font=('Segoe UI Semibold', 13),
                            padx=40, pady=12, relief='flat', cursor='hand2')
        book_btn.pack(pady=20)

        # Hover effect
        book_btn.bind('<Enter>', lambda e: book_btn.config(bg='#fbbf24'))
        book_btn.bind('<Leave>', lambda e: book_btn.config(bg=self.accent))

    def _book_round_trip(self):
        """Book a round trip"""
        try:
            onward_sel = self.rt_train_onward.get().strip()
            return_sel = self.rt_train_return.get().strip()

            if not onward_sel or not return_sel:
                messagebox.showerror('Error', 'Please select both trains')
                return

            train_id_onward = onward_sel.split(' - ')[0].strip()
            train_id_return = return_sel.split(' - ')[0].strip()
            date_onward = self.rt_date_onward.get().strip()
            date_return = self.rt_date_return.get().strip()

            try:
                coach = int(self.rt_coach.get())
            except:
                messagebox.showerror('Error', 'Please enter valid coach number')
                return

            seat_str = self.rt_seats.get().strip()
            if not seat_str:
                messagebox.showerror('Error', 'Please enter seat numbers')
                return
            seats = [int(s.strip()) for s in seat_str.split(',') if s.strip()]

            name = self.rt_name.get().strip()
            phone = self.rt_phone.get().strip()

            if not all([train_id_onward, train_id_return, date_onward, date_return, name, phone]) or not seats:
                messagebox.showerror('Error', 'Please fill all fields')
                return

            confirm = messagebox.askyesno('Confirm Round Trip',
                f'Book round trip?\n\nOnward: {train_id_onward} on {date_onward}\nReturn: {train_id_return} on {date_return}\nSeats: {", ".join(map(str, seats))}')
            if not confirm:
                return

            booking_ids, error = self.api.book_round_trip(train_id_onward, train_id_return,
                                                          date_onward, date_return, coach, seats,
                                                          name, phone)

            if booking_ids:
                messagebox.showinfo('Success', f'Round trip booked!\nBooking IDs: {", ".join(booking_ids)}')
                self._refresh_history()
            else:
                messagebox.showerror('Error', error or 'Booking failed')

        except ValueError:
            messagebox.showerror('Error', 'Invalid seat numbers. Use format: 1,2,3')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _build_multibooking_tab(self):
        """Build multi-booking tab for booking multiple tickets at once"""
        main = tk.Frame(self.tab_multibooking, bg=self.bg)
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Header
        header_frame = tk.Frame(main, bg=self.bg)
        header_frame.pack(pady=(0, 20))

        tk.Label(header_frame, text='🎫', bg=self.bg, fg=self.accent,
                font=('Segoe UI', 32)).pack(side='left', padx=(0, 10))

        title_frame = tk.Frame(header_frame, bg=self.bg)
        title_frame.pack(side='left')
        tk.Label(title_frame, text='Multi-Ticket Booking', bg=self.bg, fg='#e2e8f0',
                font=('Segoe UI Bold', 18)).pack(anchor='w')
        tk.Label(title_frame, text='Book multiple seats for your group - Perfect for family trips!',
                bg=self.bg, fg='#64748b', font=self.font_small).pack(anchor='w')

        # Content area
        content = tk.Frame(main, bg=self.panel_bg, relief='flat', bd=2)
        content.pack(fill='both', expand=True)

        # Left: Form
        left_panel = tk.Frame(content, bg=self.panel_bg)
        left_panel.pack(side='left', fill='both', expand=True, padx=20, pady=20)

        tk.Label(left_panel, text='📋 Booking Information', bg=self.panel_bg, fg='#e2e8f0',
                font=('Segoe UI Semibold', 13)).pack(pady=(0, 15))

        form = tk.Frame(left_panel, bg=self.panel_bg)
        form.pack(fill='both', expand=True)

        # Train selection
        tk.Label(form, text='Select Train:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))

        self.available_trains = self._load_trains()
        train_options = [f"{t['id']} - {t['name']} ({t['route']}) - ৳{t['base_price']}"
                        for t in self.available_trains]

        self.multi_train_var = tk.StringVar()
        self.multi_train = ttk.Combobox(form, textvariable=self.multi_train_var,
                                       values=train_options, width=45,
                                       font=self.font_regular, state='readonly')
        self.multi_train.pack(fill='x', pady=(0, 15))
        if train_options:
            self.multi_train.set(train_options[0])

        # Date
        tk.Label(form, text='Date (YYYY-MM-DD):', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))
        self.multi_date = tk.Entry(form, bg=self.surface, fg='#e2e8f0',
                                   font=self.font_regular, relief='flat', bd=5)
        self.multi_date.pack(fill='x', pady=(0, 15), ipady=6)
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        self.multi_date.insert(0, tomorrow)

        # Coach
        tk.Label(form, text='Coach Number:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))
        self.multi_coach = tk.Spinbox(form, from_=1, to=10, bg=self.surface, fg='#e2e8f0',
                                      font=self.font_regular, relief='flat', bd=5)
        self.multi_coach.pack(fill='x', pady=(0, 15), ipady=6)

        # Number of seats
        tk.Label(form, text='Number of Seats:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))
        self.multi_num_seats = tk.Spinbox(form, from_=1, to=10, bg=self.surface, fg='#e2e8f0',
                                          font=self.font_regular, relief='flat', bd=5)
        self.multi_num_seats.pack(fill='x', pady=(0, 15), ipady=6)

        # Seat numbers
        tk.Label(form, text='Seat Numbers (comma-separated):', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))
        self.multi_seats = tk.Entry(form, bg=self.surface, fg='#e2e8f0',
                                    font=self.font_regular, relief='flat', bd=5)
        self.multi_seats.pack(fill='x', pady=(0, 15), ipady=6)

        tk.Label(form, text='Example: 15,16,17,18', bg=self.panel_bg, fg='#64748b',
                font=self.font_tiny).pack(anchor='w')

        # Passenger details
        tk.Label(form, text='Main Passenger Name:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(15, 5))
        self.multi_name = tk.Entry(form, bg=self.surface, fg='#e2e8f0',
                                   font=self.font_regular, relief='flat', bd=5)
        self.multi_name.pack(fill='x', pady=(0, 15), ipady=6)
        self.multi_name.insert(0, self.current_user.get('full_name', ''))

        tk.Label(form, text='Phone:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(anchor='w', pady=(0, 5))
        self.multi_phone = tk.Entry(form, bg=self.surface, fg='#e2e8f0',
                                    font=self.font_regular, relief='flat', bd=5)
        self.multi_phone.pack(fill='x', pady=(0, 15), ipady=6)
        self.multi_phone.insert(0, self.current_user.get('phone', ''))

        # Book button
        book_btn = tk.Button(left_panel, text='🎫 Book Multiple Tickets',
                            command=self._book_multiple_tickets,
                            bg=self.accent, fg='#0f172a', font=('Segoe UI Semibold', 13),
                            padx=40, pady=12, relief='flat', cursor='hand2')
        book_btn.pack(pady=20)
        book_btn.bind('<Enter>', lambda e: book_btn.config(bg='#fbbf24'))
        book_btn.bind('<Leave>', lambda e: book_btn.config(bg=self.accent))

        # Right: Info panel
        right_panel = tk.Frame(content, bg=self.panel_bg)
        right_panel.pack(side='left', fill='both', expand=True, padx=20, pady=20)

        tk.Label(right_panel, text='💡 Multi-Booking Tips', bg=self.panel_bg, fg='#e2e8f0',
                font=('Segoe UI Semibold', 13)).pack(pady=(0, 15))

        tips = [
            ('🎯', 'Perfect for Groups', 'Book seats for your whole family or group at once'),
            ('💰', 'Same Price', 'Each seat priced individually - no hidden fees'),
            ('🪑', 'Adjacent Seats', 'Try to book consecutive seat numbers for best experience'),
            ('📧', 'Single Email', 'Get all tickets in one email delivery'),
            ('⚡', 'Fast Process', 'Much faster than booking individually'),
        ]

        for emoji, title, desc in tips:
            tip_card = tk.Frame(right_panel, bg=self.surface, relief='flat')
            tip_card.pack(fill='x', pady=8)

            tk.Label(tip_card, text=emoji, bg=self.surface, fg=self.accent,
                    font=('Segoe UI', 20)).pack(side='left', padx=15, pady=10)

            text_frame = tk.Frame(tip_card, bg=self.surface)
            text_frame.pack(side='left', fill='x', expand=True, pady=10, padx=(0, 15))

            tk.Label(text_frame, text=title, bg=self.surface, fg='#e2e8f0',
                    font=('Segoe UI Semibold', 11), anchor='w').pack(anchor='w')
            tk.Label(text_frame, text=desc, bg=self.surface, fg='#94a3b8',
                    font=('Segoe UI', 9), anchor='w').pack(anchor='w')

    def _book_multiple_tickets(self):
        """Book multiple tickets at once"""
        try:
            train_selection = self.multi_train.get().strip()
            if not train_selection:
                messagebox.showerror('Error', 'Please select a train')
                return
            train_id = train_selection.split(' - ')[0].strip()
            date = self.multi_date.get().strip()
            coach = int(self.multi_coach.get())
            seat_str = self.multi_seats.get().strip()
            if not seat_str:
                messagebox.showerror('Error', 'Please enter seat numbers')
                return
            seats = [int(s.strip()) for s in seat_str.split(',') if s.strip()]
            name = self.multi_name.get().strip()
            phone = self.multi_phone.get().strip()

            if not all([train_id, date, name, phone]) or not seats:
                messagebox.showerror('Error', 'Please fill all fields')
                return

            confirm = messagebox.askyesno('Confirm Booking',
                f'Book {len(seats)} seats?\n\nTrain: {train_id}\nSeats: {", ".join(map(str, seats))}')
            if not confirm:
                return

            # Use batch-booking endpoint
            booking_ids, error = self.api.book_batch(train_id, date, coach, seats, name, phone)

            if booking_ids:
                messagebox.showinfo('Success', f'Multi-booking successful!\nIDs: {", ".join(booking_ids)}')
                self._refresh_history()
                self._draw_seat_map()
            else:
                messagebox.showerror('Error', error or 'Booking failed')

        except ValueError:
            messagebox.showerror('Error', 'Invalid seat numbers. Use format: 15,16,17')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _build_compare_tab(self):
        """Build train comparison tab"""
        main = tk.Frame(self.tab_compare, bg=self.bg)
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Header
        header_frame = tk.Frame(main, bg=self.bg)
        header_frame.pack(pady=(0, 20))

        tk.Label(header_frame, text='⚖️', bg=self.bg, fg=self.accent,
                font=('Segoe UI', 32)).pack(side='left', padx=(0, 10))

        title_frame = tk.Frame(header_frame, bg=self.bg)
        title_frame.pack(side='left')
        tk.Label(title_frame, text='Compare Trains', bg=self.bg, fg='#e2e8f0',
                font=('Segoe UI Bold', 18)).pack(anchor='w')
        tk.Label(title_frame, text='Compare different trains to find the best option for your journey',
                bg=self.bg, fg='#64748b', font=self.font_small).pack(anchor='w')

        # Selection area
        selection_frame = tk.Frame(main, bg=self.panel_bg, relief='flat', bd=2)
        selection_frame.pack(fill='x', pady=(0, 20))

        tk.Label(selection_frame, text='Select Trains to Compare', bg=self.panel_bg, fg='#e2e8f0',
                font=('Segoe UI Semibold', 12)).pack(pady=15)

        select_frame = tk.Frame(selection_frame, bg=self.panel_bg)
        select_frame.pack(padx=30, pady=(0, 20))

        self.available_trains = self._load_trains()
        train_options = [f"{t['id']} - {t['name']}" for t in self.available_trains]

        # Train 1
        tk.Label(select_frame, text='Train 1:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=0, column=0, sticky='w', padx=10, pady=10)
        self.compare_train1_var = tk.StringVar()
        self.compare_train1 = ttk.Combobox(select_frame, textvariable=self.compare_train1_var,
                                          values=train_options, width=35,
                                          font=self.font_regular, state='readonly')
        self.compare_train1.grid(row=0, column=1, padx=10, pady=10)
        if train_options:
            self.compare_train1.set(train_options[0])

        # Train 2
        tk.Label(select_frame, text='Train 2:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=1, column=0, sticky='w', padx=10, pady=10)
        self.compare_train2_var = tk.StringVar()
        self.compare_train2 = ttk.Combobox(select_frame, textvariable=self.compare_train2_var,
                                          values=train_options, width=35,
                                          font=self.font_regular, state='readonly')
        self.compare_train2.grid(row=1, column=1, padx=10, pady=10)
        if len(train_options) > 1:
            self.compare_train2.set(train_options[1])

        # Compare button
        compare_btn = tk.Button(selection_frame, text='⚖️ Compare Trains',
                               command=self._do_compare_trains,
                               bg=self.accent, fg='#0f172a',
                               font=('Segoe UI Semibold', 12), padx=40, pady=10,
                               relief='flat', cursor='hand2')
        compare_btn.pack(pady=(0, 20))
        compare_btn.bind('<Enter>', lambda e: compare_btn.config(bg='#fbbf24'))
        compare_btn.bind('<Leave>', lambda e: compare_btn.config(bg=self.accent))

        # Comparison results area
        self.comparison_frame = tk.Frame(main, bg=self.panel_bg, relief='flat', bd=2)
        self.comparison_frame.pack(fill='both', expand=True)

        # Initial message
        tk.Label(self.comparison_frame, text='Select two trains and click Compare',
                bg=self.panel_bg, fg='#64748b',
                font=('Segoe UI', 12)).pack(expand=True)

    def _do_compare_trains(self):
        """Compare selected trains"""
        try:
            train1_sel = self.compare_train1.get().strip()
            train2_sel = self.compare_train2.get().strip()

            if not train1_sel or not train2_sel:
                messagebox.showerror('Error', 'Please select both trains')
                return

            train1_id = train1_sel.split(' - ')[0].strip()
            train2_id = train2_sel.split(' - ')[0].strip()

            if train1_id == train2_id:
                messagebox.showwarning('Warning', 'Please select different trains')
                return

            # Get train details
            train1 = next((t for t in self.available_trains if t['id'] == train1_id), None)
            train2 = next((t for t in self.available_trains if t['id'] == train2_id), None)

            if not train1 or not train2:
                messagebox.showerror('Error', 'Train details not found')
                return

            # Clear comparison frame
            for widget in self.comparison_frame.winfo_children():
                widget.destroy()

            # Build comparison table
            tk.Label(self.comparison_frame, text='Comparison Results', bg=self.panel_bg,
                    fg='#e2e8f0', font=('Segoe UI Bold', 14)).pack(pady=15)

            # Comparison table
            table_frame = tk.Frame(self.comparison_frame, bg=self.panel_bg)
            table_frame.pack(padx=40, pady=20, fill='both', expand=True)

            # Headers
            headers = ['Feature', train1['name'], train2['name']]
            for col, header in enumerate(headers):
                bg = self.surface if col == 0 else self.accent if col == 1 else self.window_color
                tk.Label(table_frame, text=header, bg=bg, fg='white' if col > 0 else '#e2e8f0',
                        font=('Segoe UI Semibold', 11), padx=20, pady=15,
                        relief='flat').grid(row=0, column=col, sticky='ew', padx=2, pady=2)

            # Comparison rows
            comparisons = [
                ('Train ID', train1['id'], train2['id']),
                ('Route', train1['route'], train2['route']),
                ('Coaches', str(train1['coaches']), str(train2['coaches'])),
                ('Seats per Coach', str(train1['seats_per_coach']), str(train2['seats_per_coach'])),
                ('Total Capacity', str(train1['coaches'] * train1['seats_per_coach']),
                 str(train2['coaches'] * train2['seats_per_coach'])),
                ('Base Price', f"৳{train1['base_price']}", f"৳{train2['base_price']}"),
            ]

            for row, (feature, val1, val2) in enumerate(comparisons, start=1):
                # Feature name
                tk.Label(table_frame, text=feature, bg=self.surface, fg='#e2e8f0',
                        font=self.font_regular, padx=20, pady=12,
                        anchor='w').grid(row=row, column=0, sticky='ew', padx=2, pady=2)

                # Train 1 value
                tk.Label(table_frame, text=val1, bg='#1e3a5f', fg='#e2e8f0',
                        font=self.font_regular, padx=20, pady=12).grid(row=row, column=1,
                                                                       sticky='ew', padx=2, pady=2)

                # Train 2 value
                tk.Label(table_frame, text=val2, bg='#1e4a6f', fg='#e2e8f0',
                        font=self.font_regular, padx=20, pady=12).grid(row=row, column=2,
                                                                       sticky='ew', padx=2, pady=2)

            # Configure column weights
            for i in range(3):
                table_frame.columnconfigure(i, weight=1)

            # Winner badge
            winner_frame = tk.Frame(self.comparison_frame, bg=self.panel_bg)
            winner_frame.pack(pady=20)

            if train1['base_price'] < train2['base_price']:
                winner = train1['name']
                color = self.accent
            elif train2['base_price'] < train1['base_price']:
                winner = train2['name']
                color = self.window_color
            else:
                winner = "Same Price!"
                color = self.good

            tk.Label(winner_frame, text='🏆', bg=self.panel_bg,
                    font=('Segoe UI', 30)).pack(side='left', padx=10)
            tk.Label(winner_frame, text=f'Best Value: {winner}', bg=self.panel_bg,
                    fg=color, font=('Segoe UI Bold', 14)).pack(side='left')

        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _logout(self):
        if messagebox.askyesno('Logout', 'Are you sure you want to logout?'):
            self.current_user = None
            self.api.token = None
            for widget in self.root.winfo_children():
                widget.destroy()
            self._show_login()

    def _build_status_bar(self):
        status = tk.Frame(self.root, bg=self.panel_bg, height=35)
        status.pack(fill='x', side='bottom')

        # Left side - status
        left_status = tk.Frame(status, bg=self.panel_bg)
        left_status.pack(side='left', padx=15, pady=8)

        status_indicator = tk.Label(left_status, text='●', bg=self.panel_bg, fg=self.good,
                                   font=('Segoe UI', 12))
        status_indicator.pack(side='left', padx=(0, 5))
        tk.Label(left_status, text='All Systems Operational', bg=self.panel_bg,
                fg=self.text_secondary, font=('Segoe UI', 9)).pack(side='left')

        # Center - version info
        tk.Label(status, text='Bangladesh Railway v2.5 • Ultra Premium Edition',
                bg=self.panel_bg, fg=self.text_secondary,
                font=('Segoe UI', 8)).pack(side='left', expand=True)

        # Right side - links
        right_status = tk.Frame(status, bg=self.panel_bg)
        right_status.pack(side='right', padx=15)

        links = [
            ('💬 Support', lambda: messagebox.showinfo('Support', 'Email: support@railway.bd\nPhone: +880 1234-567890')),
            ('📖 Help', lambda: webbrowser.open('https://github.com')),
            ('⭐ Rate Us', lambda: messagebox.showinfo('Thank You!', 'Thank you for using our service! ⭐⭐⭐⭐⭐'))
        ]

        for text, cmd in links:
            link_btn = tk.Label(right_status, text=text, bg=self.panel_bg, fg=self.accent,
                               font=('Segoe UI', 8), cursor='hand2')
            link_btn.pack(side='left', padx=8)
            link_btn.bind('<Button-1>', lambda e, c=cmd: c())
            link_btn.bind('<Enter>', lambda e, l=link_btn: l.config(fg=self.accent_hover))
            link_btn.bind('<Leave>', lambda e, l=link_btn: l.config(fg=self.accent))

    def _build_dashboard_tab(self):
        main = tk.Frame(self.tab_dashboard, bg=self.bg)
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Welcome banner
        welcome = tk.Frame(main, bg=self.panel_bg, height=120)
        welcome.pack(fill='x', pady=(0, 20))
        welcome.pack_propagate(False)

        welcome_content = tk.Frame(welcome, bg=self.panel_bg)
        welcome_content.pack(expand=True, padx=30)

        tk.Label(welcome_content, text=f'👋 Welcome back, {self.current_user["full_name"]}!',
                bg=self.panel_bg, fg=self.text_primary, font=('Segoe UI Bold', 24)).pack(anchor='w')
        tk.Label(welcome_content, text='Ready to book your next journey? Let\'s get started!',
                bg=self.panel_bg, fg=self.text_secondary, font=('Segoe UI', 12)).pack(anchor='w', pady=(5, 0))

        # Quick action cards
        actions_frame = tk.Frame(main, bg=self.bg)
        actions_frame.pack(fill='x', pady=(0, 20))

        quick_actions = [
            ('🎫', 'Quick Book', 'Book a ticket now', self.accent, lambda: self.notebook.select(1)),
            ('🔄', 'Round Trip', 'Plan your journey', self.good, lambda: self.notebook.select(2)),
            ('📜', 'My Tickets', 'View bookings', self.info, lambda: self.notebook.select(4)),
            ('🚆', 'All Trains', 'Browse trains', self.warning, self._refresh_trains)
        ]

        for emoji, title, subtitle, color, cmd in quick_actions:
            card = tk.Frame(actions_frame, bg=self.panel_bg, relief='flat')
            card.pack(side='left', fill='both', expand=True, padx=5, ipadx=20, ipady=20)

            tk.Label(card, text=emoji, bg=self.panel_bg, font=('Segoe UI', 40)).pack(pady=(10, 5))
            tk.Label(card, text=title, bg=self.panel_bg, fg=self.text_primary,
                    font=('Segoe UI Bold', 14)).pack()
            tk.Label(card, text=subtitle, bg=self.panel_bg, fg=self.text_secondary,
                    font=('Segoe UI', 9)).pack(pady=(2, 10))

            btn = tk.Button(card, text='Go →', bg=color, fg='white',
                          font=('Segoe UI Bold', 10), relief='flat', cursor='hand2',
                          padx=25, pady=8, borderwidth=0, command=cmd)
            btn.pack()
            btn.bind('<Enter>', lambda e, b=btn, c=color: b.config(bg=self._darken_color(c)))
            btn.bind('<Leave>', lambda e, b=btn, c=color: b.config(bg=c))

        # Statistics dashboard
        stats_section = tk.Frame(main, bg=self.bg)
        stats_section.pack(fill='both', expand=True)

        # Left: Recent activity
        left_panel = tk.Frame(stats_section, bg=self.panel_bg)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))

        tk.Label(left_panel, text='📊 Your Statistics', bg=self.panel_bg, fg=self.text_primary,
                font=('Segoe UI Bold', 16)).pack(anchor='w', padx=20, pady=(20, 15))

        try:
            bookings = self.api.get_booking_history()
            total_bookings = len(bookings)
            active_bookings = len([b for b in bookings if b['status'] == 'BOOKED'])

            stats_data = [
                ('Total Bookings', str(total_bookings), '📈', self.accent),
                ('Active Tickets', str(active_bookings), '🎫', self.good),
                ('Completed', str(total_bookings - active_bookings), '✅', self.info)
            ]
        except:
            stats_data = [
                ('Total Bookings', '0', '📈', self.accent),
                ('Active Tickets', '0', '🎫', self.good),
                ('Completed', '0', '✅', self.info)
            ]

        for label, value, emoji, color in stats_data:
            stat_row = tk.Frame(left_panel, bg=self.surface)
            stat_row.pack(fill='x', padx=20, pady=5)

            tk.Label(stat_row, text=emoji, bg=self.surface, font=('Segoe UI', 20)).pack(side='left', padx=10, pady=10)

            info_frame = tk.Frame(stat_row, bg=self.surface)
            info_frame.pack(side='left', fill='x', expand=True, pady=10)

            tk.Label(info_frame, text=label, bg=self.surface, fg=self.text_secondary,
                    font=('Segoe UI', 10)).pack(anchor='w')
            tk.Label(info_frame, text=value, bg=self.surface, fg=color,
                    font=('Segoe UI Bold', 18)).pack(anchor='w')

        # Right: Latest trains
        right_panel = tk.Frame(stats_section, bg=self.panel_bg)
        right_panel.pack(side='left', fill='both', expand=True, padx=(10, 0))

        tk.Label(right_panel, text='🚆 Available Trains', bg=self.panel_bg, fg=self.text_primary,
                font=('Segoe UI Bold', 16)).pack(anchor='w', padx=20, pady=(20, 15))

        trains_container = tk.Frame(right_panel, bg=self.panel_bg)
        trains_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        trains = self._load_trains()[:4]  # Show first 4 trains
        for train in trains:
            train_card = tk.Frame(trains_container, bg=self.surface)
            train_card.pack(fill='x', pady=5)

            tk.Label(train_card, text='🚂', bg=self.surface, font=('Segoe UI', 18)).pack(side='left', padx=10, pady=10)

            train_info = tk.Frame(train_card, bg=self.surface)
            train_info.pack(side='left', fill='x', expand=True, pady=10)

            tk.Label(train_info, text=f"{train['id']} - {train['name']}", bg=self.surface,
                    fg=self.text_primary, font=('Segoe UI Bold', 11)).pack(anchor='w')
            tk.Label(train_info, text=train['route'], bg=self.surface, fg=self.text_secondary,
                    font=('Segoe UI', 9)).pack(anchor='w')

            tk.Label(train_card, text=f"৳{train['base_price']}", bg=self.surface,
                    fg=self.accent, font=('Segoe UI Bold', 12)).pack(side='right', padx=15)

    def _darken_color(self, hex_color):
        """Helper to darken a hex color"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = max(0, r-30), max(0, g-30), max(0, b-30)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _build_history_tab(self):
        frame = tk.Frame(self.tab_history, bg=self.bg)
        frame.pack(fill='both', expand=True)
        self.history_list = tk.Listbox(frame, bg=self.surface, fg='#e2e8f0')
        self.history_list.pack(fill='both', expand=True, padx=20, pady=20)
        self._refresh_history()

    def _refresh_history(self):
        if not hasattr(self, 'history_list'):
            return
        self.history_list.delete(0, 'end')
        for b in self.api.get_booking_history():
            self.history_list.insert('end', f"{b['booking_id']} - {b['train_id']} {b['date']} C{b['coach']} S{b['seat']} - {b['status']}")

    def _build_refunds_tab(self):
        frame = tk.Frame(self.tab_refunds, bg=self.bg)
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text='Enter Booking ID to request refund', bg=self.bg, fg='#e2e8f0').pack(pady=10)
        self.refund_id_entry = tk.Entry(frame, bg=self.surface, fg='#e2e8f0')
        self.refund_id_entry.pack(pady=5)
        tk.Button(frame, text='Request Refund', command=self._request_refund, bg=self.accent).pack(pady=10)

    def _request_refund(self):
        bid = self.refund_id_entry.get().strip()
        if not bid:
            messagebox.showerror('Error', 'Enter a booking ID')
            return
        data, err = self.api.request_refund(bid, 'Change of plans')
        if data:
            messagebox.showinfo('Refund', f"Requested: {data['refund_id']} Amount: {data['refund_amount']}")
        else:
            messagebox.showerror('Error', err or 'Failed')

    def _build_schedules_tab(self):
        frame = tk.Frame(self.tab_schedules, bg=self.bg)
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text='Train Schedules', bg=self.bg, fg='#e2e8f0', font=self.font_heading).pack(pady=10)
        trains = self._load_trains()
        options = [f"{t['id']} - {t['name']}" for t in trains]
        self.sch_var = tk.StringVar(value=options[0] if options else '')
        ttk.Combobox(frame, textvariable=self.sch_var, values=options, state='readonly').pack(pady=5)
        self.sch_text = tk.Text(frame, bg=self.surface, fg='#e2e8f0', height=10)
        self.sch_text.pack(fill='both', expand=True, padx=20, pady=10)
        tk.Button(frame, text='Load Schedule', command=self._load_schedule, bg=self.accent).pack(pady=8)

    def _load_schedule(self):
        sel = self.sch_var.get()
        tid = sel.split(' - ')[0] if sel else ''
        data = self.api.get_train_schedule(tid)
        self.sch_text.delete('1.0', 'end')
        if data:
            self.sch_text.insert('end', str(data))
        else:
            self.sch_text.insert('end', 'No schedule found')

    def _build_reports_tab(self):
        frame = tk.Frame(self.tab_reports, bg=self.bg)
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text='Reports', bg=self.bg, fg='#e2e8f0', font=self.font_heading).pack(pady=10)
        tk.Button(frame, text='Popular Routes', command=self._show_popular_routes, bg=self.accent).pack(pady=5)
        self.reports_text = tk.Text(frame, bg=self.surface, fg='#e2e8f0', height=12)
        self.reports_text.pack(fill='both', expand=True, padx=20, pady=10)

    def _show_popular_routes(self):
        data = self.api.get_popular_routes()
        self.reports_text.delete('1.0', 'end')
        if not data:
            self.reports_text.insert('end', 'No data')
            return
        for r in data.get('popular_routes', []):
            self.reports_text.insert('end', f"{r['route']}: {r['bookings']} bookings\n")

    def _build_settings_tab(self):
        frame = tk.Frame(self.tab_settings, bg=self.bg)
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text='Email Settings', bg=self.bg, fg='#e2e8f0', font=self.font_heading).pack(pady=10)
        tk.Label(frame, text='Gmail Address', bg=self.bg, fg='#e2e8f0').pack()
        self.email_entry = tk.Entry(frame, bg=self.surface, fg='#e2e8f0', width=40)
        self.email_entry.pack(pady=5)
        tk.Label(frame, text='App Password', bg=self.bg, fg='#e2e8f0').pack()
        self.pass_entry = tk.Entry(frame, bg=self.surface, fg='#e2e8f0', width=40, show='•')
        self.pass_entry.pack(pady=5)
        tk.Button(frame, text='Save', command=self._save_email_settings, bg=self.accent).pack(pady=10)

    def _save_email_settings(self):
        email = self.email_entry.get().strip()
        pwd = self.pass_entry.get().strip()
        if not email or not pwd:
            messagebox.showerror('Error', 'Enter email and app password')
            return
        self.email_service.configure_email(email, pwd)
        messagebox.showinfo('Saved', 'Email settings saved')


def main():

    print("=" * 70)
    print("    🚂 BANGLADESH RAILWAY V2 - ENHANCED BOOKING SYSTEM")
    print("=" * 70)

    api = TrainAPIClientV2()

    # Always create GUI root first
    root = tk.Tk()

    # Non-blocking API connection check
    connected = api.check_api_connection()
    if not connected:
        # Show a top-level warning banner but continue to load GUI
        root.withdraw()
        messagebox.showwarning(
            "API Server Not Running",
            "API V2 server is not running. Some features will be disabled until you start api_server_v2.py.\n\n"
            "Run: python api_server_v2.py"
        )
        root.deiconify()
        print("⚠️  API V2 server not running; GUI will still start.")
    else:
        print("✓ Connected to API V2 server")
        print("  Starting Enhanced GUI...")

    app = EnhancedTrainBookingApp(root, api)
    root.mainloop()


if __name__ == '__main__':
    main()


