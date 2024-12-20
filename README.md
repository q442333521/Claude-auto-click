# Claude Auto Clicker

A Python-based auto-clicker tool specifically designed for the Claude chat window. It automatically detects and clicks the "Allow" button in Claude's interface, making it more convenient to use Claude for extended conversations.

## Features

- Automatically detects and clicks the "Allow" button in Claude's chat window
- User-friendly GUI interface
- Configurable detection interval
- Real-time status display and logging
- Emergency stop by moving mouse to screen corner
- Smart window detection to avoid unnecessary scanning
- Multi-threaded design for responsive UI

## Requirements

- Windows OS
- Python 3.8 or higher
- Required packages listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/claude-auto-clicker.git
cd claude-auto-clicker
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Running from Source

1. Run the main script:
```bash
python auto_click.py
```

2. Click "开始自动点击" (Start Auto Click) to begin the auto-clicking process
3. Adjust the detection interval as needed (0.1-60 seconds)
4. The program will automatically detect the Claude window and click the "Allow" button when it appears

### Using the Compiled Version

1. Download the latest release from the Releases page
2. Run the executable file `Claude自动点击器.exe`
3. No installation or Python environment required

## Building from Source

To create your own executable:

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Run the build script:
```bash
python build.py
```

The compiled executable will be created in the `dist` directory.

## Development

### Project Structure

- `auto_click.py`: Main program file containing the GUI and clicking logic
- `build.py`: Build script for creating the executable
- `allow_button.png`: Reference image for button detection
- `requirements.txt`: Required Python packages

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Safety Notes

- The program includes a failsafe feature: moving the mouse to the screen's top-left corner will stop the program
- The tool only works when the Claude window is active and visible
- Detection interval can be adjusted to reduce system load
