"""
Ledger charting functionality for MapleLegends ShopHelper
Provides visualization of financial data over time
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
import time

class LedgerChartWidget(QWidget):
    """Widget for displaying ledger data in chart form"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the UI
        self.setup_ui()
        
        # Initialize data
        self.chart_data = {
            'timestamps': [],
            'sales_values': [],
            'capital_values': [],
            'cash_values': []
        }
        
        # Default chart settings
        self.chart_type = 'line'  # Default chart type
        self.time_period = 30     # Default time period (days)
        
    def setup_ui(self):
        """Set up the UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        self.setStyleSheet("background-color: #2D2D2D; color: #E0E0E0;")
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Chart type selector
        self.type_label = QLabel("Chart Type:")
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
        self.type_combo.addItem("Line Chart", "line")
        self.type_combo.addItem("Bar Chart", "bar")
        self.type_combo.addItem("Stacked Bar Chart", "stacked")
        self.type_combo.currentIndexChanged.connect(self.update_chart)
        
        # Time period selector
        self.period_label = QLabel("Time Period:")
        self.period_combo = QComboBox()
        self.period_combo.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
        self.period_combo.addItem("Last 7 Days", 7)
        self.period_combo.addItem("Last 30 Days", 30)
        self.period_combo.addItem("Last 90 Days", 90)
        self.period_combo.addItem("All Time", 0)
        self.period_combo.setCurrentIndex(1)  # Default to 30 days
        self.period_combo.currentIndexChanged.connect(self.update_chart)
        
        # Add controls to layout
        controls_layout.addWidget(self.type_label)
        controls_layout.addWidget(self.type_combo)
        controls_layout.addWidget(self.period_label)
        controls_layout.addWidget(self.period_combo)
        controls_layout.addStretch()
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.figure.patch.set_facecolor('#2D2D2D')  # Set figure background color
        self.canvas = FigureCanvas(self.figure)
        
        # Add components to main layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.canvas)
        
    def set_data(self, data):
        """Set chart data
        
        Args:
            data: Dictionary with timestamps, sales_values, capital_values, and cash_values lists
        """
        self.chart_data = data
        self.update_chart()
        
    def update_chart(self):
        """Update the chart with current data and settings"""
        # Get chart type and time period
        self.chart_type = self.type_combo.currentData()
        self.time_period = self.period_combo.currentData()
        
        # Clear the figure
        self.figure.clear()
        
        # Create subplot with adjusted spacing
        self.figure.subplots_adjust(bottom=0.15, left=0.1, right=0.95, top=0.9)
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#3D3D3D')  # Set plot background color
        
        # Set text color to white for dark mode
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
        
        # Filter data by time period if needed
        timestamps = self.chart_data.get('timestamps', [])
        sales_values = self.chart_data.get('sales_values', [])
        capital_values = self.chart_data.get('capital_values', [])
        cash_values = self.chart_data.get('cash_values', [])
        
        if not timestamps:
            # No data to display
            ax.set_title("No Data Available")
            self.canvas.draw()
            return
            
        # Filter by time period if not "All Time"
        if self.time_period > 0:
            cutoff_date = datetime.now() - timedelta(days=self.time_period)
            
            # Create filtered lists
            filtered_data = [(t, s, c, ca) for t, s, c, ca in zip(timestamps, sales_values, capital_values, cash_values) 
                            if isinstance(t, datetime) and t >= cutoff_date]
            
            if filtered_data:
                timestamps, sales_values, capital_values, cash_values = zip(*filtered_data)
            else:
                # No data in the selected time period
                ax.set_title(f"No Data Available for Last {self.time_period} Days")
                self.canvas.draw()
                return
        
        # Create the chart based on type
        if self.chart_type == 'line':
            # Line chart
            ax.plot(timestamps, sales_values, 'g-', label='Sales', linewidth=2)
            ax.plot(timestamps, capital_values, 'b-', label='Incoming Capital', linewidth=2)
            ax.plot(timestamps, cash_values, 'y-', label='Cash Flow', linewidth=2)
            
            # Add value annotations for significant points
            for i, (t, s, c, ca) in enumerate(zip(timestamps, sales_values, capital_values, cash_values)):
                # Only annotate points with significant values (over 1 million)
                if s > 1000000:
                    ax.annotate(f"{s/1000000:.1f}M", (t, s), textcoords="offset points", 
                                xytext=(0,10), ha='center', color='white', fontsize=8)
                if c > 1000000:
                    ax.annotate(f"{c/1000000:.1f}M", (t, c), textcoords="offset points", 
                                xytext=(0,10), ha='center', color='white', fontsize=8)
                if abs(ca) > 1000000:
                    ax.annotate(f"{ca/1000000:.1f}M", (t, ca), textcoords="offset points", 
                                xytext=(0,10), ha='center', color='white', fontsize=8)
                
        elif self.chart_type == 'bar':
            # Bar chart
            bar_width = 0.25
            index = range(len(timestamps))
            
            # Position bars side by side
            sales_bars = ax.bar([i - bar_width for i in index], sales_values, bar_width, 
                   label='Sales', color='#50C878')
            capital_bars = ax.bar(index, capital_values, bar_width, 
                   label='Incoming Capital', color='#4B9CD3')
            cash_bars = ax.bar([i + bar_width for i in index], cash_values, bar_width, 
                   label='Cash Flow', color='#FFD700')
            
            # Add value labels on top of bars
            self._add_value_labels(ax, sales_bars)
            self._add_value_labels(ax, capital_bars)
            self._add_value_labels(ax, cash_bars)
            
            # Set x-ticks to dates
            ax.set_xticks(index)
            ax.set_xticklabels([t.strftime('%m/%d') for t in timestamps], rotation=45)
        else:  # stacked bar chart
            # Stacked bar chart
            index = range(len(timestamps))
            
            # Create stacked bars
            sales_bars = ax.bar(index, sales_values, label='Sales', color='#50C878')
            
            # Only add positive cash values to the stack
            positive_cash = [max(0, val) for val in cash_values]
            cash_bars = ax.bar(index, positive_cash, bottom=sales_values, 
                   label='Cash Flow (Positive)', color='#FFD700')
            
            # Add capital as a separate bar
            capital_bars = ax.bar([i + 0.3 for i in index], capital_values, width=0.3, label='Incoming Capital', 
                   color='#4B9CD3', alpha=0.7)
            
            # Show negative cash values as separate bars below zero
            negative_cash = [min(0, val) for val in cash_values]
            if any(val < 0 for val in negative_cash):
                neg_cash_bars = ax.bar(index, negative_cash, label='Cash Flow (Negative)', 
                       color='#FF6B6B')
                # Add value labels for negative cash
                self._add_value_labels(ax, neg_cash_bars)
            
            # Add value labels
            self._add_value_labels(ax, sales_bars)
            self._add_value_labels(ax, cash_bars)
            self._add_value_labels(ax, capital_bars)
            
            # Set x-ticks to dates
            ax.set_xticks(index)
            ax.set_xticklabels([t.strftime('%m/%d') for t in timestamps], rotation=45)
        
        # Format the x-axis for dates
        if self.chart_type == 'line':
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Add grid, legend, and labels
        ax.grid(True, linestyle='--', alpha=0.7, color='#555555')
        ax.legend(facecolor='#3D3D3D', edgecolor='#555555', labelcolor='white')
        
        # Set labels
        ax.set_xlabel('Date')
        ax.set_ylabel('Mesos')
        ax.set_title('Financial Activity Over Time')
        
        # Format y-axis with commas for thousands and M for millions
        ax.get_yaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, loc: self._format_meso_value(x)))
        
        # Adjust spacing to prevent clipping
        self.figure.tight_layout()
        
        # Draw the canvas
        self.canvas.draw()
        
    def _format_meso_value(self, value):
        """Format meso values with M for millions, K for thousands"""
        abs_val = abs(value)
        if abs_val >= 1000000:
            return f"{value/1000000:.1f}M"
        elif abs_val >= 1000:
            return f"{value/1000:.0f}K"
        else:
            return f"{int(value)}"
            
    def _add_value_labels(self, ax, bars):
        """Add value labels on top of bars"""
        for bar in bars:
            height = bar.get_height()
            if height == 0:
                continue
                
            # Format the value
            value_text = self._format_meso_value(height)
            
            # Position the text above the bar
            ax.text(
                bar.get_x() + bar.get_width()/2, 
                height + (0.05 * height if height > 0 else -0.1 * height),
                value_text,
                ha='center', 
                va='bottom' if height > 0 else 'top',
                color='white',
                fontsize=8,
                rotation=0
            )
        
    def generate_sample_data(self):
        """Generate sample data for testing"""
        # This is just for development/testing
        now = datetime.now()
        timestamps = [now - timedelta(days=i) for i in range(30, 0, -1)]
        
        # Generate some random-ish but realistic looking data
        import random
        sales_values = [random.randint(500000, 2000000) for _ in range(30)]
        capital_values = [random.randint(300000, 1500000) for _ in range(30)]
        cash_values = [random.randint(-500000, 500000) for _ in range(30)]
        
        # Sort by date
        data = list(zip(timestamps, sales_values, capital_values, cash_values))
        data.sort(key=lambda x: x[0])
        timestamps, sales_values, capital_values, cash_values = zip(*data)
        
        self.chart_data = {
            'timestamps': timestamps,
            'sales_values': sales_values,
            'capital_values': capital_values,
            'cash_values': cash_values
        }
        
        self.update_chart()
