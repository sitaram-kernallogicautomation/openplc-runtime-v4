# OpenPLC Runtime v4

OpenPLC Runtime v4 is an industrial automation execution environment that runs Programmable Logic Controller (PLC) programs on standard computing hardware. It provides a web-based interface for uploading, compiling, and controlling PLC programs with real-time execution capabilities.

## What is OpenPLC Runtime?

OpenPLC Runtime v4 consists of two main components:

1. **Web Server (Python/Flask)** - HTTPS interface on port 8443 for program management, monitoring, and debugging
2. **PLC Runtime Core (C/C++)** - Real-time execution engine with deterministic scan cycles

The runtime executes programs created in [OpenPLC Editor v4](https://github.com/Autonomy-Logic/openplc-editor), supporting IEC 61131-3 programming languages (Ladder Logic, Structured Text, Function Block Diagram, etc.).

## Quick Start

### Docker (Recommended)

The fastest way to get started:

```bash
docker pull ghcr.io/autonomy-logic/openplc-runtime:latest

docker run -d \
  --name openplc-runtime \
  -p 8443:8443 \
  -v openplc-runtime-data:/var/run/runtime \
  ghcr.io/autonomy-logic/openplc-runtime:latest
```

Access the web interface at https://localhost:8443 (accept the self-signed certificate warning).

**Supported Architectures:** amd64, arm64, armv7

### Linux Installation

For native Linux installation:

```bash
# Clone repository
git clone https://github.com/Autonomy-Logic/openplc-runtime.git
cd openplc-runtime
git checkout development

# Install dependencies and compile
sudo ./install.sh

# Start the runtime
sudo ./start_openplc.sh
```

Access the web interface at https://localhost:8443.

**Supported Distributions:** Ubuntu, Debian, Fedora, CentOS, RHEL

**Requirements:**
- GCC compiler
- CMake
- Python 3.8+
- Root privileges (for real-time scheduling and port binding)

## How It Works

1. **Create Program** - Design your PLC program in OpenPLC Editor v4
2. **Generate ZIP** - Click "Generate program for OpenPLC Runtime v4" in the editor
3. **Upload** - Upload the ZIP file via the web interface at https://localhost:8443
4. **Compile** - Runtime automatically compiles the program (progress shown in web UI)
5. **Run** - Start/stop PLC execution via the web interface or REST API

The runtime compiles uploaded programs into shared libraries and loads them dynamically. The PLC core executes with real-time priority (SCHED_FIFO) for deterministic timing.

## Key Features

- **Web-Based Management** - Upload, compile, and control programs via HTTPS interface
- **Real-Time Execution** - Deterministic scan cycles with configurable timing
- **REST API** - Programmatic control via REST endpoints
- **WebSocket Debug Interface** - Real-time variable inspection and modification
- **Plugin System** - Extensible I/O drivers for various hardware
- **Multi-Architecture** - Runs on x86_64, ARM64, and ARM32 platforms
- **Docker Support** - Official multi-arch images available
- **Security** - TLS encryption, JWT authentication, file upload validation

## Architecture

OpenPLC Runtime v4 uses a dual-process architecture:

- **Web Server Process** - Flask application managing the web interface, REST API, and WebSocket debug interface
- **PLC Runtime Process** - C/C++ real-time engine executing PLC programs

The processes communicate via Unix domain sockets for command/control and log streaming.

**For detailed architecture information, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).**

## Documentation

### Getting Started
- [Docker Deployment](docs/DOCKER.md) - Container usage and configuration
- [Compilation Flow](docs/COMPILATION_FLOW.md) - How programs are built and loaded
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

### Advanced Topics
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [API Reference](docs/API.md) - REST endpoints and responses
- [Debug Protocol](docs/DEBUG_PROTOCOL.md) - WebSocket debug interface
- [Security](docs/SECURITY.md) - Authentication, TLS, and file validation
- [Plugin System](docs/PLUGIN_VENV_GUIDE.md) - Hardware I/O plugins
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and development setup

### Additional Resources
- [Plugin Driver Documentation](core/src/drivers/README.md) - Plugin driver layer details
- [WebSocket Debug Details](webserver/DEBUG_WEBSOCKET.md) - Debug WebSocket implementation
- [Logger Module](webserver/logger/logger_module_documentation.md) - Logging subsystem

## REST API

The runtime provides a REST API for programmatic control:

```bash
# Get PLC status
curl -k https://localhost:8443/api?argument=status

# Start PLC
curl -k https://localhost:8443/api?argument=start-plc

# Stop PLC
curl -k https://localhost:8443/api?argument=stop-plc

# Upload program
curl -k -X POST -F "file=@program.zip" \
  https://localhost:8443/api?argument=upload-file

# Check compilation status
curl -k https://localhost:8443/api?argument=compilation-status
```

**For complete API documentation, see [docs/API.md](docs/API.md).**

## WebSocket Debug Interface

Real-time debugging via WebSocket:

```javascript
import io from 'socket.io-client';

// Connect with JWT authentication
const socket = io('wss://localhost:8443/api/debug', {
  transports: ['websocket'],
  query: { token: jwt_token }
});

// Send debug command
socket.emit('debug_command', {
  command: '44 00 03 00 00 00 01 00 02'  // Get variables 0, 1, 2
});

// Receive response
socket.on('debug_response', (response) => {
  console.log(response.data);
});
```

**For complete debug protocol documentation, see [docs/DEBUG_PROTOCOL.md](docs/DEBUG_PROTOCOL.md).**

## Docker Usage

### Basic Usage

```bash
# Pull image
docker pull ghcr.io/autonomy-logic/openplc-runtime:latest

# Run with persistent storage
docker run -d \
  --name openplc-runtime \
  -p 8443:8443 \
  -v openplc-runtime-data:/var/run/runtime \
  ghcr.io/autonomy-logic/openplc-runtime:latest

# View logs
docker logs -f openplc-runtime

# Stop container
docker stop openplc-runtime
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  openplc-runtime:
    image: ghcr.io/autonomy-logic/openplc-runtime:latest
    container_name: openplc-runtime
    ports:
      - "8443:8443"
    volumes:
      - openplc-runtime-data:/var/run/runtime
    restart: unless-stopped

volumes:
  openplc-runtime-data:
```

Start with: `docker-compose up -d`

**For complete Docker documentation, see [docs/DOCKER.md](docs/DOCKER.md).**

## Building from Source

### Prerequisites

Install dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install build-essential gcc make cmake \
  python3-dev python3-pip python3-venv

# Fedora/RHEL/CentOS
sudo dnf install gcc gcc-c++ make cmake \
  python3 python3-devel python3-pip python3-venv
```

### Build Steps

```bash
# Clone repository
git clone https://github.com/Autonomy-Logic/openplc-runtime.git
cd openplc-runtime
git checkout development

# Run installation script
sudo ./install.sh
```

The installation script will:
1. Detect your Linux distribution
2. Install system dependencies
3. Create Python virtual environment at `venvs/runtime/`
4. Install Python dependencies
5. Compile the PLC runtime core with CMake

### Manual Build

For manual compilation:

```bash
# Create Python virtual environment
python3 -m venv venvs/runtime
source venvs/runtime/bin/activate
pip install -r requirements.txt
pip install -e .

# Compile runtime core
mkdir -p build
cd build
cmake ..
make -j$(nproc)
cd ..
```

### Starting the Runtime

```bash
sudo ./start_openplc.sh
```

The startup script will:
1. Check installation status
2. Setup plugin virtual environments (if plugins have requirements.txt)
3. Activate runtime virtual environment
4. Start the web server (which automatically manages the PLC runtime process)

**Note:** Root privileges are required for:
- Real-time scheduling (SCHED_FIFO priority)
- Binding to port 8443
- Creating Unix domain sockets in `/run/runtime/`

## Plugin System

OpenPLC Runtime supports plugins for hardware I/O:

**Plugin Types:**
- Python plugins (with isolated virtual environments)
- C/C++ plugins

**Configuration:** Edit `plugins.conf` to enable/disable plugins

**Example:**
```
# name,path,enabled,type,config_path,venv_path
modbus_slave,./core/src/drivers/plugins/python/modbus_slave_plugin/simple_modbus.py,1,0,./config.json,./venvs/modbus_slave
```

**Managing Plugin Virtual Environments:**
```bash
# Create venv for plugin
sudo bash scripts/manage_plugin_venvs.sh create plugin_name

# Install dependencies
sudo bash scripts/manage_plugin_venvs.sh install plugin_name

# List all plugin venvs
sudo bash scripts/manage_plugin_venvs.sh list
```

**For complete plugin documentation, see [docs/PLUGIN_VENV_GUIDE.md](docs/PLUGIN_VENV_GUIDE.md) and [core/src/drivers/README.md](core/src/drivers/README.md).**

## Security

### TLS/HTTPS

The runtime automatically generates self-signed TLS certificates on first run:
- Certificate: `webserver/certOPENPLC.pem`
- Private key: `webserver/keyOPENPLC.pem`

Browsers will show a certificate warning - this is normal for self-signed certificates. Click "Advanced" and proceed.

### File Upload Security

Uploaded ZIP files undergo comprehensive security validation:
- Path traversal prevention
- Size limits (10 MB per file, 50 MB total)
- ZIP bomb detection (compression ratio check)
- Extension whitelist (blocks .exe, .dll, .sh, .bat, .js, .vbs, .scr)
- macOS metadata removal

### Authentication

- JWT tokens for WebSocket debug interface
- Secrets stored in `/var/run/runtime/.env`
- Password hashing with salt and pepper

**For complete security documentation, see [docs/SECURITY.md](docs/SECURITY.md).**

## Troubleshooting

### Common Issues

**Cannot access web interface:**
```bash
# Check if runtime is running
ps aux | grep python3 | grep webserver

# Test connectivity
curl -k https://localhost:8443/api?argument=ping

# Check firewall
sudo ufw status
```

**Compilation failed:**
```bash
# Check compilation logs
curl -k https://localhost:8443/api?argument=compilation-status

# Verify ZIP file contains required files
unzip -l program.zip
```

**Permission errors:**
```bash
# Ensure running with sudo
sudo ./start_openplc.sh

# Check socket directory
ls -la /run/runtime/
```

**For complete troubleshooting guide, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).**

## Development

### Setup Development Environment

```bash
git clone https://github.com/Autonomy-Logic/openplc-runtime.git
cd openplc-runtime
git checkout development
sudo ./install.sh
```

### Running Tests

```bash
sudo bash scripts/setup-tests-env.sh
pytest tests/
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### Code Style

- **C/C++:** Follow existing style, 4-space indentation, no tabs
- **Python:** Follow PEP 8, type hints, docstrings
- **No emojis** anywhere in code, comments, or documentation (project standard)

### Contributing

1. Fork the repository
2. Create a feature branch from `development`
3. Make your changes
4. Submit a pull request

**For complete development guide, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).**

## Project Structure

```
openplc-runtime/
├── webserver/              # Flask web application (Python)
│   ├── app.py             # Main application entry
│   ├── restapi.py         # REST API blueprint
│   ├── debug_websocket.py # WebSocket debug interface
│   └── ...
├── core/
│   ├── src/plc_app/       # PLC runtime source (C/C++)
│   │   ├── plc_main.c     # Main entry point
│   │   ├── plc_state_manager.c/h # State management
│   │   ├── unix_socket.c/h # IPC server
│   │   └── utils/         # Utilities (log, watchdog, timing)
│   └── src/drivers/       # Plugin driver system
├── scripts/               # Build and management scripts
│   ├── compile.sh         # Compile PLC program
│   ├── compile-clean.sh   # Clean and rename library
│   └── manage_plugin_venvs.sh # Plugin venv management
├── build/                 # Compilation output
│   ├── plc_main           # Compiled runtime executable
│   └── libplc_*.so        # Compiled PLC program libraries
├── docs/                  # Documentation
├── CMakeLists.txt         # CMake build configuration
├── Dockerfile             # Container definition
├── install.sh             # Installation script
└── start_openplc.sh       # Startup script
```

## System Requirements

### Minimum Requirements
- **CPU:** 1 GHz single-core
- **RAM:** 512 MB
- **Disk:** 500 MB free space
- **OS:** Linux (Ubuntu 20.04+, Debian 11+, Fedora, CentOS, RHEL)

### Recommended Requirements
- **CPU:** 2 GHz dual-core or better
- **RAM:** 1 GB or more
- **Disk:** 1 GB free space
- **OS:** Ubuntu 22.04 LTS or Debian 12

### Real-Time Performance
For deterministic real-time performance:
- Dedicated CPU core recommended
- Real-time kernel (PREEMPT_RT) optional but beneficial
- Minimal background processes
- Root privileges for SCHED_FIFO scheduling

## License

See LICENSE file for details.

## Support

- **Issues:** https://github.com/Autonomy-Logic/openplc-runtime/issues
- **Documentation:** See `docs/` directory
- **OpenPLC Editor:** https://github.com/Autonomy-Logic/openplc-editor

## Related Projects

- [OpenPLC Editor v4](https://github.com/Autonomy-Logic/openplc-editor) - PLC programming environment
- [OpenPLC v3](https://github.com/thiagoralves/OpenPLC_v3) - Previous version

## Acknowledgments

OpenPLC Runtime v4 is developed and maintained by Autonomy Logic.
