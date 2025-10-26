#!/usr/bin/env python3
"""
Create Additional Demo Video for MERLIN
Shows a different mission scenario with blue object and different target location.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from docker_3d_robot_demo import Robot3DSimulator
import time

def create_blue_object_mission_video():
    """Create a demo video with blue object mission."""
    print("🎬 Creating Blue Object Mission Video...")
    
    # Create simulator
    simulator = Robot3DSimulator(output_dir="/Users/ahmadkaddoura/calhacks/Data")
    
    # Mission parameters - different from red cube
    mission_prompt = "Move the blue block to coordinates 4,3"
    target_color = "blue"
    target_object = "blue_block"
    target_location = [4.0, 3.0]
    
    # Set up the figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Create subplots
    ax_main = fig.add_subplot(2, 3, (1, 4), projection='3d')  # Main 3D view
    ax_prompt = fig.add_subplot(2, 3, 2)  # Prompt display
    ax_detection = fig.add_subplot(2, 3, 3)  # Color detection
    ax_progress = fig.add_subplot(2, 3, 5)  # Mission progress
    ax_status = fig.add_subplot(2, 3, 6)  # Robot status
    
    # Mission phases with different scenario
    phases = [
        {
            "name": "System Ready", 
            "duration": 2, 
            "robot_pos": [0.5, 0.5], 
            "gripper_open": True,
            "description": f"System initialized, ready for mission",
            "detected_objects": [
                {"name": "red_cube", "position": [2.0, 1.5], "color": "red", "confidence": 92},
                {"name": "green_sphere", "position": [3.5, 2.0], "color": "green", "confidence": 89},
                {"name": "blue_block", "position": [1.8, 3.2], "color": "blue", "confidence": 94}
            ],
            "target_info": "All objects detected and mapped"
        },
        {
            "name": "User Command", 
            "duration": 2, 
            "robot_pos": [0.5, 0.5], 
            "gripper_open": True,
            "description": f"Command: '{mission_prompt}'",
            "detected_objects": [],
            "target_info": "Processing natural language command"
        },
        {
            "name": "Target Selection", 
            "duration": 2, 
            "robot_pos": [0.5, 0.5], 
            "gripper_open": True,
            "description": f"Selected {target_color} block as target",
            "detected_objects": [
                {"name": "blue_block", "position": [1.8, 3.2], "color": "blue", "confidence": 94}
            ],
            "target_info": f"Target: {target_color} block at [1.8, 3.2]"
        },
        {
            "name": "Navigate to Target", 
            "duration": 4, 
            "robot_pos": [1.8, 3.2], 
            "gripper_open": True,
            "description": f"Moving to {target_color} block location",
            "detected_objects": [
                {"name": "blue_block", "position": [1.8, 3.2], "color": "blue", "confidence": 94}
            ],
            "target_info": f"Approaching target object"
        },
        {
            "name": "Grasp Object", 
            "duration": 1, 
            "robot_pos": [1.8, 3.2], 
            "gripper_open": False,
            "description": f"Grasping {target_color} block",
            "detected_objects": [],
            "target_info": f"Object grasped successfully"
        },
        {
            "name": "Transport to Destination", 
            "duration": 4, 
            "robot_pos": target_location, 
            "gripper_open": False,
            "description": f"Moving to destination {target_location}",
            "detected_objects": [],
            "target_info": f"Transporting to [4, 3]"
        },
        {
            "name": "Place Object", 
            "duration": 1, 
            "robot_pos": target_location, 
            "gripper_open": True,
            "description": f"Placing at destination",
            "detected_objects": [],
            "target_info": f"Mission complete! Blue block at {target_location}"
        }
    ]
    
    # Calculate frame data
    frame_data = []
    current_time = 0
    fps = 2
    
    for phase in phases:
        phase_frames = int(phase["duration"] * fps)
        for i in range(phase_frames):
            progress = i / phase_frames if phase_frames > 0 else 0
            
            # Interpolate robot position for movement phases
            if phase["name"] == "Navigate to Target":
                start_pos = [0.5, 0.5]
                end_pos = [1.8, 3.2]
                robot_pos = [
                    start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                    start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                ]
            elif phase["name"] == "Transport to Destination":
                start_pos = [1.8, 3.2]
                end_pos = target_location
                robot_pos = [
                    start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                    start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                ]
            else:
                robot_pos = phase["robot_pos"]
            
            # Update object position if being held
            if phase["name"] in ["Grasp Object", "Transport to Destination"] and not phase["gripper_open"]:
                gripper_offset = 0.3
                gripper_pos = [
                    robot_pos[0] + gripper_offset * np.cos(progress * 2 * np.pi),
                    robot_pos[1] + gripper_offset * np.sin(progress * 2 * np.pi),
                    0.0
                ]
                simulator.objects[target_object]['position'] = np.array(gripper_pos)
                simulator.held_object = target_object
            else:
                simulator.held_object = None
            
            frame_data.append({
                "time": current_time,
                "phase": phase["name"],
                "robot_pos": robot_pos,
                "gripper_open": phase["gripper_open"],
                "progress": progress,
                "description": phase["description"],
                "detected_objects": phase["detected_objects"],
                "target_info": phase["target_info"]
            })
            
            current_time += 1/fps
    
    def animate(frame):
        """Enhanced animation function with multiple views."""
        # Clear all subplots
        ax_main.clear()
        ax_prompt.clear()
        ax_detection.clear()
        ax_progress.clear()
        ax_status.clear()
        
        if frame < len(frame_data):
            data = frame_data[frame]
            
            # Main 3D view
            ax_main.set_xlim(0, 5)
            ax_main.set_ylim(0, 5)
            ax_main.set_zlim(0, 1.0)
            ax_main.set_xlabel('X Position (meters)')
            ax_main.set_ylabel('Y Position (meters)')
            ax_main.set_zlabel('Z Position (meters)')
            ax_main.set_title(f'MERLIN: {data["phase"]} - {data["time"]:.1f}s', fontsize=12, fontweight='bold')
            
            # Draw ground plane grid
            x = np.linspace(0, 5, 6)
            y = np.linspace(0, 5, 6)
            for i in range(len(x)):
                ax_main.plot([x[i], x[i]], [0, 5], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            for i in range(len(y)):
                ax_main.plot([0, 5], [y[i], y[i]], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            
            # Draw robot
            robot_pos = data["robot_pos"]
            ax_main.scatter(robot_pos[0], robot_pos[1], 0.1, color='blue', s=200, marker='s', label='Robot')
            
            # Draw gripper
            gripper_color = 'green' if data["gripper_open"] else 'red'
            gripper_pos = [robot_pos[0] + 0.3, robot_pos[1], 0.1]
            ax_main.scatter(gripper_pos[0], gripper_pos[1], 0.1, color=gripper_color, s=100, marker='^', label='Gripper')
            
            # Draw objects
            for name, obj in simulator.objects.items():
                if name != simulator.held_object:
                    pos = obj['position']
                    color = obj['color']
                    # Highlight target object
                    if name == target_object and data["phase"] in ["Target Selection", "Navigate to Target"]:
                        ax_main.scatter(pos[0], pos[1], pos[2], color=color, s=300, marker='s', alpha=0.9, 
                                      edgecolors='yellow', linewidth=3, label=f'{name.replace("_", " ").title()} (TARGET)')
                    else:
                        ax_main.scatter(pos[0], pos[1], pos[2], color=color, s=200, marker='s', alpha=0.8, 
                                      label=name.replace('_', ' ').title())
            
            # Draw held object
            if simulator.held_object:
                held_obj = simulator.objects[simulator.held_object]
                gripper_offset = 0.3
                held_pos = [
                    robot_pos[0] + gripper_offset * np.cos(data["progress"] * 2 * np.pi),
                    robot_pos[1] + gripper_offset * np.sin(data["progress"] * 2 * np.pi),
                    0.0
                ]
                ax_main.scatter(held_pos[0], held_pos[1], held_pos[2], 
                              color=held_obj['color'], s=300, marker='s', alpha=0.9,
                              edgecolors='yellow', linewidth=2,
                              label=f'Holding {simulator.held_object.replace("_", " ").title()}')
            
            # Draw drop zone
            drop_zone = np.array([target_location[0], target_location[1], 0.0])
            theta = np.linspace(0, 2*np.pi, 30)
            x_circle = drop_zone[0] + 0.2 * np.cos(theta)
            y_circle = drop_zone[1] + 0.2 * np.sin(theta)
            z_circle = np.zeros_like(theta)
            ax_main.plot(x_circle, y_circle, z_circle, 'g--', linewidth=3, alpha=0.8, label='Target Location')
            
            # Prompt display
            ax_prompt.set_xlim(0, 1)
            ax_prompt.set_ylim(0, 1)
            ax_prompt.axis('off')
            ax_prompt.set_title('Mission Command', fontsize=12, fontweight='bold')
            ax_prompt.text(0.5, 0.7, f'"{mission_prompt}"', ha='center', va='center', 
                          fontsize=14, fontweight='bold', color='#58a6ff',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor='#161B22', alpha=0.8))
            ax_prompt.text(0.5, 0.4, f'Target: {target_color} block', ha='center', va='center', 
                          fontsize=12, color='#e6edf3')
            ax_prompt.text(0.5, 0.2, f'Destination: {target_location}', ha='center', va='center', 
                          fontsize=12, color='#e6edf3')
            
            # Color detection display
            ax_detection.set_xlim(0, 1)
            ax_detection.set_ylim(0, 1)
            ax_detection.axis('off')
            ax_detection.set_title('Object Detection', fontsize=12, fontweight='bold')
            
            if data["detected_objects"]:
                y_pos = 0.8
                for obj in data["detected_objects"]:
                    color = obj['color']
                    confidence = obj['confidence']
                    # Highlight target object
                    if obj['name'] == target_object:
                        ax_detection.text(0.1, y_pos, f'🎯 {color.upper()} {obj["name"]} (TARGET)', 
                                        fontsize=10, color=color, fontweight='bold')
                    else:
                        ax_detection.text(0.1, y_pos, f'• {color.upper()} {obj["name"]}', 
                                        fontsize=10, color=color)
                    ax_detection.text(0.7, y_pos, f'{confidence}%', 
                                    fontsize=10, color='#10b981', fontweight='bold')
                    y_pos -= 0.15
            else:
                ax_detection.text(0.5, 0.5, 'No objects detected', ha='center', va='center', 
                                fontsize=12, color='#7d8590')
            
            # Mission progress
            ax_progress.set_xlim(0, 1)
            ax_progress.set_ylim(0, 1)
            ax_progress.axis('off')
            ax_progress.set_title('Mission Progress', fontsize=12, fontweight='bold')
            
            phase_names = ["System Ready", "User Command", "Target Selection", "Navigate to Target", "Grasp Object", "Transport to Destination", "Place Object"]
            current_phase_idx = phase_names.index(data["phase"]) if data["phase"] in phase_names else 0
            
            for i, phase_name in enumerate(phase_names):
                if i <= current_phase_idx:
                    color = '#10b981' if i == current_phase_idx else '#58a6ff'
                    marker = '●' if i == current_phase_idx else '✓'
                else:
                    color = '#6b7280'
                    marker = '○'
                
                y_pos = 0.8 - i * 0.1
                ax_progress.text(0.1, y_pos, f'{marker} {phase_name}', 
                               fontsize=9, color=color, fontweight='bold')
            
            # Robot status
            ax_status.set_xlim(0, 1)
            ax_status.set_ylim(0, 1)
            ax_status.axis('off')
            ax_status.set_title('Robot Status', fontsize=12, fontweight='bold')
            
            gripper_status = "OPEN" if data["gripper_open"] else "CLOSED"
            gripper_color = '#10b981' if data["gripper_open"] else '#ef4444'
            
            ax_status.text(0.1, 0.8, f'Position: [{robot_pos[0]:.1f}, {robot_pos[1]:.1f}]', 
                         fontsize=10, color='#e6edf3')
            ax_status.text(0.1, 0.6, f'Gripper: {gripper_status}', 
                         fontsize=10, color=gripper_color, fontweight='bold')
            ax_status.text(0.1, 0.4, f'Progress: {data["progress"]*100:.0f}%', 
                         fontsize=10, color='#f59e0b')
            ax_status.text(0.1, 0.2, data["target_info"], 
                         fontsize=9, color='#7d8590')
    
    # Create animation
    total_frames = len(frame_data)
    anim = animation.FuncAnimation(fig, animate, frames=total_frames, interval=1000/fps, repeat=True)
    
    # Save as video
    print("💾 Saving blue object mission video...")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='MERLIN'), bitrate=1800)
    
    try:
        anim.save('Data/videos/merlin_blue_mission_demo.mp4', writer=writer)
        print("✅ Blue object mission video saved as merlin_blue_mission_demo.mp4")
    except Exception as e:
        print(f"⚠️ Could not save video (ffmpeg not available): {e}")
        print("💡 Saving as GIF instead...")
        try:
            anim.save('Data/videos/merlin_blue_mission_demo.gif', writer='pillow', fps=fps)
            print("✅ Blue object mission video saved as merlin_blue_mission_demo.gif")
        except Exception as e2:
            print(f"⚠️ Could not save GIF either: {e2}")
            print("💡 Saving individual frames instead...")
            # Save individual frames
            for i in range(min(20, total_frames)):  # Save first 20 frames
                animate(i)
                plt.savefig(f'Data/videos/blue_mission_frame_{i:03d}.png', dpi=150, bbox_inches='tight')
            print("✅ Individual blue mission frames saved")
    
    plt.close()

def create_green_sphere_mission_video():
    """Create a demo video with green sphere mission."""
    print("🎬 Creating Green Sphere Mission Video...")
    
    # Create simulator
    simulator = Robot3DSimulator(output_dir="/Users/ahmadkaddoura/calhacks/Data")
    
    # Mission parameters - green sphere scenario
    mission_prompt = "Get the green sphere and put it at 1,4"
    target_color = "green"
    target_object = "green_sphere"
    target_location = [1.0, 4.0]
    
    # Set up the figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Create subplots
    ax_main = fig.add_subplot(2, 3, (1, 4), projection='3d')  # Main 3D view
    ax_prompt = fig.add_subplot(2, 3, 2)  # Prompt display
    ax_detection = fig.add_subplot(2, 3, 3)  # Color detection
    ax_progress = fig.add_subplot(2, 3, 5)  # Mission progress
    ax_status = fig.add_subplot(2, 3, 6)  # Robot status
    
    # Mission phases with green sphere scenario
    phases = [
        {
            "name": "Environment Scan", 
            "duration": 2, 
            "robot_pos": [2.5, 2.5], 
            "gripper_open": True,
            "description": f"Scanning environment for objects",
            "detected_objects": [
                {"name": "red_cube", "position": [1.2, 1.8], "color": "red", "confidence": 91},
                {"name": "green_sphere", "position": [3.8, 2.2], "color": "green", "confidence": 96},
                {"name": "blue_block", "position": [2.1, 3.5], "color": "blue", "confidence": 89}
            ],
            "target_info": "Environment mapped successfully"
        },
        {
            "name": "Mission Planning", 
            "duration": 2, 
            "robot_pos": [2.5, 2.5], 
            "gripper_open": True,
            "description": f"Planning path to {target_color} sphere",
            "detected_objects": [
                {"name": "green_sphere", "position": [3.8, 2.2], "color": "green", "confidence": 96}
            ],
            "target_info": f"Target identified: {target_color} sphere"
        },
        {
            "name": "Approach Target", 
            "duration": 3, 
            "robot_pos": [3.8, 2.2], 
            "gripper_open": True,
            "description": f"Moving to {target_color} sphere",
            "detected_objects": [
                {"name": "green_sphere", "position": [3.8, 2.2], "color": "green", "confidence": 96}
            ],
            "target_info": f"Approaching target sphere"
        },
        {
            "name": "Grasp Sphere", 
            "duration": 1, 
            "robot_pos": [3.8, 2.2], 
            "gripper_open": False,
            "description": f"Grasping {target_color} sphere",
            "detected_objects": [],
            "target_info": f"Sphere grasped successfully"
        },
        {
            "name": "Navigate to Goal", 
            "duration": 4, 
            "robot_pos": target_location, 
            "gripper_open": False,
            "description": f"Moving to goal position {target_location}",
            "detected_objects": [],
            "target_info": f"Transporting to [1, 4]"
        },
        {
            "name": "Mission Success", 
            "duration": 1, 
            "robot_pos": target_location, 
            "gripper_open": True,
            "description": f"Mission completed successfully",
            "detected_objects": [],
            "target_info": f"Green sphere delivered to {target_location}"
        }
    ]
    
    # Calculate frame data
    frame_data = []
    current_time = 0
    fps = 2
    
    for phase in phases:
        phase_frames = int(phase["duration"] * fps)
        for i in range(phase_frames):
            progress = i / phase_frames if phase_frames > 0 else 0
            
            # Interpolate robot position for movement phases
            if phase["name"] == "Approach Target":
                start_pos = [2.5, 2.5]
                end_pos = [3.8, 2.2]
                robot_pos = [
                    start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                    start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                ]
            elif phase["name"] == "Navigate to Goal":
                start_pos = [3.8, 2.2]
                end_pos = target_location
                robot_pos = [
                    start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                    start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                ]
            else:
                robot_pos = phase["robot_pos"]
            
            # Update object position if being held
            if phase["name"] in ["Grasp Sphere", "Navigate to Goal"] and not phase["gripper_open"]:
                gripper_offset = 0.3
                gripper_pos = [
                    robot_pos[0] + gripper_offset * np.cos(progress * 2 * np.pi),
                    robot_pos[1] + gripper_offset * np.sin(progress * 2 * np.pi),
                    0.0
                ]
                simulator.objects[target_object]['position'] = np.array(gripper_pos)
                simulator.held_object = target_object
            else:
                simulator.held_object = None
            
            frame_data.append({
                "time": current_time,
                "phase": phase["name"],
                "robot_pos": robot_pos,
                "gripper_open": phase["gripper_open"],
                "progress": progress,
                "description": phase["description"],
                "detected_objects": phase["detected_objects"],
                "target_info": phase["target_info"]
            })
            
            current_time += 1/fps
    
    def animate(frame):
        """Enhanced animation function with multiple views."""
        # Clear all subplots
        ax_main.clear()
        ax_prompt.clear()
        ax_detection.clear()
        ax_progress.clear()
        ax_status.clear()
        
        if frame < len(frame_data):
            data = frame_data[frame]
            
            # Main 3D view
            ax_main.set_xlim(0, 5)
            ax_main.set_ylim(0, 5)
            ax_main.set_zlim(0, 1.0)
            ax_main.set_xlabel('X Position (meters)')
            ax_main.set_ylabel('Y Position (meters)')
            ax_main.set_zlabel('Z Position (meters)')
            ax_main.set_title(f'MERLIN: {data["phase"]} - {data["time"]:.1f}s', fontsize=12, fontweight='bold')
            
            # Draw ground plane grid
            x = np.linspace(0, 5, 6)
            y = np.linspace(0, 5, 6)
            for i in range(len(x)):
                ax_main.plot([x[i], x[i]], [0, 5], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            for i in range(len(y)):
                ax_main.plot([0, 5], [y[i], y[i]], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            
            # Draw robot
            robot_pos = data["robot_pos"]
            ax_main.scatter(robot_pos[0], robot_pos[1], 0.1, color='blue', s=200, marker='s', label='Robot')
            
            # Draw gripper
            gripper_color = 'green' if data["gripper_open"] else 'red'
            gripper_pos = [robot_pos[0] + 0.3, robot_pos[1], 0.1]
            ax_main.scatter(gripper_pos[0], gripper_pos[1], 0.1, color=gripper_color, s=100, marker='^', label='Gripper')
            
            # Draw objects
            for name, obj in simulator.objects.items():
                if name != simulator.held_object:
                    pos = obj['position']
                    color = obj['color']
                    # Highlight target object
                    if name == target_object and data["phase"] in ["Mission Planning", "Approach Target"]:
                        ax_main.scatter(pos[0], pos[1], pos[2], color=color, s=300, marker='o', alpha=0.9, 
                                      edgecolors='yellow', linewidth=3, label=f'{name.replace("_", " ").title()} (TARGET)')
                    else:
                        ax_main.scatter(pos[0], pos[1], pos[2], color=color, s=200, marker='o', alpha=0.8, 
                                      label=name.replace('_', ' ').title())
            
            # Draw held object
            if simulator.held_object:
                held_obj = simulator.objects[simulator.held_object]
                gripper_offset = 0.3
                held_pos = [
                    robot_pos[0] + gripper_offset * np.cos(data["progress"] * 2 * np.pi),
                    robot_pos[1] + gripper_offset * np.sin(data["progress"] * 2 * np.pi),
                    0.0
                ]
                ax_main.scatter(held_pos[0], held_pos[1], held_pos[2], 
                              color=held_obj['color'], s=300, marker='o', alpha=0.9,
                              edgecolors='yellow', linewidth=2,
                              label=f'Holding {simulator.held_object.replace("_", " ").title()}')
            
            # Draw drop zone
            drop_zone = np.array([target_location[0], target_location[1], 0.0])
            theta = np.linspace(0, 2*np.pi, 30)
            x_circle = drop_zone[0] + 0.2 * np.cos(theta)
            y_circle = drop_zone[1] + 0.2 * np.sin(theta)
            z_circle = np.zeros_like(theta)
            ax_main.plot(x_circle, y_circle, z_circle, 'g--', linewidth=3, alpha=0.8, label='Goal Location')
            
            # Prompt display
            ax_prompt.set_xlim(0, 1)
            ax_prompt.set_ylim(0, 1)
            ax_prompt.axis('off')
            ax_prompt.set_title('Mission Command', fontsize=12, fontweight='bold')
            ax_prompt.text(0.5, 0.7, f'"{mission_prompt}"', ha='center', va='center', 
                          fontsize=14, fontweight='bold', color='#58a6ff',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor='#161B22', alpha=0.8))
            ax_prompt.text(0.5, 0.4, f'Target: {target_color} sphere', ha='center', va='center', 
                          fontsize=12, color='#e6edf3')
            ax_prompt.text(0.5, 0.2, f'Goal: {target_location}', ha='center', va='center', 
                          fontsize=12, color='#e6edf3')
            
            # Color detection display
            ax_detection.set_xlim(0, 1)
            ax_detection.set_ylim(0, 1)
            ax_detection.axis('off')
            ax_detection.set_title('Object Detection', fontsize=12, fontweight='bold')
            
            if data["detected_objects"]:
                y_pos = 0.8
                for obj in data["detected_objects"]:
                    color = obj['color']
                    confidence = obj['confidence']
                    # Highlight target object
                    if obj['name'] == target_object:
                        ax_detection.text(0.1, y_pos, f'🎯 {color.upper()} {obj["name"]} (TARGET)', 
                                        fontsize=10, color=color, fontweight='bold')
                    else:
                        ax_detection.text(0.1, y_pos, f'• {color.upper()} {obj["name"]}', 
                                        fontsize=10, color=color)
                    ax_detection.text(0.7, y_pos, f'{confidence}%', 
                                    fontsize=10, color='#10b981', fontweight='bold')
                    y_pos -= 0.15
            else:
                ax_detection.text(0.5, 0.5, 'No objects detected', ha='center', va='center', 
                                fontsize=12, color='#7d8590')
            
            # Mission progress
            ax_progress.set_xlim(0, 1)
            ax_progress.set_ylim(0, 1)
            ax_progress.axis('off')
            ax_progress.set_title('Mission Progress', fontsize=12, fontweight='bold')
            
            phase_names = ["Environment Scan", "Mission Planning", "Approach Target", "Grasp Sphere", "Navigate to Goal", "Mission Success"]
            current_phase_idx = phase_names.index(data["phase"]) if data["phase"] in phase_names else 0
            
            for i, phase_name in enumerate(phase_names):
                if i <= current_phase_idx:
                    color = '#10b981' if i == current_phase_idx else '#58a6ff'
                    marker = '●' if i == current_phase_idx else '✓'
                else:
                    color = '#6b7280'
                    marker = '○'
                
                y_pos = 0.8 - i * 0.12
                ax_progress.text(0.1, y_pos, f'{marker} {phase_name}', 
                               fontsize=9, color=color, fontweight='bold')
            
            # Robot status
            ax_status.set_xlim(0, 1)
            ax_status.set_ylim(0, 1)
            ax_status.axis('off')
            ax_status.set_title('Robot Status', fontsize=12, fontweight='bold')
            
            gripper_status = "OPEN" if data["gripper_open"] else "CLOSED"
            gripper_color = '#10b981' if data["gripper_open"] else '#ef4444'
            
            ax_status.text(0.1, 0.8, f'Position: [{robot_pos[0]:.1f}, {robot_pos[1]:.1f}]', 
                         fontsize=10, color='#e6edf3')
            ax_status.text(0.1, 0.6, f'Gripper: {gripper_status}', 
                         fontsize=10, color=gripper_color, fontweight='bold')
            ax_status.text(0.1, 0.4, f'Progress: {data["progress"]*100:.0f}%', 
                         fontsize=10, color='#f59e0b')
            ax_status.text(0.1, 0.2, data["target_info"], 
                         fontsize=9, color='#7d8590')
    
    # Create animation
    total_frames = len(frame_data)
    anim = animation.FuncAnimation(fig, animate, frames=total_frames, interval=1000/fps, repeat=True)
    
    # Save as video
    print("💾 Saving green sphere mission video...")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='MERLIN'), bitrate=1800)
    
    try:
        anim.save('Data/videos/merlin_green_mission_demo.mp4', writer=writer)
        print("✅ Green sphere mission video saved as merlin_green_mission_demo.mp4")
    except Exception as e:
        print(f"⚠️ Could not save video (ffmpeg not available): {e}")
        print("💡 Saving as GIF instead...")
        try:
            anim.save('Data/videos/merlin_green_mission_demo.gif', writer='pillow', fps=fps)
            print("✅ Green sphere mission video saved as merlin_green_mission_demo.gif")
        except Exception as e2:
            print(f"⚠️ Could not save GIF either: {e2}")
            print("💡 Saving individual frames instead...")
            # Save individual frames
            for i in range(min(20, total_frames)):  # Save first 20 frames
                animate(i)
                plt.savefig(f'Data/videos/green_mission_frame_{i:03d}.png', dpi=150, bbox_inches='tight')
            print("✅ Individual green mission frames saved")
    
    plt.close()

def main():
    """Create additional demo videos."""
    print("🎬 Starting Additional MERLIN Demo Video Creation")
    print("=" * 60)
    
    # Create output directory
    os.makedirs('Data/videos', exist_ok=True)
    
    try:
        create_blue_object_mission_video()
        create_green_sphere_mission_video()
        
        print("\n🎉 Additional demo videos created successfully!")
        print("📁 Output directory: Data/videos/")
        print("\nGenerated files:")
        print("  • merlin_blue_mission_demo.mp4 (blue block mission)")
        print("  • merlin_green_mission_demo.mp4 (green sphere mission)")
        
    except Exception as e:
        print(f"\n💥 Error creating additional demo videos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
