import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import Investment


class InvestmentStorage:
    """Handles storage and retrieval of investment data."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize storage with specified data directory."""
        if data_dir is None:
            data_dir = Path.cwd() / "data"
        self.data_dir = data_dir
        self.file_path = data_dir / "investments.json"
        self.backup_dir = data_dir / "backups"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

    def load_investments(self) -> List[Investment]:
        """Load all investments from JSON file."""
        if not self.file_path.exists():
            return []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            investments = []
            for inv_data in data.get('investments', []):
                try:
                    investments.append(Investment.from_dict(inv_data))
                except Exception as e:
                    print(f"Warning: Failed to load investment {inv_data.get('id', 'unknown')}: {e}")
                    continue
            
            return investments

        except json.JSONDecodeError as e:
            print(f"Error: Corrupted JSON file. Loading from backup if available.")
            return self._load_from_backup()
        except Exception as e:
            print(f"Error loading investments: {e}")
            return []

    def save_investments(self, investments: List[Investment]) -> None:
        """Save investments to JSON file with backup."""
        # Create backup before saving
        if self.file_path.exists():
            self._create_backup()

        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "investments": [inv.to_dict() for inv in investments]
        }

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving investments: {e}")
            raise

    def _create_backup(self) -> None:
        """Create a backup of the current file."""
        if not self.file_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"investments_{timestamp}.json"
        
        try:
            shutil.copy2(self.file_path, backup_path)
            # Clean up old backups, keep only last 10
            self._cleanup_old_backups(max_backups=10)
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")

    def _cleanup_old_backups(self, max_backups: int = 10) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        backup_files = self.get_backup_files()
        
        if len(backup_files) > max_backups:
            # Remove oldest backups (files are sorted by modification time, newest first)
            files_to_remove = backup_files[max_backups:]
            for backup_file in files_to_remove:
                try:
                    backup_file.unlink()
                except Exception as e:
                    print(f"Warning: Failed to remove old backup {backup_file.name}: {e}")

    def _load_from_backup(self) -> List[Investment]:
        """Load investments from the most recent backup."""
        backup_files = list(self.backup_dir.glob("investments_*.json"))
        
        if not backup_files:
            print("No backup files found.")
            return []

        # Get the most recent backup
        latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_backup, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            investments = []
            for inv_data in data.get('investments', []):
                investments.append(Investment.from_dict(inv_data))
            
            print(f"Loaded data from backup: {latest_backup.name}")
            return investments

        except Exception as e:
            print(f"Error loading from backup: {e}")
            return []

    def get_backup_files(self) -> List[Path]:
        """Get list of backup files sorted by modification time."""
        backup_files = list(self.backup_dir.glob("investments_*.json"))
        return sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True)

    def restore_from_backup(self, backup_path: Path) -> None:
        """Restore investments from a specific backup file."""
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Create backup of current file before restoring
        if self.file_path.exists():
            self._create_backup()

        try:
            shutil.copy2(backup_path, self.file_path)
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            raise

    def clear_all_data(self) -> None:
        """Clear all investment data (creates backup first)."""
        if self.file_path.exists():
            self._create_backup()
        self.save_investments([])

    def export_to_csv(self, csv_path: Path) -> None:
        """Export investments to CSV format."""
        import csv
        
        investments = self.load_investments()
        
        if not investments:
            print("No investments to export.")
            return

        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Name', 'Timeframe', 'Final Amount', 'Percentage Change',
                    'Original Amount', 'Profit/Loss', 'Created At', 'Updated At'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for inv in investments:
                    writer.writerow({
                        'Name': inv.name,
                        'Timeframe': inv.timeframe,
                        'Final Amount': inv.final_amount,
                        'Percentage Change': inv.percentage_change,
                        'Original Amount': inv.original_amount,
                        'Profit/Loss': inv.profit_loss_amount,
                        'Created At': inv.created_at.isoformat(),
                        'Updated At': inv.updated_at.isoformat(),
                    })
            
            print(f"Exported {len(investments)} investments to {csv_path}")

        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            raise