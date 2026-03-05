"""
PyQt5 GUI Application for Sentinel-2 Time-Lapse Analysis
Features: Segmentation, Zoom, Optimization, AI Change Detection
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

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSlider, QSpinBox, QCheckBox,
    QFileDialog, QMessageBox, QProgressBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QScrollArea, QGridLayout, QStatusBar, QGroupBox,
    QDoubleSpinBox
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect

from config import AOI_CONFIG

# ============================================================================
# SEGMENTATION & OPTIMIZATION MODULE
# ============================================================================

class ImageProcessor:
    """Process satellite imagery with optimization and enhancement"""
    
    @staticmethod
    def apply_enhancement(image_array, brightness=1.0, contrast=1.0, saturation=1.0):
        """Apply brightness, contrast, saturation adjustments"""
        
        # Convert to PIL for easier processing
        if len(image_array.shape) == 3 and image_array.shape[2] == 4:
            img = Image.fromarray(image_array[:, :, :3], 'RGB')
        else:
            img = Image.fromarray(image_array, 'RGB')
        
        # Brightness
        from PIL import ImageEnhance
        img = ImageEnhance.Brightness(img).enhance(brightness)
        # Contrast
        img = ImageEnhance.Contrast(img).enhance(contrast)
        # Saturation
        img = ImageEnhance.Color(img).enhance(saturation)
        
        return np.array(img)
    
    @staticmethod
    def segment_region(image_array, bbox):
        """Crop image to bounding box (normalized 0-1)"""
        h, w = image_array.shape[:2]
        
        # Convert normalized bbox to pixel coordinates
        x1 = int(bbox[0] * w)
        y1 = int(bbox[1] * h)
        x2 = int(bbox[2] * w)
        y2 = int(bbox[3] * h)
        
        return image_array[y1:y2, x1:x2]
    
    @staticmethod
    def apply_sharpening(image_array, strength=1.0):
        """Apply image sharpening"""
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ]) / strength
        
        if len(image_array.shape) == 3:
            result = np.zeros_like(image_array, dtype=float)
            for i in range(image_array.shape[2]):
                result[:, :, i] = cv2.filter2D(image_array[:, :, i].astype(float), -1, kernel)
            return np.clip(result, 0, 255).astype(np.uint8)
        else:
            result = cv2.filter2D(image_array.astype(float), -1, kernel)
            return np.clip(result, 0, 255).astype(np.uint8)
    
    @staticmethod
    def compute_histogram_equalization(image_array):
        """Apply histogram equalization for better contrast"""
        if len(image_array.shape) == 3:
            hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
            hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        else:
            return cv2.equalizeHist(image_array)


# ============================================================================
# AI CHANGE DETECTION MODULE
# ============================================================================

class ChangeDetector:
    """Detect changes between image frames using computer vision"""
    
    @staticmethod
    def compute_structural_similarity(img1, img2):
        """Compute SSIM (Structural Similarity Index) between two images"""
        from skimage.metrics import structural_similarity as ssim
        
        # Convert to grayscale for comparison
        if len(img1.shape) == 3:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
        else:
            gray1 = img1
            gray2 = img2
        
        score, diff = ssim(gray1, gray2, full=True)
        return score, diff
    
    @staticmethod
    def detect_changes(img_before, img_after, threshold=0.1):
        """Detect pixel-level changes between two images"""
        
        # Ensure same size
        if img_before.shape != img_after.shape:
            h, w = img_before.shape[:2]
            img_after = cv2.resize(img_after, (w, h))
        
        # Compute difference
        diff = cv2.absdiff(img_before.astype(float), img_after.astype(float))
        
        # Threshold
        change_mask = np.mean(diff, axis=2) if len(diff.shape) == 3 else diff
        change_pixels = change_mask > (threshold * 255)
        
        return change_pixels, change_mask
    
    @staticmethod
    def extract_change_regions(change_mask, min_area=100):
        """Extract bounding boxes of significant changes"""
        
        # Threshold
        binary = (change_mask > 0).astype(np.uint8) * 255
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                regions.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'centroid': (x + w//2, y + h//2)
                })
        
        return regions


# ============================================================================
# MAIN GUI APPLICATION
# ============================================================================

class TimeLapseGUI(QMainWindow):
    """Main PyQt5 GUI for satellite time-lapse analysis"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛰️ Sentinel-2 Time-Lapse Analyzer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Data storage
        self.current_aoi = None
        self.images = []  # List of loaded images
        self.current_image_idx = 0
        self.change_history = []  # Track changes over time
        
        self.init_ui()
        self.load_style()
    
    def init_ui(self):
        """Initialize UI components"""
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel: Controls
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel: Image viewer & analysis
        right_panel = self.create_viewer_panel()
        main_layout.addWidget(right_panel, 2)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_control_panel(self):
        """Create left control panel"""
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("🛰️ Time-Lapse Analyzer")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # ===== AOI Selection =====
        layout.addWidget(self.create_group("📍 AOI Selection", self.create_aoi_controls()))
        
        # ===== Segmentation =====
        layout.addWidget(self.create_group("🎯 Segmentation", self.create_segmentation_controls()))
        
        # ===== Image Optimization =====
        layout.addWidget(self.create_group("✨ Optimization", self.create_optimization_controls()))
        
        # ===== AI Analysis =====
        layout.addWidget(self.create_group("🤖 AI Analysis", self.create_ai_controls()))
        
        layout.addStretch()
        
        return panel
    
    def create_aoi_controls(self):
        """AOI selection controls"""
        layout = QVBoxLayout()
        
        # City selector
        city_layout = QHBoxLayout()
        city_layout.addWidget(QLabel("City:"))
        self.city_combo = QComboBox()
        self.city_combo.addItems(list(AOI_CONFIG.keys()))
        self.city_combo.currentTextChanged.connect(self.on_aoi_changed)
        city_layout.addWidget(self.city_combo)
        layout.addLayout(city_layout)
        
        # Sub-AOI selector
        subaoi_layout = QHBoxLayout()
        subaoi_layout.addWidget(QLabel("Sub-AOI:"))
        self.subaoi_combo = QComboBox()
        self.subaoi_combo.addItems([
            "Full (5×5 km)",
            "Center (2×2 km)",
            "Industrial (2×2 km)",
            "Custom"
        ])
        subaoi_layout.addWidget(self.subaoi_combo)
        layout.addLayout(subaoi_layout)
        
        # Load button
        load_btn = QPushButton("📂 Load Images")
        load_btn.clicked.connect(self.load_images)
        layout.addWidget(load_btn)
        
        return layout
    
    def create_segmentation_controls(self):
        """Segmentation controls"""
        layout = QVBoxLayout()
        
        # Zoom slider
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(10)
        self.zoom_slider.setValue(1)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("1.0×")
        zoom_layout.addWidget(self.zoom_label)
        layout.addLayout(zoom_layout)
        
        # ROI selection
        roi_layout = QHBoxLayout()
        self.roi_checkbox = QCheckBox("Enable ROI Selection")
        roi_layout.addWidget(self.roi_checkbox)
        layout.addLayout(roi_layout)
        
        # Segmentation button
        segment_btn = QPushButton("🎯 Segment Region")
        segment_btn.clicked.connect(self.segment_region)
        layout.addWidget(segment_btn)
        
        return layout
    
    def create_optimization_controls(self):
        """Image optimization controls"""
        layout = QVBoxLayout()
        
        # Brightness
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(QLabel("Brightness:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(50)
        self.brightness_slider.setMaximum(200)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self.on_optimization_changed)
        bright_layout.addWidget(self.brightness_slider)
        self.bright_label = QLabel("1.0")
        bright_layout.addWidget(self.bright_label)
        layout.addLayout(bright_layout)
        
        # Contrast
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Contrast:"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setMinimum(50)
        self.contrast_slider.setMaximum(200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.on_optimization_changed)
        contrast_layout.addWidget(self.contrast_slider)
        self.contrast_label = QLabel("1.0")
        contrast_layout.addWidget(self.contrast_label)
        layout.addLayout(contrast_layout)
        
        # Saturation
        sat_layout = QHBoxLayout()
        sat_layout.addWidget(QLabel("Saturation:"))
        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setMinimum(50)
        self.saturation_slider.setMaximum(200)
        self.saturation_slider.setValue(100)
        self.saturation_slider.valueChanged.connect(self.on_optimization_changed)
        sat_layout.addWidget(self.saturation_slider)
        self.sat_label = QLabel("1.0")
        sat_layout.addWidget(self.sat_label)
        layout.addLayout(sat_layout)
        
        # Sharpening
        sharp_layout = QHBoxLayout()
        sharp_layout.addWidget(QLabel("Sharpening:"))
        self.sharpening_slider = QSlider(Qt.Horizontal)
        self.sharpening_slider.setMinimum(0)
        self.sharpening_slider.setMaximum(50)
        self.sharpening_slider.setValue(0)
        self.sharpening_slider.valueChanged.connect(self.on_optimization_changed)
        sharp_layout.addWidget(self.sharpening_slider)
        self.sharp_label = QLabel("0%")
        sharp_layout.addWidget(self.sharp_label)
        layout.addLayout(sharp_layout)
        
        # Apply & Reset buttons
        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("✅ Apply")
        apply_btn.clicked.connect(self.apply_optimization)
        btn_layout.addWidget(apply_btn)
        
        reset_btn = QPushButton("↻ Reset")
        reset_btn.clicked.connect(self.reset_optimization)
        btn_layout.addWidget(reset_btn)
        layout.addLayout(btn_layout)
        
        return layout
    
    def create_ai_controls(self):
        """AI analysis controls"""
        layout = QVBoxLayout()
        
        # Change detection
        detect_btn = QPushButton("🔍 Detect Changes")
        detect_btn.clicked.connect(self.detect_changes)
        layout.addWidget(detect_btn)
        
        # Comparison
        compare_btn = QPushButton("📊 Compare Days")
        compare_btn.clicked.connect(self.compare_days)
        layout.addWidget(compare_btn)
        
        # Similarity score
        self.similarity_label = QLabel("Similarity: N/A")
        layout.addWidget(self.similarity_label)
        
        # Change regions
        self.change_regions_label = QLabel("Changes Detected: 0")
        layout.addWidget(self.change_regions_label)
        
        # Export results
        export_btn = QPushButton("💾 Export Analysis")
        export_btn.clicked.connect(self.export_analysis)
        layout.addWidget(export_btn)
        
        return layout
    
    def create_viewer_panel(self):
        """Create right viewer panel"""
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Image viewer tab
        viewer_tab = QWidget()
        viewer_layout = QVBoxLayout(viewer_tab)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setMinimumSize(600, 600)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        scroll = QScrollArea()
        scroll.setWidget(self.image_label)
        viewer_layout.addWidget(scroll)
        
        # Frame controls
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("Frame:"))
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.valueChanged.connect(self.on_frame_changed)
        frame_layout.addWidget(self.frame_slider)
        self.frame_label = QLabel("0/0")
        frame_layout.addWidget(self.frame_label)
        viewer_layout.addLayout(frame_layout)
        
        self.tabs.addTab(viewer_tab, "📷 Viewer")
        
        # Analysis tab
        analysis_tab = self.create_analysis_tab()
        self.tabs.addTab(analysis_tab, "📊 Analysis")
        
        layout.addWidget(self.tabs)
        
        return panel
    
    def create_analysis_tab(self):
        """Create analysis results tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(
            ["Date", "Similarity", "Changes", "Area Changed"]
        )
        layout.addWidget(self.results_table)
        
        return tab
    
    def create_group(self, title, content):
        """Create a grouped section"""
        group = QGroupBox(title)
        group.setLayout(content)
        return group
    
    def load_style(self):
        """Apply modern stylesheet"""
        style = """
        QMainWindow, QWidget {
            background-color: #f5f5f5;
        }
        QGroupBox {
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
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
        QComboBox, QSlider, QSpinBox {
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 3px;
        }
        """
        self.setStyleSheet(style)
    
    # ===== SLOT METHODS =====
    
    def on_aoi_changed(self):
        """Handle AOI change"""
        self.current_aoi = self.city_combo.currentText()
        self.statusBar().showMessage(f"AOI changed to: {self.current_aoi}")
    
    def on_zoom_changed(self, value):
        """Handle zoom change"""
        zoom = 1.0 + (value - 1) * 0.1
        self.zoom_label.setText(f"{zoom:.1f}×")
    
    def on_optimization_changed(self):
        """Handle optimization slider changes"""
        bright = self.brightness_slider.value() / 100.0
        contrast = self.contrast_slider.value() / 100.0
        sat = self.saturation_slider.value() / 100.0
        sharp = self.sharpening_slider.value() / 100.0
        
        self.bright_label.setText(f"{bright:.2f}")
        self.contrast_label.setText(f"{contrast:.2f}")
        self.sat_label.setText(f"{sat:.2f}")
        self.sharp_label.setText(f"{sharp:.0%}")
    
    def on_frame_changed(self, index):
        """Handle frame slider change"""
        if self.images:
            self.current_image_idx = index
            self.display_image(self.images[index])
            self.frame_label.setText(f"{index + 1}/{len(self.images)}")
    
    def load_images(self):
        """Load satellite images"""
        archive_dir = Path("archive") / self.current_aoi
        if not archive_dir.exists():
            QMessageBox.warning(self, "Error", f"Archive not found: {archive_dir}")
            return
        
        # Load GeoTIFF files
        tif_files = sorted(archive_dir.glob("*.tif"))
        self.images = []
        
        for tif_file in tif_files:
            try:
                with rasterio.open(tif_file) as src:
                    data = src.read([1, 2, 3])
                    data = np.clip(data, 0, 255).astype(np.uint8)
                    data = np.transpose(data, (1, 2, 0))
                    self.images.append(data)
            except Exception as e:
                print(f"Error loading {tif_file}: {e}")
        
        # Setup frame slider
        self.frame_slider.setMaximum(len(self.images) - 1)
        self.frame_slider.setValue(0)
        self.frame_label.setText(f"1/{len(self.images)}")
        
        if self.images:
            self.display_image(self.images[0])
            self.statusBar().showMessage(f"Loaded {len(self.images)} images")
    
    def display_image(self, image_array):
        """Display image in viewer"""
        h, w = image_array.shape[:2]
        
        # Convert to RGB
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        else:
            rgb = image_array
        
        # Resize for display
        display_size = 600
        scale = min(display_size / w, display_size / h)
        new_w, new_h = int(w * scale), int(h * scale)
        rgb = cv2.resize(rgb, (new_w, new_h))
        
        # Convert to QPixmap
        h, w = rgb.shape[:2]
        bytes_per_line = 3 * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        self.image_label.setPixmap(pixmap)
    
    def segment_region(self):
        """Segment selected region"""
        if not self.images:
            QMessageBox.warning(self, "Error", "No images loaded")
            return
        
        QMessageBox.information(self, "Segmentation", "Segmentation tool selected")
        # Implement interactive ROI selection
    
    def apply_optimization(self):
        """Apply image optimizations"""
        if not self.images:
            return
        
        bright = self.brightness_slider.value() / 100.0
        contrast = self.contrast_slider.value() / 100.0
        sat = self.saturation_slider.value() / 100.0
        
        img = self.images[self.current_image_idx].copy()
        img = ImageProcessor.apply_enhancement(img, bright, contrast, sat)
        
        self.display_image(img)
        self.statusBar().showMessage("Optimization applied")
    
    def reset_optimization(self):
        """Reset optimizations"""
        self.brightness_slider.setValue(100)
        self.contrast_slider.setValue(100)
        self.saturation_slider.setValue(100)
        self.sharpening_slider.setValue(0)
        
        self.display_image(self.images[self.current_image_idx])
        self.statusBar().showMessage("Optimization reset")
    
    def detect_changes(self):
        """Detect changes in current image"""
        if len(self.images) < 2:
            QMessageBox.warning(self, "Error", "Need at least 2 images")
            return
        
        if self.current_image_idx == 0:
            QMessageBox.information(self, "Info", "Cannot compare first frame")
            return
        
        img_before = self.images[self.current_image_idx - 1]
        img_after = self.images[self.current_image_idx]
        
        # Detect changes
        change_pixels, change_mask = ChangeDetector.detect_changes(img_before, img_after, 0.15)
        regions = ChangeDetector.extract_change_regions(change_mask)
        
        # Compute similarity
        try:
            from skimage.metrics import structural_similarity
            similarity, _ = ChangeDetector.compute_structural_similarity(img_before, img_after)
        except:
            similarity = 0.0
        
        # Update UI
        self.similarity_label.setText(f"Similarity: {similarity:.2%}")
        self.change_regions_label.setText(f"Changes Detected: {len(regions)}")
        
        # Store in history
        self.change_history.append({
            'frame': self.current_image_idx,
            'similarity': similarity,
            'regions': len(regions),
            'area': sum(r['area'] for r in regions)
        })
        
        # Update table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(str(self.current_image_idx)))
        self.results_table.setItem(row, 1, QTableWidgetItem(f"{similarity:.2%}"))
        self.results_table.setItem(row, 2, QTableWidgetItem(str(len(regions))))
        self.results_table.setItem(row, 3, QTableWidgetItem(f"{sum(r['area'] for r in regions)}"))
        
        self.statusBar().showMessage(f"Detected {len(regions)} change regions")
    
    def compare_days(self):
        """Compare imagery across days"""
        if not self.change_history:
            QMessageBox.information(self, "Info", "Run change detection first")
            return
        
        msg = "Daily Comparison Results:\n\n"
        for i, entry in enumerate(self.change_history):
            msg += f"Day {i+1}: Similarity {entry['similarity']:.2%}, {entry['regions']} changes\n"
        
        QMessageBox.information(self, "Comparison Results", msg)
    
    def export_analysis(self):
        """Export analysis results"""
        if not self.change_history:
            QMessageBox.warning(self, "Error", "No analysis results to export")
            return
        
        output = {
            'aoi': self.current_aoi,
            'analysis_date': datetime.now().isoformat(),
            'results': self.change_history
        }
        
        # Save to JSON
        output_file = Path("analysis_output") / f"analysis_{self.current_aoi}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        QMessageBox.information(self, "Export", f"Saved to {output_file}")
        self.statusBar().showMessage(f"Analysis exported")


def main():
    app = QApplication(sys.argv)
    window = TimeLapseGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
