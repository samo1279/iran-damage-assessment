"""
Advanced PyQt5 GUI with Integrated AI Training & Daily Comparison
Full-featured satellite analysis dashboard
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import cv2
import numpy as np
from PIL import Image
import rasterio
from collections import defaultdict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSlider, QSpinBox, QCheckBox,
    QFileDialog, QMessageBox, QProgressBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QScrollArea, QGridLayout, QStatusBar, QGroupBox,
    QDoubleSpinBox, QDialog, QSplitter
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor, QChart, QChartView
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect, QTimer

from config import AOI_CONFIG

try:
    from ai_change_trainer import ChangeTrainer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


# ============================================================================
# ADVANCED GUI APPLICATION
# ============================================================================

class AdvancedTimeLapseGUI(QMainWindow):
    """Advanced GUI with AI integration"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛰️ Sentinel-2 Advanced Time-Lapse Analyzer (AI-Powered)")
        self.setGeometry(100, 100, 1600, 950)
        
        # Data storage
        self.current_aoi = None
        self.images = []
        self.image_dates = []
        self.current_image_idx = 0
        self.change_history = []
        
        # AI trainer
        self.ai_trainer = ChangeTrainer() if AI_AVAILABLE else None
        self.ai_models_trained = False
        self.daily_comparisons = defaultdict(list)
        
        self.init_ui()
        self.load_style()
    
    def init_ui(self):
        """Initialize UI"""
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left: Controls
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right: Viewer & Analysis
        right_panel = self.create_viewer_panel()
        main_layout.addWidget(right_panel, 2)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_control_panel(self):
        """Create control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        title = QLabel("🛰️ Advanced Analyzer")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # AOI Selection
        aoi_group = self.create_aoi_group()
        layout.addWidget(aoi_group)
        
        # Viewer Controls
        viewer_group = self.create_viewer_controls_group()
        layout.addWidget(viewer_group)
        
        # Image Optimization
        opt_group = self.create_optimization_group()
        layout.addWidget(opt_group)
        
        # AI Tools (if available)
        if AI_AVAILABLE:
            ai_group = self.create_ai_group()
            layout.addWidget(ai_group)
        
        # Comparison Tools
        comp_group = self.create_comparison_group()
        layout.addWidget(comp_group)
        
        layout.addStretch()
        return panel
    
    def create_aoi_group(self):
        """AOI selection group"""
        group = QGroupBox("📍 AOI Selection")
        layout = QVBoxLayout()
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("City:"))
        self.city_combo = QComboBox()
        self.city_combo.addItems(list(AOI_CONFIG.keys()))
        self.city_combo.currentTextChanged.connect(self.on_aoi_changed)
        h_layout.addWidget(self.city_combo)
        layout.addLayout(h_layout)
        
        load_btn = QPushButton("📂 Load Images")
        load_btn.clicked.connect(self.load_images)
        layout.addWidget(load_btn)
        
        group.setLayout(layout)
        return group
    
    def create_viewer_controls_group(self):
        """Viewer controls group"""
        group = QGroupBox("📷 Viewer Controls")
        layout = QVBoxLayout()
        
        # Zoom
        zoom_h = QHBoxLayout()
        zoom_h.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(10)
        self.zoom_slider.setValue(1)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        zoom_h.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("1.0×")
        zoom_h.addWidget(self.zoom_label)
        layout.addLayout(zoom_h)
        
        # Frame slider
        frame_h = QHBoxLayout()
        frame_h.addWidget(QLabel("Frame:"))
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.valueChanged.connect(self.on_frame_changed)
        frame_h.addWidget(self.frame_slider)
        self.frame_label = QLabel("0/0")
        frame_h.addWidget(self.frame_label)
        layout.addLayout(frame_h)
        
        # Auto-play
        play_h = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.toggle_playback)
        play_h.addWidget(self.play_btn)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(100, 2000)
        self.speed_spin.setValue(500)
        self.speed_spin.setSuffix(" ms")
        play_h.addWidget(QLabel("Speed:"))
        play_h.addWidget(self.speed_spin)
        layout.addLayout(play_h)
        
        group.setLayout(layout)
        return group
    
    def create_optimization_group(self):
        """Image optimization group"""
        group = QGroupBox("✨ Optimization")
        layout = QVBoxLayout()
        
        # Brightness
        bright_h = QHBoxLayout()
        bright_h.addWidget(QLabel("Brightness:"))
        self.bright_slider = QSlider(Qt.Horizontal)
        self.bright_slider.setRange(50, 200)
        self.bright_slider.setValue(100)
        self.bright_slider.valueChanged.connect(self.update_optimization)
        bright_h.addWidget(self.bright_slider)
        self.bright_label = QLabel("1.0")
        bright_h.addWidget(self.bright_label)
        layout.addLayout(bright_h)
        
        # Contrast
        contrast_h = QHBoxLayout()
        contrast_h.addWidget(QLabel("Contrast:"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(50, 200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.update_optimization)
        contrast_h.addWidget(self.contrast_slider)
        self.contrast_label = QLabel("1.0")
        contrast_h.addWidget(self.contrast_label)
        layout.addLayout(contrast_h)
        
        # Saturation
        sat_h = QHBoxLayout()
        sat_h.addWidget(QLabel("Saturation:"))
        self.sat_slider = QSlider(Qt.Horizontal)
        self.sat_slider.setRange(50, 200)
        self.sat_slider.setValue(100)
        self.sat_slider.valueChanged.connect(self.update_optimization)
        sat_h.addWidget(self.sat_slider)
        self.sat_label = QLabel("1.0")
        sat_h.addWidget(self.sat_label)
        layout.addLayout(sat_h)
        
        # Apply/Reset
        btn_h = QHBoxLayout()
        apply_btn = QPushButton("✅ Apply")
        apply_btn.clicked.connect(self.apply_optimization)
        btn_h.addWidget(apply_btn)
        reset_btn = QPushButton("↻ Reset")
        reset_btn.clicked.connect(self.reset_optimization)
        btn_h.addWidget(reset_btn)
        layout.addLayout(btn_h)
        
        group.setLayout(layout)
        return group
    
    def create_ai_group(self):
        """AI tools group"""
        group = QGroupBox("🤖 AI Analysis")
        layout = QVBoxLayout()
        
        # Train model
        train_btn = QPushButton("🧠 Train AI Model")
        train_btn.clicked.connect(self.train_ai_model)
        layout.addWidget(train_btn)
        
        self.model_status = QLabel("Model: Not trained")
        layout.addWidget(self.model_status)
        
        # Detect changes
        detect_btn = QPushButton("🔍 Detect Daily Changes")
        detect_btn.clicked.connect(self.detect_daily_changes)
        layout.addWidget(detect_btn)
        
        # Anomaly detection
        anomaly_btn = QPushButton("⚠️ Find Anomalies")
        anomaly_btn.clicked.connect(self.find_anomalies)
        layout.addWidget(anomaly_btn)
        
        # Results
        self.ai_results = QLabel("Results: -")
        layout.addWidget(self.ai_results)
        
        group.setLayout(layout)
        return group
    
    def create_comparison_group(self):
        """Comparison group"""
        group = QGroupBox("📊 Comparison")
        layout = QVBoxLayout()
        
        # Compare cities
        compare_cities_btn = QPushButton("🏙️ Compare Cities")
        compare_cities_btn.clicked.connect(self.compare_cities)
        layout.addWidget(compare_cities_btn)
        
        # Daily report
        daily_btn = QPushButton("📅 Daily Report")
        daily_btn.clicked.connect(self.generate_daily_report)
        layout.addWidget(daily_btn)
        
        # Export
        export_btn = QPushButton("💾 Export Results")
        export_btn.clicked.connect(self.export_results)
        layout.addWidget(export_btn)
        
        group.setLayout(layout)
        return group
    
    def create_viewer_panel(self):
        """Create viewer panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.tabs = QTabWidget()
        
        # Image viewer
        viewer_tab = QWidget()
        viewer_layout = QVBoxLayout(viewer_tab)
        self.image_label = QLabel()
        self.image_label.setMinimumSize(700, 700)
        self.image_label.setStyleSheet("border: 2px solid #0066cc;")
        self.image_label.setAlignment(Qt.AlignCenter)
        viewer_layout.addWidget(self.image_label)
        self.tabs.addTab(viewer_tab, "📷 Viewer")
        
        # Analysis tab
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(
            ["Frame", "Date", "Similarity", "Changes", "Anomaly"]
        )
        analysis_layout.addWidget(self.results_table)
        
        self.tabs.addTab(analysis_tab, "📊 Analysis")
        
        # Summary tab
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        self.summary_text = QLabel()
        self.summary_text.setWordWrap(True)
        summary_layout.addWidget(self.summary_text)
        summary_layout.addStretch()
        self.tabs.addTab(summary_tab, "📈 Summary")
        
        layout.addWidget(self.tabs)
        
        return panel
    
    def load_style(self):
        """Apply stylesheet"""
        style = """
        QMainWindow, QWidget {
            background-color: #f5f5f5;
        }
        QGroupBox {
            border: 2px solid #0066cc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
            color: #0066cc;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        QPushButton {
            background-color: #0066cc;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #0052a3;
        }
        QPushButton:pressed {
            background-color: #003d7a;
        }
        QTableWidget {
            background-color: white;
            gridline-color: #ddd;
        }
        QLabel {
            color: #333;
        }
        """
        self.setStyleSheet(style)
    
    # ===== SLOT METHODS =====
    
    def on_aoi_changed(self):
        """Handle AOI change"""
        self.current_aoi = self.city_combo.currentText()
        self.statusBar().showMessage(f"AOI: {self.current_aoi}")
    
    def update_zoom(self, value):
        """Update zoom label"""
        zoom = 1.0 + (value - 1) * 0.1
        self.zoom_label.setText(f"{zoom:.1f}×")
    
    def update_optimization(self):
        """Update optimization labels"""
        self.bright_label.setText(f"{self.bright_slider.value() / 100:.2f}")
        self.contrast_label.setText(f"{self.contrast_slider.value() / 100:.2f}")
        self.sat_label.setText(f"{self.sat_slider.value() / 100:.2f}")
    
    def on_frame_changed(self, index):
        """Handle frame change"""
        if self.images:
            self.current_image_idx = index
            self.display_image(self.images[index])
            date_str = self.image_dates[index] if self.image_dates else "N/A"
            self.frame_label.setText(f"{index + 1}/{len(self.images)} - {date_str}")
    
    def load_images(self):
        """Load images from archive"""
        if not self.current_aoi:
            QMessageBox.warning(self, "Error", "Please select AOI first")
            return
        
        archive_dir = Path("archive") / self.current_aoi
        if not archive_dir.exists():
            QMessageBox.warning(self, "Error", f"Archive not found: {archive_dir}")
            return
        
        tif_files = sorted(archive_dir.glob("*.tif"))
        self.images = []
        self.image_dates = []
        
        for tif_file in tif_files:
            try:
                with rasterio.open(tif_file) as src:
                    data = src.read([1, 2, 3])
                    data = np.clip(data, 0, 255).astype(np.uint8)
                    data = np.transpose(data, (1, 2, 0))
                    self.images.append(data)
                    
                    # Extract date from filename
                    date_str = tif_file.stem.split('_')[0] if '_' in tif_file.stem else "?"
                    self.image_dates.append(date_str)
            except Exception as e:
                print(f"Error loading {tif_file}: {e}")
        
        # Setup UI
        self.frame_slider.setMaximum(len(self.images) - 1)
        self.frame_slider.setValue(0)
        
        if self.images:
            self.display_image(self.images[0])
            self.statusBar().showMessage(f"Loaded {len(self.images)} images from {self.current_aoi}")
    
    def display_image(self, image_array):
        """Display image"""
        h, w = image_array.shape[:2]
        scale = min(700 / w, 700 / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        rgb = cv2.resize(image_array, (new_w, new_h))
        
        bytes_per_line = 3 * new_w
        q_img = QImage(rgb.data, new_w, new_h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        self.image_label.setPixmap(pixmap)
    
    def apply_optimization(self):
        """Apply image optimization"""
        if not self.images:
            return
        
        bright = self.bright_slider.value() / 100.0
        contrast = self.contrast_slider.value() / 100.0
        sat = self.sat_slider.value() / 100.0
        
        img = self.images[self.current_image_idx].copy()
        
        # Apply adjustments
        pil_img = Image.fromarray(img, 'RGB')
        from PIL import ImageEnhance
        pil_img = ImageEnhance.Brightness(pil_img).enhance(bright)
        pil_img = ImageEnhance.Contrast(pil_img).enhance(contrast)
        pil_img = ImageEnhance.Color(pil_img).enhance(sat)
        
        img = np.array(pil_img)
        self.display_image(img)
        self.statusBar().showMessage("Optimization applied")
    
    def reset_optimization(self):
        """Reset optimization"""
        self.bright_slider.setValue(100)
        self.contrast_slider.setValue(100)
        self.sat_slider.setValue(100)
        self.display_image(self.images[self.current_image_idx])
    
    def toggle_playback(self):
        """Toggle playback"""
        QMessageBox.information(self, "Playback", "Playback feature enabled!")
    
    def train_ai_model(self):
        """Train AI model"""
        if len(self.images) < 2:
            QMessageBox.warning(self, "Error", "Need at least 2 images")
            return
        
        if not AI_AVAILABLE:
            QMessageBox.warning(self, "Error", "AI module not available")
            return
        
        try:
            # Create image pairs
            pairs = [(self.images[i], self.images[i+1]) for i in range(len(self.images)-1)]
            labels = [1] * len(pairs)  # All are changes (from different dates)
            
            # Train
            accuracy = self.ai_trainer.train_change_detector(pairs, labels)
            self.ai_models_trained = True
            self.model_status.setText(f"Model: Trained ({accuracy:.2%} accuracy)")
            
            QMessageBox.information(self, "Success", f"Model trained!\nAccuracy: {accuracy:.2%}")
            self.statusBar().showMessage(f"AI model trained with {accuracy:.2%} accuracy")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Training failed: {str(e)}")
    
    def detect_daily_changes(self):
        """Detect changes between frames"""
        if not self.ai_models_trained:
            QMessageBox.warning(self, "Error", "Please train AI model first")
            return
        
        self.results_table.setRowCount(0)
        
        for i in range(1, len(self.images)):
            pair = (self.images[i-1], self.images[i])
            prediction = self.ai_trainer.predict_change(pair)
            
            # Add to table
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            self.results_table.setItem(row, 0, QTableWidgetItem(str(i)))
            self.results_table.setItem(row, 1, QTableWidgetItem(self.image_dates[i]))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{prediction['change_prob']:.2%}"))
            self.results_table.setItem(row, 3, QTableWidgetItem(
                "✓ Yes" if prediction['change_detected'] else "✗ No"
            ))
            
            # Anomaly detection
            anomaly = self.ai_trainer.detect_anomaly(pair)
            anomaly_text = "⚠️ Anomaly" if anomaly['is_anomaly'] else "Normal"
            self.results_table.setItem(row, 4, QTableWidgetItem(anomaly_text))
        
        self.statusBar().showMessage(f"Analyzed {len(self.images)-1} frame transitions")
    
    def find_anomalies(self):
        """Find anomalous frames"""
        if not self.ai_models_trained:
            QMessageBox.warning(self, "Error", "Please train AI model first")
            return
        
        anomalies = []
        for i in range(1, len(self.images)):
            pair = (self.images[i-1], self.images[i])
            anomaly = self.ai_trainer.detect_anomaly(pair)
            if anomaly['is_anomaly']:
                anomalies.append({
                    'frame': i,
                    'date': self.image_dates[i],
                    'score': anomaly['anomaly_score']
                })
        
        msg = f"Found {len(anomalies)} anomalies:\n\n"
        for anom in anomalies[:5]:  # Show top 5
            msg += f"• Frame {anom['frame']} ({anom['date']}): Score {anom['score']:.3f}\n"
        
        QMessageBox.information(self, "Anomalies", msg if anomalies else "No anomalies detected")
    
    def compare_cities(self):
        """Compare analysis between cities"""
        msg = f"Comparing {self.current_aoi}...\n\n"
        
        if self.ai_models_trained and len(self.images) > 1:
            pairs = [(self.images[i], self.images[i+1]) for i in range(min(5, len(self.images)-1))]
            results = self.ai_trainer.get_daily_comparison([self.images[i] for i in range(len(self.images))])
            
            msg += f"Daily Changes: {len(results['daily_changes'])}\n"
            msg += f"Change Trend: {results['trend']:.6f}\n"
            msg += f"Volatility: {results['volatility']:.3f}\n"
        
        QMessageBox.information(self, "City Comparison", msg)
    
    def generate_daily_report(self):
        """Generate daily report"""
        if not self.images:
            return
        
        report = {
            'city': self.current_aoi,
            'date': datetime.now().isoformat(),
            'frames': len(self.images),
            'date_range': f"{self.image_dates[0]} to {self.image_dates[-1]}" if self.image_dates else "N/A"
        }
        
        report_dir = Path("daily_reports")
        report_dir.mkdir(exist_ok=True)
        
        report_path = report_dir / f"{self.current_aoi}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        QMessageBox.information(self, "Report", f"Report saved to {report_path}")
    
    def export_results(self):
        """Export results"""
        if not self.images:
            QMessageBox.warning(self, "Error", "No data to export")
            return
        
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_file = export_dir / f"analysis_{self.current_aoi}_{timestamp}.json"
        
        export_data = {
            'aoi': self.current_aoi,
            'timestamp': timestamp,
            'frames': len(self.images),
            'dates': self.image_dates,
            'ai_trained': self.ai_models_trained
        }
        
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        QMessageBox.information(self, "Export", f"Exported to {export_file}")
        self.statusBar().showMessage(f"Results exported")


def main():
    app = QApplication(sys.argv)
    window = AdvancedTimeLapseGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
