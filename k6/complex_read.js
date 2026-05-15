/**
 * k6/complex_read.js — Teste 3: Leitura Complexa com JOINs / N+1
 *
 * Compara 3 estratégias:
 *   - ORM N+1        : lazy loading (múltiplas queries)
 *   - ORM Otimizado  : joinedload (1 query com JOINs)
 *   - SQL Nativo     : 1 query explícita com 4 JOINs
 *
 * Execução:
 *   k6 run k6/complex_read.js
 *   k6 run --out csv=results/complex_read.csv k6/complex_read.js
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

const ormN1Latency  = new Trend("orm_n1_latency_ms",   true);
//const ormOptLatency = new Trend("orm_opt_latency_ms",  true);
const sqlLatency    = new Trend("sql_join_latency_ms", true);
const ormN1Errors   = new Rate("orm_n1_error_rate");
//const ormOptErrors  = new Rate("orm_opt_error_rate");
const sqlErrors     = new Rate("sql_join_error_rate");

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
    orm_n1_latency_ms:   ["p(95)<3000"],
  //  orm_opt_latency_ms:  ["p(95)<500"],
    sql_join_latency_ms: ["p(95)<300"],
  },
};

const BASE = "http://localhost:8000";

export default function () {
  const orderId = Math.floor(Math.random() * 2000) + 1;

  if (__ENV.TARGET === 'orm') {
  const n1Res = http.get(`${BASE}/api/orm/orders/${orderId}/details`);
  ormN1Latency.add(n1Res.timings.duration);
  ormN1Errors.add(n1Res.status !== 200);
    }

  // ORM Otimizado
//  const optRes = http.get(`${BASE}/api/orm/orders/${orderId}/details/optimized`);
 // ormOptLatency.add(optRes.timings.duration);
 // ormOptErrors.add(optRes.status !== 200);
 // check(optRes, { "[ORM-OPT] status 200": (r) => r.status === 200 });

  if (__ENV.TARGET === 'sql') {
  const sqlRes = http.get(`${BASE}/api/sql/orders/${orderId}/details`);
  sqlLatency.add(sqlRes.timings.duration);
  sqlErrors.add(sqlRes.status !== 200);
    }

  sleep(0.1);
}
