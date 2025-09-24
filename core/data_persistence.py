"""Data persistence handler for the Image Ranking System with binning support - tier bounds system removed."""

import json
import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional


class DataPersistence:
    """Handles saving and loading data to/from JSON files including binned images."""
    
    CURRENT_VERSION = '2.2'
    REQUIRED_FIELDS = ['image_folder', 'vote_count', 'image_stats']
    
    def save_to_file(self, filename: str, data: Dict[str, Any]) -> bool:
        """
        Save data to a JSON file.
        
        Args:
            filename: Path to save the file
            data: Dictionary containing all data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add metadata
            data['timestamp'] = datetime.now().isoformat()
            data['version'] = self.CURRENT_VERSION
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def load_from_file(self, filename: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Load data from a JSON file.
        
        Args:
            filename: Path to load the file from
            
        Returns:
            Tuple of (success, data, error_message)
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            for field in self.REQUIRED_FIELDS:
                if field not in data:
                    return False, {}, f"Missing required field: {field}"
            
            return True, data, ""
            
        except json.JSONDecodeError as e:
            return False, {}, f"Invalid JSON format: {e}"
        except FileNotFoundError:
            return False, {}, "File not found"
        except Exception as e:
            return False, {}, f"Error loading data: {e}"
    
    def validate_and_fix_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and fix common data inconsistencies.
        
        Args:
            data: Loaded data dictionary
            
        Returns:
            Fixed data dictionary
        """
        # Fix vote count inconsistencies
        if 'image_stats' in data:
            fixed_count = 0
            for image_filename, stats in data['image_stats'].items():
                wins = stats.get('wins', 0)
                losses = stats.get('losses', 0)
                votes = stats.get('votes', 0)
                expected_votes = wins + losses
                
                if votes != expected_votes:
                    stats['votes'] = expected_votes
                    fixed_count += 1
            
            if fixed_count > 0:
                print(f"Corrected vote count inconsistencies for {fixed_count} images")
        
        return data
    
    def prepare_save_data(self, core_data: Dict[str, Any], 
                         weight_data: Dict[str, Any],
                         algorithm_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare save data without tier bounds settings.
        
        Args:
            core_data: Core data (image_folder, vote_count, image_stats, metadata_cache, binned_images)
            weight_data: Weight manager export data
            algorithm_settings: Algorithm settings export
            
        Returns:
            Complete data dictionary ready for saving
        """
        save_data = core_data.copy()
        save_data.update(weight_data)
        save_data.update(algorithm_settings)
        
        # Ensure binned_images is included
        if 'binned_images' not in save_data:
            save_data['binned_images'] = []
        
        return save_data
    
    def extract_core_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract core data including binned images.
        
        Args:
            data: Complete loaded data
            
        Returns:
            Dictionary with only core data fields
        """
        return {
            'image_folder': data.get('image_folder', ''),
            'vote_count': data.get('vote_count', 0),
            'image_stats': data.get('image_stats', {}),
            'metadata_cache': data.get('metadata_cache', {}),
            'binned_images': set(data.get('binned_images', []))  # Convert to set
        }
    
    def get_version(self, data: Dict[str, Any]) -> str:
        """Get the version of the loaded data."""
        return data.get('version', '1.0')
    
    def needs_migration(self, data: Dict[str, Any]) -> bool:
        """Check if data needs migration to current version."""
        version = self.get_version(data)
        return version != self.CURRENT_VERSION
    
    def migrate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate data from older versions to current version.
        
        Args:
            data: Data to migrate
            
        Returns:
            Migrated data
        """
        version = self.get_version(data)
        
        # Add any version-specific migrations here
        if version in ['1.0', '2.0', '2.1']:
            # Remove tier bounds settings if present from older versions
            if 'tier_bounds_settings' in data:
                del data['tier_bounds_settings']
                print(f"Removed deprecated tier bounds settings from version {version}")
            
            print(f"Migrated data from version {version} to {self.CURRENT_VERSION}")
        
        return data
    
    def create_backup(self, filename: str) -> Optional[str]:
        """
        Create a backup of an existing file before overwriting.
        
        Args:
            filename: File to backup
            
        Returns:
            Path to backup file if created, None otherwise
        """
        if not os.path.exists(filename):
            return None
        
        try:
            backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(filename, 'r') as source:
                with open(backup_name, 'w') as backup:
                    backup.write(source.read())
            return backup_name
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
