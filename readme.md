# Image Ranking System

A sophisticated pairwise comparison system for ranking large image collections using advanced algorithms, AI-generated content analysis, and intelligent tier management.

## 🎯 Overview

The Image Ranking System is a professional-grade tool for organizing and ranking image collections through intelligent pairwise comparisons. It uses advanced algorithms with tier overflow detection, confidence-based selection, and adaptive tier bounds to create stable, meaningful rankings from user preferences.

## ✨ Key Features

### 🧠 Advanced Algorithm Engine
- **Intelligent Pair Selection**: Dual-weight system with separate algorithms for left and right image selection
- **Tier Overflow Detection**: Automatically identifies and prioritizes overcrowded tiers for optimal distribution
- **Confidence-Based Ranking**: Uses voting history and tier stability to calculate image confidence scores
- **Adaptive Tier Bounds**: Prevents runaway tier inflation while allowing exceptional images to reach extremes
- **Strategic Timing**: New images are strategically placed to optimize their initial ranking opportunities

### 🎨 AI-Generated Content Support
- **Automatic Prompt Extraction**: Reads generation prompts from PNG text chunks, EXIF data, and metadata
- **Prompt Analysis Engine**: Correlates specific words with image tier performance
- **Word Performance Tracking**: Identifies which prompt elements lead to higher-ranked images
- **Metadata Caching**: Efficient background processing for large collections

### 📊 Comprehensive Analytics
- **Real-time Statistics**: Live tracking of votes, win rates, and tier distributions
- **Tier Distribution Charts**: Visual representation with normal distribution overlay
- **Individual Image Tracking**: Complete voting history and tier progression for each image
- **Confidence Calculations**: Advanced stability metrics using square root scaling
- **Export Capabilities**: CSV export for rankings, statistics, and word analysis

### 🎮 Professional Interface
- **Dark Theme**: Optimized for extended use with reduced eye strain
- **Hover Preview**: Instant image preview in statistics and analysis windows
- **Keyboard Shortcuts**: Efficient voting with arrow keys and customizable hotkeys
- **Progress Tracking**: Visual progress indicators for long-running operations
- **Multi-tab Interface**: Organized statistics, analysis, and settings panels

### ⚙️ Advanced Configuration
- **Algorithmic Tuning**: Adjustable parameters for tier distribution, overflow detection, and confidence calculation
- **Tier Bounds Management**: Configurable bounds with qualification requirements
- **Dual-Weight System**: Independent algorithm weights for left and right selection
- **Adaptive Settings**: Algorithm parameters that scale with collection size

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- 4GB+ RAM recommended for large collections (10,000+ images)

### Setup
1. **Clone or download** the repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

### Optional Dependencies
For enhanced chart functionality:
```bash
pip install matplotlib numpy
```

## 🎯 Quick Start Guide

### Basic Workflow
1. **Select Image Folder**: Choose your image collection (supports subfolders)
2. **Start Ranking**: Vote on image pairs using mouse clicks or keyboard shortcuts
3. **Monitor Progress**: Watch real-time statistics and tier distributions
4. **Analyze Results**: Use the comprehensive analytics to understand your preferences
5. **Save & Export**: Preserve your rankings and export data for external analysis

### Keyboard Shortcuts
- **← / A**: Vote for left image
- **→ / D**: Vote for right image
- **Ctrl+S**: Save progress
- **Ctrl+O**: Load saved progress
- **Ctrl+T**: Open statistics window
- **Ctrl+P**: Open prompt analysis
- **Ctrl+,**: Open settings

## 📈 Understanding the Algorithm

### Tier System
Images are organized into tiers ranging from negative to positive values:
- **Tier 0**: Starting point for all images
- **Positive Tiers**: Higher-ranked images
- **Negative Tiers**: Lower-ranked images
- **Tier Bounds**: Intelligent limits that prevent extreme tier inflation

### Selection Process
1. **Overflow Detection**: Identifies tiers with too many images
2. **Confidence Calculation**: Evaluates image stability using voting history
3. **Strategic Pairing**: Selects low-confidence vs. high-confidence images within overflowing tiers
4. **Fallback Mechanism**: Random selection when no tier overflow detected

### Confidence Metrics
Confidence scores combine:
- **Tier Stability**: How consistent an image's tier position has been
- **Vote Count**: Total number of comparisons (with square root scaling)
- **Recent Activity**: How recently the image was voted on

## 🔧 Advanced Configuration

### Algorithm Parameters
- **Tier Distribution Standard Deviation**: Controls expected tier spread (default: 1.5)
- **Overflow Threshold**: When a tier is considered overcrowded (default: 1.0x expected)
- **Minimum Overflow Images**: Minimum images needed to trigger overflow detection (default: 2)

### Tier Bounds Settings
- **Bounds Multiplier**: How many standard deviations to allow (default: 3.0)
- **Minimum Confidence**: Confidence threshold to exceed bounds (default: 0.8)
- **Minimum Votes**: Vote threshold to exceed bounds (default: 10)
- **Adaptive Scaling**: Whether bounds grow with collection size (default: enabled)

### Selection Weights
Customize the importance of different factors:
- **Recency**: How recently an image was voted on
- **Low Votes**: Priority for images with fewer votes
- **Instability**: Priority for images with unstable tier positions
- **Tier Size**: Priority based on tier population

## 📊 Analytics & Insights

### Statistics Window
- **Sortable Tables**: Click column headers to sort by any metric
- **Live Preview**: Hover over any row to see image preview
- **Comprehensive Metrics**: Votes, win rates, stability, confidence, and more
- **Export Options**: Save statistics to CSV for external analysis

### Prompt Analysis
- **Word Performance**: See which prompt words correlate with higher tiers
- **Frequency Analysis**: Identify common and rare prompt elements
- **Example Images**: View sample images for each analyzed word
- **Search & Filter**: Find specific words or patterns in your prompts

### Visual Charts
- **Tier Distribution**: Bar chart with normal distribution overlay
- **Progress Tracking**: Real-time updates as you vote
- **Confidence Visualization**: Graphical representation of image stability

## 💾 Data Management

### File Format
- **JSON Storage**: Human-readable format for rankings and metadata
- **Metadata Caching**: Efficient storage of image prompts and properties
- **Backward Compatibility**: Automatic upgrading of older save formats

### Export Options
- **Individual Statistics**: Complete data for each image
- **Tier Distribution**: Summary of tier populations
- **Word Analysis**: Prompt word performance data
- **Comprehensive Reports**: Executive-level summaries

## 🎨 AI Image Features

### Supported Formats
- **PNG**: Text chunks, EXIF data, PIL metadata
- **JPEG**: EXIF data extraction
- **Multiple Sources**: Automatic detection of prompt storage methods

### Analysis Features
- **Main Prompt Extraction**: Separates positive from negative prompts
- **Word Correlation**: Statistical analysis of word performance
- **Tier Prediction**: Insights into which prompt elements work best
- **Batch Processing**: Background analysis of large collections

## 🏗️ Technical Architecture

### Core Components
- **Data Manager**: Handles persistence and statistics with tier bounds
- **Ranking Algorithm**: Implements confidence-based pair selection
- **Image Processor**: Optimized loading and metadata extraction
- **Prompt Analyzer**: Advanced text analysis for AI-generated content

### UI Components
- **Modular Design**: Separate components for different functions
- **Image Display**: Efficient rendering with memory management
- **Progress Tracking**: Visual feedback for long operations
- **Settings Management**: Comprehensive configuration interface

## 🔧 Performance & Scalability

### Optimizations
- **Background Processing**: Metadata extraction doesn't block UI
- **Memory Management**: Efficient image loading and garbage collection
- **Caching Systems**: File system and metadata caching
- **Batch Operations**: Optimized handling of large collections

### Tested Scales
- **Small Collections**: 100-1,000 images (instant response)
- **Medium Collections**: 1,000-10,000 images (background processing)
- **Large Collections**: 10,000+ images (progress tracking, optimized algorithms)

## 🛠️ Development

### Project Structure
```
image-ranking-system/
├── core/                    # Business logic and algorithms
├── ui/                      # User interface components
├── config.py               # Configuration constants
├── main.py                 # Application entry point
└── requirements.txt        # Dependencies
```

### Architecture Principles
- **Separation of Concerns**: UI and business logic completely separated
- **Modular Design**: Each component has a single responsibility
- **Error Handling**: Comprehensive exception management
- **Resource Management**: Proper cleanup and memory management

## 📚 Advanced Usage

### Custom Algorithms
The system supports extensive customization:
- Modify selection weights for different ranking priorities
- Adjust tier bounds for different collection characteristics
- Configure confidence calculations for specific use cases
- Implement custom export formats

### Integration Possibilities
- **External Analytics**: CSV export for integration with data analysis tools
- **Batch Processing**: Command-line interface for automated operations
- **Custom Metadata**: Extension points for additional image properties
- **API Integration**: Potential for web service integration

## 🤝 Contributing

### Development Guidelines
- Follow the established architecture patterns
- Maintain separation between UI and business logic
- Include comprehensive error handling
- Add appropriate documentation and comments

### Testing
- Test with various image formats and sizes
- Verify algorithm behavior with different collection sizes
- Ensure UI responsiveness during long operations
- Validate data persistence and loading

## 📄 License

This project is open source. See the LICENSE file for details.

## 🙏 Acknowledgments

Built with Python and Tkinter, featuring advanced algorithms for image ranking and AI-generated content analysis. Special thanks to the open-source community for the foundational libraries and tools.

---

*Transform your image collection from chaos to clarity with intelligent, algorithm-driven ranking.*