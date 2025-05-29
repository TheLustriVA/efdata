"""
Anomaly Detection Pipeline for EconCell Economic Data

Detects anomalies in economic data streams using statistical methods
and AI-powered pattern recognition for real-time alerts and analysis.
"""

import logging
import time
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json
import pandas as pd
import numpy as np
from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class AnomalyDetectionPipeline:
    """
    Pipeline for detecting anomalies in economic data streams
    
    Features:
    - Statistical anomaly detection (Z-score, IQR, trend analysis)
    - Time series anomaly detection
    - Cross-indicator correlation anomalies
    - AI-powered pattern recognition
    - Real-time alerting system
    - Historical anomaly tracking
    """
    
    def __init__(self):
        # Historical data storage for anomaly detection
        self.historical_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.indicator_stats: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Anomaly detection configuration
        self.config = {
            "z_score_threshold": 3.0,
            "iqr_multiplier": 1.5,
            "min_samples_for_detection": 10,
            "correlation_threshold": 0.8,
            "trend_change_threshold": 0.5,
            "enable_ai_detection": True,
            "alert_threshold": "medium",  # low, medium, high, critical
            "historical_window_days": 365
        }
        
        # Anomaly tracking
        self.detected_anomalies: List[Dict[str, Any]] = []
        self.anomaly_patterns: Dict[str, int] = defaultdict(int)
        
        # Performance statistics
        self.stats = {
            "items_processed": 0,
            "anomalies_detected": 0,
            "false_positives": 0,
            "alerts_generated": 0,
            "processing_time_ms": deque(maxlen=1000)
        }
        
        # Economic indicator definitions
        self.economic_indicators = {
            "inflation": {"normal_range": (0, 10), "critical_threshold": 15},
            "unemployment": {"normal_range": (3, 12), "critical_threshold": 20},
            "interest_rate": {"normal_range": (0, 15), "critical_threshold": 25},
            "gdp_growth": {"normal_range": (-5, 8), "critical_threshold": 15},
            "exchange_rate": {"normal_range": (0.5, 2.0), "critical_threshold": 3.0},
            "commodity_price": {"normal_range": (50, 500), "critical_threshold": 1000}
        }
        
        logger.info("AnomalyDetectionPipeline initialized")
    
    def open_spider(self, spider):
        """Initialize pipeline when spider starts"""
        logger.info(f"AnomalyDetectionPipeline opened for spider: {spider.name}")
        
        # Load historical data if available
        self._load_historical_data()
        
        # Initialize indicator statistics
        self._initialize_indicator_stats()
    
    def close_spider(self, spider):
        """Cleanup when spider closes"""
        # Save anomaly detection results
        self._save_anomaly_results()
        
        # Log final statistics
        logger.info(f"AnomalyDetectionPipeline stats: {self.get_stats()}")
        
        # Generate summary report
        self._generate_anomaly_report()
    
    def process_item(self, item, spider):
        """Process items for anomaly detection"""
        start_time = time.time()
        
        try:
            adapter = ItemAdapter(item)
            
            # Extract economic indicators from item
            indicators = self._extract_economic_indicators(adapter)
            
            if not indicators:
                return item
            
            # Detect anomalies in the indicators
            anomalies = self._detect_anomalies(indicators, adapter)
            
            # Apply anomaly information to item
            if anomalies:
                self._apply_anomaly_data(adapter, anomalies)
                self.stats["anomalies_detected"] += len(anomalies)
                
                # Generate alerts for critical anomalies
                critical_anomalies = [a for a in anomalies if a.get("severity") == "critical"]
                if critical_anomalies:
                    self._generate_alerts(critical_anomalies, adapter)
            
            # Update historical data
            self._update_historical_data(indicators)
            
            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            self.stats["processing_time_ms"].append(processing_time)
            self.stats["items_processed"] += 1
            
            return item
            
        except Exception as e:
            logger.error(f"Error in anomaly detection pipeline: {e}")
            return item
    
    def _extract_economic_indicators(self, adapter: ItemAdapter) -> Dict[str, float]:
        """Extract economic indicators from item data"""
        indicators = {}
        
        try:
            # Look for common economic indicator fields
            indicator_fields = [
                'inflation_rate', 'unemployment_rate', 'interest_rate',
                'gdp_growth', 'exchange_rate', 'commodity_price',
                'cpi', 'ppi', 'wage_growth', 'retail_sales'
            ]
            
            for field in indicator_fields:
                if field in adapter:
                    value = adapter[field]
                    if isinstance(value, (int, float)):
                        indicators[field] = float(value)
                    elif isinstance(value, str):
                        try:
                            # Try to parse numeric value from string
                            import re
                            numeric_match = re.search(r'-?\d+\.?\d*', value)
                            if numeric_match:
                                indicators[field] = float(numeric_match.group())
                        except:
                            continue
            
            # Extract from structured data if available
            if 'data' in adapter:
                data = adapter['data']
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (int, float)) and self._is_economic_indicator(key):
                            indicators[key] = float(value)
            
            # Extract from enriched data
            if 'economic_indicators' in adapter:
                enriched_indicators = adapter['economic_indicators']
                if isinstance(enriched_indicators, list):
                    for indicator in enriched_indicators:
                        if isinstance(indicator, dict) and 'value' in indicator:
                            name = indicator.get('name', '').lower()
                            value = indicator.get('value')
                            if isinstance(value, (int, float)):
                                indicators[name] = float(value)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error extracting economic indicators: {e}")
            return {}
    
    def _is_economic_indicator(self, field_name: str) -> bool:
        """Check if field name represents an economic indicator"""
        economic_keywords = [
            'rate', 'growth', 'index', 'price', 'inflation', 'unemployment',
            'gdp', 'cpi', 'ppi', 'wage', 'sales', 'export', 'import'
        ]
        
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in economic_keywords)
    
    def _detect_anomalies(self, indicators: Dict[str, float], adapter: ItemAdapter) -> List[Dict[str, Any]]:
        """Detect anomalies in economic indicators"""
        anomalies = []
        
        for indicator_name, value in indicators.items():
            # Statistical anomaly detection
            statistical_anomalies = self._detect_statistical_anomalies(indicator_name, value)
            anomalies.extend(statistical_anomalies)
            
            # Range-based anomaly detection
            range_anomalies = self._detect_range_anomalies(indicator_name, value)
            anomalies.extend(range_anomalies)
            
            # Trend anomaly detection
            trend_anomalies = self._detect_trend_anomalies(indicator_name, value)
            anomalies.extend(trend_anomalies)
        
        # Cross-indicator correlation anomalies
        correlation_anomalies = self._detect_correlation_anomalies(indicators)
        anomalies.extend(correlation_anomalies)
        
        # Remove duplicates and rank by severity
        unique_anomalies = self._deduplicate_and_rank_anomalies(anomalies)
        
        return unique_anomalies
    
    def _detect_statistical_anomalies(self, indicator_name: str, value: float) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods"""
        anomalies = []
        
        if indicator_name not in self.historical_data:
            return anomalies
        
        historical_values = list(self.historical_data[indicator_name])
        
        if len(historical_values) < self.config["min_samples_for_detection"]:
            return anomalies
        
        try:
            # Z-score based detection
            mean_val = statistics.mean(historical_values)
            std_val = statistics.stdev(historical_values)
            
            if std_val > 0:
                z_score = abs(value - mean_val) / std_val
                
                if z_score > self.config["z_score_threshold"]:
                    anomalies.append({
                        "type": "statistical_outlier",
                        "indicator": indicator_name,
                        "value": value,
                        "z_score": z_score,
                        "mean": mean_val,
                        "std": std_val,
                        "severity": self._calculate_severity(z_score, "z_score"),
                        "description": f"{indicator_name} value {value} is {z_score:.2f} standard deviations from mean"
                    })
            
            # IQR based detection
            if len(historical_values) >= 4:
                q1 = np.percentile(historical_values, 25)
                q3 = np.percentile(historical_values, 75)
                iqr = q3 - q1
                
                lower_bound = q1 - (self.config["iqr_multiplier"] * iqr)
                upper_bound = q3 + (self.config["iqr_multiplier"] * iqr)
                
                if value < lower_bound or value > upper_bound:
                    anomalies.append({
                        "type": "iqr_outlier",
                        "indicator": indicator_name,
                        "value": value,
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound,
                        "severity": self._calculate_severity(
                            max(abs(value - lower_bound), abs(value - upper_bound)) / iqr, 
                            "iqr"
                        ),
                        "description": f"{indicator_name} value {value} outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]"
                    })
            
        except Exception as e:
            logger.error(f"Error in statistical anomaly detection for {indicator_name}: {e}")
        
        return anomalies
    
    def _detect_range_anomalies(self, indicator_name: str, value: float) -> List[Dict[str, Any]]:
        """Detect anomalies based on expected ranges for economic indicators"""
        anomalies = []
        
        # Check against known indicator ranges
        for indicator_type, config in self.economic_indicators.items():
            if indicator_type in indicator_name.lower():
                normal_range = config["normal_range"]
                critical_threshold = config["critical_threshold"]
                
                if value < normal_range[0] or value > normal_range[1]:
                    severity = "critical" if (value < 0 or value > critical_threshold) else "high"
                    
                    anomalies.append({
                        "type": "range_anomaly",
                        "indicator": indicator_name,
                        "value": value,
                        "normal_range": normal_range,
                        "critical_threshold": critical_threshold,
                        "severity": severity,
                        "description": f"{indicator_name} value {value} outside normal range {normal_range}"
                    })
                
                break
        
        return anomalies
    
    def _detect_trend_anomalies(self, indicator_name: str, value: float) -> List[Dict[str, Any]]:
        """Detect trend-based anomalies"""
        anomalies = []
        
        if indicator_name not in self.historical_data:
            return anomalies
        
        historical_values = list(self.historical_data[indicator_name])
        
        if len(historical_values) < 5:  # Need at least 5 points for trend analysis
            return anomalies
        
        try:
            # Calculate recent trend
            recent_values = historical_values[-5:]  # Last 5 values
            if len(recent_values) >= 2:
                recent_trend = (recent_values[-1] - recent_values[0]) / len(recent_values)
                
                # Calculate expected next value based on trend
                expected_value = recent_values[-1] + recent_trend
                
                # Check if current value deviates significantly from trend
                trend_deviation = abs(value - expected_value)
                relative_deviation = trend_deviation / (abs(expected_value) + 1e-10)
                
                if relative_deviation > self.config["trend_change_threshold"]:
                    anomalies.append({
                        "type": "trend_anomaly",
                        "indicator": indicator_name,
                        "value": value,
                        "expected_value": expected_value,
                        "trend_deviation": trend_deviation,
                        "relative_deviation": relative_deviation,
                        "severity": self._calculate_severity(relative_deviation, "trend"),
                        "description": f"{indicator_name} value {value} deviates from trend (expected: {expected_value:.2f})"
                    })
            
        except Exception as e:
            logger.error(f"Error in trend anomaly detection for {indicator_name}: {e}")
        
        return anomalies
    
    def _detect_correlation_anomalies(self, indicators: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect anomalies in cross-indicator correlations"""
        anomalies = []
        
        # Known economic indicator correlations (simplified)
        known_correlations = {
            ("unemployment_rate", "inflation_rate"): -0.5,  # Phillips curve
            ("interest_rate", "inflation_rate"): 0.7,       # Monetary policy response
            ("gdp_growth", "unemployment_rate"): -0.6,      # Okun's law
            ("exchange_rate", "inflation_rate"): -0.3       # Import price effects
        }
        
        try:
            for (indicator1, indicator2), expected_corr in known_correlations.items():
                if indicator1 in indicators and indicator2 in indicators:
                    # Check if both indicators have sufficient historical data
                    if (indicator1 in self.historical_data and indicator2 in self.historical_data and
                        len(self.historical_data[indicator1]) >= 10 and 
                        len(self.historical_data[indicator2]) >= 10):
                        
                        # Calculate actual correlation
                        hist1 = list(self.historical_data[indicator1])
                        hist2 = list(self.historical_data[indicator2])
                        
                        # Ensure same length
                        min_len = min(len(hist1), len(hist2))
                        hist1 = hist1[-min_len:]
                        hist2 = hist2[-min_len:]
                        
                        actual_corr = np.corrcoef(hist1, hist2)[0, 1]
                        
                        # Check for correlation breakdown
                        if abs(actual_corr - expected_corr) > self.config["correlation_threshold"]:
                            anomalies.append({
                                "type": "correlation_anomaly",
                                "indicators": [indicator1, indicator2],
                                "values": [indicators[indicator1], indicators[indicator2]],
                                "expected_correlation": expected_corr,
                                "actual_correlation": actual_corr,
                                "correlation_deviation": abs(actual_corr - expected_corr),
                                "severity": self._calculate_severity(
                                    abs(actual_corr - expected_corr), "correlation"
                                ),
                                "description": f"Correlation between {indicator1} and {indicator2} deviating from expected"
                            })
            
        except Exception as e:
            logger.error(f"Error in correlation anomaly detection: {e}")
        
        return anomalies
    
    def _calculate_severity(self, metric_value: float, metric_type: str) -> str:
        """Calculate anomaly severity based on metric value and type"""
        if metric_type == "z_score":
            if metric_value > 5:
                return "critical"
            elif metric_value > 4:
                return "high"
            elif metric_value > 3:
                return "medium"
            else:
                return "low"
        elif metric_type == "iqr":
            if metric_value > 3:
                return "critical"
            elif metric_value > 2:
                return "high"
            elif metric_value > 1.5:
                return "medium"
            else:
                return "low"
        elif metric_type == "trend":
            if metric_value > 0.8:
                return "critical"
            elif metric_value > 0.6:
                return "high"
            elif metric_value > 0.4:
                return "medium"
            else:
                return "low"
        elif metric_type == "correlation":
            if metric_value > 0.9:
                return "critical"
            elif metric_value > 0.7:
                return "high"
            elif metric_value > 0.5:
                return "medium"
            else:
                return "low"
        else:
            return "medium"  # Default
    
    def _deduplicate_and_rank_anomalies(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate anomalies and rank by severity"""
        if not anomalies:
            return []
        
        # Remove duplicates based on indicator and type
        seen = set()
        unique_anomalies = []
        
        for anomaly in anomalies:
            key = (anomaly.get("indicator", ""), anomaly.get("type", ""))
            if key not in seen:
                seen.add(key)
                unique_anomalies.append(anomaly)
        
        # Sort by severity (critical > high > medium > low)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unique_anomalies.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
        
        return unique_anomalies
    
    def _apply_anomaly_data(self, adapter: ItemAdapter, anomalies: List[Dict[str, Any]]):
        """Apply anomaly detection results to the item"""
        try:
            adapter["anomalies_detected"] = anomalies
            adapter["anomaly_count"] = len(anomalies)
            adapter["has_critical_anomalies"] = any(a.get("severity") == "critical" for a in anomalies)
            adapter["anomaly_detection_timestamp"] = datetime.now().isoformat()
            
            # Create summary statistics
            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            anomaly_types = set()
            
            for anomaly in anomalies:
                severity = anomaly.get("severity", "low")
                severity_counts[severity] += 1
                anomaly_types.add(anomaly.get("type", "unknown"))
            
            adapter["anomaly_severity_counts"] = severity_counts
            adapter["anomaly_types"] = list(anomaly_types)
            
            # Update global tracking
            for anomaly in anomalies:
                self.detected_anomalies.append({
                    **anomaly,
                    "timestamp": datetime.now().isoformat(),
                    "source": adapter.get("url", "unknown")
                })
                
                anomaly_key = f"{anomaly.get('type', 'unknown')}_{anomaly.get('indicator', 'unknown')}"
                self.anomaly_patterns[anomaly_key] += 1
            
        except Exception as e:
            logger.error(f"Error applying anomaly data to item: {e}")
    
    def _generate_alerts(self, critical_anomalies: List[Dict[str, Any]], adapter: ItemAdapter):
        """Generate alerts for critical anomalies"""
        try:
            for anomaly in critical_anomalies:
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "alert_type": "economic_anomaly",
                    "severity": anomaly.get("severity", "unknown"),
                    "indicator": anomaly.get("indicator", "unknown"),
                    "value": anomaly.get("value"),
                    "description": anomaly.get("description", ""),
                    "source": adapter.get("url", "unknown"),
                    "data_source": adapter.get("source", "unknown")
                }
                
                # Log the alert
                logger.warning(f"ECONOMIC ANOMALY ALERT: {alert['description']}")
                
                # Here you could integrate with external alerting systems
                # self._send_to_alerting_system(alert)
                
                self.stats["alerts_generated"] += 1
            
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
    
    def _update_historical_data(self, indicators: Dict[str, float]):
        """Update historical data with new indicator values"""
        for indicator_name, value in indicators.items():
            self.historical_data[indicator_name].append(value)
            
            # Update running statistics
            historical_values = list(self.historical_data[indicator_name])
            if len(historical_values) >= 2:
                self.indicator_stats[indicator_name] = {
                    "mean": statistics.mean(historical_values),
                    "std": statistics.stdev(historical_values) if len(historical_values) > 1 else 0,
                    "min": min(historical_values),
                    "max": max(historical_values),
                    "count": len(historical_values),
                    "last_updated": time.time()
                }
    
    def _load_historical_data(self):
        """Load historical data for anomaly detection (placeholder)"""
        # In a real implementation, this would load from a database
        logger.info("Loading historical data for anomaly detection")
    
    def _initialize_indicator_stats(self):
        """Initialize indicator statistics (placeholder)"""
        logger.info("Initializing indicator statistics")
    
    def _save_anomaly_results(self):
        """Save anomaly detection results"""
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "total_anomalies": len(self.detected_anomalies),
                "anomaly_patterns": dict(self.anomaly_patterns),
                "statistics": self.get_stats(),
                "recent_anomalies": self.detected_anomalies[-50:]  # Last 50 anomalies
            }
            
            # Save to file (in production, this would go to a database)
            output_file = f"anomaly_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Saved anomaly results to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving anomaly results: {e}")
    
    def _generate_anomaly_report(self):
        """Generate summary report of anomaly detection"""
        try:
            stats = self.get_stats()
            
            report = f"""
            Anomaly Detection Summary Report
            ================================
            
            Processing Statistics:
            - Items Processed: {stats['items_processed']}
            - Anomalies Detected: {stats['anomalies_detected']}
            - Alerts Generated: {stats['alerts_generated']}
            - Average Processing Time: {stats['avg_processing_time_ms']:.2f}ms
            - Anomaly Detection Rate: {stats['anomaly_rate']:.2%}
            
            Top Anomaly Patterns:
            """
            
            # Add top anomaly patterns
            sorted_patterns = sorted(
                self.anomaly_patterns.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            for pattern, count in sorted_patterns:
                report += f"- {pattern}: {count} occurrences\n"
            
            logger.info(report)
            
        except Exception as e:
            logger.error(f"Error generating anomaly report: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        processing_times = list(self.stats["processing_time_ms"])
        
        stats = self.stats.copy()
        
        if processing_times:
            stats["avg_processing_time_ms"] = statistics.mean(processing_times)
            stats["max_processing_time_ms"] = max(processing_times)
        else:
            stats["avg_processing_time_ms"] = 0
            stats["max_processing_time_ms"] = 0
        
        if stats["items_processed"] > 0:
            stats["anomaly_rate"] = stats["anomalies_detected"] / stats["items_processed"]
        else:
            stats["anomaly_rate"] = 0
        
        stats["total_patterns"] = len(self.anomaly_patterns)
        stats["unique_anomaly_types"] = len(set(
            anomaly.get("type", "unknown") for anomaly in self.detected_anomalies
        ))
        
        return stats