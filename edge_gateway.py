#!/usr/bin/env python3
import os
import sys
import time
import math
import json
import argparse
import threading
import numpy as np
import websocket

# Dynamic import of serial
try:
    import serial
except ImportError:
    serial = None

current_sim_mode = 'N'  # 'N' = normal, 'B' = bradycardia, 'T' = tachycardia
serial_session = None

def clean_line_and_parse(line):
    line = line.strip().replace('"', '')
    if not line:
        return None
    parts = line.split(',')
    if any(h in parts[0] for h in ['time_ms', 'timestamp', 'az', 'ax', 'ay', 'occupancy', 'temp', 'humidity']):
        return None
    try:
        vals = []
        for p in parts:
            p_clean = p.strip().lower()
            if p_clean in ('nan', 'nanf'):
                vals.append(float('nan'))
            elif p_clean in ('inf', 'inff', '+inf', '+inff'):
                vals.append(float('inf'))
            elif p_clean in ('-inf', '-inff'):
                vals.append(float('-inf'))
            else:
                vals.append(float(p))

        if len(vals) >= 4 and not all(np.isfinite(v) for v in vals[:4]):
            return None

        if len(vals) == 1:
            return (time.time() * 1000.0, 0.0, 0.0, vals[0], 1, float('nan'), float('nan'))
        elif len(vals) == 2:
            return (vals[0], 0.0, 0.0, vals[1], 1, float('nan'), float('nan'))
        elif len(vals) == 4:
            return (vals[0], vals[1], vals[2], vals[3], 1, float('nan'), float('nan'))
        elif len(vals) >= 7:
            if not math.isnan(vals[4]):
                occ = int(np.clip(vals[4], 0.0, 1.0))
            else:
                occ = 0
            return (vals[0], vals[1], vals[2], vals[3], occ, vals[5], vals[6])
    except (ValueError, IndexError):
        pass
    return None

def start_ws_sender(ws_url, port, baudrate, mode):
    global current_sim_mode, serial_session
    
    def on_message(ws, message):
        global current_sim_mode, serial_session
        try:
            payload = json.loads(message)
            cmd = payload.get("command")
            if cmd in ('N', 'B', 'T'):
                current_sim_mode = cmd
                print(f"Server override command set simulation mode to: {cmd}")
                if serial_session and serial_session.is_open:
                    serial_session.write(cmd.encode('utf-8'))
        except Exception as e:
            print(f"Error handling server command: {e}")

    def on_error(ws, error):
        print(f"WebSocket Error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print("WebSocket Connection Closed. Reconnecting in 3 seconds...")
        time.sleep(3)

    def on_open(ws):
        print("Connected to WebSocket Server successfully.")
        
        # Start a thread to read and stream data
        def data_streamer():
            global serial_session
            if mode == 'serial' and serial is not None:
                print(f"Connecting to serial port {port} at {baudrate} baud...")
                try:
                    serial_session = serial.Serial(port, baudrate, timeout=1.0)
                    serial_session.reset_input_buffer()
                    print("Serial port connection established.")
                except Exception as e:
                    print(f"Error opening serial port: {e}. Falling back to simulation.")
                    run_simulation(ws)
                    return
                
                while ws.sock and ws.sock.connected:
                    try:
                        if serial_session.in_waiting > 0:
                            line = serial_session.readline().decode('utf-8', errors='ignore')
                            parsed = clean_line_and_parse(line)
                            if parsed:
                                t_ms, ax, ay, az, occupancy, temp, humidity = parsed
                                payload = {
                                    "time_ms": int(t_ms),
                                    "ax": ax,
                                    "ay": ay,
                                    "az": az,
                                    "occupancy": occupancy,
                                    "temp": temp if np.isfinite(temp) else None,
                                    "humidity": humidity if np.isfinite(humidity) else None
                                }
                                ws.send(json.dumps(payload))
                        else:
                            time.sleep(0.01)
                    except Exception as e:
                        time.sleep(0.01)
            else:
                run_simulation(ws)

        threading.Thread(target=data_streamer, daemon=True).start()

    def run_simulation(ws):
        print("Simulated Data Generator running...")
        start_time = time.time()
        dt = 0.01  # 100 Hz simulation
        while ws.sock and ws.sock.connected:
            try:
                time.sleep(dt)
                curr_time = time.time()
                t_ms = int((curr_time - start_time) * 1000)
                
                # Target BPM
                if current_sim_mode == 'B':
                    target_bpm = 42.0
                elif current_sim_mode == 'T':
                    target_bpm = 145.0
                else:
                    target_bpm = 72.0
                
                freq = target_bpm / 60.0
                cycle_t = (curr_time - start_time) % 60.0
                occupancy = 1 if cycle_t < 45.0 else 0
                
                bcg = 15.0 * np.sin(2 * np.pi * freq * (t_ms / 1000.0)) + \
                      5.0 * np.sin(2 * np.pi * 2 * freq * (t_ms / 1000.0))
                if occupancy == 0:
                    bcg = 0.0
                    
                ax = -110.0 + bcg * 0.5 + np.random.normal(0, 3.0)
                ay = 95.0 + bcg * 0.3 + np.random.normal(0, 2.0)
                az = 650.0 + bcg * 1.0 + np.random.normal(0, 4.0)
                
                if 30.0 < cycle_t < 40.0:
                    temp = 36.5
                    humidity = 82.5
                else:
                    temp = 29.4 + 0.5 * np.sin(2 * np.pi * (t_ms / 60000.0))
                    humidity = 71.2 + 2.0 * np.cos(2 * np.pi * (t_ms / 60000.0))
                
                if 10.0 < cycle_t < 12.0:
                    temp = float('nan')
                    humidity = float('nan')
                    
                payload = {
                    "time_ms": t_ms,
                    "ax": ax,
                    "ay": ay,
                    "az": az,
                    "occupancy": occupancy,
                    "temp": temp if np.isfinite(temp) else None,
                    "humidity": humidity if np.isfinite(humidity) else None
                }
                ws.send(json.dumps(payload))
            except Exception as e:
                time.sleep(0.1)

    while True:
        try:
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            print(f"WebSocket client loop exception: {e}")
            time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BCG Edge WebSocket Gateway")
    parser.add_argument("--url", type=str, default="ws://127.0.0.1:8000/ws/device", help="Cloud WebSocket server endpoint")
    parser.add_argument("--mode", type=str, choices=['serial', 'sim'], default='sim', help="Connection mode")
    parser.add_argument("--port", type=str, default="COM5", help="Serial port target")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    args = parser.parse_args()
    
    start_ws_sender(args.url, args.port, args.baud, args.mode)
