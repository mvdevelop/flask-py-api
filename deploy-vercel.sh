
#!/bin/bash
echo "🚀 Preparando deploy para Vercel..."

# 1. Cria estrutura da Vercel
mkdir -p api
echo "📁 Estrutura de pastas criada"

# 2. Copia o arquivo de entrada da Vercel
cat > api/index.py << 'EOF'
"""
Entry point for Vercel Serverless Functions
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.app import create_app
app = create_app('production')
application = app
EOF

echo "✅ api/index.py criado"

# 3. Cria vercel.json
cat > vercel.json << 'EOF'
{
  "version": 2,
  "name": "pystore-api",
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/api/index.py"
    }
  ],
  "env": {
    "FLASK_ENV": "production"
  },
  "functions": {
    "api/index.py": {
      "maxDuration": 10,
      "memory": 1024
    }
  },
  "regions": ["gru1"]
}
EOF

echo "✅ vercel.json criado"

# 4. Instala Vercel CLI se não existir
if ! command -v vercel &> /dev/null; then
    echo "📦 Instalando Vercel CLI..."
    npm install -g vercel
fi

# 5. Faz deploy
echo "🌐 Iniciando deploy..."
vercel --prod

echo "✅ Deploy concluído!"
