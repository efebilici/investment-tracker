import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .models import Investment, Portfolio


class InvestmentStorage:
    """Handles storage and retrieval of portfolio and investment data."""

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

    def load_all(self) -> Tuple[List[Portfolio], List[Investment]]:
        """Load all portfolios and investments from JSON file."""
        if not self.file_path.exists():
            return [], []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            version = data.get('version', '1.0')
            
            # Handle migration from old format
            if version == '1.0' and 'portfolios' not in data:
                return self._migrate_from_v1(data)
            
            # Load portfolios
            portfolios = []
            for port_data in data.get('portfolios', []):
                try:
                    portfolios.append(Portfolio.from_dict(port_data))
                except Exception as e:
                    print(f"Warning: Failed to load portfolio {port_data.get('id', 'unknown')}: {e}")
                    continue
            
            # Load investments
            investments = []
            for inv_data in data.get('investments', []):
                try:
                    investments.append(Investment.from_dict(inv_data))
                except Exception as e:
                    print(f"Warning: Failed to load investment {inv_data.get('id', 'unknown')}: {e}")
                    continue
            
            return portfolios, investments

        except json.JSONDecodeError as e:
            print(f"Error: Corrupted JSON file. Loading from backup if available.")
            return self._load_from_backup()
        except Exception as e:
            print(f"Error loading data: {e}")
            return [], []

    def save_all(self, portfolios: List[Portfolio], investments: List[Investment]) -> None:
        """Save portfolios and investments to JSON file with backup."""
        # Create backup before saving
        if self.file_path.exists():
            self._create_backup()

        data = {
            "version": "2.0",
            "last_updated": datetime.now().isoformat(),
            "portfolios": [port.to_dict() for port in portfolios],
            "investments": [inv.to_dict() for inv in investments]
        }

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")
            raise

    def _migrate_from_v1(self, data: dict) -> Tuple[List[Portfolio], List[Investment]]:
        """Migrate data from version 1.0 format to 2.0 format.
        
        Creates default portfolios for each unique timeframe found in investments.
        """
        print("Migrating data from v1.0 to v2.0 format...")
        
        old_investments = data.get('investments', [])
        if not old_investments:
            return [], []
        
        # Group investments by timeframe
        investments_by_timeframe = {}
        for inv_data in old_investments:
            timeframe = inv_data.get('timeframe', '1M')
            if timeframe not in investments_by_timeframe:
                investments_by_timeframe[timeframe] = []
            investments_by_timeframe[timeframe].append(inv_data)
        
        # Create default portfolios for each timeframe
        timeframe_names = {
            '1M': 'Default 1 Month Portfolio',
            '3M': 'Default 3 Month Portfolio',
            '6M': 'Default 6 Month Portfolio',
            '1Y': 'Default 1 Year Portfolio',
        }
        
        portfolios = []
        portfolio_id_map = {}  # Maps timeframe -> portfolio_id
        
        for timeframe in investments_by_timeframe.keys():
            portfolio = Portfolio.create_new(
                name=timeframe_names.get(timeframe, f'Default {timeframe} Portfolio'),
                description=f'Auto-created portfolio for {timeframe} investments',
                timeframe=timeframe
            )
            portfolios.append(portfolio)
            portfolio_id_map[timeframe] = portfolio.id
        
        # Migrate investments - assign them to appropriate portfolio
        investments = []
        for inv_data in old_investments:
            timeframe = inv_data.get('timeframe', '1M')
            portfolio_id = portfolio_id_map.get(timeframe)
            
            if portfolio_id:
                try:
                    investment = Investment.from_dict({
                        'id': inv_data['id'],
                        'name': inv_data['name'],
                        'portfolio_id': portfolio_id,
                        'final_amount': inv_data['final_amount'],
                        'percentage_change': inv_data['percentage_change'],
                        'created_at': inv_data['created_at'],
                        'updated_at': inv_data['updated_at'],
                    })
                    investments.append(investment)
                except Exception as e:
                    print(f"Warning: Failed to migrate investment {inv_data.get('id', 'unknown')}: {e}")
        
        # Save the migrated data immediately
        print(f"Created {len(portfolios)} default portfolios and migrated {len(investments)} investments")
        self.save_all(portfolios, investments)
        print("Migration complete!")
        
        return portfolios, investments

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

    def _load_from_backup(self) -> Tuple[List[Portfolio], List[Investment]]:
        """Load data from the most recent backup."""
        backup_files = list(self.backup_dir.glob("investments_*.json"))
        
        if not backup_files:
            print("No backup files found.")
            return [], []

        # Get the most recent backup
        latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_backup, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle migration if needed
            version = data.get('version', '1.0')
            if version == '1.0' and 'portfolios' not in data:
                return self._migrate_from_v1(data)
            
            portfolios = []
            for port_data in data.get('portfolios', []):
                portfolios.append(Portfolio.from_dict(port_data))
            
            investments = []
            for inv_data in data.get('investments', []):
                investments.append(Investment.from_dict(inv_data))
            
            print(f"Loaded data from backup: {latest_backup.name}")
            return portfolios, investments

        except Exception as e:
            print(f"Error loading from backup: {e}")
            return [], []

    def get_backup_files(self) -> List[Path]:
        """Get list of backup files sorted by modification time."""
        backup_files = list(self.backup_dir.glob("investments_*.json"))
        return sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True)

    def restore_from_backup(self, backup_path: Path) -> None:
        """Restore data from a specific backup file."""
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
        """Clear all data (creates backup first)."""
        if self.file_path.exists():
            self._create_backup()
        self.save_all([], [])

    def export_to_csv(self, csv_path: Path, portfolios: List[Portfolio], investments: List[Investment]) -> None:
        """Export investments to CSV format."""
        import csv
        
        if not investments:
            print("No investments to export.")
            return

        # Build lookup for portfolio names
        portfolio_map = {port.id: port for port in portfolios}

        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Portfolio', 'Portfolio Timeframe', 'Investment Name', 
                    'Final Amount', 'Percentage Change', 'Original Amount', 
                    'Profit/Loss', 'Created At', 'Updated At'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for inv in investments:
                    portfolio = portfolio_map.get(inv.portfolio_id)
                    portfolio_name = portfolio.name if portfolio else 'Unknown'
                    portfolio_timeframe = portfolio.timeframe if portfolio else 'Unknown'
                    
                    writer.writerow({
                        'Portfolio': portfolio_name,
                        'Portfolio Timeframe': portfolio_timeframe,
                        'Investment Name': inv.name,
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

    # Backward compatibility methods
    def load_investments(self) -> List[Investment]:
        """Load only investments (backward compatibility)."""
        _, investments = self.load_all()
        return investments

    def save_investments(self, investments: List[Investment]) -> None:
        """Save only investments (backward compatibility - creates empty portfolios list if needed)."""
        portfolios, _ = self.load_all()
        self.save_all(portfolios, investments)
