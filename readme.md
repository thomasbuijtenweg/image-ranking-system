# Image Ranking System

A sophisticated pairwise comparison system for ranking collections of images through intelligent voting algorithms.

## Overview

The Image Ranking System helps users systematically compare and rank large collections of images by presenting them in pairs and asking "which one do you prefer?" This approach is psychologically easier than ranking dozens of images at once and produces more consistent results.

The system implements a tier-based ranking algorithm where images start at "Tier 0" and move up or down based on voting outcomes. Over time, the best images naturally rise to higher tiers while weaker images settle into lower tiers.

## Key Features

### Intelligent Pair Selection
- **Priority-based algorithm** that considers multiple factors:
  - **Recency**: How recently an image was voted on
  - **Vote count**: Prioritizes images with fewer total votes
  - **Stability**: Prioritizes images with unstable tier positions
  - **Tier size**: Prioritizes images in crowded tiers

### AI Image Support
- **Automatic prompt extraction** from AI-generated images
- **Metadata display** showing generation parameters
- **Multiple format support** (PNG text chunks, EXIF data, PIL info)

### Comprehensive Statistics
- **Real-time tier tracking** with history for each image
- **Individual stability measurements** using standard deviation
- **Detailed matchup history** and win/loss records
- **Multiple ranking views** (tier, win rate, total votes, stability)

### User-Friendly Interface
- **Dark theme** optimized for extended use
- **Responsive design** that adapts to different screen sizes
- **Keyboard shortcuts** for efficient voting
- **Image preloading** for smooth transitions between pairs

### Data Persistence
- **JSON-based save/load** functionality
- **Data validation** and integrity checking
- **CSV export** for further analysis
- **Configurable algorithm weights**

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/image-ranking-system.git
   cd image-ranking-system
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

### Basic Workflow

1. **Select a folder** containing your images using the "Select Image Folder" button
2. **Start voting** by clicking on your preferred image or using arrow keys (← for left, → for right)
3. **Save your progress** regularly using the "Save Progress" button
4. **View results** using the "View Rankings" and "View Stats" buttons

### Keyboard Shortcuts

- **Left Arrow** or **A**: Vote for left image
- **Right Arrow** or **D**: Vote for right image
- **Ctrl+S**: Save progress
- **Ctrl+O**: Load progress
- **Ctrl+R**: View rankings
- **Ctrl+T**: View statistics
- **Ctrl+,**: Open settings

### Understanding the Algorithm

The system uses a sophisticated multi-factor algorithm to determine which images to compare next:

**New Image Introduction**: When an image has never been voted on, it gets paired with an image from Tier 0 or the closest available tier.

**Tier-Based Matching**: Under normal circumstances, images are compared within the same tier or adjacent tiers, helping to refine rankings within similar quality levels.

**Priority Scoring**: Each image receives a priority score based on:
- How recently it was voted on (less recent = higher priority)
- How many total votes it has received (fewer votes = higher priority)
- How stable its tier position is (less stable = higher priority)
- How crowded its current tier is (more crowded = higher priority)

### Customizing the Algorithm

You can adjust the algorithm's behavior through the Settings window:

- **Recency Weight**: Controls how much the system prioritizes recently unvoted images
- **Low Votes Weight**: Controls how much the system prioritizes images with fewer total votes
- **Instability Weight**: Controls how much the system prioritizes images with unstable tier positions
- **Tier Size Weight**: Controls how much the system prioritizes images in crowded tiers

All weights should sum to 1.0 for optimal performance.

## Project Structure

```
image_ranking_system/
├── main.py                    # Application entry point
├── config.py                  # Configuration constants and themes
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── core/
│   ├── __init__.py
│   ├── data_manager.py       # Data persistence and management
│   ├── image_processor.py    # Image loading and metadata extraction
│   └── ranking_algorithm.py  # Intelligent pair selection algorithm
├── ui/
│   ├── __init__.py
│   ├── main_window.py        # Main voting interface
│   ├── rankings_window.py    # Rankings display window
│   ├── stats_window.py       # Statistics and analytics window
│   └── settings_window.py    # Configuration and settings window
└── utils/
    ├── __init__.py
    └── helpers.py            # Utility functions (if needed)
```

## Technical Details

### Architecture

The application follows a modular architecture with clear separation of concerns:

- **Core modules** handle business logic (data management, image processing, ranking algorithms)
- **UI modules** handle user interface components
- **Configuration** is centralized for easy customization
- **Entry point** is kept simple and focused

### Data Format

Rankings are stored in JSON format with the following structure:

```json
{
  "image_folder": "/path/to/images",
  "vote_count": 150,
  "weights": {
    "recency": 0.25,
    "low_votes": 0.25,
    "instability": 0.25,
    "tier_size": 0.25
  },
  "image_stats": {
    "image1.jpg": {
      "votes": 12,
      "wins": 8,
      "losses": 4,
      "current_tier": 2,
      "tier_history": [0, 1, 2, 1, 2],
      "last_voted": 145,
      "matchup_history": [...],
      "prompt": "Generated image prompt...",
      "display_metadata": "Size: 1024x1024..."
    }
  }
}
```

### Performance Optimizations

- **Image preloading**: Next pair is loaded in background while user makes current vote
- **Cached calculations**: Rankings are cached and only recalculated when needed
- **Efficient data structures**: Uses appropriate data structures for fast lookups
- **Responsive UI**: Heavy calculations happen in background threads

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Python and tkinter for maximum compatibility
- Uses Pillow (PIL) for image processing
- Inspired by the need for systematic preference evaluation in creative work

## Future Enhancements

- **Multi-user support**: Allow multiple users to vote on the same collection
- **Web interface**: Browser-based version for easier sharing
- **Advanced statistics**: More detailed analytics and visualization
- **Batch operations**: Tools for managing large image collections
- **Machine learning**: Optional AI-assisted ranking predictions