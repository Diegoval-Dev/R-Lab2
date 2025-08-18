#!/bin/bash

# Lab 2 Part 2 - System Startup Script
# Starts WebSocket receiver, Streamlit UI, and provides Go emitter ready to use

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Lab 2 Part 2 - Sistema de Arquitectura por Capas${NC}"
echo "=================================================="

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Puerto $1 está en uso${NC}"
        return 1
    else
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    echo -n "Esperando $service_name en puerto $port"
    while [ $attempt -le $max_attempts ]; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo -e " ${RED}❌ Timeout${NC}"
    return 1
}

# Check prerequisites
echo -e "\n${YELLOW}📋 Verificando prerequisitos...${NC}"

# Check Python venv
if [ ! -d "receiver-py/venv" ]; then
    echo -e "${RED}❌ Python venv no encontrado en receiver-py/venv${NC}"
    echo "Ejecuta: cd receiver-py && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check Go binary
if [ ! -f "emitter-go/bin/simple_test" ]; then
    echo -e "${YELLOW}🔨 Compilando emisor Go...${NC}"
    cd emitter-go
    go build -o bin/simple_test ./cmd/simple_test
    cd ..
fi

# Check ports
RECEIVER_PORT=8765
STREAMLIT_PORT=8003

echo -e "${GREEN}✅ Prerequisites OK${NC}"

# Start services
echo -e "\n${YELLOW}🚀 Iniciando servicios...${NC}"

# Kill any existing processes on our ports
echo "Limpiando puertos..."
lsof -ti:$RECEIVER_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$STREAMLIT_PORT | xargs kill -9 2>/dev/null || true
sleep 2

# Start WebSocket Receiver
echo -e "\n${BLUE}1. Iniciando Receptor WebSocket (Puerto $RECEIVER_PORT)...${NC}"
cd receiver-py
source venv/bin/activate
PYTHONPATH=./src python src/layered_receiver.py --host localhost --port $RECEIVER_PORT > ../logs/receiver.log 2>&1 &
RECEIVER_PID=$!
cd ..

# Wait for receiver to be ready
wait_for_service $RECEIVER_PORT "Receptor WebSocket" || {
    echo -e "${RED}❌ Error iniciando receptor${NC}"
    kill $RECEIVER_PID 2>/dev/null || true
    exit 1
}

# Start Streamlit UI
echo -e "\n${BLUE}2. Iniciando Streamlit UI (Puerto $STREAMLIT_PORT)...${NC}"
cd receiver-py
source venv/bin/activate
PYTHONPATH=./src streamlit run src/streamlit_integrated.py --server.port $STREAMLIT_PORT --server.headless true > ../logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
cd ..

# Wait for Streamlit to be ready
wait_for_service $STREAMLIT_PORT "Streamlit UI" || {
    echo -e "${RED}❌ Error iniciando Streamlit${NC}"
    kill $RECEIVER_PID $STREAMLIT_PID 2>/dev/null || true
    exit 1
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Save PIDs for cleanup
echo $RECEIVER_PID > logs/receiver.pid
echo $STREAMLIT_PID > logs/streamlit.pid

echo -e "\n${GREEN}✅ Sistema iniciado correctamente!${NC}"
echo "=================================================="

echo -e "\n${BLUE}📊 Estado del Sistema:${NC}"
echo -e "🔗 Receptor WebSocket: ${GREEN}ws://localhost:$RECEIVER_PORT${NC}"
echo -e "🌐 Streamlit UI: ${GREEN}http://localhost:$STREAMLIT_PORT${NC}"
echo -e "🚀 Emisor Go: ${GREEN}./emitter-go/bin/simple_test${NC}"

echo -e "\n${BLUE}🧪 Pruebas rápidas:${NC}"
echo "# CRC sin ruido (debería funcionar):"
echo "./emitter-go/bin/simple_test \"Hello World\" crc 0.0"
echo ""
echo "# CRC con ruido (debería ser rechazado):"
echo "./emitter-go/bin/simple_test \"Hello World\" crc 0.05"
echo ""
echo "# Hamming con poco ruido (debería corregir):"
echo "./emitter-go/bin/simple_test \"Test\" hamming 0.01"

echo -e "\n${BLUE}📱 Acceso Web:${NC}"
echo -e "Abre en tu navegador: ${GREEN}http://localhost:$STREAMLIT_PORT${NC}"

echo -e "\n${YELLOW}📝 Logs:${NC}"
echo "Receptor: tail -f logs/receiver.log"
echo "Streamlit: tail -f logs/streamlit.log"

echo -e "\n${YELLOW}🛑 Para detener el sistema:${NC}"
echo "./stop_lab2_system.sh"

# Trap to cleanup on script exit
cleanup() {
    echo -e "\n${YELLOW}🧹 Limpiando procesos...${NC}"
    kill $RECEIVER_PID $STREAMLIT_PID 2>/dev/null || true
    rm -f logs/receiver.pid logs/streamlit.pid
}

# Create stop script
cat > stop_lab2_system.sh << 'EOF'
#!/bin/bash

# Lab 2 Part 2 - System Stop Script

echo "🛑 Deteniendo Lab 2 System..."

# Kill processes by PID if available
if [ -f logs/receiver.pid ]; then
    kill $(cat logs/receiver.pid) 2>/dev/null || true
    rm -f logs/receiver.pid
fi

if [ -f logs/streamlit.pid ]; then
    kill $(cat logs/streamlit.pid) 2>/dev/null || true  
    rm -f logs/streamlit.pid
fi

# Kill by port as backup
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true

echo "✅ Sistema detenido"
EOF

chmod +x stop_lab2_system.sh

# Keep script running to maintain services
echo -e "\n${GREEN}⏳ Sistema corriendo... Presiona Ctrl+C para detener${NC}"
trap cleanup EXIT INT TERM

# Wait for user interrupt
while true; do
    sleep 1
done