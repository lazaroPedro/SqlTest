#!/bin/bash

# Cria diretórios de saída
mkdir -p results/k6
mkdir -p results/prometheus

# Testes e Alvos
SCRIPTS=("simple_read.js" "write_test.js" "complex_read.js")
TARGETS=("orm" "sql")

echo "==================================================="
echo " INICIANDO SUÍTE DE BENCHMARK AUTOMATIZADA"
echo "==================================================="

for TARGET in "${TARGETS[@]}"; do
  for SCRIPT in "${SCRIPTS[@]}"; do
    
    # Define o nome único para a label do Prometheus
    SCRIPT_NAME=$(basename $SCRIPT .js)
    export TYPE_TEST="${TARGET}_${SCRIPT_NAME}"
    
    echo ""
    echo "---------------------------------------------------"
    echo "▶ Iniciando cenário: [$TARGET] com script [$SCRIPT]"
    echo "▶ Label Prometheus: test_type=$TYPE_TEST"
    echo "---------------------------------------------------"

    # 1. Sobe o servidor (o -v no down garante um banco de dados limpo e re-semeado)
    echo "⚙️  Limpando e subindo containers..."
    docker compose down -v > /dev/null 2>&1
    docker compose up -d > /dev/null 2>&1

    # Aguarda a API ficar saudável
    echo "⏳ Aguardando API (Healthcheck)..."
    until curl -s -f http://localhost:8000/health > /dev/null; do
        sleep 2
    done
    sleep 5 # Tempo extra para o Prometheus iniciar o scraping

    # 2. Warm-up (Esquenta as conexões, pool do banco, caches)
    echo "🔥 Executando Warm-up (10 VUs por 10s)..."
    k6 run -e TARGET=$TARGET --vus 10 --duration 10s --quiet k6/$SCRIPT > /dev/null 2>&1

    # 3. Teste Oficial
    echo "🚀 Rodando Teste de Carga Oficial..."
    k6 run -e TARGET=$TARGET --out csv=results/k6/${TYPE_TEST}.csv k6/$SCRIPT
    
    # Aguarda 15 segundos para o Prometheus realizar os últimos scrapes (intervalo é 15s)
    echo "⏳ Aguardando coleta final de métricas do Prometheus..."
    sleep 15


    # 4. Extração de Métricas do Prometheus
    echo "📊 Extraindo dados do Prometheus..."
    
    PROM_URL="http://localhost:9090/api/v1/query"

    # =========================================================
    # DADOS PARA O GRÁFICO DE BARRAS (Picos/Máximos)
    # =========================================================
    
    # Pico de RAM
    curl -s -G "$PROM_URL" --data-urlencode 'query=max_over_time(process_resident_memory_bytes[5m])' > results/prometheus/${TYPE_TEST}_ram_max.json
    
    # Pico de CPU
    curl -s -G "$PROM_URL" --data-urlencode 'query=max_over_time(rate(process_cpu_seconds_total[1m])[5m:15s])' > results/prometheus/${TYPE_TEST}_cpu_max.json

    # Pico de TPS do Banco
    curl -s -G "$PROM_URL" --data-urlencode 'query=max_over_time(rate(pg_stat_database_xact_commit{datname="benchmark"}[1m])[5m:15s])' > results/prometheus/${TYPE_TEST}_db_tps.json

    # =========================================================
    # DADOS PARA O GRÁFICO DE LINHAS (Séries Temporais)
    # =========================================================
    
    # Série de RAM
    curl -s -G "$PROM_URL" --data-urlencode 'query=process_resident_memory_bytes[5m]' > results/prometheus/${TYPE_TEST}_ram_series.json
    
    # Série de CPU
    curl -s -G "$PROM_URL" --data-urlencode 'query=rate(process_cpu_seconds_total[1m])[5m:15s]' > results/prometheus/${TYPE_TEST}_cpu_series.json


    # 5. Derruba o servidor (O -v limpa os volumes, garantindo isolamento para o próximo loop)
    echo "🛑 Derrubando containers do cenário..."
    docker compose down -v > /dev/null 2>&1

  done
done

echo ""
echo "✅ BENCHMARK FINALIZADO! Resultados salvos na pasta 'results/'"