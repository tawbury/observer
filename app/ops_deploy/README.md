# QTS Observer Deployment Package

## Structure
- `/app/` - Observer application root
- `/app/data/observer` - Data storage directory
- `/app/logs` - Log files directory
- `/app/config` - Configuration files

## Quick Start

### Using Docker
```bash
docker-compose up -d
```

### Manual Deployment
```bash

# Extract package
tar -xzf ops_deploy.tar.gz
cd ops_deploy

# Run startup script
./start_ops.sh
```

## Environment Variables
- `QTS_OBSERVER_STANDALONE=1` - Enable standalone mode
- `PYTHONPATH=/app/src:/app` - Python path configuration
- `OBSERVER_DATA_DIR=/app/data/observer` - Data directory
- `OBSERVER_LOG_DIR=/app/logs` - Log directory

## Volumes
- `./data` - Observer data files
- `./logs` - Application logs
- `./config` - Configuration files

## Ports
- `8000` - Future web interface (currently not implemented)

## Health Check
The container includes a basic health check. Monitor with:
```bash
docker ps
docker logs qts-observer
```

