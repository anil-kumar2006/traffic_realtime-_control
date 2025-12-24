import tkinter as tk
from tkinter import font
import datetime
import random
import time
from dataclasses import dataclass
from typing import List, Dict

# ==========================================
# PART 1: CONFIGURATION
# ==========================================

WEIGHTS = {
    'car': 3,
    'bus': 4,
    'truck': 4,
    'bike': 2,
    'auto': 2,
    'van': 3,
    'ambulance': 100,
    'fire_engine': 100
}

# Vehicle Icons for Visualization
ICONS = {
    'car': '🚗',
    'bus': '🚌',
    'truck': '🚛',
    'bike': '🏍️',
    'auto': '🛺',
    'van': '🚐',
    'ambulance': '🚑',
    'fire_engine': '🚒'
}

# Time Settings
SCHOOL_MODE_START = datetime.time(8, 45)
SCHOOL_MODE_END = datetime.time(9, 0)
HEAVY_TRAFFIC_START = datetime.time(15, 30)
HEAVY_TRAFFIC_END = datetime.time(21, 0)

@dataclass
class LaneData:
    lane_id: str
    vehicle_counts: Dict[str, int]
    vehicle_list: List[str] # List of vehicle types for drawing
    is_school_route: bool = False
    density_score: int = 0
    has_emergency: bool = False
    status: str = "RED" 

# ==========================================
# PART 2: BACKEND (AI LOGIC)
# ==========================================

class TrafficAIController:
    def __init__(self):
        self.active_mode = "NORMAL"

    def calculate_density(self, counts: Dict[str, int]) -> int:
        score = 0
        for vehicle, count in counts.items():
            if vehicle in WEIGHTS and vehicle not in ['ambulance', 'fire_engine']:
                score += count * WEIGHTS.get(vehicle, 1)
        return score

    def detect_emergency(self, counts: Dict[str, int]) -> bool:
        return counts.get('ambulance', 0) > 0 or counts.get('fire_engine', 0) > 0

    def generate_random_time(self):
        h, m = random.randint(0, 23), random.randint(0, 59)
        return datetime.time(h, m)

    def generate_simulation_data(self) -> List[LaneData]:
        lanes = []
        lane_names = ["North", "South", "East", "West"]
        school_route_index = random.randint(0, 3)

        for i, name in enumerate(lane_names):
            counts = {
                'car': random.randint(0, 6), 'bus': random.randint(0, 2),
                'truck': random.randint(0, 2), 'bike': random.randint(0, 8),
                'auto': random.randint(0, 3), 'van': random.randint(0, 2),
                'ambulance': 0, 'fire_engine': 0
            }
            
            # Generate a flat list of vehicles for drawing (e.g., ['car', 'car', 'bus'])
            vehicle_list = []
            for v_type, count in counts.items():
                vehicle_list.extend([v_type] * count)
            
            # 10% Emergency Chance
            if random.random() < 0.10:
                e_type = 'ambulance' if random.choice([True, False]) else 'fire_engine'
                counts[e_type] = 1
                vehicle_list.insert(0, e_type) # Emergency always at front visually
            
            # Shuffle list so vehicles are mixed up like real traffic
            if not (counts['ambulance'] or counts['fire_engine']):
                random.shuffle(vehicle_list)

            is_school = (i == school_route_index)
            lane = LaneData(lane_id=name, vehicle_counts=counts, vehicle_list=vehicle_list, is_school_route=is_school)
            
            lane.has_emergency = self.detect_emergency(lane.vehicle_counts)
            lane.density_score = self.calculate_density(lane.vehicle_counts)
            lanes.append(lane)
            
        return lanes

    def decide_signals(self, lanes: List[LaneData], current_time):
        emergency_lanes = [l for l in lanes if l.has_emergency]
        normal_lanes = [l for l in lanes if not l.has_emergency]
        
        for l in lanes: l.status = "RED"
        selected_lane = None
        mode_desc = ""

        if emergency_lanes:
            mode_desc = "!!! EMERGENCY PROTOCOL !!!"
            selected_lane = emergency_lanes[0]
        elif SCHOOL_MODE_START <= current_time <= SCHOOL_MODE_END:
            mode_desc = "MODE: SCHOOL RUSH (School Priority)"
            normal_lanes.sort(key=lambda x: (not x.is_school_route, x.density_score))
            if normal_lanes: selected_lane = normal_lanes[0]
        elif HEAVY_TRAFFIC_START <= current_time <= HEAVY_TRAFFIC_END:
            mode_desc = "MODE: HEAVY TRAFFIC (Low Density First)"
            normal_lanes.sort(key=lambda x: x.density_score)
            if normal_lanes: selected_lane = normal_lanes[0]
        else:
            mode_desc = "MODE: NORMAL FLOW"
            normal_lanes.sort(key=lambda x: x.density_score)
            if normal_lanes: selected_lane = normal_lanes[0]

        if selected_lane: selected_lane.status = "GREEN"
        return lanes, mode_desc

# ==========================================
# PART 3: FRONTEND (GUI WITH VISUALS)
# ==========================================

class TrafficGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Traffic Vision System")
        self.root.geometry("1100x800")
        self.root.configure(bg="#222") # Dark Mode for better visuals
        
        self.controller = TrafficAIController()
        
        # Styles
        self.style_header = font.Font(family="Arial", size=18, weight="bold")
        self.style_lane = font.Font(family="Arial", size=14, weight="bold")
        
        # Header
        header = tk.Frame(root, bg="#111", pady=15)
        header.pack(fill="x")
        self.lbl_time = tk.Label(header, text="TIME: --:--", font=self.style_header, fg="#00e5ff", bg="#111")
        self.lbl_time.pack(side="left", padx=20)
        self.lbl_mode = tk.Label(header, text="SYSTEM READY", font=self.style_header, fg="#ffd700", bg="#111")
        self.lbl_mode.pack(side="right", padx=20)

        # Main Grid (Roads)
        self.grid_frame = tk.Frame(root, bg="#333", pady=10, padx=10)
        self.grid_frame.pack(expand=True, fill="both")
        
        self.lane_widgets = []
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        
        for i in range(4):
            # Container for each lane
            container = tk.Frame(self.grid_frame, bg="#444", bd=2, relief="sunken")
            container.grid(row=positions[i][0], column=positions[i][1], padx=5, pady=5, sticky="nsew")
            self.grid_frame.grid_columnconfigure(positions[i][1], weight=1)
            self.grid_frame.grid_rowconfigure(positions[i][0], weight=1)
            
            # Title & Signal Bar
            top_bar = tk.Frame(container, bg="#555", height=40)
            top_bar.pack(fill="x")
            
            lbl_name = tk.Label(top_bar, text=f"Lane {i}", font=self.style_lane, bg="#555", fg="white")
            lbl_name.pack(side="left", padx=10)
            
            lbl_signal = tk.Label(top_bar, text="🔴", font=("Arial", 20), bg="#555")
            lbl_signal.pack(side="right", padx=10)
            
            # The Road (Canvas)
            canvas = tk.Canvas(container, bg="#333", height=200, highlightthickness=0)
            canvas.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Draw Road Lines
            canvas.create_line(10, 100, 500, 100, fill="white", dash=(20, 20), width=2) # Divider
            
            # Info Label
            lbl_info = tk.Label(container, text="Density: 0", bg="#444", fg="#aaa", font=("Consolas", 10))
            lbl_info.pack(anchor="w", padx=5, pady=2)

            self.lane_widgets.append({
                "name": lbl_name,
                "signal": lbl_signal,
                "canvas": canvas,
                "info": lbl_info,
                "frame": container,
                "top_bar": top_bar
            })

        # Button
        btn_frame = tk.Frame(root, bg="#222", pady=10)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="Generate Live Traffic Scenario", command=self.run_simulation,
                  bg="#00b894", fg="white", font=("Arial", 14, "bold"), padx=20).pack()

    def draw_vehicles(self, canvas, vehicles):
        """Draws vehicle icons on the canvas road."""
        canvas.delete("all")
        
        # Road Markings
        w = canvas.winfo_width()
        canvas.create_rectangle(0, 40, w, 160, fill="#2d3436", outline="") # Tarmac
        canvas.create_line(0, 100, w, 100, fill="white", dash=(20, 20), width=2) # Center line
        
        # Draw Vehicles
        # We define slots (x, y) coordinates for vehicles to park
        x_start = 20
        y_lanes = [70, 130] # Top lane, Bottom lane
        
        for idx, v_type in enumerate(vehicles):
            # Limit visuals to prevent clutter (max 14 vehicles shown)
            if idx >= 14: break 
            
            icon = ICONS.get(v_type, '?')
            x_pos = x_start + (idx // 2) * 50  # Move right every 2 cars
            y_pos = y_lanes[idx % 2]          # Alternate lanes
            
            # Draw Text Icon
            font_size = 24 if v_type in ['ambulance', 'fire_engine', 'truck', 'bus'] else 20
            color = "white"
            
            canvas.create_text(x_pos, y_pos, text=icon, font=("Segoe UI Emoji", font_size), fill=color)

    def run_simulation(self):
        sim_time = self.controller.generate_random_time()
        self.lbl_time.config(text=f"TIME: {sim_time.strftime('%H:%M')}")
        
        lanes = self.controller.generate_simulation_data()
        processed_lanes, mode_text = self.controller.decide_signals(lanes, sim_time)
        
        self.lbl_mode.config(text=mode_text)
        if "EMERGENCY" in mode_text: self.lbl_mode.config(fg="#ff4757")
        elif "SCHOOL" in mode_text: self.lbl_mode.config(fg="#ffa502")
        else: self.lbl_mode.config(fg="#2ed573")

        for i, lane in enumerate(processed_lanes):
            widgets = self.lane_widgets[i]
            
            # Update Text
            title_text = f"{lane.lane_id}"
            if lane.is_school_route: title_text += " (School)"
            widgets["name"].config(text=title_text)
            
            # Update Canvas (Draw Cars)
            self.draw_vehicles(widgets["canvas"], lane.vehicle_list)
            
            # Update Info
            widgets["info"].config(text=f"Density Score: {lane.density_score} | Vehicles: {len(lane.vehicle_list)}")
            
            # Update Signal
            if lane.status == "GREEN":
                widgets["signal"].config(text="🟢 GO", fg="#55efc4")
                widgets["top_bar"].config(bg="#006266") # Dark Green header
                widgets["name"].config(bg="#006266")
                widgets["signal"].config(bg="#006266")
            else:
                widgets["signal"].config(text="🔴 STOP", fg="#ff7675")
                widgets["top_bar"].config(bg="#636e72") # Gray header
                widgets["name"].config(bg="#636e72")
                widgets["signal"].config(bg="#636e72")

if __name__ == "__main__":
    root = tk.Tk()
    app = TrafficGUI(root)
    root.mainloop()