# HPLC_ChartRecorder.py
# Python 3.10
# This script collects data from the serial port
# Intended for using cheap ADCs as a chart-recorder substitute
# For use with old HPLCs
# Mostafa Hagar | 2023

# GUI packages
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from ttkthemes import ThemedTk
from threading import Thread
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Data Logic
from collections import defaultdict
import serial
import time
import csv
import re

# File I/O
import os
import sys

# Hard-coded Config Values
# TODO: Make the program load these from a config file
BAUD_RATE = 115200
TIMEOUT = 1
FILENAME = 'temp.csv'
ACTIVE_CHANNELS = [1, 8]
TOTAL_CHANNEL_NUM = 10


class ChartRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Chart Recorder")

        self.initialize_flags()

        ### TKINTER GUI ###
        # SERIAL PORT
        self.port_frame = ttk.LabelFrame(self.root, text="Serial Port Settings")
        self.port_frame.pack(padx=1, pady=1, fill="x", expand=False)

        # Label
        self.port_label = ttk.Label(self.port_frame, text="Serial Port:")
        self.port_label.grid(row=0, column=0, padx=2, pady=5, sticky="w")

        # Text field
        self.port_field = ttk.Entry(self.port_frame)
        self.port_field.insert(0, "/dev/ttyUSB0")
        self.port_field.grid(row=0, column=1, padx=2, pady=5, sticky="w")

        # Connect Button
        self.port_connect_btn = ttk.Button(self.port_frame,
                                           text="Connect",
                                           command=self.connect_serial)
        self.port_connect_btn.grid(row=0, column=2, padx=2, pady=5)

        # Port Status Readout
        self.port_status_label = ttk.Label(self.port_frame,
                                           text=f"Status: Disconnected")
        self.port_status_label.grid(row=0, column=3, padx=2, pady=5)

        # CONTROLS
        self.controls_frame = ttk.LabelFrame(self.root, text="Controls")
        self.controls_frame.pack(padx=1, pady=1, fill="x", expand=False)

        # Save Button
        self.save_btn = ttk.Button(self.controls_frame,
                                   text="Save Recording",
                                   command=self.save_data)
        self.save_btn.grid(row=0, column=0, padx=2, pady=5, sticky="e")

        # Load Button
        self.load_btn = ttk.Button(self.controls_frame,
                                   text="Load Recording",
                                   command=self.load_data)
        self.load_btn.grid(row=0, column=1, padx=2, pady=5, sticky="e")

        # Reset View Button
        self.unlock_view_btn = ttk.Button(self.controls_frame,
                                   text="Unlock view",
                                   command=self.unlock_view)
        self.unlock_view_btn.grid(row=0, column=2, padx=2, pady=5, sticky="e")

        # Inject Button
        self.inject_btn = ttk.Button(self.controls_frame,
                            text="Inject",
                            command=self.inject)
        self.inject_btn.grid(row=0, column=4, padx=100, pady=5, sticky="e")

        # Stop Button
        self.stop_btn = ttk.Button(self.controls_frame,
                                   text="Stop",
                                   command=self.stop)
        self.stop_btn.grid(row=0, column=5, padx=2, pady=5, sticky="e")


        # DATA PLOT
        self.plot_frame = ttk.LabelFrame(self.root, text="Plot")
        self.plot_frame.pack(padx=2, pady=2, fill="both", expand=True)
        self.initialize_plot()

    def initialize_flags(self):
        # Flags and data objects
        self.streaming = False
        self.viewlock = True
        self.ser = serial.Serial()

    
    def initialize_plot(self):
        self.plots_dict = {}
        self.axes_dict = {}

        plt.style.use('ggplot')

        self.fig = Figure(figsize=(8,6))
        self.fig.subplots_adjust(left=0, right=1, top=0.95, bottom=0.05)
        for channel in ACTIVE_CHANNELS:
            ax = self.fig.add_subplot(len(ACTIVE_CHANNELS),
                                      1,
                                      ACTIVE_CHANNELS.index(channel) + 1)
            self.axes_dict[channel] = ax

            plot, = ax.plot([0], [0], label=f"Channel {channel}")
            self.plots_dict[channel] = plot


        for k in list(self.axes_dict.keys())[1:]:
            self.axes_dict[k].sharex(self.axes_dict[ACTIVE_CHANNELS[0]])

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill="both", expand=1)
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


    def connect_serial(self):
        if self.ser.is_open:
            self.ser.close()
            self.port_connect_btn.configure(text="Connect")
            self.port_status_label.configure(text="Status: Disconnected")
            try: self.stop()
            except: pass
            return

        port_dir = self.port_field.get()
        try:
            self.ser = serial.Serial(port_dir,
                                     baudrate=BAUD_RATE,
                                     timeout=TIMEOUT)
        except serial.SerialException as e:
            messagebox.showerror("Serial Port Issue",
                                f"{e} \n \n"\
                                 "Hint: if permission denied, try "\
                                 "$ sudo chmod o+rw /dev/ttyUSB0")
            return

        self.port_status_label.configure(text="Status: Connected")
        self.port_connect_btn.configure(text="Disconnect")

    def save_data(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[(".csv files", "*.csv"),
                                                       ("All files", "*.*")])

        if path:
            with open(path, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(self.temp_record.keys()) # Write Header
                csvwriter.writerows(zip(*self.temp_record.values())) # Values
                

    def load_data(self):
        path = filedialog.askopenfilename(title="Open File",
                                          filetypes=[(".csv files", "*.csv"),
                                                     ("All files", "*.*")])
        with open(path, 'r', newline='') as csvfile:
            csvreader = csv.DictReader(csvfile)
            dict_of_lists = defaultdict(list)
            for line_dict in csvreader:
                for k, v in line_dict.items():
                    if k != 'Time':
                        k = int(k)
                    
                    dict_of_lists[k].append(float(v))
            
            self.temp_record = dict_of_lists
            print(self.temp_record)
            self.update_plot(None)
            
        

    def unlock_view(self):
        if self.viewlock == False:
            self.viewlock = True
            self.unlock_view_btn.configure(text="Lock View")
        else:
            self.viewlock = False
            self.unlock_view_btn.configure(text="Unlock View")


    def inject(self):
        if not self.ser.is_open:
            return
        
        try:  # This block is funny but prevents stopping an unstarted run
            self.stop()
        except AttributeError:
            pass

        self.temp_record = {key: [] for key in range(TOTAL_CHANNEL_NUM)}
        self.temp_record['Time'] = []
        self.time0 = time.time()
        
        empty_data_chunk = []
        self.streaming_thread = Thread(target=self.stream, args=[empty_data_chunk])
        self.streaming_thread.start()
        self.streaming = True
        print("streaming = True")
        
        time.sleep(1)
        self.animation = FuncAnimation(self.fig, self.update_plot, interval=1000)
        self.animation.event_source.start()
        self.canvas.draw()


    def stream(self, data_chunk):
        while True:
            line = self.ser.readline()
            data_chunk.append(line)
            if line == b'\r\n':
                # time.sleep(0.5)
                self.dump(data_chunk)
                data_chunk = []
            if self.streaming == False:
                break


    def dump(self, data_chunk):
        row = {}
        for datum in data_chunk:
            text = datum.decode()

            # Match channel number (i.e. `CH5`):
            match_ch_num = re.search(r'CH(\d+)', text)
            if match_ch_num:
                ch_number = int(match_ch_num.group(1))
            else: break
            
            # Match voltage (i.e. '1.454V'):
            match_volt = re.search(r'(\d+\.\d+)V', text)
            if match_volt:
                volt = float(match_volt.group(1))
            else: break

            row[ch_number] = volt
            row['Time'] = time.time() - self.time0

        # Append row to temp_record
        for k in row.keys():
            self.temp_record[k].append(row[k])


    def update_plot(self, _):        
        x = self.temp_record['Time']
        for channel in ACTIVE_CHANNELS:            
            y = self.temp_record[channel]

            plot = self.plots_dict[channel]
            plot.set_xdata(x)
            plot.set_ydata(y)
            
            if self.viewlock:
                ax = self.axes_dict[channel]
                ax.set_xlim(min(x)-1, max(x)+1)
                ax.set_ylim(min(y)-0.1, max(y)+0.1)

        self.canvas.draw()


    def stop(self):
        self.streaming = False
        self.animation.event_source.stop()
        
        try:
            if self.streaming_thread.is_alive():
                self.streaming_thread.join() # Wait for thread to finish
        except (NameError, AttributeError) as e:
            print("No ongoing stream")


    def close_app(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = ChartRecorderApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()
    
    sys.exit()