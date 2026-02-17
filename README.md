# SDGW 1914-1919

A comprehensive data access and web application system for the **Soldiers Died in the Great War 1914-1919** dataset. This project modernizes historical military data access through a complete migration from legacy systems to a modern web interface.

## 🎯 Project Overview

The SDGW 1914-1919 project preserves and provides modern access to historical military records from World War I. It transforms a legacy Windows application into a modern, searchable web interface with comprehensive data export capabilities.

### Key Features

- **🔍 Advanced Search**: Search through 709,203+ military records
- **📊 Data Export**: Complete CSV exports for analysis
- **🌐 Modern Web UI**: Clean, responsive interface built with Flask
- **📱 Senior-Friendly Design**: Large fonts and intuitive navigation
- **🗄️ SQLite Database**: Fast, reliable data storage with 26 indexes
- **🧪 Comprehensive Testing**: 39+ tests ensuring data integrity

## 📋 Project Status

### ✅ Phase A: Data Access Layer (Complete)
- DataExtractor class for accessing legacy MDB files
- 7 CSV exports with validation
- Data profiling and documentation
- **14 tests passing**

### ✅ Phase B: Data Migration (Complete)  
- Complete migration to SQLite database
- 709,203 records across 7 tables
- 26 performance indexes
- **25 tests passing**

### 🟡 Phase C: Basic Web UI (~75% Complete)
- Flask web application with search and detail views
- Responsive design with accessibility features
- **Known Issues**: Pagination bug, date formatting
- **Missing**: Related records, breadcrumbs, UI tests

### 🔴 Phase D: Desktop Application (Not Started)
- Standalone desktop app using pywebview
- Senior-first UX overhaul
- Fuzzy search capabilities
- Windows deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/eek2020/SDGW1914-1919.git
   cd SDGW1914-1919
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the web application**
   ```bash
   python src/web_app.py
   ```

4. **Access the application**
   Open your browser to `http://localhost:5000`

### Database Setup

The main database (`data/sd_2011.db`) is excluded from git due to size constraints. To recreate it:

1. Place your original `sd_2011.mdb` file in the `data/` directory
2. Run the migration script:
   ```bash
   python src/data_migration.py
   ```

## 📁 Project Structure

```
SDGW1914-1919/
├── src/                    # Source code
│   ├── web_app.py         # Flask web application
│   ├── data_access.py     # Legacy data access
│   ├── data_migration.py  # Database migration
│   ├── schema.sql         # Database schema
│   ├── scripts/           # Utility scripts
│   ├── templates/         # HTML templates
│   └── static/           # CSS and assets
├── data/                  # Data files
│   ├── exports/          # CSV exports
│   └── backups/          # Database backups
├── tests/                 # Test suite
├── docs/                  # Documentation
├── old_system/           # Legacy system files
└── logs/                 # Application logs
```

## 🧪 Testing

Run the complete test suite:

```bash
# Data access tests
python -m pytest tests/test_data_access.py

# Migration tests  
python -m pytest tests/test_migration.py

# All tests
python -m pytest tests/
```

## 📊 Data Overview

### Database Schema

| Table | Records | Description |
|-------|---------|-------------|
| soldiers | ~703,000 | Service personnel records |
| officers | ~6,200 | Officer records |
| battalions | ~8,500 | Unit information |
| ranks | ~500 | Rank hierarchy |
| regiments | ~300 | Regiment details |
| casualties | ~703,000 | Casualty information |
| theaters | ~10 | Theater of operations |

### Key Data Fields

- **Personnel**: Name, service number, rank, regiment, battalion
- **Service**: Enlistment date, death date, theater of operations
- **Casualty**: Death date, burial location, memorial information
- **Administrative**: Record source, validation status

## 🔧 Development

### Adding New Features

1. **Database changes**: Update `src/schema.sql`
2. **Web features**: Modify `src/web_app.py` and templates
3. **Data access**: Extend `src/data_access.py`
4. **Testing**: Add corresponding tests in `tests/`

### Code Style

- Follow PEP 8 for Python code
- Use descriptive variable names
- Add docstrings for functions and classes
- Maintain test coverage above 90%

## 📚 Documentation

- **[Data Access Plan](docs/01_DATA_ACCESS_PLAN.md)** - Phase A specifications
- **[Migration Plan](docs/04_PRD_B_DATA_MIGRATION.md)** - Phase B specifications  
- **[UI Specifications](docs/05_PRD_C_BASIC_UI.md)** - Phase C requirements
- **[Desktop Application](docs/09_PRD_D_DESKTOP_APPLICATION.md)** - Phase D roadmap
- **[Implementation Status](docs/08_IMPLEMENTATION_STATUS.md)** - Current progress

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is dedicated to preserving historical military data. Please ensure respect for the historical records and individuals documented.

## 🙏 Acknowledgments

- Original data from Commonwealth War Graves Commission
- Legacy system preservation efforts
- Contributors to historical data digitization

## 📞 Support

For questions, issues, or contributions:

- Create an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the test files for usage examples

---

**Note**: Large database files are excluded from this repository for size constraints. See the Database Setup section above for recreation instructions.
