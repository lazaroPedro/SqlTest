/**
 * k6/write_test.js — Teste 2: Escrita (INSERT massivo de pedidos)
 *
 * Execução:
 *   k6 run k6/write_test.js
 *   k6 run --out csv=results/write_test.csv k6/write_test.js
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

const ormWriteLatency = new Trend("orm_write_latency_ms", true);
const sqlWriteLatency = new Trend("sql_write_latency_ms", true);
const ormWriteErrors  = new Rate("orm_write_error_rate");
const sqlWriteErrors  = new Rate("sql_write_error_rate");

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
    orm_write_latency_ms: ["p(95)<1000"],
    sql_write_latency_ms: ["p(95)<600"],
  },
};

const BASE    = "http://localhost:8000";
const HEADERS = { "Content-Type": "application/json" };

function buildPayload() {
  const userId    = Math.floor(Math.random() * 1000) + 1;
  const itemCount = Math.floor(Math.random() * 4)    + 1;
  const items = Array.from({ length: itemCount }, () => ({
    product_id: Math.floor(Math.random() * 500) + 1,
    quantity:   Math.floor(Math.random() * 5)   + 1,
    unit_price: +(Math.random() * 990 + 10).toFixed(2),
  }));
  return JSON.stringify({ user_id: userId, items });
}

export default function () {
  const payload = buildPayload();

  // ORM
  const ormRes = http.post(`${BASE}/api/orm/orders`, payload, { headers: HEADERS });
  ormWriteLatency.add(ormRes.timings.duration);
  ormWriteErrors.add(ormRes.status !== 200);
  check(ormRes, { "[ORM-Write] status 200": (r) => r.status === 200 });

  // SQL Nativo
  const sqlRes = http.post(`${BASE}/api/sql/orders`, payload, { headers: HEADERS });
  sqlWriteLatency.add(sqlRes.timings.duration);
  sqlWriteErrors.add(sqlRes.status !== 200);
  check(sqlRes, { "[SQL-Write] status 200": (r) => r.status === 200 });

  sleep(0.2);
}
