import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from api_client import TrainAPIClient


class TrainBookingApp:

    def __init__(self, root, api):
        self.root = root
        self.api = api

        self.root.title('🚂 Bangladesh Railway - Ticket Booking System')
        self.root.geometry('1300x700')
        self.root.minsize(1100, 600)

        self.bg = '#0f172a'
        self.panel_bg = '#1e293b'
        self.surface = '#334155'
        self.accent = '#f59e0b'
        self.accent_hover = '#fbbf24'
        self.good = '#10b981'
        self.bad = '#ef4444'
        self.window_color = '#3b82f6'
        self.aisle_color = '#6366f1'

        self.root.configure(bg=self.bg)

        self.font_small = ('Segoe UI', 9)
        self.font_regular = ('Segoe UI', 10)
        self.font_bold = ('Segoe UI Semibold', 10)
        self.font_title = ('Segoe UI Semibold', 16)

        self.current_train_id = None
        self.current_date = datetime.date.today().strftime('%Y-%m-%d')
        self.current_coach = 1
        self._selected_seats = set()

        self._setup_styles()

        self._build_header()
        self._build_toolbar()
        self._build_main_content()
        self._build_status_bar()

        self._refresh_train_list()

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass

        style.configure('TButton', padding=6)
        style.configure('Accent.TButton', background=self.accent, foreground='#0f172a')
        style.configure('Treeview', background=self.surface, fieldbackground=self.surface,
                       foreground='#e2e8f0', rowheight=24, font=self.font_small)
        style.configure('Treeview.Heading', background=self.accent, foreground='#0f172a',
                       font=('Segoe UI Semibold', 9))

    def _build_header(self):
        header = tk.Frame(self.root, bg=self.panel_bg, height=50)
        header.pack(fill='x', padx=10, pady=(10, 5))
        header.pack_propagate(False)

        tk.Label(header, text='🚂 Bangladesh Railway', bg=self.panel_bg, fg=self.accent,
                font=self.font_title).pack(side='left', padx=10, pady=10)

        tk.Label(header, text='Ticket Booking System', bg=self.panel_bg, fg='#64748b',
                font=self.font_regular).pack(side='left', pady=10)

        today = datetime.datetime.now().strftime("%B %d, %Y")
        tk.Label(header, text=f'📅 {today}', bg=self.panel_bg, fg='#94a3b8',
                font=self.font_regular).pack(side='right', padx=10)

    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, bg=self.bg)
        toolbar.pack(fill='x', padx=10, pady=5)

        tk.Label(toolbar, text='Train:', bg=self.bg, fg='#e2e8f0',
                font=self.font_bold).pack(side='left', padx=(0, 5))
        self.train_cmb = ttk.Combobox(toolbar, width=35, state='readonly', font=self.font_regular)
        self.train_cmb.pack(side='left', padx=(0, 15))
        self.train_cmb.bind('<<ComboboxSelected>>', lambda e: self._on_train_change())

        tk.Label(toolbar, text='Date:', bg=self.bg, fg='#e2e8f0',
                font=self.font_bold).pack(side='left', padx=(0, 5))
        self.date_entry = tk.Entry(toolbar, width=12, font=self.font_regular,
                                   bg=self.surface, fg='#e2e8f0', insertbackground='white')
        self.date_entry.insert(0, self.current_date)
        self.date_entry.pack(side='left', padx=(0, 5))

        tk.Button(toolbar, text='Set', command=self._set_date, bg=self.accent, fg='#0f172a',
                 font=self.font_small, padx=8).pack(side='left', padx=(0, 5))
        tk.Button(toolbar, text='◀', command=self._date_prev, bg=self.surface, fg='#e2e8f0',
                 font=self.font_small, width=3).pack(side='left', padx=1)
        tk.Button(toolbar, text='▶', command=self._date_next, bg=self.surface, fg='#e2e8f0',
                 font=self.font_small, width=3).pack(side='left', padx=(1, 15))

        tk.Label(toolbar, text='Coach:', bg=self.bg, fg='#e2e8f0',
                font=self.font_bold).pack(side='left', padx=(0, 5))
        self.coach_cmb = ttk.Combobox(toolbar, width=5, state='readonly', font=self.font_regular)
        self.coach_cmb.pack(side='left', padx=(0, 15))
        self.coach_cmb.bind('<<ComboboxSelected>>', lambda e: self._on_coach_change())

        self.summary_lbl = tk.Label(toolbar, text='', bg=self.bg, fg=self.accent, font=self.font_bold)
        self.summary_lbl.pack(side='right')

    def _build_main_content(self):
        main = tk.Frame(self.root, bg=self.bg)
        main.pack(fill='both', expand=True, padx=10, pady=5)

        left_panel = tk.Frame(main, bg=self.panel_bg, width=150)
        left_panel.pack(side='left', fill='y', padx=(0, 8))
        left_panel.pack_propagate(False)
        self._build_actions_panel(left_panel)

        center_panel = tk.Frame(main, bg=self.panel_bg)
        center_panel.pack(side='left', fill='both', expand=True, padx=(0, 8))
        self._build_seat_panel(center_panel)

        right_panel = tk.Frame(main, bg=self.panel_bg, width=260)
        right_panel.pack(side='left', fill='y', padx=(0, 8))
        right_panel.pack_propagate(False)
        self._build_booking_panel(right_panel)

        admin_panel = tk.Frame(main, bg=self.panel_bg, width=160)
        admin_panel.pack(side='left', fill='y')
        admin_panel.pack_propagate(False)
        self._build_admin_panel(admin_panel)

    def _build_actions_panel(self, parent):
        tk.Label(parent, text='⚡ Actions', bg=self.panel_bg, fg=self.accent,
                font=self.font_bold).pack(anchor='w', padx=8, pady=(10, 8))

        actions = [
            ('📋 View Bookings', self._show_bookings),
            ('❌ Cancel Booking', self._cancel_booking),
            ('🎫 Print Ticket', self._print_ticket),
            ('📄 Export Text', self._export_ticket_text),
            ('🖼️ Export Image', self._export_ticket_image),
        ]

        for text, cmd in actions:
            btn = tk.Button(parent, text=text, command=cmd, bg=self.surface, fg='#e2e8f0',
                           font=self.font_small, anchor='w', padx=8, pady=4, relief='flat',
                           activebackground=self.accent, activeforeground='#0f172a')
            btn.pack(fill='x', padx=6, pady=2)

    def _build_seat_panel(self, parent):
        header = tk.Frame(parent, bg=self.panel_bg)
        header.pack(fill='x', padx=10, pady=(8, 4))

        tk.Label(header, text='🚃 Coach Layout', bg=self.panel_bg, fg=self.accent,
                font=self.font_bold).pack(side='left')

        legend = tk.Frame(header, bg=self.panel_bg)
        legend.pack(side='right')

        for color, label in [(self.window_color, 'Window'), (self.aisle_color, 'Aisle'),
                             (self.accent, 'Selected'), (self.good, 'Free'), (self.bad, 'Booked')]:
            tk.Label(legend, text='■', bg=self.panel_bg, fg=color, font=('Segoe UI', 10)).pack(side='left')
            tk.Label(legend, text=label, bg=self.panel_bg, fg='#94a3b8', font=('Segoe UI', 8)).pack(side='left', padx=(0, 8))

        self.seat_container = tk.Frame(parent, bg='#1f2937', relief='ridge', bd=2)
        self.seat_container.pack(fill='both', expand=True, padx=10, pady=(0, 8))

        coach_header = tk.Frame(self.seat_container, bg='#374151', height=25)
        coach_header.pack(fill='x')
        coach_header.pack_propagate(False)
        tk.Label(coach_header, text='◀ FRONT', bg='#374151', fg='#9ca3af',
                font=('Segoe UI', 8)).pack(side='left', padx=8)
        self.coach_lbl = tk.Label(coach_header, text='COACH 1', bg='#374151', fg='#e5e7eb',
                                  font=('Segoe UI Semibold', 9))
        self.coach_lbl.pack(side='left', expand=True)
        tk.Label(coach_header, text='REAR ▶', bg='#374151', fg='#9ca3af',
                font=('Segoe UI', 8)).pack(side='right', padx=8)

        self.seat_frame = tk.Frame(self.seat_container, bg='#1f2937')
        self.seat_frame.pack(fill='both', expand=True, padx=8, pady=8)

    def _build_booking_panel(self, parent):
        tk.Label(parent, text='📝 Booking Details', bg=self.panel_bg, fg=self.accent,
                font=self.font_bold).pack(anchor='w', padx=10, pady=(10, 8))

        form = tk.Frame(parent, bg=self.panel_bg)
        form.pack(fill='x', padx=10)

        tk.Label(form, text='Passenger Name', bg=self.panel_bg, fg='#94a3b8',
                font=self.font_small).pack(anchor='w')
        self.name_entry = tk.Entry(form, font=self.font_regular, bg=self.surface,
                                   fg='#e2e8f0', insertbackground='white', relief='flat')
        self.name_entry.pack(fill='x', pady=(2, 8))

        tk.Label(form, text='Phone Number', bg=self.panel_bg, fg='#94a3b8',
                font=self.font_small).pack(anchor='w')
        self.phone_entry = tk.Entry(form, font=self.font_regular, bg=self.surface,
                                    fg='#e2e8f0', insertbackground='white', relief='flat')
        self.phone_entry.pack(fill='x', pady=(2, 8))

        tk.Label(form, text='Selected Seats', bg=self.panel_bg, fg='#94a3b8',
                font=self.font_small).pack(anchor='w')
        self.selected_lbl = tk.Label(form, text='None', bg=self.surface, fg=self.accent,
                                     font=self.font_bold, pady=4, wraplength=220)
        self.selected_lbl.pack(fill='x', pady=(2, 8))

        self.total_lbl = tk.Label(form, text='💰 Total: ৳0.00', bg=self.panel_bg,
                                  fg=self.accent, font=('Segoe UI Semibold', 12))
        self.total_lbl.pack(anchor='w', pady=(4, 12))

        for text, cmd, bg in [
            ('✓ Book Seats', self._book_seats, self.accent),
            ('✕ Clear Selection', self._clear_selection, self.surface),
            ('💳 Pay & Confirm', self._pay_booking, self.good),
            ('🎫 Generate Ticket', self._generate_ticket, self.window_color),
        ]:
            btn = tk.Button(form, text=text, command=cmd, bg=bg,
                           fg='#0f172a' if bg == self.accent else '#e2e8f0',
                           font=self.font_regular, pady=6, relief='flat',
                           activebackground=self.accent_hover)
            btn.pack(fill='x', pady=3)

    def _build_admin_panel(self, parent):
        tk.Label(parent, text='🔧 Admin', bg=self.panel_bg, fg=self.accent,
                font=self.font_bold).pack(anchor='w', padx=8, pady=(10, 8))

        sections = [
            ('Trains', [
                ('+ Create', self._admin_create_train),
                ('✎ Update', self._admin_update_train),
                ('✕ Delete', self._admin_delete_train),
            ]),
            ('Bookings', [
                ('Move Seat', self._admin_move_seat),
                ('Delete', self._admin_delete_booking),
            ]),
            ('Tickets', [
                ('Del Text', self._admin_delete_ticket_text),
                ('Del Image', self._admin_delete_ticket_image),
            ]),
            ('Users', [
                ('Manage', self._admin_user_files),
            ]),
        ]

        for title, items in sections:
            tk.Label(parent, text=title, bg=self.panel_bg, fg='#64748b',
                    font=('Segoe UI', 8)).pack(anchor='w', padx=8, pady=(6, 2))
            for text, cmd in items:
                btn = tk.Button(parent, text=text, command=cmd, bg=self.surface, fg='#e2e8f0',
                               font=self.font_small, pady=2, relief='flat')
                btn.pack(fill='x', padx=6, pady=1)

    def _build_status_bar(self):
        status = tk.Frame(self.root, bg=self.panel_bg, height=28)
        status.pack(fill='x', side='bottom', padx=10, pady=(0, 10))
        status.pack_propagate(False)

        self.status_var = tk.StringVar(value='✓ Ready')
        tk.Label(status, textvariable=self.status_var, bg=self.panel_bg, fg=self.good,
                font=self.font_small).pack(side='left', padx=8, pady=4)

    def _refresh_train_list(self):
        trains = self.api.get_trains()
        vals = [f"{t['id']} - {t['name']} ({t['route']})" for t in trains]
        self.train_cmb['values'] = vals
        if vals:
            self.train_cmb.current(0)
            self._on_train_change()

    def _on_train_change(self):
        sel = self.train_cmb.get()
        if not sel:
            return
        self.current_train_id = sel.split(' ')[0]
        train = self.api.get_train(self.current_train_id)
        if train:
            self.coach_cmb['values'] = [str(i) for i in range(1, train['coaches'] + 1)]
            self.coach_cmb.current(0)
            self.current_coach = 1
        self._selected_seats.clear()
        self._update_seat_grid()

    def _on_coach_change(self):
        val = self.coach_cmb.get()
        if val:
            self.current_coach = int(val)
            self._selected_seats.clear()
            self._update_seat_grid()

    def _set_date(self):
        val = self.date_entry.get().strip()
        try:
            dt = datetime.datetime.strptime(val, '%Y-%m-%d').date()
            if dt < datetime.date.today():
                messagebox.showerror('Error', 'Cannot select past date')
                return
            self.current_date = val
            self._selected_seats.clear()
            self._update_seat_grid()
        except ValueError:
            messagebox.showerror('Error', 'Invalid date format. Use YYYY-MM-DD')

    def _date_prev(self):
        try:
            d = datetime.datetime.strptime(self.current_date, '%Y-%m-%d').date()
            nd = d - datetime.timedelta(days=1)
            if nd < datetime.date.today():
                messagebox.showwarning('Warning', 'Cannot select past date')
                return
            self.current_date = nd.strftime('%Y-%m-%d')
            self.date_entry.delete(0, 'end')
            self.date_entry.insert(0, self.current_date)
            self._selected_seats.clear()
            self._update_seat_grid()
        except Exception as e:
            self._set_status(f'Error: {e}')

    def _date_next(self):
        try:
            d = datetime.datetime.strptime(self.current_date, '%Y-%m-%d').date()
            nd = d + datetime.timedelta(days=1)
            self.current_date = nd.strftime('%Y-%m-%d')
            self.date_entry.delete(0, 'end')
            self.date_entry.insert(0, self.current_date)
            self._selected_seats.clear()
            self._update_seat_grid()
        except Exception as e:
            self._set_status(f'Error: {e}')

    def _update_seat_grid(self):
        if not self.current_train_id:
            return

        for w in self.seat_frame.winfo_children():
            w.destroy()

        seats = self.api.list_available_seats(self.current_train_id, self.current_date, self.current_coach)
        train = self.api.get_train(self.current_train_id)

        if not train or not seats:
            tk.Label(self.seat_frame, text='No seats available', bg='#1f2937', fg='#9ca3af').pack()
            return

        self.coach_lbl.config(text=f'COACH {self.current_coach}')

        center = tk.Frame(self.seat_frame, bg='#1f2937')
        center.pack(expand=True)

        headers = ['', 'A', 'B', '', 'C', 'D', '']
        for col, h in enumerate(headers):
            if col == 3:
                lbl = tk.Label(center, text='', bg='#1f2937', width=4)
            else:
                lbl = tk.Label(center, text=h, bg='#1f2937', fg='#9ca3af',
                              font=('Segoe UI Semibold', 10), width=5)
            lbl.grid(row=0, column=col, padx=1, pady=(0, 6))

        seats_per_row = 4
        total = len(seats)
        num_rows = (total + seats_per_row - 1) // seats_per_row
        seat_idx = 0

        for row_num in range(num_rows):
            grid_row = row_num + 1

            tk.Label(center, text=str(row_num + 1), bg='#1f2937', fg='#6b7280',
                    font=('Segoe UI', 9), width=3).grid(row=grid_row, column=0, padx=(0, 6))

            for col in range(2):
                if seat_idx < total:
                    s = seats[seat_idx]
                    seat_type = 'window' if col == 0 else 'aisle'
                    btn = self._create_seat_btn(center, s['seat'], s['available'], seat_type)
                    btn.grid(row=grid_row, column=col + 1, padx=2, pady=2)
                    seat_idx += 1

            aisle = tk.Frame(center, bg='#374151', width=28, height=30)
            aisle.grid(row=grid_row, column=3, padx=6, pady=2)
            aisle.grid_propagate(False)

            for col in range(2):
                if seat_idx < total:
                    s = seats[seat_idx]
                    seat_type = 'aisle' if col == 0 else 'window'
                    btn = self._create_seat_btn(center, s['seat'], s['available'], seat_type)
                    btn.grid(row=grid_row, column=col + 4, padx=2, pady=2)
                    seat_idx += 1

            tk.Label(center, text=str(row_num + 1), bg='#1f2937', fg='#6b7280',
                    font=('Segoe UI', 9), width=3).grid(row=grid_row, column=6, padx=(6, 0))

        booked = len([s for s in seats if not s['available']])
        free = total - booked
        price = train['base_price']
        sel_count = len(self._selected_seats)

        self.summary_lbl.config(text=f'💺 Free: {free}/{total} | Selected: {sel_count} | ৳{price:.0f}/seat')
        self.total_lbl.config(text=f'💰 Total: ৳{sel_count * price:.2f}')
        self.selected_lbl.config(text=', '.join(str(s) for s in sorted(self._selected_seats)) or 'None')

    def _create_seat_btn(self, parent, seat_num, available, seat_type):
        selected = seat_num in self._selected_seats

        if not available:
            color = self.bad
            text_color = '#ffffff'
            cursor = 'arrow'
        elif selected:
            color = self.accent
            text_color = '#0f172a'
            cursor = 'hand2'
        elif seat_type == 'window':
            color = self.window_color
            text_color = '#ffffff'
            cursor = 'hand2'
        else:
            color = self.aisle_color
            text_color = '#ffffff'
            cursor = 'hand2'

        btn = tk.Button(parent, text=str(seat_num), width=5, height=2,
                       bg=color, fg=text_color, bd=1,
                       relief='sunken' if not available else 'raised',
                       font=('Segoe UI Semibold', 9), cursor=cursor,
                       command=lambda s=seat_num, a=available: self._toggle_seat(s, a))
        return btn

    def _toggle_seat(self, seat, available):
        if not available:
            self._set_status('Seat already booked')
            return

        if seat in self._selected_seats:
            self._selected_seats.remove(seat)
        else:
            self._selected_seats.add(seat)

        self._update_seat_grid()

    def _book_seats(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()

        if not name or not phone:
            messagebox.showerror('Error', 'Please enter passenger name and phone')
            return

        if not self._selected_seats:
            messagebox.showerror('Error', 'Please select at least one seat')
            return

        if not self.current_train_id:
            messagebox.showerror('Error', 'Please select a train first')
            return

        if not self.api.check_api_connection():
            messagebox.showerror('Error', 'API server is not running!\nPlease start api_server.py first.')
            return

        errors = []
        booked = []

        for seat in sorted(self._selected_seats):
            try:
                bid, err = self.api.book(self.current_train_id, self.current_date,
                                         self.current_coach, seat, name, phone)
                if err:
                    errors.append(f'Seat {seat}: {err}')
                elif bid:
                    booked.append(bid)
                else:
                    errors.append(f'Seat {seat}: Unknown error')
            except Exception as e:
                errors.append(f'Seat {seat}: {str(e)}')

        self._selected_seats.clear()
        self._update_seat_grid()

        if booked:
            try:
                self.api.create_user_file(phone)
                self.api.update_user_file(phone)
            except:
                pass

            messagebox.showinfo('Success', f'Booked {len(booked)} seat(s):\n' + '\n'.join(booked))

        if errors:
            messagebox.showwarning('Some Failed', '\n'.join(errors))

    def _clear_selection(self):
        self._selected_seats.clear()
        self._update_seat_grid()

    def _pay_booking(self):
        phone = self.phone_entry.get().strip()
        if not phone:
            messagebox.showerror('Error', 'Enter phone number to mark as paid')
            return

        ok = self.api.mark_paid_by_phone(self.current_train_id, self.current_date, phone)
        if ok:
            messagebox.showinfo('Success', 'Marked as PAID')
            self._update_seat_grid()
        else:
            messagebox.showerror('Error', 'No bookings found or already paid')

    def _generate_ticket(self):
        phone = self.phone_entry.get().strip()
        if not phone:
            messagebox.showerror('Error', 'Enter phone number')
            return

        path = self.api.create_group_ticket(phone, self.current_train_id, self.current_date)
        if path:
            messagebox.showinfo('Success', f'Ticket saved:\n{path}')
        else:
            messagebox.showerror('Error', 'No bookings found')

    def _show_bookings(self):
        win = tk.Toplevel(self.root)
        win.title('All Bookings')
        win.geometry('950x550')
        win.configure(bg=self.panel_bg)

        search_frame = tk.Frame(win, bg=self.panel_bg)
        search_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(search_frame, text='🔍 Search:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(side='left', padx=(0, 8))

        search_entry = tk.Entry(search_frame, width=24, font=self.font_regular,
                               bg=self.surface, fg='#e2e8f0', insertbackground='white')
        search_entry.pack(side='left', padx=(0, 8))

        filter_var = tk.StringVar(value='All')
        filter_cmb = ttk.Combobox(search_frame, values=['All', 'Name', 'Phone', 'Booking ID', 'Train', 'Status'],
                                  state='readonly', width=12)
        filter_cmb.current(0)
        filter_cmb.pack(side='left', padx=(0, 8))

        cols = ('id', 'train', 'date', 'coach', 'seat', 'name', 'phone', 'price', 'status')
        tv = ttk.Treeview(win, columns=cols, show='headings', height=20)

        for col in cols:
            tv.heading(col, text=col.capitalize())
        tv.column('id', width=90, anchor='center')
        tv.column('train', width=80, anchor='center')
        tv.column('date', width=90, anchor='center')
        tv.column('coach', width=50, anchor='center')
        tv.column('seat', width=50, anchor='center')
        tv.column('name', width=150)
        tv.column('phone', width=100, anchor='center')
        tv.column('price', width=70, anchor='e')
        tv.column('status', width=80, anchor='center')

        scroll = ttk.Scrollbar(win, orient='vertical', command=tv.yview)
        tv.configure(yscrollcommand=scroll.set)

        tv.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=(0, 10))
        scroll.pack(side='left', fill='y', pady=(0, 10), padx=(0, 10))

        def populate(data):
            for i in tv.get_children():
                tv.delete(i)
            for b in sorted(data, key=lambda x: (x['date'], x['train_id'], x['coach'], x['seat'])):
                tv.insert('', 'end', values=(
                    b['booking_id'], b['train_id'], b['date'], b['coach'], b['seat'],
                    b['name'], b['phone'], f"৳{b['price']:.0f}", b['status']
                ))

        def do_search(*args):
            query = search_entry.get().strip().lower()
            filter_type = filter_cmb.get()
            all_items = self.api.list_all_bookings()

            if not query:
                populate(all_items)
                return

            filtered = []
            for b in all_items:
                match = False
                if filter_type == 'All':
                    match = (query in b['booking_id'].lower() or query in b['name'].lower() or
                            query in b['phone'].lower() or query in b['train_id'].lower() or
                            query in b['status'].lower())
                elif filter_type == 'Name':
                    match = query in b['name'].lower()
                elif filter_type == 'Phone':
                    match = query in b['phone'].lower()
                elif filter_type == 'Booking ID':
                    match = query in b['booking_id'].lower()
                elif filter_type == 'Train':
                    match = query in b['train_id'].lower()
                elif filter_type == 'Status':
                    match = query in b['status'].lower()

                if match:
                    filtered.append(b)

            populate(filtered)

        search_entry.bind('<KeyRelease>', do_search)
        filter_cmb.bind('<<ComboboxSelected>>', do_search)

        tk.Button(search_frame, text='Search', command=do_search, bg=self.accent, fg='#0f172a',
                 font=self.font_small, padx=10).pack(side='left', padx=(0, 5))
        tk.Button(search_frame, text='Clear', command=lambda: (search_entry.delete(0, 'end'), do_search()),
                 bg=self.surface, fg='#e2e8f0', font=self.font_small, padx=10).pack(side='left')

        populate(self.api.list_all_bookings())

    def _cancel_booking(self):
        bid = self._ask_input('Cancel Booking', 'Enter Booking ID:')
        if not bid:
            return

        booking = self.api.get_booking(bid)
        if not booking:
            messagebox.showerror('Error', f'Booking {bid} not found')
            return

        details = (f"Booking ID: {booking['booking_id']}\n"
                  f"Train: {booking['train_id']}\n"
                  f"Date: {booking['date']}\n"
                  f"Coach: {booking['coach']}, Seat: {booking['seat']}\n"
                  f"Passenger: {booking['name']}\n"
                  f"Phone: {booking['phone']}\n"
                  f"Status: {booking['status']}\n"
                  f"Price: ৳{booking['price']:.2f}")

        if booking['status'] == 'CANCELLED':
            messagebox.showinfo('Info', f'This booking is already cancelled.\n\n{details}')
            return

        if booking['status'] == 'BOOKED':
            if messagebox.askyesno('Confirm Cancel', f'Cancel this booking?\n\n{details}'):
                ok = self.api.cancel(bid)
                if ok:
                    messagebox.showinfo('Success', 'Booking cancelled (status changed to CANCELLED)')
                    self._update_seat_grid()
                else:
                    messagebox.showerror('Error', 'Could not cancel booking')
        else:
            choice = messagebox.askyesnocancel(
                'Cancel Paid Booking',
                f'This booking is PAID.\n\n{details}\n\n'
                f'Yes = Cancel (change to CANCELLED)\n'
                f'No = Delete permanently\n'
                f'Cancel = Do nothing'
            )
            if choice is True:
                ok = self.api.cancel(bid)
                if not ok:
                    messagebox.showinfo('Info', 'Cannot soft-cancel PAID booking. Use Delete instead.')
            elif choice is False:
                ok, err = self.api.delete_booking(bid)
                if ok:
                    messagebox.showinfo('Success', 'Booking deleted permanently')
                    self._update_seat_grid()
                else:
                    messagebox.showerror('Error', f'Could not delete: {err}')

    def _print_ticket(self):
        bid = self._ask_input('Print Ticket', 'Enter Booking ID:')
        if not bid:
            return

        path = self.api.create_ticket_text_file(bid)
        if path:
            try:
                os.startfile(path, 'print')
                messagebox.showinfo('Success', 'Sent to printer')
            except:
                messagebox.showinfo('Info', f'Ticket saved: {path}')
        else:
            messagebox.showerror('Error', 'Booking not found')

    def _export_ticket_text(self):
        bid = self._ask_input('Export Ticket Text', 'Enter Booking ID:')
        if not bid:
            return

        path = self.api.create_ticket_text_file(bid)
        if path:
            messagebox.showinfo('Success', f'Saved: {path}')
        else:
            messagebox.showerror('Error', 'Booking not found')

    def _export_ticket_image(self):
        bid = self._ask_input('Export Ticket Image', 'Enter Booking ID:')
        if not bid:
            return

        path = self.api.create_ticket_image_file(bid)
        if path:
            messagebox.showinfo('Success', f'Saved: {path}')
        else:
            messagebox.showerror('Error', 'Failed (check PIL/qrcode installed)')

    def _admin_create_train(self):
        win = tk.Toplevel(self.root)
        win.title('Create Train')
        win.configure(bg=self.panel_bg)

        fields = [('ID', 'id'), ('Name', 'name'), ('Route', 'route'),
                 ('Coaches', 'coaches'), ('Seats/Coach', 'seats'), ('Base Price', 'price')]
        entries = {}

        for i, (label, key) in enumerate(fields):
            tk.Label(win, text=label, bg=self.panel_bg, fg='#e2e8f0').grid(row=i, column=0, padx=8, pady=4, sticky='w')
            e = tk.Entry(win, width=28, bg=self.surface, fg='#e2e8f0')
            e.grid(row=i, column=1, padx=8, pady=4)
            entries[key] = e

        def create():
            try:
                ok, err = self.api.create_train(
                    entries['id'].get().strip(),
                    entries['name'].get().strip(),
                    entries['route'].get().strip(),
                    int(entries['coaches'].get()),
                    int(entries['seats'].get()),
                    float(entries['price'].get())
                )
                if ok:
                    messagebox.showinfo('Success', 'Train created')
                    self._refresh_train_list()
                    win.destroy()
                else:
                    messagebox.showerror('Error', err)
            except ValueError:
                messagebox.showerror('Error', 'Invalid numeric values')

        tk.Button(win, text='Create', command=create, bg=self.accent, fg='#0f172a',
                 font=self.font_regular).grid(row=len(fields), column=0, columnspan=2, pady=10, padx=8, sticky='we')

    def _admin_update_train(self):
        win = tk.Toplevel(self.root)
        win.title('Update Train')
        win.configure(bg=self.panel_bg)

        tk.Label(win, text='Train ID', bg=self.panel_bg, fg='#e2e8f0').grid(row=0, column=0, padx=8, pady=4, sticky='w')
        tid_entry = tk.Entry(win, width=24, bg=self.surface, fg='#e2e8f0')
        tid_entry.grid(row=0, column=1, padx=8, pady=4)

        tk.Label(win, text='Field', bg=self.panel_bg, fg='#e2e8f0').grid(row=1, column=0, padx=8, pady=4, sticky='w')
        field_cmb = ttk.Combobox(win, values=['name', 'route', 'coaches', 'seats_per_coach', 'base_price'], state='readonly')
        field_cmb.grid(row=1, column=1, padx=8, pady=4)

        tk.Label(win, text='Value', bg=self.panel_bg, fg='#e2e8f0').grid(row=2, column=0, padx=8, pady=4, sticky='w')
        val_entry = tk.Entry(win, width=24, bg=self.surface, fg='#e2e8f0')
        val_entry.grid(row=2, column=1, padx=8, pady=4)

        def update():
            tid = tid_entry.get().strip()
            field = field_cmb.get()
            val = val_entry.get().strip()
            if not all([tid, field, val]):
                return
            ok, err = self.api.update_train(tid, **{field: val})
            if ok:
                messagebox.showinfo('Success', 'Train updated')
                self._refresh_train_list()
                win.destroy()
            else:
                messagebox.showerror('Error', err)

        tk.Button(win, text='Update', command=update, bg=self.accent, fg='#0f172a').grid(row=3, column=0, columnspan=2, pady=10, padx=8, sticky='we')

    def _admin_delete_train(self):
        tid = self._ask_input('Delete Train', 'Enter Train ID:')
        if not tid:
            return
        ok, err = self.api.delete_train(tid)
        if ok:
            messagebox.showinfo('Success', 'Train deleted')
            self._refresh_train_list()
        else:
            messagebox.showerror('Error', err)

    def _admin_move_seat(self):
        win = tk.Toplevel(self.root)
        win.title('Move Booking to Different Seat')
        win.geometry('400x280')
        win.configure(bg=self.panel_bg)

        tk.Label(win, text='🔄 Move Booking to New Seat', bg=self.panel_bg, fg=self.accent,
                font=self.font_bold).pack(pady=(15, 10))

        form = tk.Frame(win, bg=self.panel_bg)
        form.pack(fill='x', padx=20, pady=10)

        tk.Label(form, text='Booking ID:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=0, column=0, sticky='w', pady=5)
        bid_entry = tk.Entry(form, width=20, bg=self.surface, fg='#e2e8f0',
                            font=self.font_regular, insertbackground='white')
        bid_entry.grid(row=0, column=1, padx=(10, 0), pady=5)

        tk.Label(form, text='New Coach:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=1, column=0, sticky='w', pady=5)
        coach_entry = tk.Entry(form, width=20, bg=self.surface, fg='#e2e8f0',
                              font=self.font_regular, insertbackground='white')
        coach_entry.grid(row=1, column=1, padx=(10, 0), pady=5)

        tk.Label(form, text='New Seat:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).grid(row=2, column=0, sticky='w', pady=5)
        seat_entry = tk.Entry(form, width=20, bg=self.surface, fg='#e2e8f0',
                             font=self.font_regular, insertbackground='white')
        seat_entry.grid(row=2, column=1, padx=(10, 0), pady=5)

        tk.Label(win, text='This will move the booking to a new coach/seat\nif the new seat is available.',
                bg=self.panel_bg, fg='#94a3b8', font=self.font_small).pack(pady=10)

        def do_move():
            booking_id = bid_entry.get().strip()
            new_coach = coach_entry.get().strip()
            new_seat = seat_entry.get().strip()

            if not booking_id or not new_coach or not new_seat:
                messagebox.showwarning('Warning', 'Please fill all fields')
                return

            try:
                new_coach = int(new_coach)
                new_seat = int(new_seat)
            except ValueError:
                messagebox.showerror('Error', 'Coach and Seat must be numbers')
                return

            booking = self.api.get_booking(booking_id)
            if not booking:
                messagebox.showerror('Error', f'Booking {booking_id} not found')
                return

            seats = self.api.list_available_seats(booking['train_id'], booking['date'], new_coach)
            if not seats:
                messagebox.showerror('Error', 'Could not get seat availability')
                return

            seat_info = next((s for s in seats if s['seat'] == new_seat), None)
            if not seat_info:
                messagebox.showerror('Error', f'Seat {new_seat} does not exist in coach {new_coach}')
                return

            if not seat_info['available']:
                messagebox.showerror('Error', f'Seat {new_seat} in coach {new_coach} is already booked')
                return

            old_name = booking['name']
            old_phone = booking['phone']
            old_status = booking['status']

            ok, err = self.api.delete_booking(booking_id)
            if not ok:
                messagebox.showerror('Error', f'Could not delete old booking: {err}')
                return

            new_bid, err = self.api.book(booking['train_id'], booking['date'],
                                         new_coach, new_seat, old_name, old_phone)

            if err:
                messagebox.showerror('Error', f'Could not create new booking: {err}\n\nOld booking was deleted!')
                return

            if old_status == 'PAID':
                self.api.mark_paid(new_bid)

            messagebox.showinfo('Success',
                f'Booking moved successfully!\n\n'
                f'Old: {booking_id} (deleted)\n'
                f'New: {new_bid}\n\n'
                f'Coach {new_coach}, Seat {new_seat}')

            self._update_seat_grid()
            win.destroy()

        btn_frame = tk.Frame(win, bg=self.panel_bg)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text='🔄 Move Seat', command=do_move, bg=self.accent, fg='#0f172a',
                 font=self.font_regular, padx=20, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Cancel', command=win.destroy, bg=self.surface, fg='#e2e8f0',
                 font=self.font_regular, padx=20, pady=5).pack(side='left', padx=5)

    def _admin_delete_booking(self):
        bid = self._ask_input('Delete Booking', 'Enter Booking ID:')
        if not bid:
            return
        ok, err = self.api.delete_booking(bid)
        if ok:
            messagebox.showinfo('Success', 'Booking deleted')
            self._update_seat_grid()
        else:
            messagebox.showerror('Error', err)

    def _admin_delete_ticket_text(self):
        bid = self._ask_input('Delete Ticket Text', 'Enter Booking ID:')
        if not bid:
            return
        ok = self.api.delete_ticket_text_file(bid)
        messagebox.showinfo('Result', 'Deleted' if ok else 'Not found')

    def _admin_delete_ticket_image(self):
        bid = self._ask_input('Delete Ticket Image', 'Enter Booking ID:')
        if not bid:
            return
        ok = self.api.delete_ticket_image_file(bid)
        messagebox.showinfo('Result', 'Deleted' if ok else 'Not found')

    def _admin_user_files(self):
        win = tk.Toplevel(self.root)
        win.title('User File Management')
        win.geometry('500x400')
        win.configure(bg=self.panel_bg)

        tk.Label(win, text='👤 User File Management', bg=self.panel_bg, fg=self.accent,
                font=self.font_bold).pack(pady=(10, 5))

        tk.Label(win, text='Manage individual user booking history files',
                bg=self.panel_bg, fg='#94a3b8', font=self.font_small).pack(pady=(0, 10))

        input_frame = tk.Frame(win, bg=self.panel_bg)
        input_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(input_frame, text='Phone Number:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_regular).pack(side='left', padx=(0, 10))
        phone_entry = tk.Entry(input_frame, width=20, bg=self.surface, fg='#e2e8f0',
                              font=self.font_regular, insertbackground='white')
        phone_entry.pack(side='left', padx=(0, 10))

        current_phone = self.phone_entry.get().strip()
        if current_phone:
            phone_entry.insert(0, current_phone)

        btn_frame = tk.Frame(win, bg=self.panel_bg)
        btn_frame.pack(fill='x', padx=20, pady=10)

        content_frame = tk.Frame(win, bg=self.panel_bg)
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Label(content_frame, text='User File Content:', bg=self.panel_bg, fg='#e2e8f0',
                font=self.font_bold).pack(anchor='w')

        content_text = tk.Text(content_frame, height=12, bg=self.surface, fg='#e2e8f0',
                              font=('Consolas', 9), relief='flat', wrap='word')
        content_text.pack(fill='both', expand=True, pady=(5, 0))

        def do_view():
            phone = phone_entry.get().strip()
            if not phone:
                messagebox.showwarning('Warning', 'Enter phone number')
                return
            content = self.api.get_user_file(phone)
            content_text.delete('1.0', 'end')
            if content:
                content_text.insert('1.0', content)
            else:
                content_text.insert('1.0', f'No user file found for {phone}')

        def do_create():
            phone = phone_entry.get().strip()
            if not phone:
                messagebox.showwarning('Warning', 'Enter phone number')
                return
            ok, msg = self.api.create_user_file(phone)
            if ok:
                messagebox.showinfo('Success', f'User file created for {phone}')
                do_view()
            else:
                messagebox.showerror('Error', msg)

        def do_update():
            phone = phone_entry.get().strip()
            if not phone:
                messagebox.showwarning('Warning', 'Enter phone number')
                return
            ok, msg = self.api.update_user_file(phone)
            if ok:
                messagebox.showinfo('Success', f'User file updated with booking history')
                do_view()
            else:
                messagebox.showerror('Error', msg)

        def do_delete():
            phone = phone_entry.get().strip()
            if not phone:
                messagebox.showwarning('Warning', 'Enter phone number')
                return
            if messagebox.askyesno('Confirm', f'Delete user file for {phone}?'):
                ok, msg = self.api.delete_user_file(phone)
                if ok:
                    messagebox.showinfo('Success', f'User file deleted')
                    content_text.delete('1.0', 'end')
                else:
                    messagebox.showerror('Error', msg)

        tk.Button(btn_frame, text='📖 View', command=do_view, bg=self.window_color, fg='#ffffff',
                 font=self.font_regular, padx=12, pady=4).pack(side='left', padx=4)
        tk.Button(btn_frame, text='➕ Create', command=do_create, bg=self.good, fg='#0f172a',
                 font=self.font_regular, padx=12, pady=4).pack(side='left', padx=4)
        tk.Button(btn_frame, text='🔄 Update', command=do_update, bg=self.accent, fg='#0f172a',
                 font=self.font_regular, padx=12, pady=4).pack(side='left', padx=4)
        tk.Button(btn_frame, text='🗑️ Delete', command=do_delete, bg=self.bad, fg='#ffffff',
                 font=self.font_regular, padx=12, pady=4).pack(side='left', padx=4)

        tk.Label(win, text='User files store booking history per phone number',
                bg=self.panel_bg, fg='#64748b', font=('Segoe UI', 8)).pack(side='bottom', pady=5)

    def _ask_input(self, title, prompt):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=self.panel_bg)
        win.grab_set()

        tk.Label(win, text=prompt, bg=self.panel_bg, fg='#e2e8f0').pack(padx=10, pady=(10, 5))
        entry = tk.Entry(win, width=28, bg=self.surface, fg='#e2e8f0')
        entry.pack(padx=10, pady=5)
        entry.focus_set()

        result = {'value': None}

        def submit():
            result['value'] = entry.get().strip()
            win.destroy()

        entry.bind('<Return>', lambda e: submit())
        tk.Button(win, text='OK', command=submit, bg=self.accent, fg='#0f172a', padx=20).pack(pady=10)

        win.wait_window()
        return result['value']

    def _set_status(self, msg):
        self.status_var.set(msg)


def start_api_server():
    import threading

    def run_server():
        try:
            import uvicorn
            import api_server
            uvicorn.run(api_server.app, host="127.0.0.1", port=5000, log_level="warning")
        except Exception as e:
            print(f"Server error: {e}")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    return server_thread


def main():
    import time

    print("=" * 60)
    print("       🚂 BANGLADESH RAILWAY - TICKET BOOKING SYSTEM")
    print("=" * 60)

    api = TrainAPIClient()

    if not api.check_api_connection():
        print("\n⚠️  API server not running, starting automatically...")
        start_api_server()

        for i in range(10):
            time.sleep(1)
            print(f"   Waiting for server... ({i+1}/10)")
            if api.check_api_connection():
                print("   ✓ Server started!")
                break
        else:
            print("   ✗ Could not start server")
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Server Error",
                "Could not start the API server.\n\n"
                "Try running api_server.py manually first."
            )
            return

    print("✓ Connected to API server")
    print("  Starting GUI...")

    root = tk.Tk()
    app = TrainBookingApp(root, api)
    root.mainloop()


if __name__ == '__main__':
    main()

