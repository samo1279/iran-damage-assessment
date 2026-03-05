"""
AI Training Module for Change Detection
Trains simple ML models to detect and compare daily changes
"""

import numpy as np
from pathlib import Path
from datetime import datetime
import json
import joblib
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')


class ChangeTrainer:
    """Train AI models to detect changes between images"""
    
    def __init__(self, model_dir="trained_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.models = {
            'change_detector': None,  # RandomForest for change classification
            'anomaly_detector': None,  # IsolationForest for anomalies
            'pca': None,  # PCA for dimensionality reduction
            'scaler': None
        }
        self.training_history = []
    
    def extract_features(self, image_pair):
        """Extract features from image pair"""
        img1, img2 = image_pair
        
        # Ensure same dimensions
        if img1.shape != img2.shape:
            h, w = img1.shape[:2]
            img2 = cv2.resize(img2, (w, h))
        
        # Compute difference
        diff = np.abs(img1.astype(float) - img2.astype(float))
        
        # Feature extraction
        features = []
        
        # Per-channel statistics
        for c in range(3):
            ch_diff = diff[:, :, c] if len(diff.shape) == 3 else diff
            features.extend([
                np.mean(ch_diff),      # Mean difference
                np.std(ch_diff),       # Std deviation
                np.max(ch_diff),       # Max difference
                np.percentile(ch_diff, 75),  # 75th percentile
                np.percentile(ch_diff, 95),  # 95th percentile
            ])
        
        # Spatial features
        if len(diff.shape) == 3:
            gray_diff = np.mean(diff, axis=2)
        else:
            gray_diff = diff
        
        # Edge detection
        edges = np.gradient(gray_diff)
        features.extend([
            np.mean(np.abs(edges[0])),
            np.mean(np.abs(edges[1])),
        ])
        
        # Histogram features
        hist = np.histogram(gray_diff, bins=10)[0]
        features.extend(hist / np.sum(hist))  # Normalize histogram
        
        return np.array(features)
    
    def train_change_detector(self, image_pairs, labels):
        """
        Train RandomForest to detect changes
        
        Args:
            image_pairs: List of (img_before, img_after) tuples
            labels: List of change/no-change labels (0 or 1)
        """
        print("[AI Training] Extracting features from images...")
        X = np.array([self.extract_features(pair) for pair in image_pairs])
        y = np.array(labels)
        
        # Standardize features
        self.models['scaler'] = StandardScaler()
        X_scaled = self.models['scaler'].fit_transform(X)
        
        # Reduce dimensionality
        self.models['pca'] = PCA(n_components=min(20, X_scaled.shape[1]))
        X_pca = self.models['pca'].fit_transform(X_scaled)
        
        # Train classifier
        print("[AI Training] Training RandomForest classifier...")
        self.models['change_detector'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        self.models['change_detector'].fit(X_pca, y)
        
        # Feature importance
        importance = self.models['change_detector'].feature_importances_
        print(f"[AI Training] Top 5 important features: {np.argsort(importance)[-5:][::-1]}")
        
        # Save model
        self.save_models('change_detector')
        return self.models['change_detector'].score(X_pca, y)
    
    def train_anomaly_detector(self, normal_pairs, contamination=0.1):
        """
        Train anomaly detector for unusual changes
        
        Args:
            normal_pairs: List of normal image pairs
            contamination: Proportion of anomalies expected
        """
        print("[AI Training] Training anomaly detector...")
        X = np.array([self.extract_features(pair) for pair in normal_pairs])
        X_scaled = self.models['scaler'].transform(X)
        X_pca = self.models['pca'].transform(X_scaled)
        
        self.models['anomaly_detector'] = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        self.models['anomaly_detector'].fit(X_pca)
        
        self.save_models('anomaly_detector')
        print("[AI Training] Anomaly detector ready")
    
    def predict_change(self, image_pair):
        """Predict if image pair contains significant change"""
        if self.models['change_detector'] is None:
            return None
        
        features = self.extract_features(image_pair)
        features_scaled = self.models['scaler'].transform(features.reshape(1, -1))
        features_pca = self.models['pca'].transform(features_scaled)
        
        prediction = self.models['change_detector'].predict(features_pca)[0]
        probability = self.models['change_detector'].predict_proba(features_pca)[0]
        
        return {
            'change_detected': bool(prediction),
            'confidence': float(probability[prediction]),
            'no_change_prob': float(probability[0]),
            'change_prob': float(probability[1])
        }
    
    def detect_anomaly(self, image_pair):
        """Detect if image pair is anomalous"""
        if self.models['anomaly_detector'] is None:
            return None
        
        features = self.extract_features(image_pair)
        features_scaled = self.models['scaler'].transform(features.reshape(1, -1))
        features_pca = self.models['pca'].transform(features_scaled)
        
        anomaly_score = self.models['anomaly_detector'].decision_function(features_pca)[0]
        is_anomaly = self.models['anomaly_detector'].predict(features_pca)[0] == -1
        
        return {
            'is_anomaly': bool(is_anomaly),
            'anomaly_score': float(anomaly_score)
        }
    
    def compare_cities(self, tehran_pairs, isfahan_pairs):
        """
        Compare change patterns between cities
        
        Returns:
            Dictionary with comparison metrics
        """
        print("[AI Training] Comparing cities...")
        
        tehran_features = np.array([self.extract_features(p) for p in tehran_pairs])
        isfahan_features = np.array([self.extract_features(p) for p in isfahan_pairs])
        
        comparison = {
            'tehran': {
                'mean_change': float(np.mean(tehran_features)),
                'std_change': float(np.std(tehran_features)),
                'change_rate': float(np.mean(tehran_features > np.median(tehran_features))),
            },
            'isfahan': {
                'mean_change': float(np.mean(isfahan_features)),
                'std_change': float(np.std(isfahan_features)),
                'change_rate': float(np.mean(isfahan_features > np.median(isfahan_features))),
            }
        }
        
        # Correlation between cities
        if len(tehran_features) > 1 and len(isfahan_features) > 1:
            min_len = min(len(tehran_features), len(isfahan_features))
            correlation = np.corrcoef(
                np.mean(tehran_features[:min_len], axis=1),
                np.mean(isfahan_features[:min_len], axis=1)
            )[0, 1]
            comparison['correlation'] = float(correlation)
        
        return comparison
    
    def get_daily_comparison(self, image_sequence):
        """Analyze changes across daily sequence"""
        results = {
            'daily_changes': [],
            'trend': None,
            'volatility': None
        }
        
        for i in range(1, len(image_sequence)):
            pair = (image_sequence[i-1], image_sequence[i])
            prediction = self.predict_change(pair)
            results['daily_changes'].append(prediction)
        
        # Compute trend
        if results['daily_changes']:
            change_probs = [r['change_prob'] for r in results['daily_changes']]
            results['trend'] = np.polyfit(range(len(change_probs)), change_probs, 1)[0]
            results['volatility'] = float(np.std(change_probs))
        
        return results
    
    def save_models(self, model_name=None):
        """Save trained models"""
        if model_name is None:
            # Save all
            for name, model in self.models.items():
                if model is not None:
                    path = self.model_dir / f"{name}.pkl"
                    joblib.dump(model, path)
                    print(f"[AI Training] Saved {name} to {path}")
        else:
            if self.models[model_name] is not None:
                path = self.model_dir / f"{model_name}.pkl"
                joblib.dump(self.models[model_name], path)
                print(f"[AI Training] Saved {model_name}")
    
    def load_models(self):
        """Load trained models"""
        for name in self.models.keys():
            path = self.model_dir / f"{name}.pkl"
            if path.exists():
                self.models[name] = joblib.load(path)
                print(f"[AI Training] Loaded {name}")
    
    def generate_report(self, city_name, analysis_results):
        """Generate analysis report"""
        report = {
            'city': city_name,
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis_results,
            'model_version': '1.0'
        }
        
        # Save report
        report_dir = Path("ai_reports")
        report_dir.mkdir(exist_ok=True)
        report_path = report_dir / f"report_{city_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[AI Training] Report saved to {report_path}")
        return report_path


# Example usage
if __name__ == "__main__":
    trainer = ChangeTrainer()
    print("AI Change Trainer initialized")
    print("Use with GUI application for integrated training and analysis")
