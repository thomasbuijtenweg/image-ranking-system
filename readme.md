# Image Ranking System

A pairwise comparison system for ranking large image collections through intelligent voting algorithms with AI-generated content support.

## Overview

The Image Ranking System helps you compare and rank image collections by presenting them in pairs and asking "which one do you prefer?" Images are organized into a tier-based ranking system where they move up or down based on voting outcomes.

## Key Features

### 🧠 Advanced Pair Selection Algorithm
- **Dual-weight system**: Separate algorithm weights for left and right image selection
- **Multi-factor prioritization**: Considers recency, vote count, tier stability, and tier population
- **Smart tier distribution**: Uses normal distribution centered at tier 0 for balanced rankings

### 🎨 AI-Generated Image Support
- **Automatic prompt extraction** from PNG text chunks, EXIF data, and PIL metadata
- **Intelligent prompt analysis** that correlates specific words with image tier performance
- **Metadata caching** for improved performance with large collections

### ⚡ Performance Optimizations
- **Background processing** for metadata extraction from thousands of images
- **Image preloading** for smooth transitions between voting pairs
- **Memory management** and garbage collection for extended use

### 🖥️ User-Friendly Interface
- **Dark theme** optimized for extended voting sessions
- **Image preview on hover** in rankings and statistics windows
- **Keyboard shortcuts** for efficient voting (arrow keys, letters)

### 📊 Comprehensive Analytics
- **Multiple ranking views**: Sort by tier, win rate, total votes, or stability
- **Individual image tracking**: Complete voting history and tier progression
- **Prompt word analysis**: Discover which words correlate with higher rankings
- **Export capabilities**: Save rankings and word analysis to CSV files

### 🔧 Customizable Algorithm
- **Independent left/right weights**: Different priorities for each side of comparison
- **Stability preferences**: Choose to prioritize stable or unstable tier positions
- **Vote count preferences**: Focus on heavily-voted or lightly-voted images

## Installation

1. **Install Python 3.8+**
2. **Install dependencies**:
   ```bash
   pip install Pillow
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

## Quick Start

1. **Select a folder** containing your images using "Select Image Folder"
2. **Start voting** by clicking your preferred image or using arrow keys (← for left, → for right)
3. **View progress** in real-time as images move between tiers
4. **Analyze results** using "View Rankings" and "View Stats" buttons
5. **Save your work** regularly with "Save Progress"

### Keyboard Shortcuts
- **Left Arrow** or **A**: Vote for left image
- **Right Arrow** or **D**: Vote for right image
- **Ctrl+S**: Save progress
- **Ctrl+O**: Load progress
- **Ctrl+R**: View rankings
- **Ctrl+T**: View statistics

## Understanding the Algorithm

The system uses a multi-factor algorithm with separate weights for left and right image selection:

**New Image Introduction**: Unvoted images are paired with tier 0 images for initial positioning.

**Intelligent Matching**: Images are primarily compared within the same tier or adjacent tiers to refine rankings.

**Priority Scoring**: Each image receives priority scores based on:
- **Recency**: How recently it was voted on
- **Vote Count**: Total number of comparisons
- **Stability**: How much its tier position fluctuates
- **Tier Size**: How crowded its current tier is relative to expected distribution

**Separate Selection**: Left and right images are chosen independently using their respective weight sets.

## AI Prompt Analysis

For AI-generated images, the system automatically:
- Extracts generation prompts from image metadata
- Analyzes which words correlate with higher tier rankings
- Provides statistics on word performance across your collection
- Helps identify effective prompt patterns for quality image generation

## System Requirements

- **Python 3.8+**
- **Pillow (PIL)** for image processing
- **4GB+ RAM** recommended for large collections (10,000+ images)
- **Modern display** for optimal image preview experience