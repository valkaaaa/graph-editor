import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from translator import tr


PAGE_SIZES_MM = {
    'A3':     (297, 420),
    'A4':     (210, 297),
    'A5':     (148, 210),
    'Letter': (216, 279),
    'Legal':  (216, 356),
}


class PdfExportMixin:

    def export_pdf(self):
        if not hasattr(self, 'fig'):
            return
        win = tk.Toplevel(self.root)
        win.title(tr.t('msg.pdf_title'))
        win.transient(self.root)
        win.geometry('400x430')

        size_var       = tk.StringVar(value='A4')
        orient_var     = tk.StringVar(value='portrait')
        margin_var     = tk.IntVar(value=10)
        dpi_var        = tk.IntVar(value=300)
        transparent_var = tk.BooleanVar(value=False)

        f1 = ttk.Frame(win, padding=8); f1.pack(fill=tk.X)
        ttk.Label(f1, text=tr.t('msg.pdf_page')).pack(anchor=tk.W)
        ttk.Combobox(f1, textvariable=size_var,
                     values=list(PAGE_SIZES_MM.keys()),
                     state='readonly', width=12).pack(anchor=tk.W, pady=2)

        f2 = ttk.Frame(win, padding=8); f2.pack(fill=tk.X)
        ttk.Label(f2, text=tr.t('msg.pdf_orientation')).pack(anchor=tk.W)
        ttk.Radiobutton(f2, text='Portrait', value='portrait',
                        variable=orient_var).pack(anchor=tk.W)
        ttk.Radiobutton(f2, text='Landscape', value='landscape',
                        variable=orient_var).pack(anchor=tk.W)

        f3 = ttk.Frame(win, padding=8); f3.pack(fill=tk.X)
        ttk.Label(f3, text=tr.t('msg.pdf_margin')).pack(anchor=tk.W)
        ttk.Spinbox(f3, from_=0, to=50, textvariable=margin_var,
                    width=6).pack(anchor=tk.W, pady=2)
        ttk.Label(f3, text=tr.t('msg.pdf_dpi')).pack(anchor=tk.W, pady=(8, 0))
        ttk.Spinbox(f3, from_=72, to=600, increment=50,
                    textvariable=dpi_var, width=6).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(f3, text=tr.t('msg.pdf_transparent'),
                        variable=transparent_var).pack(anchor=tk.W, pady=4)

        def do_export():
            try:
                w_mm, h_mm = PAGE_SIZES_MM[size_var.get()]
                if orient_var.get() == 'landscape':
                    w_mm, h_mm = h_mm, w_mm
                w_in = w_mm / 25.4
                h_in = h_mm / 25.4
                m_in = margin_var.get() / 25.4

                path = filedialog.asksaveasfilename(
                    defaultextension='.pdf',
                    filetypes=[('PDF', '*.pdf')])
                if not path:
                    return

                old_size = self.fig.get_size_inches()
                try:
                    self.fig.set_size_inches(w_in, h_in)
                    self.fig.subplots_adjust(
                        left=m_in / w_in,
                        right=1 - m_in / w_in,
                        bottom=m_in / h_in,
                        top=1 - m_in / h_in)
                    self.fig.savefig(path,
                                      dpi=dpi_var.get(),
                                      transparent=transparent_var.get())
                finally:
                    self.fig.set_size_inches(*old_size)
                    self._redraw()

                win.destroy()
                self._show_history(tr.t('hist.exported_pdf',
                                         name=os.path.basename(path)))
                messagebox.showinfo(tr.t('msg.done'),
                                     tr.t('msg.pdf_exported', path=path))
            except Exception as e:
                messagebox.showerror(tr.t('msg.error'), str(e))

        bf = ttk.Frame(win, padding=8); bf.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(bf, text=tr.t('msg.pdf_cancel'),
                    command=win.destroy).pack(side=tk.RIGHT, padx=2)
        ttk.Button(bf, text=tr.t('msg.pdf_export'),
                    command=do_export).pack(side=tk.RIGHT, padx=2)