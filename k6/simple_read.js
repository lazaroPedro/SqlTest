/**
 * k6/simple_read.js — Teste 1: Leitura Simples (SELECT user por ID)
 *
 * Cenários:
 *   Baixa:  10 VUs × 30s
 *   Média:  75 VUs × 30s
 *   Alta:  500 VUs × 30s
 *
 * Execução:
 *   k6 run k6/simple_read.js
 *   k6 run --out csv=results/simple_read.csv k6/simple_read.js
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

const ormLatency = new Trend("orm_latency_ms", true);
const sqlLatency = new Trend("sql_latency_ms", true);
const ormErrors  = new Rate("orm_error_rate");
const sqlErrors  = new Rate("sql_error_rate");

export const options = {
  scenarios: {
    low_load: {
      executor: "constant-vus",
      vus: 10,
      duration: "30s",
      startTime: "0s",
    },
    medium_load: {
      executor: "constant-vus",
      vus: 75,
      duration: "30s",
      startTime: "35s",
    },
    high_load: {
      executor: "constant-vus",
      vus: 500,
      duration: "30s",
      startTime: "70s",
    },
  },
  thresholds: {
    orm_latency_ms: ["p(95)<500"],
    sql_latency_ms: ["p(95)<200"],
    orm_error_rate: ["rate<0.01"],
    sql_error_rate: ["rate<0.01"],
  },
};

const BASE = "http://localhost:8000";

export default function () {
  const userId = Math.floor(Math.random() * 1000) + 1;

  // ORM
  const ormRes = http.get(`${BASE}/api/orm/users/${userId}`);
  ormLatency.add(ormRes.timings.duration);
  ormErrors.add(ormRes.status !== 200);
  check(ormRes, { "[ORM] status 200": (r) => r.status === 200 });

  // SQL Nativo
  const sqlRes = http.get(`${BASE}/api/sql/users/${userId}`);
  sqlLatency.add(sqlRes.timings.duration);
  sqlErrors.add(sqlRes.status !== 200);
  check(sqlRes, { "[SQL] status 200": (r) => r.status === 200 });

  sleep(0.1);
}
